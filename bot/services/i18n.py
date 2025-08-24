# bot/services/i18n.py
from __future__ import annotations
import json
from typing import Any, Dict, Optional

from bot.config.settings import TRANSLATIONS_PATH, DEFAULT_LANGUAGE


class I18n:
    """Loads translations and resolves keys by language with default-language fallback."""

    def __init__(self):
        self._translations: Dict[str, Dict[str, str]] = {}
        self._load()

    def _load(self) -> None:
        """Load the translations JSON into memory."""
        if not TRANSLATIONS_PATH.exists():
            raise FileNotFoundError(f"Translations file not found at {TRANSLATIONS_PATH}")

        try:
            with open(TRANSLATIONS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format in {TRANSLATIONS_PATH}: {e}")

        if not isinstance(data, dict) or not data:
            raise ValueError(f"No valid languages found in {TRANSLATIONS_PATH}")

        # Expected shape: { "English": { "KEY": "text" }, "Français": { ... } }
        self._translations = data

    def translate(self, key: str, lang: Optional[str] = None, **fmt: Any) -> str:
        """
        Translate a key using the provided language, falling back to the default language.
        Raises KeyError if the key does not exist in the target language nor in the default language.
        """
        language = lang or DEFAULT_LANGUAGE
        text = self._resolve_key(key, language)
        return text.format(**fmt) if fmt else text

    def translate_for_user(self, key: str, user_id: int, user_manager, **fmt: Any) -> str:
        """
        Translate a key using a user's language obtained from UserManager.
        Falls back to the default language if the key is missing in the user's language.
        Raises KeyError if the key is missing everywhere.
        """
        prefs = user_manager.get_user(user_id)
        return self.translate(key, prefs.language, **fmt)

    def _resolve_key(self, key: str, lang: str) -> str:
        """
        Return the translation for `key` in `lang`, or fallback to DEFAULT_LANGUAGE.
        Raise KeyError if the key is not present in either.
        """
        # Try the requested language first
        lang_map = self._translations.get(lang, {})
        if key in lang_map:
            return lang_map[key]

        # Fallback to default language
        default_map = self._translations.get(DEFAULT_LANGUAGE, {})
        if key in default_map:
            return default_map[key]

        # Not found anywhere -> raise
        raise KeyError(
            f"Missing translation for key='{key}' in lang='{lang}' "
            f"and in default='{DEFAULT_LANGUAGE}'"
        )
