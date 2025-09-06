from __future__ import annotations
from bot.services.logging_config import get_logger
logger = get_logger(__name__)
from typing import Tuple, Dict, Any, List
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
import re

from bot.task import trigger_update_realtokens_owned_single_wallet

CALLBACK_PREFIX = "uns"  # user notification settings

# --- UI builders -------------------------------------------------------------

def build_main_keyboard(i18n, user_id: int, user_manager) -> InlineKeyboardMarkup:
    """
    Build the main inline keyboard with buttons for notification types, token scope, and back/close.
    """
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            i18n.translate_for_user("notifications.btn.types", user_id, user_manager),
            callback_data=f"{CALLBACK_PREFIX}:nav:types")],
        [InlineKeyboardButton(
            i18n.translate_for_user("notifications.btn.scope", user_id, user_manager),
            callback_data=f"{CALLBACK_PREFIX}:nav:scope")],
        [InlineKeyboardButton(
            i18n.translate_for_user("notifications.btn.close", user_id, user_manager),
            callback_data=f"{CALLBACK_PREFIX}:close")],
    ])

def render_main_message(i18n, user_id: int, user_manager) -> Tuple[str, InlineKeyboardMarkup]:
    """
    Reads the user's preferences via UserManager and builds the (text + inline keyboard)
    for the main notifications settings screen. No callback logic here.
    """
    prefs = user_manager.get_user(user_id)

    notification_types: Dict[str, Any] = getattr(prefs, "notification_types", {}) or {}
    token_scope: Dict[str, Any] = getattr(prefs, "token_scope", {}) or {}

    # JSON field names
    income_enabled = bool(notification_types.get("income_updates", True))
    price_enabled  = bool(notification_types.get("price_token_updates", True))
    other_enabled  = bool(notification_types.get("other_updates", False))

    mode = token_scope.get("mode", "all")  # "all" or "wallet"
    scope_label = "All" if mode == "all" else "Wallet"

    checked, unchecked = "☑", "☐"

    # Text parts via i18n
    title        = i18n.translate_for_user("notifications.title", user_id, user_manager)
    types_header = i18n.translate_for_user("notifications.types.header", user_id, user_manager)
    income_label = i18n.translate_for_user("notifications.types.income", user_id, user_manager)
    price_label  = i18n.translate_for_user("notifications.types.price", user_id, user_manager)
    other_label  = i18n.translate_for_user("notifications.types.other", user_id, user_manager)
    scope_header = i18n.translate_for_user("notifications.scope.header", user_id, user_manager, scope=scope_label)
    scope_legend = i18n.translate_for_user("notifications.scope.legend", user_id, user_manager)
    cta          = i18n.translate_for_user("notifications.cta", user_id, user_manager)

    message_text = (
        f"{title}\n\n"
        f"{types_header}\n\n"
        f" {checked if income_enabled else unchecked} {income_label}\n"
        f" {checked if price_enabled else unchecked} {price_label}\n"
        f" {checked if other_enabled else unchecked} {other_label}\n"
        f"\n\n"
        f"{scope_header}\n"
        f"    {scope_legend}\n\n"
        f"{cta}"
    )

    keyboard = build_main_keyboard(i18n, user_id, user_manager)
    return message_text, keyboard


def build_notification_types_keyboard(i18n, user_id: int, user_manager) -> InlineKeyboardMarkup:
    """
    Build the inline keyboard for the 'Notification Types' submenu.
    Shows current on/off state with checkboxes and provides a Back button.
    """
    prefs = user_manager.get_user(user_id)
    notification_types = getattr(prefs, "notification_types", {}) or {}

    income_enabled = bool(notification_types.get("income_updates", True))
    price_enabled  = bool(notification_types.get("price_token_updates", True))
    other_enabled  = bool(notification_types.get("other_updates", False))

    checked, unchecked = "✔", "✖"

    # Labels via i18n (short versions for buttons)
    income_label = i18n.translate_for_user("notifications.types.income_short", user_id, user_manager)
    price_label  = i18n.translate_for_user("notifications.types.price_short",  user_id, user_manager)
    other_label  = i18n.translate_for_user("notifications.types.other_short",  user_id, user_manager)
    back_label   = i18n.translate_for_user("notifications.btn.back",          user_id, user_manager)

    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{checked if income_enabled else unchecked} {income_label}",
                              callback_data=f"{CALLBACK_PREFIX}:toggle:income")],
        [InlineKeyboardButton(f"{checked if price_enabled else unchecked} {price_label}",
                              callback_data=f"{CALLBACK_PREFIX}:toggle:price")],
        [InlineKeyboardButton(f"{checked if other_enabled else unchecked} {other_label}",
                              callback_data=f"{CALLBACK_PREFIX}:toggle:other")],
        [InlineKeyboardButton(back_label, callback_data=f"{CALLBACK_PREFIX}:nav:main")],
    ])

