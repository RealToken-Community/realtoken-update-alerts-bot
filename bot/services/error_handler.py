from __future__ import annotations
from telegram.error import BadRequest

from bot.services.logging_config import get_logger
logger = get_logger(__name__)

async def global_error_handler(update, context):
    """
    Global error handler for the Telegram application.

    Logs harmless 'Message is not modified' errors as INFO including the actual error object.
    """
    err = context.error

    # Log harmless Telegram error as INFO instead of ERROR
    if isinstance(err, BadRequest) and "Message is not modified" in str(err):
        logger.info(f"Telegram BadRequest ignored: {err}")
        return

    # Log all other errors normally (with traceback)
    logger.exception(f"Unhandled error while processing update: {err}", exc_info=err)