from __future__ import annotations
from datetime import timedelta

from bot.services.logging_config import get_logger
logger = get_logger("bot.main")

from telegram.ext import Application, CommandHandler, CallbackQueryHandler, JobQueue, MessageHandler, filters

from bot.core.sub import build_history_state

from bot.config.settings import get_settings, REALTOKENS_LIST_URL, REALTOKEN_HISTORY_URL, FRENQUENCY_CHECKING_FOR_UPDATES, FRENQUENCY_WALLET_UPDATE
from bot.services import I18n, UserManager, fetch_json
from bot.services.utilities import list_to_dict_by_uuid, load_abis
from bot.services.error_handler import global_error_handler
from bot.services.send_telegram_alert import send_telegram_alert
from bot.services.on_post_shutdown import on_post_shutdown
from bot.task.job import job_update_and_notify, job_update_realtoken_owned
from bot.handlers import (
    health,
    start,
    set_language,
    set_language_callback,
    start_user_notifications_settings,
    handle_notifications_settings_callback,
    handle_wallet_text,
    CALLBACK_PREFIX
)

def main() -> None:
    settings = get_settings()

    # Create the UserManager instance and load all user data
    user_manager = UserManager()  # default path = USER_DATA_PATH
    
    # Create the I18n instance and load translations from JSON
    i18n = I18n()

    # Build the Telegram application
    jq = JobQueue()
    app = (
        Application.builder()
        .token(settings.bot_token)
        .job_queue(jq)
        .post_shutdown(on_post_shutdown)
        .build()
    )

    # Fetch RealToken data (as-is from the API)
    realtoken_data = list_to_dict_by_uuid(fetch_json(REALTOKENS_LIST_URL) or [])
    realtoken_history_data = list_to_dict_by_uuid(fetch_json(REALTOKEN_HISTORY_URL) or [])

    # Loads ABIs
    abis = load_abis()

    # Store services in bot_data so all handlers can access them
    app.bot_data["user_manager"] = user_manager
    app.bot_data["i18n"] = i18n
    app.bot_data["realtokens"] = realtoken_data
    app.bot_data["realtoken_history"] = realtoken_history_data
    app.bot_data["realtoken_history_state"] = build_history_state(realtoken_history_data)
    app.bot_data["abis"] = abis   

    # Register handlers 
    app.add_handler(CommandHandler("health", health)) # check if the bot is running
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setlanguage", set_language))
    app.add_handler(CommandHandler("notification_settings", start_user_notifications_settings))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_wallet_text))

    # Resgister callback
    app.add_handler(CallbackQueryHandler(set_language_callback, pattern=r"^lang_.+"))
    app.add_handler(CallbackQueryHandler(handle_notifications_settings_callback, pattern=f"^{CALLBACK_PREFIX}:"))

    # Register the global error handler
    app.add_error_handler(global_error_handler)

    # register job to trigger run_update_cycle_and_notify every FRENQUENCY_CHECKING_FOR_UPDATES 
    app.job_queue.run_repeating(
        job_update_and_notify,
        interval=timedelta(minutes=FRENQUENCY_CHECKING_FOR_UPDATES),
        first=timedelta(seconds=60),
        name="realtoken_update_and_notify_cycle",
    )
    # register job to update users' realtoken owned every FRENQUENCY_WALLET_UPDATE 
    app.job_queue.run_repeating(
        job_update_realtoken_owned,
        interval=timedelta(minutes=FRENQUENCY_WALLET_UPDATE),
        first=timedelta(seconds=300),
        name="realtoken_in_wallet_update",
    )
    
    logger.info("Starting bot polling…")
    print("Starting bot polling…")
    send_telegram_alert("realtoken update alert bot: Starting bot polling…")
    app.run_polling()


if __name__ == "__main__":
    main()


# ----------------------------------------------------------------------
# TESTING ONLY
# The section below can override realtoken_history_data with a local file instead of API call.
# This block simulates API history changes during development and can be copy/paste higher in the code
# Remove or comment this out in production!
# ----------------------------------------------------------------------
#import json
#with open("tokenHistory_testing.json", "r", encoding="utf-8") as f:
#    realtoken_history_data = list_to_dict_by_uuid(json.load(f))
