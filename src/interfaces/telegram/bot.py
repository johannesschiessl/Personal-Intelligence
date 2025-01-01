from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from typing import Optional

class TelegramBot:
    def __init__(self, token: str, message_handler):
        self.token = token
        self.message_handler = message_handler
        self.app = Application.builder().token(token).build()
        self.current_update: Optional[Update] = None
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Hello! I'm your personal AI assistant. How can I help you today?")
    
    async def send_tool_notification(self, tool_name: str):
        if self.current_update:
            tool_emojis = {
                "memory": "🧠",
            }
            emoji = tool_emojis.get(tool_name, "🛠️")
            await self.current_update.message.reply_text(f"{emoji} Using {tool_name.capitalize()}")
        
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.current_update = update
        
        if update.message.photo:
            photo = update.message.photo[-1]
            file = await context.bot.get_file(photo.file_id)
            file_url = file.file_path
            
            message = {
                "image_url": file_url,
                "text": update.message.caption if update.message.caption else None
            }
            
            response = self.message_handler(message, self.send_tool_notification)
        else:
            message_text = update.message.text
            response = self.message_handler(message_text, self.send_tool_notification)
            
        await update.message.reply_text(response)
        self.current_update = None
        
    async def error(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        print(f'Update {update} caused error {context.error}')
        
    def run(self):
        print('Starting bot...')
        self.app.add_handler(CommandHandler('start', self.start_command))
        self.app.add_handler(MessageHandler(filters.PHOTO | filters.TEXT, self.handle_message))
        self.app.add_error_handler(self.error)
        self.app.run_polling(poll_interval=3)
