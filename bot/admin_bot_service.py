"""
Admin Bot Notification Service

This module handles sending administrative notifications to superuser(s)
via a separate Telegram bot for:
- Contact form submissions from landing page
- Subscription renewal requests from customers

Bot: @multilang_robot
Token: 8014558483:AAFQfx4OXxWHMujEK_AXNHfqHMJxIWHy2HM

Features:
- Supports multiple recipients (users, channels, groups)
- Sends notifications to all configured Telegram IDs
- Handles individual send failures gracefully

Configuration:
- Set ADMIN_TELEGRAM_ID in settings.py or as environment variable
- Supports single ID: ADMIN_TELEGRAM_ID = "123456789"
- Supports multiple IDs: ADMIN_TELEGRAM_ID = "123456789,987654321,-1001234567890"
- Or temporarily set it in this file (ADMIN_TELEGRAM_ID variable below)
- Run: python manage.py configure_admin_bot --test to verify setup

Note: Channel/Group IDs are negative numbers (e.g., -1001234567890)
"""

import logging
import os
import telebot
from telebot.apihelper import ApiTelegramException
from django.conf import settings
from django.utils import timezone
import psutil
import time

logger = logging.getLogger(__name__)

# Admin bot PID file
ADMIN_BOT_PID_FILE = '/tmp/wowdash_admin_bot.pid'


# Duplicate Prevention Utilities

def write_admin_bot_pid():
    """Write current process PID to file"""
    try:
        with open(ADMIN_BOT_PID_FILE, 'w') as f:
            f.write(str(os.getpid()))
        logger.info(f"Created admin bot PID file with PID {os.getpid()}")
    except Exception as e:
        logger.error(f"Error writing PID file: {e}")


def remove_admin_bot_pid():
    """Remove admin bot PID file"""
    try:
        if os.path.exists(ADMIN_BOT_PID_FILE):
            os.remove(ADMIN_BOT_PID_FILE)
            logger.info("Removed admin bot PID file")
    except Exception as e:
        logger.error(f"Error removing PID file: {e}")


