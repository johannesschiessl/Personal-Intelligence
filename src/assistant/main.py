from config import ASSISTANT_MODEL, NOTION_API_TOKEN, NOTION_DATABASES
import openai
import json
from pathlib import Path
from typing import List, Dict, Union

from assistant.tools.memory import Memory, MemoryMode
from assistant.tools.tasks import Tasks, TaskMode
from assistant.tools.calendar import Calendar
from assistant.tools.url import Url
from assistant.tools.notion import Notion
from prompts.assistant import system_prompt, tools

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
        self.notion = Notion(api_token=NOTION_API_TOKEN, databases=NOTION_DATABASES)

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
        return system_prompt
    
    def _get_tools(self) -> List[Dict]:
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
        elif tool_call.name == "notion": 
            mode = args.pop("mode") 
            return self.notion.process(mode=mode, **args)
        
        return "Unknown tool"

    def _get_conversation_messages(self) -> List[Dict[str, str]]:
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
        system_prompt = self._get_system_prompt()
        
        tool_call_count = 0
        max_tool_calls = 10
        
        current_conversation_input = list(conversation_messages) 

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
                        assistant_response_text = response.output_text 
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
            
            if not tool_calls_found: 
                print("Assistant: No tool calls or text response from API.")
                break 

            tool_call_count += len(tool_calls_found) 
            
            if tool_call_count >= max_tool_calls: 
                current_conversation_input.append({
                    "role": "developer", 
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
                    
                    asyncio.create_task(tool_callback(tool_call.name))
                
                model_function_call_message = {
                    "type": "function_call", 
                    "id": tool_call.id,      
                    "call_id": tool_call.call_id, 
                    "name": tool_call.name,
                    "arguments": tool_call.arguments
                }
                self.messages.append(model_function_call_message) 
                current_conversation_input.append(model_function_call_message)

                result = self._process_tool_call(tool_call) 
                print("[Tool call result]:", result)
                
                function_output_message = {
                    "type": "function_call_output", 
                    "call_id": tool_call.call_id,   
                    "output": str(result)           
                }
                self.messages.append(function_output_message)
                current_conversation_input.append(function_output_message)
                
                self._save_conversation_history()
        
        final_response = self.client.responses.create(
            model=self.model,
            instructions=system_prompt,
            input=current_conversation_input 
        )
        
        final_message_text = "Sorry, I reached a limit in processing your request. Please try again." 
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
