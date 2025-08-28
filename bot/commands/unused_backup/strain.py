"""Consolidated strain command replacing multiple strain-related commands."""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional, List
import logging
import random
from datetime import datetime

from bot.services.strain_database_service import StrainDatabaseService

logger = logging.getLogger(__name__)

class StrainCommands(commands.Cog):
    """Unified strain lookup and recommendation commands."""
    
    def __init__(self, bot):
        self.bot = bot
        self.strain_service = StrainDatabaseService()
    
    async def cog_load(self):
        """Load the strain database when cog loads."""
        await self.strain_service.load_database()
    
    def _get_strain_color(self, strain_type: str) -> int:
        """Get embed color based on strain type."""
        colors = {
            'indica': 0x9C27B0,    # Purple
            'sativa': 0x4CAF50,    # Green  
            'hybrid': 0xFF9800     # Orange
        }
        return colors.get(strain_type.lower(), 0x607D8B)
    
    def _format_range(self, low: Optional[float], high: Optional[float]) -> str:
        """Format THC/CBD range for display."""
        if low is not None and high is not None:
            if low == high:
                return f"{low}"
            return f"{low}-{high}"
        elif high is not None:
            return f"~{high}"
        elif low is not None:
            return f"~{low}"
        return "Unknown"
    
    @app_commands.command(name="strain", description="All-in-one strain lookup, search, and recommendations")
    @app_commands.describe(
        action="What you want to do with strains",
        query="Strain name, effect, or search term (depends on action)",
        strain_type="Filter by strain type (optional)",
        limit="Number of results to show (1-10, default 3)"
    )
    @app_commands.choices(
        action=[
            app_commands.Choice(name="🔍 Lookup - Get detailed strain info", value="lookup"),
            app_commands.Choice(name="🔎 Search - Search by effects/type/medical use", value="search"),
            app_commands.Choice(name="💡 Recommend - Get personalized recommendations", value="recommend"),
            app_commands.Choice(name="🎲 Random - Get random strain suggestions", value="random"),
            app_commands.Choice(name="🎁 Surprise - Daily surprise recommendation", value="surprise"),
            app_commands.Choice(name="⭐ Featured - Today's featured strain", value="featured"),
            app_commands.Choice(name="📊 Stats - Database statistics", value="stats")
        ],
        strain_type=[
            app_commands.Choice(name="🌿 Any", value="any"),
            app_commands.Choice(name="🟣 Indica", value="indica"),
            app_commands.Choice(name="🟢 Sativa", value="sativa"),
            app_commands.Choice(name="🟠 Hybrid", value="hybrid")
        ]
    )
    async def strain(
        self,
        interaction: discord.Interaction,
        action: app_commands.Choice[str],
        query: Optional[str] = None,
        strain_type: Optional[app_commands.Choice[str]] = None,
        limit: Optional[int] = 3
    ):
        """Universal strain command."""
        try:
            await interaction.response.defer()
            
            action_value = action.value
            type_filter = strain_type.value if strain_type and strain_type.value != "any" else None
            limit = max(1, min(limit or 3, 10))  # Clamp between 1-10
            
            if action_value == "lookup":
                await self._handle_lookup(interaction, query, limit)
            elif action_value == "search":
                await self._handle_search(interaction, query, type_filter, limit)
            elif action_value == "recommend":
                await self._handle_recommend(interaction, query, type_filter, limit)
            elif action_value == "random":
                await self._handle_random(interaction, type_filter, limit)
            elif action_value == "surprise":
                await self._handle_surprise(interaction)
            elif action_value == "featured":
                await self._handle_featured(interaction)
            elif action_value == "stats":
                await self._handle_stats(interaction)
            else:
                await interaction.followup.send("❌ Unknown action", ephemeral=True)
                
        except Exception as e:
            logger.error(f"Error in strain command: {e}")
            await interaction.followup.send(
                "❌ An error occurred while processing your request.",
                ephemeral=True
            )
    
    async def _handle_lookup(self, interaction: discord.Interaction, query: Optional[str], limit: int):
        """Handle strain lookup."""
        if not query:
            embed = discord.Embed(
                title="🔍 Strain Lookup",
                description="Please provide a strain name to look up.\n\n" +
                          "**Example:** `/strain action:lookup query:Blue Dream`",
                color=0xFF9800
            )
            await interaction.followup.send(embed=embed)
            return
        
        results = await self.strain_service.search_strain(query)
        
        if not results:
            embed = discord.Embed(
                title="❌ No Strains Found",
                description=f"No strains found matching '{query}'.",
                color=0xF44336
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Show detailed info for best match
        strain = results[0]
        embed = await self._create_detailed_strain_embed(strain)
        await interaction.followup.send(embed=embed)
    
    async def _handle_search(self, interaction: discord.Interaction, query: Optional[str], type_filter: Optional[str], limit: int):
        """Handle strain search."""
        if not query:
            embed = discord.Embed(
                title="🔎 Strain Search",
                description="Please provide search terms (effects, medical uses, etc.).\n\n" +
                          "**Examples:**\n" +
                          "• `/strain action:search query:relaxing`\n" +
                          "• `/strain action:search query:pain strain_type:indica`",
                color=0xFF9800
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Try different search methods
        results = []
        
        # First try effect-based search
        if query.lower() in ['relaxed', 'happy', 'euphoric', 'uplifted', 'creative', 'focused', 'energetic', 'sleepy']:
            results = await self.strain_service.get_strains_by_effects([query.lower()])
        else:
            # Try general search
            results = await self.strain_service.search_strain(query)
        
        # Filter by type if specified
        if type_filter and results:
            results = [s for s in results if s.type.lower() == type_filter.lower()]
        
        if not results:
            embed = discord.Embed(
                title="❌ No Results",
                description=f"No strains found for '{query}'" + 
                          (f" of type {type_filter}" if type_filter else ""),
                color=0xF44336
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Show multiple results
        embed = await self._create_search_results_embed(results[:limit], f"Search: {query}")
        await interaction.followup.send(embed=embed)
    
    async def _handle_recommend(self, interaction: discord.Interaction, query: Optional[str], type_filter: Optional[str], limit: int):
        """Handle strain recommendations."""
        preferences = {}
        if type_filter:
            preferences['strain_type'] = type_filter
        if query:
            preferences['desired_effects'] = [query.lower()]
        
        results = await self.strain_service.get_strain_recommendations(preferences)
        
        if not results:
            # Fallback to random strains of specified type
            results = await self.strain_service.get_random_strains(limit, type_filter)
        
        if not results:
            embed = discord.Embed(
                title="❌ No Recommendations",
                description="No recommendations available at this time.",
                color=0xF44336
            )
            await interaction.followup.send(embed=embed)
            return
        
        embed = await self._create_search_results_embed(results[:limit], "Recommendations")
        await interaction.followup.send(embed=embed)
    
    async def _handle_random(self, interaction: discord.Interaction, type_filter: Optional[str], limit: int):
        """Handle random strain suggestions."""
        results = await self.strain_service.get_random_strains(limit, type_filter)
        
        if not results:
            embed = discord.Embed(
                title="❌ No Random Strains",
                description="No strains available for random selection.",
                color=0xF44336
            )
            await interaction.followup.send(embed=embed)
            return
        
        embed = await self._create_search_results_embed(results, "Random Strains")
        await interaction.followup.send(embed=embed)
    
    async def _handle_surprise(self, interaction: discord.Interaction):
        """Handle surprise recommendation."""
        strain = await self.strain_service.get_surprise_recommendation()
        
        if not strain:
            embed = discord.Embed(
                title="❌ No Surprise Available",
                description="No surprise strain available at this time.",
                color=0xF44336
            )
            await interaction.followup.send(embed=embed)
            return
        
        embed = await self._create_detailed_strain_embed(strain, "🎁 Surprise Strain!")
        await interaction.followup.send(embed=embed)
    
    async def _handle_featured(self, interaction: discord.Interaction):
        """Handle daily featured strain."""
        strain = await self.strain_service.get_daily_featured_strain()
        
        if not strain:
            embed = discord.Embed(
                title="❌ No Featured Strain",
                description="No featured strain available today.",
                color=0xF44336
            )
            await interaction.followup.send(embed=embed)
            return
        
        embed = await self._create_detailed_strain_embed(strain, "⭐ Today's Featured Strain")
        await interaction.followup.send(embed=embed)
    
    async def _handle_stats(self, interaction: discord.Interaction):
        """Handle database statistics."""
        stats = self.strain_service.get_database_stats()
        
        embed = discord.Embed(
            title="📊 Strain Database Statistics",
            color=0x2196F3,
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="📈 Overview",
            value=f"**Total Strains:** {stats.get('total_strains', 0)}\n" +
                  f"**With Images:** {stats.get('strains_with_images', 0)}\n" +
                  f"**Avg THC:** {stats.get('average_thc', 0):.1f}%",
            inline=True
        )
        
        embed.add_field(
            name="🌿 By Type",
            value=f"**Indica:** {stats.get('indica_count', 0)}\n" +
                  f"**Sativa:** {stats.get('sativa_count', 0)}\n" +
                  f"**Hybrid:** {stats.get('hybrid_count', 0)}",
            inline=True
        )
        
        embed.add_field(
            name="🔝 Top Effects",
            value="\n".join([f"• {effect}" for effect in stats.get('top_effects', [])[:5]]),
            inline=True
        )
        
        await interaction.followup.send(embed=embed)
    
    async def _create_detailed_strain_embed(self, strain, title: Optional[str] = None) -> discord.Embed:
        """Create a detailed embed for a single strain."""
        embed = discord.Embed(
            title=title or f"🌿 {strain.name}",
            description=strain.description or "No description available",
            color=self._get_strain_color(strain.type)
        )
        
        # Add strain image if available
        if strain.image_url:
            embed.set_image(url=strain.image_url)
        
        # Basic info
        thc_range = self._format_range(strain.thc_low, strain.thc_high)
        
        embed.add_field(
            name="📊 Basic Information",
            value=f"**Type:** {strain.type.title()}\n" +
                  f"**THC:** {thc_range}%\n" +
                  f"**Main Terpene:** {strain.most_common_terpene or 'Unknown'}",
            inline=True
        )
        
        # Top effects with percentages
        top_effects = self.strain_service.get_top_effects(strain, limit=3)
        if top_effects:
            effect_text = []
            for effect, percentage in top_effects:
                emoji = "😌" if effect == "relaxed" else "😊" if effect == "happy" else "🚀" if effect == "euphoric" else "💫"
                effect_text.append(f"{emoji} {effect.title()} {percentage:.0f}%")
            
            embed.add_field(
                name="⚡ Top Effects",
                value="\n".join(effect_text),
                inline=True
            )
        
        # Usage tips
        if strain.type.lower() == "indica":
            tips = "🌙 Best for evening/nighttime use\n⚠️ May cause drowsiness"
        elif strain.type.lower() == "sativa":
            tips = "☀️ Great for daytime use\n💪 May increase energy"
        else:
            tips = "🌅 Suitable for any time\n⚖️ Balanced effects"
        
        embed.add_field(
            name="💡 Usage Tips",
            value=tips,
            inline=True
        )
        
        embed.set_footer(text="🗃️ Data from Leafly Cannabis Database")
        return embed
    
    async def _create_search_results_embed(self, strains: List, title: str) -> discord.Embed:
        """Create an embed showing multiple strain results."""
        embed = discord.Embed(
            title=f"🔍 {title}",
            color=0x4CAF50,
            timestamp=datetime.utcnow()
        )
        
        if not strains:
            embed.description = "No strains found."
            return embed
        
        # Show up to 5 strains in the embed
        for i, strain in enumerate(strains[:5], 1):
            thc_range = self._format_range(strain.thc_low, strain.thc_high)
            top_effects = self.strain_service.get_top_effects(strain, limit=2)
            effects_text = ", ".join([f"{effect.title()}" for effect, _ in top_effects])
            
            type_emoji = "🟣" if strain.type.lower() == "indica" else "🟢" if strain.type.lower() == "sativa" else "🟠"
            
            embed.add_field(
                name=f"{i}. {type_emoji} {strain.name}",
                value=f"**Type:** {strain.type.title()}\n" +
                      f"**THC:** {thc_range}%\n" +
                      f"**Effects:** {effects_text or 'Unknown'}",
                inline=True
            )
        
        if len(strains) > 5:
            embed.set_footer(text=f"Showing 5 of {len(strains)} results • Use /strain action:lookup for detailed info")
        else:
            embed.set_footer(text="Use /strain action:lookup query:STRAIN_NAME for detailed info")
        
        return embed

async def setup(bot):
    """Setup the cog."""
    await bot.add_cog(StrainCommands(bot))
