# User
USER_NAME = "Johannes"
USER_ROLE = "Developer"
USER_BIO = """
I create software.
"""
USER_COUNTRY = "DE"
USER_CITY = "Somewhere"
USER_REGION = "Somewhere"

# Assistant
ASSISTANT_NAME = "Pai"
ASSISTANT_RESPONSE_STYLE = """
Friendly and casual.
"""

# Time
TIME_ZONE = "CET"

# Models
ASSISTANT_MODEL = "gpt-4.1" # Must be an OpenAI model

# Notion
NOTION_API_TOKEN = os.getenv("NOTION_API_TOKEN") # Get this from https://www.notion.so/profile/integrations
NOTION_DATABASES = {
    "notes": "your-database-id",
}
