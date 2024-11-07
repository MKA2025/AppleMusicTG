import logging
import asyncio
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Set

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from telegram.constants import ParseMode

from gamdl.apple_music_api import AppleMusicApi
from gamdl.downloader import Downloader
from gamdl.downloader_song import DownloaderSong
from gamdl.downloader_music_video import DownloaderMusicVideo

# Configuration
TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN"
ADMIN_USER_IDS = {123456789}  # Add admin Telegram user IDs here
DOWNLOAD_PATH = Path("./downloads")
TEMP_PATH = Path("./temp")
COOKIES_PATH = Path("./cookies.txt")

# Initialize logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Global state
active_downloads: Dict[int, Set[str]] = {}  # User ID -> Set of download IDs
download_history: Dict[int, list] = {}  # User ID -> List of downloads

class GamdlBot:
    def __init__(self):
        # Initialize APIs and downloaders
        self.apple_music_api = AppleMusicApi(cookies_path=COOKIES_PATH)
        self.downloader = Downloader(
            self.apple_music_api,
            output_path=DOWNLOAD_PATH,
            temp_path=TEMP_PATH
        )
        self.downloader_song = DownloaderSong(self.downloader)
        self.downloader_music_video = DownloaderMusicVideo(self.downloader)
        
        # Set up download directories
        DOWNLOAD_PATH.mkdir(parents=True, exist_ok=True)
        TEMP_PATH.mkdir(parents=True, exist_ok=True)

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        welcome_text = (
            "👋 *Welcome to Apple Music Downloader Bot!*\n\n"
            "I can help you download songs and music videos from Apple Music.\n\n"
            "*Commands:*\n"
            "/download `<Apple Music URL>` - Download song/video\n"
            "/history - View your download history\n"
            "/help - Show this help message\n\n"
            "*Supported URLs:*\n"
            "• Song URLs\n"
            "• Album URLs\n"
            "• Playlist URLs\n"
            "• Music Video URLs"
        )
        await update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN)

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        await self.start(update, context)

    async def download(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /download command"""
        user_id = update.effective_user.id
        
        # Check if user has active downloads
        if user_id in active_downloads and len(active_downloads[user_id]) >= 3:
            await update.message.reply_text(
                "❌ You have too many active downloads. Please wait for them to complete."
            )
            return

        # Get URL from command
        if not context.args:
            await update.message.reply_text(
                "❌ Please provide an Apple Music URL.\n"
                "Example: `/download https://music.apple.com/...`",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        url = context.args[0]
        
        try:
            # Send processing message
            status_message = await update.message.reply_text(
                "🔄 Processing your request..."
            )

            # Get download information
            url_info = self.downloader.get_url_info(url)
            download_queue = self.downloader.get_download_queue(url_info)

            # Initialize user's active downloads if needed
            if user_id not in active_downloads:
                active_downloads[user_id] = set()

            # Process each track
            for track in download_queue.tracks_metadata:
                try:
                    # Update status message
                    await status_message.edit_text(
                        f"⏳ Downloading: {track['attributes']['name']}"
                    )

                    if track["type"] == "songs":
                        await self.process_song(track, user_id, status_message)
                    elif track["type"] == "music-videos":
                        await self.process_music_video(track, user_id, status_message)

                    # Add to history
                    if user_id not in download_history:
                        download_history[user_id] = []
                    download_history[user_id].append({
                        'title': track['attributes']['name'],
                        'type': track['type'],
                        'date': datetime.now().isoformat()
                    })

                except Exception as e:
                    logger.error(f"Error processing track: {str(e)}", exc_info=True)
                    await status_message.edit_text(
                        f"❌ Error downloading {track['attributes']['name']}: {str(e)}"
                    )

            await status_message.edit_text("✅ Download complete!")

        except Exception as e:
            logger.error(f"Error processing URL: {str(e)}", exc_info=True)
            await status_message.edit_text(f"❌ Error: {str(e)}")

    async def process_song(self, track, user_id, status_message):
        """Process and download a song"""
        # Get song information
        webplayback = self.apple_music_api.get_webplayback(track["id"])
        tags = self.downloader_song.get_tags(webplayback, None)
        
        # Get stream info and download
        stream_info = self.downloader_song.get_stream_info(track)
        
        if not stream_info.stream_url:
            raise Exception("Song not available for download")

        # Get decryption key
        decryption_key = self.downloader.get_decryption_key(
            stream_info.pssh, 
            track["id"]
        )

        # Download and process
        encrypted_path = self.downloader_song.get_encrypted_path(track["id"])
        decrypted_path = self.downloader_song.get_decrypted_path(track["id"])
        remuxed_path = self.downloader_song.get_remuxed_path(track["id"])

        # Download
        await status_message.edit_text(f"⏳ Downloading: {tags['title']}")
        self.downloader.download(encrypted_path, stream_info.stream_url)

        # Decrypt
        await status_message.edit_text(f"🔄 Processing: {tags['title']}")
        self.downloader_song.decrypt(encrypted_path, decrypted_path, decryption_key)

        # Remux
        self.downloader_song.remux(decrypted_path, remuxed_path, stream_info.codec)

        # Move to final location
        final_path = self.downloader.get_final_path(tags, ".m4a")
        self.downloader.move_to_output_path(rem
