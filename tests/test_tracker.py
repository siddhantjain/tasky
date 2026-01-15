"""
Tests for the task tracker.
"""

import pytest
import json
import os
from datetime import date, timedelta
from pathlib import Path

# Set up test data directory before importing
TEST_DATA_DIR = Path(__file__).parent / "test_data"


@pytest.fixture(autouse=True)
def setup_test_data(monkeypatch, tmp_path):
    """Use temporary directory for test data."""
    import src.tracker as tracker
    
    test_tasks_file = tmp_path / "tasks.json"
    monkeypatch.setattr(tracker, "DATA_DIR", tmp_path)
    monkeypatch.setattr(tracker, "TASKS_FILE", test_tasks_file)
    
    yield
    
    # Cleanup
    if test_tasks_file.exists():
        test_tasks_file.unlink()


class TestAddTask:
    """Tests for add_task function."""
    
    def test_add_simple_task(self):
        from src.tracker import add_task, list_tasks
        
        task = add_task("Buy groceries")
        
        assert task["title"] == "Buy groceries"
        assert task["status"] == "pending"
        assert task["id"].startswith("task_")
        assert "created_at" in task
        
        tasks = list_tasks()
        assert len(tasks) == 1
    
    def test_add_task_with_due_date(self):
        from src.tracker import add_task
        
        task = add_task("Submit report", due="tomorrow")
        
        expected_due = (date.today() + timedelta(days=1)).isoformat()
        assert task["due"] == expected_due
    
    def test_add_task_with_priority(self):
        from src.tracker import add_task
        
        task = add_task("Fix bug", priority="high")
        
        assert task["priority"] == "high"
    
    def test_add_task_with_tags(self):
        from src.tracker import add_task
        
        task = add_task("Code review", tags=["work", "dev"])
        
        assert task["tags"] == ["work", "dev"]
    
    def test_add_task_infers_priority(self):
        from src.tracker import add_task
        
        task = add_task("URGENT: Fix production issue")
        
        assert task["priority"] == "high"
    
    def test_add_task_with_notes(self):
        from src.tracker import add_task
        
        task = add_task("Call doctor", notes="Ask about prescription")
        
        assert task["notes"] == "Ask about prescription"


class TestListTasks:
    """Tests for list_tasks function."""
    
    def test_list_empty(self):
        from src.tracker import list_tasks
        
        tasks = list_tasks()
        assert tasks == []
    
    def test_list_filters_by_status(self):
        from src.tracker import add_task, complete_task, list_tasks
        
        add_task("Task 1")
        task2 = add_task("Task 2")
        complete_task(task2["id"])
        
        pending = list_tasks(status="pending")
        completed = list_tasks(status="completed")
        
        assert len(pending) == 1
        assert len(completed) == 1
    
    def test_list_filters_by_tag(self):
        from src.tracker import add_task, list_tasks
        
        add_task("Work task", tags=["work"])
        add_task("Personal task", tags=["personal"])
        
        work_tasks = list_tasks(tag="work")
        
        assert len(work_tasks) == 1
        assert work_tasks[0]["title"] == "Work task"
    
    def test_list_filters_by_priority(self):
        from src.tracker import add_task, list_tasks
        
        add_task("High priority", priority="high")
        add_task("Low priority", priority="low")
        
        high = list_tasks(priority="high")
        
        assert len(high) == 1
        assert high[0]["priority"] == "high"
    
    def test_list_due_today(self):
        from src.tracker import add_task, list_tasks
        
        add_task("Due today", due="today")
        add_task("Due tomorrow", due="tomorrow")
        
        today_tasks = list_tasks(due_today=True)
        
        assert len(today_tasks) == 1
        assert today_tasks[0]["title"] == "Due today"
    
    def test_list_sorted_by_priority(self):
        from src.tracker import add_task, list_tasks
        
        add_task("Low", priority="low")
        add_task("High", priority="high")
        add_task("Medium", priority="medium")
        
        tasks = list_tasks()
        
        assert tasks[0]["priority"] == "high"
        assert tasks[1]["priority"] == "medium"
        assert tasks[2]["priority"] == "low"


