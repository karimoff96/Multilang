"""
Bot Notification Service for Order Routing

This module handles sending order notifications to Telegram channels
based on the multi-tenant bot infrastructure.

Order Routing Rules:
- ALWAYS send to center.company_orders_channel_id (if set)
- If B2C (individual customer) -> send to branch.b2c_orders_channel_id (if set)
- If B2B (agency customer) -> send to branch.b2b_orders_channel_id (if set)
"""

import logging
import telebot
from telebot.apihelper import ApiTelegramException
from functools import lru_cache
from django.conf import settings

logger = logging.getLogger(__name__)

# Cache for bot instances to avoid creating new instances for every request
_bot_instances = {}


def get_bot_instance(bot_token):
    """
    Get or create a bot instance for the given token.
    Uses caching to avoid creating multiple instances for the same token.
    """
    if not bot_token:
        return None
    
    if bot_token not in _bot_instances:
        try:
            bot = telebot.TeleBot(bot_token, parse_mode="HTML", threaded=False)
            _bot_instances[bot_token] = bot
            logger.info(f"Created new bot instance for token ending in ...{bot_token[-8:]}")
        except Exception as e:
            logger.error(f"Failed to create bot instance: {e}")
            return None
    
    return _bot_instances[bot_token]


def clear_bot_cache(bot_token=None):
    """Clear cached bot instances. If token provided, only clear that one."""
    global _bot_instances
    if bot_token and bot_token in _bot_instances:
        del _bot_instances[bot_token]
    elif bot_token is None:
        _bot_instances = {}


def format_order_message(order, include_details=True):
    """Format order details for Telegram notification."""
    from orders.models import Order
    
    # Determine customer type
    is_b2b = order.bot_user.is_agency if order.bot_user else False
    customer_type = "🏢 B2B" if is_b2b else "👤 B2C"
    
    # Status emoji mapping
    status_emoji = {
        'pending': '🟡',
        'in_progress': '🔵',
        'ready': '🟢',
        'completed': '✅',
        'cancelled': '❌',
    }
    status_icon = status_emoji.get(order.status, '⚪')
    
    message = f"""
<b>📋 New Order #{order.id}</b>
{customer_type} | {status_icon} {order.get_status_display()}

<b>Customer:</b> {order.bot_user.display_name if order.bot_user else 'N/A'}
<b>Phone:</b> {order.bot_user.phone if order.bot_user and order.bot_user.phone else 'N/A'}
<b>Branch:</b> {order.branch.name if order.branch else 'N/A'}
"""
    
    if include_details:
        message += f"""
<b>Product:</b> {order.product.name if order.product else 'N/A'}
<b>Pages:</b> {order.total_pages}
<b>Copies:</b> {order.copy_number}
<b>Total Price:</b> {order.total_price:,.0f} UZS
<b>Payment:</b> {order.get_payment_type_display()}
"""
        if order.description:
            message += f"\n<b>Notes:</b> {order.description[:200]}"
    
    message += f"\n\n<i>Created: {order.created_at.strftime('%Y-%m-%d %H:%M')}</i>"
    
    return message


def send_message_to_channel(bot_token, channel_id, message, retry_count=3):
    """
    Send a message to a Telegram channel with retry logic.
    
    Args:
        bot_token: The bot token to use
        channel_id: The channel ID to send to
        message: The message text (HTML formatted)
        retry_count: Number of retries on failure
    
    Returns:
        tuple: (success: bool, error_message: str or None)
    """
    if not bot_token or not channel_id:
        return False, "Missing bot_token or channel_id"
    
    bot = get_bot_instance(bot_token)
    if not bot:
        return False, "Failed to create bot instance"
    
    for attempt in range(retry_count):
        try:
            bot.send_message(channel_id, message)
            logger.info(f"Message sent to channel {channel_id}")
            return True, None
        except ApiTelegramException as e:
            error_msg = f"Telegram API error: {e.description}"
            logger.warning(f"Attempt {attempt + 1}/{retry_count} failed: {error_msg}")
            if attempt == retry_count - 1:
                logger.error(f"Failed to send message after {retry_count} attempts: {error_msg}")
                return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    return False, "Max retries exceeded"


