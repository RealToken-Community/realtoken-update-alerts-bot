# bot/handlers/health.py
from __future__ import annotations
from telegram import Update
from telegram.ext import ContextTypes

async def health(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Command handler to confirm the bot is alive."""
    await update.message.reply_text("✅ Bot is running!")
