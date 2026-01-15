# 📋 Tasky

**An AI-native personal task tracker designed for LLM agents.**

Tasky is a minimal, conversational task tracker built for AI assistants. No UI needed—just natural language.

## Features

- 🤖 **Agent-Native** — Designed for LLM-first interaction
- 📝 **Natural Language Dates** — "tomorrow", "next monday", "in 3 days"
- 🎯 **Smart Priority** — Auto-infers urgency from context
- 🏷️ **Context Tags** — Organize by work/personal/project
- 📊 **Daily Summary** — What's due, overdue, completed
- 🔍 **Search** — Find tasks by title, notes, or tags

## Installation

```bash
git clone https://github.com/siddhantjain/tasky.git
cd tasky
```

No dependencies required beyond Python 3.8+.

## Quick Start

```python
from src import add_task, list_tasks, complete_task, daily_summary

# Add tasks with natural language
add_task("Review PR for auth service", due="tomorrow", tags=["work"])
add_task("Buy birthday gift for Sowmya", due="next friday", priority="high")
add_task("Call dentist")  # Priority auto-inferred as low

# List tasks
list_tasks()                    # All pending tasks
list_tasks(tag="work")          # Work tasks only
list_tasks(due_today=True)      # Due today
list_tasks(overdue=True)        # Past due

# Complete a task
complete_task("PR review")      # Partial title match works

# Daily summary
summary = daily_summary()
print(summary["summary"])
# ⚠️ 1 overdue task(s)
# 📅 2 task(s) due today
```

## API Reference

### add_task(title, due?, priority?, tags?, notes?)

Add a new task.

```python
add_task(
    "Submit quarterly report",
    due="end of week",           # Natural language date
    priority="high",             # high, medium, low (or auto-inferred)
    tags=["work", "finance"],    # Context tags
    notes="Include Q4 metrics"   # Additional notes
)
```

### list_tasks(status?, priority?, tag?, due_today?, overdue?)

List tasks with optional filters.

```python
list_tasks()                        # All pending
list_tasks(status="completed")      # Completed tasks
list_tasks(priority="high")         # High priority only
list_tasks(tag="work")              # By tag
list_tasks(due_today=True)          # Due today
list_tasks(overdue=True)            # Past due
list_tasks(include_completed=True)  # Include completed
```

### complete_task(task_id)

Mark a task as done. Accepts task ID or partial title match.

```python
complete_task("task_abc123")  # By ID
complete_task("quarterly")    # By title match
```

### delete_task(task_id, archive=True)

Delete (archive) a task.

```python
delete_task("task_abc123")              # Archive (recoverable)
delete_task("task_abc123", archive=False)  # Permanent delete
```

### update_task(task_id, title?, due?, priority?, tags?, notes?)

Update an existing task.

```python
update_task("task_abc123", priority="high", due="tomorrow")
```

### daily_summary(date?)

Get a summary for a specific day.

```python
summary = daily_summary()           # Today
summary = daily_summary("2026-01-16")  # Specific date

# Returns:
{
    "date": "2026-01-15",
    "due_today": [...],
    "overdue": [...],
    "completed_today": [...],
    "high_priority": [...],
    "summary": "📅 2 task(s) due today\n✅ 1 completed today"
}
```

### search_tasks(query)

Search by title, notes, or tags.

```python
search_tasks("report")  # Matches title or notes
search_tasks("work")    # Matches tag
```

## Date Parsing

Tasky understands natural language dates:

| Input | Result |
|-------|--------|
| `today` | Today |
| `tomorrow` | Tomorrow |
| `in 3 days` | 3 days from now |
| `next monday` | Next week's Monday |
| `friday` | This coming Friday |
| `end of week` / `eow` | Friday |
| `end of month` / `eom` | Last day of month |
| `in 2 weeks` | 2 weeks from now |
| `2026-01-20` | Specific date (ISO) |

## Priority Inference

If you don't specify priority, Tasky infers it:

| Signal | Priority |
|--------|----------|
| "URGENT", "ASAP", "critical" in title | High |
| Due today or overdue | High |
| "urgent" or "important" tag | High |
| Due within 2 days | Medium |
| "work", "meeting" tag | Medium |
| "review", "follow up" in title | Medium |
| No urgency signals | Low |

## Data Storage

Tasks are stored in `data/tasks.json`:

```json
[
  {
    "id": "task_abc123",
    "title": "Review PR",
    "status": "pending",
    "priority": "high",
    "due": "2026-01-16",
    "tags": ["work"],
    "notes": null,
    "created_at": "2026-01-15T10:00:00Z",
    "completed_at": null
  }
]
```

## Testing

```bash
pip install pytest
pytest tests/ -v
```

## For LLM Agents

Tasky is designed for conversational interfaces. Example integration:

```python
# User: "Add a task to review the PR by tomorrow"
from src import add_task
task = add_task("Review PR", due="tomorrow", tags=["work"])
response = f"Added: {task['title']} (due {task['due']}, {task['priority']} priority)"

# User: "What's on my plate today?"
from src import daily_summary
summary = daily_summary()
response = summary["summary"]

# User: "Done with the PR review"
from src import complete_task
task = complete_task("PR review")
response = f"Completed: {task['title']}" if task else "Task not found"
```

## License

MIT

## Author

Built for [Siddhant Jain](https://github.com/siddhantjain) by Neo 🐙
