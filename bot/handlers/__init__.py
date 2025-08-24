"""
Handlers package.
Re-export commonly used handlers so you can do:
    from bot.handlers import set_language, health
"""

from .set_language import set_language, set_language_callback
from .health import health
from .user_notifications_settings import start_user_notifications_settings, handle_notifications_settings_callback, handle_wallet_text, CALLBACK_PREFIX
from .start import start

# If/when you add these, uncomment the lines below:
# from .start import start
# from .language import language

__all__ = [
    "set_language",
    "health",
    "start",
    # "language",
]