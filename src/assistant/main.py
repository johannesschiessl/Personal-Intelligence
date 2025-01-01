import openai
import json
from pathlib import Path
from typing import List, Dict
from config import USER_NAME, ASSISTANT_NAME, ASSISTANT_MODEL, CUSTOM_INSTRUCTIONS
from utils.datetime import get_current_date, get_current_time

class Assistant:
    def __init__(self):
        self.client = openai.OpenAI()
        self.model = ASSISTANT_MODEL
        self.history_file = Path("data/assistant/conversation_history.json")
        self.messages = self._load_conversation_history()

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
</assistant_info>

<current_context>
Date: {get_current_date()}
Time: {get_current_time()}
</current_context>

<custom_instructions>
{CUSTOM_INSTRUCTIONS}
</custom_instructions>
"""
        return system_prompt

    def _get_context_messages(self) -> List[Dict[str, str]]:
        context = [{"role": "system", "content": self._get_system_prompt()}]
        context.extend(self.messages[-50:] if len(self.messages) > 50 else self.messages)
        return context
    
    def chat(self, message: str) -> str:
        self.messages.append({"role": "user", "content": message})

        print("User:", message)
        
        context_messages = self._get_context_messages()
        response = self.client.chat.completions.create(
            model=self.model,
            messages=context_messages,
        )
        
        assistant_message = {"role": "assistant", "content": response.choices[0].message.content}
        self.messages.append(assistant_message) 
        
        self._save_conversation_history()
        
        print("Assistant:", response.choices[0].message.content)
        
        return response.choices[0].message.content
