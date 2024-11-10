import os
import sys
import asyncio
import logging
import json
from typing import Dict, Any
from datetime import datetime

# Import necessary modules
from telegram import Update
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    filters, 
    ContextTypes
)

# Import custom modules
from utils.config_manager import ConfigManager
from utils.logger import TelegramLogger
from utils.notification_manager import NotificationManager
from utils.bandwidth_tracker import BandwidthTracker
from utils.media_analyzer import MediaAnalyzer


class MusicDownloadBot:
    def __init__(self):
        # Configure logging
        self._setup_logging()

        # Initialize core components
        self.config_manager = ConfigManager(config_path="config/config.json") 

        # Load bot token from config.json
        self.config = self.config_manager.load_config()
        self.bot_token = self.config.get("BOT_TOKEN")
        if not self.bot_token:
            logging.critical("No Telegram Bot Token found in config!")
            sys.exit(1)

        # Initialize other components
        self.database_manager = DatabaseManager()
        self.notification_manager = NotificationManager(config=self.config)
        self.bandwidth_tracker = BandwidthTracker()
        self.media_analyzer = MediaAnalyzer()
        self.telegram_logger = TelegramLogger(log_channel_id=self.config.get('LOG_CHANNEL_ID'))

    def _setup_logging(self):
        """Configure logging settings"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('bot.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )

    async def initialize_bot(self):
        """Initialize bot and its components"""
        try:
            # Initialize Telegram Bot
            self.application = Application.builder().token(self.bot_token).build()
            
            # Register handlers
            self._register_handlers()
            
            logging.info("Bot initialized successfully")
            
            # Send startup notification
            await self._send_startup_notification()
        
        except Exception as e:
            logging.error(f"Bot initialization failed: {e}")
            await self.telegram_logger.log_error(e)

    def _register_handlers(self):
        """Register all bot command and message handlers"""
        # Initialize handler classes
        user_handler = UserHandler(self.database_manager, self.notification_manager)
        download_handler = DownloadHandler(self.database_manager, self.bandwidth_tracker, self.notification_manager)
        admin_handler = AdminHandler(self.database_manager, self.notification_manager)

        # Command Handlers
        handlers = [
            # User Commands
            CommandHandler('start', user_handler.start_command),
            CommandHandler('help', user_handler.help_command),
            CommandHandler('stats', user_handler.get_user_stats),
            
            # Download Commands
            CommandHandler('download', download_handler.download_command),
            CommandHandler('queue', download_handler.show_download_queue),
            
            # Admin Commands
            CommandHandler('admin', admin_handler.admin_command),
            CommandHandler('broadcast', admin_handler.broadcast_command),
            
            # Message Handlers
            MessageHandler(filters.TEXT & ~filters.COMMAND, download_handler.handle_download_url)
        ]

        # Add handlers to application
        for handler in handlers:
            self.application.add_handler(handler)

    async def _send_startup_notification(self):
        """Send startup notification to admin or log channel"""
        try:
            admin_chat_id = self.config.get('ADMIN_CHAT_ID')
            if admin_chat_id:
                await self.notification_manager.queue_notification(
                    recipient=admin_chat_id,
                    message="🤖 Bot Started Successfully!\n"
                            f"Timestamp: {datetime.now()}"
                )
        except Exception as e:
            logging.error(f"Startup notification error: {e}")

    async def start_background_tasks(self):
        """Start background monitoring tasks"""
        tasks = [
            # Bandwidth monitoring
            asyncio.create_task(self.bandwidth_tracker.monitor_bandwidth()),
            
            # Notification queue processing
            asyncio.create_task(self.notification_manager.process_notification_queue())
        ]
        return tasks

    async def run(self):
        """Main bot run method"""
        try:
            # Initialize bot
            await self.initialize_bot()
            
            # Start background tasks
            background_tasks = await self.start_background_tasks()
            
            # Start polling
            await self.application.run_polling(drop_pending_updates=True, stop_signals=None)
            
            # Wait for background tasks
            await asyncio.gather(*background_tasks)
        
        except KeyboardInterrupt:
            logging.info("Bot stopped by user")
        except Exception as e:
            logging.error(f"Unexpected bot run error: {e}")
            await self.telegram_logger.log_error(e)
        finally:
            # Cleanup tasks
            await self.cleanup()

    async def cleanup(self):
        """Perform cleanup operations"""
        try:
            # Close database connections
            await self.database_manager.close()
            
            # Stop background tasks
            for task in asyncio.all_tasks():
                task.cancel()
            
            logging.info("Bot cleanup completed")
        except Exception as e:
            logging.error(f"Cleanup error: {e}")

def main():
    """Main entry point"""
    bot = MusicDownloadBot()
    
    try:
        # Run bot with asyncio
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        logging.info("Bot stopped by user")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")

if __name__ == '__main__':
    main()
