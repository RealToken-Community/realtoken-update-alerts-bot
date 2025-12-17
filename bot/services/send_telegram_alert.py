import os
import time
import threading
import requests
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_ALERT_BOT_TOKEN")
GROUP_ID = os.getenv("TELEGRAM_ALERT_GROUP_ID")

TELEGRAM_MAX_LEN = 4096

# --- No-repeat cache (process-local) ---
_SENT_CACHE = {}  # key -> last_sent_epoch_seconds
_SENT_CACHE_LOCK = threading.Lock()


def escape_markdown_v2(text: str) -> str:
    # Characters that must be escaped in Telegram MarkdownV2
    special = r'_\*\[\]\(\)~`>#+\-=|{}.!'
    out = []
    for ch in str(text):
        if ch in special:
            out.append("\\" + ch)
        else:
            out.append(ch)
    return "".join(out)


def _cleanup_cache(now: float, max_age_seconds: float) -> None:
    # Remove old entries to prevent the cache from growing indefinitely
    to_del = [k for k, t in _SENT_CACHE.items() if (now - t) > max_age_seconds]
    for k in to_del:
        del _SENT_CACHE[k]


def send_telegram_alert(
    message,
    group_id=GROUP_ID,
    bot_token=BOT_TOKEN,
    *,
    no_repeat: bool = True,
    repeat_window_minutes: int = 5,
):
    if not bot_token or not group_id:
        return None

    msg_raw = str(message)

    # Anti-repeat logic (based on raw message content + chat)
    if no_repeat:
        window_s = max(0, int(repeat_window_minutes)) * 60
        now = time.time()
        cache_key = (str(group_id), msg_raw)

        with _SENT_CACHE_LOCK:
            last = _SENT_CACHE.get(cache_key)
            if last is not None and (now - last) < window_s:
                return None  # Message already sent recently → skip sending

            _SENT_CACHE[cache_key] = now

            # Periodic cleanup of expired cache entries
            _cleanup_cache(now, max_age_seconds=max(window_s, 30 * 60))

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    msg = msg_raw
    if len(msg) > TELEGRAM_MAX_LEN:
        msg = msg[:4000] + "\n…(truncated)…"

    msg = escape_markdown_v2(msg)

    payload = {
        "chat_id": group_id,
        "text": msg,
        "disable_web_page_preview": True,
        "parse_mode": "MarkdownV2",
    }

    resp = requests.post(url, json=payload, timeout=10)
    return resp
