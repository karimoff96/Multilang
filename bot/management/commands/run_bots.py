"""
Multi-tenant Telegram Bot Polling Command

This command runs all configured Telegram bots in polling mode for local development.
Each Translation Center with a bot_token will have its bot started in a separate thread.

Usage:
    python manage.py run_bots              # Run all bots
    python manage.py run_bots --center-id 1  # Run only specific center's bot
    python manage.py run_bots --list         # List all centers
    python manage.py run_bots --reload       # Auto-reload on file changes
"""
import threading
import time
import signal
import sys
import os
import subprocess
import psutil
from django.core.management.base import BaseCommand
from organizations.models import TranslationCenter
from bot.webhook_manager import get_ssl_session
import telebot
from telebot import apihelper
import logging

logger = logging.getLogger(__name__)

# PID file directory
PID_DIR = '/tmp/wowdash_bots'

# Try to import watchdog for auto-reload functionality
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, PatternMatchingEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    logger.warning("watchdog not installed. Auto-reload won't be available. Run: pip install watchdog")


# Process Management Functions

def ensure_pid_dir():
    """Ensure PID directory exists"""
    os.makedirs(PID_DIR, exist_ok=True)


def get_pid_file(center_id=None):
    """Get PID file path for a center or all bots"""
    ensure_pid_dir()
    if center_id:
        return os.path.join(PID_DIR, f'bot_center_{center_id}.pid')
    return os.path.join(PID_DIR, 'bot_all.pid')


def write_pid_file(center_id=None):
    """Write current process PID to file"""
    pid_file = get_pid_file(center_id)
    with open(pid_file, 'w') as f:
        f.write(str(os.getpid()))
    logger.info(f"Created PID file: {pid_file} with PID {os.getpid()}")


def remove_pid_file(center_id=None):
    """Remove PID file"""
    pid_file = get_pid_file(center_id)
    try:
        if os.path.exists(pid_file):
            os.remove(pid_file)
            logger.info(f"Removed PID file: {pid_file}")
    except Exception as e:
        logger.error(f"Error removing PID file {pid_file}: {e}")


