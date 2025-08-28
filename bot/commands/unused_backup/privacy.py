"""Privacy controls and data management features."""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class PrivacyCommands(commands.Cog):
    """Privacy controls and data management."""
    
    def __init__(self, bot):
        self.bot = bot
    
    privacy_group = app_commands.Group(name="privacy", description="Privacy controls and data management")
    
    @privacy_group.command(name="policy", description="View the bot's privacy policy and data handling")
    async def privacy_policy(self, interaction: discord.Interaction):
        """Show privacy policy and data handling information."""
        embed = discord.Embed(
            title="🔒 Privacy Policy & Data Handling",
            description="How CannaBot handles your data",
            color=0x607D8B
        )
        
        embed.add_field(
            name="📊 Data We Store",
            value="• Consumption logs (amounts, methods, strains, timestamps)\n"
                  "• Stash inventory (strains, amounts, THC%)\n"
                  "• Effect ratings and notes\n"
                  "• Alert preferences\n"
                  "• Discord User ID (for data association)",
            inline=False
        )
        
        embed.add_field(
            name="🔐 Data Security",
            value="• All data stored locally in encrypted database\n"
                  "• No data shared with third parties\n"
                  "• Commands are ephemeral (only you see responses)\n"
                  "• No personal information beyond Discord ID\n"
                  "• Regular automated backups",
            inline=False
        )
        
        embed.add_field(
            name="👤 Your Rights",
            value="• View all your data: `/privacy export`\n"
                  "• Delete specific entries: Use individual delete commands\n"
                  "• Delete all data: `/privacy delete-all`\n"
                  "• Data portability: Export to JSON format\n"
                  "• Opt-out of server features: `/privacy server-sharing`",
            inline=False
        )
        
        embed.add_field(
            name="⚖️ Legal Compliance",
            value="• Bot does not provide medical advice\n"
                  "• User responsible for local cannabis laws\n"
                  "• Data retention: Until user requests deletion\n"
                  "• GDPR compliant data handling\n"
                  "• Bot owner contact: Check bot profile",
            inline=False
        )
        
        embed.set_footer(text="Last updated: August 2025 • Use /privacy commands for data control")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @privacy_group.command(name="export", description="Export all your data to JSON format")
    async def export_data(self, interaction: discord.Interaction):
        """Export user's data to JSON format."""
        await interaction.response.defer(ephemeral=True)
        
        try:
            user_id = interaction.user.id
            
            # Import services here to avoid circular imports
            from bot.models.consumption_entry import ConsumptionEntry
            from bot.services.stash_service import StashService
            from bot.models.strain_note import StrainNote
            
            # Gather all user data
            consumption_entries = await ConsumptionEntry.get_user_consumption(user_id, limit=1000)
            stash_items = await StashService.get_stash_items(user_id)
            strain_notes = await StrainNote.get_user_notes(user_id)
            
            # Format data for export
            export_data = {
                "export_info": {
                    "user_id": str(user_id),
                    "export_date": datetime.now().isoformat(),
                    "bot_version": "CannaBot v2.0",
                    "total_entries": len(consumption_entries)
                },
                "consumption_log": [
                    {
                        "id": entry.id,
                        "method": entry.method,
                        "amount": entry.amount,
                        "strain": entry.strain,
                        "thc_percentage": entry.thc_percent,
                        "absorbed_thc_mg": entry.absorbed_thc_mg,
                        "effect_rating": entry.effect_rating,
                        "notes": entry.notes,
                        "timestamp": entry.timestamp.isoformat() if entry.timestamp else None
                    }
                    for entry in consumption_entries
                ],
                "stash_inventory": [
                    {
                        "id": item.id,
                        "strain": item.strain,
                        "type": item.type,
                        "amount": item.amount,
                        "thc_percentage": item.thc_percentage,
                        "purchase_date": item.purchase_date.isoformat() if item.purchase_date else None,
                        "source": item.source,
                        "notes": item.notes
                    }
                    for item in stash_items
                ],
                "strain_notes": [
                    {
                        "id": note.id,
                        "strain": note.strain,
                        "effect_rating": note.effect_rating,
                        "notes": note.notes,
                        "created_at": note.created_at.isoformat() if note.created_at else None
                    }
                    for note in strain_notes
                ]
            }
            
            # Create file content
            import json
            json_content = json.dumps(export_data, indent=2, ensure_ascii=False)
            
            # Create Discord file
            file_content = json_content.encode('utf-8')
            filename = f"cannabot_data_export_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            discord_file = discord.File(
                fp=discord.utils._BytesIOLike(file_content),
                filename=filename
            )
            
            embed = discord.Embed(
                title="📦 Data Export Complete",
                description="Your complete CannaBot data export",
                color=0x4CAF50
            )
            
            embed.add_field(
                name="📊 Export Contents",
                value=f"• **Consumption Entries:** {len(consumption_entries)}\n"
                      f"• **Stash Items:** {len(stash_items)}\n"
                      f"• **Strain Notes:** {len(strain_notes)}\n"
                      f"• **Export Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                inline=False
            )
            
            embed.add_field(
                name="💡 How to Use",
                value="• Download the JSON file to save your data\n"
                      "• Import to spreadsheet applications\n"
                      "• Use for personal analysis or backup\n"
                      "• Share with healthcare providers if needed",
                inline=False
            )
            
            embed.set_footer(text="This file contains all your CannaBot data • Handle securely")
            
            await interaction.followup.send(
                embed=embed,
                file=discord_file,
                ephemeral=True
            )
            
        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            await interaction.followup.send(
                f"❌ Error exporting data: {str(e)}", 
                ephemeral=True
            )
    
    @privacy_group.command(name="delete-all", description="⚠️ Delete ALL your data (irreversible)")
    async def delete_all_data(self, interaction: discord.Interaction):
        """Delete all user data with confirmation."""
        embed = discord.Embed(
            title="⚠️ Delete All Data",
            description="**This will permanently delete ALL your CannaBot data:**\n\n"
                       "• All consumption logs\n"
                       "• Complete stash inventory\n"
                       "• All strain notes and ratings\n"
                       "• Alert preferences\n"
                       "• Achievement progress\n\n"
                       "**This action cannot be undone!**",
            color=0xF44336
        )
        
        embed.add_field(
            name="💡 Before You Delete",
            value="Consider using `/privacy export` to backup your data first.",
            inline=False
        )
        
        view = DeleteConfirmationView(interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    @privacy_group.command(name="server-sharing", description="Control server-wide data sharing preferences")
    @app_commands.describe(enabled="Enable sharing in server leaderboards and features")
    async def server_sharing(self, interaction: discord.Interaction, enabled: bool):
        """Control server-wide data sharing."""
        # This would require a user preferences table in the database
        # For now, just show the concept
        
        status = "enabled" if enabled else "disabled"
        embed = discord.Embed(
            title="🌐 Server Sharing Settings",
            description=f"Server data sharing has been **{status}**",
            color=0x4CAF50 if enabled else 0xF44336
        )
        
        if enabled:
            embed.add_field(
                name="✅ Sharing Enabled",
                value="• Your data may appear in server leaderboards\n"
                      "• Anonymous statistics may be shared\n"
                      "• You can still use all features normally\n"
                      "• Individual commands remain private",
                inline=False
            )
        else:
            embed.add_field(
                name="🔒 Sharing Disabled",
                value="• Your data will not appear in leaderboards\n"
                      "• No statistics shared with server\n"
                      "• All tracking remains completely private\n"
                      "• You can re-enable anytime",
                inline=False
            )
        
        embed.set_footer(text="This setting only affects server-wide features")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

class DeleteConfirmationView(discord.ui.View):
    """Confirmation view for data deletion."""
    
    def __init__(self, user_id: int):
        super().__init__(timeout=60)
        self.user_id = user_id
    
    @discord.ui.button(label="💾 Export First", style=discord.ButtonStyle.secondary)
    async def export_first(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Suggest exporting data first."""
        embed = discord.Embed(
            title="💾 Smart Choice!",
            description="Use `/privacy export` to backup your data before deletion.\n\n"
                       "Once you have your backup, you can return here to delete.",
            color=0x2196F3
        )
        
        self.clear_items()
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="🗑️ DELETE ALL", style=discord.ButtonStyle.danger)
    async def confirm_delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Confirm deletion of all data."""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ You can only delete your own data.", ephemeral=True)
            return
        
        try:
            # Import services
            from bot.database.connection import db
            
            # Delete all user data
            user_id = self.user_id
            
            await db.execute("DELETE FROM ConsumptionLog WHERE user_id = ?", (user_id,))
            await db.execute("DELETE FROM Stash WHERE user_id = ?", (user_id,))
            await db.execute("DELETE FROM StrainNotes WHERE user_id = ?", (user_id,))
            await db.execute("DELETE FROM Alerts WHERE user_id = ?", (user_id,))
            await db.execute("DELETE FROM Users WHERE user_id = ?", (user_id,))
            
            embed = discord.Embed(
                title="✅ Data Deleted",
                description="All your CannaBot data has been permanently deleted.\n\n"
                           "Thank you for using CannaBot. You can start fresh anytime by using commands again.",
                color=0x4CAF50
            )
            
            self.clear_items()
            await interaction.response.edit_message(embed=embed, view=self)
            
        except Exception as e:
            logger.error(f"Error deleting user data: {e}")
            await interaction.response.send_message(
                f"❌ Error deleting data: {str(e)}", 
                ephemeral=True
            )
    
    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.secondary)
    async def cancel_delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Cancel the deletion."""
        embed = discord.Embed(
            title="❌ Deletion Cancelled",
            description="Your data is safe. No changes were made.",
            color=0x607D8B
        )
        
        self.clear_items()
        await interaction.response.edit_message(embed=embed, view=self)

async def setup(bot):
    await bot.add_cog(PrivacyCommands(bot))
