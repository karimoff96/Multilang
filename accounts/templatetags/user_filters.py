from django import template

register = template.Library()


@register.filter
def user_avatar(user_id, total_images=6):
    """
    Returns a number between 1 and total_images based on user_id.
    This ensures each user gets a consistent avatar image.
    """
    try:
        return (int(user_id) % total_images) + 1
    except (ValueError, TypeError):
        return 1
