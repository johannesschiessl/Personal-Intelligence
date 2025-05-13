# Personal-Intelligence
A personal intelligence system based on AI agents.

## Features
- Tasks
- Google Calendar Integration
- Open Urls
- Analysis (execute python code)
- Memory
- Notion Integration

## Getting Started

### Prerequisites
- Python 3.12 or higher and uv
- Git
- A Telegram account and bot token
- OpenAI API key
- Google Calendar API credentials
- Notion Integration
- Docker installed and running

### Setup Instructions

1. Clone the repository:
   ```bash
   git clone https://github.com/johannesschiessl/Personal-Intelligence.git
   cd Personal-Intelligence
   ```

2. Set up Python environment and install dependencies:
   ```bash
   uv sync
   ```

3. Rename the `.env.example` file to `.env` and set the following variables:
   ```
   OPENAI_API_KEY=your_openai_api_key # Get this from https://platform.openai.com/api-keys
   TELEGRAM_TOKEN=your_telegram_bot_token # Get this from https://t.me/BotFather
   NOTION_API_TOKEN=your_notion_api_token # Get this from https://www.notion.so/profile/integrations
   ```

4. Set up Google Calendar integration:
   - Go to the Google Cloud Console
   - Create a new project
   - Enable the Google Calendar API
   - Create OAuth 2.0 credentials
   - Download the credentials and save them as `data/calendar/credentials.json`

5. Set up config.py:
   - Copy `config-example.py` to `config.py`
   - Fill in the required fields

6. Start the application:
   Make sure docker is running and then run:
   ```bash
   uv run src/main.py
   ```

## Contributing

Feel free to contribute by creating issues. Suggestions for new features are always welcome!

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
