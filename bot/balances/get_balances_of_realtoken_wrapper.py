import time
from typing import List, Dict, Tuple
from web3 import Web3
from web3.contract import Contract
from hexbytes import HexBytes
from bot.services import w3_handler
from bot.config.settings import MULTICALLV3_ADDRESS, REALTOKEN_WRAPPER

def _split_into_batches(items, batch_size: int):
    """Yield consecutive slices (batches) from items with at most batch_size elements each."""
    for start in range(0, len(items), batch_size):
        yield items[start:start + batch_size]


def _encode_wrapper_calls(
    w3: Web3,
    users: List[str],
    wrapper_abi: List[Dict],
) -> List[Tuple[str, bytes, str]]:
    """
    Build the (target, callData) list for getAllTokenBalancesOfUser(user) for every user.
    Returns a list of tuples: (wrapper_address_checksum, call_data_bytes, user_address_checksum)
    """
    wrapper_contract: Contract = w3.eth.contract(
        address=w3.to_checksum_address(REALTOKEN_WRAPPER),
        abi=wrapper_abi,
    )

    calls: List[Tuple[str, bytes, str]] = []
    for user in users:
        user_checksum = w3.to_checksum_address(user)
        # Web3.py 7.x: encode calldata via _encode_transaction_data()
        hex_data = wrapper_contract.functions.getAllTokenBalancesOfUser(user_checksum)._encode_transaction_data()
        call_data_bytes = HexBytes(hex_data)
        calls.append((w3.to_checksum_address(REALTOKEN_WRAPPER), call_data_bytes, user_checksum))
    return calls


def _decode_address_uint256_arrays(
    w3: Web3,
    return_data_bytes: bytes,
) -> Tuple[List[str], List[int]]:
    """
    Decode ABI-encoded (address[], uint256[]) into Python lists.
    Uses the low-level codec to stay version-agnostic.
    """
    if not return_data_bytes:
        return [], []
    try:
        # Equivalent to decoding the outputs of (address[], uint256[])
        addresses, balances = w3.codec.decode(["address[]", "uint256[]"], return_data_bytes)
        # Normalize to checksum addresses and Python ints
        addresses_cs = [w3.to_checksum_address(a) for a in addresses]
        balances_int = [int(b) for b in balances]
        return addresses_cs, balances_int
    except Exception as error:
        print(f"[decode] failed: {error}. raw=0x{return_data_bytes.hex()}")
        return [], []

@w3_handler()
def get_balances_of_realtoken_wrapper(
    w3: Web3,
    users_addresses: List[str],
    abi_realtoken_wrapper: List[Dict],
    abi_multicall3: List[Dict],
    *,
    max_subcalls_per_multicall: int = 800,
) -> Dict[str, Dict[str, int]]:
    """
    Query getAllTokenBalancesOfUser(user) for each user via Multicall3.tryAggregate.

    - Batching: we split the user calls into batches of size <= max_subcalls_per_multicall.
    - Each batch is sent via tryAggregate(requireSuccess=False) so a failing sub-call doesn't revert the batch.
    - Output: { user_checksum: { token_checksum: raw_balance_int } } with zero balances filtered out.

    Args:
        w3: Web3 instance.
        users_addresses: list of user addresses.
        abi_realtoken_wrapper: ABI that contains getAllTokenBalancesOfUser(address).
        abi_multicall3: Multicall3 ABI (must contain tryAggregate(bool,(address,bytes)[])).
        max_subcalls_per_multicall: max number of sub-calls per multicall (default 800).

    Returns:
        { user_checksum: { token_checksum: raw_balance_int } }
    """
    # Output skeleton with checksum addresses
    balances_result: Dict[str, Dict[str, int]] = {
        w3.to_checksum_address(user): {} for user in users_addresses
    }
    if not users_addresses:
        return balances_result

    # Prepare all sub-calls (one per user)
    prepared_calls = _encode_wrapper_calls(
        w3=w3,
        users=users_addresses,
        wrapper_abi=abi_realtoken_wrapper,
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
            (target_address, call_data_bytes)
            for (target_address, call_data_bytes, _user_address) in call_batch
        ]

        # returns: List[Tuple[bool, bytes]]
        multicall_returns = multicall_contract.functions.tryAggregate(False, payload).call()

        # Map decoded (addresses[], balances[]) back to each user in this batch
        for (success, return_data_bytes), (
            _target_address,
            _call_data_bytes,
            user_address,
        ) in zip(multicall_returns, call_batch):

            if not success or not return_data_bytes:
                # Skip failed or empty responses to keep behavior consistent
                continue

            token_addresses, token_balances = _decode_address_uint256_arrays(w3, return_data_bytes)

            # Store only strictly positive balances (adjust as needed)
            user_map = balances_result[user_address]
            for token_addr, bal in zip(token_addresses, token_balances):
                if bal > 0:
                    user_map[token_addr] = bal
        time.sleep(0.5)

    return balances_result


if __name__ == "__main__":
    import json
    from pprint import pprint

    # Load ABIs
    with open("ressources/abi.json", "r", encoding="utf-8") as f:
        abi = json.load(f)

    # Example input (replace as needed)
    users = [
        "0xB999041bBAd79E8435286DA3A56231E92e98f71a",
        "0x49a2dcc237a65cc1f412ed47e0594602f6141936",
        "0xca543f90a221dac783490bfee4a1173ae07547c2",
        "0xa1f0da6d8c3480ad43d6755d2b5f8721f9680fb4",
    ]

    balances = get_balances_of_realtoken_wrapper(
        users_addresses=users,
        abi_realtoken_wrapper=abi["realtoken-wrapper"],
        abi_multicall3=abi["multicall3"],
        max_subcalls_per_multicall=1000,
    )

    pprint(balances)
