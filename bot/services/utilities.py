from typing import Any, Dict, List, Iterable, Optional
from bot.config.settings import THRESHOLD_BALANCE_DEC
from bot.services.logging_config import get_logger
logger = get_logger(__name__)

def list_to_dict_by_uuid(items: Optional[List[Dict[str, Any]]]) -> Optional[Dict[str, Dict[str, Any]]]:
    """
    Convert a list of dictionaries into a dictionary keyed by the 'uuid' value.

    Args:
        items: A list of dictionaries, each expected to contain a 'uuid' key.
               If None, returns None.

    Returns:
        - None if input is None.
        - Otherwise, a dictionary where:
            * Keys are the 'uuid' values from the input dictionaries.
            * Values are the corresponding full dictionaries from the list.
        Entries without a 'uuid' key or with a falsy 'uuid' value are ignored.
    """
    if items is None:
        return None

    result: Dict[str, Dict[str, Any]] = {}
    for item in items:
        uuid = item.get("uuid")
        if not uuid:
            continue
        result[uuid] = item
    return result





def get_latest_value_for_key(
    item: Dict[str, Any],
    key: str,
    *,
    default: Any = None,
    return_date: bool = False
) -> Any:
    """
    Return the most recent value for `key` found inside the nested `values` dicts
    of the `history` list in `item`.

    The function sorts history entries by their 'date' (format 'YYYYMMDD') in
    descending order, and returns the first occurrence where `key` is present
    in `values`. If the key never appears, `default` is returned.

    Args:
        item: A dictionary with at least a 'history' key holding a list of entries.
              Each entry is a dict that should contain 'date' (YYYYMMDD as str)
              and 'values' (a dict of fields like 'netRentYear', 'tokenPrice', etc.).
        key: The field name to look up inside each entry's 'values'.
        default: Value to return if `key` is never found.
        return_date: If True, return a tuple (value, date_str). Otherwise, return the value.

    Returns:
        The latest value for `key` (or (value, date_str) if return_date=True),
        or `default` if the key is not found in any entry.
    """
    history: Iterable[Dict[str, Any]] = item.get("history") or []

    # Sort by date descending. String sort works for 'YYYYMMDD' safely.
    # Entries without a 'date' fall to the end.
    history_sorted = sorted(
        history,
        key=lambda h: h.get("date") or "",
        reverse=True,
    )

    for entry in history_sorted:
        values: Dict[str, Any] = entry.get("values") or {}
        if key in values:
            return (values[key], entry.get("date")) if return_date else values[key]

    return (default, None) if return_date else default


import json
from typing import Dict, Any


def load_abis(path: str = "ressources/abi.json") -> Dict[str, Any]:
    """
    Load contract ABIs from a JSON file.

    Args:
        path (str): Path to the ABI JSON file. Defaults to "ressources/abi.json".

    Returns:
        Dict[str, Any]: Dictionary mapping contract names to their ABI definitions.
                        Example: {"realtoken-wrapper": [...], "multicall3": [...]}
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            abis = json.load(f)
        logger.info("ABIs successfully loaded from %s", path)
        return abis

    except FileNotFoundError:
        logger.error("ABI file not found at %s", path)
        raise
    except json.JSONDecodeError as e:
        logger.error("Invalid JSON in ABI file %s: %s", path, e)
        raise
    except Exception as e:
        logger.error("Unexpected error while loading ABIs from %s: %s", path, e)
        raise

User   = str   # checksum address
Token  = str   # checksum address
Amount = int

def merge_user_token_balances(
    dictionaries: Iterable[Dict[User, Dict[Token, Amount]]]
) -> Dict[User, Dict[Token, Amount]]:
    """
    Merge multiple {user: {token: balance}} dicts.
    If the same (user, token) appears in multiple dicts, balances are summed.

    Args:
        dictionaries: iterable of balance dicts (e.g., [balances_realtoken_wrapper, balances_realtokens]).
    Returns:
        A new merged dict; inputs are NOT mutated.
        Users are always kept, even if their token map becomes empty.
    """
    merged: Dict[User, Dict[Token, Amount]] = {}

    for d in dictionaries:
        if not d:
            continue
        for user, tok_map in d.items():
            dest = merged.setdefault(user, {})
            if not tok_map:
                continue
            for token, amount in tok_map.items():
                dest[token] = dest.get(token, 0) + int(amount)

    if THRESHOLD_BALANCE_DEC > 0:
        for user in merged:
            merged[user] = {
                t: a for t, a in merged[user].items()
                if a >= THRESHOLD_BALANCE_DEC * 10**18
            }
            # We keep an empty dict if there are no balances in a wallet

    return merged


# test cases 
if __name__ == '__main__':
    import json
    with open("tokenHistory_testing.json", "r", encoding="utf-8") as f:
        realtoken_history_data = json.load(f)
    realtoken_history_data_last = list_to_dict_by_uuid(realtoken_history_data)
    last_tokenPrice = get_latest_value_for_key(realtoken_history_data_last['0x140d6cfde793f1a2eed5274454aa6f463ec8c075'], 'tokenPrice')
    print(last_tokenPrice)