def kill_duplicate_processes(center_id=None, current_pid=None):
    """
    Kill duplicate bot processes for the same center.
    Returns number of processes killed.
    """
    if current_pid is None:
        current_pid = os.getpid()
    
    killed_count = 0
    pattern = f"run_bots --center-id={center_id}" if center_id else "run_bots"
    
    try:
        # Find all matching processes
        for proc in psutil.process_iter(['pid', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline'] or [])
                # Match the pattern and exclude current process
                if pattern in cmdline and proc.info['pid'] != current_pid:
                    logger.warning(f"Killing duplicate process: PID {proc.info['pid']}, CMD: {cmdline}")
                    proc.kill()
                    killed_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
    except Exception as e:
        logger.error(f"Error detecting duplicate processes: {e}")
    
    if killed_count > 0:
        logger.info(f"Killed {killed_count} duplicate bot process(es)")
        time.sleep(1)  # Wait for processes to fully terminate
    
    return killed_count


def check_existing_process(center_id=None):
    """
    Check if a bot process is already running for this center.
    Returns (is_running, pid) tuple.
    """
    pid_file = get_pid_file(center_id)
    
    if not os.path.exists(pid_file):
        return False, None
    
    try:
        with open(pid_file, 'r') as f:
            pid = int(f.read().strip())
        
        # Check if process is actually running
        if psutil.pid_exists(pid):
            try:
                proc = psutil.Process(pid)
                cmdline = ' '.join(proc.cmdline())
                if 'run_bots' in cmdline:
                    return True, pid
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # PID file exists but process is dead - clean up
        remove_pid_file(center_id)
        return False, None
        
    except Exception as e:
        logger.error(f"Error checking existing process: {e}")
        return False, None


def copy_handlers_from_template(template_bot, target_bot):
    """
    Copy all handlers from template bot to target bot.
    The template bot is just used to get the handler definitions.
    """
    # Copy message handlers
    target_bot.message_handlers = template_bot.message_handlers.copy()
    
    # Copy callback query handlers  
    target_bot.callback_query_handlers = template_bot.callback_query_handlers.copy()
    
    # Copy other handlers
    target_bot.inline_handlers = template_bot.inline_handlers.copy()
    target_bot.chosen_inline_handlers = template_bot.chosen_inline_handlers.copy()
    target_bot.edited_message_handlers = template_bot.edited_message_handlers.copy()


class BotThread(threading.Thread):
    """Thread class for running a single bot with polling"""
    
    def __init__(self, center, bot_instance, stdout):
        super().__init__(daemon=True)
        self.center = center
        self.bot = bot_instance  # This is the actual bot object (telebot.TeleBot)
        self.running = True
        self.stdout = stdout
        self.name = f"Bot-{center.id}-{center.name}"
    
    def run(self):
        """Run the bot with infinity polling"""
        logger.info(f"Starting bot for center: {self.center.name} (ID: {self.center.id})")
        
        try:
            # Remove any existing webhook first
            self.bot.remove_webhook()
            time.sleep(0.5)  # Brief pause to ensure webhook is cleared
            
            # Start polling
            while self.running:
                try:
                    self.bot.infinity_polling(
                        timeout=30, 
                        long_polling_timeout=25,
                        allowed_updates=["message", "callback_query"]
                    )
                except Exception as e:
                    logger.error(f"Bot {self.center.name} polling error: {e}")
                    if self.running:
                        logger.info(f"Restarting bot {self.center.name} in 5 seconds...")
                        time.sleep(5)
        except Exception as e:
            logger.error(f"Bot thread for {self.center.name} crashed: {e}")
    
    def stop(self):
        """Stop the bot polling"""
        self.running = False
        try:
            self.bot.stop_polling()
        except Exception:
            pass


class BotFileWatcher(PatternMatchingEventHandler if WATCHDOG_AVAILABLE else object):
    """
    Watches for file changes in the bot directory and triggers reload.
    """
    
    def __init__(self, callback, stdout, patterns=None):
        if WATCHDOG_AVAILABLE:
            super().__init__(
                patterns=patterns or ['*.py'],
                ignore_patterns=['*__pycache__*', '*.pyc', '*migrations*'],
                ignore_directories=True,
                case_sensitive=True
            )
        self.callback = callback
        self.stdout = stdout
        self.last_reload = 0
        self.debounce_seconds = 2  # Prevent multiple reloads for same change
    
    def on_modified(self, event):
        self._handle_change(event)
    
    def on_created(self, event):
        self._handle_change(event)
    
    def _handle_change(self, event):
        """Handle file change with debouncing"""
        current_time = time.time()
        
        # Debounce - ignore if we just reloaded
        if current_time - self.last_reload < self.debounce_seconds:
            return
        
        self.last_reload = current_time
        
        # Get relative path for display
        try:
            rel_path = os.path.relpath(event.src_path)
        except ValueError:
            rel_path = event.src_path
        
        self.stdout.write(
            f'\n  🔄 File changed: {rel_path}\n'
            f'  ⏳ Reloading bots...\n'
        )
        
        self.callback()


class AutoReloadBotRunner:
    """
    Runs bots with auto-reload on file changes.
    Uses subprocess isolation for clean reloads.
    """
    
    def __init__(self, stdout, stderr, watch_paths=None):
        self.stdout = stdout
        self.stderr = stderr
        self.watch_paths = watch_paths or []
        self.process = None
        self.running = True
        self.observer = None
        self.center_id = None
    
    def start_bot_process(self):
        """Start the bot subprocess"""
        import subprocess
        
        manage_py = os.path.join(os.getcwd(), 'manage.py')
        
        cmd = [sys.executable, manage_py, 'run_bots', '--no-reload']
        if self.center_id:
            cmd.append(f'--center-id={self.center_id}')
        
        self.process = subprocess.Popen(
            cmd,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        
        return self.process
    
    def reload(self):
        """Reload the bot by restarting the subprocess"""
        if self.process:
            self.stdout.write('  🛑 Stopping current bot process...\n')
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except:
                self.process.kill()
                self.process.wait()
        
        self.stdout.write('  🚀 Starting new bot process...\n')
        self.start_bot_process()
        self.stdout.write('  ✅ Bot reloaded successfully!\n\n')
    
    def run(self, center_id=None):
        """Run with file watching"""
        self.center_id = center_id
        
        if not WATCHDOG_AVAILABLE:
            self.stderr.write(
                '\n  ❌ watchdog library not installed!\n'
                '  Run: pip install watchdog\n\n'
            )
            return
        
        # Start the bot process
        self.stdout.write('\n  🔍 Starting file watcher for auto-reload...\n')
        self.start_bot_process()
        
        # Set up file watcher
        self.observer = Observer()
        handler = BotFileWatcher(self.reload, self.stdout)
        
        # Watch the bot directory and related directories
        for path in self.watch_paths:
            if os.path.exists(path):
                self.observer.schedule(handler, path, recursive=True)
                self.stdout.write(f'  👁️  Watching: {path}\n')
        
        self.observer.start()
        
        self.stdout.write(
            f'\n  ✅ Auto-reload enabled! Watching for file changes...\n'
            f'  📝 Edit any .py file in watched directories to trigger reload.\n'
            f'  Press Ctrl+C to stop.\n\n'
        )
        
        try:
            while self.running:
                if self.process.poll() is not None:
                    # Process exited unexpectedly
                    if self.running:
                        self.stdout.write('  ⚠️  Bot process exited. Restarting in 3 seconds...\n')
                        time.sleep(3)
                        self.start_bot_process()
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Shutdown watcher and bot process"""
        self.running = False
        
        if self.observer:
            self.observer.stop()
            self.observer.join(timeout=2)
        
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except:
                self.process.kill()


class MultiCenterBotRunner:
    """
    Runs multiple bots for different centers using subprocess-based isolation.
    Each center's bot runs in its own subprocess for better isolation.
    """
    
    def __init__(self, stdout, stderr):
        self.stdout = stdout
        self.stderr = stderr
        self.processes = []
        self.running = True
    
    def start_bot_subprocess(self, center_id):
        """Start a bot in a subprocess"""
        import subprocess
        import os
        
        # Get the manage.py path
        manage_py = os.path.join(os.getcwd(), 'manage.py')
        
        # Start the subprocess
        process = subprocess.Popen(
            [sys.executable, manage_py, 'run_bots', f'--center-id={center_id}'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        return process
    
    def run_all(self, centers):
        """Run all center bots in separate subprocesses"""
        for center in centers:
            try:
                process = self.start_bot_subprocess(center.id)
                self.processes.append((center, process))
                self.stdout.write(f'  📱 Started subprocess for: {center.name} (PID: {process.pid})\n')
            except Exception as e:
                self.stderr.write(f'  ❌ Failed to start bot for {center.name}: {e}\n')
        
        return len(self.processes) > 0
    
    def monitor(self):
        """Monitor all subprocesses"""
        while self.running and self.processes:
            # Check processes and remove dead ones
            still_running = []
            for center, process in self.processes:
                # Check if process is still running
                if process.poll() is None:
                    # Process is still alive
                    still_running.append((center, process))
                else:
                    # Process has exited
                    self.stdout.write(f'  ⚠️ Bot for {center.name} stopped (exit code: {process.returncode})\n')
            
            # Update the process list to only include running processes
            self.processes = still_running
            
            # If no processes left, exit monitoring
            if not self.processes:
                self.stdout.write('  All bot processes have stopped.\n')
                break
            
            time.sleep(1)
    
    def shutdown(self):
        """Shutdown all subprocesses"""
        self.running = False
        self.stdout.write('  Terminating all bot processes...\n')
        
        for center, process in self.processes:
            try:
                self.stdout.write(f'  Stopping bot for {center.name}...\n')
                process.terminate()
            except Exception as e:
                self.stderr.write(f'  Error terminating {center.name}: {e}\n')
        
        # Wait for processes to terminate gracefully
        time.sleep(2)
        
        # Force kill any remaining processes
        for center, process in self.processes:
            if process.poll() is None:
                try:
                    self.stdout.write(f'  Force killing bot for {center.name}...\n')
                    process.kill()
                    process.wait(timeout=2)
                except Exception as e:
                    self.stderr.write(f'  Error killing {center.name}: {e}\n')
        
        self.processes = []
        self.stdout.write('  All bot processes terminated.\n')


class Command(BaseCommand):
    help = 'Run all Telegram bots with polling (for local development)'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot_threads = []
        self.running = True
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--center-id',
            type=int,
            help='Run only a specific center\'s bot'
        )
        parser.add_argument(
            '--list',
            action='store_true',
            help='List all centers with bot tokens configured'
        )
        parser.add_argument(
            '--reload',
            action='store_true',
            help='Enable auto-reload on file changes (requires watchdog)'
        )
        parser.add_argument(
            '--no-reload',
            action='store_true',
            help='Disable auto-reload (used internally by reload wrapper)'
        )
    
    def handle(self, *args, **options):
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        if options.get('list'):
            self.list_centers()
            return
        
        center_id = options.get('center_id')
        use_reload = options.get('reload', False)
        no_reload = options.get('no_reload', False)
        
        # ===== AUTOMATED DUPLICATE PREVENTION =====
        # Check if a bot is already running for this center (or all bots)
        is_running, existing_pid = check_existing_process(center_id)
        
        if is_running and existing_pid:
            self.stdout.write(self.style.WARNING(
                f'\n⚠️  Bot already running (PID: {existing_pid})\n'
            ))
            # Try to verify it's actually responding
            try:
                proc = psutil.Process(existing_pid)
                if proc.is_running():
                    self.stdout.write(self.style.ERROR(
                        f'❌ Another instance is already running. Exiting.\n'
                        f'   To force restart: kill {existing_pid}\n'
                    ))
                    return
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Kill any duplicate/zombie processes before starting
        self.stdout.write(self.style.WARNING('🔍 Checking for duplicate processes...\n'))
        killed = kill_duplicate_processes(center_id, os.getpid())
        
        if killed > 0:
            self.stdout.write(self.style.SUCCESS(
                f'✅ Cleaned up {killed} duplicate process(es)\n'
            ))
        else:
            self.stdout.write('✓ No duplicates found\n')
        
        # Write PID file for this process
        write_pid_file(center_id)
        
        # Register cleanup on exit
        import atexit
        atexit.register(lambda: remove_pid_file(center_id))
        # ===== END DUPLICATE PREVENTION =====
        
        # If --reload flag is used, start the auto-reload wrapper
        if use_reload and not no_reload:
            self.stdout.write(self.style.SUCCESS(
                f'\n{"="*60}\n'
                f'  🔄 Auto-Reload Mode Enabled\n'
                f'{"="*60}\n'
            ))
            
            # Directories to watch for changes
            watch_paths = [
                os.path.join(os.getcwd(), 'bot'),
                os.path.join(os.getcwd(), 'orders'),
                os.path.join(os.getcwd(), 'services'),
                os.path.join(os.getcwd(), 'organizations'),
                os.path.join(os.getcwd(), 'accounts'),
                os.path.join(os.getcwd(), 'core'),
            ]
            
            runner = AutoReloadBotRunner(self.stdout, self.stderr, watch_paths)
            try:
                runner.run(center_id)
            except KeyboardInterrupt:
                pass
            finally:
                runner.shutdown()
            return
        
        # Get centers with bot tokens
        
        # Get centers with bot tokens
        if center_id:
            centers = TranslationCenter.objects.filter(
                id=center_id,
                bot_token__isnull=False,
                is_active=True
            ).exclude(bot_token='')
            
            if not centers.exists():
                self.stderr.write(self.style.ERROR(
                    f'Center {center_id} not found or has no bot token configured'
                ))
                return
        else:
            centers = TranslationCenter.objects.filter(
                bot_token__isnull=False,
                is_active=True
            ).exclude(bot_token='')
        
        if not centers.exists():
            self.stderr.write(self.style.WARNING(
                'No centers with bot tokens found. '
                'Configure a bot token in the admin panel for your Translation Center.'
            ))
            return
        
        self.stdout.write(self.style.SUCCESS(
            f'\n{"="*60}\n'
            f'  Multi-Tenant Bot Manager - Starting {centers.count()} bot(s)\n'
            f'{"="*60}\n'
        ))
        
        # Set up SSL session for all bots
        apihelper.SESSION = get_ssl_session()
        
        # If running all bots (no center_id), use subprocesses for isolation
        if not center_id and centers.count() > 1:
            self.stdout.write(self.style.WARNING(
                '\n  Running multiple bots using subprocesses for isolation...\n'
            ))
            
            runner = MultiCenterBotRunner(self.stdout, self.stderr)
            if runner.run_all(centers):
                self.stdout.write(self.style.SUCCESS(
                    f'\n✅ {len(runner.processes)} bot(s) running in subprocesses. Press Ctrl+C to stop.\n'
                ))
                try:
                    runner.monitor()
                except KeyboardInterrupt:
                    pass
                finally:
                    runner.shutdown()
            return
        
        # Import the bot module and update the global bot's token
        # This is necessary because handlers use the global 'bot' object
        import bot.main as bot_module
        
        # Start a bot thread for each center (single bot mode)
        for center in centers:
            self.start_bot_for_center(center, bot_module)
        
        if not self.bot_threads:
            self.stderr.write(self.style.ERROR('No bots were started'))
            return
        
        self.stdout.write(self.style.SUCCESS(
            f'\n✅ {len(self.bot_threads)} bot(s) running. Press Ctrl+C to stop.\n'
        ))
        
        # Keep main thread alive
        try:
            while self.running:
                # Check if all threads are still alive
                alive_threads = [t for t in self.bot_threads if t.is_alive()]
                if not alive_threads:
                    self.stdout.write(self.style.WARNING('All bot threads have stopped'))
                    break
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            self.shutdown()
    
    def start_bot_for_center(self, center, bot_module):
        """Create and start a bot thread for a center"""
        try:
            # IMPORTANT: Replace the global bot's token with this center's token
            # This is necessary because all handlers reference the global 'bot' object
            bot_module.bot.token = center.bot_token
            
            self.stdout.write(
                f'  📱 Starting bot for: {self.style.SUCCESS(center.name)}\n'
                f'     Token: {center.bot_token[:20]}...{center.bot_token[-10:]}\n'
            )
            
            # Create and start thread using the global bot (now with correct token)
            thread = BotThread(center, bot_module.bot, self.stdout)
            thread.start()
            self.bot_threads.append(thread)
            
        except Exception as e:
            self.stderr.write(self.style.ERROR(
                f'  ❌ Failed to start bot for {center.name}: {e}'
            ))
            import traceback
            traceback.print_exc()
    
    def list_centers(self):
        """List all centers and their bot configuration"""
        centers = TranslationCenter.objects.all()
        
        self.stdout.write(self.style.SUCCESS('\nTranslation Centers:\n' + '='*60))
        
        for center in centers:
            has_token = bool(center.bot_token)
            status = self.style.SUCCESS('✅ Token configured') if has_token else self.style.WARNING('❌ No token')
            active = self.style.SUCCESS('Active') if center.is_active else self.style.ERROR('Inactive')
            
            self.stdout.write(
                f'\n  ID: {center.id}\n'
                f'  Name: {center.name}\n'
                f'  Owner: {center.owner}\n'
                f'  Status: {active}\n'
                f'  Bot: {status}\n'
            )
            
            if has_token:
                self.stdout.write(f'  Token: {center.bot_token[:15]}...{center.bot_token[-8:]}\n')
                
                if center.company_orders_channel_id:
                    self.stdout.write(f'  Company Channel: {center.company_orders_channel_id}\n')
        
        self.stdout.write('\n' + '='*60 + '\n')
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.stdout.write(self.style.WARNING('\n\nShutdown signal received...'))
        self.running = False
    
    def shutdown(self):
        """Gracefully shut down all bot threads"""
        self.stdout.write(self.style.WARNING('\nStopping all bots...'))
        
        for thread in self.bot_threads:
            thread.stop()
        
        # Wait for threads to finish
        for thread in self.bot_threads:
            thread.join(timeout=5)
        
        self.stdout.write(self.style.SUCCESS('All bots stopped. Goodbye! 👋\n'))
