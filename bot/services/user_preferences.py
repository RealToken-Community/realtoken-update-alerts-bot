from bot.config.settings import DEFAULT_LANGUAGE

class UserPreferences:
    """Represents a single user's preferences."""

    def __init__(self, user_id: int, language: str = DEFAULT_LANGUAGE,
                 notification_types=None, token_scope=None):
        self.user_id = user_id
        self.language = language

        # Set default notification types if none provided
        self.notification_types = notification_types or {
            "income_updates": True,
            "price_token_updates": True,
            "other_updates": False
        }

        # Set default token scope if none provided
        self.token_scope = token_scope or {
            "mode": "all",   # "all" or "wallets"
            "wallets": [],
            "realtokens_owned": []
        }

    def to_storage_dict(self) -> dict:
        """Dict for JSON storage (exclude the primary key user_id)."""
        return {
            "language": self.language,
            "notification_types": self.notification_types,
            "token_scope": self.token_scope
        }

    @classmethod
    def from_dict(cls, user_id: int, data: dict) -> "UserPreferences":
        """Create from stored dict."""
        data = dict(data) if data else {}
        return cls(
            user_id=user_id,
            language=data.get("language", DEFAULT_LANGUAGE),
            notification_types=data.get("notification_types"),
            token_scope=data.get("token_scope")
        )
