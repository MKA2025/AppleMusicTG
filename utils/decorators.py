import functools
from typing import Callable
from telegram import Update
from telegram.ext import ContextTypes

from .helpers import is_admin_user
from .exceptions import AuthorizationError

def admin_only(func: Callable):
    """Decorator to restrict command to admin users only"""
    @functools.wraps(func)
    async def wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        if not is_admin_user(user_id):
            raise AuthorizationError("This command is restricted to admin users")
        return await func(self, update, context, *args, **kwargs)
    return wrapper

def handle_errors(func: Callable):
    """Decorator to handle errors and send appropriate messages"""
    @functools.wraps(func)
    async def wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        try:
            return await func(self, update, context, *args, **kwargs)
        except AuthorizationError as e:
            await update.message.reply_text(f"⛔️ Authorization Error: {str(e)}")
        except RegionError as e:
            await update.message.reply_text(f"🌍 Region Error: {str(e)}")
        except DownloadError as e:
            await update.message.reply_text(f"⚠️ Download Error: {str(e)}")
        except Exception as e:
            await update.message.reply_text(
                "❌ An unexpected error occurred. Please try again later."
            )
            self.logger.error(f"Unexpected error: {str(e)}", exc_info=True)
    return wrapper
