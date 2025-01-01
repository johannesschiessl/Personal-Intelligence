from enum import Enum
from pathlib import Path
import json
from typing import Optional, Dict

class MemoryMode(Enum):
    WRITE = "w"
    DELETE = "d"

class Memory:
    def __init__(self):
        self.memory_file = Path("data/assistant/memories.json")
        self.memories = self._load_memories()
        
    def _load_memories(self) -> Dict:
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        
        if self.memory_file.exists():
            with open(self.memory_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _save_memories(self):
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump(self.memories, f, ensure_ascii=False, indent=2)

    def process(self, mode: MemoryMode, memory_id: str, content: Optional[str] = None) -> str:
        if mode == MemoryMode.WRITE:
            self.memories[memory_id] = content
            self._save_memories()
            return f"Memory {memory_id} saved successfully"
        elif mode == MemoryMode.DELETE:
            if memory_id in self.memories:
                del self.memories[memory_id]
                self._save_memories()
                return f"Memory {memory_id} deleted successfully"
            return f"Memory {memory_id} not found"
        
    def get_all_memories(self) -> str:
        if not self.memories:
            return "No memories stored"
        
        memory_str = ""
        for memory_id, content in self.memories.items():
            memory_str += f"{memory_id}: {content}\n"
        return memory_str.strip()
