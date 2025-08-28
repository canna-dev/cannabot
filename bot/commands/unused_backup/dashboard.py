"""Dashboard command for quick overview."""

import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
from typing import Optional

from bot.services.consumption_service import ConsumptionService
from bot.services.stash_service import StashService
from bot.database.models import Alert


class DashboardCommands(commands.Cog):
    """Dashboard slash commands."""
    
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="dashboard", description="View your cannabis tracking dashboard")
    async def dashboard(self, interaction: discord.Interaction):
        """Show comprehensive dashboard overview."""
        try:
            user_id = interaction.user.id
            
            # Get today's data
            today_summary = await ConsumptionService.get_consumption_summary(user_id, days=1)
            week_summary = await ConsumptionService.get_consumption_summary(user_id, days=7)
            
            # Get stash overview
            stash_items = await StashService.get_stash_items(user_id)
            total_stash_value = sum(item.amount for item in stash_items)
            low_items = [item for item in stash_items if item.amount < 1.0]  # Less than 1g
            
            # Get active alerts
            active_alerts = await Alert.get_user_alerts(user_id, active_only=True)
            
            # Calculate predictions
            avg_daily_usage = week_summary.get('total_thc_mg', 0) / 7 if week_summary.get('total_thc_mg', 0) > 0 else 0
            
            embed = discord.Embed(
                title="🌿 Cannabis Tracking Dashboard",
                description=f"Overview for {interaction.user.display_name}",
                color=0x4CAF50,
                timestamp=datetime.now()
            )
            
            # Today's Usage
            today_thc = today_summary.get('total_thc_mg', 0)
            today_sessions = today_summary.get('session_count', 0)
            embed.add_field(
                name="📅 Today's Usage",
                value=f"**THC Absorbed:** {today_thc:.1f}mg\n"
                      f"**Sessions:** {today_sessions}\n"
                      f"**Methods:** {', '.join(today_summary.get('methods', ['None']))[:50]}",
                inline=True
            )
            
            # Weekly Trends
            week_thc = week_summary.get('total_thc_mg', 0)
            week_sessions = week_summary.get('session_count', 0)
            avg_daily_sessions = week_sessions / 7 if week_sessions > 0 else 0
            embed.add_field(
                name="📊 7-Day Trends",
                value=f"**Total THC:** {week_thc:.1f}mg\n"
                      f"**Avg Daily:** {avg_daily_usage:.1f}mg\n"
                      f"**Avg Sessions:** {avg_daily_sessions:.1f}/day",
                inline=True
            )
            
            # Stash Overview
            stash_text = f"**Total Items:** {len(stash_items)}\n"
            stash_text += f"**Total Weight:** {total_stash_value:.1f}g\n"
            if low_items:
                stash_text += f"**Low Stock:** {len(low_items)} items ⚠️"
            else:
                stash_text += "**Stock Levels:** Good ✅"
            
            embed.add_field(
                name="📦 Stash Status",
                value=stash_text,
                inline=True
            )
            
            # Tolerance Insights
            if len(week_summary.get('daily_data', [])) >= 3:
                recent_effectiveness = []
                for day_data in week_summary.get('daily_data', [])[-3:]:
                    if day_data.get('avg_effect_rating'):
                        recent_effectiveness.append(day_data['avg_effect_rating'])
                
                if recent_effectiveness:
                    avg_effectiveness = sum(recent_effectiveness) / len(recent_effectiveness)
                    if avg_effectiveness < 3.0:
                        tolerance_status = "Consider tolerance break 🔄"
                        tolerance_color = "🟡"
                    elif avg_effectiveness >= 4.0:
                        tolerance_status = "Optimal effectiveness ✨"
                        tolerance_color = "🟢"
                    else:
                        tolerance_status = "Good effectiveness 👍"
                        tolerance_color = "🟢"
                else:
                    tolerance_status = "Track effects for insights"
                    tolerance_color = "⚪"
            else:
                tolerance_status = "Need more data"
                tolerance_color = "⚪"
                
            embed.add_field(
                name="🎯 Tolerance Status",
                value=f"{tolerance_color} {tolerance_status}",
                inline=True
            )
            
            # Predictions
            if avg_daily_usage > 0 and stash_items:
                # Estimate days remaining for each strain
                strain_predictions = []
                for item in stash_items[:3]:  # Top 3 items
                    if item.amount > 0:
                        # Rough estimate assuming this strain represents portion of daily usage
                        days_left = (item.amount * 1000) / (avg_daily_usage * 0.1)  # Assume 10% of daily usage per strain
                        strain_predictions.append(f"{item.strain}: ~{int(days_left)}d")
                
                predictions_text = "\n".join(strain_predictions[:2]) if strain_predictions else "Add more stash data"
            else:
                predictions_text = "Track more usage for predictions"
                
            embed.add_field(
                name="🔮 Stash Predictions",
                value=predictions_text,
                inline=True
            )
            
            # Quick Actions
            quick_actions = [
                "`/smoke` - Log smoking session",
                "`/stash add` - Add to stash",
                "`/reports daily` - Detailed report",
                "`/analytics trends` - Usage trends"
            ]
            
            embed.add_field(
                name="⚡ Quick Actions",
                value="\n".join(quick_actions),
                inline=False
            )
            
            # Alerts & Achievements
            footer_text = ""
            if active_alerts:
                footer_text += f"🔔 {len(active_alerts)} active alerts • "
            footer_text += f"Updated {datetime.now().strftime('%H:%M')}"
            
            embed.set_footer(text=footer_text)
            
            # Add warning indicators
            warnings = []
            if today_thc > 50:  # High daily usage
                warnings.append("⚠️ High daily THC intake")
            if len(low_items) > 0:
                warnings.append(f"📦 {len(low_items)} items running low")
            if avg_daily_usage > 0 and today_thc > avg_daily_usage * 2:
                warnings.append("📈 Usage above weekly average")
                
            if warnings:
                embed.add_field(
                    name="⚠️ Notifications",
                    value="\n".join(warnings),
                    inline=False
                )

            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error loading dashboard: {str(e)}",
                ephemeral=True
            )

    @app_commands.command(name="quick", description="Quick consumption logging with minimal input")
    @app_commands.describe(
        method="Consumption method",
        amount="Amount (g for flower/concentrates, mg for edibles)",
        strain="Strain name (optional)"
    )
    async def quick_log(
        self,
        interaction: discord.Interaction,
        method: str,
        amount: float,
        strain: Optional[str] = None
    ):
        """Quick consumption logging for frequent users."""
        try:
            # Map method to proper consumption command
            method_map = {
                "smoke": ("smoking", "flower"),
                "vape": ("vaporizer", "flower"),
                "dab": ("dabbing", "concentrate"),
                "edible": ("edible", "edible"),
                "tincture": ("tincture", "tincture")
            }
            
            if method.lower() not in method_map:
                await interaction.response.send_message(
                    f"❌ Unknown method. Use: {', '.join(method_map.keys())}",
                    ephemeral=True
                )
                return
                
            consumption_method, product_type = method_map[method.lower()]
            
            # Auto-detect unit and convert if needed
            if product_type in ["edible", "tincture"] and amount < 10:
                # Likely entered in grams, convert to mg
                amount = amount * 1000
                unit = "mg"
            elif product_type in ["flower", "concentrate"]:
                unit = "g"
            else:
                unit = "mg"
            
            # Auto-fill THC from stash if strain provided
            thc_percent = None
            if strain:
                user_id = interaction.user.id
                stash_items = await StashService.get_stash_items(user_id)
                matching_item = next(
                    (item for item in stash_items 
                     if item.strain and item.strain.lower() == strain.lower() and item.thc_percent),
                    None
                )
                if matching_item:
                    thc_percent = matching_item.thc_percent
            
            # Log consumption using existing service
            user_id = interaction.user.id
            
            if product_type == "edible":
                amount_g = amount / 1000  # Convert mg to g for calculation
                thc_percent = 100.0  # Assume 100% for mg dosing
            elif product_type == "tincture":
                amount_g = amount / 1000
                thc_percent = 100.0
            else:
                amount_g = amount
                
            entry, warnings = await ConsumptionService.log_consumption(
                user_id=user_id,
                product_type=product_type,
                amount=amount_g,
                method=consumption_method,
                strain=strain,
                thc_percent=thc_percent,
                notes=f"Quick logged via /quick {method}"
            )
            
            # Quick response
            embed = discord.Embed(
                title="⚡ Quick Log Complete",
                color=0x4CAF50
            )
            
            strain_text = f" ({strain})" if strain else ""
            embed.add_field(
                name="Session",
                value=f"**{consumption_method.title()}** {amount}{unit}{strain_text}\n"
                      f"**THC Absorbed:** {entry.absorbed_thc_mg:.1f}mg",
                inline=False
            )
            
            if warnings:
                embed.add_field(
                    name="⚠️ Warnings",
                    value="\n".join(warnings),
                    inline=False
                )
                
            embed.set_footer(text="Use full commands for more options (effects, symptoms, notes)")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error in quick log: {str(e)}",
                ephemeral=True
            )


async def setup(bot):
    await bot.add_cog(DashboardCommands(bot))
