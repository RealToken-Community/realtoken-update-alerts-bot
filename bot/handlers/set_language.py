# bot/handlers/set_language.py
from __future__ import annotations
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    BotCommand,
    BotCommandScopeChat,
)
from telegram.ext import ContextTypes

CALLBACK_PREFIX = "lang_"


async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show language choices and prompt in the user's current language."""
    user_manager = context.bot_data["user_manager"]
    i18n = context.bot_data["i18n"]

    # Build buttons directly from loaded translation languages
    languages = list(i18n._translations.keys())
    keyboard = [[InlineKeyboardButton(lang, callback_data=f"{CALLBACK_PREFIX}{lang}")]
                for lang in languages]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Prompt in user's current language (falls back to default internally)
    user_id = update.effective_user.id
    prompt_select_language = i18n.translate_for_user("select_language_prompt", user_id, user_manager)
    
    await update.message.reply_text(prompt_select_language, reply_markup=reply_markup)

async def _apply_user_custom_menu(
    context: ContextTypes.DEFAULT_TYPE, chat_id: int, lang: str
) -> None:
    """Create a per-chat custom command menu translated in the selected language.

    This sets commands only for the current chat scope so it affects this user
    without changing the global/default command list.
    """
    i18n = context.bot_data["i18n"]

    # Translate command descriptions using the selected language.
    # If a key is missing, your i18n module should fall back to default language.
    notif_desc = i18n.translate("menu.notification_settings", lang)
    setlang_desc = i18n.translate("menu.set_language", lang)

    commands = [
        BotCommand(command="notification_settings", description=notif_desc),
        BotCommand(command="setlanguage", description=setlang_desc),
    ]

    # Apply the commands for this specific chat.
    # We also pass lang so Telegram can show it appropriately if needed.
    await context.bot.set_my_commands(
        commands=commands,
        scope=BotCommandScopeChat(chat_id)
    )


async def set_language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Persist the selected language and confirm in that language."""
    query = update.callback_query
    await query.answer()

    user_manager = context.bot_data["user_manager"]
    i18n = context.bot_data["i18n"]

    # Extract the selected language from callback data
    selected_lang = (query.data or "")[len(CALLBACK_PREFIX):]

    # Save to memory + JSON via UserManager
    user_id = update.effective_user.id
    user_manager.update_user(user_id, language=selected_lang)

    # Create a per-chat custom menu translated in the new language
    chat_id = update.effective_chat.id
    await _apply_user_custom_menu(context, chat_id, selected_lang)

    # Confirm in the newly selected language
    confirmation = i18n.translate("language_set", selected_lang)
    prompt_ready = i18n.translate_for_user("ready", user_id, user_manager)
    await query.edit_message_text(confirmation + "\n" + prompt_ready)
