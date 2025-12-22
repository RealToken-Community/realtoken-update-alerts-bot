from __future__ import annotations

import traceback
from telegram.error import BadRequest, NetworkError, TimedOut, RetryAfter

from bot.services.send_telegram_alert import send_telegram_alert
from bot.services.logging_config import get_logger

logger = get_logger(__name__)


async def global_error_handler(update, context):
    """
    Global error handler for the Telegram application.

    - Ignores harmless 'Message is not modified' BadRequest as INFO.
    - Logs other errors with traceback.
    - Sends a concise Telegram alert for real errors (avoids alert spam on transient network issues).
    """
    err = context.error

    # 1) Harmless Telegram error: message not modified
    if isinstance(err, BadRequest) and "Message is not modified" in str(err):
        logger.info(f"Telegram BadRequest ignored: {err}")
        return

    # 2) Transient network issues: log as WARNING and do NOT alert
    #    (prevents spam when Telegram has temporary hiccups)
    if isinstance(err, (NetworkError, TimedOut, RetryAfter)):
        logger.warning(f"Telegram network/transient error: {err}", exc_info=True)
        return

    # 3) Everything else: log with traceback + send Telegram alert (text only)
    logger.exception(f"Unhandled error while processing update: {err}", exc_info=True)

    # Keep Telegram message short + useful
    alert_text = (
        "🚨 Unhandled error while processing update\n"
        f"Error: {err}"
    )
    send_telegram_alert(alert_text)
