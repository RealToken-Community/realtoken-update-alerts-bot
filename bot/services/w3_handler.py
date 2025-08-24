from __future__ import annotations

from bot.services.logging_config import get_logger
logger = get_logger(__name__)

from typing import Callable, Any, List
from functools import lru_cache
import time
import os, json

from web3 import Web3

from dotenv import load_dotenv

load_dotenv()


# -----------------------------
# Internal helpers
# -----------------------------

@lru_cache(maxsize=1)
def _load_rpc_urls() -> List[str]:
    raw = os.getenv("RPC_URLS", "").strip()
    if not raw:
        raise RuntimeError("RPC_URLS missing")
    try:
        urls = json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"RPC_URLS is not valid JSON: {e}")
    if not isinstance(urls, list) or not all(isinstance(u, str) for u in urls):
        raise RuntimeError("RPC_URLS must be a JSON array of strings")
    return urls


@lru_cache(maxsize=1)
def _build_w3_list() -> List[Web3]:
    """Build and cache Web3 objects once for all decorated calls."""
    urls = _load_rpc_urls()
    return [Web3(Web3.HTTPProvider(u)) for u in urls]


# -----------------------------
# The decorator
# -----------------------------

def w3_handler(
    *,
    attempts_per_w3: int = 4,
    retry_delay_sec: float = 2,
    restart_on_all_fail: bool = False,
    restart_delay_sec: float = 120.0,
) -> Callable:
    def decorator(fn: Callable) -> Callable:
        def wrapper(*args, **kwargs) -> Any:
            while True:
                for url, w3 in zip(_load_rpc_urls(), _build_w3_list()):
                    for attempt in range(1, attempts_per_w3 + 1):
                        try:
                            return fn(w3, *args, **kwargs)
                        except Exception as e:
                            if attempt < attempts_per_w3:
                                logger.warning(
                                    f"[w3_handler] RPC {url} failed (attempt {attempt}/{attempts_per_w3}): {e}. Retrying..."
                                )
                                time.sleep(retry_delay_sec)
                            else:
                                logger.info(
                                    f"[w3_handler] RPC {url} exhausted after {attempts_per_w3} attempts. Switching to next..."
                                )
                                # on break pour passer au prochain w3
                                break
                if restart_on_all_fail:
                    logger.error(
                        f"[w3_handler] All RPC endpoints failed. Waiting {restart_delay_sec}s before retrying from the first..."
                    )
                    time.sleep(restart_delay_sec)
                    continue
                raise RuntimeError("w3_handler: All RPC endpoints failed for this call.")
        return wrapper
    return decorator