def send_order_notification(order_id):
    """
    Send order notification to appropriate channels based on routing rules.
    
    Routing Rules:
    1. ALWAYS send to center.company_orders_channel_id (if configured)
    2. If B2C customer -> send to branch.b2c_orders_channel_id (if configured)
    3. If B2B customer -> send to branch.b2b_orders_channel_id (if configured)
    
    Args:
        order_id: The ID of the order to notify about
    
    Returns:
        dict: Results of notification attempts
    """
    from orders.models import Order
    
    results = {
        'order_id': order_id,
        'company_channel': {'sent': False, 'error': None},
        'branch_channel': {'sent': False, 'error': None, 'type': None},
    }
    
    try:
        order = Order.objects.select_related(
            'branch__center', 'bot_user', 'product'
        ).get(id=order_id)
    except Order.DoesNotExist:
        results['error'] = f"Order {order_id} not found"
        logger.error(results['error'])
        return results
    
    # Get center and branch
    branch = order.branch
    if not branch:
        results['error'] = "Order has no branch assigned"
        logger.error(results['error'])
        return results
    
    center = branch.center
    if not center:
        results['error'] = "Branch has no center"
        logger.error(results['error'])
        return results
    
    # Check if center has bot token
    bot_token = center.bot_token
    if not bot_token:
        results['error'] = "Center has no bot token configured"
        logger.warning(results['error'])
        return results
    
    # Format the message
    message = format_order_message(order)
    
    # 1. Send to company orders channel (always)
    if center.company_orders_channel_id:
        success, error = send_message_to_channel(
            bot_token, 
            center.company_orders_channel_id, 
            message
        )
        results['company_channel'] = {'sent': success, 'error': error}
    else:
        results['company_channel']['error'] = "Company channel not configured"
    
    # 2. Determine B2C or B2B and send to appropriate branch channel
    is_b2b = order.bot_user.is_agency if order.bot_user else False
    
    if is_b2b:
        # B2B order
        results['branch_channel']['type'] = 'B2B'
        if branch.b2b_orders_channel_id:
            success, error = send_message_to_channel(
                bot_token,
                branch.b2b_orders_channel_id,
                message
            )
            results['branch_channel']['sent'] = success
            results['branch_channel']['error'] = error
        else:
            results['branch_channel']['error'] = "B2B channel not configured for branch"
    else:
        # B2C order
        results['branch_channel']['type'] = 'B2C'
        if branch.b2c_orders_channel_id:
            success, error = send_message_to_channel(
                bot_token,
                branch.b2c_orders_channel_id,
                message
            )
            results['branch_channel']['sent'] = success
            results['branch_channel']['error'] = error
        else:
            results['branch_channel']['error'] = "B2C channel not configured for branch"
    
    # Log summary
    logger.info(
        f"Order {order_id} notification results: "
        f"company={results['company_channel']['sent']}, "
        f"branch_{results['branch_channel']['type']}={results['branch_channel']['sent']}"
    )
    
    return results


def send_order_status_update(order_id, old_status=None):
    """
    Send order status update notification.
    Similar to send_order_notification but with status change context.
    """
    from orders.models import Order
    
    try:
        order = Order.objects.select_related(
            'branch__center', 'bot_user', 'product'
        ).get(id=order_id)
    except Order.DoesNotExist:
        logger.error(f"Order {order_id} not found for status update")
        return None
    
    branch = order.branch
    if not branch or not branch.center:
        return None
    
    center = branch.center
    if not center.bot_token:
        return None
    
    # Format status update message
    status_emoji = {
        'pending': '🟡',
        'in_progress': '🔵',
        'ready': '🟢',
        'completed': '✅',
        'cancelled': '❌',
    }
    
    message = f"""
<b>📝 Order #{order.id} Status Update</b>

{status_emoji.get(order.status, '⚪')} <b>New Status:</b> {order.get_status_display()}
"""
    if old_status:
        message += f"<i>Previous: {old_status}</i>\n"
    
    message += f"""
<b>Customer:</b> {order.bot_user.display_name if order.bot_user else 'N/A'}
<b>Branch:</b> {branch.name}
"""
    
    # Send only to company channel for status updates
    if center.company_orders_channel_id:
        return send_message_to_channel(
            center.bot_token,
            center.company_orders_channel_id,
            message
        )
    
    return None
