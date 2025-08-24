"""
Service layer for the bot.
This package contains reusable services such as:
- I18n: Translation handling
- UserManager: User preferences storage and persistence
- UserPreferences: Data structure for a single user's settings
"""

from .i18n import I18n
from .user_manager import UserManager
from .user_preferences import UserPreferences
from .fetch_json import fetch_json
from .w3_handler import w3_handler

__all__ = [
    "I18n",
    "UserManager",
    "UserPreferences",
    "fetch_json",
    "w3_handler"
]