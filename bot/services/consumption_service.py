"""Consumption tracking service."""

from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from bot.database.models import ConsumptionEntry, StashItem, User
from bot.config import BIOAVAILABILITY_RATES
from bot.services.stash_service import StashService

class ConsumptionService:
    """Service for tracking cannabis consumption."""

    @staticmethod
    def calculate_absorbed_thc(
        amount: float, 
        thc_percent: float, 
        method: str
    ) -> float:
        """Calculate absorbed THC in mg based on consumption method."""
        if method not in BIOAVAILABILITY_RATES:
            raise ValueError(f"Unknown consumption method: {method}")
        
        # Convert amount to mg THC, then apply bioavailability
        thc_mg = amount * (thc_percent / 100) * 1000  # grams to mg
        bioavailability = BIOAVAILABILITY_RATES[method]
        absorbed_mg = thc_mg * bioavailability
        
        return round(absorbed_mg, 2)

    @staticmethod
    async def log_consumption(
        user_id: int,
        product_type: str,
        amount: float,
        method: str,
        strain: Optional[str] = None,
        thc_percent: Optional[float] = None,
        notes: Optional[str] = None,
        symptom: Optional[str] = None,
        effect_rating: Optional[int] = None,
        auto_deduct_stash: bool = True
    ) -> Tuple[ConsumptionEntry, List[str]]:
        """Log a consumption session."""
        warnings = []
        
        # Ensure user exists
        await User.get_or_create(user_id)
        
        # Try to get THC percentage from stash if not provided
        if thc_percent is None and strain:
            stash_item = await StashItem.get_by_type_and_strain(user_id, product_type, strain)
            if stash_item and stash_item.thc_percent:
                thc_percent = stash_item.thc_percent
        
        # Default THC percentage if still not available
        if thc_percent is None:
            thc_percent = 20.0  # Default assumption
            warnings.append(f"⚠️ THC percentage not specified, assuming {thc_percent}%")
        
        # Calculate absorbed THC
        absorbed_thc = ConsumptionService.calculate_absorbed_thc(
            amount, thc_percent, method
        )
        
        # Create consumption entry
        entry = await ConsumptionEntry.create(
            user_id=user_id,
            type=product_type,
            strain=strain,
            amount=amount,
            thc_percent=thc_percent,
            method=method,
            absorbed_thc_mg=absorbed_thc,
            notes=notes,
            symptom=symptom,
            effect_rating=effect_rating
        )
        
        # Auto-deduct from stash if enabled
        if auto_deduct_stash:
            success, message = await StashService.remove_from_stash(
                user_id, product_type, amount, strain
            )
            if not success:
                warnings.append(f"⚠️ Could not deduct from stash: {message}")
        
        # Check daily limits
        daily_limit_warning = await ConsumptionService.check_daily_limit(user_id)
        if daily_limit_warning:
            warnings.append(daily_limit_warning)
        
        # Check for low stash alerts
        stash_warnings = await StashService.check_low_stash_alerts(user_id)
        warnings.extend(stash_warnings)
        
        return entry, warnings

    @staticmethod
    async def check_daily_limit(user_id: int) -> Optional[str]:
        """Check if user has exceeded their daily THC limit."""
        user = await User.get(user_id)
        if not user or not user.max_daily_thc_mg:
            return None
        
        # Get today's consumption
        today = datetime.now()
        daily_entries = await ConsumptionEntry.get_daily_consumption(user_id, today)
        
        total_absorbed = sum(entry.absorbed_thc_mg for entry in daily_entries)
        
        if total_absorbed > user.max_daily_thc_mg:
            return f"⚠️ Daily limit exceeded! Consumed: {total_absorbed:.1f}mg / Limit: {user.max_daily_thc_mg}mg"
        elif total_absorbed > user.max_daily_thc_mg * 0.8:  # 80% warning
            remaining = user.max_daily_thc_mg - total_absorbed
            return f"⚠️ Approaching daily limit! Remaining: {remaining:.1f}mg"
        
        return None

    @staticmethod
    async def get_consumption_summary(
        user_id: int, 
        days: int = 1
    ) -> dict:
        """Get consumption summary for specified number of days."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days-1)
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # For now, get recent entries (would need date range query for full implementation)
        entries = await ConsumptionEntry.get_user_consumption(user_id, limit=1000)
        
        # Filter by date range
        filtered_entries = [
            entry for entry in entries 
            if entry.timestamp and entry.timestamp >= start_date
        ]
        
        if not filtered_entries:
            return {
                "total_sessions": 0,
                "total_absorbed_mg": 0,
                "total_amount": 0,
                "average_effect": 0,
                "methods_used": [],
                "strains_used": []
            }
        
        total_sessions = len(filtered_entries)
        total_absorbed = sum(entry.absorbed_thc_mg for entry in filtered_entries)
        total_amount = sum(entry.amount for entry in filtered_entries)
        
        # Calculate average effect rating
        ratings = [entry.effect_rating for entry in filtered_entries if entry.effect_rating]
        average_effect = sum(ratings) / len(ratings) if ratings else 0
        
        # Get unique methods and strains
        methods_used = list(set(entry.method for entry in filtered_entries))
        strains_used = list(set(entry.strain for entry in filtered_entries if entry.strain))
        
        return {
            "total_sessions": total_sessions,
            "total_absorbed_mg": round(total_absorbed, 2),
            "total_amount": round(total_amount, 2),
            "average_effect": round(average_effect, 1),
            "methods_used": methods_used,
            "strains_used": strains_used
        }

    @staticmethod
    def format_consumption_entry(entry: ConsumptionEntry) -> str:
        """Format a consumption entry for display."""
        timestamp = entry.timestamp.strftime("%m/%d %I:%M %p") if entry.timestamp else "Unknown time"
        strain_text = f" ({entry.strain})" if entry.strain else ""
        
        # Determine unit based on type
        if entry.type in ["edible", "tincture", "capsule"]:
            unit = "mg"
        else:
            unit = "g"
        
        display_text = f"**{timestamp}** - {entry.method.title()}\n"
        display_text += f"  📦 {entry.amount}{unit} {entry.type}{strain_text}\n"
        display_text += f"  💊 {entry.absorbed_thc_mg}mg THC absorbed"
        
        if entry.thc_percent:
            display_text += f" ({entry.thc_percent}% THC)"
        
        if entry.effect_rating:
            stars = "⭐" * entry.effect_rating
            display_text += f"\n  {stars} Effect Rating: {entry.effect_rating}/5"
        
        if entry.symptom:
            display_text += f"\n  🏥 Symptom: {entry.symptom}"
        
        if entry.notes:
            display_text += f"\n  📝 Notes: {entry.notes}"
        
        return display_text

    @staticmethod
    def format_consumption_summary(summary: dict, days: int) -> str:
        """Format consumption summary for display."""
        period = "today" if days == 1 else f"past {days} days"
        
        if summary["total_sessions"] == 0:
            return f"📊 **Consumption Summary ({period}):**\nNo consumption recorded."
        
        text = f"📊 **Consumption Summary ({period}):**\n\n"
        text += f"🎯 **Sessions:** {summary['total_sessions']}\n"
        text += f"💊 **Total THC Absorbed:** {summary['total_absorbed_mg']}mg\n"
        text += f"📦 **Total Amount:** {summary['total_amount']}g\n"
        
        if summary["average_effect"] > 0:
            stars = "⭐" * int(summary["average_effect"])
            text += f"{stars} **Average Effect:** {summary['average_effect']}/5\n"
        
        if summary["methods_used"]:
            text += f"🔥 **Methods:** {', '.join(summary['methods_used'])}\n"
        
        if summary["strains_used"]:
            text += f"🌿 **Strains:** {', '.join(summary['strains_used'][:5])}"
            if len(summary["strains_used"]) > 5:
                text += f" (+{len(summary['strains_used']) - 5} more)"
        
        return text
