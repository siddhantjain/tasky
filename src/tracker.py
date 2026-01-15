"""
Core task tracking functionality.
"""

import json
import uuid
from datetime import datetime, date
from pathlib import Path
from typing import Optional, List, Dict, Any, Literal

from .parser import parse_due_date, infer_priority

# Data storage
DATA_DIR = Path(__file__).parent.parent / "data"
TASKS_FILE = DATA_DIR / "tasks.json"

# Types
Priority = Literal["high", "medium", "low"]
Status = Literal["pending", "completed", "archived"]


def _ensure_data_dir() -> None:
    """Ensure data directory exists."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _load_tasks() -> List[Dict[str, Any]]:
    """Load tasks from JSON file."""
    _ensure_data_dir()
    if not TASKS_FILE.exists():
        return []
    with open(TASKS_FILE) as f:
        return json.load(f)


def _save_tasks(tasks: List[Dict[str, Any]]) -> None:
    """Save tasks to JSON file."""
    _ensure_data_dir()
    with open(TASKS_FILE, "w") as f:
        json.dump(tasks, f, indent=2, default=str)


def add_task(
    title: str,
    due: Optional[str] = None,
    priority: Optional[Priority] = None,
    tags: Optional[List[str]] = None,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Add a new task.
    
    Args:
        title: Task title/description
        due: Due date (natural language like "tomorrow", "next monday", or ISO date)
        priority: high, medium, or low (auto-inferred if not provided)
        tags: List of context tags (e.g., ["work", "urgent"])
        notes: Additional notes
    
    Returns:
        The created task dict
    
    Example:
        >>> add_task("Review PR for auth service", due="tomorrow", tags=["work"])
        >>> add_task("Buy birthday gift for Sowmya", due="next friday", priority="high")
        >>> add_task("Call dentist")  # No due date, priority auto-inferred as low
    """
    # Parse due date if provided
    due_date = None
    if due:
        due_date = parse_due_date(due)
    
    # Infer priority if not provided
    if priority is None:
        priority = infer_priority(title, due_date, tags)
    
    task = {
        "id": f"task_{uuid.uuid4().hex[:8]}",
        "title": title,
        "status": "pending",
        "priority": priority,
        "due": due_date.isoformat() if due_date else None,
        "tags": tags or [],
        "notes": notes,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "completed_at": None,
    }
    
    tasks = _load_tasks()
    tasks.append(task)
    _save_tasks(tasks)
    
    return task


def list_tasks(
    status: Optional[Status] = "pending",
    priority: Optional[Priority] = None,
    tag: Optional[str] = None,
    due_before: Optional[str] = None,
    due_today: bool = False,
    overdue: bool = False,
    include_completed: bool = False,
) -> List[Dict[str, Any]]:
    """
    List tasks with optional filters.
    
    Args:
        status: Filter by status (pending, completed, archived). None for all.
        priority: Filter by priority level
        tag: Filter by tag
        due_before: Show tasks due before this date
        due_today: Show only tasks due today
        overdue: Show only overdue tasks
        include_completed: Include completed tasks (overrides status filter)
    
    Returns:
        List of matching tasks, sorted by priority then due date
    
    Example:
        >>> list_tasks()  # All pending tasks
        >>> list_tasks(tag="work")  # Work tasks
        >>> list_tasks(due_today=True)  # Due today
        >>> list_tasks(overdue=True)  # Past due
    """
    tasks = _load_tasks()
    today = date.today()
    
    # Apply filters
    filtered = []
    for task in tasks:
        # Status filter
        if include_completed:
            if task["status"] == "archived":
                continue
        elif status and task["status"] != status:
            continue
        
        # Priority filter
        if priority and task.get("priority") != priority:
            continue
        
        # Tag filter
        if tag and tag not in task.get("tags", []):
            continue
        
        # Due date filters
        task_due = None
        if task.get("due"):
            task_due = date.fromisoformat(task["due"])
        
        if due_today:
            if not task_due or task_due != today:
                continue
        
        if overdue:
            if not task_due or task_due >= today:
                continue
        
        if due_before:
            before_date = date.fromisoformat(due_before)
            if not task_due or task_due > before_date:
                continue
        
        filtered.append(task)
    
    # Sort by priority (high > medium > low) then by due date
    priority_order = {"high": 0, "medium": 1, "low": 2, None: 3}
    
    def sort_key(t):
        pri = priority_order.get(t.get("priority"), 3)
        due = t.get("due") or "9999-99-99"  # No due date sorts last
        return (pri, due)
    
    filtered.sort(key=sort_key)
    
    return filtered


