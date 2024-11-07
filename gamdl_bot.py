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
from utils.decorators import admin_only, handle_errors
from utils.cache_manager import CacheManager
from utils.rate_limiter import RateLimiter

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    filename='bot.log'
)
logger = logging.getLogger(__name__)

class AppleMusicBot:
    def __init__(self):
        self.config = self.load_config()
        self.active_downloads: Dict[int, asyncio.Task] = {}
        self.download_progress: Dict[int, Dict] = {}
        self.cache_manager = CacheManager(Path("cache"))
        self.rate_limiter = RateLimiter(max_calls=5, time_frame=1.0)  # 5 calls per second
        self.user_preferences: Dict[int, Dict] = {}
        
    def load_config(self) -> dict:
        with open("config/config.json", "r", encoding="utf-8") as f:
            return json.load(f)

    def is_authorized(self, user_id: int) -> bool:
        return user_id in self.config["admin_users"]

    def is_valid_region(self, region: str) -> bool:
        return region.lower() in self.config["regions"]

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
            "/help - Show detailed help\n\n"
            "Available regions: " + ", ".join(self.config["regions"].keys()).upper()
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
        )
        await update.message.reply_text(help_text)

    @handle_errors
    async def handle_url(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle Apple Music URL messages"""
        url = update.message.text
        user_id = update.effective_user.id

        if not self.is_authorized(user_id):
            raise AuthorizationError("You are not authorized to use this bot.")

        if not is_valid_apple_music_url(url):
            await update.message.reply_text("❌ Invalid Apple Music URL. Please send a valid URL.")
            return

        # Check active downloads
        if user_id in self.active_downloads:
            await update.message.reply_text(
                "⚠️ You already have an active download. Use /cancel to cancel it first."
            )
            return

        # Get user preferences or default region
        user_prefs = self.user_preferences.get(user_id, {})
        region = user_prefs.get('region', 'us')  # Default to US if not set

        # Initialize download
        status_message = await update.message.reply_text("🔄 Initializing download...")
        download_task = asyncio.create_task(
            self._process_download(update, context, url, region, status_message)
        )
        self.active_downloads[user_id] = download_task

    async def _process_download(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                              url: str, region: str, status_message):
        """Process the download with progress tracking"""
        user_id = update.effective_user.id
        try:
            # Check cache first
            cache_key = f"{url}_{region}"
            cached_data = self.cache_manager.get(cache_key)
            
            if cached_data:
                logger.info(f"Using cached data for {url}")
                track_info = cached_data
            else:
                # Initialize APIs with rate limiting
                await self.rate_limiter.wait(f"api_{user_id}")
                
                region_config = self.config["regions"][region]
                apple_music_api = AppleMusicApi(
                    cookies_path=Path(region_config["cookies_file"]),
                    language=region_config["language"],
                    storefront=region_config["storefront"]
                )
                
                itunes_api = ItunesApi(
                    storefront=region_config["storefront"],
                    language=region_config["language"]
                )

                # Get track info
                track_info = await self._get_track_info(apple_music_api, url)
                self.cache_manager.set(cache_key, track_info)

            # Update status message with track info
            await status_message.edit_text(
                f"📥 Downloading: {track_info['title']}\n"
                f"👤 Artist: {track_info['artist']}\n"
                f"💿 Album: {track_info.get('album', 'N/A')}\n"
                f"⏳ Progress: Initializing..."
            )

            # Initialize download manager
            downloader = self._create_downloader(apple_music_api, itunes_api)
            
            # Set up progress callback
            progress = {"current": 0, "total": 0, "status": "downloading"}
            
            def progress_callback(current, total):
                progress["current"] = current
                progress["total"] = total
                self.download_progress[user_id] = progress

            # Start download with progress tracking
            file_path = await self._download_track(
                downloader, track_info, progress_callback
            )

            # Upload file to Telegram
            await self._send_file(update, context, file_path, track_info)

            # Cleanup
            os.remove(file_path)
            await status_message.edit_text("✅ Download completed!")

        except Exception as e:
            logger.error(f"Download error: {str(e)}", exc_info=True)
            await status_message.edit_text(f"❌ Download failed: {str(e)}")
            raise DownloadError(str(e))

        finally:
            if user_id in self.active_downloads:
                del self.active_downloads[user_id]
            if user_id in self.download_progress:
                del self.download_progress[user_id]

    async def _get_track_info(self, api: AppleMusicApi, url: str) -> dict:
        """Get track information from Apple Music API"""
        try:
            track_data = await api.get_track_data(url)
            return {
                'title': track_data['attributes']['name'],
                'artist': track_data['attributes']['artistName'],
                'album': track_data['attributes'].get('albumName'),
                'artwork_url': track_data['attributes'].get('artwork', {}).get('url'),
                'duration': track_data['attributes'].get('durationInMillis'),
                'track_number': track_data['attributes'].get('trackNumber'),
                'genre': track_data['attributes'].get('genreNames', [])[0],
                'release_date': track_data['attributes'].get('releaseDate'),
            }
        except Exception as e:
            raise AppleMusicAPIError(f"Failed to get track info: {str(e)}")

    def _create_downloader(self, apple_music_api: AppleMusicApi, itunes_api: ItunesApi) -> Downloader:
        """Create and configure downloader instance"""
        return Downloader(
            apple_music_api=apple_music_api,
            itunes_api=itunes_api,
            output_path=Path(self.config["download_settings"]["output_path"]),
            temp_path=Path(self.config["download_settings"]["temp_path"]),
            download_mode=DownloadMode(self.config["download_settings"]["download_mode"]),
            remux_mode=RemuxMode(self.config["download_settings"]["remux_mode"]),
            cover_format=CoverFormat(self.config["download_settings"]["cover_format"]),
            song_codec=SongCodec(self.config["download_settings"]["song_codec"]),
            video_codec=MusicVideoCodec(self.config["download_settings"]["video_codec"]),
            post_quality=PostQuality(self.config["download_settings"]["post_quality"])
        )

    async def _send_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                        file_path: Path, track_info: dict):
        """Send downloaded file to user with metadata"""
        caption = (
            f"🎵 {track_info['title']}\n"
            f"👤 {track_info['artist']}\n"
            f"💿 {track_info.get('album', 'N/A')}\n"
            f"🎼 {track_info.get('genre', 'N/A')}\n"
            f"📅 {track_info.get('release_date', 'N/A')}"
        )

        with open(file_path, 'rb') as f:
            await context.bot.send_audio(
                chat_id=update.effective_chat.id,
                audio=f,
                caption=caption,
                title=track_info['title'],
                performer=track_info['artist'],
                thumb=track_info.get('artwork_url'),
                duration=track_info.get('duration', 0) // 1000
            )

    @handle_errors
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT
