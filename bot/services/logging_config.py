# logging_config.py
from __future__ import annotations
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from bot.config.settings import LOG_DIR

# --- Toggle Development Mode -------------------------------------------------
# Set this variable to True to also show INFO and WARNING logs in the console.
# By default (False), only ERROR logs are displayed in the console.
DEVELOPMENT = False

# --- Paths -------------------------------------------------------------------
LOG_DIR.mkdir(parents=True, exist_ok=True)
log_file = LOG_DIR / "realtoken-update-alerts-bot.log"

# --- Formatters --------------------------------------------------------------
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
formatter = logging.Formatter(LOG_FORMAT)

# --- File handler (always on, INFO/WARNING/ERROR) ----------------------------
file_handler = RotatingFileHandler(
    log_file,
    maxBytes=3 * 1024 * 1024,  # 3 MB
    backupCount=10,
    encoding="utf-8",
)
file_handler.setLevel(logging.INFO)  # File captures INFO and above
file_handler.setFormatter(formatter)

# --- Console handler for ERROR (always on) -----------------------------------
console_errors = logging.StreamHandler()
console_errors.setLevel(logging.ERROR)  # Always show errors in console
console_errors.setFormatter(formatter)

# --- Optional console handler for INFO/WARNING (dev only) --------------------
console_dev = logging.StreamHandler()
console_dev.setLevel(logging.INFO)  # Show INFO and above (INFO/WARNING/ERROR)
console_dev.setFormatter(formatter)

# --- Root logger setup -------------------------------------------------------
handlers = [file_handler, console_errors]

if DEVELOPMENT:
    # Add dev console handler only when DEVELOPMENT mode is enabled
    handlers.append(console_dev)

logging.basicConfig(
    level=logging.INFO,
    handlers=handlers,
)

def get_logger(name: str) -> logging.Logger:
    """Return a logger with the given name."""
    return logging.getLogger(name)

# Silence noisy HTTPX request logs, but keep warnings/errors
logging.getLogger("httpx").setLevel(logging.WARNING)

# Log that the config is initialized
get_logger(__name__).info(
    "Logging initialized: file=INFO+, console=ERROR"
    + ("+INFO/WARNING (DEV MODE)" if DEVELOPMENT else "")
)