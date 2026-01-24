"""
Custom template filters for number formatting and utilities
"""

from django import template
from decimal import Decimal, InvalidOperation

register = template.Library()


@register.filter
def getattr_filter(obj, attr):
    """
    Get an attribute from an object dynamically.
    Usage: {{ object|getattr:"attribute_name" }}
    """
    try:
        return getattr(obj, attr, None)
    except (TypeError, AttributeError):
        return None


@register.filter(name='getattr')
def getattr_alias(obj, attr):
    """Alias for getattr_filter"""
    return getattr_filter(obj, attr)


@register.filter(name='has_effective_permission')
def has_effective_permission(role, permission):
    """
    Check if a role has effective permission (considering master permissions).
    Usage: {{ role|has_effective_permission:"can_view_centers" }}
    """
    try:
        if hasattr(role, 'has_effective_permission'):
            return role.has_effective_permission(permission)
        return getattr(role, permission, False)
    except (TypeError, AttributeError):
        return False


@register.filter
def get_item(dictionary, key):
    """
    Get an item from a dictionary by key.
    Usage: {{ dict|get_item:key }}
    """
    if dictionary is None:
        return ''
    try:
        return dictionary.get(key, key)
    except (TypeError, AttributeError):
        return key


@register.filter
def short_number(value):
    """
    Convert large numbers to shortened format (K, M)
    Examples:
        1234 -> 1.2K
        1234567 -> 1.2M
        1234567890 -> 1235M
    """
    if value is None:
        return "0"
    try:
        if isinstance(value, Decimal):
            value = float(value)
        else:
            value = float(value)
    except (TypeError, ValueError, InvalidOperation):
        return "0"

    if value >= 1_000_000:
        # Format millions: 1234567 -> 1.2M or 1234000 -> 1M
        result = value / 1_000_000
        if result >= 10:
            return f"{result:.0f}M"
        else:
            return f"{result:.1f}M".rstrip('0').rstrip('.')
    elif value >= 1_000:
        # Format thousands: 1234 -> 1.2K or 1000 -> 1K
        result = value / 1_000
        if result >= 10:
            return f"{result:.0f}K"
        else:
            return f"{result:.1f}K".rstrip('0').rstrip('.')
    else:
        return f"{value:.0f}"


@register.filter
def format_currency(value, short=False):
    """
    Format number as currency with thousand separators
    If short=True, uses short_number format
    """
    if value is None:
        return "0"
    try:
        if isinstance(value, Decimal):
            value = float(value)
        else:
            value = float(value)
    except (TypeError, ValueError, InvalidOperation):
        return "0"

    if short:
        return short_number(value)

    # Format with thousand separators
    return f"{value:,.0f}"


@register.filter
def intcomma(value):
    """
    Add commas to an integer or float value for readability.
    Similar to Django's humanize intcomma filter.
    Examples:
        1234 -> 1,234
        1234567 -> 1,234,567
    """
    if value is None:
        return "0"
    try:
        if isinstance(value, Decimal):
            value = float(value)
        else:
            value = float(value)
        if value == int(value):
            return f"{int(value):,}"
        return f"{value:,.2f}"
    except (TypeError, ValueError, InvalidOperation):
        return "0"


@register.filter
def percentage(value, total):
    """Calculate percentage of value from total"""
    try:
        if total == 0:
            return 0
        return round((float(value) / float(total)) * 100, 1)
    except (TypeError, ValueError, ZeroDivisionError):
        return 0


@register.filter
def format_number(value):
    """
    Format number with thousand separators using space.
    Examples:
        1234 -> 1 234
        1234567.89 -> 1 234 567.89
    """
    if value is None:
        return "0"
    try:
        # Handle Decimal specifically
        if isinstance(value, Decimal):
            value = float(value)
        else:
            value = float(value)
        if value == int(value):
            return f"{int(value):,}".replace(',', ' ')
        return f"{value:,.2f}".replace(',', ' ')
    except (TypeError, ValueError, InvalidOperation):
        return "0"
