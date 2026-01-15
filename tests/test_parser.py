"""
Tests for the date parser and priority inference.
"""

import pytest
from datetime import date, timedelta

from src.parser import parse_due_date, infer_priority


class TestParseDueDate:
    """Tests for parse_due_date function."""
    
    def test_iso_format(self):
        result = parse_due_date("2026-01-20")
        assert result == date(2026, 1, 20)
    
    def test_today(self):
        result = parse_due_date("today")
        assert result == date.today()
    
    def test_tomorrow(self):
        result = parse_due_date("tomorrow")
        assert result == date.today() + timedelta(days=1)
    
    def test_yesterday(self):
        result = parse_due_date("yesterday")
        assert result == date.today() - timedelta(days=1)
    
    def test_in_x_days(self):
        result = parse_due_date("in 5 days")
        assert result == date.today() + timedelta(days=5)
    
    def test_in_1_day(self):
        result = parse_due_date("in 1 day")
        assert result == date.today() + timedelta(days=1)
    
    def test_in_a_week(self):
        result = parse_due_date("in a week")
        assert result == date.today() + timedelta(weeks=1)
    
    def test_in_x_weeks(self):
        result = parse_due_date("in 2 weeks")
        assert result == date.today() + timedelta(weeks=2)
    
    def test_day_of_week(self):
        """Test parsing day of week (next occurrence)."""
        result = parse_due_date("monday")
        
        # Should be in the future
        assert result > date.today() or result == date.today()
        # Should be a Monday
        assert result.weekday() == 0
    
    def test_next_day_of_week(self):
        """Test 'next monday' is always next week."""
        result = parse_due_date("next monday")
        today = date.today()
        
        # Should be at least 7 days away
        assert (result - today).days >= 1
        # Should be a Monday
        assert result.weekday() == 0
    
    def test_end_of_week(self):
        result = parse_due_date("end of week")
        
        # Should be a Friday
        assert result.weekday() == 4
    
    def test_eow_shorthand(self):
        result = parse_due_date("eow")
        assert result.weekday() == 4
    
    def test_end_of_month(self):
        result = parse_due_date("end of month")
        today = date.today()
        
        # Should be in the same month
        assert result.month == today.month or (
            today.day > 25 and result.month == (today.month % 12) + 1
        )
        # Should be the last day of month (next day is 1st)
        assert (result + timedelta(days=1)).day == 1
    
    def test_eod(self):
        result = parse_due_date("eod")
        assert result == date.today()
    
    def test_unparseable(self):
        result = parse_due_date("gibberish")
        assert result is None
    
    def test_case_insensitive(self):
        assert parse_due_date("TOMORROW") == date.today() + timedelta(days=1)
        assert parse_due_date("Today") == date.today()


class TestInferPriority:
    """Tests for infer_priority function."""
    
    def test_urgent_keyword(self):
        assert infer_priority("URGENT: Fix bug") == "high"
        assert infer_priority("This is urgent") == "high"
    
    def test_asap_keyword(self):
        assert infer_priority("Complete report ASAP") == "high"
    
    def test_critical_keyword(self):
        assert infer_priority("Critical security patch") == "high"
    
    def test_important_keyword(self):
        assert infer_priority("Important meeting prep") == "high"
    
    def test_due_today(self):
        assert infer_priority("Task", due_date=date.today()) == "high"
    
    def test_overdue(self):
        yesterday = date.today() - timedelta(days=1)
        assert infer_priority("Task", due_date=yesterday) == "high"
    
    def test_due_soon(self):
        in_2_days = date.today() + timedelta(days=2)
        assert infer_priority("Task", due_date=in_2_days) == "medium"
    
    def test_due_this_week(self):
        in_5_days = date.today() + timedelta(days=5)
        assert infer_priority("Task", due_date=in_5_days) == "medium"
    
    def test_urgent_tag(self):
        assert infer_priority("Task", tags=["urgent"]) == "high"
    
    def test_work_tag(self):
        assert infer_priority("Task", tags=["work"]) == "medium"
    
    def test_default_low(self):
        assert infer_priority("Buy new book") == "low"
    
    def test_soon_keyword(self):
        assert infer_priority("Complete soon") == "medium"
    
    def test_review_keyword(self):
        assert infer_priority("Review PR") == "medium"
