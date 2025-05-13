from dotenv import load_dotenv
import os

load_dotenv()

# User
USER_NAME = "Your Name"
USER_ROLE = "Your Role"
USER_BIO = """
What you want the assistant to know about you
"""
USER_COUNTRY = "Your Country" # e.g. DE, US, etc.
USER_REGION = "Your Region" # e.g. Berlin, California, etc.
USER_CITY = "Your City" # e.g. Berlin, San Francisco, etc.

# Assistant
ASSISTANT_NAME = "Name of your assistant"
ASSISTANT_RESPONSE_STYLE = """
How you want the assistant to respond to you
""" 

# Time
TIME_ZONE = "UTC" # e.g. CET, EST, etc.

# Models
ASSISTANT_MODEL = "gpt-4.1" # Must be an OpenAI model

# Notion
NOTION_API_TOKEN = os.getenv("NOTION_API_TOKEN") # Get this from https://www.notion.so/profile/integrations
NOTION_DATABASES = {
    "database-name": "database_id",
}
