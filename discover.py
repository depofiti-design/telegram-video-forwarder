"""One-time backfill: scan the source channel for existing videos and
build the initial state.json. Uses the admin's private chat with the bot
as a disposable staging area (copy then immediately delete) so nothing
is left behind and no real target channel is touched.

Usage: python discover.py <bot_token> <source_channel_id> <staging_chat_id>
"""
import json
import sys
import time

from tg import copy_message, delete_message, TelegramError

STATE_PATH = "state.json"
CONSECUTIVE_MISS_LIMIT = 60
DELAY = 0.12


def probe(token, source_id, staging_id, message_id):
    try:
        result = copy_message(token, staging_id, source_id, message_id, disable_notification=True)
        delete_message(token, staging_id, result["message_id"])
        return True
    except TelegramError:
        return False


def main():
    token, source_id, staging_id = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])

    found = []
    misses_in_a_row = 0
    message_id = 1
    highest_hit = 0

    print("Scanning source channel for existing videos...")
    while True:
        ok = probe(token, source_id, staging_id, message_id)
        if ok:
            found.append(message_id)
            highest_hit = message_id
            misses_in_a_row = 0
        else:
            misses_in_a_row += 1
        if message_id % 25 == 0:
            print(f"  checked up to id={message_id}, found={len(found)}")
        time.sleep(DELAY)
        message_id += 1
        if misses_in_a_row >= CONSECUTIVE_MISS_LIMIT:
            print(f"Stopping: {CONSECUTIVE_MISS_LIMIT} consecutive misses after id={highest_hit}.")
            break
        if message_id > 200000:
            print("Safety cap reached (200000). Stopping.")
            break

    state = {
        "last_scanned_id": highest_hit,
        "videos": {str(mid): {"total_uses": 0, "last_used": None, "history": []} for mid in found},
    }
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

    print(f"Done. {len(found)} videos found. last_scanned_id={state['last_scanned_id']}")
    print(f"Wrote {STATE_PATH}")


if __name__ == "__main__":
    main()