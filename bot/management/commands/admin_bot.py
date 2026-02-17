"""
Unified admin bot management command
Combines configuration, testing, and running the bot
"""
from django.core.management.base import BaseCommand
from bot.admin_bot_service import (
    start_bot_polling, 
    ADMIN_TELEGRAM_IDS, 
    ADMIN_BOT_TOKEN,
    get_admin_bot
)
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Manage admin bot: configure, test, or start the bot listener'

    def add_arguments(self, parser):
        parser.add_argument(
            '--configure',
            action='store_true',
            help='Show bot configuration and setup instructions',
        )
        parser.add_argument(
            '--test',
            action='store_true',
            help='Send a test notification to verify setup',
        )

    def handle(self, *args, **options):
        configure_mode = options['configure']
        test_mode = options['test']
        
        # If configure or test flags provided, show configuration
        if configure_mode or test_mode:
            self._show_configuration()
        
        # If test flag provided, send test notification
        if test_mode:
            self._send_test_notification()
        
        # If no flags provided, start the bot (default behavior)
        if not configure_mode and not test_mode:
            self._start_bot()
    
    def _show_configuration(self):
        """Show bot configuration and setup instructions"""
        self.stdout.write(self.style.SUCCESS('\n=== Admin Bot Configuration ===\n'))
        
        # Show bot info
        bot = get_admin_bot()
        if not bot:
            self.stdout.write(self.style.ERROR('Failed to initialize admin bot'))
            return
        
        try:
            bot_info = bot.get_me()
            self.stdout.write(f'🤖 Bot: @{bot_info.username}')
            self.stdout.write(f'📝 Bot Name: {bot_info.first_name}\n')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error getting bot info: {e}\n'))
        
        # Show current admin IDs
        if ADMIN_TELEGRAM_IDS:
            self.stdout.write(f'✅ Admin Telegram IDs ({len(ADMIN_TELEGRAM_IDS)}):')
            for admin_id in ADMIN_TELEGRAM_IDS:
                id_type = 'Channel/Group' if admin_id < 0 else 'User'
                self.stdout.write(f'   • {admin_id} ({id_type})')
            self.stdout.write('')
        else:
            self.stdout.write(self.style.WARNING('⚠️ Admin Telegram IDs not configured!\n'))
        
        # Instructions to get telegram ID
        self.stdout.write(self.style.WARNING('📋 To get your Telegram ID:'))
        self.stdout.write('  1. Open Telegram and search for @multilang_robot')
        self.stdout.write('  2. Start a chat with the bot (/start or /myid)')
        self.stdout.write('  3. Or use @userinfobot - send it any message')
        self.stdout.write('  4. For channels/groups: Add bot as admin, then use /myid\n')
        
        # Show where to configure
        self.stdout.write(self.style.WARNING('⚙️ To configure Admin Telegram IDs:'))
        self.stdout.write('  Supports multiple IDs (users, channels, groups) - comma separated\n')
        self.stdout.write('  Examples:')
        self.stdout.write('    • Single:   ADMIN_TELEGRAM_ID = "123456789"')
        self.stdout.write('    • Multiple: ADMIN_TELEGRAM_ID = "123456789,987654321,-1001234567890"')
        self.stdout.write('    • Note: Channel IDs are negative numbers\n')
        self.stdout.write('  Configuration options:')
        self.stdout.write('    1. Set in .env file: ADMIN_TELEGRAM_ID=123456789')
        self.stdout.write('    2. Add to settings.py: ADMIN_TELEGRAM_ID = "123456789"')
        self.stdout.write('    3. Set in bot/admin_bot_service.py (ADMIN_TELEGRAM_ID variable)\n')
    
    def _send_test_notification(self):
        """Send test notification to configured admin IDs"""
        self.stdout.write(self.style.SUCCESS('=== Testing Notifications ===\n'))
        
        if not ADMIN_TELEGRAM_IDS:
            self.stdout.write(self.style.ERROR('❌ Cannot send test: ADMIN_TELEGRAM_IDS not configured'))
            return
        
        bot = get_admin_bot()
        if not bot:
            self.stdout.write(self.style.ERROR('❌ Failed to initialize admin bot'))
            return
        
        try:
            test_message = """
🔔 <b>Admin Bot Test Notification</b>

✅ Admin bot is configured correctly!

You will receive notifications for:
• 📧 Contact form submissions from landing page
• 🔄 Subscription renewal requests from customers

<i>This is a test message from Django management command.</i>
            """.strip()
            
            success_count = 0
            failed_ids = []
            
            for admin_id in ADMIN_TELEGRAM_IDS:
                try:
                    bot.send_message(
                        chat_id=admin_id,
                        text=test_message,
                        parse_mode="HTML"
                    )
                    id_type = 'Channel/Group' if admin_id < 0 else 'User'
                    self.stdout.write(self.style.SUCCESS(f'✅ Test sent to {admin_id} ({id_type})'))
                    success_count += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'❌ Failed to send to {admin_id}: {e}'))
                    failed_ids.append(admin_id)
            
            self.stdout.write('')
            if success_count > 0:
                self.stdout.write(self.style.SUCCESS(
                    f'✅ Successfully sent {success_count}/{len(ADMIN_TELEGRAM_IDS)} test notifications'
                ))
                self.stdout.write('   Check your Telegram to verify you received it.\n')
            
            if failed_ids:
                self.stdout.write(self.style.WARNING(f'⚠️ Failed to send to: {failed_ids}'))
                self.stdout.write('   Make sure:')
                self.stdout.write('   1. You have started a chat with @multilang_robot (for users)')
                self.stdout.write('   2. The bot is added as admin (for channels/groups)')
                self.stdout.write('   3. The Telegram IDs are correct')
                self.stdout.write('   4. The bot token is valid\n')
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Failed to send test notification: {e}\n'))
    
    def _start_bot(self):
        """Start the bot listener (long polling)"""
        self.stdout.write(self.style.SUCCESS('\n=== Starting Admin Bot Listener ===\n'))
        
        # Check configuration
        if not ADMIN_BOT_TOKEN:
            self.stdout.write(self.style.ERROR('❌ ADMIN_BOT_TOKEN not configured!'))
            self.stdout.write('   Set it in settings.py or as environment variable.\n')
            return
        
        if not ADMIN_TELEGRAM_IDS:
            self.stdout.write(self.style.WARNING('⚠️ Warning: ADMIN_TELEGRAM_IDS not configured.'))
            self.stdout.write('   The bot will start but no one will receive notifications.')
            self.stdout.write('   Set ADMIN_TELEGRAM_ID in settings.py or environment variable.\n')
        else:
            self.stdout.write(f'✅ Bot token configured')
            self.stdout.write(f'✅ Admin recipients: {len(ADMIN_TELEGRAM_IDS)}')
            for admin_id in ADMIN_TELEGRAM_IDS:
                id_type = 'Channel/Group' if admin_id < 0 else 'User'
                self.stdout.write(f'   • {admin_id} ({id_type})')
            self.stdout.write('')
        
        self.stdout.write('🤖 Bot: @multilang_robot')
        self.stdout.write('📡 Mode: Long polling')
        self.stdout.write('')
        self.stdout.write('📱 Available commands for users:')
        self.stdout.write('   /start  - Welcome message with user ID')
        self.stdout.write('   /myid   - Get your Telegram ID')
        self.stdout.write('   /status - View bot configuration (admins only)')
        self.stdout.write('   /help   - Show help message')
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('🚀 Starting bot... Press Ctrl+C to stop\n'))
        
        try:
            # Start polling (blocking call)
            start_bot_polling()
        except KeyboardInterrupt:
            self.stdout.write(self.style.SUCCESS('\n\n✋ Bot stopped by user'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Bot error: {e}'))
            raise