def render_notification_types_message(i18n, user_id: int, user_manager) -> Tuple[str, InlineKeyboardMarkup]:
    """
    Build the (text + inline keyboard) for the 'Notification Types' submenu.
    """
    title = i18n.translate_for_user("notifications.types.screen.title", user_id, user_manager)
    help_text = i18n.translate_for_user("notifications.types.screen.help", user_id, user_manager)

    text = f"{title}\n\n{help_text}"
    keyboard = build_notification_types_keyboard(i18n, user_id, user_manager)
    return text, keyboard

def build_token_scope_keyboard(i18n, user_id: int, user_manager) -> InlineKeyboardMarkup:
    """
    Build the inline keyboard for the 'Token Scope' submenu.
    Buttons: All, Wallet, Manage Wallet, Back.
    'All' and 'Wallet' show a check ("✔") if active, a black cross (✖) if inactive.
    """
    prefs = user_manager.get_user(user_id)
    token_scope = getattr(prefs, "token_scope", {}) or {}
    mode = token_scope.get("mode", "all")  # "all" | "wallet"

    checked, crossed = "✔", "✖"

    # Short labels via i18n
    all_label         = i18n.translate_for_user("notifications.scope.all_short",    user_id, user_manager)
    wallet_label      = i18n.translate_for_user("notifications.scope.wallet_short", user_id, user_manager)
    manage_wallet_lbl = i18n.translate_for_user("notifications.scope.manage_wallet", user_id, user_manager)
    back_label        = i18n.translate_for_user("notifications.btn.back",           user_id, user_manager)

    all_text    = f"{checked if mode == 'all' else crossed} {all_label}"
    wallet_text = f"{checked if mode == 'wallet' else crossed} {wallet_label}"

    return InlineKeyboardMarkup([
        [InlineKeyboardButton(all_text,    callback_data=f"{CALLBACK_PREFIX}:set_scope:all")],
        [InlineKeyboardButton(wallet_text, callback_data=f"{CALLBACK_PREFIX}:set_scope:wallet")],
        [InlineKeyboardButton(manage_wallet_lbl, callback_data=f"{CALLBACK_PREFIX}:nav:manage_wallet")],
        [InlineKeyboardButton(back_label,  callback_data=f"{CALLBACK_PREFIX}:nav:main")],
    ])


def render_token_scope_message(i18n, user_id: int, user_manager) -> tuple[str, InlineKeyboardMarkup]:
    """
    Build the (text + inline keyboard) for the 'Token Scope' submenu.
    """
    title = i18n.translate_for_user("notifications.scope.screen.title", user_id, user_manager)
    help_text = i18n.translate_for_user("notifications.scope.screen.help", user_id, user_manager)

    text = f"{title}\n\n{help_text}"
    keyboard = build_token_scope_keyboard(i18n, user_id, user_manager)
    return text, keyboard



def build_manage_wallet_keyboard(i18n, user_id: int, user_manager) -> InlineKeyboardMarkup:
    """
    Build the inline keyboard for the 'Manage Wallets' submenu.
    - One button per configured wallet
    - One 'Add a wallet' button (no action yet)
    - One 'Back' button to return to the Token Scope screen
    """
    def _short_addr(addr: str) -> str:
        """Return a compact 0x address representation like 0x1234…abcd."""
        if not isinstance(addr, str) or len(addr) < 10:
            return addr
        return f"{addr[:8]}…{addr[-8:]}"
    
    prefs = user_manager.get_user(user_id)
    token_scope = getattr(prefs, "token_scope", {}) or {}
    wallets: List[str] = token_scope.get("wallets", []) or []

    # Labels (English text per user request for this screen)
    add_wallet_label = i18n.translate_for_user("notifications.scope.add_wallet", user_id, user_manager)
    back_label = i18n.translate_for_user("notifications.btn.back", user_id, user_manager)

    # One line per wallet; callback placeholders for future logic
    rows = []
    for idx, w in enumerate(wallets, start=1):
        label = f"🗑️ {_short_addr(w)}"
        rows.append([InlineKeyboardButton(label, callback_data=f"{CALLBACK_PREFIX}:wallet:{idx}")])

    # Add the "Add a wallet" and "Back" buttons
    rows.append([InlineKeyboardButton(add_wallet_label, callback_data=f"{CALLBACK_PREFIX}:wallet:add")])
    rows.append([InlineKeyboardButton(back_label, callback_data=f"{CALLBACK_PREFIX}:nav:scope")])

    return InlineKeyboardMarkup(rows)

