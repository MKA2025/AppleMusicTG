from telegram import Bot, Update
from telegram.ext import ContextTypes
from typing import Optional

class UserAuthorization:
    def __init__(self, bot: Bot, auth_channel_id: Optional[int] = None):
        self.bot = bot
        self.auth_channel_id = auth_channel_id

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

    def admin_only(self, admin_users: list):
        """Decorator for admin-only commands"""
        async def decorator(func):
            async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
                user_id = update.effective_user.id
                if user_id not in admin_users:
                    await update.message.reply_text(
                        "⚠️ This command is for administrators only."
                    )
                    return
                return await func(update, context)
            return wrapper
        return decorator
