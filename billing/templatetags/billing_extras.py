from django import template

register = template.Library()

@register.filter
def replace(value, arg):
    """
    Replace occurrences in a string.
    Usage: {{ value|replace:"old:new" }}
    """
    if not arg:
        return value
    
    try:
        old, new = arg.split(':', 1)
        return str(value).replace(old, new)
    except ValueError:
        return value

@register.filter
def intspace(value):
    """
    Format integer with space as thousand separator.
    Usage: {{ 1000000|intspace }} -> "1 000 000"
    """
    try:
        value = int(float(value))
        return "{:,}".format(value).replace(',', ' ')
    except (ValueError, TypeError):
        return value
