# management/commands/run_bot.py
from django.core.management.base import BaseCommand
from bot.main import bot  # Import your existing bot instance


class Command(BaseCommand):
    help = "Run Telegram bot with polling"

    def handle(self, *args, **kwargs):
        # Remove webhook first
        bot.remove_webhook()

        self.stdout.write(self.style.SUCCESS("Bot started with polling..."))

        # Start polling with your existing bot
        bot.infinity_polling()
