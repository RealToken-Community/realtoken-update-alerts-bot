from __future__ import annotations
import asyncio
from web3 import Web3
from telegram.ext import ContextTypes
from bot.balances import get_balances_of_realtokens, get_balances_of_realtoken_wrapper
from bot.config.settings import THRESHOLD_BALANCE_DEC

def update_realtokens_owned_single_wallet(context: ContextTypes.DEFAULT_TYPE, addr_norm: str, user_id: int, user_manager) -> None:
    """
    Synchronous worker that will run in a background thread.
    For now, it simply prints 'OK'. Later, you'll put the RealToken logic here.
    """

    abis = context.application.bot_data['abis']
    realtokens_list = context.application.bot_data['realtokens']

    realtokens_uuid = [
        uuid
        for uuid, data in realtokens_list.items()
        if data.get("gnosisContract") is not None
    ]

    balances_realtokens = get_balances_of_realtokens(
        users_addresses=[addr_norm],
        realtoken_contract_addresses=realtokens_uuid,
        abi_realtoken=abis["realtoken"],
        abi_multicall3=abis["multicall3"],
    )

    balances_wrapper = get_balances_of_realtoken_wrapper(
        users_addresses=[addr_norm],
        abi_realtoken_wrapper=abis["realtoken-wrapper"],
        abi_multicall3=abis["multicall3"],
    )

    new_realtokens_owned = set()

    addr_checksum = Web3.to_checksum_address(addr_norm)

    for realtoken, balance in balances_realtokens[addr_checksum].items():
        if balance > THRESHOLD_BALANCE_DEC * 10**18:
            new_realtokens_owned.add(realtoken)
    
    for realtoken, balance in balances_wrapper[addr_checksum].items():
        if balance > THRESHOLD_BALANCE_DEC * 10**18:
            new_realtokens_owned.add(realtoken)

    # Fetch user preferences object
    user_prefs = user_manager.get_user(user_id)
    current_scope = user_prefs.token_scope

    # Normalize everything to lowercase
    new_realtokens_owned = {rt.lower() for rt in new_realtokens_owned}
    previous_realtokens_owned = {rt.lower() for rt in current_scope.setdefault("realtokens_owned", [])}

    # Merge and save back
    merged_realtokens_owned = list(previous_realtokens_owned.union(new_realtokens_owned))

    # Build updated scope
    new_token_scope = {
        **current_scope,
        "realtokens_owned": merged_realtokens_owned
    }

    # Update via manager (persists to file automatically)
    user_manager.update_user(user_id, token_scope=new_token_scope)


def trigger_update_realtokens_owned_single_wallet(
    context: ContextTypes.DEFAULT_TYPE,
    addr_norm: str,
    user_id: int,
    user_manager,
) -> None:
    """
    Fire-and-forget launcher. It schedules the synchronous worker
    into a background thread without blocking the event loop.
    """

    # Schedule the worker to run in a thread and return immediately.
    context.application.create_task(
        asyncio.to_thread(update_realtokens_owned_single_wallet, context, addr_norm, user_id, user_manager)
    )
