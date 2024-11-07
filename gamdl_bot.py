import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from gamdl import (
    AppleMusicApi,
    Downloader,
    DownloaderSong,
    DownloaderMusicVideo,
    DownloaderPost,
    ItunesApi,
)
from gamdl.enums import (
    DownloadMode,
    RemuxMode,
    SongCodec,
    MusicVideoCodec,
    PostQuality,
    CoverFormat,
)
from utils.exceptions import AuthorizationError, DownloadError, RegionError, AppleMusicAPIError
from utils.helpers import is_admin_user, format_file_size, is_valid_apple_music_url
from utils.decorators import admin_only, handle_errors, rate_limit
from utils.cache_manager import CacheManager
from utils.rate_limiter import RateLimiter
from utils.stats import UserStats
from utils.config_manager import ConfigManager
from utils.download_manager import DownloadManager
from utils.keyboard_manager import KeyboardManager

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    filename='bot.log'
)
logger = logging.getLogger(__name__)

class AppleMusicBot:
    def __init__(self):
        self.config = ConfigManager(Path("config/config.json"))
        self.active_downloads: Dict[int, asyncio.Task] = {}
        self.download_progress: Dict[int, Dict] = {}
        self.cache_manager = CacheManager(Path("cache"))
        self.rate_limiter = RateLimiter(max_calls=5, time_frame=1.0)  # 5 calls per second
        self.user_preferences: Dict[int, Dict] = {}
        self.stats_manager = UserStats()
        self.download_manager = DownloadManager(max_concurrent=self.config.get("max_concurrent_downloads", 2))
        self.keyboard_manager = KeyboardManager()
        
    def is_authorized(self, user_id: int) -> bool:
        return user_id in self.config.get("admin_users", [])

    def is_valid_region(self, region: str) -> bool:
        return region.lower() in self.config.get("regions", {})

    @handle_errors
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        welcome_text = (
            "👋 Welcome to Apple Music Downloader Bot!\n\n"
            "To download, simply send an Apple Music URL.\n\n"
            "Available commands:\n"
            "/regions - Show available regions\n"
            "/settings - Configure download settings\n"
            "/status - Check download status\n"
            "/cancel - Cancel active download\n"
            "/stats - View your download statistics\n"
            "/help - Show detailed help\n\n"
            f"Available regions: {', '.join(self.config.get('regions', {}).keys()).upper()}"
        )
        await update.message.reply_text(welcome_text)

    @handle_errors
    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_text = (
            "📖 Detailed Help\n\n"
            "1. How to Download:\n"
            "   Simply send an Apple Music URL to the bot.\n"
            "   Example: https://music.apple.com/us/album/...\n\n"
            "2. Supported Content:\n"
            "   • Songs\n"
            "   • Albums\n"
            "   • Playlists\n"
            "   • Music Videos\n\n"
            "3. Download Settings:\n"
            "   • Song Codec: AAC, AAC_HE, ALAC\n"
            "   • Video Codec: H264, H265\n"
            "   • Quality: Various options available\n\n"
            "4. Additional Features:\n"
            "   • Progress tracking\n"
            "   • Download cancellation\n"
            "   • Region selection\n"
            "   • User statistics\n"
        )
        await update.message.reply_text(help_text)

    @handle_errors
    @rate_limit(5)  # 5 seconds cooldown between downloads
    async def handle_url(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle Apple Music URL messages"""
        url = update.message.text
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name

        if not self.is_authorized(user_id):
            raise AuthorizationError("You are not authorized to use this bot.")

        if not is_valid_apple_music_url(url):
            await update.message.reply_text("❌ Invalid Apple Music URL. Please send a valid URL.")
            return

        # Check queue status
        queue_position = self.download_manager.get_queue_position(user_id)
        if queue_position:
            await update.message.reply_text(
                f"⏳ You are already in queue (Position: {queue_position}). "
                "Use /cancel to remove your download from queue."
            )
            return

        # Initialize download
        status_message = await update.message.reply_text("🔄 Initializing download...")
        
        try:
            # Get track info
            track_info = await self._get_track_info(url)
            
            # Add to queue
            queue_item = {
                'user_id': user_id,
                'user_name': user_name,
                'url': url,
                'track_info': track_info,
                'status_message': status_message
            }
            
            position = await self.download_manager.add_download(user_id, queue_item)
            
            if position > 1:
                await status_message.edit_text(
                    f"🎵 {track_info['title']}\n"
                    f"👤 {track_info['artist']}\n"
                    f"📝 Added to queue (Position: {position})"
                )
            else:
                await self._process_download(update, context, url, status_message)
                
        except Exception as e:
            logger.error(f"Download error: {str(e)}", exc_info=True)
            await status_message.edit_text(f"❌ Download failed: {str(e)}")
            raise DownloadError(str(e))

    async def _process_download(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                              url: str, status_message):
        """Process the download with progress tracking"""
        user_id = update.effective_user.id
        try:
            # Check cache first
            cache_key = f"{url}_{self.user_preferences.get(user_id, {}).get('region', 'us')}"
            cached_data = self.cache_manager.get(cache_key)
            
