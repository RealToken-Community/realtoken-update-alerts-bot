import os
import requests
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_ALERT_BOT_TOKEN")
GROUP_ID = os.getenv("TELEGRAM_ALERT_GROUP_ID")

TELEGRAM_MAX_LEN = 4096

def escape_markdown_v2(text: str) -> str:
    # Caractères à échapper en MarkdownV2 (spec Telegram)
    special = r'_\*\[\]\(\)~`>#+\-=|{}.!'
    out = []
    for ch in str(text):
        if ch in special:
            out.append("\\" + ch)
        else:
            out.append(ch)
    return "".join(out)

def send_telegram_alert(message, group_id=GROUP_ID, bot_token=BOT_TOKEN):
    if not bot_token or not group_id:
        return None

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    msg = str(message)
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
