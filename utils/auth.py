from functools import wraps
from telegram import Bot, Update
from telegram.ext import ContextTypes
from typing import Optional, Callable

class UserAuthorization:
    def __init__(self, bot: Bot, config: dict):
        self.bot = bot
        self.config = config
        self.auth_channel_id = config.get('auth_channel_id')
        self.admin_users = config.get('admin_users', [])

    async def check_user_auth(self, user_id: int) -> bool:
        """Check if user is authorized via channel membership"""
        if not self.auth_channel_id:
            return True
            
        try:
            member = await self.bot.get_chat_member(
                chat_id=self.auth_channel_id,
                user_id=user_id
            )
            return member.status in ['member', 'administrator', 'creator']
        except Exception:
            return False

    def admin_only(self) -> Callable:
        """Decorator for admin-only commands"""
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
                user_id = update.effective_user.id
                if user_id not in
