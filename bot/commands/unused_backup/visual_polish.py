"""Visual polish and enhanced status indicators."""

import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
import asyncio

from bot.services.consumption_service import ConsumptionService
from bot.services.stash_service import StashService

class VisualPolishCog(commands.Cog):
    """Visual enhancements and status indicators."""
    
    def __init__(self, bot):
        self.bot = bot
        # Color scheme for different categories
        self.colors = {
            'consumption': 0x4CAF50,  # Green
            'strains': 0x9C27B0,      # Purple  
            'stash': 0x2196F3,        # Blue
            'alerts': 0xFF9800,       # Orange
            'reports': 0x607D8B,      # Blue Grey
            'achievements': 0xFFD700,  # Gold
            'error': 0xF44336,        # Red
            'success': 0x4CAF50,      # Green
            'warning': 0xFF9800,      # Orange
            'info': 0x2196F3          # Blue
        }
    
    def create_progress_bar(self, current: float, maximum: float, length: int = 10) -> str:
        """Create a visual progress bar."""
        if maximum == 0:
            return "▱" * length
        
        filled = int((current / maximum) * length)
        filled = min(filled, length)  # Don't exceed max length
        
        # Use different characters for different fill levels
        if current >= maximum:
            bar = "▰" * length  # Full bar
        else:
            bar = "▰" * filled + "▱" * (length - filled)
        
        percentage = min((current / maximum) * 100, 100)
        return f"{bar} {percentage:.0f}%"
    
    def get_trend_indicator(self, current: float, previous: float) -> str:
        """Get trend indicator emoji."""
        if current > previous * 1.1:
            return "📈"  # Trending up
        elif current < previous * 0.9:
            return "📉"  # Trending down
        else:
            return "➡️"  # Stable
    
    def get_consumption_emoji(self, method: str) -> str:
        """Get emoji for consumption method."""
        emojis = {
            'smoke': '💨',
            'vaporizer': '💨',
            'dab': '🔥',
            'edible': '🍪',
            'tincture': '💧',
            'capsule': '💊'
        }
        return emojis.get(method, '🌿')
    
    def format_large_number(self, number: float) -> str:
        """Format large numbers with appropriate units."""
        if number >= 1000:
            return f"{number/1000:.1f}K"
        elif number >= 100:
            return f"{number:.0f}"
        else:
            return f"{number:.1f}"
    
    @app_commands.command(name="status", description="Show your cannabis tracking status with visual indicators")
    async def status(self, interaction: discord.Interaction):
        """Show comprehensive status with visual polish."""
        await interaction.response.defer(ephemeral=True)
        
        try:
            user_id = interaction.user.id
            
            # Get data
            today_summary = await ConsumptionService.get_consumption_summary(user_id, days=1)
            week_summary = await ConsumptionService.get_consumption_summary(user_id, days=7)
            stash_items = await StashService.get_stash_items(user_id)
            
            # Create main status embed
            embed = discord.Embed(
                title=f"🌿 {interaction.user.display_name}'s Cannabis Status",
                description="Your tracking overview with visual indicators",
                color=self.colors['info'],
                timestamp=datetime.now()
            )
            
            # Today's consumption
            today_sessions = today_summary.get('session_count', 0)
            today_thc = today_summary.get('total_thc_mg', 0)
            
            daily_status = "🌱 Clean day" if today_sessions == 0 else f"🍃 {today_sessions} sessions"
            
            embed.add_field(
                name="📅 Today",
                value=f"{daily_status}\n"
                      f"**THC:** {self.format_large_number(today_thc)}mg\n"
                      f"**Status:** {'Active' if today_sessions > 0 else 'Sober'}",
                inline=True
            )
            
            # Weekly overview
            week_sessions = week_summary.get('session_count', 0)
            week_thc = week_summary.get('total_thc_mg', 0)
            daily_avg = week_thc / 7 if week_thc > 0 else 0
            
            # Progress bar for weekly activity
            max_daily_sessions = 5  # Arbitrary max for progress bar
            session_progress = self.create_progress_bar(today_sessions, max_daily_sessions, 8)
            
            embed.add_field(
                name="📊 This Week",
                value=f"**Sessions:** {week_sessions}\n"
                      f"**THC:** {self.format_large_number(week_thc)}mg\n"
                      f"**Daily Avg:** {self.format_large_number(daily_avg)}mg",
                inline=True
            )
            
            # Stash overview
            total_stash_weight = sum(item.amount for item in stash_items if item.amount)
            stash_strains = len(set(item.strain for item in stash_items if item.strain))
            
            # Low stash warning
            stash_status = "📦 Well stocked"
            if total_stash_weight < 1.0:
                stash_status = "⚠️ Running low"
            elif total_stash_weight < 0.2:
                stash_status = "🚨 Almost empty"
            
            embed.add_field(
                name="📦 Stash",
                value=f"{stash_status}\n"
                      f"**Weight:** {total_stash_weight:.1f}g\n"
                      f"**Strains:** {stash_strains} varieties",
                inline=True
            )
            
            # Activity indicators
            activity_level = "🟢 Active" if today_sessions > 0 else "🔴 Sober"
            frequency = "High" if daily_avg > 50 else "Moderate" if daily_avg > 20 else "Low"
            
            embed.add_field(
                name="🎯 Activity Level",
                value=f"**Today:** {activity_level}\n"
                      f"**Frequency:** {frequency}\n"
                      f"**Trend:** {self.get_trend_indicator(today_thc, daily_avg)}",
                inline=True
            )
            
            # Quick insights
            insights = []
            
            if today_sessions == 0:
                insights.append("🌱 Taking a break today")
            elif today_sessions > 3:
                insights.append("⚡ High activity day")
            
            if total_stash_weight < 1.0:
                insights.append("📦 Consider restocking stash")
            
            if daily_avg > 100:
                insights.append("💡 Consider tolerance break")
            
            if insights:
                embed.add_field(
                    name="💡 Smart Insights",
                    value="\n".join(insights[:3]),  # Limit to 3 insights
                    inline=False
                )
            
            # Progress visualization
            progress_text = f"**Daily Activity:** {session_progress}\n"
            
            # THC progress (arbitrary 100mg daily max for visualization)
            thc_progress = self.create_progress_bar(today_thc, 100, 8)
            progress_text += f"**THC Level:** {thc_progress}"
            
            embed.add_field(
                name="📊 Progress Bars",
                value=progress_text,
                inline=False
            )
            
            # Footer with timestamp
            embed.set_footer(
                text=f"Last updated • Use /dashboard for detailed analytics",
                icon_url=interaction.user.display_avatar.url
            )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Status Error",
                description=f"Could not load status: {str(e)}",
                color=self.colors['error']
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(VisualPolishCog(bot))
