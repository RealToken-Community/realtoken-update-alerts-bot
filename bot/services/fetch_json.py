import requests
from typing import Any, Optional
from bot.services.logging_config import get_logger
logger = get_logger(__name__)


def fetch_json(url: str, timeout: int = 20) -> Optional[Any]:
    """
    Fetch JSON from a URL and return it as Python data.
    Returns None if the request fails or if JSON is invalid.
    """
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        logger.warning("Failed to fetch JSON from %s: %s", url, e)
        return None
