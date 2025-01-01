import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from typing import Optional, Set
from assistant.main import Assistant
from interfaces.telegram.chatid import USER_CHAT_ID

class TelegramBot:
    def __init__(self, assistant: Assistant):
        self.assistant = assistant
        self.token = os.getenv('TELEGRAM_TOKEN')
        if not self.token:
            raise ValueError("TELEGRAM_TOKEN not found in environment variables")
        
        self.app = Application.builder().token(self.token).build()
        self.current_update: Optional[Update] = None
        self.chat_ids: Set[int] = {USER_CHAT_ID} if USER_CHAT_ID else set()
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.message.chat_id not in self.chat_ids:
            self.chat_ids.add(update.message.chat_id)
        await update.message.reply_text("Hello! I'm your personal AI assistant. How can I help you today? Type /chatid to get your chat ID.")
    
    async def chatid_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Command to get one's chat ID"""
        chat_id = update.message.chat_id
        await update.message.reply_text(
            f"Your chat ID is: {chat_id}\n\n"
            f"To make the assistant always respond to this chat:\n"
            f"1. Copy this number: {chat_id}\n"
            f"2. Set USER_CHAT_ID in src/config.py to this number\n"
            f"3. Restart the assistant"
        )
    
    async def send_tool_notification(self, tool_name: str):
        """Send a tool usage notification to users"""
        tool_emojis = {
            "memory": "🧠",
            "tasks": "📝",
        }
        emoji = tool_emojis.get(tool_name, "🛠️")
        message = f"{emoji} Using {tool_name.capitalize()}"
        
        if self.current_update:
            await self.current_update.message.reply_text(message)
        else:
            await self.broadcast_message(message)
    
    async def broadcast_message(self, message: str):
        """Send a message to all known users"""
        if USER_CHAT_ID and USER_CHAT_ID not in self.chat_ids:
            self.chat_ids.add(USER_CHAT_ID)
            
        if not self.chat_ids:
            print("Warning: No chat IDs available to send message to")
            return
            
        for chat_id in self.chat_ids:
            if chat_id is None:
                continue
            try:
                await self.app.bot.send_message(chat_id=chat_id, text=message)
            except Exception as e:
                print(f"Error sending message to chat {chat_id}: {e}")
        
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.message.chat_id not in self.chat_ids:
            self.chat_ids.add(update.message.chat_id)
            
        self.current_update = update
        
        try:
            if update.message.photo:
                photo = update.message.photo[-1]
                file = await context.bot.get_file(photo.file_id)
                file_url = file.file_path
                
                message = {
                    "image_url": file_url,
                    "text": update.message.caption if update.message.caption else None
                }
                
                response = self.assistant.chat(message, self.send_tool_notification)
            else:
                message_text = update.message.text
                response = self.assistant.chat(message_text, self.send_tool_notification)
                
            await update.message.reply_text(response)
        except Exception as e:
            error_message = f"Sorry, an error occurred: {str(e)}"
            await update.message.reply_text(error_message)
            print(f"Error handling message: {e}")
        finally:
            self.current_update = None
        
    async def error(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        print(f'Update {update} caused error {context.error}')
        if update:
            await update.message.reply_text("Sorry, an error occurred while processing your message.")
    
    async def setup(self):
        """Set up the bot handlers"""
        print('Setting up bot handlers...')
        self.app.add_handler(CommandHandler('start', self.start_command))
        self.app.add_handler(CommandHandler('chatid', self.chatid_command))
        self.app.add_handler(MessageHandler(filters.PHOTO | filters.TEXT, self.handle_message))
        self.app.add_error_handler(self.error)
        
    async def start(self):
        """Start the bot"""
        print('Starting bot...')
        await self.setup()
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling(poll_interval=3.0)
        
    async def stop(self):
        """Stop the bot gracefully"""
        print('Stopping bot...')
        try:
            if self.app.updater:
                print('Stopping updater...')
                await self.app.updater.stop()
            print('Stopping application...')
            await self.app.stop()
            await self.app.shutdown()
        except Exception as e:
            print(f"Error during bot shutdown: {e}")
