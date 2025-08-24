# bot/services/user_manager.py
from __future__ import annotations
import json
from typing import Dict
from pathlib import Path

from bot.config.settings import USER_DATA_PATH
from bot.services.user_preferences import UserPreferences


class UserManager:
    """Manages all users' preferences in memory and persists them to a JSON file."""

    def __init__(self, json_path: Path = USER_DATA_PATH):
        """
        Initialize the manager.

        Args:
            json_path: Path to the JSON file where user configurations are persisted.
        """
        self.json_path = json_path
        self.users: Dict[int, UserPreferences] = {}
        self.load_from_file()

    def load_from_file(self) -> None:
        """Load all users from the JSON file into memory."""
        if not self.json_path.exists():
            self.users = {}
            return

        try:
            with open(self.json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format in {self.json_path}: {e}") from e

        if not isinstance(data, dict):
            raise ValueError(f"Unexpected JSON structure in {self.json_path}: expected an object at root.")

        self.users = {
            int(user_id): UserPreferences.from_dict(int(user_id), prefs)
            for user_id, prefs in data.items()
        }

    def save_to_file(self) -> None:
        """Save the current state of all users to the JSON file (atomic write)."""
        serializable_data = {
            str(user_id): prefs.to_storage_dict()   # <-- exclude inner user_id
            for user_id, prefs in self.users.items()
        }

        self.json_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.json_path.with_suffix(self.json_path.suffix + ".tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(serializable_data, f, ensure_ascii=False, indent=2)
        tmp_path.replace(self.json_path)

    def get_user(self, user_id: int) -> UserPreferences:
        """
        Retrieve a user's preferences from memory.
        If the user does not exist yet, create them with default preferences.
        """
        if user_id not in self.users:
            self.users[user_id] = UserPreferences(user_id=user_id)
            self.save_to_file()
        return self.users[user_id]

    def update_user(self, user_id: int, **kwargs) -> None:
        """
        Update a user's preferences and persist changes.

        Raises:
            AttributeError: if a provided key is not a valid attribute of UserPreferences.
        """
        user = self.get_user(user_id)

        for key, value in kwargs.items():
            if not hasattr(user, key):
                raise AttributeError(f"Unknown user preference: {key}")
            setattr(user, key, value)

        self.save_to_file()
