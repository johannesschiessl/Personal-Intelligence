from config import USER_CITY, USER_COUNTRY, USER_NAME, USER_REGION, USER_ROLE, USER_BIO, ASSISTANT_NAME, ASSISTANT_RESPONSE_STYLE, TIME_ZONE
from utils.datetime import get_current_date, get_current_time

system_prompt = f"""
# Role and Objective
You are {ASSISTANT_NAME}, the proactive and highly capable personal assistant for {USER_NAME}, interacting primarily via Telegram. Your goal is to help {USER_NAME} efficiently manage their daily tasks, reminders, calendar events, and knowledge in their Notion databases, and provide concise, friendly, and context-aware responses.

# Instructions
- Keep your responses concise, friendly, and informal. Always match {USER_NAME}'s conversational style described in {ASSISTANT_RESPONSE_STYLE}.
- Do not use markdown formatting in responses to {USER_NAME}, as interactions occur via Telegram.
- You can see and analyze images sent by {USER_NAME}.
- Always proactively store relevant memories (using the memory tool) to enhance interactions, anticipate user needs, and get to know {USER_NAME} better over time.
- If {USER_NAME} references something matching the name of an available Notion database, you can be certain they are referring to that database. Use the Notion tool accordingly.

## Agentic Reminders
- Persistence: You are an agent. Continue interactions until {USER_NAME}'s request is fully addressed. Only terminate your response once you're certain the user's query is fully resolved.
- Tool-calling: Actively use your provided tools. Never guess or fabricate answers. When uncertain about content or user-related context, always use tools (memory, calendar, tasks, notion, web_search, url) to retrieve accurate information.
- Planning: Explicitly plan your actions before executing tool calls. Reflect thoroughly on outcomes after each tool call. Avoid silent chains of tool calls—clearly articulate your thought process.

# Tools Overview

## Memory
- Store/update: memory(mode='w', id='descriptive_id', content='relevant information')
- Delete: memory(mode='d', id='descriptive_id')

## Tasks
- Write: tasks(mode='w', id='task_id', instructions='what to do', datetime='YYYY-MM-DD HH:MM:SS', repeat='optional frequency')
- Read: tasks(mode='r', id='task_id')
- Delete: tasks(mode='d', id='task_id')

## Calendar
- Read: calendar(mode='r', range_val=10 or -10 for past events)
- Write/Update: calendar(mode='w', title='', start_time='', end_time='', description='', event_id='optional for updates')
- Delete: calendar(mode='d', event_id='')
- All calendar operations are in the {TIME_ZONE} timezone.

## Web Search
- Use directly: web_search()

## URL Tool
- Fetch URL content: url(url='https://example.com')

## Notion
Available databases: {", ".join(self.notion.databases.keys())}
- List databases: notion(mode='list_databases')
- Create new page:
  notion(mode="create_page", page_title="", database_name="", properties_json="", content_blocks_json="")
- Query database:
  notion(mode="query_db", database_name="", filter_json="", sorts_json="")
- Add content to a page:
  notion(mode='add_page_content', page_id='', content_blocks_json='')
- Retrieve page content:
  notion(mode='get_page_content', page_id='')
- Update page properties:
  notion(mode='update_page_props', page_id='', properties_json='')

# Reasoning Strategy
1. Clearly identify and analyze {USER_NAME}'s request.
2. Determine if relevant information exists in memories, calendar, tasks, or Notion databases.
3. Explicitly plan your next actions and explain your reasoning to {USER_NAME} before proceeding.
4. Execute planned tool calls.
5. Reflect on outcomes and communicate results clearly back to {USER_NAME}.

# Output Format
- Do NOT use markdown in your responses.
- Maintain short, casual, and natural language.

# Proactive Memory Management
- Proactively store relevant information about {USER_NAME} to anticipate and encourage positive habits (e.g., mowing the lawn).

# Contextual Information
- User name: {USER_NAME}
- User role: {USER_ROLE}
- User bio: {USER_BIO}
- User location: {USER_CITY}, {USER_REGION}, {USER_COUNTRY}

# Current Context
- Date: {get_current_date()}
- Time: {get_current_time()}

# Final Instructions
Always aim to make interactions smooth, helpful, and contextually relevant. Proactively leverage all available tools to keep track of important details to assist {USER_NAME} efficiently and enhance their productivity.
"""


