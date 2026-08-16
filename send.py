"""Scheduled run: sends exactly one video to each target channel.

Picks, for every target channel, the least-recently-used video that has
not already been sent to ANY channel today (so the same video never
lands in two channels on the same day, but can recur on a later day).
Also does a small incremental scan past the last known message id in
the source channel, in case new videos were archived since the last run.

Env vars required:
  BOT_TOKEN            - bot token
  SOURCE_CHANNEL_ID    - source archive channel id
  TARGET_CHANNEL_IDS   - comma-separated target channel ids
  STAGING_CHAT_ID       - private chat id used to probe for new videos
"""
import json
import os
import random
import time
from datetime import datetime, timezone, timedelta

from tg import copy_message, delete_message, TelegramError

STATE_PATH = "state.json"
INCREMENTAL_SCAN_LIMIT = 40
MAX_JITTER_SECONDS = 45  # small variance only - GitHub Actions minutes are billed even while sleeping

TR_TZ = timezone(timedelta(hours=3))


def load_state():
    with open(STATE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state):
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def today_str():
    return datetime.now(TR_TZ).strftime("%Y-%m-%d")


def incremental_scan(token, source_id, staging_id, state):
    start = state["last_scanned_id"] + 1
    misses = 0
    scanned = 0
    mid = start
    while scanned < INCREMENTAL_SCAN_LIMIT:
        try:
            result = copy_message(token, staging_id, source_id, mid, disable_notification=True)
            delete_message(token, staging_id, result["message_id"])
            state["videos"][str(mid)] = {"total_uses": 0, "last_used": None, "history": []}
            state["last_scanned_id"] = mid
            misses = 0
        except TelegramError:
            misses += 1
            if misses >= 15:
                break
        scanned += 1
        mid += 1
        time.sleep(0.12)


def pick_video(state, excluded_today, channel_id):
    candidates = [
        (mid, info) for mid, info in state["videos"].items() if mid not in excluded_today
    ]
    if not candidates:
        return None
    candidates.sort(key=lambda item: (item[1]["total_uses"], item[1]["last_used"] or ""))
    return candidates[0][0]


def main():
    token = os.environ["BOT_TOKEN"]
    source_id = os.environ["SOURCE_CHANNEL_ID"]
    targets = [c.strip() for c in os.environ["TARGET_CHANNEL_IDS"].split(",") if c.strip()]
    staging_id = os.environ["STAGING_CHAT_ID"]

    jitter = random.randint(0, MAX_JITTER_SECONDS)
    print(f"Sleeping {jitter}s jitter before sending...")
    time.sleep(jitter)

    state = load_state()

    incremental_scan(token, source_id, staging_id, state)

    day = today_str()
    excluded_today = {
        mid for mid, info in state["videos"].items()
        if any(h["date"] == day for h in info["history"])
    }

    for channel_id in targets:
        video_id = pick_video(state, excluded_today, channel_id)
        if video_id is None:
            print(f"No available video for channel {channel_id}, skipping.")
            continue
        try:
            copy_message(token, channel_id, source_id, int(video_id))
        except TelegramError as e:
            print(f"Failed to send {video_id} to {channel_id}: {e.description}")
            continue

        info = state["videos"][video_id]
        info["total_uses"] += 1
        info["last_used"] = day
        info["history"].append({"channel": channel_id, "date": day})
        excluded_today.add(video_id)
        print(f"Sent video {video_id} -> {channel_id}")
        time.sleep(1)

    save_state(state)


if __name__ == "__main__":
    main()