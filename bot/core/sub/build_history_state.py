from typing import Any, Dict

HistoryState = Dict[str, Dict[str, Any]]

def build_history_state(payload: Dict[str, Any]) -> HistoryState:
    """
    Create a minimal state from the history endpoint payload, to check new entries easily
    State contains only the number of history entries and the last date per token UUID.

    Example return:
    {
        "0xABC...": {"last_seen_len": 5, "last_seen_date": "20250321"},
        ...
    }
    """
    history_state: HistoryState = {}

    for uuid, item in payload.items() or []:

        history = item.get("history") or []
        # Ensure chronological order
        history_sorted = sorted(history, key=lambda x: x.get("date", ""))

        last_date = history_sorted[-1]["date"] if history_sorted else None
        history_state[uuid] = {
            "last_seen_len": len(history_sorted),
            "last_seen_date": last_date,
        }

    return history_state