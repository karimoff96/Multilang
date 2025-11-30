from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def trans_name(obj, default=''):
    """
    Returns translated name fields for an object as data attributes.
    Usage: {{ category|trans_name }}
    This returns a span with data-name-uz, data-name-ru, data-name-en attributes.
    JavaScript will display the correct one based on dashboard language.
    """
    if obj is None:
        return default
    
    name_uz = getattr(obj, 'name_uz', None) or ''
    name_ru = getattr(obj, 'name_ru', None) or ''
    name_en = getattr(obj, 'name_en', None) or ''
    fallback = getattr(obj, 'name', None) or default
    
    return mark_safe(
        f'<span class="translatable-name" '
        f'data-name-uz="{name_uz}" '
        f'data-name-ru="{name_ru}" '
        f'data-name-en="{name_en}" '
        f'data-name-fallback="{fallback}">'
        f'{fallback}</span>'
    )


@register.filter
def trans_desc(obj, default=''):
    """
    Returns translated description fields for an object as data attributes.
    Usage: {{ category|trans_desc }}
    """
    if obj is None:
        return default
    
    desc_uz = getattr(obj, 'description_uz', None) or ''
    desc_ru = getattr(obj, 'description_ru', None) or ''
    desc_en = getattr(obj, 'description_en', None) or ''
    fallback = getattr(obj, 'description', None) or default
    
    return mark_safe(
        f'<span class="translatable-desc" '
        f'data-desc-uz="{desc_uz}" '
        f'data-desc-ru="{desc_ru}" '
        f'data-desc-en="{desc_en}" '
        f'data-desc-fallback="{fallback}">'
        f'{fallback}</span>'
    )


@register.simple_tag
def get_translated_field(obj, field_name, lang='uz'):
    """
    Get a specific translated field value.
    Usage: {% get_translated_field category 'name' 'en' %}
    """
    if obj is None:
        return ''
    
    # Try language-specific field first
    lang_field = f'{field_name}_{lang}'
    value = getattr(obj, lang_field, None)
    
    if value:
        return value
    
    # Fallback to default field
    return getattr(obj, field_name, '') or ''
