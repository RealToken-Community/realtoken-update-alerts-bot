import time
from typing import List, Dict, Tuple
from web3 import Web3
from web3.contract import Contract
from hexbytes import HexBytes
from bot.services import w3_handler
from bot.config.settings import MULTICALLV3_ADDRESS


@w3_handler()
def _encode_balance_of_calls(
    w3: Web3,
    users: List[str],
    tokens: List[str],
    erc20_abi: List[Dict],
) -> List[Tuple[str, bytes, str, str]]:
    """
    Build the (target, callData) list for balanceOf(user) for every (user, token) pair.

    This function is decorated with @w3_handler so it receives a Web3 instance
    automatically; callers do NOT pass w3 explicitly.

    Returns a list of tuples: (token_address, call_data_bytes, user_address, token_address)
    """
    token_contracts: Dict[str, Contract] = {
        w3.to_checksum_address(token): w3.eth.contract(
            address=w3.to_checksum_address(token),
            abi=erc20_abi,
        )
        for token in tokens
    }

    calls: List[Tuple[str, bytes, str, str]] = []
    for user in users:
        user_checksum = w3.to_checksum_address(user)
        for token in tokens:
            token_checksum = w3.to_checksum_address(token)
            token_contract = token_contracts[token_checksum]
            # Web3.py 7.x: encode calldata via _encode_transaction_data()
            hex_data = token_contract.functions.balanceOf(
                user_checksum
            )._encode_transaction_data()
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
def _run_multicall3_batch(
    w3: Web3,
    call_batch: List[Tuple[str, bytes, str, str]],
    abi_multicall3: List[Dict],
):
    """
    Execute a single Multicall3 tryAggregate batch.

    This is the function that is responsible for the actual RPC call and is
    decorated with @w3_handler, so RPC failover happens at the *batch* level.
    """
    multicall_contract = w3.eth.contract(
        address=w3.to_checksum_address(MULTICALLV3_ADDRESS),
        abi=abi_multicall3,
    )

    # Multicall3 expects a list of (target, callData) tuples
    payload = [
        (token_address, call_data_bytes)
        for (token_address, call_data_bytes, _user, _token) in call_batch
    ]

    # returns: List[Tuple[bool, bytes]]
    return multicall_contract.functions.tryAggregate(False, payload).call()


def get_balances_of_realtokens(
    users_addresses: List[str],
    realtoken_contract_addresses: List[str],
    abi_realtoken: List[Dict],
    abi_multicall3: List[Dict],
    *,
    max_subcalls_per_multicall: int = 2600,
) -> Dict[str, Dict[str, int]]:
    """
    Query balanceOf for each user across all given RealToken contracts using Multicall3.

    - Batching: we split the (user, token) calls into chunks of size <= max_subcalls_per_multicall.
    - Each chunk is sent via tryAggregate(requireSuccess=False).
    - RPC failover is handled at the *batch* level by the @w3_handler on _run_multicall3_batch.

    Args:
        users_addresses: list of user addresses.
        realtoken_contract_addresses: list of ERC20 token addresses (RealToken).
        abi_realtoken: ERC20 ABI (must contain balanceOf(address)).
        abi_multicall3: Multicall3 ABI (must contain tryAggregate(bool,(address,bytes)[])).
        max_subcalls_per_multicall: max number of sub-calls per multicall (default 2600).

    Returns:
        { user_checksum: { token_checksum: raw_balance_int } }
    """
    # Output skeleton with checksum addresses
    balances_result: Dict[str, Dict[str, int]] = {
        Web3.to_checksum_address(user): {} for user in users_addresses
    }

    prepared_calls = _encode_balance_of_calls(
        users_addresses,
        realtoken_contract_addresses,
        abi_realtoken,
    )
    if not prepared_calls:
        return balances_result

    # Process in batches to avoid oversized payloads.
    # Each batch goes through _run_multicall3_batch, which is decorated with @w3_handler.
    for call_batch in _split_into_batches(prepared_calls, max_subcalls_per_multicall):
        multicall_returns = _run_multicall3_batch(call_batch, abi_multicall3)

        # Map decoded balances back to (user, token) order within this batch.
        for (success, return_data_bytes), (
            _token_address,
            _call_data_bytes,
            user_address,
            token_address,
        ) in zip(multicall_returns, call_batch):
            balance = _decode_uint256_or_zero(return_data_bytes) if success else 0
            balances_result[user_address][token_address] = balance

        time.sleep(0.5)

    return balances_result


# test case
# python -m bot.balances.get_balances_of_realtokens
if __name__ == "__main__":
    import json
    from pprint import pprint
    from bot.services.logging_config import get_logger
    from bot.services import fetch_json
    from bot.services.utilities import list_to_dict_by_uuid
    from web3 import Web3
    logger = get_logger(__name__)

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
        "0x62244C1b3d7D23eA942f483d51B31BB101e1C759",
        "0x134d928B26DB2Da678F16974580B22E799293E6c",
        "0xc147895Ad84dBE01A2fffd0CC8d967f9973ef991",
        "0xCA84B1a823d502da097dd247Ce65eDcb3C692408",
        "0xAB1c40889175EA24b83175d9e09ee335DdF5A1aB",
        "0xB2CC0d719B71Fb91082e050967b644a5E55b33a0",
        "0x97E7634bE705079ad6769904b1BaBd82960df851",
        "0xFFF14378eC8D8F294dDb4E2bA6674004BaCB5575",
        "0x42A203a03BAf90F320441726533CAE899ea42af0",
        "0x2ABC4192378087b802B0e45bb0ffa9d7A07148a2",
        "0x1754352eacb753327Fec2d4F48f0fb36B672C5e0",
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

    logger.info(balances)
    print(len(balances))
