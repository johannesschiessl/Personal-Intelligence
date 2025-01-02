# Personal-Intelligence
A personal intelligence system based on AI agents.

## Getting Started

### Prerequisites
- Python 3.12 or higher
- Git
- A Telegram account and bot token
- OpenAI API key
- Google Calendar API credentials

### Setup Instructions

1. Clone the repository:
   ```bash
   git clone https://github.com/johannesschiessl/Personal-Intelligence.git
   cd Personal-Intelligence
   ```

2. Set up Python environment:
   ```bash
   # Create a virtual environment
   python -m venv .venv
   
   # Activate the virtual environment
   # On Windows:
   .venv\Scripts\activate
   # On macOS/Linux:
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -e .
   ```

4. Rename the `.env.example` file to `.env` and set the following variables:
   ```
   OPENAI_API_KEY=your_openai_api_key
   TELEGRAM_TOKEN=your_telegram_bot_token
   ```

5. Set up Google Calendar integration:
   - Go to the Google Cloud Console
   - Create a new project
   - Enable the Google Calendar API
   - Create OAuth 2.0 credentials
   - Download the credentials and save them as `data/calendar/credentials.json`

6. Start the application:
   ```bash
   python src/main.py
   ```

## Contributing

Feel free to contribute by creating issues. Suggestions for new features are always welcome!

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
