from typing import Any, Dict, List
from bot.core.sub import build_history_state

import logging
logger = logging.getLogger(__name__)

# Typing:
HistoryState = Dict[str, Dict[str, Any]]
HistoryItem = Dict[str, Any]
TokenPayload = Dict[str, Any]

def get_new_updates(app: Any, current_payload: Dict[str, Any], previous_history_state: HistoryState, new_history_state) -> Dict[str, List[Dict[str, Any]]]:
    """
    Return newly added history items grouped by UUID, but only for UUIDs that already existed
    in the previous baseline and whose history length increased.
    Also:
      - Updates app.bot_data["history_baseline"] with the new baseline.
    Returns:
      Dict[uuid, List[{date, values}]] or {} if nothing to report.
    """

    # Compare and print status (-> we compute a history state because it is easier to check new entries from that than comparing raw payload)
    if new_history_state == previous_history_state:
        return {}

    # Case where there is update:
    updated_uuids: List[str] = []
    for uuid, new_entry in new_history_state.items():
        prev_entry = previous_history_state.get(uuid)
        if prev_entry is None:
            # New UUID -> ignore
            continue
        old_len = int(prev_entry.get("last_seen_len", 0))
        new_len = int(new_entry.get("last_seen_len", 0))
        if new_len > old_len:
            updated_uuids.append(uuid)
        # If new_len < old_len (truncated), ignore for now 
    
    # Early exit if no eligible UUIDs
    if not updated_uuids:
        return {}
    
    histories_by_uuid: Dict[str, List[HistoryItem]] = {}
    for uuid, item in (current_payload.items() or {}):
        histories_by_uuid[uuid] = item.get("history") or []

    # Slice tail items for each impacted UUID and aggregate them into a dict of new histories where each key is a token UUID
    new_history_items_by_uuid: Dict[str, List[Dict[str, Any]]] = {}
    
    for uuid in updated_uuids:
        hist = histories_by_uuid.get(uuid, [])
        if not hist:
            continue
    
        old_len = int(previous_history_state[uuid].get("last_seen_len", 0))
        new_len = int(new_history_state[uuid].get("last_seen_len", 0))
        tail = hist[old_len:new_len]  # only the newly added history items
    
        if not tail:
            continue
    
        # If the UUID key doesn't exist yet, create an empty list
        if uuid not in new_history_items_by_uuid:
            new_history_items_by_uuid[uuid] = []
    
        # Append each new item to the list for this UUID
        for item in tail:
            new_history_items_by_uuid[uuid].append({
                "date": item.get("date", ""),
                "values": item.get("values", {}),
            })
    
    
    logger.info(
        "Detected %d new update(s).",
        len(new_history_items_by_uuid)
    )
    logger.debug(new_history_items_by_uuid)

    return new_history_items_by_uuid