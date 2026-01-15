"""
Tasky - AI-native personal task tracker

A minimal, LLM-agent friendly task tracker designed for conversational interfaces.
"""

from .tracker import (
    add_task,
    list_tasks,
    get_task,
    complete_task,
    delete_task,
    update_task,
    daily_summary,
    search_tasks,
)
from .parser import parse_due_date, infer_priority

__version__ = "0.1.0"
__all__ = [
    "add_task",
    "list_tasks", 
    "get_task",
    "complete_task",
    "delete_task",
    "update_task",
    "daily_summary",
    "search_tasks",
    "parse_due_date",
    "infer_priority",
]