def kill_duplicate_admin_bots():
    """
    Kill duplicate admin bot processes.
    Returns number of processes killed.
    """
    current_pid = os.getpid()
    killed_count = 0
    
    try:
        for proc in psutil.process_iter(['pid', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline'] or [])
                # Match admin_bot command and exclude current process
                if 'manage.py admin_bot' in cmdline and proc.info['pid'] != current_pid:
                    logger.warning(f"Killing duplicate admin bot: PID {proc.info['pid']}")
                    proc.kill()
                    killed_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
    except Exception as e:
        logger.error(f"Error detecting duplicate admin bot processes: {e}")
    
    if killed_count > 0:
        logger.info(f"Killed {killed_count} duplicate admin bot process(es)")
        time.sleep(1)
    
    return killed_count


def check_admin_bot_running():
    """
    Check if admin bot is already running.
    Returns (is_running, pid) tuple.
    """
    if not os.path.exists(ADMIN_BOT_PID_FILE):
        return False, None
    
    try:
        with open(ADMIN_BOT_PID_FILE, 'r') as f:
            pid = int(f.read().strip())
        
        if psutil.pid_exists(pid):
            try:
                proc = psutil.Process(pid)
                cmdline = ' '.join(proc.cmdline())
                if 'admin_bot' in cmdline:
                    return True, pid
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # PID file exists but process is dead
        remove_admin_bot_pid()
        return False, None
        
    except Exception as e:
        logger.error(f"Error checking admin bot process: {e}")
        return False, None

# Admin bot token - separate from customer bot
ADMIN_BOT_TOKEN = getattr(settings, 'ADMIN_BOT_TOKEN', None) or os.getenv('ADMIN_BOT_TOKEN')

# Admin telegram IDs - comma-separated list of user/channel IDs who should receive notifications
# Priority: 1. settings.ADMIN_TELEGRAM_ID, 2. Environment variable, 3. Hardcoded below
ADMIN_TELEGRAM_ID = getattr(settings, 'ADMIN_TELEGRAM_ID', None) or os.getenv('ADMIN_TELEGRAM_ID')

# TODO: Replace None with your Telegram user/channel IDs (get user ID from @userinfobot)

# Parse ADMIN_TELEGRAM_ID into a list of integers
ADMIN_TELEGRAM_IDS = []
if ADMIN_TELEGRAM_ID:
    try:
        if isinstance(ADMIN_TELEGRAM_ID, (list, tuple)):
            ADMIN_TELEGRAM_IDS = [int(id) for id in ADMIN_TELEGRAM_ID]
        elif isinstance(ADMIN_TELEGRAM_ID, str):
            # Split by comma and convert to int
            ADMIN_TELEGRAM_IDS = [int(id.strip()) for id in ADMIN_TELEGRAM_ID.split(',') if id.strip()]
        else:
            ADMIN_TELEGRAM_IDS = [int(ADMIN_TELEGRAM_ID)]
        logger.info(f"Admin Telegram IDs configured: {ADMIN_TELEGRAM_IDS}")
    except (ValueError, TypeError) as e:
        logger.error(f"Invalid ADMIN_TELEGRAM_ID format: {ADMIN_TELEGRAM_ID}. Error: {e}")
        ADMIN_TELEGRAM_IDS = []

# Cache bot instance
_admin_bot = None


def get_admin_bot():
    """Get or create admin bot instance."""
    global _admin_bot
    if _admin_bot is None:
        try:
            _admin_bot = telebot.TeleBot(ADMIN_BOT_TOKEN, parse_mode="HTML", threaded=False)
            logger.info("Admin bot instance created")
        except Exception as e:
            logger.error(f"Failed to create admin bot: {e}")
            return None
    return _admin_bot


def send_contact_request_notification(contact_request):
    """
    Send notification to admin(s) when new contact request is received.
    Sends to all configured admin Telegram IDs (users and channels).
    
    Args:
        contact_request: ContactRequest model instance
    """
    logger.info(f"Attempting to send contact request notification for {contact_request.name}")
    
    if not ADMIN_TELEGRAM_IDS:
        logger.warning(f"ADMIN_TELEGRAM_IDS not configured. Current value: {ADMIN_TELEGRAM_IDS}. Skipping notification.")
        return False
    
    if not ADMIN_BOT_TOKEN:
        logger.error(f"ADMIN_BOT_TOKEN not configured. Cannot send notification.")
        return False
    
    bot = get_admin_bot()
    if not bot:
        logger.error("Admin bot not available - get_admin_bot() returned None")
        return False
    
    try:
        # Format the message
        message = f"""
🔔 <b>New Contact Request</b>

👤 <b>Name:</b> {contact_request.name}
📧 <b>Email:</b> {contact_request.email}
🏢 <b>Company:</b> {contact_request.company or 'N/A'}
📱 <b>Phone/Telegram:</b> {contact_request.phone or 'N/A'}

💬 <b>Message:</b>
{contact_request.message}

⏰ <b>Received:</b> {timezone.localtime(contact_request.created_at).strftime('%Y-%m-%d %H:%M')} (Tashkent)
📊 <b>Status:</b> {contact_request.get_status_display()}

<i>View in admin panel to respond.</i>
        """.strip()
        
        # Send to all admin IDs
        success_count = 0
        failed_ids = []
        
        for admin_id in ADMIN_TELEGRAM_IDS:
            try:
                logger.info(f"Sending message to telegram ID: {admin_id}")
                bot.send_message(
                    chat_id=admin_id,
                    text=message,
                    parse_mode="HTML"
                )
                success_count += 1
                logger.info(f"✅ Sent to {admin_id}")
            except ApiTelegramException as e:
                logger.error(f"❌ Failed to send to {admin_id}: {e}")
                failed_ids.append(admin_id)
            except Exception as e:
                logger.error(f"❌ Unexpected error sending to {admin_id}: {e}")
                failed_ids.append(admin_id)
        
        if success_count > 0:
            logger.info(f"✅ Contact request notification sent to {success_count}/{len(ADMIN_TELEGRAM_IDS)} recipients")
            if failed_ids:
                logger.warning(f"⚠️ Failed to send to: {failed_ids}")
            return True
        else:
            logger.error(f"❌ Failed to send contact notification to all recipients")
            return False
        
    except Exception as e:
        logger.error(f"❌ Unexpected error in send_contact_request_notification: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def send_renewal_request_notification(subscription_history):
    """
    Send notification to admin(s) when renewal request is submitted.
    Sends to all configured admin Telegram IDs (users and channels).
    
    Args:
        subscription_history: SubscriptionHistory model instance with action='renewal_requested'
    """
    if not ADMIN_TELEGRAM_IDS:
        logger.warning("ADMIN_TELEGRAM_IDS not configured. Skipping notification.")
        return False
    
    bot = get_admin_bot()
    if not bot:
        logger.error("Admin bot not available")
        return False
    
    try:
        subscription = subscription_history.subscription
        organization = subscription.organization
        user = subscription_history.performed_by
        
        # Format the message
        message = f"""
🔔 <b>New Subscription Renewal Request</b>

🏢 <b>Organization:</b> {organization.name}
👤 <b>Requested by:</b> {user.get_full_name() or user.username} ({user.email})

📋 <b>Current Subscription:</b>
   • Tariff: {subscription.tariff.title}
   • Ends: {subscription.end_date.strftime('%Y-%m-%d')}

📝 <b>Request Details:</b>
{subscription_history.description}

⏰ <b>Requested:</b> {timezone.localtime(subscription_history.timestamp).strftime('%Y-%m-%d %H:%M')} (Tashkent)

<i>View in admin panel to approve or reject.</i>
        """.strip()
        
        # Send to all admin IDs
        success_count = 0
        failed_ids = []
        
        for admin_id in ADMIN_TELEGRAM_IDS:
            try:
                bot.send_message(
                    chat_id=admin_id,
                    text=message,
                    parse_mode="HTML"
                )
                success_count += 1
                logger.info(f"✅ Renewal notification sent to {admin_id}")
            except ApiTelegramException as e:
                logger.error(f"❌ Failed to send renewal notification to {admin_id}: {e}")
                failed_ids.append(admin_id)
            except Exception as e:
                logger.error(f"❌ Unexpected error sending renewal notification to {admin_id}: {e}")
                failed_ids.append(admin_id)
        
        if success_count > 0:
            logger.info(f"Renewal request notification sent to {success_count}/{len(ADMIN_TELEGRAM_IDS)} recipients for {organization.name}")
            if failed_ids:
                logger.warning(f"⚠️ Failed to send to: {failed_ids}")
            return True
        else:
            logger.error(f"Failed to send renewal notification to all recipients")
            return False
        
    except Exception as e:
        logger.error(f"Error sending renewal request notification: {e}")
        return False


def set_admin_telegram_id(telegram_ids):
    """
    Set the admin telegram IDs (useful for configuration).
    
    Args:
        telegram_ids: Integer, string (comma-separated), or list of telegram user/channel IDs
    """
    global ADMIN_TELEGRAM_IDS
    try:
        if isinstance(telegram_ids, (list, tuple)):
            ADMIN_TELEGRAM_IDS = [int(id) for id in telegram_ids]
        elif isinstance(telegram_ids, str):
            ADMIN_TELEGRAM_IDS = [int(id.strip()) for id in telegram_ids.split(',') if id.strip()]
        else:
            ADMIN_TELEGRAM_IDS = [int(telegram_ids)]
        logger.info(f"Admin telegram IDs set to {ADMIN_TELEGRAM_IDS}")
    except (ValueError, TypeError) as e:
        logger.error(f"Invalid telegram_ids format: {telegram_ids}. Error: {e}")
        ADMIN_TELEGRAM_IDS = []


# ============================================================================
# Bot Command Handlers (for incoming messages)
# ============================================================================

def setup_bot_handlers():
    """
    Setup message handlers for the admin bot.
    These handlers respond to commands sent to the bot.
    """
    bot = get_admin_bot()
    if not bot:
        logger.error("Cannot setup handlers - admin bot not available")
        return None
    
    @bot.message_handler(commands=['start', 'help'])
    def handle_start(message):
        """Handle /start and /help commands"""
        user_id = message.from_user.id
        username = message.from_user.username or message.from_user.first_name
        
        welcome_text = f"""
👋 <b>Welcome to MultiLang Admin Bot!</b>

Hello, {username}!

<b>Your Telegram ID:</b> <code>{user_id}</code>

This bot sends administrative notifications for:
• 📧 Contact form submissions from landing page
• 🔄 Subscription renewal requests

<b>Available Commands:</b>
/start or /help - Show this message
/myid - Get your Telegram ID
/status - Check bot configuration
/stats - View notification statistics (coming soon)

<i>Only authorized administrators receive notifications.</i>
        """
        
        try:
            bot.reply_to(message, welcome_text, parse_mode="HTML")
            logger.info(f"Sent welcome message to user {user_id} (@{username})")
        except Exception as e:
            logger.error(f"Failed to send welcome message: {e}")
    
    @bot.message_handler(commands=['myid'])
    def handle_myid(message):
        """Handle /myid command - show user their Telegram ID"""
        user_id = message.from_user.id
        username = message.from_user.username or message.from_user.first_name
        
        # Check if user is in admin list
        is_admin = user_id in ADMIN_TELEGRAM_IDS
        
        id_text = f"""
🆔 <b>Your Telegram Information</b>

<b>User ID:</b> <code>{user_id}</code>
<b>Username:</b> @{message.from_user.username or 'None'}
<b>Name:</b> {message.from_user.first_name} {message.from_user.last_name or ''}

<b>Admin Status:</b> {'✅ Authorized' if is_admin else '❌ Not authorized'}

<i>Copy your User ID to add it to ADMIN_TELEGRAM_ID configuration.</i>
        """
        
        try:
            bot.reply_to(message, id_text, parse_mode="HTML")
            logger.info(f"Sent ID info to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send ID info: {e}")
    
    @bot.message_handler(commands=['status'])
    def handle_status(message):
        """Handle /status command - show bot configuration status"""
        user_id = message.from_user.id
        
        # Check if user is admin
        if user_id not in ADMIN_TELEGRAM_IDS:
            bot.reply_to(message, "⛔ This command is only available for authorized administrators.")
            return
        
        status_text = f"""
⚙️ <b>Admin Bot Status</b>

<b>Bot:</b> @multilang_robot
<b>Status:</b> ✅ Running

<b>Configured Recipients:</b> {len(ADMIN_TELEGRAM_IDS)}
"""
        
        for admin_id in ADMIN_TELEGRAM_IDS:
            id_type = 'Channel/Group' if admin_id < 0 else 'User'
            is_you = '(You)' if admin_id == user_id else ''
            status_text += f"\n  • {admin_id} - {id_type} {is_you}"
        
        status_text += "\n\n<b>Notification Types:</b>"
        status_text += "\n  ✅ Contact form submissions"
        status_text += "\n  ✅ Subscription renewal requests"
        
        try:
            bot.reply_to(message, status_text, parse_mode="HTML")
            logger.info(f"Sent status info to admin {user_id}")
        except Exception as e:
            logger.error(f"Failed to send status: {e}")
    
    @bot.message_handler(func=lambda message: True)
    def handle_unknown(message):
        """Handle all other messages"""
        help_text = """
ℹ️ Unknown command. Use /help to see available commands.
        """
        try:
            bot.reply_to(message, help_text)
        except Exception as e:
            logger.error(f"Failed to send help message: {e}")
    
    logger.info("Admin bot handlers setup complete")
    return bot


def start_bot_polling():
    """
    Start the bot polling to listen for incoming messages.
    This is a blocking call - runs indefinitely until interrupted.
    """
    # ===== AUTOMATED DUPLICATE PREVENTION =====
    is_running, existing_pid = check_admin_bot_running()
    
    if is_running and existing_pid:
        logger.warning(f"Admin bot already running (PID: {existing_pid})")
        try:
            proc = psutil.Process(existing_pid)
            if proc.is_running():
                logger.error(f"Another instance is already running. Exiting to prevent 409 conflicts.")
                return
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    # Kill any duplicate/zombie processes
    logger.info("Checking for duplicate admin bot processes...")
    killed = kill_duplicate_admin_bots()
    
    if killed > 0:
        logger.info(f"Cleaned up {killed} duplicate admin bot process(es)")
    
    # Write PID file for this process
    write_admin_bot_pid()
    
    # Register cleanup on exit
    import atexit
    atexit.register(remove_admin_bot_pid)
    # ===== END DUPLICATE PREVENTION =====
    
    bot = setup_bot_handlers()
    if not bot:
        logger.error("Cannot start polling - bot setup failed")
        remove_admin_bot_pid()
        return
    
    logger.info("🤖 Starting admin bot polling...")
    logger.info(f"Bot: @multilang_robot")
    logger.info(f"Configured admins: {ADMIN_TELEGRAM_IDS}")
    
    try:
        # Remove any existing webhooks (in case they were set before)
        bot.remove_webhook()
        logger.info("Removed any existing webhooks")
        
        # Start polling with auto-reconnect on network errors
        bot.infinity_polling(
            timeout=30,
            long_polling_timeout=30,
            logger_level=logging.INFO,
            allowed_updates=['message']
        )
    except KeyboardInterrupt:
        logger.info("Admin bot polling stopped by user")
        remove_admin_bot_pid()
    except Exception as e:
        logger.error(f"Error during bot polling: {e}")
        remove_admin_bot_pid()
        raise
