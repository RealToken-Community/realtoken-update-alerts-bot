import time
from typing import List, Dict, Tuple
from web3 import Web3
from web3.contract import Contract
from hexbytes import HexBytes
from bot.services import w3_handler
from bot.config.settings import MULTICALLV3_ADDRESS


def _encode_balance_of_calls(
    w3: Web3,
    users: List[str],
    tokens: List[str],
    erc20_abi: List[Dict],
) -> List[Tuple[str, bytes, str, str]]:
    """
    Build the (target, callData) list for balanceOf(user) for every (user, token) pair.
    Returns a list of tuples: (token_address, call_data_bytes, user_address, token_address)
    """
    token_contracts: Dict[str, Contract] = {
        w3.to_checksum_address(token): w3.eth.contract(address=w3.to_checksum_address(token), abi=erc20_abi)
        for token in tokens
    }

    calls: List[Tuple[str, bytes, str, str]] = []
    for user in users:
        user_checksum = w3.to_checksum_address(user)
        for token in tokens:
            token_checksum = w3.to_checksum_address(token)
            token_contract = token_contracts[token_checksum]
            # Web3.py 7.x: encode calldata via _encode_transaction_data()
            hex_data = token_contract.functions.balanceOf(user_checksum)._encode_transaction_data()
            call_data_bytes = HexBytes(hex_data)  # raw bytes for Multicall3
            calls.append((token_checksum, call_data_bytes, user_checksum, token_checksum))
    return calls


def _decode_uint256_or_zero(data: bytes) -> int:
    """
    Decode a uint256 from 32-byte ABI output. Return 0 on bad/empty data.
    Using int.from_bytes is version-agnostic and fast.
    """
    if not data:
        return 0
    try:
        return int.from_bytes(data, byteorder="big", signed=False)
    except Exception as error:
        print(f"[decode] failed: {error}. raw=0x{data.hex()}")
        return 0


def _split_into_batches(items, batch_size: int):
    """Yield consecutive slices (batches) from items with at most batch_size elements each."""
    for start in range(0, len(items), batch_size):
        yield items[start:start + batch_size]

@w3_handler()
def get_balances_of_realtokens(
    w3: Web3,
    users_addresses: List[str],
    realtoken_contract_addresses: List[str],
    abi_realtoken: List[Dict],
    abi_multicall3: List[Dict],
    *,
    max_subcalls_per_multicall: int = 10000,
) -> Dict[str, Dict[str, int]]:
    """
    Query balanceOf for each user across all given RealToken contracts using Multicall3.

    - Batching: we split the (user, token) calls into chunks of size <= max_subcalls_per_multicall.
    - Each chunk is sent via tryAggregate(requireSuccess=False) so a failing sub-call doesn't revert the batch.
    - No retries, no extra safeguards: intentionally simple and straightforward.

    Args:
        w3: Web3 instance.
        users_addresses: list of user addresses.
        realtoken_contract_addresses: list of ERC20 token addresses (RealToken).
        abi_realtoken: ERC20 ABI (must contain balanceOf(address)).
        abi_multicall3: Multicall3 ABI (must contain tryAggregate(bool,(address,bytes)[])).
        max_subcalls_per_multicall: max number of sub-calls per multicall (default 1000).

    Returns:
        { user_checksum: { token_checksum: raw_balance_int } }
    """
    # Output skeleton with checksum addresses
    balances_result: Dict[str, Dict[str, int]] = {
        w3.to_checksum_address(user): {} for user in users_addresses
    }

    # Prepare all sub-calls (one per (user, token) pair)
    prepared_calls = _encode_balance_of_calls(
        w3, users_addresses, realtoken_contract_addresses, abi_realtoken
    )
    if not prepared_calls:
        return balances_result

    multicall_contract = w3.eth.contract(
        address=w3.to_checksum_address(MULTICALLV3_ADDRESS),
        abi=abi_multicall3,
    )

    # Process in batches to avoid oversized payloads
    for call_batch in _split_into_batches(prepared_calls, max_subcalls_per_multicall):
        # Multicall3 expects a list of (target, callData) tuples
        payload = [
            (token_address, call_data_bytes)
            for (token_address, call_data_bytes, _user, _token) in call_batch
        ]

        # returns: List[Tuple[bool, bytes]]
        multicall_returns = multicall_contract.functions.tryAggregate(False, payload).call()

        # Map decoded balances back to (user, token) order within this batch
        for (success, return_data_bytes), (
            _token_address,
            _call_data_bytes,
            user_address,
            token_address,
        ) in zip(multicall_returns, call_batch):
            balance = _decode_uint256_or_zero(return_data_bytes) if success else 0
            balances_result[user_address][token_address] = balance
        time.sleep(0.2)

    return balances_result

# test case
# python -m bot.balances.get_balances_of_realtokens
if __name__ == "__main__":
    import json
    from pprint import pprint
    from bot.services import fetch_json
    from bot.services.utilities import list_to_dict_by_uuid
    from web3 import Web3

    # Load ABIs
    with open("ressources/abi.json", "r", encoding="utf-8") as f:
        abi = json.load(f)

    realtoken_data = list_to_dict_by_uuid(fetch_json('https://api.realtoken.community/v1/token') or [])

    # Example input
    users = [
        "0x24c47db1cc0ba028836bf808175c044055d037ec",
        "0x49a2dcc237a65cc1f412ed47e0594602f6141936",
        "0xca543f90a221dac783490bfee4a1173ae07547c2",
        "0x3409a6d40335617927b9116fad5fa743d168ec39",
    ]
    tokens = [
        uuid
        for uuid, data in realtoken_data.items()
        if data.get("gnosisContract") is not None
    ]
    
    
    balances = get_balances_of_realtokens(
        users_addresses=users,
        realtoken_contract_addresses=tokens,
        abi_realtoken=abi["realtoken"],
        abi_multicall3=abi["multicall3"],
    )

    pprint(balances)
    print(len(balances[Web3.to_checksum_address('0x24c47db1cc0ba028836bf808175c044055d037ec')]))
