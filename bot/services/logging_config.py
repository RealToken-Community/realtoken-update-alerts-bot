from __future__ import annotations
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from bot.config.settings import LOG_DIR

LOG_DIR.mkdir(parents=True, exist_ok=True)
log_file = LOG_DIR / "realtoken-update-alerts-bot.log"

# --- File Handler (INFO and above) ---
file_handler = RotatingFileHandler(
    log_file,
    maxBytes=3 * 1024 * 1024,  # 3 MB
    backupCount=10,            # keep last 10 logs
    encoding="utf-8"
)
file_handler.setLevel(logging.INFO)

# --- Console Handler for ERRORS (always active) ---
console_handler_errors = logging.StreamHandler()
console_handler_errors.setLevel(logging.ERROR)

# --- Optional Console Handler for INFO/DEBUG (dev only) ---
# Uncomment during development to also see INFO in console
# console_handler_info = logging.StreamHandler()
# console_handler_info.setLevel(logging.INFO)

# --- Base logging config ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        file_handler,
        console_handler_errors,
        # console_handler_info,  # <--- Uncomment to show INFO in console
    ],
)

def get_logger(name: str) -> logging.Logger:
    """Return a logger with the given name."""
    return logging.getLogger(name)

# Silence noisy HTTPX request logs, but keep warnings/errors
logging.getLogger("httpx").setLevel(logging.WARNING)

# Log that the config is initialized
get_logger(__name__).info("Logging initialized with rotation (max 10 files, 3MB each).")
