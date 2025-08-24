
"""Application configuration and constants for this repository layout."""
from __future__ import annotations
import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

FRENQUENCY_CHECKING_FOR_UPDATES = 90 # minutes
FRENQUENCY_WALLET_UPDATE = 1080 # minutes

DEFAULT_LANGUAGE = "English"  # Fallback language

# RealToken public endpoints
REALTOKENS_LIST_URL = "https://api.realtoken.community/v1/token"
REALTOKEN_HISTORY_URL = "https://api.realtoken.community/v1/tokenHistory"

PROJECT_ROOT = Path(__file__).resolve().parents[2]

TRANSLATIONS_PATH = PROJECT_ROOT / "translations" / "translations.json"
USER_DATA_PATH = PROJECT_ROOT / "user_configurations" / "user_configurations.json"
LOG_DIR = PROJECT_ROOT / "logs"


MULTICALLV3_ADDRESS = "0xcA11bde05977b3631167028862bE2a173976CA11"
REALTOKEN_WRAPPER = "0x10497611Ee6524D75FC45E3739F472F83e282AD5"

THRESHOLD_BALANCE_DEC = 0.00001 # balance needed by user to be considered in wallet (in dec)

@dataclass(frozen=True)
class Settings:
    bot_token: str

def get_settings() -> Settings:
    token = os.getenv("BOT_REALTOKENS_UPDATE_ALERTS_TOKEN", "").strip()
    if not token:
        raise RuntimeError("BOT_TOKEN is not set. Define it in environment or .env file.")
    return Settings(bot_token=token)
