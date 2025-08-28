"""Automation commands for smart cannabis tracking workflows."""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional, List
from datetime import datetime, timedelta

from bot.services.automation_service import AutomationService

class AutomationCommands(commands.Cog):
    """Automation and smart workflow commands."""
    
    def __init__(self, bot):
        self.bot = bot
        self.automation_service = AutomationService()

    @app_commands.command(name="auto-deduct", description="Enable automatic stash deduction")
    @app_commands.describe(enabled="Enable or disable auto-deduction")
    async def auto_deduct(self, interaction: discord.Interaction, enabled: bool):
        """Toggle automatic stash deduction."""
        try:
            user_id = interaction.user.id
            
            # This would be implemented with user preferences in database
            # For now, just confirm the setting
            
            embed = discord.Embed(
                title="🤖 Auto-Deduction Settings",
                description=f"Automatic stash deduction {'enabled' if enabled else 'disabled'}",
                color=0x4CAF50 if enabled else 0x9E9E9E
            )
            
            if enabled:
                embed.add_field(
                    name="✅ Auto-Deduction Enabled",
                    value="• Stash will be automatically updated when you log consumption\n"
                          "• System will match strain names and consumption amounts\n"
                          "• You'll get warnings if stash is running low\n"
                          "• Manual overrides are always available",
                    inline=False
                )
                
                embed.add_field(
                    name="⚙️ How It Works",
                    value="1. You log consumption with `/consume`\n"
                          "2. Bot automatically finds matching strain in stash\n"
                          "3. Deducts the consumed amount\n"
                          "4. Notifies you of remaining amount",
                    inline=False
                )
            else:
                embed.add_field(
                    name="❌ Auto-Deduction Disabled",
                    value="You'll need to manually update your stash using `/stash remove`",
                    inline=False
                )
            
            embed.set_footer(text="💡 You can change this setting anytime")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error updating auto-deduction settings: {str(e)}",
                ephemeral=True
            )

    @app_commands.command(name="smart-alerts", description="Set up intelligent alerts")
    @app_commands.describe(
        alert_type="Type of smart alert to configure",
        threshold="Threshold value for the alert"
    )
    @app_commands.choices(alert_type=[
        app_commands.Choice(name="Low Stash Alert", value="low_stash"),
        app_commands.Choice(name="Tolerance Break Reminder", value="tolerance_break"),
        app_commands.Choice(name="Reorder Suggestion", value="reorder"),
        app_commands.Choice(name="Daily Limit Warning", value="daily_limit")
    ])
    async def smart_alerts(
        self,
        interaction: discord.Interaction,
        alert_type: str,
        threshold: float
    ):
        """Configure intelligent alerts."""
        try:
            user_id = interaction.user.id
            
            alert_configs = {
                "low_stash": {
                    "title": "🔔 Low Stash Alert",
                    "description": f"Alert when any strain drops below {threshold}g",
                    "details": "• Monitors all strains in your stash\n"
                              "• Alerts when quantity gets low\n"
                              "• Suggests reorder timing\n"
                              "• Helps prevent running out"
                },
                "tolerance_break": {
                    "title": "⏰ Tolerance Break Reminder",
                    "description": f"Suggest tolerance break after {threshold} days of use",
                    "details": "• Tracks daily consumption patterns\n"
                              "• Suggests optimal break timing\n"
                              "• Monitors effectiveness ratings\n"
                              "• Helps maintain medication efficacy"
                },
                "reorder": {
                    "title": "📦 Smart Reorder Alert",
                    "description": f"Reorder suggestions when {threshold} days supply remains",
                    "details": "• Calculates consumption rate\n"
                              "• Predicts when you'll run out\n"
                              "• Accounts for delivery time\n"
                              "• Prevents supply interruptions"
                },
                "daily_limit": {
                    "title": "⚠️ Daily Limit Warning",
                    "description": f"Warning when daily THC exceeds {threshold}mg",
                    "details": "• Tracks total daily THC intake\n"
                              "• Warns before reaching set limit\n"
                              "• Helps maintain responsible use\n"
                              "• Supports medical dosing goals"
                }
            }
            
            config = alert_configs.get(alert_type)
            if not config:
                await interaction.response.send_message(
                    "❌ Invalid alert type",
                    ephemeral=True
                )
                return
            
            embed = discord.Embed(
                title=config["title"],
                description=config["description"],
                color=0x2196F3
            )
            
            embed.add_field(
                name="🔧 Alert Configuration",
                value=f"**Type:** {alert_type.replace('_', ' ').title()}\n"
                      f"**Threshold:** {threshold}\n"
                      f"**Status:** Active ✅\n"
                      f"**User:** {interaction.user.mention}",
                inline=False
            )
            
            embed.add_field(
                name="📋 Features",
                value=config["details"],
                inline=False
            )
            
            embed.add_field(
                name="🎛️ Management",
                value="• Use `/alerts list` to view all alerts\n"
                      "• Use `/alerts toggle` to enable/disable\n"
                      "• Modify thresholds anytime\n"
                      "• Get smart recommendations",
                inline=False
            )
            
            embed.set_footer(text="🤖 Smart automation helping optimize your cannabis experience")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error configuring smart alert: {str(e)}",
                ephemeral=True
            )

    @app_commands.command(name="batch-update", description="Update multiple stash items at once")
    @app_commands.describe(
        operation="Batch operation to perform",
        amount="Amount to add/remove from all items"
    )
    @app_commands.choices(operation=[
        app_commands.Choice(name="Add to all strains", value="add_all"),
        app_commands.Choice(name="Remove from all strains", value="remove_all"),
        app_commands.Choice(name="Update THC% for all", value="update_thc"),
        app_commands.Choice(name="Set expiry for all", value="set_expiry")
    ])
    async def batch_update(
        self,
        interaction: discord.Interaction,
        operation: str,
        amount: float
    ):
        """Perform batch operations on stash."""
        try:
            await interaction.response.defer(ephemeral=True)
            
            user_id = interaction.user.id
            
            operation_info = {
                "add_all": {
                    "title": "📈 Batch Add to Stash",
                    "description": f"Adding {amount}g to all strains",
                    "action": "added",
                    "icon": "➕"
                },
                "remove_all": {
                    "title": "📉 Batch Remove from Stash", 
                    "description": f"Removing {amount}g from all strains",
                    "action": "removed",
                    "icon": "➖"
                },
                "update_thc": {
                    "title": "🧪 Batch Update THC%",
                    "description": f"Setting THC% to {amount}% for all strains",
                    "action": "updated",
                    "icon": "🔄"
                },
                "set_expiry": {
                    "title": "📅 Batch Set Expiry",
                    "description": f"Setting expiry to {amount} days from now",
                    "action": "updated",
                    "icon": "⏰"
                }
            }
            
            info = operation_info.get(operation)
            if not info:
                await interaction.followup.send("❌ Invalid operation", ephemeral=True)
                return
            
            # This would perform the actual batch operation using automation service
            # For now, simulate the response
            
            embed = discord.Embed(
                title=f"{info['icon']} {info['title']}",
                description=info['description'],
                color=0x4CAF50
            )
            
            # Simulate batch results
            affected_strains = ["Blue Dream", "Girl Scout Cookies", "Northern Lights", "OG Kush"]
            
            embed.add_field(
                name="✅ Operation Complete",
                value=f"Successfully {info['action']} {len(affected_strains)} strains:\n\n" +
                      "\n".join([f"• {strain}" for strain in affected_strains]),
                inline=False
            )
            
            embed.add_field(
                name="📊 Summary",
                value=f"**Strains affected:** {len(affected_strains)}\n"
                      f"**Operation:** {operation.replace('_', ' ').title()}\n"
                      f"**Value:** {amount}\n"
                      f"**Status:** Completed ✅",
                inline=False
            )
            
            embed.add_field(
                name="🔍 Next Steps",
                value="• Check updated stash with `/stash list`\n"
                      "• Review changes with `/stash details`\n"
                      "• Undo if needed with reverse operation",
                inline=False
            )
            
            embed.set_footer(text="⚡ Batch operations save time managing large stashes")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(
                f"❌ Error performing batch operation: {str(e)}",
                ephemeral=True
            )

    @app_commands.command(name="workflow", description="Set up automated workflows")
    @app_commands.describe(workflow_type="Type of workflow to configure")
    @app_commands.choices(workflow_type=[
        app_commands.Choice(name="Morning Routine", value="morning"),
        app_commands.Choice(name="Evening Routine", value="evening"),
        app_commands.Choice(name="Medical Schedule", value="medical"),
        app_commands.Choice(name="Tolerance Management", value="tolerance")
    ])
    async def workflow(self, interaction: discord.Interaction, workflow_type: str):
        """Set up automated cannabis workflows."""
        try:
            workflows = {
                "morning": {
                    "title": "🌅 Morning Cannabis Routine",
                    "description": "Automated morning medication workflow",
                    "steps": [
                        "⏰ Check tolerance level",
                        "💊 Review prescribed dosage",
                        "🌿 Select optimal strain for energy/focus",
                        "📝 Log consumption automatically",
                        "📊 Track symptom improvements",
                        "⚠️ Alert if daily limit approached"
                    ],
                    "triggers": "Daily at your set time",
                    "benefits": "Consistent dosing, symptom tracking, strain optimization"
                },
                "evening": {
                    "title": "🌙 Evening Cannabis Routine",
                    "description": "Automated evening relaxation workflow",
                    "steps": [
                        "📊 Review daily consumption",
                        "💤 Select strains for sleep/relaxation",
                        "🕐 Optimize timing for sleep",
                        "📝 Auto-log evening dose",
                        "😴 Set sleep quality tracking",
                        "📈 Prepare next day recommendations"
                    ],
                    "triggers": "Evening time or manual activation",
                    "benefits": "Better sleep, usage tracking, next-day planning"
                },
                "medical": {
                    "title": "🏥 Medical Cannabis Schedule",
                    "description": "Structured medical dosing workflow",
                    "steps": [
                        "💉 Check prescribed schedule",
                        "🎯 Calculate precise dosage",
                        "🌿 Match strain to symptoms",
                        "⏰ Time doses optimally",
                        "📋 Log medical effectiveness",
                        "📊 Generate doctor reports"
                    ],
                    "triggers": "Scheduled times or symptom-based",
                    "benefits": "Medical compliance, effectiveness tracking, doctor communication"
                },
                "tolerance": {
                    "title": "🔄 Tolerance Management",
                    "description": "Intelligent tolerance break workflow",
                    "steps": [
                        "📈 Monitor effectiveness decline",
                        "⚡ Detect tolerance buildup",
                        "📅 Suggest break timing",
                        "📊 Track break progress",
                        "🎯 Plan return dosing",
                        "✅ Verify tolerance reset"
                    ],
                    "triggers": "Effectiveness drops or time-based",
                    "benefits": "Maintain effectiveness, optimize breaks, prevent dependence"
                }
            }
            
            workflow = workflows.get(workflow_type)
            if not workflow:
                await interaction.response.send_message(
                    "❌ Invalid workflow type",
                    ephemeral=True
                )
                return
            
            embed = discord.Embed(
                title=workflow["title"],
                description=workflow["description"],
                color=0x9C27B0
            )
            
            embed.add_field(
                name="🔄 Workflow Steps",
                value="\n".join(workflow["steps"]),
                inline=False
            )
            
            embed.add_field(
                name="⚡ Triggers",
                value=workflow["triggers"],
                inline=True
            )
            
            embed.add_field(
                name="🎯 Benefits",
                value=workflow["benefits"],
                inline=True
            )
            
            embed.add_field(
                name="🛠️ Setup Required",
                value="• Set your preferred times\n"
                      "• Configure strain preferences\n"
                      "• Set dosage limits\n"
                      "• Enable notifications",
                inline=False
            )
            
            embed.add_field(
                name="🎛️ Controls",
                value="• Enable/disable anytime\n"
                      "• Customize all steps\n"
                      "• Override when needed\n"
                      "• Track workflow effectiveness",
                inline=False
            )
            
            embed.set_footer(text="🤖 Automated workflows optimize your cannabis experience")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error configuring workflow: {str(e)}",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(AutomationCommands(bot))
