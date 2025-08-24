# bot/handlers/start.py
from __future__ import annotations
from telegram import Update
from telegram.ext import ContextTypes

from bot.handlers import set_language

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await set_language(update, context)
