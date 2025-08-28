"""Stash management service."""

from typing import List, Optional, Tuple
from bot.database.models import StashItem, User
from bot.config import PRODUCT_TYPES

class StashService:
    """Service for managing user stash inventory."""

    @staticmethod
    async def get_user_stash(user_id: int) -> List[StashItem]:
        """Get all stash items for a user."""
        return await StashItem.get_user_stash(user_id)

    @staticmethod
    async def get_stash_items(user_id: int) -> List[StashItem]:
        """Get all stash items for a user (alias for compatibility)."""
        return await StashItem.get_user_stash(user_id)

    @staticmethod
    async def add_to_stash(
        user_id: int, 
        product_type: str, 
        amount: float, 
        strain: Optional[str] = None,
        thc_percent: Optional[float] = None,
        notes: Optional[str] = None
    ) -> StashItem:
        """Add or update stash item."""
        # Validate product type
        if product_type not in PRODUCT_TYPES:
            raise ValueError(f"Invalid product type. Must be one of: {', '.join(PRODUCT_TYPES)}")

        # Get existing stash item or create new one
        existing = await StashItem.get_by_type_and_strain(user_id, product_type, strain)
        
        if existing:
            # Update existing item
            existing.amount += amount
            if thc_percent is not None:
                existing.thc_percent = thc_percent
            if notes:
                existing.notes = notes
            await existing.save()
            return existing
        else:
            # Create new item
            stash_item = StashItem(
                user_id=user_id,
                type=product_type,
                strain=strain,
                amount=amount,
                thc_percent=thc_percent,
                notes=notes
            )
            await stash_item.save()
            return stash_item

    @staticmethod
    async def remove_from_stash(
        user_id: int, 
        product_type: str, 
        amount: float, 
        strain: Optional[str] = None
    ) -> Tuple[bool, str]:
        """Remove amount from stash. Returns (success, message)."""
        stash_item = await StashItem.get_by_type_and_strain(user_id, product_type, strain)
        
        if not stash_item:
            strain_text = f" ({strain})" if strain else ""
            return False, f"No {product_type}{strain_text} found in stash"
        
        if stash_item.amount < amount:
            return False, f"Not enough {product_type} in stash. Available: {stash_item.amount}g"
        
        stash_item.amount -= amount
        
        if stash_item.amount <= 0:
            await stash_item.delete()
            return True, f"Removed {amount}g of {product_type}. Item deleted (empty)."
        else:
            await stash_item.save()
            return True, f"Removed {amount}g of {product_type}. Remaining: {stash_item.amount}g"

    @staticmethod
    async def set_stash_amount(
        user_id: int, 
        product_type: str, 
        amount: float, 
        strain: Optional[str] = None,
        thc_percent: Optional[float] = None
    ) -> StashItem:
        """Set exact stash amount."""
        stash_item = await StashItem.get_by_type_and_strain(user_id, product_type, strain)
        
        if stash_item:
            stash_item.amount = amount
            if thc_percent is not None:
                stash_item.thc_percent = thc_percent
            await stash_item.save()
        else:
            stash_item = StashItem(
                user_id=user_id,
                type=product_type,
                strain=strain,
                amount=amount,
                thc_percent=thc_percent
            )
            await stash_item.save()
        
        return stash_item

    @staticmethod
    async def check_low_stash_alerts(user_id: int) -> List[str]:
        """Check for low stash alerts and return warning messages."""
        from bot.database.models import Alert
        
        alerts = await Alert.get_user_alerts(user_id)
        stash_items = await StashItem.get_user_stash(user_id)
        warnings = []
        
        for alert in alerts:
            if alert.alert_type == "low_stash" and alert.target_type:
                # Find matching stash items
                matching_items = [
                    item for item in stash_items 
                    if item.type == alert.target_type
                ]
                
                total_amount = sum(item.amount for item in matching_items)
                
                if total_amount <= (alert.threshold or 0):
                    warnings.append(
                        alert.message or 
                        f"⚠️ Low {alert.target_type}: {total_amount}g remaining"
                    )
        
        return warnings

    @staticmethod
    def format_stash_display(stash_items: List[StashItem]) -> str:
        """Format stash items for display."""
        if not stash_items:
            return "Your stash is empty! Use `/stash add` to add items."
        
        display_text = "🏪 **Your Current Stash:**\n\n"
        
        # Group by type
        by_type = {}
        for item in stash_items:
            if item.type not in by_type:
                by_type[item.type] = []
            by_type[item.type].append(item)
        
        for product_type, items in by_type.items():
            display_text += f"**{product_type.title()}:**\n"
            
            for item in items:
                strain_text = f" ({item.strain})" if item.strain else ""
                thc_text = f" - {item.thc_percent}% THC" if item.thc_percent else ""
                
                if product_type in ["edible", "tincture", "capsule"]:
                    unit = "mg"
                else:
                    unit = "g"
                
                display_text += f"  • {item.amount}{unit}{strain_text}{thc_text}\n"
            
            display_text += "\n"
        
        return display_text.strip()
