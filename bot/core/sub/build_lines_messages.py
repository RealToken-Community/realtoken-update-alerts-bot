from datetime import datetime
from bot.services.utilities import get_latest_value_for_key

import logging
logger = logging.getLogger(__name__)

icon_up = "📈"
icon_down = "📉"
arrow_up = "▲"
arrow_down = "▼"

def get_last_value(items, field):
    """Return the last value for a field in the 'values' dict of items, or None."""
    for entry in reversed(items):
        if field in entry["values"]:
            return entry["values"][field]
    return None


def build_lines_messages(new_history_items_by_uuid, realtoken_data, realtoken_history_data_last, user_manager, i18n, user_id):
    
    lines_messages = []

    # small helper for translations
    def translate(key: str, **fmt):
        return i18n.translate_for_user(key, user_id, user_manager, **fmt)

    for uuid, new_history_item in new_history_items_by_uuid.items():

        realtoken_name = realtoken_data[uuid]['shortName']

        # Use the latest date (arbitrary choice)
        date_obj = datetime.strptime(new_history_item[-1]['date'], "%Y%m%d")
        
        # Find the last non-None value for each field
        netRentYear = get_last_value(new_history_item, "netRentYear")
        tokenPrice = get_last_value(new_history_item, "tokenPrice")
        underlyingAssetPrice = get_last_value(new_history_item, "underlyingAssetPrice")
        totalInvestment = get_last_value(new_history_item, "totalInvestment")
        initialMaintenanceReserve = get_last_value(new_history_item, "initialMaintenanceReserve")
        renovationReserve = get_last_value(new_history_item, "renovationReserve")
        rentedUnits = get_last_value(new_history_item, "rentedUnits")
        
        header_line = translate("updates.header", name=realtoken_name)

        # Token price line
        if tokenPrice is not None:
            old_tokenPrice = get_latest_value_for_key(realtoken_history_data_last[uuid], 'tokenPrice')
            change_var = tokenPrice - old_tokenPrice
            change_pct = (change_var / old_tokenPrice) * 100
        
            is_up = change_var > 0
            icon  = icon_up if is_up else icon_down
            arrow = arrow_up if is_up else arrow_down
        
            tokenPrice_line = (
                translate("updates.token_price.title", icon=icon) + "\n" +
                translate("updates.token_price.line", old=old_tokenPrice, new=tokenPrice, arrow=arrow, pct=abs(change_pct))
            )
        else:
            tokenPrice_line = ""

        # Income line
        if netRentYear is not None or totalInvestment is not None:
            old_netRentYear = get_latest_value_for_key(realtoken_history_data_last[uuid], 'netRentYear')
            old_totalInvestment = get_latest_value_for_key(realtoken_history_data_last[uuid], 'totalInvestment')
            netRentYear = netRentYear or old_netRentYear
            totalInvestment = totalInvestment or old_totalInvestment

            old_income = (old_netRentYear / old_totalInvestment) * 100
            new_income = (netRentYear / totalInvestment) * 100
            change_var = new_income - old_income
            change_pct = (change_var / old_income) * 100

            is_up = change_var > 0
            icon  = icon_up if is_up else icon_down
            arrow = arrow_up if is_up else arrow_down
    
            income_line = (
                translate("updates.income.title", icon=icon) + "\n" +
                translate("updates.income.line", old=old_income, new=new_income, arrow=arrow, pct=abs(change_pct))
            )
        else:
            income_line = ''

        # underlyingAssetPrice
        if underlyingAssetPrice is not None:
            old_underlying = get_latest_value_for_key(realtoken_history_data_last[uuid], 'underlyingAssetPrice')

            change_var = underlyingAssetPrice - old_underlying
            change_pct = (change_var / old_underlying) * 100
    
            is_up = change_var > 0
            icon  = icon_up if is_up else icon_down
            arrow = arrow_up if is_up else arrow_down
    
            underlyingAssetPrice_line = (
                translate("updates.underlying_asset.title", icon=icon) + "\n" +
                translate("updates.underlying_asset.line", old=old_underlying, new=underlyingAssetPrice, arrow=arrow, pct=abs(change_pct))
            )
        else:
            underlyingAssetPrice_line = ""
                    
        # initialMaintenanceReserve
        if initialMaintenanceReserve is not None:
            old_imr = get_latest_value_for_key(realtoken_history_data_last[uuid], 'initialMaintenanceReserve')
            change_var = initialMaintenanceReserve - old_imr
            change_pct = (change_var / old_imr) * 100
    
            is_up = change_var > 0
            icon  = icon_up if is_up else icon_down
            arrow = arrow_up if is_up else arrow_down
            
            initialMaintenanceReserve_line = (
                translate("updates.initial_maintenance.title", icon=icon) + "\n" +
                (
                    translate("updates.initial_maintenance.line", old=old_imr, new=initialMaintenanceReserve, arrow=arrow, pct=abs(change_pct))
                    if initialMaintenanceReserve != 0
                    else translate("updates.initial_maintenance.line_no_pct", old=old_imr, new=initialMaintenanceReserve)
                )
            )
        else:
            initialMaintenanceReserve_line = ""
            
        # renovationReserve
        if renovationReserve is not None:
            old_rr = get_latest_value_for_key(realtoken_history_data_last[uuid], 'renovationReserve')
            change_var = renovationReserve - old_rr
            change_pct = (change_var / old_rr) * 100
    
            is_up = change_var > 0
            icon  = icon_up if is_up else icon_down
            arrow = arrow_up if is_up else arrow_down
    
            renovationReserve_line = (
                translate("updates.renovation_reserve.title", icon=icon) + "\n" +
                (
                    translate("updates.renovation_reserve.line", old=old_rr, new=renovationReserve, arrow=arrow, pct=abs(change_pct))
                    if renovationReserve != 0
                    else translate("updates.renovation_reserve.line_no_pct", old=old_rr, new=renovationReserve)
                )
            )
        else:
            renovationReserve_line = ""

        # rentedUnits
        if rentedUnits is not None:
            old_ru = get_latest_value_for_key(realtoken_history_data_last[uuid], 'rentedUnits')
            change_var = rentedUnits - old_ru
        
            # Only calculate percentage if old value is not zero
            if old_ru != 0:
                change_pct = (change_var / old_ru) * 100
                has_pct = True
            else:
                change_pct = 0
                has_pct = False
        
            is_up = change_var > 0
            icon  = icon_up if is_up else icon_down
            arrow = arrow_up if is_up else arrow_down
        
            # Build the text line
            if rentedUnits != 0 and has_pct:
                rentedUnits_line = (
                    translate("updates.rented_units.title", icon=icon) + "\n" +
                    translate("updates.rented_units.line", old=old_ru, new=rentedUnits, arrow=arrow, pct=abs(change_pct))
                )
            else:
                # Skip percentage if either old or new value is zero
                rentedUnits_line = (
                    translate("updates.rented_units.title", icon=icon) + "\n" +
                    translate("updates.rented_units.line_no_pct", old=old_ru, new=rentedUnits)
                )
        else:
            rentedUnits_line = ""
        
        lines_message = {
            "uuid" : uuid,
            "header_line": header_line,
            "tokenPrice_line": tokenPrice_line,
            "income_line": income_line,
            "underlyingAssetPrice_line": underlyingAssetPrice_line,
            "initialMaintenanceReserve_line": initialMaintenanceReserve_line,
            "renovationReserve_line": renovationReserve_line,
            "rentedUnits_line": rentedUnits_line
        }
        lines_messages.append(lines_message)

    return lines_messages