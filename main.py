import os
import sys
import asyncio
import logging
from typing import Dict, Any

# Import necessary modules
from dotenv import load_dotenv
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
from utils.database import DatabaseManager
from notification_manager import NotificationManager
from bandwidth_tracker import BandwidthTracker
from metadata_enhancer import MetadataEnhancer
from gamdl.cli import main as gamdl_download

# Import other necessary components
from handlers.user_handler import UserHandler
from handlers.download_handler import DownloadHandler
from handlers.admin_handler import AdminHandler

class MusicDownloadBot:
    def __init__(self):
        # Load environment variables
        load_dotenv()

        # Configure logging
        self._setup_logging()

        # Initialize core components
        self.config_manager = ConfigManager()
        self.database_manager = DatabaseManager()
        
        # Telegram bot setup
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not self.bot_token:
            logging.critical("No Telegram Bot Token found!")
            sys.exit(1)

        # Initialize managers
        self.notification_manager = NotificationManager(
            bot=self.application.bot,
            config=self.config_manager.get_all()
        )
        self.bandwidth_tracker = BandwidthTracker()
        self.telegram_logger = TelegramLogger(
            bot=self.application.bot, 
            log_channel_id=self.config_manager.get('LOG_CHANNEL_ID')
        )

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
            self._register_handlers()
            logging.info("Bot initialized successfully")
        except Exception as e:
            logging.error(f"Bot initialization failed: {e}")
            await self.telegram_logger.log_error(e)

    def _register_handlers(self):
        """Register all bot command and message handlers"""
        user_handler = UserHandler(self.database_manager, self.notification_manager)
        download_handler = DownloadHandler(self.database_manager, self.bandwidth_tracker, self.notification_manager)
        admin_handler = AdminHandler(self.database_manager, self.notification_manager)

        # Command Handlers
        self.application.add_handler(CommandHandler('start', user_handler.start_command))
        self.application.add_handler(CommandHandler('help', user_handler.help_command))
        self.application.add_handler(CommandHandler('download', download_handler.download_command))
        
        # Admin Commands
        self.application.add_handler(CommandHandler('admin', admin_handler.admin_command))
        
        # Message Handlers
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_handler.handle_download_url))

    async def download_music(self, url: str, user_id: int):
        """Wrapper for music download functionality"""
        try:
            # Prepare download parameters
            sys.argv = ['gamdl', url, '--cookies-path', f'cookies/{user_id}_cookies.txt']
            # Execute download
            await gamdl_download()
            # Log successful download
            await self.telegram_logger.log_download(user_id=user_id, user_name="", track_info={"url": url})
        except Exception as e:
            logging.error(f"Download failed: {e}")
            await self.telegram_logger.log_error(e)

    async def start_background_tasks(self):
        """Start background tasks"""
        asyncio.create_task(self.bandwidth_tracker.monitor_bandwidth())

    async def run(self):
        """Main bot run method"""
        await self.initialize_bot()
        await self.start_background_tasks()
        # Start polling
        await self.application.run_polling(drop_pending_updates=True)

def main():
    """Main entry point"""
    bot = MusicDownloadBot()
    
    try:
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        logging.info("Bot stopped by user")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")

if __name__ == '__main__':
    main()
