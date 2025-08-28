"""Reports and analytics commands."""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional

from bot.services.consumption_service import ConsumptionService
from bot.database.models import ConsumptionEntry

class ReportCommands(commands.Cog):
    """Report and analytics slash commands."""
    
    def __init__(self, bot):
        self.bot = bot

    report_group = app_commands.Group(name="report", description="View consumption reports and analytics")

    @report_group.command(name="daily", description="View daily consumption report")
    async def daily_report(self, interaction: discord.Interaction):
        """Generate daily consumption report."""
        try:
            user_id = interaction.user.id
            summary = await ConsumptionService.get_consumption_summary(user_id, days=1)
            
            embed = discord.Embed(
                title="📊 Daily Consumption Report",
                description=ConsumptionService.format_consumption_summary(summary, 1),
                color=0x2196F3
            )
            
            embed.set_footer(text="Data shows consumption for today")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error generating daily report: {str(e)}", 
                ephemeral=True
            )

    @report_group.command(name="weekly", description="View weekly consumption report")
    async def weekly_report(self, interaction: discord.Interaction):
        """Generate weekly consumption report."""
        try:
            user_id = interaction.user.id
            summary = await ConsumptionService.get_consumption_summary(user_id, days=7)
            
            embed = discord.Embed(
                title="📊 Weekly Consumption Report",
                description=ConsumptionService.format_consumption_summary(summary, 7),
                color=0x2196F3
            )
            
            if summary["total_sessions"] > 0:
                avg_per_day = summary["total_absorbed_mg"] / 7
                embed.add_field(
                    name="📈 Daily Average",
                    value=f"{avg_per_day:.1f}mg THC absorbed",
                    inline=True
                )
            
            embed.set_footer(text="Data shows consumption for the past 7 days")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error generating weekly report: {str(e)}", 
                ephemeral=True
            )

    @report_group.command(name="monthly", description="View monthly consumption report")
    async def monthly_report(self, interaction: discord.Interaction):
        """Generate monthly consumption report."""
        try:
            user_id = interaction.user.id
            summary = await ConsumptionService.get_consumption_summary(user_id, days=30)
            
            embed = discord.Embed(
                title="📊 Monthly Consumption Report",
                description=ConsumptionService.format_consumption_summary(summary, 30),
                color=0x2196F3
            )
            
            if summary["total_sessions"] > 0:
                avg_per_day = summary["total_absorbed_mg"] / 30
                avg_per_session = summary["total_absorbed_mg"] / summary["total_sessions"]
                
                embed.add_field(
                    name="📈 Averages",
                    value=f"**Daily:** {avg_per_day:.1f}mg THC\n**Per Session:** {avg_per_session:.1f}mg THC",
                    inline=True
                )
            
            embed.set_footer(text="Data shows consumption for the past 30 days")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error generating monthly report: {str(e)}", 
                ephemeral=True
            )

    @report_group.command(name="recent", description="View recent consumption sessions")
    @app_commands.describe(
        limit="Number of recent sessions to show (default: 10)"
    )
    async def recent_sessions(
        self, 
        interaction: discord.Interaction,
        limit: Optional[int] = 10
    ):
        """Show recent consumption sessions."""
        try:
            if limit and (limit < 1 or limit > 50):
                await interaction.response.send_message(
                    "❌ Limit must be between 1 and 50",
                    ephemeral=True
                )
                return
            
            user_id = interaction.user.id
            entries = await ConsumptionEntry.get_user_consumption(user_id, limit or 10)
            
            if not entries:
                embed = discord.Embed(
                    title="📝 Recent Sessions",
                    description="No consumption sessions recorded yet.",
                    color=0x9E9E9E
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            embed = discord.Embed(
                title=f"📝 Recent Sessions ({len(entries)})",
                color=0x2196F3
            )
            
            # Format entries for display
            description_parts = []
            for i, entry in enumerate(entries[:10], 1):  # Limit to 10 for embed size
                session_text = ConsumptionService.format_consumption_entry(entry)
                description_parts.append(f"**{i}.** {session_text}")
            
            # Join with separators, but limit total length
            description = "\n\n".join(description_parts)
            if len(description) > 4000:  # Discord embed limit
                description = description[:4000] + "..."
            
            embed.description = description
            embed.set_footer(text=f"Showing {len(entries)} most recent sessions")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error showing recent sessions: {str(e)}", 
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(ReportCommands(bot))