def render_manage_wallet_message(i18n, user_id: int, user_manager) -> Tuple[str, InlineKeyboardMarkup]:
    """
    Build the (text + inline keyboard) for the 'Manage Wallets' submenu.
    The message description must be exactly 'Your wallets' (English).
    """
    manage_wallet_header = i18n.translate_for_user("notifications.scope.manage_wallet", user_id, user_manager)
    keyboard = build_manage_wallet_keyboard(i18n, user_id, user_manager)

    if len(keyboard.inline_keyboard) == 2: # if btn Add and btn Back -> no wallet yet registered for the user
        description = i18n.translate_for_user("notifications.scope.manage_wallet.description_without_wallet", user_id, user_manager)
    else:
        description =  i18n.translate_for_user("notifications.scope.manage_wallet.description_with_wallet", user_id, user_manager)
    text = manage_wallet_header + '\n\n' + description
    keyboard = build_manage_wallet_keyboard(i18n, user_id, user_manager)
    return text, keyboard


# --- Command handler ---------------------------------------------------------

async def start_user_notifications_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /notifications_settings → Sends the main settings screen (description + inline keyboard).
    """
    user_id = update.effective_user.id
    i18n = context.bot_data["i18n"]
    user_manager = context.bot_data["user_manager"]

    text, keyboard = render_main_message(i18n, user_id, user_manager)
    await update.message.reply_text(text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)


# --- Callback handler --------------------------------------------------------

async def handle_notifications_settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    i18n = context.bot_data["i18n"]
    user_manager = context.bot_data["user_manager"]

    parts = (query.data or "").split(":")  # e.g. ["uns","nav","types"]
    if not parts or parts[0] != CALLBACK_PREFIX:
        return

    action = parts[1] if len(parts) > 1 else ""

    if action == "close":
        closed_text = i18n.translate_for_user("notifications.closed", user_id, user_manager)
        # Avoid parse_mode here if your text may contain unescaped Markdown characters
        await query.edit_message_text(closed_text, reply_markup=None)
        return

    if action == "nav":
        dest = parts[2] if len(parts) > 2 else ""
        if dest == "types":
            text, kb = render_notification_types_message(i18n, user_id, user_manager)
            await query.edit_message_text(text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
            return
        if dest == "scope":
            text, kb = render_token_scope_message(i18n, user_id, user_manager)
            await query.edit_message_text(text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
            return
        if dest == "manage_wallet":
            text, kb = render_manage_wallet_message(i18n, user_id, user_manager)
            await query.edit_message_text(text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
            return
        if dest == "main":
            text, kb = render_main_message(i18n, user_id, user_manager)
            await query.edit_message_text(text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
            return
        return
    
    if action == "toggle":
        # parts: ["uns", "toggle", "income" | "price" | "other"]
        target = parts[2] if len(parts) > 2 else ""
        # Map button to JSON/storage key
        key_map = {
            "income": "income_updates",
            "price":  "price_token_updates",
            "other":  "other_updates",
        }
        pref_key = key_map.get(target)
        if not pref_key:
            return
    
        # Read current preferences
        prefs = user_manager.get_user(user_id)
        notification_types = getattr(prefs, "notification_types", {}) or {}
    
        # Flip the target flag
        current_val = bool(notification_types.get(pref_key, False))
        notification_types[pref_key] = not current_val
    
        # Persist using UserManager
        user_manager.update_user(user_id, notification_types=notification_types)
    
        # Rebuild only the keyboard for the Notification Types screen
        new_kb = build_notification_types_keyboard(i18n, user_id, user_manager)
        # Update markup without changing the text
        await query.edit_message_reply_markup(reply_markup=new_kb)
        return
    
    if action == "set_scope":
        # parts: ["uns", "set_scope", "all" | "wallet"]
        choice = (parts[2] if len(parts) > 2 else "").lower()
        if choice not in ("all", "wallet"):
            return

        # Read current preferences and token_scope (dict expected: {"mode": "...", "wallets": [...]})
        prefs = user_manager.get_user(user_id)
        token_scope = getattr(prefs, "token_scope", {}) or {}

        # Update mode while preserving existing wallets
        new_token_scope = {**token_scope, "mode": choice}
        user_manager.update_user(user_id, token_scope=new_token_scope)

        # Refresh the Token Scope screen (both text and inline keyboard)
        text, kb = render_token_scope_message(i18n, user_id, user_manager)
        await query.edit_message_text(text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
        return

    if action == "wallet":
        sub = parts[2] if len(parts) > 2 else ""

        # "Add" does nothing yet (navigation-only phase)
        if sub == "add":
            # Flag that we expect the next text message to be a wallet address
            context.user_data["awaiting_wallet_address"] = True

            text_enter_wallet = i18n.translate_for_user("notifications.scope.manage_wallet.enter_new_wallet", user_id, user_manager)
            # As requested, message must be exactly this (and remove inline keyboards)
            await query.edit_message_text(text_enter_wallet, reply_markup=None)
            return

        # If the user tapped a wallet button, `sub` is the 1-based index
        try:
            idx = int(sub)  # 1-based index
        except ValueError:
            return

        # Load current wallets
        prefs = user_manager.get_user(user_id)
        token_scope = getattr(prefs, "token_scope", {}) or {}
        wallets = list(token_scope.get("wallets", []) or [])
    
        # Bounds check and delete
        real_index = idx - 1  # convert to 0-based
        if 0 <= real_index < len(wallets):
            wallet_to_delete = wallets[real_index]
            del wallets[real_index]
            new_token_scope = {**token_scope, "wallets": wallets}
        
        # If no wallets remain, clear realtokens_owned
        if not wallets:
            new_token_scope["realtokens_owned"] = []
            new_token_scope["mode"] = 'all'
            logger.info(
                f"User {user_id} deleted the last wallet ({wallet_to_delete});"
                f"reset token_scope['realtokens_owned'] to empty list."
                f"reset token_scope['mode'] to all."
            )
        else:
            logger.info(
                f"User {user_id} deleted wallet address {wallet_to_delete}; "
                f"{len(wallets)} wallet(s) remain."
            )
    
        # Persist changes in a single update
        user_manager.update_user(user_id, token_scope=new_token_scope)

        # Refresh the Manage Wallets screen (text + keyboard may change)
        text, kb = render_manage_wallet_message(i18n, user_id, user_manager)
        await query.edit_message_text(text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
        return

    # Future actions (e.g., toggle/set_scope) will be handled here
    return


async def handle_wallet_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    When awaiting a wallet address (after pressing 'Add a wallet'),
    validate the user's text. If valid, save it and return to Manage Wallets.
    If invalid, prompt again.
    """
    def is_valid_evm_address(addr: str) -> bool:
        """Return True if addr looks like a valid EVM address (0x + 40 hex chars)."""
        if not isinstance(addr, str):
            return False
        return bool(re.fullmatch(r"0x[a-fA-F0-9]{40}", addr.strip()))


    # Only proceed if we are in the "awaiting wallet" state
    if not context.user_data.get("awaiting_wallet_address"):
        return

    user_id = update.effective_user.id
    i18n = context.bot_data["i18n"]
    user_manager = context.bot_data["user_manager"]

    addr = (update.message.text or "").strip()

    # Validate EVM address
    if not is_valid_evm_address(addr):
        # Keep waiting; re-prompt user with a short validation hint
        invalid_wallet = i18n.translate_for_user("notifications.scope.manage_wallet.invalid_address", user_id, user_manager)
        text_enter_wallet = i18n.translate_for_user("notifications.scope.manage_wallet.enter_new_wallet", user_id, user_manager)
        await update.message.reply_text(
            f"{invalid_wallet}\n{text_enter_wallet}"
        )
        return

    # Normalize address storage (lowercase is fine unless you enforce EIP-55 checksums)
    addr_norm = addr.lower()

    # Append to the user's wallets (avoid duplicates)
    prefs = user_manager.get_user(user_id)
    token_scope = getattr(prefs, "token_scope", {}) or {}
    wallets: List[str] = list(token_scope.get("wallets", []) or [])
    if addr_norm not in wallets:
        wallets.append(addr_norm)
    

    new_token_scope = {**token_scope, "wallets": wallets}
    new_token_scope["mode"] = "wallet"
    user_manager.update_user(user_id, token_scope=new_token_scope)

    # Clear the awaiting flag
    context.user_data["awaiting_wallet_address"] = False

    # Return to Manage Wallets screen
    text, kb = render_manage_wallet_message(i18n, user_id, user_manager)
    await update.message.reply_text(text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)

    # Fire-and-forget background task to update owned RealTokens
    trigger_update_realtokens_owned_single_wallet(context, addr_norm, user_id, user_manager)

    logger.info(f'User {user_id} added wallet address {addr_norm}')