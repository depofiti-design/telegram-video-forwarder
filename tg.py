"""Minimal Telegram Bot API client using only the standard library."""
import json
import time
import urllib.request
import urllib.error

API_ROOT = "https://api.telegram.org/bot{token}/{method}"


class TelegramError(Exception):
    def __init__(self, description, error_code=None):
        super().__init__(description)
        self.description = description
        self.error_code = error_code


def call(token, method, params, retries=5):
    url = API_ROOT.format(token=token, method=method)
    data = json.dumps(params).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}
    )
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                if body.get("ok"):
                    return body["result"]
                raise TelegramError(body.get("description"), body.get("error_code"))
        except urllib.error.HTTPError as e:
            body = json.loads(e.read().decode("utf-8"))
            code = body.get("error_code")
            desc = body.get("description", "")
            if code == 429:
                retry_after = body.get("parameters", {}).get("retry_after", 5)
                time.sleep(retry_after + 1)
                continue
            raise TelegramError(desc, code)
    raise TelegramError("retries exhausted for " + method)


def copy_message(token, chat_id, from_chat_id, message_id, disable_notification=False):
    return call(token, "copyMessage", {
        "chat_id": chat_id,
        "from_chat_id": from_chat_id,
        "message_id": message_id,
        "disable_notification": disable_notification,
    })


def delete_message(token, chat_id, message_id):
    try:
        call(token, "deleteMessage", {"chat_id": chat_id, "message_id": message_id})
    except TelegramError:
        pass