tools = [
            {
                "type": "web_search_preview",
                "search_context_size": "medium",
                "user_location": {
                    "type": "approximate",
                    "country": USER_COUNTRY,
                    "city": USER_CITY,
                    "region": USER_REGION,
                },
            },
            {
                "type": "function",
                "name": "memory",
                "description": "Store or delete memories that persist across conversations",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "mode": {
                            "type": "string",
                            "enum": ["w", "d"],
                            "description": "The mode of operation - 'w' for write, 'd' for delete"
                        },
                        "id": {
                            "type": "string",
                            "description": "The unique identifier for the memory"
                        },
                        "content": {
                            "type": "string",
                            "description": "The content to store (only required for write mode)"
                        }
                    },
                    "required": ["mode", "id"]
                }
            },
            {
                "type": "function",
                "name": "url",
                "description": "Fetch and parse content from a URL",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "The URL to fetch content from"
                        }
                    },
                    "required": ["url"]
                }
            },
            {
                "type": "function",
                "name": "tasks",
                "description": "Schedule instructions for the assistant to execute at a specific time",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "mode": {
                            "type": "string",
                            "enum": ["r", "w", "d"],
                            "description": "The mode of operation - 'r' for read, 'w' for write, 'd' for delete"
                        },
                        "id": {
                            "type": "string",
                            "description": "The unique identifier for the task"
                        },
                        "instructions": {
                            "type": "string",
                            "description": "The instructions to execute when the task is due (only required for write mode)"
                        },
                        "datetime": {
                            "type": "string",
                            "description": "The date and time when the task should be executed in format YYYY-MM-DD HH:MM:SS (only required for write mode)"
                        },
                        "repeat": {
                            "type": "string",
                            "enum": ["never", "daily", "weekly", "biweekly", "monthly", "yearly"],
                            "description": "How often the task should repeat (optional, defaults to never)"
                        }
                    },
                    "required": ["mode", "id"]
                }
            },
            {
                "type": "function",
                "name": "calendar",
                "description": "Interact with the user's Google Calendar to read, write, or delete events",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "mode": {
                            "type": "string",
                            "enum": ["r", "w", "d"],
                            "description": "The mode of operation - 'r' for read, 'w' for write, 'd' for delete"
                        },
                        "range_val": {
                            "type": "integer",
                            "description": "For read mode: number of events to show (positive for future, negative for past, default 10)"
                        },
                        "event_id": {
                            "type": "string",
                            "description": "The event ID for updating or deleting events"
                        },
                        "title": {
                            "type": "string",
                            "description": "The title/summary of the event (required for write mode)"
                        },
                        "description": {
                            "type": "string",
                            "description": "Optional description of the event"
                        },
                        "start_time": {
                            "type": "string",
                            "description": "Start time of the event in YYYY-MM-DD HH:MM:SS format (required for write mode)"
                        },
                        "end_time": {
                            "type": "string",
                            "description": "End time of the event in YYYY-MM-DD HH:MM:SS format (required for write mode)"
                        }
                    },
                    "required": ["mode"]
                }
            },
            { 
                "type": "function",
                "name": "notion",
                "description": "Interact with your Notion workspace to create/query pages and databases, and manage content.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "mode": {
                            "type": "string",
                            "enum": ["list_databases", "create_page", "query_db", "add_page_content", "get_page_content", "update_page_props"],
                            "description": "The Notion operation to perform."
                        },
                        "database_name": {"type": "string", "description": "Name of the database to use (for 'create_page' or 'query_db'). Available databases shown in system prompt."},
                        "page_title": {"type": "string", "description": "Title of the page (required for 'create_page')."},
                        "parent_database_id": {"type": "string", "description": "ID of the parent database (for 'create_page' if parent is a database and database_name is not provided)."},
                        "parent_page_id": {"type": "string", "description": "ID of the parent page (for 'create_page' if parent is another page)."},
                        "database_id": {"type": "string", "description": "ID of the Notion database (for 'query_db' if database_name is not provided)."},
                        "page_id": {"type": "string", "description": "ID of the Notion page (for 'add_page_content', 'get_page_content', 'update_page_props')."},
                        "properties_json": {"type": "string", "description": "JSON string for page properties. For 'create_page' in a database or for 'update_page_props'."},
                        "content_blocks_json": {"type": "string", "description": "JSON string of Notion block objects. For 'create_page' or 'add_page_content'."},
                        "filter_json": {"type": "string", "description": "JSON string for Notion API filter object when querying a database."},
                        "sorts_json": {"type": "string", "description": "JSON string for Notion API sorts array when querying a database."}
                    },
                    "required": ["mode"] 
                }
            }
        ]