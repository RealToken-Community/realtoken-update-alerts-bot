import logging
import asyncio
from telegram.ext import Application
from bot.services.send_telegram_alert import send_telegram_alert

logger = logging.getLogger(__name__)

async def on_post_shutdown(app: Application) -> None:
    logger.info("PTB app stopped -> sending shutdown alert (sync wrapper)")
    await asyncio.to_thread(
        send_telegram_alert,
        "Realtoken Update Alerts bot: Telegram bot stopped."
    )