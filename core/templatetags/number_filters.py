"""
Custom template filters for number formatting and utilities
"""

from django import template
from decimal import Decimal

register = template.Library()


@register.filter
def short_number(value):
    """
    Convert large numbers to shortened format (K, M, B)
    Examples:
        1234 -> 1.2K
        1234567 -> 1.2M
        1234567890 -> 1.2B
    """
    try:
        value = float(value)
    except (TypeError, ValueError):
        return value

    if value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.1f}B"
    elif value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    elif value >= 1_000:
        return f"{value / 1_000:.1f}K"
    else:
        return f"{value:.0f}"


@register.filter
def format_currency(value, short=False):
    """
    Format number as currency with thousand separators
    If short=True, uses short_number format
    """
    try:
        value = float(value)
    except (TypeError, ValueError):
        return value

    if short:
        return short_number(value)

    # Format with thousand separators
    return f"{value:,.0f}"


@register.filter
def percentage(value, total):
    """Calculate percentage of value from total"""
    try:
        if total == 0:
            return 0
        return round((float(value) / float(total)) * 100, 1)
    except (TypeError, ValueError, ZeroDivisionError):
        return 0
