from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

class TelegramBot:
    def __init__(self, token: str, message_handler):
        self.token = token
        self.message_handler = message_handler
        self.app = Application.builder().token(token).build()
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Hello! I'm your personal AI assistant. How can I help you today?")
        
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        message_text = update.message.text
        response = self.message_handler(message_text)
        await update.message.reply_text(response)
        
    async def error(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        print(f'Update {update} caused error {context.error}')
        
    def run(self):
        print('Starting bot...')
        self.app.add_handler(CommandHandler('start', self.start_command))
        self.app.add_handler(MessageHandler(filters.TEXT, self.handle_message))
        self.app.add_error_handler(self.error)
        self.app.run_polling(poll_interval=3)