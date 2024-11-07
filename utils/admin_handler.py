from telegram import Update
from telegram.ext import ContextTypes
from utils.auth import UserAuthorization
from utils.logger import TelegramLogger

class AdminHandler:
    def __init__(self, config: dict, logger: TelegramLogger, auth: UserAuthorization):
        self.config = config
        self.logger = logger
        self.auth = auth

    @property
    def admin_decorator(self):
        return self.auth.admin_only(self.config['admin_users'])

    @admin_decorator
    async def broadcast(self, update
