import requests, time
from typing import Any, Optional
from bot.services.logging_config import get_logger
logger = get_logger(__name__)

def fetch_json(url: str, timeout: int = 20) -> Optional[Any]:
    """Fetch JSON with basic cache-busting to avoid stale CDN responses."""
    try:
        headers = {
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Accept": "application/json",
            "User-Agent": "RealtokenUpdateAlertsBot/1.0",
        }
        params = {"_": str(int(time.time()))}  # cache-buster
        resp = requests.get(url, headers=headers, params=params, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        logger.warning("Failed to fetch JSON from %s: %s", url, e)
        return None
