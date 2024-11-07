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
        
    def load_config(self) -> dict:
        """Load bot configuration"""
        with open("config/config.json", "r", encoding="utf-8") as f:
            return json.load(f)

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for /start command"""
        welcome_text = (
            "👋 Welcome to Apple Music Downloader Bot!\n\n"
            "Available commands:\n"
            "/download <URL> <region> - Download from Apple Music\n"
            "/regions - Show available regions\n"
            "/settings - Configure download settings\n"
            "/status - Check download status\n"
            "/cancel - Cancel active download\n\n"
            "Available regions: " + ", ".join(self.config["regions"].keys()).upper()
        )
        await update.message.reply_text(welcome_text)

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

    async def download(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle download command"""
        user_id = update.effective_user.id
        
        # Check authorization
        if not self.is_authorized(user_id):
            await update.message.reply_text("⛔️ You are not authorized to use this bot.")
            return

        # Validate command format
        if not context.args or len(context.args) < 2:
            await update.message.reply_text(
                "❌ Invalid format. Use: /download <URL> <region>\n"
                "Example: /download https://music.apple.com/... us"
            )
            return

        url = context.args[0]
        region = context.args[1].lower()

        # Validate region
        if not self.is_valid_region(region):
            await update.message.reply_text(
                f"❌ Invalid region: {region}\n"
                f"Available regions: {', '.join(self.config['regions'].keys()).upper()}"
            )
            return

        # Check active downloads
        if user_id in self.active_downloads:
            await update.message.reply_text(
                "⚠️ You already have an active download. "
                "Use /cancel to cancel it first."
            )
            return

        # Initialize download
        status_message = await update.message.reply_text("🔄 Initializing download...")
        download_task = asyncio.create_task(
            self._process_download(update, context, url, region, status_message)
        )
        self.active_downloads[user_id] = download_task

    async def _process_download(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                              url: str, region: str, status_message):
        """Process the download"""
        user_id = update.effective_user.id
        try:
            # Initialize APIs
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

            # Initialize downloaders
            downloader = Downloader(
                apple_music_api=apple_music_api,
                itunes_api=itunes_api,
                output_path=Path(self.config["download_settings"]["output_path"]),
                temp_path=Path(self.config["download_settings"]["temp_path"]),
                download_mode=DownloadMode(self.config["download_settings"]["download_mode"]),
                remux_mode=RemuxMode(self.config["download_settings"]["remux_mode"]),
                cover_