def get_task(task_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a specific task by ID.
    
    Args:
        task_id: The task ID
    
    Returns:
        Task dict or None if not found
    """
    tasks = _load_tasks()
    for task in tasks:
        if task["id"] == task_id:
            return task
    return None


def complete_task(task_id: str) -> Optional[Dict[str, Any]]:
    """
    Mark a task as completed.
    
    Args:
        task_id: The task ID (or partial match of title)
    
    Returns:
        The completed task, or None if not found
    
    Example:
        >>> complete_task("task_abc123")
        >>> complete_task("PR review")  # Partial title match
    """
    tasks = _load_tasks()
    
    # Find task by ID or title match
    for task in tasks:
        if task["id"] == task_id or task_id.lower() in task["title"].lower():
            if task["status"] == "completed":
                return task  # Already completed
            
            task["status"] = "completed"
            task["completed_at"] = datetime.utcnow().isoformat() + "Z"
            _save_tasks(tasks)
            return task
    
    return None


def delete_task(task_id: str, archive: bool = True) -> Optional[Dict[str, Any]]:
    """
    Delete (archive) a task.
    
    Args:
        task_id: The task ID (or partial match of title)
        archive: If True, mark as archived. If False, permanently delete.
    
    Returns:
        The deleted/archived task, or None if not found
    """
    tasks = _load_tasks()
    
    for i, task in enumerate(tasks):
        if task["id"] == task_id or task_id.lower() in task["title"].lower():
            if archive:
                task["status"] = "archived"
                _save_tasks(tasks)
                return task
            else:
                deleted = tasks.pop(i)
                _save_tasks(tasks)
                return deleted
    
    return None


def update_task(
    task_id: str,
    title: Optional[str] = None,
    due: Optional[str] = None,
    priority: Optional[Priority] = None,
    tags: Optional[List[str]] = None,
    notes: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Update an existing task.
    
    Args:
        task_id: The task ID
        title: New title (if changing)
        due: New due date (if changing)
        priority: New priority (if changing)
        tags: New tags (replaces existing)
        notes: New notes (if changing)
    
    Returns:
        The updated task, or None if not found
    """
    tasks = _load_tasks()
    
    for task in tasks:
        if task["id"] == task_id:
            if title is not None:
                task["title"] = title
            if due is not None:
                task["due"] = parse_due_date(due).isoformat() if due else None
            if priority is not None:
                task["priority"] = priority
            if tags is not None:
                task["tags"] = tags
            if notes is not None:
                task["notes"] = notes
            
            _save_tasks(tasks)
            return task
    
    return None


def daily_summary(target_date: Optional[str] = None) -> Dict[str, Any]:
    """
    Get a summary of tasks for a specific day.
    
    Args:
        target_date: Date in ISO format (defaults to today)
    
    Returns:
        Summary dict with due_today, overdue, and completed_today lists
    
    Example:
        >>> daily_summary()
        >>> daily_summary("2026-01-16")
    """
    if target_date:
        today = date.fromisoformat(target_date)
    else:
        today = date.today()
    
    tasks = _load_tasks()
    
    due_today = []
    overdue = []
    completed_today = []
    high_priority = []
    
    for task in tasks:
        task_due = date.fromisoformat(task["due"]) if task.get("due") else None
        
        # Completed today
        if task["status"] == "completed" and task.get("completed_at"):
            completed_date = datetime.fromisoformat(
                task["completed_at"].replace("Z", "")
            ).date()
            if completed_date == today:
                completed_today.append(task)
        
        # Skip non-pending for other categories
        if task["status"] != "pending":
            continue
        
        # Due today
        if task_due == today:
            due_today.append(task)
        
        # Overdue
        elif task_due and task_due < today:
            overdue.append(task)
        
        # High priority (regardless of due date)
        if task.get("priority") == "high" and task_due != today:
            high_priority.append(task)
    
    # Sort each list
    priority_order = {"high": 0, "medium": 1, "low": 2}
    for lst in [due_today, overdue, high_priority]:
        lst.sort(key=lambda t: priority_order.get(t.get("priority"), 2))
    
    return {
        "date": today.isoformat(),
        "due_today": due_today,
        "overdue": overdue,
        "completed_today": completed_today,
        "high_priority": high_priority,
        "summary": _format_summary(due_today, overdue, completed_today, high_priority),
    }


def _format_summary(due_today, overdue, completed_today, high_priority) -> str:
    """Format a human-readable summary."""
    lines = []
    
    if overdue:
        lines.append(f"⚠️ {len(overdue)} overdue task(s)")
    
    if due_today:
        lines.append(f"📅 {len(due_today)} task(s) due today")
    
    if high_priority:
        lines.append(f"🔴 {len(high_priority)} high priority task(s)")
    
    if completed_today:
        lines.append(f"✅ {len(completed_today)} completed today")
    
    if not lines:
        return "No tasks for today. Enjoy! 🎉"
    
    return "\n".join(lines)


def search_tasks(query: str) -> List[Dict[str, Any]]:
    """
    Search tasks by title or notes.
    
    Args:
        query: Search string
    
    Returns:
        List of matching tasks
    """
    tasks = _load_tasks()
    query_lower = query.lower()
    
    results = []
    for task in tasks:
        if task["status"] == "archived":
            continue
        
        title_match = query_lower in task["title"].lower()
        notes_match = task.get("notes") and query_lower in task["notes"].lower()
        tag_match = any(query_lower in tag.lower() for tag in task.get("tags", []))
        
        if title_match or notes_match or tag_match:
            results.append(task)
    
    return results
