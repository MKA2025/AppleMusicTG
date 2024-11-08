# broadcast_manager.py
import asyncio
import logging
from typing import List, Union, Dict, Optional
from telegram import Bot, Update
from telegram.ext import CommandHandler, ContextTypes, Application
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json

Base = declarative_base()

class BroadcastLog(Base):
    """Broadcast log database model"""
    __tablename__ = 'broadcast_logs'
    
    id = Column(Integer, primary_key=True)
    message = Column(Text)
    sender_id = Column(Integer)
    total_recipients = Column(Integer)
    success_count = Column(Integer)
    failure_count = Column(Integer)
    error_details = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)

class UserDatabase:
    """User management and database operations"""
    def __init__(self, db_path: str = 'users.db'):
        self.engine = create_engine(f'sqlite:///{db_path}')
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def get_all_users(self) -> List[int]:
        """Retrieve all registered user IDs"""
        session = self.Session()
        try:
            # TODO: Implement actual user retrieval from your database
            # Example placeholder
            users = [246]  # Your specific user ID
            return users
        finally:
            session.close()

class BroadcastManager:
    def __init__(
        self, 
        config: Dict, 
        user_db: Optional[UserDatabase] = None
    ):
        """
        Initialize BroadcastManager
        
        :param config: Configuration dictionary
        :param user_db: Optional UserDatabase instance
        """
        self.config = config
        self.admin_users = config.get('admin_users', [246])  # Default admin
        self.logger = logging.getLogger(__name__)
        self.user_db = user_db or UserDatabase()

    async def send_force_message(
        self, 
        bot: Bot,
        recipients: Union[List[int], str], 
        message: str,
        sender_id: int = None,
        parse_mode: str = 'HTML',
        extra_options: Dict = None
    ) -> Dict[str, Union[int, List]]:
        """
        Advanced force message sending with comprehensive tracking
        
        :param bot: Telegram Bot instance
        :param recipients: List of user IDs or 'all'
        :param message: Message to send
        :param sender_id: ID of the admin sending the message
        :param parse_mode: Telegram parse mode
        :param extra_options: Additional message sending options
        :return: Broadcast statistics
        """
        try:
            # Determine recipients
            if recipients == 'all':
                recipients = await self._get_all_users()
            elif isinstance(recipients, int):
                recipients = [recipients]

            # Validate message
            if not message or len(message) > 4096:
                raise ValueError("Invalid message length")

            # Prepare broadcast tracking
            success_count = 0
            failure_count = 0
            error_details = []

            # Default extra options
            options = extra_options or {}

            # Broadcast messages
            for user_id in recipients:
                try:
                    # Prepare message with potential customizations
                    await bot.send_message(
                        chat_id=user_id, 
                        text=message,
                        parse_mode=parse_mode,
                        disable_web_page_preview=options.get('disable_preview', True),
                        **{k: v for k, v in options.items() if k != 'disable_preview'}
                    )
                    success_count += 1
                except Exception as send_error:
                    failure_count += 1
                    error_details.append({
                        'user_id': user_id,
                        'error': str(send_error)
                    })
                    self.logger.error(f"Failed to send message to {user_id}: {send_error}")
                
                # Prevent Telegram rate limiting
                await asyncio.sleep(0.1)

            # Log broadcast details
            await self._log_broadcast(
                message=message,
                sender_id=sender_id or 246,
                total_recipients=len(recipients),
                success_count=success_count,
                failure_count=failure_count,
                error_details=error_details
            )

            return {
                'total_recipients': len(recipients),
                'success_count': success_count,
                'failure_count': failure_count,
                'error_details': error_details
            }

        except Exception as e:
            self.logger.error(f"Broadcast error: {e}")
            return None

    async def _get_all_users(self) -> List[int]:
        """
        Retrieve all registered users 
        
        :return: List of user IDs
        """
        # Combine users from multiple sources
        config_users = self.config.get('registered_users', [])
        db_users = self.user_db.get_all_users()
        
        # Remove duplicates and ensure 246 is included
        users = list(set(config_users + db_users + [246]))
        return users

    async def _log_broadcast(
        self, 
        message: str, 
        sender_id: int,
        total_recipients: int,
        success_count: int, 
        failure_count: int,
        error_details: List[Dict] = None
    ):
        """
        Log broadcast details to database
        """
        session = self.user_db.Session()
        try:
            log_entry = BroadcastLog(
                message=message[:500],  # Truncate for storage
                sender_id=sender_id,
                total_recipients=total_recipients,
                success_count=success_count,
                failure_count=failure_count,
                error_details=json.dumps(error_details) if error_details else None
            )
            session.add(log_entry)
            session.commit()
        except Exception as e:
            self.logger.error(f"Broadcast logging error: {e}")
            session.rollback()
        finally:
            session.close()

    @classmethod
    async def broadcast_handler(
        cls, 
        update: Update, 
        context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Telegram command handler for broadcasting
        """
        # Validate admin access
        user_id = update.effective_user.id
        config = context.bot_data.get('config', {})
        admin_users = config.get('admin_users', [246])

        if user_id not in admin_users:
            await update.message.reply_text("❌ Admin access only")
            return

        # Validate message input
        if not context.args:
            await update.message.reply_text(
                "Broadcast Usage:\n"
                "/broadcast <message>\n"
                "/broadcast all <message>"
            )
            return

        # Determine broadcast type
        if context.args[0] == 'all':
            message = ' '.join(context.args[1:])
            recipients = 'all'
        else:
            message = ' '.join(context.args)
            recipients = (
                update.message.reply_to_message.from_user.id 
                if update.message.reply_to_message 
                else None
            )

        if not message:
            await update.message.reply_text("Please provide a message to broadcast")
            return

        # Initialize broadcast manager
        broadcast_manager = cls(config)

                # Send broadcast
        result = await broadcast_manager.send_force_message(
            bot=context.bot,
            recipients=recipients, 
            message=message,
            sender_id=user_id
        )

        # Send result notification
        if result:
            response = (
                f"📢 Broadcast Result:\n"
                f"Total Recipients: {result['total_recipients']}\n"
                f"✅ Success: {result['success_count']}\n"
                f"❌ Failed: {result['failure_count']}"
            )
            
            # Add error details if failures occurred
            if result['failure_count'] > 0:
                response += "\n\nError Details:"
                for error in result.get('error_details', [])[:5]:  # Limit to 5 error details
                    response += f"\n- User {error['user_id']}: {error['error']}"
            
            await update.message.reply_text(response)
        else:
            await update.message.reply_text("❌ Broadcast failed unexpectedly")

def setup_broadcast_handler(application: Application):
    """
    Setup broadcast handler in Telegram bot
    
    :param application: Telegram Bot Application
    """
    application.add_handler(
        CommandHandler('broadcast', BroadcastManager.broadcast_handler)
    )

# Optional: Additional utility methods
class BroadcastUtilities:
    """
    Additional broadcast-related utility methods
    """
    @staticmethod
    async def schedule_broadcast(
        bot: Bot, 
        message: str, 
        recipients: Union[List[int], str],
        schedule_time: datetime
    ):
        """
        Schedule a broadcast for a future time
        
        :param bot: Telegram Bot instance
        :param message: Message to broadcast
        :param recipients: List of recipients or 'all'
        :param schedule_time: Datetime to send the message
        """
        # Implement scheduling logic
        # Could use APScheduler or custom async scheduling
        pass

    @staticmethod
    async def create_broadcast_template(
        template_type: str
    ) -> str:
        """
        Generate predefined broadcast templates
        
        :param template_type: Type of template (welcome, update, etc.)
        :return: Formatted message template
        """
        templates = {
            'welcome': "👋 Welcome to our community! Stay tuned for updates.",
            'update': "🔔 Important update: Check our latest announcements.",
            # Add more templates
        }
        return templates.get(template_type, "")