import logging
logger = logging.getLogger(__name__)

def filter_messages(lines_messages, user_id, notification_types, token_scope):
    """
    Build the final message by concatenating only non-empty lines.
    Ensures at most one blank line between blocks.
    """
    message_parts = []

    def push(line: str) -> None:
        """Append a line only if it is a non-empty, non-whitespace string."""
        if isinstance(line, str) and line.strip():
            message_parts.append(line + "\n")

    for lines_message in lines_messages:
        
        if token_scope['mode'] == 'wallet' and lines_message['uuid'].lower() not in token_scope['realtokens_owned']:
            continue

        # Header
        push(lines_message['header_line'])

        # Conditionally add lines (each may be empty; push() filters them)
        if notification_types["income_updates"]:
            push(lines_message["yield_income_new_valuation_line"])
            push(lines_message["yield_income_initial_valuation_line"])
        if notification_types["price_token_updates"]:
            push(lines_message["tokenPrice_line"])
        if notification_types["other_updates"]:
            push(lines_message["annual_income_line"])
            push(lines_message["underlyingAssetPrice_line"])
            push(lines_message["initialMaintenanceReserve_line"])
            push(lines_message["renovationReserve_line"])
            push(lines_message["rentedUnits_line"])

        # remove header if there is no line that have been pushed and that header is the only item (so the last)
        if message_parts[-1][:len(lines_message['header_line'])] == lines_message['header_line']:
            message_parts.pop()

        message_parts.append("")

    # Remove trailing blank line if present
    if message_parts and message_parts[-1] == "":
        message_parts.pop()

    return "\n".join(message_parts)