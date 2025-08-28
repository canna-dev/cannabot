"""Quick actions and interactive buttons for enhanced UX."""

import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta

from bot.models.consumption_entry import ConsumptionEntry
from bot.services.consumption_service import ConsumptionService
from bot.services.strain_service import StrainService

class QuickActionView(discord.ui.View):
    """Interactive view with quick action buttons."""
    
    def __init__(self, user_id: int):
        super().__init__(timeout=300)  # 5 minute timeout
        self.user_id = user_id
    
    @discord.ui.button(label="🔄 Repeat Last", style=discord.ButtonStyle.primary, emoji="🔄")
    async def repeat_last_session(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Repeat the user's last consumption session."""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ You can only use your own quick actions.", ephemeral=True)
            return
        
        try:
            # Get last consumption entry
            entries = await ConsumptionEntry.get_user_consumption(self.user_id, limit=1)
            if not entries:
                await interaction.response.send_message("❌ No previous sessions found to repeat.", ephemeral=True)
                return
            
            last_entry = entries[0]
            
            # Create confirmation embed
            embed = discord.Embed(
                title="🔄 Repeat Last Session?",
                description=f"**Method:** {last_entry.method}\n"
                           f"**Amount:** {last_entry.amount}g\n"
                           f"**Strain:** {last_entry.strain or 'Unknown'}\n"
                           f"**THC%:** {last_entry.thc_percentage}%",
                color=0x4CAF50
            )
            
            view = RepeatConfirmView(self.user_id, last_entry)
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)
    
    @discord.ui.button(label="📊 Quick Stats", style=discord.ButtonStyle.secondary, emoji="📊")
    async def quick_stats(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show quick daily/weekly stats."""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ You can only use your own quick actions.", ephemeral=True)
            return
        
        try:
            # Get today's and this week's consumption
            today_summary = await ConsumptionService.get_consumption_summary(self.user_id, days=1)
            week_summary = await ConsumptionService.get_consumption_summary(self.user_id, days=7)
            
            embed = discord.Embed(
                title="⚡ Quick Stats",
                color=0x2196F3
            )
            
            # Today's stats
            today_sessions = today_summary.get('session_count', 0)
            today_thc = today_summary.get('total_thc_mg', 0)
            
            embed.add_field(
                name="📅 Today",
                value=f"**Sessions:** {today_sessions}\n**THC:** {today_thc:.1f}mg",
                inline=True
            )
            
            # Week stats
            week_sessions = week_summary.get('session_count', 0)
            week_thc = week_summary.get('total_thc_mg', 0)
            daily_avg = week_thc / 7 if week_thc > 0 else 0
            
            embed.add_field(
                name="📊 This Week",
                value=f"**Sessions:** {week_sessions}\n**THC:** {week_thc:.1f}mg\n**Daily Avg:** {daily_avg:.1f}mg",
                inline=True
            )
            
            # Quick insights
            if today_sessions == 0:
                insight = "🌱 No sessions today - perfect day for a break!"
            elif today_thc > daily_avg * 1.5:
                insight = "⚠️ Above average consumption today"
            else:
                insight = "✅ Moderate consumption day"
            
            embed.add_field(
                name="💡 Insight",
                value=insight,
                inline=False
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)
    
    @discord.ui.button(label="🔍 Strain Info", style=discord.ButtonStyle.secondary, emoji="🔍")
    async def strain_lookup(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Quick strain lookup modal."""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ You can only use your own quick actions.", ephemeral=True)
            return
        
        modal = QuickStrainModal()
        await interaction.response.send_modal(modal)

class RepeatConfirmView(discord.ui.View):
    """Confirmation view for repeating last session."""
    
    def __init__(self, user_id: int, last_entry):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.last_entry = last_entry
    
    @discord.ui.button(label="✅ Confirm", style=discord.ButtonStyle.success)
    async def confirm_repeat(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Confirm and log the repeated session."""
        try:
            # Create new consumption entry with same details
            new_entry = await ConsumptionService.log_consumption(
                user_id=self.user_id,
                method=self.last_entry.method,
                amount=self.last_entry.amount,
                strain=self.last_entry.strain,
                thc_percentage=self.last_entry.thc_percentage
            )
            
            embed = discord.Embed(
                title="✅ Session Repeated!",
                description=f"Logged {self.last_entry.method} session with {self.last_entry.strain or 'Unknown strain'}",
                color=0x4CAF50
            )
            
            embed.add_field(
                name="📊 Details",
                value=f"**Amount:** {self.last_entry.amount}g\n"
                      f"**THC Absorbed:** {new_entry.absorbed_thc_mg:.1f}mg\n"
                      f"**Time:** {datetime.now().strftime('%I:%M %p')}",
                inline=False
            )
            
            # Clear the view
            self.clear_items()
            await interaction.response.edit_message(embed=embed, view=self)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error repeating session: {str(e)}", ephemeral=True)
    
    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.danger)
    async def cancel_repeat(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Cancel the repeat action."""
        embed = discord.Embed(
            title="❌ Cancelled",
            description="Session repeat cancelled.",
            color=0xF44336
        )
        
        self.clear_items()
        await interaction.response.edit_message(embed=embed, view=self)

class QuickStrainModal(discord.ui.Modal):
    """Quick strain lookup modal."""
    
    def __init__(self):
        super().__init__(title="🔍 Quick Strain Lookup")
    
    strain_name = discord.ui.TextInput(
        label="Strain Name",
        placeholder="Enter strain name (e.g., Blue Dream, OG Kush)",
        required=True,
        max_length=100
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        """Handle strain lookup submission."""
        try:
            strain_info = await StrainService.lookup_strain(self.strain_name.value)
            
            if strain_info:
                embed = discord.Embed(
                    title=f"🌿 {strain_info['name']}",
                    color=0x9C27B0
                )
                
                if strain_info.get('type'):
                    embed.add_field(name="Type", value=strain_info['type'], inline=True)
                if strain_info.get('thc_min') and strain_info.get('thc_max'):
                    embed.add_field(name="THC Range", value=f"{strain_info['thc_min']}-{strain_info['thc_max']}%", inline=True)
                if strain_info.get('effects'):
                    embed.add_field(name="Effects", value=", ".join(strain_info['effects'][:3]), inline=False)
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(
                    f"❌ Strain '{self.strain_name.value}' not found in database.", 
                    ephemeral=True
                )
                
        except Exception as e:
            await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)

class QuickActionsCog(commands.Cog):
    """Quick actions and interactive features."""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="quickbar", description="Show quick action buttons for faster bot interaction")
    async def quickbar(self, interaction: discord.Interaction):
        """Show the quick action bar."""
        embed = discord.Embed(
            title="⚡ Quick Actions",
            description="Use the buttons below for fast access to common actions:",
            color=0x00BCD4
        )
        
        embed.add_field(
            name="🔄 Repeat Last",
            value="Quickly repeat your previous session",
            inline=False
        )
        
        embed.add_field(
            name="📊 Quick Stats",
            value="See today's and weekly stats",
            inline=False
        )
        
        embed.add_field(
            name="🔍 Strain Info",
            value="Quick strain database lookup",
            inline=False
        )
        
        view = QuickActionView(interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

async def setup(bot):
    await bot.add_cog(QuickActionsCog(bot))
