"""
Natural language parsing for dates and priority inference.
"""

import re
from datetime import date, timedelta
from typing import Optional, List


def parse_due_date(text: str) -> Optional[date]:
    """
    Parse natural language date into a date object.
    
    Supports:
        - ISO format: "2026-01-15"
        - Relative: "today", "tomorrow", "yesterday"
        - Days of week: "monday", "next tuesday", "this friday"
        - Relative weeks: "next week", "in 2 weeks"
        - Relative days: "in 3 days", "in a week"
        - Named: "end of week", "end of month"
    
    Args:
        text: Natural language date string
    
    Returns:
        date object, or None if unparseable
    
    Examples:
        >>> parse_due_date("tomorrow")
        >>> parse_due_date("next monday")
        >>> parse_due_date("in 3 days")
        >>> parse_due_date("2026-01-20")
    """
    text = text.lower().strip()
    today = date.today()
    
    # ISO format (YYYY-MM-DD)
    iso_match = re.match(r"^\d{4}-\d{2}-\d{2}$", text)
    if iso_match:
        try:
            return date.fromisoformat(text)
        except ValueError:
            pass
    
    # Relative days
    if text == "today":
        return today
    
    if text == "tomorrow":
        return today + timedelta(days=1)
    
    if text == "yesterday":
        return today - timedelta(days=1)
    
    # "in X days"
    in_days_match = re.match(r"in (\d+) days?", text)
    if in_days_match:
        days = int(in_days_match.group(1))
        return today + timedelta(days=days)
    
    # "in a week" / "in X weeks"
    in_weeks_match = re.match(r"in (?:a|(\d+)) weeks?", text)
    if in_weeks_match:
        weeks = int(in_weeks_match.group(1) or 1)
        return today + timedelta(weeks=weeks)
    
    # "next week" (next Monday)
    if text == "next week":
        days_until_monday = (7 - today.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        return today + timedelta(days=days_until_monday)
    
    # "end of week" (Friday)
    if text in ("end of week", "eow"):
        days_until_friday = (4 - today.weekday()) % 7
        if days_until_friday == 0 and today.weekday() == 4:
            return today  # Already Friday
        if days_until_friday <= 0:
            days_until_friday += 7
        return today + timedelta(days=days_until_friday)
    
    # "end of month" / "eom"
    if text in ("end of month", "eom"):
        # Last day of current month
        if today.month == 12:
            next_month = date(today.year + 1, 1, 1)
        else:
            next_month = date(today.year, today.month + 1, 1)
        return next_month - timedelta(days=1)
    
    # "end of day" / "eod" (today)
    if text in ("end of day", "eod"):
        return today
    
    # Day of week parsing
    days_of_week = {
        "monday": 0, "mon": 0,
        "tuesday": 1, "tue": 1, "tues": 1,
        "wednesday": 2, "wed": 2,
        "thursday": 3, "thu": 3, "thur": 3, "thurs": 3,
        "friday": 4, "fri": 4,
        "saturday": 5, "sat": 5,
        "sunday": 6, "sun": 6,
    }
    
    # "next monday", "this friday", "tuesday"
    for day_name, day_num in days_of_week.items():
        if day_name in text:
            # Calculate days until that day
            days_ahead = day_num - today.weekday()
            
            if "next" in text:
                # Always next week
                if days_ahead <= 0:
                    days_ahead += 7
                days_ahead += 7  # Push to next week
            elif "this" in text:
                # This week (could be in past)
                if days_ahead < 0:
                    days_ahead += 7
            else:
                # Default: next occurrence
                if days_ahead <= 0:
                    days_ahead += 7
            
            return today + timedelta(days=days_ahead)
    
    # Couldn't parse
    return None


def infer_priority(
    title: str,
    due_date: Optional[date] = None,
    tags: Optional[List[str]] = None,
) -> str:
    """
    Infer task priority from context.
    
    Considers:
        - Urgency keywords in title
        - Due date proximity
        - Tags like "urgent" or "important"
    
    Args:
        title: Task title
        due_date: Due date if set
        tags: Task tags
    
    Returns:
        "high", "medium", or "low"
    
    Examples:
        >>> infer_priority("URGENT: Fix production bug")  # high
        >>> infer_priority("Buy groceries", due_date=date.today())  # high (due today)
        >>> infer_priority("Research new laptop")  # low (no urgency)
    """
    title_lower = title.lower()
    tags_lower = [t.lower() for t in (tags or [])]
    today = date.today()
    
    # High priority signals
    high_keywords = [
        "urgent", "asap", "critical", "emergency", "important",
        "deadline", "must", "blocker", "p0", "p1"
    ]
    
    for keyword in high_keywords:
        if keyword in title_lower:
            return "high"
        if keyword in tags_lower:
            return "high"
    
    # Due date proximity
    if due_date:
        days_until = (due_date - today).days
        
        if days_until < 0:  # Overdue
            return "high"
        elif days_until == 0:  # Due today
            return "high"
        elif days_until <= 2:  # Due very soon
            return "medium"
        elif days_until <= 7:  # Due this week
            return "medium"
    
    # Medium priority signals
    medium_keywords = ["soon", "this week", "review", "follow up", "check"]
    
    for keyword in medium_keywords:
        if keyword in title_lower:
            return "medium"
    
    # Work-related tags often medium priority
    work_tags = ["work", "job", "meeting", "project"]
    for tag in work_tags:
        if tag in tags_lower:
            return "medium"
    
    # Default to low
    return "low"
