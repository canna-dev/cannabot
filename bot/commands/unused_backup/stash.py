"""Stash management commands."""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
import random

from bot.services.stash_service import StashService
from bot.services.strain_database_service import strain_db
from bot.config import PRODUCT_TYPES

class StashCommands(commands.Cog):
    """Stash management slash commands."""
    
    def __init__(self, bot):
        self.bot = bot

    stash_group = app_commands.Group(name="stash", description="Manage your cannabis stash")

    @stash_group.command(name="view", description="View your current stash inventory")
    async def view_stash(self, interaction: discord.Interaction):
        """View current stash."""
        try:
            user_id = interaction.user.id
            stash_items = await StashService.get_user_stash(user_id)
            
            display_text = StashService.format_stash_display(stash_items)
            
            embed = discord.Embed(
                title="🏪 Your Stash",
                description=display_text,
                color=0x4CAF50
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error viewing stash: {str(e)}", 
                ephemeral=True
            )

    @stash_group.command(name="add", description="Add items to your stash")
    @app_commands.describe(
        type="Type of cannabis product",
        amount="Amount to add (grams for flower/concentrates, mg for edibles)",
        strain="Strain name (optional)",
        thc_percent="THC percentage (optional)",
        notes="Additional notes (optional)"
    )
    async def add_stash(
        self,
        interaction: discord.Interaction,
        type: str,
        amount: float,
        strain: Optional[str] = None,
        thc_percent: Optional[float] = None,
        notes: Optional[str] = None
    ):
        """Add to stash."""
        try:
            if type not in PRODUCT_TYPES:
                await interaction.response.send_message(
                    f"❌ Invalid type. Valid types: {', '.join(PRODUCT_TYPES)}",
                    ephemeral=True
                )
                return
            
            if amount <= 0:
                await interaction.response.send_message(
                    "❌ Amount must be positive",
                    ephemeral=True
                )
                return
            
            if thc_percent is not None and (thc_percent < 0 or thc_percent > 100):
                await interaction.response.send_message(
                    "❌ THC percentage must be between 0 and 100",
                    ephemeral=True
                )
                return
            
            user_id = interaction.user.id
            stash_item = await StashService.add_to_stash(
                user_id, type, amount, strain, thc_percent, notes
            )
            
            strain_text = f" ({strain})" if strain else ""
            thc_text = f" at {thc_percent}% THC" if thc_percent else ""
            
            unit = "mg" if type in ["edible", "tincture", "capsule"] else "g"
            
            embed = discord.Embed(
                title="✅ Added to Stash",
                description=f"Added {amount}{unit} of {type}{strain_text}{thc_text}",
                color=0x4CAF50
            )
            
            if notes:
                embed.add_field(name="Notes", value=notes, inline=False)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error adding to stash: {str(e)}", 
                ephemeral=True
            )

    @stash_group.command(name="remove", description="Remove items from your stash")
    @app_commands.describe(
        type="Type of cannabis product",
        amount="Amount to remove",
        strain="Strain name (optional)"
    )
    async def remove_stash(
        self,
        interaction: discord.Interaction,
        type: str,
        amount: float,
        strain: Optional[str] = None
    ):
        """Remove from stash."""
        try:
            if type not in PRODUCT_TYPES:
                await interaction.response.send_message(
                    f"❌ Invalid type. Valid types: {', '.join(PRODUCT_TYPES)}",
                    ephemeral=True
                )
                return
            
            if amount <= 0:
                await interaction.response.send_message(
                    "❌ Amount must be positive",
                    ephemeral=True
                )
                return
            
            user_id = interaction.user.id
            success, message = await StashService.remove_from_stash(
                user_id, type, amount, strain
            )
            
            if success:
                embed = discord.Embed(
                    title="✅ Removed from Stash",
                    description=message,
                    color=0x4CAF50
                )
            else:
                embed = discord.Embed(
                    title="❌ Could Not Remove",
                    description=message,
                    color=0xF44336
                )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error removing from stash: {str(e)}", 
                ephemeral=True
            )

    @stash_group.command(name="set", description="Set exact amount in stash")
    @app_commands.describe(
        type="Type of cannabis product",
        amount="Exact amount to set",
        strain="Strain name (optional)",
        thc_percent="THC percentage (optional)"
    )
    async def set_stash(
        self,
        interaction: discord.Interaction,
        type: str,
        amount: float,
        strain: Optional[str] = None,
        thc_percent: Optional[float] = None
    ):
        """Set exact stash amount."""
        try:
            if type not in PRODUCT_TYPES:
                await interaction.response.send_message(
                    f"❌ Invalid type. Valid types: {', '.join(PRODUCT_TYPES)}",
                    ephemeral=True
                )
                return
            
            if amount < 0:
                await interaction.response.send_message(
                    "❌ Amount cannot be negative",
                    ephemeral=True
                )
                return
            
            if thc_percent is not None and (thc_percent < 0 or thc_percent > 100):
                await interaction.response.send_message(
                    "❌ THC percentage must be between 0 and 100",
                    ephemeral=True
                )
                return
            
            user_id = interaction.user.id
            stash_item = await StashService.set_stash_amount(
                user_id, type, amount, strain, thc_percent
            )
            
            strain_text = f" ({strain})" if strain else ""
            thc_text = f" at {thc_percent}% THC" if thc_percent else ""
            
            unit = "mg" if type in ["edible", "tincture", "capsule"] else "g"
            
            embed = discord.Embed(
                title="✅ Stash Updated",
                description=f"Set {type}{strain_text} to {amount}{unit}{thc_text}",
                color=0x4CAF50
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error setting stash: {str(e)}", 
                ephemeral=True
            )

    @add_stash.autocomplete('type')
    @remove_stash.autocomplete('type')
    @set_stash.autocomplete('type')
    async def type_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        """Autocomplete for product types."""
        return [
            app_commands.Choice(name=product_type.title(), value=product_type)
            for product_type in PRODUCT_TYPES
            if current.lower() in product_type.lower()
        ][:25]

    @stash_group.command(name="random", description="Get a random strain from your stash to consume")
    async def random_stash(self, interaction: discord.Interaction):
        """Pick a random strain from user's stash for consumption."""
        try:
            await interaction.response.defer()
            
            user_id = interaction.user.id
            stash_items = await StashService.get_user_stash(user_id)
            
            # Filter out items with no strain or zero amount
            available_strains = [
                item for item in stash_items 
                if item.strain and item.amount > 0
            ]
            
            if not available_strains:
                embed = discord.Embed(
                    title="🎲 No Strains Available",
                    description="You don't have any named strains in your stash to pick from!\n\n"
                              "💡 **Tip:** Add some strains to your stash using `/stash add` with strain names.",
                    color=0x9E9E9E
                )
                await interaction.followup.send(embed=embed)
                return
            
            # Pick a random strain
            selected_item = random.choice(available_strains)
            
            # Try to get strain info from database
            strain_info = None
            if selected_item.strain:
                strain_results = await strain_db.search_strain(selected_item.strain)
                strain_info = strain_results[0] if strain_results else None
            
            # Create embed
            embed = discord.Embed(
                title="🎲 Random Stash Pick",
                description=f"Time to enjoy some **{selected_item.strain}**!",
                color=0xFF9800
            )
            
            # Add strain image if available
            if strain_info and strain_info.image_url:
                embed.set_image(url=strain_info.image_url)
            
            # Stash details
            stash_info = f"**Type:** {selected_item.type.title()}\n"
            stash_info += f"**Amount Available:** {selected_item.amount}g\n"
            
            if selected_item.thc_percent:
                stash_info += f"**THC:** {selected_item.thc_percent}%\n"
            
            if selected_item.notes:
                stash_info += f"**Your Notes:** {selected_item.notes}\n"
            
            embed.add_field(
                name="📦 From Your Stash",
                value=stash_info,
                inline=False
            )
            
            # Add strain info if available
            if strain_info:
                effects_display = strain_db.format_effects_display(strain_info)
                thc_range = self._format_range(strain_info.thc_low, strain_info.thc_high)
                
                strain_details = f"**Type:** {strain_info.type.title()}\n"
                strain_details += f"**Effects:** {effects_display}\n"
                
                if strain_info.most_common_terpene:
                    strain_details += f"**Main Terpene:** {strain_info.most_common_terpene.title()}\n"
                
                if thc_range != "N/A":
                    strain_details += f"**Database THC:** {thc_range}%\n"
                
                # Add description if available
                if strain_info.description:
                    # Truncate description if too long
                    desc = strain_info.description[:200] + "..." if len(strain_info.description) > 200 else strain_info.description
                    strain_details += f"**About:** {desc}\n"
                
                embed.add_field(
                    name="🌿 Strain Database Info",
                    value=strain_details,
                    inline=False
                )
                
                # Add detailed effects breakdown if available
                top_effects = strain_db.get_top_effects(strain_info, 5)
                if top_effects:
                    effects_breakdown = "\n".join([f"**{name}:** {pct:.0f}%" for name, pct in top_effects])
                    embed.add_field(
                        name="📊 Detailed Effects Profile",
                        value=effects_breakdown,
                        inline=True
                    )
                
                # Add usage suggestion based on strain type
                if strain_info.type.lower() == 'indica':
                    usage_tip = "🌙 **Best for:** Evening relaxation, sleep, pain relief\n💡 **Timing:** 1-2 hours before bed"
                elif strain_info.type.lower() == 'sativa':
                    usage_tip = "☀️ **Best for:** Daytime energy, creativity, focus\n💡 **Timing:** Morning or afternoon"
                else:  # hybrid
                    usage_tip = "⚖️ **Best for:** Balanced effects, versatile use\n💡 **Timing:** Any time of day"
                
                embed.add_field(
                    name="🎯 Usage Guide",
                    value=usage_tip,
                    inline=True
                )
                
            else:
                # Strain not found in database - provide general info
                embed.add_field(
                    name="ℹ️ Strain Information",
                    value=f"**{selected_item.strain}** is not in our strain database.\n\n"
                          f"💡 **Tip:** You can search our database with `/lookup {selected_item.strain}` "
                          f"or try `/search {selected_item.strain}` to find similar strains.\n\n"
                          f"🌿 **Your experience matters!** Consider adding notes about this strain's "
                          f"effects using `/stash add` when you restock.",
                    inline=False
                )
            
            # Add some encouraging text
            embed.set_footer(text="🎯 Enjoy your session! Remember to consume responsibly.")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(
                f"❌ Error picking random strain: {str(e)}", 
                ephemeral=True
            )

    def _format_range(self, low: Optional[float], high: Optional[float]) -> str:
        """Format THC/CBD range for display."""
        if low is None and high is None:
            return "N/A"
        elif low is None:
            return f"≤{high:.1f}"
        elif high is None:
            return f"≥{low:.1f}"
        elif low == high:
            return f"{low:.1f}"
        else:
            return f"{low:.1f}-{high:.1f}"

async def setup(bot):
    await bot.add_cog(StashCommands(bot))
