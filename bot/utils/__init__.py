"""Utility functions for the bot."""

import re
from datetime import datetime, timezone
from typing import Optional

def validate_strain_name(strain: str) -> bool:
    """Validate strain name format."""
    if not strain or len(strain.strip()) == 0:
        return False
    
    if len(strain) > 100:  # Reasonable limit
        return False
    
    # Allow letters, numbers, spaces, and common punctuation
    pattern = r'^[a-zA-Z0-9\s\-_#.\'\"]+$'
    return bool(re.match(pattern, strain.strip()))

def format_duration(seconds: int) -> str:
    """Format seconds into human-readable duration."""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes}m"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        if minutes > 0:
            return f"{hours}h {minutes}m"
        return f"{hours}h"

def format_timestamp(dt: datetime, format_type: str = "relative") -> str:
    """Format datetime for display."""
    if not dt:
        return "Unknown"
    
    # Ensure timezone aware
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    now = datetime.now(timezone.utc)
    diff = now - dt
    
    if format_type == "relative":
        if diff.days > 7:
            return dt.strftime("%m/%d/%Y")
        elif diff.days > 0:
            return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        else:
            return "Just now"
    elif format_type == "short":
        return dt.strftime("%m/%d %I:%M %p")
    elif format_type == "full":
        return dt.strftime("%Y-%m-%d %I:%M:%S %p")
    else:
        return str(dt)

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to maximum length."""
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers, returning default if denominator is zero."""
    if denominator == 0:
        return default
    return numerator / denominator

def parse_amount(amount_str: str) -> Optional[float]:
    """Parse amount string to float, handling common formats."""
    if not amount_str:
        return None
    
    # Remove common characters and convert to lowercase
    cleaned = amount_str.lower().strip()
    cleaned = re.sub(r'[^0-9.]', '', cleaned)
    
    try:
        return float(cleaned)
    except ValueError:
        return None

def validate_thc_percentage(thc_percent: float) -> bool:
    """Validate THC percentage is within reasonable bounds."""
    return 0 <= thc_percent <= 100

def format_amount_with_unit(amount: float, product_type: str) -> str:
    """Format amount with appropriate unit based on product type."""
    if product_type in ["edible", "tincture", "capsule"]:
        return f"{amount}mg"
    else:
        return f"{amount}g"

def calculate_percentage_change(old_value: float, new_value: float) -> float:
    """Calculate percentage change between two values."""
    if old_value == 0:
        return 0.0 if new_value == 0 else 100.0
    
    return ((new_value - old_value) / old_value) * 100
