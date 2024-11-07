import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Dict, Optional, List

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
from utils.exceptions import AuthorizationError, DownloadError, RegionError
from utils.helpers import is_admin_user, format_file_size, is_valid_apple_music_url
from utils.decorators import admin_only, handle_errors

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class AppleMusicBot:
    def __init__(self):
        self.config = self.load_config()
        self.active_downloads: Dict[int, asyncio.Task] = {}
        self.download_progress: Dict[int, Dict] = {}
        self.cache_manager = self.init_cache_manager()
        
    def load_config(self) -> dict:
        """Load bot configuration"""
        with open("config/config.json", "r", encoding="utf-8") as f:
            return json.load(f)

    def init_cache_manager(self):
        """Initialize cache manager"""
        cache_dir = Path("cache")
        cache_dir.mkdir(exist_ok=True)
        return cache_dir

    def is_authorized(self, user_id: int) -> bool:
        """Check if user is authorized"""
        return user_id in self.config["admin_users"]

    def is_valid_region(self, region: str) -> bool:
        """Check if region is valid"""
        return region.lower() in self.config["regions"]

    @handle_errors
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for /start command"""
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
        """Handler for /help command"""
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
    async def regions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show available regions and their details"""
        regions_text = "🌎 Available regions:\n\n"
        for region, config in self.config["regions"].items():
            regions_text += (
                f"• {region.upper()}:\n"
                f"  Language: {config['language']}\n"
                f"  Storefront: {config['storefront']}\n\n"
            )
        await update.message.reply_text(regions_text)

    @handle_errors
    async def settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show and modify download settings"""
        keyboard = [
            [
                InlineKeyboardButton("Song Codec", callback_data="set_song_codec"),
                InlineKeyboardButton("Video Codec", callback_data="set_video_codec")
            ],
            [
                InlineKeyboardButton("Download Mode", callback_data="set_download_mode"),
                InlineKeyboardButton("Remux Mode", callback_data="set_remux_mode")
            ],
            [
                InlineKeyboardButton("Cover Format", callback_data="set_cover_format"),
                InlineKeyboardButton("Quality", callback_data="set_quality")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("⚙️ Select setting to modify:", reply_markup=reply_markup)

    @handle_errors
    async def handle_settings_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle settings callback queries"""
        query = update.callback_query
        await query.answer()

        if query.data == "set_song_codec":
            options = [codec.value for codec in SongCodec]
        elif query.data == "set_video_codec":
            options = [codec.value for codec in MusicVideoCodec]
        elif query.data == "set_download_mode":
            options = [mode.value for mode in DownloadMode]
        elif query.data == "set_remux_mode":
            options = [mode.value for mode in RemuxMode]
        elif query.data == "set_cover_format":
            options = [fmt.value for fmt in CoverFormat]
        elif query.data == "set_quality":
            options = [quality.value for quality in PostQuality]

        keyboard = [
            [InlineKeyboardButton(opt, callback_data=f"option_{opt}")]
            for opt in options
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"Select {query.data.replace('set_', '').replace('_', ' ')}:",
            reply_markup=reply_markup
        )

    @admin_only
    @handle_errors
    async def handle_url(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle Apple Music URL"""
        url = update.message.text
        user_id = update.effective_user.id

        if not is_valid_apple_music_url(url):
            await update.message.reply_
