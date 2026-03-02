"""
Custom template filters for number formatting and utilities
"""

from django import template
from django.utils.html import format_html
from decimal import Decimal, InvalidOperation

register = template.Library()


def _to_float(value):
    """Convert value to float, return None on failure."""
    if value is None:
        return None
    try:
        if isinstance(value, Decimal):
            return float(value)
        return float(value)
    except (TypeError, ValueError, InvalidOperation):
        return None


def _space_sep_display(v):
    """Format with non-breaking spaces for display (prevents line-wrapping)."""
    return f"{int(v):,}".replace(',', '\u00a0')


def _space_sep_title(v):
    """Format with regular spaces for title attribute tooltip."""
    return f"{int(v):,}".replace(',', ' ')


def _abbrev(v):
    """Return abbreviated string: K / M with space-sep prefix when large."""
    if v >= 1_000_000:
        d = v / 1_000_000
        if d >= 1_000:
            # e.g. 1_500_000_000 → "1 500M"
            return _space_sep_display(round(d)) + "M"
        elif d >= 10:
            return f"{d:.0f}M"
        else:
            return f"{d:.1f}".rstrip('0').rstrip('.') + "M"
    elif v >= 1_000:
        d = v / 1_000
        if d >= 1_000:
            return _space_sep_display(round(d)) + "K"
        elif d >= 10:
            return f"{d:.0f}K"
        else:
            return f"{d:.1f}".rstrip('0').rstrip('.') + "K"
    else:
        return f"{v:.0f}"


@register.filter(is_safe=True)
def smart_num(value):
    """
    Display a number abbreviated (K/M) with the full value on hover.
    Returns HTML: <span title="1 500 000" style="...">1.5M</span>
    The title uses plain spaces so browser tooltip renders correctly.
    """
    v = _to_float(value)
    if v is None:
        return format_html('0')
    abbrev = _abbrev(v)
    # Build the plain-space full number for the title attribute
    if v == int(v):
        full_title = _space_sep_title(v)
    else:
        full_title = f"{v:,.2f}".replace(',', ' ')
    # Only add hover span when the number was actually abbreviated
    if abbrev != full_title.replace(' ', ''):
        return format_html(
            '<span data-bs-toggle="tooltip" data-bs-placement="top" title="{}" style="cursor:help;border-bottom:1px dotted currentColor">{}</span>',
            full_title,
            abbrev,
        )
    return format_html('{}', abbrev)


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
def intspace(value):
    """
    Add spaces as thousand separators; mirrors intcomma but with spaces.
    Examples:
        1234 -> 1 234
        1234567 -> 1 234 567
    """
    if value is None:
        return "0"
    try:
        if isinstance(value, Decimal):
            value = float(value)
        else:
            value = float(value)
        if value == int(value):
            return f"{int(value):,}".replace(',', ' ')
        return f"{value:,.2f}".replace(',', ' ')
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
