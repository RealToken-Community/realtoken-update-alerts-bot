from __future__ import annotations

from bot.services.logging_config import get_logger
logger = get_logger(__name__)

from typing import Callable, Any, List, Dict
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


# Cooldown registry: url -> unix timestamp until which it is disabled
_RPC_COOLDOWN_UNTIL: Dict[str, float] = {}


# -----------------------------
# The decorator
# -----------------------------

def w3_handler(
    *,
    attempts_per_w3: int = 4,
    retry_delay_sec: float = 10,
    restart_on_all_fail: bool = False,
    restart_delay_sec: float = 600.0,
    cooldown_after_exhaust_sec: float = 6000.0,
) -> Callable:
    """
    Decorator to inject a Web3 instance and provide RPC failover.

    New behavior:
      - When an RPC URL is exhausted (all attempts_per_w3 failed),
        it can be put on cooldown for `cooldown_after_exhaust_sec` seconds.
      - While on cooldown, that URL will be skipped for all decorated calls.
    """
    def decorator(fn: Callable) -> Callable:
        def wrapper(*args, **kwargs) -> Any:
            while True:
                urls = _load_rpc_urls()
                w3_list = _build_w3_list()

                now = time.time()
                any_tried = False

                for url, w3 in zip(urls, w3_list):
                    # Check whether this URL is in cooldown
                    cooldown_until = _RPC_COOLDOWN_UNTIL.get(url, 0.0)
                    if cooldown_until > now:
                        logger.warning(
                            f"[w3_handler] Skipping RPC {url} (in cooldown for another "
                            f"{int(cooldown_until - now)}s)."
                        )
                        continue

                    any_tried = True
                    for attempt in range(1, attempts_per_w3 + 1):
                        try:
                            return fn(w3, *args, **kwargs)
                        except Exception as e:
                            if attempt < attempts_per_w3:
                                logger.warning(
                                    f"[w3_handler] RPC {url} failed (attempt {attempt}/{attempts_per_w3}): {e}. "
                                    f"Retrying in {retry_delay_sec}s..."
                                )
                                time.sleep(retry_delay_sec)
                            else:
                                logger.warning(
                                    f"[w3_handler] RPC {url} exhausted after {attempts_per_w3} attempts."
                                )
                                # Put this URL in cooldown if configured
                                if cooldown_after_exhaust_sec > 0:
                                    _RPC_COOLDOWN_UNTIL[url] = time.time() + cooldown_after_exhaust_sec
                                    logger.warning(
                                        f"[w3_handler] RPC {url} disabled for "
                                        f"{int(cooldown_after_exhaust_sec)} seconds."
                                    )
                                # Break to try the next URL (if any)
                                break

                # If no URL was eligible (all in cooldown), we treat this as "all endpoints failed"
                if not any_tried:
                    logger.error("[w3_handler] All RPC endpoints are currently in cooldown.")

                if restart_on_all_fail:
                    logger.error(
                        f"[w3_handler] All RPC endpoints failed or are in cooldown. "
                        f"Waiting {restart_delay_sec}s before retrying from the first..."
                    )
                    time.sleep(restart_delay_sec)
                    continue

                raise RuntimeError("w3_handler: All RPC endpoints failed for this call.")
        return wrapper
    return decorator