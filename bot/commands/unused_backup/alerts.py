"""Alert system for stash levels and consumption limits."""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
from datetime import datetime, timedelta

from bot.database.models import Alert, User
from bot.services.stash_service import StashService
from bot.services.consumption_service import ConsumptionService

class AlertCommands(commands.Cog):
    """Smart alert system commands."""
    
    def __init__(self, bot):
        self.bot = bot

    alert_group = app_commands.Group(name="alert", description="Manage smart alerts and notifications")

    @alert_group.command(name="low-stash", description="Set low stash alerts for products")
    @app_commands.describe(
        threshold_grams="Alert when any product drops below this amount (grams)",
        enabled="Enable or disable low stash alerts"
    )
    async def set_low_stash_alert(
        self,
        interaction: discord.Interaction,
        threshold_grams: float,
        enabled: bool = True
    ):
        """Set low stash alert threshold."""
        try:
            if threshold_grams < 0:
                await interaction.response.send_message(
                    "❌ Threshold must be positive", 
                    ephemeral=True
                )
                return

            user_id = interaction.user.id
            
            # Create or update alert
            alert = await Alert.create_or_update(
                user_id=user_id,
                alert_type='low_stash',
                threshold=threshold_grams,
                active=enabled
            )

            status = "✅ Enabled" if enabled else "❌ Disabled"
            embed = discord.Embed(
                title="🔔 Low Stash Alert Updated",
                color=0x4CAF50 if enabled else 0x9E9E9E
            )
            
            embed.add_field(
                name="📊 Threshold",
                value=f"{threshold_grams}g",
                inline=True
            )
            
            embed.add_field(
                name="🔔 Status",
                value=status,
                inline=True
            )

            embed.add_field(
                name="ℹ️ Info",
                value="You'll be notified when any product drops below this amount",
                inline=False
            )

            await interaction.response.send_message(embed=embed, ephemeral=True)

            # Check if any current products are below threshold
            if enabled:
                await self._check_low_stash_alerts(user_id, interaction.followup)

        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error setting alert: {str(e)}", 
                ephemeral=True
            )

    @alert_group.command(name="daily-limit", description="Set daily consumption limit alerts")
    @app_commands.describe(
        limit_mg="Daily THC limit in milligrams",
        enabled="Enable or disable daily limit alerts"
    )
    async def set_daily_limit_alert(
        self,
        interaction: discord.Interaction,
        limit_mg: float,
        enabled: bool = True
    ):
        """Set daily consumption limit alert."""
        try:
            if limit_mg <= 0:
                await interaction.response.send_message(
                    "❌ Daily limit must be positive", 
                    ephemeral=True
                )
                return

            user_id = interaction.user.id
            
            # Create or update alert
            alert = await Alert.create_or_update(
                user_id=user_id,
                alert_type='daily_limit',
                threshold=limit_mg,
                active=enabled
            )

            status = "✅ Enabled" if enabled else "❌ Disabled"
            embed = discord.Embed(
                title="🔔 Daily Limit Alert Updated",
                color=0x4CAF50 if enabled else 0x9E9E9E
            )
            
            embed.add_field(
                name="📊 Daily Limit",
                value=f"{limit_mg}mg THC",
                inline=True
            )
            
            embed.add_field(
                name="🔔 Status",
                value=status,
                inline=True
            )

            embed.add_field(
                name="ℹ️ Info",
                value="You'll be warned when approaching or exceeding this daily limit",
                inline=False
            )

            await interaction.response.send_message(embed=embed, ephemeral=True)

            # Check current daily consumption
            if enabled:
                await self._check_daily_limit_alert(user_id, interaction.followup)

        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error setting alert: {str(e)}", 
                ephemeral=True
            )

    @alert_group.command(name="view", description="View your current alert settings")
    async def view_alerts(self, interaction: discord.Interaction):
        """View current alert settings."""
        try:
            user_id = interaction.user.id
            alerts = await Alert.get_user_alerts(user_id)

            embed = discord.Embed(
                title="🔔 Your Alert Settings",
                color=0x2196F3
            )

            if not alerts:
                embed.description = "No alerts configured. Use `/alert low-stash` or `/alert daily-limit` to set up alerts."
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            for alert in alerts:
                status = "✅ Enabled" if alert.active else "❌ Disabled"
                
                if alert.alert_type == 'low_stash':
                    embed.add_field(
                        name="📦 Low Stash Alert",
                        value=f"**Threshold:** {alert.threshold}g\n**Status:** {status}",
                        inline=True
                    )
                elif alert.alert_type == 'daily_limit':
                    embed.add_field(
                        name="⚠️ Daily Limit Alert",
                        value=f"**Limit:** {alert.threshold}mg THC\n**Status:** {status}",
                        inline=True
                    )

            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error viewing alerts: {str(e)}", 
                ephemeral=True
            )

    @alert_group.command(name="test", description="Test your alert system")
    async def test_alerts(self, interaction: discord.Interaction):
        """Test alert system."""
        try:
            user_id = interaction.user.id
            
            embed = discord.Embed(
                title="🧪 Testing Alert System",
                color=0xFF9800
            )

            # Check low stash alerts
            low_stash_triggered = await self._check_low_stash_alerts(user_id, interaction.followup, test_mode=True)
            
            # Check daily limit alerts
            daily_limit_triggered = await self._check_daily_limit_alert(user_id, interaction.followup, test_mode=True)

            if not low_stash_triggered and not daily_limit_triggered:
                embed.description = "✅ All alerts are working! No current alerts triggered."
            else:
                embed.description = "⚠️ Some alerts are currently triggered (see below)"

            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error testing alerts: {str(e)}", 
                ephemeral=True
            )

    async def _check_low_stash_alerts(self, user_id: int, followup=None, test_mode=False):
        """Check for low stash conditions."""
        try:
            # Get low stash alert settings
            alert = await Alert.get_user_alert(user_id, 'low_stash')
            if not alert or not alert.active:
                return False

            # Get current stash
            stash_items = await StashService.get_stash_items(user_id)
            low_items = [item for item in stash_items if item.amount < alert.threshold]

            if low_items and followup:
                embed = discord.Embed(
                    title="⚠️ Low Stash Alert" + (" (Test)" if test_mode else ""),
                    color=0xFF5722
                )

                low_list = "\n".join([
                    f"• **{item.strain}** ({item.product_type}): {item.amount}g remaining"
                    for item in low_items
                ])

                embed.add_field(
                    name="📦 Low Stock Items",
                    value=low_list,
                    inline=False
                )

                embed.add_field(
                    name="📊 Alert Threshold",
                    value=f"{alert.threshold}g",
                    inline=True
                )

                embed.set_footer(text="Consider restocking these items!")
                
                await followup.send(embed=embed, ephemeral=True)

            return len(low_items) > 0

        except Exception as e:
            print(f"Error checking low stash alerts: {e}")
            return False

    async def _check_daily_limit_alert(self, user_id: int, followup=None, test_mode=False):
        """Check for daily limit conditions."""
        try:
            # Get daily limit alert settings
            alert = await Alert.get_user_alert(user_id, 'daily_limit')
            if not alert or not alert.active:
                return False

            # Get today's consumption
            summary = await ConsumptionService.get_consumption_summary(user_id, days=1)
            today_thc = summary.get('total_thc_mg', 0)

            # Check if approaching or exceeding limit
            warning_threshold = alert.threshold * 0.8  # Warn at 80%
            
            if today_thc >= warning_threshold and followup:
                if today_thc >= alert.threshold:
                    # Exceeded limit
                    title = "🚨 Daily Limit Exceeded" + (" (Test)" if test_mode else "")
                    color = 0xF44336
                    message = f"You've exceeded your daily limit!"
                else:
                    # Approaching limit  
                    title = "⚠️ Approaching Daily Limit" + (" (Test)" if test_mode else "")
                    color = 0xFF9800
                    message = f"You're approaching your daily limit."

                embed = discord.Embed(title=title, color=color)
                
                embed.add_field(
                    name="📊 Today's Consumption",
                    value=f"{today_thc:.1f}mg THC",
                    inline=True
                )
                
                embed.add_field(
                    name="🎯 Daily Limit",
                    value=f"{alert.threshold}mg THC",
                    inline=True
                )

                percent_used = (today_thc / alert.threshold) * 100
                embed.add_field(
                    name="📈 Limit Usage",
                    value=f"{percent_used:.1f}%",
                    inline=True
                )

                embed.description = message
                
                await followup.send(embed=embed, ephemeral=True)

            return today_thc >= warning_threshold

        except Exception as e:
            print(f"Error checking daily limit alerts: {e}")
            return False

async def setup(bot):
    await bot.add_cog(AlertCommands(bot))
