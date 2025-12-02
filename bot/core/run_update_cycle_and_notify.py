import logging
logger = logging.getLogger(__name__)

from telegram.ext import Application
from telegram.constants import ParseMode
from telegram.error import Forbidden, TelegramError
from bot.services import fetch_json
from bot.config.settings import REALTOKENS_LIST_URL, REALTOKEN_HISTORY_URL
from bot.services.utilities import list_to_dict_by_uuid
from bot.core.sub import get_new_updates, build_lines_messages, build_history_state, filter_messages

import re

async def run_update_cycle_and_notify(app: Application) -> None:
    """
    Orchestrates the process of checking for RealToken updates and sending notifications.
    """
    user_manager = app.bot_data["user_manager"]
    i18n = app.bot_data["i18n"]

    ### Fetch Realtoken data and Realtoken history from community API ###
    realtoken_data_last = app.bot_data["realtokens"]
    realtoken_data_current = list_to_dict_by_uuid(fetch_json(REALTOKENS_LIST_URL))
    logger.info(f"realtoken data updated: {len(realtoken_data_current) if realtoken_data_current is not None else None} realtokens fetched")

    if realtoken_data_current is not None:
        realtoken_data = realtoken_data_current
        app.bot_data["realtokens"] = realtoken_data
    else:
        realtoken_data = realtoken_data_last

    realtoken_history_data_last = app.bot_data["realtoken_history"]
    realtoken_history_state_last = app.bot_data["realtoken_history_state"]
    realtoken_history_data_current = list_to_dict_by_uuid(fetch_json(REALTOKEN_HISTORY_URL))
    
    # If API not available or parsing failed, stop the cycle gracefully
    if realtoken_history_data_current is None:
        logger.warning("Realtoken history data not fetched (API might be unavailable). Skipping update cycle.")
        return
    
    realtoken_history_state_current = build_history_state(realtoken_history_data_current)
    new_history_items_by_uuid = get_new_updates(app, realtoken_history_data_current, realtoken_history_state_last, realtoken_history_state_current, realtoken_data)
     
    # Loop over user IDs and preferences and filter messages if there is at least a new item
    if len(new_history_items_by_uuid) > 0:
        for user_id, prefs in user_manager.users.items():
    
            lines_messages = build_lines_messages(new_history_items_by_uuid, realtoken_data, realtoken_history_data_last, user_manager, i18n, user_id)
    
            message = filter_messages(lines_messages, user_id, prefs.notification_types, prefs.token_scope)
    
            if message and message.strip():  # ensures the string has at least one non-whitespace character
                try:
                    await app.bot.send_message(
                        chat_id=user_id,
                        text=re.sub(r'([.\-()])', r'\\\1', message),
                        parse_mode=ParseMode.MARKDOWN_V2,
                    )
                except Forbidden as e:
                    # User blocked the bot
                    logger.warning(
                        "User %s blocked the bot. Error: %s",
                        user_id,
                        e,
                    )
                    continue
                except TelegramError as e:
                    # Any other Telegram-related error should not break the whole job
                    logger.warning(
                        "Failed to send message to user %s: %s",
                        user_id,
                        e,
                    )
                    continue

    # update new realtoken history
    app.bot_data["realtoken_history_state"] = realtoken_history_state_current
    app.bot_data["realtoken_history"] = realtoken_history_data_current

    logger.info(f"Update cycle completed: {len(new_history_items_by_uuid)} tokens updated")