class TestCompleteTask:
    """Tests for complete_task function."""
    
    def test_complete_by_id(self):
        from src.tracker import add_task, complete_task, get_task
        
        task = add_task("Test task")
        result = complete_task(task["id"])
        
        assert result["status"] == "completed"
        assert result["completed_at"] is not None
        
        updated = get_task(task["id"])
        assert updated["status"] == "completed"
    
    def test_complete_by_title_match(self):
        from src.tracker import add_task, complete_task
        
        add_task("Buy groceries from store")
        result = complete_task("groceries")
        
        assert result is not None
        assert result["status"] == "completed"
    
    def test_complete_nonexistent(self):
        from src.tracker import complete_task
        
        result = complete_task("nonexistent_task")
        
        assert result is None


class TestDeleteTask:
    """Tests for delete_task function."""
    
    def test_delete_archives_by_default(self):
        from src.tracker import add_task, delete_task, get_task
        
        task = add_task("Test task")
        delete_task(task["id"])
        
        updated = get_task(task["id"])
        assert updated["status"] == "archived"
    
    def test_delete_permanently(self):
        from src.tracker import add_task, delete_task, get_task
        
        task = add_task("Test task")
        delete_task(task["id"], archive=False)
        
        assert get_task(task["id"]) is None


class TestUpdateTask:
    """Tests for update_task function."""
    
    def test_update_title(self):
        from src.tracker import add_task, update_task
        
        task = add_task("Old title")
        updated = update_task(task["id"], title="New title")
        
        assert updated["title"] == "New title"
    
    def test_update_priority(self):
        from src.tracker import add_task, update_task
        
        task = add_task("Test", priority="low")
        updated = update_task(task["id"], priority="high")
        
        assert updated["priority"] == "high"
    
    def test_update_tags(self):
        from src.tracker import add_task, update_task
        
        task = add_task("Test", tags=["old"])
        updated = update_task(task["id"], tags=["new", "tags"])
        
        assert updated["tags"] == ["new", "tags"]


class TestDailySummary:
    """Tests for daily_summary function."""
    
    def test_summary_empty(self):
        from src.tracker import daily_summary
        
        summary = daily_summary()
        
        assert summary["due_today"] == []
        assert summary["overdue"] == []
        assert "No tasks" in summary["summary"]
    
    def test_summary_with_due_today(self):
        from src.tracker import add_task, daily_summary
        
        add_task("Due today", due="today")
        summary = daily_summary()
        
        assert len(summary["due_today"]) == 1
        assert "1 task(s) due today" in summary["summary"]
    
    def test_summary_with_overdue(self):
        from src.tracker import add_task, daily_summary, _load_tasks, _save_tasks
        
        # Manually create an overdue task
        task = add_task("Overdue task")
        tasks = _load_tasks()
        tasks[0]["due"] = (date.today() - timedelta(days=1)).isoformat()
        _save_tasks(tasks)
        
        summary = daily_summary()
        
        assert len(summary["overdue"]) == 1
        assert "overdue" in summary["summary"]


class TestSearchTasks:
    """Tests for search_tasks function."""
    
    def test_search_by_title(self):
        from src.tracker import add_task, search_tasks
        
        add_task("Buy groceries")
        add_task("Call mom")
        
        results = search_tasks("groceries")
        
        assert len(results) == 1
        assert results[0]["title"] == "Buy groceries"
    
    def test_search_by_tag(self):
        from src.tracker import add_task, search_tasks
        
        add_task("Work meeting", tags=["work"])
        add_task("Personal errand")
        
        results = search_tasks("work")
        
        assert len(results) == 1
    
    def test_search_case_insensitive(self):
        from src.tracker import add_task, search_tasks
        
        add_task("IMPORTANT Task")
        
        results = search_tasks("important")
        
        assert len(results) == 1
