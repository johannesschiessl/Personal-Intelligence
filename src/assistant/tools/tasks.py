import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Union

class TaskMode(Enum):
    READ = "r"
    WRITE = "w"
    DELETE = "d"

class TaskRepeat(Enum):
    NEVER = "never"
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"

class Tasks:
    def __init__(self):
        self.tasks_file = Path("data/tasks.json")
        self.tasks_file.parent.mkdir(parents=True, exist_ok=True)
        self._load_tasks()

    def _load_tasks(self) -> None:
        if self.tasks_file.exists():
            with open(self.tasks_file, 'r', encoding='utf-8') as f:
                self.tasks = json.load(f)
        else:
            self.tasks = {}
            self._save_tasks()

    def _save_tasks(self) -> None:
        with open(self.tasks_file, 'w', encoding='utf-8') as f:
            json.dump(self.tasks, f, ensure_ascii=False, indent=2)

    def process(self, mode: TaskMode, task_id: str, instructions: Optional[str] = None,
               task_datetime: Optional[str] = None, repeat: Optional[str] = None,
               agent: str = "assistant") -> str:
        if mode == TaskMode.READ:
            if not task_id:
                return self._list_all_tasks()
            return self._read_task(task_id)
        
        elif mode == TaskMode.WRITE:
            if not all([instructions, task_datetime]):
                return "Error: instructions and datetime are required for write mode"
            
            try:
                datetime.strptime(task_datetime, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                return "Error: datetime must be in format YYYY-MM-DD HH:MM:SS"
            
            if repeat and repeat not in [r.value for r in TaskRepeat]:
                return f"Error: repeat must be one of {[r.value for r in TaskRepeat]}"
            
            if agent != "assistant":
                return "Error: only 'assistant' is supported as agent at the moment"
            
            return self._write_task(task_id, instructions, task_datetime, repeat or "never", agent)
        
        elif mode == TaskMode.DELETE:
            return self._delete_task(task_id)
        
        return "Error: Invalid mode"

    def _list_all_tasks(self) -> str:
        if not self.tasks:
            return "No tasks found"
        
        result = []
        for task_id, task in self.tasks.items():
            result.append(f"Task {task_id}:")
            result.append(f"  Instructions: {task['instructions']}")
            result.append(f"  DateTime: {task['datetime']}")
            result.append(f"  Repeat: {task['repeat']}")
            result.append(f"  Agent: {task['agent']}\n")
        
        return "\n".join(result)

    def _read_task(self, task_id: str) -> str:
        if task_id not in self.tasks:
            return f"Error: Task {task_id} not found"
        
        task = self.tasks[task_id]
        return (f"Task {task_id}:\n"
                f"Instructions: {task['instructions']}\n"
                f"DateTime: {task['datetime']}\n"
                f"Repeat: {task['repeat']}\n"
                f"Agent: {task['agent']}")

    def _write_task(self, task_id: str, instructions: str, task_datetime: str,
                    repeat: str, agent: str) -> str:
        self.tasks[task_id] = {
            "instructions": instructions,
            "datetime": task_datetime,
            "repeat": repeat,
            "agent": agent
        }
        self._save_tasks()
        return f"Task {task_id} has been {'updated' if task_id in self.tasks else 'created'}"

    def _delete_task(self, task_id: str) -> str:
        if task_id not in self.tasks:
            return f"Error: Task {task_id} not found"
        
        del self.tasks[task_id]
        self._save_tasks()
        return f"Task {task_id} has been deleted"

    def get_due_tasks(self) -> List[Dict[str, str]]:
        """Returns a list of tasks that are due for execution"""
        current_time = datetime.now()
        due_tasks = []
        
        for task_id, task in list(self.tasks.items()):
            task_time = datetime.strptime(task['datetime'], "%Y-%m-%d %H:%M:%S")
            
            if task_time <= current_time:
                due_tasks.append({
                    "id": task_id,
                    "instructions": task['instructions'],
                    "agent": task['agent']
                })
                
                if task['repeat'] != TaskRepeat.NEVER.value:
                    next_time = task_time
                    if task['repeat'] == TaskRepeat.DAILY.value:
                        next_time = next_time.replace(day=next_time.day + 1)
                    elif task['repeat'] == TaskRepeat.WEEKLY.value:
                        next_time = next_time.replace(day=next_time.day + 7)
                    elif task['repeat'] == TaskRepeat.BIWEEKLY.value:
                        next_time = next_time.replace(day=next_time.day + 14)
                    elif task['repeat'] == TaskRepeat.MONTHLY.value:
                        if next_time.month == 12:
                            next_time = next_time.replace(year=next_time.year + 1, month=1)
                        else:
                            next_time = next_time.replace(month=next_time.month + 1)
                    elif task['repeat'] == TaskRepeat.YEARLY.value:
                        next_time = next_time.replace(year=next_time.year + 1)
                    
                    task['datetime'] = next_time.strftime("%Y-%m-%d %H:%M:%S")
                    self._save_tasks()
                else:
                    del self.tasks[task_id]
                    self._save_tasks()
        
        return due_tasks
