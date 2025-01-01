import os
from dotenv import load_dotenv
from assistant.main import Assistant
from interfaces.telegram.bot import TelegramBot

def main():
    print("Starting Personal Intelligence")
    load_dotenv()
    
    assistant = Assistant()
    
    telegram_token = os.getenv('TELEGRAM_TOKEN')
    if not telegram_token:
        raise ValueError("TELEGRAM_TOKEN not found in environment variables")
    
    bot = TelegramBot(telegram_token, assistant.chat)
    bot.run()

if __name__ == "__main__":
    main()
