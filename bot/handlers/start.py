from __future__ import annotations
from telegram import Update
from telegram.ext import ContextTypes

from bot.handlers import set_language
from bot.services.logging_config import get_logger

logger = get_logger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    user_id = user.id if user else "UNKNOWN"

    # Log user start event
    logger.info(f"User {user_id} started the bot.")

    await set_language(update, context)