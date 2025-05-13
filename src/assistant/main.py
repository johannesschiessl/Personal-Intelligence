import openai
import json
from pathlib import Path
from typing import List, Dict, Union
from config import USER_CITY, USER_COUNTRY, USER_NAME, USER_REGION, USER_ROLE, USER_BIO, ASSISTANT_NAME, ASSISTANT_RESPONSE_STYLE, ASSISTANT_MODEL, TIME_ZONE
from utils.datetime import get_current_date, get_current_time
from assistant.tools.memory import Memory, MemoryMode
from assistant.tools.tasks import Tasks, TaskMode
from assistant.tools.calendar import Calendar
from assistant.tools.url import Url

class Assistant:
    def __init__(self):
        self.client = openai.OpenAI()
        self.model = ASSISTANT_MODEL
        self.history_file = Path("data/assistant/conversation_history.json")
        self.messages = self._load_conversation_history()
        self.memory = Memory()
        self.tasks = Tasks()
        self.calendar = Calendar()
        self.url = Url()

        print("Assistant initialized")

    def _load_conversation_history(self) -> List[Dict[str, str]]:
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        
        if self.history_file.exists():
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def _save_conversation_history(self):
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(self.messages, f, ensure_ascii=False, indent=2)
    
    def _get_system_prompt(self) -> str:
        system_prompt = f"""<assistant_info>
You are {ASSISTANT_NAME}, a personal assistant for {USER_NAME}.
You are interacting with {USER_NAME} via Telegram. So keep your responses short and concise. And do not use markdown.
You can see and analyze images that are sent to you. Interact with {USER_NAME} as described in the response_style. Help {USER_NAME} with what ever they need.
</assistant_info>

<response_style>
{ASSISTANT_RESPONSE_STYLE}
</response_style>

<tools>
<web_search>
You have access to a web search tool that allows you to search the web.
</web_search>

<memory>
You have access to a memory tool that allows you to store, update and delete information:
- To write a memory: Use mode 'w' with a descriptive id and the content to store, using mode w on an existing memory will overwrite its content
- To delete a memory: Use mode 'd' with the id of the memory to delete
<example>
memory(mode='w', id='user_birthday', content='April 15th')
memory(mode='d', id='user_birthday')
</example>
</memory>

<tasks>
You have access to a tasks tool that allows you to schedule instructions for yourself:
- To write a task: Use mode 'w' with a descriptive id, instructions, datetime (YYYY-MM-DD HH:MM:SS), and optional repeat setting
- To read tasks: Use mode 'r' with an id to get details of a specific task
- To delete a task: Use mode 'd' with the id of the task to delete
<example>
tasks(mode='w', id='daily_weather', instructions='Tell me the weather forecast for today', datetime='2024-01-01 08:00:00', repeat='daily')
tasks(mode='r')
tasks(mode='r', id='daily_weather')
tasks(mode='d', id='daily_weather')
</example>
</tasks>

<calendar>
You have access to a calendar tool that allows you to interact with the user's Google Calendar:
- To read events: Use mode 'r' with an optional range_val parameter (default 10, negative for past events)
- To write/update events: Use mode 'w' with title, start_time, end_time (both in YYYY-MM-DD HH:MM:SS format), optional description, and optional event_id (for updates)
- To delete events: Use mode 'd' with the event_id
- All times are in {TIME_ZONE} timezone
<example>
calendar(mode='r', range_val=7)  # Show next 7 events
calendar(mode='r', range_val=-5)  # Show 5 past events
calendar(mode='w', title='Meeting', description='Team sync', start_time='2024-01-01 10:00:00', end_time='2024-01-01 11:00:00')
calendar(mode='w', event_id='abc123', title='Updated Meeting', start_time='2024-01-01 11:00:00', end_time='2024-01-01 12:00:00')
calendar(mode='d', event_id='abc123')
</example>
</calendar>

<url>
You have access to a URL tool that allows you to fetch and parse content from web pages:
- The tool will return the text content of the webpage, cleaned and formatted
- The content is limited to 10000 characters to avoid token limits
<example>
url(url='https://example.com')
</example>
</url>

</tools>

<user_info>
<user_name>{USER_NAME}</user_name>
<user_role>{USER_ROLE}</user_role>
<user_bio>
{USER_BIO}
</user_bio>
</user_info>

<memories>
{self.memory.get_all_memories()}
</memories>

<calendar_context>
<last_event>{self.calendar.process(mode='r', range_val=-1)}</last_event>
<current_next_events>{self.calendar.process(mode='r', range_val=5)}</current_next_events>
</calendar_context>

<current_context>
<date>{get_current_date()}</date>
<time>{get_current_time()}</time>
</current_context>
"""
        return system_prompt
    
    def _get_tools(self) -> List[Dict]:
        tools = [
            {
                "type": "web_search_preview",
                "search_context_size": "low",
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
            }
        ]
        return tools

    def _process_tool_call(self, tool_call) -> str:
        args = json.loads(tool_call.arguments)
        
        if tool_call.name == "memory":
            mode = MemoryMode(args["mode"])
            memory_id = args["id"]
            content = args.get("content")
            return self.memory.process(mode, memory_id, content)
     
        
        elif tool_call.name == "tasks":
            mode = TaskMode(args["mode"])
            task_id = args["id"]
            instructions = args.get("instructions")
            task_datetime = args.get("datetime")
            repeat = args.get("repeat")
            return self.tasks.process(mode, task_id, instructions, task_datetime, repeat)
        
        elif tool_call.name == "calendar":
            mode = args["mode"]
            range_val = args.get("range_val", 10)
            event_id = args.get("event_id")
            title = args.get("title")
            description = args.get("description")
            start_time = args.get("start_time")
            end_time = args.get("end_time")
            return self.calendar.process(mode, range_val, event_id, title, description, start_time, end_time)
        
        elif tool_call.name == "url":
            url = args["url"]
            return self.url.process(url)
        
        return "Unknown tool"

    def _get_conversation_messages(self) -> List[Dict[str, str]]:
        # Returns only user and assistant messages for the 'input' parameter
        return self.messages[-200:] if len(self.messages) > 200 else self.messages
    
    def chat(self, message: Union[str, Dict], tool_callback=None) -> str:
        if isinstance(message, str):
            user_message = {"role": "user", "content": message}
            print("User:", message)
        else:
            user_message = {
                "role": "user",
                "content": [
                    {"type": "text", "text": message.get("text", "What's in this image?")},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": message["image_url"],
                            "detail": "high"
                        }
                    }
                ]
            }
            print("User: [Image]", message.get("text", ""))
        
        self.messages.append({"role": "user", "content": str(user_message["content"])})
        
        conversation_messages = self._get_conversation_messages()
        # The user_message itself is already appended to self.messages,
        # so it will be included in conversation_messages.
        # No need to replace the last element specifically.

        system_prompt = self._get_system_prompt()
        
        tool_call_count = 0
        max_tool_calls = 10
        
        current_conversation_input = list(conversation_messages) # Make a mutable copy

        while tool_call_count < max_tool_calls:
            response = self.client.responses.create(
                model=self.model,
                instructions=system_prompt,
                input=current_conversation_input,
                tools=self._get_tools()
            )
            
            assistant_response_text = None
            tool_calls_found = []

            if response.output:
                for output_item in response.output:
                    if output_item.type == "message" and output_item.content and output_item.content[0].type == "output_text":
                        assistant_response_text = response.output_text # Use convenience accessor
                        break 
                    elif output_item.type == "function_call":
                        tool_calls_found.append(output_item)
            
            if not tool_calls_found and assistant_response_text is not None:
                assistant_message_content = assistant_response_text
                assistant_message_for_history = {"role": "assistant", "content": assistant_message_content}
                self.messages.append(assistant_message_for_history)
                self._save_conversation_history()
                print("Assistant:", assistant_message_content)
                return assistant_message_content
            
            if not tool_calls_found: # No tool calls and no text response, implies an issue or empty response
                # This case should ideally not happen if the API behaves as expected
                # and provides either text or tool_calls.
                # If it does, we might need to force a final response.
                print("Assistant: No tool calls or text response from API.")
                break # Exit loop to generate final response

            tool_call_count += len(tool_calls_found) # Increment by number of tools called in this turn
            
            if tool_call_count >= max_tool_calls: # Check if total tool calls reached limit
                current_conversation_input.append({
                    "role": "developer", # Using developer role for system-like messages to the model
                    "content": "You have reached the maximum number of consecutive tool calls. Please summarize your progress and provide a final response to the user."
                })
            
            for tool_call in tool_calls_found:
                print("Assistant: Using", tool_call.name, tool_call.arguments)
                
                if tool_callback:
                    import asyncio
                    try:
                        loop = asyncio.get_running_loop()
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                    
                    # Schedule the callback without blocking
                    asyncio.create_task(tool_callback(tool_call.name))

                # Append the model's decision to call the tool
                # The Responses API uses 'function_call' type in the output,
                # and we need to construct an equivalent message for the *next* API call's input.
                # The 'assistant' message with 'tool_calls' is the Chat Completions format.
                # For Responses API, we append the 'function_call' output directly,
                # and then the 'function_call_output'.
                
                # This is the model's "request" to call a function
                model_function_call_message = {
                    "type": "function_call", # Matches the type from response.output
                    "id": tool_call.id,      # From the specific function_call item
                    "call_id": tool_call.call_id, # call_id is also present
                    "name": tool_call.name,
                    "arguments": tool_call.arguments
                }
                # self.messages is for long-term history, format might need to be consistent
                # For now, let's adapt it to what the next call to `responses.create` might expect
                # based on the documentation for "Supplying model with results"
                # The documentation shows appending the raw tool_call object.
                self.messages.append(model_function_call_message) # Storing the raw tool call
                current_conversation_input.append(model_function_call_message)


                result = self._process_tool_call(tool_call) # tool_call here is the object from response.output
                print("[Tool call result]:", result)
                
                # This is the result of our execution of the function
                function_output_message = {
                    "type": "function_call_output", # Correct type for the Responses API
                    "call_id": tool_call.call_id,   # Use call_id to link to the function_call
                    "output": str(result)           # Output must be a string
                }
                self.messages.append(function_output_message)
                current_conversation_input.append(function_output_message)
                
                self._save_conversation_history()
        
        # If loop finishes (e.g. max_tool_calls reached or no tool calls and no text)
        # Make a final call to get a text response
        final_response = self.client.responses.create(
            model=self.model,
            instructions=system_prompt,
            input=current_conversation_input # Use the latest state of conversation_input
            # No tools needed for the final summarization ideally
        )
        
        final_message_text = "Sorry, I reached a limit in processing your request. Please try again." # Default
        if final_response.output and final_response.output[0].type == "message" and final_response.output[0].content[0].type == "output_text":
            final_message_text = final_response.output_text

        self.messages.append({"role": "assistant", "content": final_message_text})
        self._save_conversation_history()
        print("Assistant:", final_message_text)
        return final_message_text

    def process_due_tasks(self, message_callback=None, tool_callback=None) -> None:
        """Process any tasks that are due for execution
        
        Args:
            message_callback: Optional async function to call with the assistant's response
            tool_callback: Optional async function to call when tools are used
        """
        due_tasks = self.tasks.get_due_tasks()
        for task in due_tasks:
            task_message = f"TASK {task['id']}: {task['instructions']}"
            response = self.chat(task_message, tool_callback)
            
            if message_callback:
                import asyncio
                asyncio.create_task(message_callback(response))
