"""Utility functions for the Cannabis Stash Tracker Bot."""

from datetime import datetime, timezone
from typing import Optional
import pytz

def format_timestamp(dt: datetime, user_timezone: str = "UTC") -> str:
    """Format a datetime for display with user timezone."""
    try:
        tz = pytz.timezone(user_timezone)
        local_dt = dt.astimezone(tz)
        return local_dt.strftime("%m/%d/%Y %I:%M %p %Z")
    except:
        # Fallback to UTC if timezone is invalid
        return dt.strftime("%m/%d/%Y %I:%M %p UTC")

def get_user_timezone_datetime(user_timezone: str = "UTC") -> datetime:
    """Get current datetime in user's timezone."""
    try:
        tz = pytz.timezone(user_timezone)
        return datetime.now(tz)
    except:
        # Fallback to UTC
        return datetime.now(timezone.utc)

def validate_thc_percentage(value: Optional[float]) -> bool:
    """Validate THC percentage is within reasonable bounds."""
    if value is None:
        return True
    return 0 <= value <= 100

def validate_effect_rating(value: Optional[int]) -> bool:
    """Validate effect rating is within bounds."""
    if value is None:
        return True
    return 1 <= value <= 5

def sanitize_strain_name(strain: Optional[str]) -> Optional[str]:
    """Clean up strain name for consistency."""
    if not strain:
        return None
    
    # Remove extra whitespace and convert to title case
    cleaned = strain.strip().title()
    
    # Return None if empty after cleaning
    return cleaned if cleaned else None

def format_amount_with_unit(amount: float, product_type: str) -> str:
    """Format amount with appropriate unit based on product type."""
    if product_type in ["edible", "tincture", "capsule"]:
        unit = "mg"
    else:
        unit = "g"
    
    # Format to remove unnecessary decimal places
    if amount == int(amount):
        return f"{int(amount)}{unit}"
    else:
        return f"{amount:.2f}".rstrip('0').rstrip('.') + unit

def calculate_tolerance_trend(consumption_history: list) -> str:
    """Analyze consumption history for tolerance trends."""
    if len(consumption_history) < 7:
        return "Not enough data for analysis"
    
    # Simple trend analysis based on weekly averages
    recent_week = consumption_history[:7]
    previous_week = consumption_history[7:14] if len(consumption_history) >= 14 else []
    
    if not previous_week:
        return "Need more history for trend analysis"
    
    recent_avg = sum(entry.absorbed_thc_mg for entry in recent_week) / len(recent_week)
    previous_avg = sum(entry.absorbed_thc_mg for entry in previous_week) / len(previous_week)
    
    if recent_avg > previous_avg * 1.2:
        return "📈 Increasing consumption trend - consider tolerance break"
    elif recent_avg < previous_avg * 0.8:
        return "📉 Decreasing consumption trend"
    else:
        return "➡️ Stable consumption pattern"

def get_emoji_for_method(method: str) -> str:
    """Get emoji representation for consumption method."""
    emoji_map = {
        "smoke": "🚬",
        "vaporizer": "💨", 
        "dab": "🔥",
        "edible": "🍪",
        "tincture": "💧",
        "capsule": "💊"
    }
    return emoji_map.get(method, "🌿")

def get_emoji_for_product_type(product_type: str) -> str:
    """Get emoji representation for product type."""
    emoji_map = {
        "flower": "🌸",
        "dab": "🥄",
        "edible": "🍪", 
        "tincture": "💧",
        "cart": "🖤",
        "capsule": "💊",
        "other": "📦"
    }
    return emoji_map.get(product_type, "🌿")
