"""Enhanced strain lookup commands using Leafly database."""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional, List
import asyncio

from bot.services.strain_database_service import strain_db, StrainData

class StrainLookupCommands(commands.Cog):
    """Enhanced strain lookup and recommendation commands."""
    
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="lookup", description="Look up detailed strain information")
    @app_commands.describe(strain_name="Name of the strain to look up")
    async def lookup_strain(self, interaction: discord.Interaction, strain_name: str):
        """Look up detailed information about a specific strain."""
        try:
            await interaction.response.defer()
            
            # Search for the strain
            results = await strain_db.search_strain(strain_name)
            
            if not results:
                embed = discord.Embed(
                    title="🔍 Strain Not Found",
                    description=f"No strains found matching '{strain_name}'",
                    color=0x9E9E9E
                )
                embed.add_field(
                    name="💡 Suggestions",
                    value="• Check spelling\n• Try partial name (e.g., 'blue' for 'Blue Dream')\n• Use `/strain-search` for browsing\n• Use `/strain-recommend` for recommendations",
                    inline=False
                )
                await interaction.followup.send(embed=embed)
                return
            
            # Show the best match
            strain = results[0]
            
            embed = discord.Embed(
                title=f"🌿 {strain.name}",
                description=strain.description or "No description available",
                color=self._get_strain_color(strain.type)
            )
            
            # Add strain image if available - prioritize image display
            if strain.image_url:
                embed.set_image(url=strain.image_url)
                # Also add as thumbnail as backup
                embed.set_thumbnail(url=strain.image_url)
            else:
                # Add thumbnail for strain type if no image
                embed.set_thumbnail(url=self._get_type_thumbnail(strain.type))
            
            # Basic info with proper formatting
            thc_range = self._format_range(strain.thc_low, strain.thc_high)
            
            # Get most common terpene for display
            terpene_display = strain.most_common_terpene.title() if strain.most_common_terpene else "Unknown"
            
            embed.add_field(
                name="📊 Basic Information",
                value=f"**Type:** {strain.type.title()}\n"
                      f"**THC:** {thc_range}%\n"
                      f"**Main Terpene:** {strain.most_common_terpene or 'Unknown'}",
                inline=True
            )
            
            # Effects with percentages - more concise
            effects_display = strain_db.format_effects_display(strain)
            embed.add_field(
                name="⚡ Top Effects",
                value=effects_display,
                inline=True
            )
            
            # Add a spacer for better layout
            embed.add_field(name="\u200b", value="\u200b", inline=True)
            
            # Additional info - condensed
            additional_info = ""
            if strain.flavors:
                flavors = ", ".join(strain.flavors[:4])
                additional_info += f"**Flavors:** {flavors}\n"
            
            if strain.medical_uses:
                medical = ", ".join(strain.medical_uses[:3])
                additional_info += f"**Medical:** {medical}\n"
            
            if additional_info:
                embed.add_field(
                    name="💡 Additional Info",
                    value=additional_info,
                    inline=False
                )
            
            # Usage tips - keep this essential info
            usage_tips = self._get_usage_tips(strain)
            embed.add_field(
                name="� Usage Tips",
                value=usage_tips,
                inline=False
            )
            
            embed.set_footer(text="💾 Data from Leafly Cannabis Database")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(
                f"❌ Error looking up strain: {str(e)}"
            )

    @app_commands.command(name="search", description="Search strains by effects, type, or medical use")
    @app_commands.describe(
        search_type="What to search by",
        query="Your search query"
    )
    @app_commands.choices(search_type=[
        app_commands.Choice(name="Effects (e.g., relaxed, happy)", value="effects"),
        app_commands.Choice(name="Medical Condition", value="medical"),
        app_commands.Choice(name="Strain Type (indica/sativa/hybrid)", value="type"),
        app_commands.Choice(name="High CBD Strains", value="high_cbd"),
        app_commands.Choice(name="Balanced THC:CBD", value="balanced")
    ])
    async def search_strains(
        self,
        interaction: discord.Interaction,
        search_type: str,
        query: Optional[str] = None
    ):
        """Search for strains by various criteria."""
        try:
            await interaction.response.defer()
            
            results = []
            search_title = "🔍 Strain Search Results"  # Default title
            
            if search_type == "effects":
                if not query:
                    await interaction.followup.send("❌ Please provide effects to search for (e.g., 'relaxed, happy')")
                    return
                effects = [e.strip() for e in query.split(',')]
                results = await strain_db.get_strains_by_effects(effects)
                search_title = f"🎯 Strains with effects: {', '.join(effects)}"
                
            elif search_type == "medical":
                if not query:
                    await interaction.followup.send("❌ Please provide a medical condition to search for")
                    return
                results = await strain_db.get_strains_by_medical_condition(query)
                search_title = f"🏥 Strains for: {query.title()}"
                
            elif search_type == "type":
                if not query or query.lower() not in ['indica', 'sativa', 'hybrid']:
                    await interaction.followup.send("❌ Please specify: indica, sativa, or hybrid")
                    return
                results = await strain_db.get_strains_by_type(query)
                search_title = f"🌿 {query.title()} Strains"
                
            elif search_type == "high_cbd":
                results = await strain_db.get_high_cbd_strains()
                search_title = "🧪 High CBD Strains (10%+ CBD)"
                
            elif search_type == "balanced":
                results = await strain_db.get_balanced_strains()
                search_title = "⚖️ Balanced THC:CBD Strains"
            
            if not results:
                embed = discord.Embed(
                    title="🔍 No Results Found",
                    description=f"No strains found for your search criteria",
                    color=0x9E9E9E
                )
                await interaction.followup.send(embed=embed)
                return
            
            # Create paginated results
            embeds = []
            strains_per_embed = 4  # Fewer strains per embed for search results
            
            for i in range(0, len(results), strains_per_embed):
                chunk = results[i:i + strains_per_embed]
                embed_num = (i // strains_per_embed) + 1
                total_embeds = (len(results) + strains_per_embed - 1) // strains_per_embed
                
                if len(embeds) == 0:
                    # First embed
                    embed = discord.Embed(
                        title=search_title,
                        description=f"Found {len(results)} strain(s)",
                        color=0x4CAF50
                    )
                else:
                    # Subsequent embeds
                    embed = discord.Embed(
                        title=f"{search_title} (continued)",
                        description=f"Part {embed_num} of {total_embeds}",
                        color=0x4CAF50
                    )
                
                # Show strains in this chunk
                strain_list = ""
                for j, strain in enumerate(chunk, i + 1):
                    thc_range = self._format_range(strain.thc_low, strain.thc_high)
                    
                    strain_list += f"**{j}. {strain.name}** ({strain.type})\n"
                    strain_list += f"   {strain_db.format_effects_display(strain)} | THC: {thc_range}%\n"
                    
                    if strain.effects:
                        top_effects = ", ".join(strain.effects[:3])
                        strain_list += f"   Effects: {top_effects}\n\n"
                    else:
                        strain_list += "\n"
                
                embed.add_field(
                    name=f"🌿 Results {i+1}-{min(i+strains_per_embed, len(results))}",
                    value=strain_list,
                    inline=False
                )
                
                # Add more info to last embed only
                if i + strains_per_embed >= len(results):
                    if len(results) > len(chunk):
                        embed.add_field(
                            name="📖 More Results",
                            value=f"Showing all {len(results)} results. Use `/strain-lookup <name>` for detailed info.",
                            inline=False
                        )
                    embed.set_footer(text="💡 Use /strain-lookup <name> for detailed strain information")
                
                embeds.append(embed)
            
            # Send first embed as response, others as followups
            await interaction.followup.send(embed=embeds[0])
            
            for embed in embeds[1:]:
                await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Error searching strains: {str(e)}")

    @app_commands.command(name="recommend", description="Get personalized strain recommendations")
    @app_commands.describe(
        preferred_effects="Effects you want (comma-separated)",
        strain_type="Preferred strain type",
        medical_condition="Medical condition (optional)",
        max_thc="Maximum THC percentage"
    )
    @app_commands.choices(strain_type=[
        app_commands.Choice(name="No preference", value=""),
        app_commands.Choice(name="Indica", value="indica"),
        app_commands.Choice(name="Sativa", value="sativa"),
        app_commands.Choice(name="Hybrid", value="hybrid")
    ])
    async def recommend_strains(
        self,
        interaction: discord.Interaction,
        preferred_effects: Optional[str] = None,
        strain_type: Optional[str] = None,
        medical_condition: Optional[str] = None,
        max_thc: Optional[float] = None
    ):
        """Get personalized strain recommendations."""
        try:
            await interaction.response.defer()
            
            # Build preferences
            preferences = {}
            
            if preferred_effects:
                preferences['effects'] = [e.strip() for e in preferred_effects.split(',')]
            
            if strain_type:
                preferences['type'] = strain_type
            
            if medical_condition:
                preferences['medical_conditions'] = [medical_condition]
            
            if max_thc is not None:
                preferences['max_thc'] = max_thc
            
            # Get recommendations
            results = await strain_db.get_strain_recommendations(preferences)
            
            if not results:
                embed = discord.Embed(
                    title="🤖 No Recommendations Found",
                    description="No strains match your criteria. Try adjusting your preferences.",
                    color=0x9E9E9E
                )
                await interaction.followup.send(embed=embed)
                return
            
            embed = discord.Embed(
                title="🤖 Personalized Strain Recommendations",
                description="Based on your preferences",
                color=0x9C27B0
            )
            
            # Show criteria
            criteria_text = ""
            if preferred_effects:
                criteria_text += f"**Effects:** {preferred_effects}\n"
            if strain_type:
                criteria_text += f"**Type:** {strain_type.title()}\n"
            if medical_condition:
                criteria_text += f"**Medical:** {medical_condition.title()}\n"
            if max_thc is not None:
                criteria_text += f"**Max THC:** {max_thc}%\n"
            
            if criteria_text:
                embed.add_field(
                    name="🎯 Your Criteria",
                    value=criteria_text,
                    inline=False
                )
            
            # Show top recommendations (limit to 3 for better formatting)
            rec_text = ""
            for i, strain in enumerate(results[:3], 1):
                match_score = self._calculate_match_percentage(strain, preferences)
                thc_range = self._format_range(strain.thc_low, strain.thc_high)
                
                rec_text += f"**{i}. {strain.name}** ({strain.type}) - {match_score}% match\n"
                rec_text += f"   {strain_db.format_effects_display(strain)} | THC: {thc_range}%\n"
                
                if strain.effects:
                    matching_effects = [e for e in strain.effects if preferences.get('effects') and any(pe.lower() in e.lower() for pe in preferences['effects'])]
                    if matching_effects:
                        rec_text += f"   ✅ Matching effects: {', '.join(matching_effects[:2])}\n"
                
                rec_text += "\n"
            
            embed.add_field(
                name="🏆 Top Recommendations",
                value=rec_text,
                inline=False
            )
            
            # If more than 3 results, show additional ones in a second embed
            if len(results) > 3:
                embed.add_field(
                    name="� Additional Matches",
                    value=f"Found {len(results)} total matches. Additional recommendations available.",
                    inline=False
                )
            
            embed.add_field(
                name="�💡 Next Steps",
                value="• Use `/strain-lookup <name>` for detailed info\n"
                      "• Add to stash with `/stash add`\n"
                      "• Save as favorite strain\n"
                      "• Check local availability",
                inline=False
            )
            
            embed.set_footer(text="🎯 Recommendations based on Leafly database analysis")
            
            await interaction.followup.send(embed=embed)
            
            # If there are more than 3 results, send additional recommendations
            if len(results) > 3:
                additional_embed = discord.Embed(
                    title="🤖 Additional Recommendations",
                    description="More strains that match your criteria",
                    color=0x9C27B0
                )
                
                additional_text = ""
                for i, strain in enumerate(results[3:6], 4):  # Show 4-6
                    match_score = self._calculate_match_percentage(strain, preferences)
                    thc_range = self._format_range(strain.thc_low, strain.thc_high)
                    
                    additional_text += f"**{i}. {strain.name}** ({strain.type}) - {match_score}% match\n"
                    additional_text += f"   {strain_db.format_effects_display(strain)} | THC: {thc_range}%\n\n"
                
                additional_embed.add_field(
                    name="🌿 More Options",
                    value=additional_text,
                    inline=False
                )
                
                await interaction.followup.send(embed=additional_embed)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Error generating recommendations: {str(e)}")

    @app_commands.command(name="database-stats", description="View strain database statistics")
    async def database_stats(self, interaction: discord.Interaction):
        """Show statistics about the strain database."""
        try:
            await interaction.response.defer()
            
            # Load database if not loaded
            if not strain_db.loaded:
                await strain_db.load_database()
            
            stats = strain_db.get_database_stats()
            
            embed = discord.Embed(
                title="📊 Strain Database Statistics",
                description="Leafly Cannabis Strains Database",
                color=0x2196F3
            )
            
            embed.add_field(
                name="📈 Overview",
                value=f"**Total Strains:** {stats.get('total_strains', 0):,}\n"
                      f"**Average Rating:** {stats.get('average_rating', 0)}⭐\n"
                      f"**Database Status:** {'✅ Loaded' if stats.get('loaded', False) else '❌ Not Loaded'}",
                inline=False
            )
            
            # Type distribution
            type_dist = stats.get('type_distribution', {})
            if type_dist:
                type_text = ""
                for strain_type, count in type_dist.items():
                    percentage = (count / stats['total_strains']) * 100
                    type_text += f"**{strain_type.title()}:** {count:,} ({percentage:.1f}%)\n"
                
                embed.add_field(
                    name="🌿 Strain Types",
                    value=type_text,
                    inline=True
                )
            
            embed.add_field(
                name="🔍 Search Features",
                value="• Strain name lookup\n"
                      "• Effect-based search\n"
                      "• Medical condition matching\n"
                      "• THC/CBD filtering\n"
                      "• Personalized recommendations\n"
                      "• Terpene information",
                inline=True
            )
            
            embed.add_field(
                name="💡 Available Commands",
                value="• `/strain-lookup <name>` - Detailed strain info\n"
                      "• `/strain-search` - Search by criteria\n"
                      "• `/strain-recommend` - Personalized recommendations\n"
                      "• Use with stash and consumption tracking",
                inline=False
            )
            
            embed.set_footer(text="💾 Data sourced from Leafly Cannabis Database")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Error getting database stats: {str(e)}")

    @app_commands.command(name="random", description="Get random strain recommendations")
    @app_commands.describe(
        count="Number of random strains to show (1-10)",
        strain_type="Filter by strain type"
    )
    @app_commands.choices(strain_type=[
        app_commands.Choice(name="Any Type", value=""),
        app_commands.Choice(name="Indica", value="indica"),
        app_commands.Choice(name="Sativa", value="sativa"), 
        app_commands.Choice(name="Hybrid", value="hybrid")
    ])
    async def random_strains(
        self,
        interaction: discord.Interaction,
        count: int = 3,
        strain_type: Optional[str] = None
    ):
        """Get random strain recommendations."""
        try:
            await interaction.response.defer()
            
            # Validate count
            if not 1 <= count <= 10:
                await interaction.followup.send("❌ Count must be between 1 and 10", ephemeral=True)
                return
            
            # Get random strains
            results = await strain_db.get_random_strains(count, strain_type)
            
            if not results:
                embed = discord.Embed(
                    title="🎲 No Random Strains Found",
                    description="No strains available for random selection",
                    color=0x9E9E9E
                )
                await interaction.followup.send(embed=embed)
                return
            
            # Split results into multiple embeds if needed (max 3 strains per embed)
            embeds = []
            strains_per_embed = 3
            
            for i in range(0, len(results), strains_per_embed):
                chunk = results[i:i + strains_per_embed]
                embed_num = (i // strains_per_embed) + 1
                total_embeds = (len(results) + strains_per_embed - 1) // strains_per_embed
                
                if len(embeds) == 0:
                    # First embed has the main title
                    embed = discord.Embed(
                        title=f"🎲 Random Strain{'s' if count > 1 else ''} Discovery",
                        description=f"Here {'are' if count > 1 else 'is'} {count} random strain{'s' if count > 1 else ''}{f' ({strain_type})' if strain_type else ''}:",
                        color=0xFF9800
                    )
                else:
                    # Subsequent embeds have continuation titles
                    embed = discord.Embed(
                        title=f"🎲 Random Strains (continued)",
                        description=f"Part {embed_num} of {total_embeds}",
                        color=0xFF9800
                    )
                
                strain_text = ""
                for j, strain in enumerate(chunk, i + 1):
                    thc_range = self._format_range(strain.thc_low, strain.thc_high)
                    
                    strain_text += f"**{j}. {strain.name}** ({strain.type})\n"
                    strain_text += f"   {strain_db.format_effects_display(strain)} | THC: {thc_range}%\n"
                    
                    if strain.effects:
                        top_effects = ", ".join(strain.effects[:3])
                        strain_text += f"   Effects: {top_effects}\n"
                    
                    if strain.description:
                        # Truncate description to fit
                        desc = strain.description[:80] + "..." if len(strain.description) > 80 else strain.description
                        strain_text += f"   💬 {desc}\n"
                    
                    strain_text += "\n"
                
                embed.add_field(
                    name=f"🌿 Strains {i+1}-{min(i+strains_per_embed, len(results))}",
                    value=strain_text,
                    inline=False
                )
                
                # Add footer info to last embed only
                if i + strains_per_embed >= len(results):
                    embed.add_field(
                        name="🔍 Want More Info?",
                        value="Use `/strain-lookup <name>` for detailed information about any of these strains",
                        inline=False
                    )
                    embed.set_footer(text="🎲 Refresh for different random strains!")
                
                embeds.append(embed)
            
            # Send first embed as response, others as followups
            await interaction.followup.send(embed=embeds[0])
            
            for embed in embeds[1:]:
                await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Error getting random strains: {str(e)}")

    @app_commands.command(name="surprise", description="Get a surprise strain recommendation")
    async def surprise_strain(self, interaction: discord.Interaction):
        """Get a surprise strain recommendation."""
        try:
            await interaction.response.defer()
            
            # Get surprise recommendation
            strain = await strain_db.get_surprise_recommendation()
            
            if not strain:
                embed = discord.Embed(
                    title="🎁 No Surprise Available",
                    description="No strains available for surprise recommendation",
                    color=0x9E9E9E
                )
                await interaction.followup.send(embed=embed)
                return
            
            embed = discord.Embed(
                title=f"🎁 Surprise Recommendation: {strain.name}!",
                description=strain.description or "A mystery strain waiting to be discovered!",
                color=0xE91E63
            )
            
            # Basic info
            thc_range = self._format_range(strain.thc_low, strain.thc_high)
            
            embed.add_field(
                name="🎯 Why This Strain?",
                value=f"**Type:** {strain.type.title()}\n"
                      f"**Top Effects:** {strain_db.format_effects_display(strain)}\n"
                      f"**THC:** {thc_range}%\n"
                      f"**Main Terpene:** {strain.most_common_terpene or 'Unknown'}",
                inline=True
            )
            
            # Effects and flavors
            if strain.effects:
                effects_text = ", ".join(strain.effects[:5])
                embed.add_field(
                    name="⚡ What to Expect",
                    value=effects_text,
                    inline=True
                )
            
            if strain.flavors:
                flavors_text = ", ".join(strain.flavors[:5])
                embed.add_field(
                    name="👅 Flavor Profile",
                    value=flavors_text,
                    inline=True
                )
            
            # Usage suggestions
            usage_tips = self._get_usage_tips(strain)
            if usage_tips:
                embed.add_field(
                    name="💡 Usage Tips",
                    value=usage_tips,
                    inline=False
                )
            
            embed.add_field(
                name="🎲 Want Another Surprise?",
                value="Run this command again for a different surprise recommendation!",
                inline=False
            )
            
            embed.set_footer(text="🎁 Every surprise is a chance to discover something new!")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Error getting surprise strain: {str(e)}")

    @app_commands.command(name="daily-featured", description="Get today's featured strain")
    async def daily_featured(self, interaction: discord.Interaction):
        """Get today's featured strain (same strain all day, changes daily)."""
        try:
            await interaction.response.defer()
            
            # Get daily featured strain
            strain = await strain_db.get_daily_featured_strain()
            
            if not strain:
                embed = discord.Embed(
                    title="📅 No Featured Strain Today",
                    description="No strains available for daily feature",
                    color=0x9E9E9E
                )
                await interaction.followup.send(embed=embed)
                return
            
            import datetime
            today = datetime.date.today()
            
            embed = discord.Embed(
                title=f"📅 Today's Featured Strain: {strain.name}",
                description=f"**{today.strftime('%B %d, %Y')}**\n\n{strain.description or 'Discover what makes this strain special!'}",
                color=0x4CAF50
            )
            
            # Detailed info for featured strain
            thc_range = self._format_range(strain.thc_low, strain.thc_high)
            
            embed.add_field(
                name="⭐ Featured Details",
                value=f"**Type:** {strain.type.title()}\n"
                      f"**Top Effects:** {strain_db.format_effects_display(strain)}\n"
                      f"**THC:** {thc_range}%\n"
                      f"**Main Terpene:** {strain.most_common_terpene or 'Unknown'}",
                inline=True
            )
            
            # Why it's featured
            featured_reasons = []
            if strain.rating >= 4.5:
                featured_reasons.append("🏆 Exceptionally high rating")
            if strain.effects and 'happy' in [e.lower() for e in strain.effects]:
                featured_reasons.append("😊 Known for positive effects")
            if strain.medical_uses:
                featured_reasons.append("🏥 Medical benefits")
            if not featured_reasons:
                featured_reasons.append("🌟 Community favorite")
            
            embed.add_field(
                name="🎯 Why Featured Today",
                value="\n".join(featured_reasons[:3]),
                inline=True
            )
            
            # Effects and flavors
            if strain.effects:
                effects_text = ", ".join(strain.effects[:6])
                embed.add_field(
                    name="⚡ Effects",
                    value=effects_text,
                    inline=False
                )
            
            if strain.flavors:
                flavors_text = ", ".join(strain.flavors[:6])
                embed.add_field(
                    name="👅 Flavors",
                    value=flavors_text,
                    inline=False
                )
            
            # Medical uses if available
            if strain.medical_uses:
                medical_text = ", ".join(strain.medical_uses[:5])
                embed.add_field(
                    name="🏥 Medical Uses",
                    value=medical_text,
                    inline=False
                )
            
            embed.add_field(
                name="💡 Today's Recommendation",
                value="This strain has been selected as today's feature based on its quality and user ratings. "
                      "Consider trying it if you're looking for something new!",
                inline=False
            )
            
            embed.set_footer(text="📅 A new strain will be featured tomorrow!")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Error getting daily featured strain: {str(e)}")

    def _get_strain_color(self, strain_type: str) -> int:
        """Get color based on strain type."""
        colors = {
            'indica': 0x9C27B0,    # Purple
            'sativa': 0x4CAF50,    # Green
            'hybrid': 0xFF9800     # Orange
        }
        return colors.get(strain_type.lower(), 0x607D8B)

    def _get_type_thumbnail(self, strain_type: str) -> str:
        """Get thumbnail image URL based on strain type."""
        thumbnails = {
            'indica': 'https://via.placeholder.com/100x100/9C27B0/FFFFFF?text=IND',
            'sativa': 'https://via.placeholder.com/100x100/4CAF50/FFFFFF?text=SAT', 
            'hybrid': 'https://via.placeholder.com/100x100/FF9800/FFFFFF?text=HYB'
        }
        return thumbnails.get(strain_type.lower(), 'https://via.placeholder.com/100x100/607D8B/FFFFFF?text=???')

    def _format_rating(self, rating: float) -> str:
        """Format rating with proper star display."""
        if rating <= 0:
            return "No rating"
        return f"{rating:.1f}⭐"

    def _format_range(self, low: Optional[float], high: Optional[float]) -> str:
        """Format percentage range."""
        if high and low:
            return f"{low}-{high}"
        elif high:
            return f"~{high}"
        elif low:
            return f"~{low}"
        else:
            return "N/A"

    def _get_usage_tips(self, strain: StrainData) -> str:
        """Generate usage tips based on strain characteristics."""
        tips = []
        
        if strain.type.lower() == 'indica':
            tips.append("🌙 Best for evening/nighttime use")
        elif strain.type.lower() == 'sativa':
            tips.append("☀️ Ideal for daytime activities")
        else:
            tips.append("⚖️ Versatile for day or evening use")
        
        if strain.thc_high and strain.thc_high > 20:
            tips.append("⚠️ High THC - start with small amounts")
        
        if strain.cbd_high and strain.cbd_high > 10:
            tips.append("🧪 High CBD - good for medical use")
        
        if 'sleepy' in [e.lower() for e in strain.effects]:
            tips.append("💤 May cause drowsiness")
        
        if 'energetic' in [e.lower() for e in strain.effects]:
            tips.append("⚡ May increase energy and focus")
        
        return "\n".join(tips[:4]) if tips else "No specific usage tips available"

    def _calculate_match_percentage(self, strain: StrainData, preferences: dict) -> int:
        """Calculate how well a strain matches user preferences."""
        score = 70  # Base score
        
        # Effects matching
        if preferences.get('effects'):
            pref_effects = [e.lower() for e in preferences['effects']]
            strain_effects = [e.lower() for e in strain.effects]
            matches = sum(1 for pe in pref_effects if any(pe in se for se in strain_effects))
            score += (matches / len(pref_effects)) * 20
        
        # Type matching
        if preferences.get('type') and strain.type.lower() == preferences['type'].lower():
            score += 10
        
        return min(100, int(score))

    def _truncate_field_value(self, text: str, max_length: int = 1024) -> str:
        """Truncate text to fit Discord embed field limits."""
        if len(text) <= max_length:
            return text
        
        # Find a good truncation point (at end of line)
        truncated = text[:max_length-3]
        last_newline = truncated.rfind('\n')
        
        if last_newline > max_length * 0.7:  # If we can truncate at a reasonable point
            truncated = truncated[:last_newline]
        
        return truncated + "..."

    def _split_strain_list(self, strains: List[StrainData], max_per_group: int = 3) -> List[List[StrainData]]:
        """Split strain list into smaller groups for multiple embeds."""
        return [strains[i:i + max_per_group] for i in range(0, len(strains), max_per_group)]

async def setup(bot):
    await bot.add_cog(StrainLookupCommands(bot))
