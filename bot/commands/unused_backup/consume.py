"""Consolidated consumption command replacing all individual method commands."""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
import logging
from datetime import datetime

from bot.services.consumption_service import ConsumptionService
from bot.services.stash_service import StashService
from bot.config import BIOAVAILABILITY_RATES

logger = logging.getLogger(__name__)

class ConsumeCommands(commands.Cog):
    """Unified consumption logging commands."""
    
    def __init__(self, bot):
        self.bot = bot
    
    async def strain_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        """Autocomplete for strain names from user's stash."""
        try:
            user_id = interaction.user.id
            stash_items = await StashService.get_stash_items(user_id)
            
            # Filter strains that match current input
            matching_strains = [
                item.strain for item in stash_items 
                if item.strain and current.lower() in item.strain.lower()
            ]
            
            # Remove duplicates and limit to 25 (Discord limit)
            unique_strains = list(set(matching_strains))[:25]
            
            return [
                app_commands.Choice(name=strain, value=strain)
                for strain in unique_strains
            ]
        except Exception:
            return []
    
    def _get_product_type_from_method(self, method: str) -> str:
        """Map consumption method to product type."""
        method_to_product = {
            'smoke': 'flower',
            'vaporizer': 'flower', 
            'dab': 'concentrate',
            'edible': 'edible',
            'tincture': 'tincture',
            'capsule': 'capsule'
        }
        return method_to_product.get(method, 'flower')
    
    @app_commands.command(name="consume", description="Log cannabis consumption (any method)")
    @app_commands.describe(
        method="Consumption method",
        amount="Amount consumed (grams for flower/concentrates, mg for edibles/tinctures)",
        strain="Strain name (optional - autocompletes from your stash)",
        thc_percent="THC percentage (optional - auto-filled from stash if available)",
        notes="Additional notes about the session",
        effect_rating="Rate the effects 1-5 (optional)"
    )
    @app_commands.choices(method=[
        app_commands.Choice(name="💨 Smoking", value="smoke"),
        app_commands.Choice(name="💨 Vaporizer", value="vaporizer"), 
        app_commands.Choice(name="🔥 Dabbing", value="dab"),
        app_commands.Choice(name="🍪 Edible", value="edible"),
        app_commands.Choice(name="💧 Tincture", value="tincture"),
        app_commands.Choice(name="💊 Capsule", value="capsule")
    ])
    @app_commands.autocomplete(strain=strain_autocomplete)
    async def consume(
        self,
        interaction: discord.Interaction,
        method: app_commands.Choice[str],
        amount: float,
        strain: Optional[str] = None,
        thc_percent: Optional[float] = None,
        notes: Optional[str] = None,
        effect_rating: Optional[int] = None
    ):
        """Universal consumption logging command with smart validation."""
        try:
            # Validate inputs
            if amount <= 0:
                await interaction.response.send_message(
                    "❌ **Invalid Amount**\nAmount must be positive.\n\n" +
                    "💡 **Examples:**\n" +
                    "• Flower/Concentrates: Use grams (0.1, 0.5, 1.0)\n" +
                    "• Edibles/Tinctures: Use mg THC (5, 10, 25)",
                    ephemeral=True
                )
                return

            if thc_percent is not None and (thc_percent < 0 or thc_percent > 100):
                await interaction.response.send_message(
                    "❌ **Invalid THC Percentage**\nTHC percentage must be between 0 and 100.\n\n" +
                    "💡 **Typical ranges:**\n" +
                    "• Low: 5-15% • Medium: 15-25% • High: 25%+",
                    ephemeral=True
                )
                return

            if effect_rating is not None and (effect_rating < 1 or effect_rating > 5):
                await interaction.response.send_message(
                    "❌ **Invalid Effect Rating**\nEffect rating must be between 1 and 5 stars.\n\n" +
                    "⭐ **Rating scale:**\n" +
                    "1⭐ Poor • 2⭐ Fair • 3⭐ Good • 4⭐ Great • 5⭐ Excellent",
                    ephemeral=True
                )
                return
            
            user_id = interaction.user.id
            consumption_method = method.value
            product_type = self._get_product_type_from_method(consumption_method)
            
            # Auto-fetch THC percentage from stash if strain is provided but THC% is not
            auto_thc_message = ""
            if strain and thc_percent is None:
                try:
                    stash_items = await StashService.get_stash_items(user_id)
                    # Find matching strain in stash (case-insensitive)
                    matching_item = next(
                        (item for item in stash_items 
                         if item.strain and item.strain.lower() == strain.lower() and item.thc_percent),
                        None
                    )
                    if matching_item:
                        thc_percent = matching_item.thc_percent
                        auto_thc_message = f" (THC: {thc_percent}% from stash)"
                except Exception:
                    # If there's any error fetching from stash, just continue without auto-fill
                    pass
            
            # Log the consumption
            entry, warnings = await ConsumptionService.log_consumption(
                user_id=user_id,
                product_type=product_type,
                amount=amount,
                method=consumption_method,
                strain=strain,
                thc_percent=thc_percent,
                notes=notes,
                effect_rating=effect_rating
            )
            
            # Create success embed
            embed = discord.Embed(
                title=f"✅ {method.name} Session Logged! 🌿",
                color=0x4CAF50,
                timestamp=datetime.utcnow()
            )
            
            # Format the entry details
            strain_text = f" ({strain}{auto_thc_message})" if strain else ""
            unit = "mg" if product_type in ["edible", "tincture", "capsule"] else "g"
            
            embed.add_field(
                name="📊 Session Details",
                value=f"**Method:** {method.name}\n" +
                      f"**Amount:** {amount}{unit} {product_type}{strain_text}\n" +
                      f"**THC Absorbed:** {entry.absorbed_thc_mg}mg",
                inline=False
            )
            
            if entry.thc_percent:
                embed.add_field(
                    name="🌿 THC Content",
                    value=f"{entry.thc_percent}%",
                    inline=True
                )
            
            if effect_rating:
                stars = "⭐" * effect_rating
                embed.add_field(
                    name="� Effect Rating",
                    value=f"{stars} {effect_rating}/5",
                    inline=True
                )
            
            # Show bioavailability info
            bioavailability = BIOAVAILABILITY_RATES.get(consumption_method, 0) * 100
            embed.add_field(
                name="🧠 Bioavailability",
                value=f"{bioavailability:.0f}%",
                inline=True
            )
            
            if notes:
                embed.add_field(
                    name="� Notes",
                    value=notes[:100] + ("..." if len(notes) > 100 else ""),
                    inline=False
                )
            
            # Show warnings if any
            if warnings:
                embed.add_field(
                    name="⚠️ Warnings",
                    value="\n".join(warnings),
                    inline=False
                )
            
            embed.set_footer(text=f"Session ID: #{entry.id} • Use /dashboard to view trends")
            await interaction.response.send_message(embed=embed)
                
        except Exception as e:
            logger.error(f"Error in consume command: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while logging consumption. Please try again.",
                ephemeral=True
            )

async def setup(bot):
    """Setup the cog."""
    await bot.add_cog(ConsumeCommands(bot))
