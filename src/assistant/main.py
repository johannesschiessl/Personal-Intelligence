import openai
import json
from pathlib import Path
from typing import List, Dict, Union
from config import USER_NAME, ASSISTANT_NAME, ASSISTANT_MODEL, CUSTOM_INSTRUCTIONS
from utils.datetime import get_current_date, get_current_time
from assistant.tools.memory import Memory, MemoryMode

class Assistant:
    def __init__(self):
        self.client = openai.OpenAI()
        self.model = ASSISTANT_MODEL
        self.history_file = Path("data/assistant/conversation_history.json")
        self.messages = self._load_conversation_history()
        self.memory = Memory()

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
You can see and analyze images that are sent to you.
</assistant_info>

<current_context>
Date: {get_current_date()}
Time: {get_current_time()}
</current_context>

<tools>
<memory>
You have access to a memory tool that allows you to store, update and delete information:
- To write a memory: Use mode 'w' with a descriptive id and the content to store, using mode w on an existing memory will overwrite its content
- To delete a memory: Use mode 'd' with the id of the memory to delete
<example>
memory(mode='w', id='user_birthday', content='April 15th')
memory(mode='d', id='user_birthday')
</example>
</memory>
</tools>

<memories>
{self.memory.get_all_memories()}
</memories>

<custom_instructions>
{CUSTOM_INSTRUCTIONS}
</custom_instructions>
"""
        return system_prompt
    
    def _get_tools(self) -> List[Dict]:
        tools = [
            {
                "type": "function",
                "function": {
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
                }
            }
        ]
        return tools

    def _process_tool_call(self, tool_call) -> str:
        if tool_call.function.name == "memory":
            args = json.loads(tool_call.function.arguments)
            mode = MemoryMode(args["mode"])
            memory_id = args["id"]
            content = args.get("content")
            return self.memory.process(mode, memory_id, content)
        return "Unknown tool"

    def _get_context_messages(self) -> List[Dict[str, str]]:
        context = [{"role": "system", "content": self._get_system_prompt()}]
        context.extend(self.messages[-50:] if len(self.messages) > 50 else self.messages)
        return context
    
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
        
        context_messages = self._get_context_messages()
        context_messages[-1] = user_message
        
        tool_call_count = 0
        max_tool_calls = 10
        
        while tool_call_count < max_tool_calls:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=context_messages,
                tools=self._get_tools()
            )
            
            message = response.choices[0].message
            
            if not message.tool_calls:
                assistant_message = {"role": "assistant", "content": message.content}
                self.messages.append(assistant_message)
                self._save_conversation_history()
                print("Assistant:", message.content)
                return message.content
            
            tool_call_count += 1
            
            if tool_call_count == max_tool_calls:
                context_messages.append({
                    "role": "system",
                    "content": "You have reached the maximum number of consecutive tool calls. Please summarize your progress and provide a final response to the user."
                })
            
            for tool_call in message.tool_calls:
                print("Assistant: Using", tool_call.function.name, tool_call.function.arguments)
                
                if tool_callback:
                    import asyncio
                    asyncio.create_task(tool_callback(tool_call.function.name))
                
                tool_call_message = {
                    "role": "assistant",
                    "content": None,
                    "tool_call_id": tool_call.id,
                    "tool_calls": [
                        {
                            "id": tool_call.id,
                            "type": "function",
                            "function": {
                                "name": tool_call.function.name,
                                "arguments": tool_call.function.arguments
                            }
                        }
                    ]
                }
                self.messages.append(tool_call_message)
                
                result = self._process_tool_call(tool_call)
                print("[Tool call result]:", result)
                
                tool_result_message = {
                    "role": "tool",
                    "content": result,
                    "tool_call_id": tool_call.id
                }
                self.messages.append(tool_result_message)
                
                context_messages.append(tool_call_message)
                context_messages.append(tool_result_message)
                
                self._save_conversation_history()
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=context_messages
        )
        
        final_message = response.choices[0].message.content
        self.messages.append({"role": "assistant", "content": final_message})
        self._save_conversation_history()
        print("Assistant:", final_message)
        return final_message
