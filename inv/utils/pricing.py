"""Pricing utilities including price rounding and calculations"""

import math
from decimal import Decimal, ROUND_UP
from typing import Union


def round_price_up(price: Union[float, Decimal, str]) -> Decimal:
    """Round price UP to nearest $5 (business rule: always round up)"""
    price_decimal = Decimal(str(price))
    
    # Round up to nearest 5
    rounded = math.ceil(price_decimal / 5) * 5
    
    return Decimal(str(rounded))


def calculate_consignment_payout(sale_price: Union[float, Decimal, str], 
                                platform_fee: Union[float, Decimal, str] = 10,
                                split_percentage: int = 70) -> Decimal:
    """Calculate consignment payout: split_percentage of (sale_price - platform_fee)"""
    sale_price_decimal = Decimal(str(sale_price))
    platform_fee_decimal = Decimal(str(platform_fee))
    
    net_amount = sale_price_decimal - platform_fee_decimal
    payout = net_amount * Decimal(str(split_percentage)) / Decimal('100')
    
    return payout.quantize(Decimal('0.01'), rounding=ROUND_UP)


def format_price(price: Union[float, Decimal, str]) -> str:
    """Format price as currency string"""
    price_decimal = Decimal(str(price))
    return f"${price_decimal:.2f}"




def get_price_range(items: list) -> str:
    """Get price range string for multiple items"""
    if not items:
        return "$0"
    
    prices = [item.current_price for item in items]
    min_price = min(prices)
    max_price = max(prices)
    
    if min_price == max_price:
        return format_price(min_price)
    else:
        return f"{format_price(min_price)} - {format_price(max_price)}"


