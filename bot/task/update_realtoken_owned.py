from typing import List
from telegram.ext import Application
from bot.balances import get_balances_of_realtokens, get_balances_of_realtoken_wrapper
from bot.services.utilities import merge_user_token_balances

from web3 import Web3

from bot.services.logging_config import get_logger
logger = get_logger(__name__)

async def update_realtoken_owned(app: Application) -> None:
    """
    Collect all unique wallets from all users' token_scope.
    """
    user_manager = app.bot_data["user_manager"]
    abis = app.bot_data['abis']
    realtokens_list = app.bot_data['realtokens']

    # Build a set to guarantee uniqueness
    wallets_set = set()

    for user in user_manager.users.values():
        token_scope = getattr(user, "token_scope", None)
        if not token_scope:
            continue

        wallets: List[str] = token_scope.get("wallets", [])
        for w in wallets:
            if w:
                wallets_set.add(w)

    # Convert back to list if needed
    unique_wallets: List[str] = list(wallets_set)

    realtokens_uuid = [
        uuid
        for uuid, data in realtokens_list.items()
        if data.get("gnosisContract") is not None
    ]

    balances_realtokens = get_balances_of_realtokens(
        users_addresses=unique_wallets,
        realtoken_contract_addresses=realtokens_uuid,
        abi_realtoken=abis["realtoken"],
        abi_multicall3=abis["multicall3"],
    )

    balances_wrapper = get_balances_of_realtoken_wrapper(
        users_addresses=unique_wallets,
        abi_realtoken_wrapper=abis["realtoken-wrapper"],
        abi_multicall3=abis["multicall3"],
    )

    all_balances = merge_user_token_balances([balances_realtokens, balances_wrapper])

    for user_id, prefs in user_manager.users.items():

        realtoken_owned_user = set()
        for wallet in prefs.token_scope["wallets"]:

            wallet = Web3.to_checksum_address(wallet)
            for token in all_balances[wallet].keys():
                realtoken_owned_user.add(token.lower())
        prefs.token_scope["realtokens_owned"] = list(realtoken_owned_user)
    
    user_manager.save_to_file()

    logger.info(f'Realtoken owned updated for {len(unique_wallets)} wallets')
