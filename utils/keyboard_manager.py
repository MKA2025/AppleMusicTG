from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Dict

class KeyboardManager:
    @staticmethod
    def get_settings_keyboard() -> InlineKeyboardMarkup:
        """Get settings menu keyboard"""
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
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def get_options_keyboard(options: List[str], callback_prefix: str) -> InlineKeyboardMarkup:
        """Get keyboard for options selection"""
        keyboard = [
            [InlineKeyboardButton(opt, callback_data=f"{callback_prefix}_{opt}")]
            for opt in options
        ]
        keyboard.append([InlineKeyboardButton("Back", callback_data="settings_back")])
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def get_confirmation_keyboard() -> InlineKeyboardMarkup:
        """Get confirmation keyboard"""
        keyboard = [
            [
                InlineKeyboardButton("Yes", callback_data="confirm_yes"),
                InlineKeyboardButton("No", callback_data="confirm_no")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
