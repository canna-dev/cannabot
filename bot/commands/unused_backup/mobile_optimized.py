"""Mobile-optimized shortcuts and quick commands."""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
import logging
from datetime import datetime

from bot.services.consumption_service import ConsumptionService
from bot.services.stash_service import StashService

logger = logging.getLogger(__name__)

class MobileOptimizedCommands(commands.Cog):
    """Mobile-optimized shortcuts and quick commands."""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="quick", description="📱 Super fast consumption logging for mobile users")
    @app_commands.describe(
        preset="Quick preset for common consumption patterns"
    )
    @app_commands.choices(preset=[
        app_commands.Choice(name="💨 Quick Smoke (0.3g)", value="smoke_quick"),
        app_commands.Choice(name="💨 Light Vape (0.2g)", value="vape_light"),
        app_commands.Choice(name="🔥 Small Dab (0.05g)", value="dab_small"),
        app_commands.Choice(name="🍪 Low Edible (5mg)", value="edible_low"),
        app_commands.Choice(name="🍪 Standard Edible (10mg)", value="edible_standard"),
        app_commands.Choice(name="💧 Tincture Drop (2.5mg)", value="tincture_drop"),
        app_commands.Choice(name="🔄 Repeat Last", value="repeat_last"),
        app_commands.Choice(name="⚡ Custom Quick", value="custom")
    ])
    async def quick_log(
        self,
        interaction: discord.Interaction,
        preset: app_commands.Choice[str],
        strain: Optional[str] = None,
        rating: Optional[app_commands.Range[int, 1, 5]] = None
    ):
        """Mobile-optimized quick logging."""
        await interaction.response.defer(ephemeral=True)
        
        try:
            user_id = interaction.user.id
            
            # Handle repeat last
            if preset.value == "repeat_last":
                entries = await ConsumptionService.get_user_consumption(user_id, limit=1)
                if not entries:
                    await interaction.followup.send("❌ No previous sessions to repeat.", ephemeral=True)
                    return
                
                last_entry = entries[0]
                preset_data = {
                    'method': last_entry.method,
                    'amount': last_entry.amount,
                    'strain': last_entry.strain,
                    'thc_percent': last_entry.thc_percent
                }
            else:
                # Get preset data
                preset_data = self._get_preset_data(preset.value)
            
            # Override with user inputs
            if strain:
                preset_data['strain'] = strain
            
            # Log consumption
            entry = await ConsumptionService.log_consumption(
                user_id=user_id,
                method=preset_data['method'],
                amount=preset_data['amount'],
                strain=preset_data.get('strain'),
                thc_percent=preset_data.get('thc_percent', 20),  # Default 20%
                effect_rating=rating,
                product_type=self._get_product_type_from_method(preset_data['method'])
            )
            
            # Quick success response
            embed = discord.Embed(
                title="✅ Quick Log Complete!",
                description=f"**{preset_data['method']}** • {preset_data['amount']}{'g' if preset_data['method'] in ['smoke', 'vaporizer', 'dab'] else 'mg'}",
                color=0x4CAF50
            )
            
            if strain:
                embed.add_field(name="🌿 Strain", value=strain, inline=True)
            if rating:
                embed.add_field(name="⭐ Rating", value=f"{'⭐' * rating} {rating}/5", inline=True)
            
            embed.add_field(
                name="🧠 THC Absorbed",
                value=f"{entry.absorbed_thc_mg:.1f}mg",
                inline=True
            )
            
            # Add quick action buttons
            view = QuickLogFollowUpView(user_id, preset_data['method'])
            
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Quick log error: {e}")
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)
    
    def _get_preset_data(self, preset_value: str) -> dict:
        """Get preset consumption data."""
        presets = {
            'smoke_quick': {'method': 'smoke', 'amount': 0.3, 'thc_percent': 20},
            'vape_light': {'method': 'vaporizer', 'amount': 0.2, 'thc_percent': 22},
            'dab_small': {'method': 'dab', 'amount': 0.05, 'thc_percent': 70},
            'edible_low': {'method': 'edible', 'amount': 5, 'thc_percent': None},
            'edible_standard': {'method': 'edible', 'amount': 10, 'thc_percent': None},
            'tincture_drop': {'method': 'tincture', 'amount': 2.5, 'thc_percent': None}
        }
        return presets.get(preset_value, presets['smoke_quick'])
    
    def _get_product_type_from_method(self, method: str) -> str:
        """Map method to product type."""
        mapping = {
            'smoke': 'flower',
            'vaporizer': 'flower', 
            'dab': 'concentrate',
            'edible': 'edible',
            'tincture': 'tincture',
            'capsule': 'capsule'
        }
        return mapping.get(method, 'flower')
    
    @app_commands.command(name="now", description="📱 What's happening right now - quick status")
    async def right_now(self, interaction: discord.Interaction):
        """Ultra-quick status for mobile."""
        await interaction.response.defer(ephemeral=True)
        
        try:
            user_id = interaction.user.id
            
            # Get today's data
            today_summary = await ConsumptionService.get_consumption_summary(user_id, days=1)
            sessions_today = today_summary.get('session_count', 0)
            thc_today = today_summary.get('total_thc_mg', 0)
            
            # Quick status emoji
            if sessions_today == 0:
                status_emoji = "🌱"
                status_text = "Sober day"
            elif sessions_today == 1:
                status_emoji = "🍃"
                status_text = "Light usage"
            elif sessions_today <= 3:
                status_emoji = "💨"
                status_text = "Active day"
            else:
                status_emoji = "🌿"
                status_text = "High usage"
            
            embed = discord.Embed(
                title=f"{status_emoji} Right Now",
                description=f"**{status_text}** • {sessions_today} sessions • {thc_today:.0f}mg THC",
                color=0x4CAF50 if sessions_today <= 2 else 0xFF9800
            )
            
            # Time since last session
            if sessions_today > 0:
                entries = await ConsumptionService.get_user_consumption(user_id, limit=1)
                if entries:
                    last_session = entries[0]
                    if last_session.timestamp:
                        time_since = datetime.now() - last_session.timestamp
                        hours_since = time_since.total_seconds() / 3600
                        
                        if hours_since < 1:
                            time_text = f"{int(time_since.total_seconds() / 60)}m ago"
                        elif hours_since < 24:
                            time_text = f"{hours_since:.1f}h ago"
                        else:
                            time_text = f"{int(hours_since / 24)}d ago"
                        
                        embed.add_field(
                            name="⏰ Last Session",
                            value=f"{time_text}\n{last_session.method} • {last_session.strain or 'Unknown'}",
                            inline=False
                        )
            
            # Quick actions
            view = MobileQuickActionsView(user_id)
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Right now error: {e}")
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)
    
    @app_commands.command(name="go", description="📱 Ultra-fast actions - mobile shortcuts")
    @app_commands.describe(action="Quick action to perform")
    @app_commands.choices(action=[
        app_commands.Choice(name="📊 Today's Stats", value="stats"),
        app_commands.Choice(name="📦 Check Stash", value="stash"),
        app_commands.Choice(name="🔍 Find Strain", value="strain"),
        app_commands.Choice(name="⚡ Quick Log", value="log"),
        app_commands.Choice(name="📈 This Week", value="week"),
        app_commands.Choice(name="🎯 Set Reminder", value="remind")
    ])
    async def mobile_go(self, interaction: discord.Interaction, action: app_commands.Choice[str]):
        """Ultra-fast mobile actions."""
        if action.value == "stats":
            # Redirect to status
            await interaction.response.send_message("📊 Use `/now` for quick status or `/status` for detailed view!", ephemeral=True)
        elif action.value == "stash":
            # Quick stash overview
            await self._show_quick_stash(interaction)
        elif action.value == "strain":
            # Quick strain search modal
            await interaction.response.send_modal(QuickStrainSearchModal())
        elif action.value == "log":
            # Quick log options
            await self._show_quick_log_options(interaction)
        elif action.value == "week":
            # Weekly summary
            await self._show_week_summary(interaction)
        elif action.value == "remind":
            # Quick reminder setup
            await interaction.response.send_message("⏰ Use `/alerts add` to set up consumption reminders!", ephemeral=True)
    
    async def _show_quick_stash(self, interaction: discord.Interaction):
        """Show quick stash overview."""
        try:
            user_id = interaction.user.id
            stash_items = await StashService.get_stash_items(user_id)
            
            if not stash_items:
                await interaction.response.send_message("📦 Your stash is empty! Use `/stash add` to add items.", ephemeral=True)
                return
            
            total_weight = sum(item.amount for item in stash_items if item.amount)
            strain_count = len(set(item.strain for item in stash_items if item.strain))
            
            # Quick status
            if total_weight > 5:
                status = "📦 Well stocked"
            elif total_weight > 1:
                status = "📦 Moderate supply"
            else:
                status = "⚠️ Running low"
            
            embed = discord.Embed(
                title="📦 Quick Stash Check",
                description=f"{status} • {total_weight:.1f}g • {strain_count} strains",
                color=0x2196F3
            )
            
            # Show top 3 strains
            top_strains = sorted(stash_items, key=lambda x: x.amount or 0, reverse=True)[:3]
            strain_list = "\n".join([
                f"• **{item.strain}**: {item.amount:.1f}g" 
                for item in top_strains if item.strain and item.amount
            ])
            
            if strain_list:
                embed.add_field(name="🌿 Top Strains", value=strain_list, inline=False)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)
    
    async def _show_quick_log_options(self, interaction: discord.Interaction):
        """Show quick logging options."""
        embed = discord.Embed(
            title="⚡ Quick Log Options",
            description="Choose your preferred quick logging method:",
            color=0x4CAF50
        )
        
        embed.add_field(
            name="📱 Mobile Commands",
            value="• `/quick preset:Quick Smoke` - Fastest\n"
                  "• `/quick preset:Repeat Last` - Repeat session\n"
                  "• `/consume` - Full control",
            inline=False
        )
        
        view = QuickLogOptionsView(interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    async def _show_week_summary(self, interaction: discord.Interaction):
        """Show quick weekly summary."""
        try:
            user_id = interaction.user.id
            week_summary = await ConsumptionService.get_consumption_summary(user_id, days=7)
            
            sessions = week_summary.get('session_count', 0)
            thc = week_summary.get('total_thc_mg', 0)
            daily_avg = thc / 7 if thc > 0 else 0
            
            embed = discord.Embed(
                title="📈 This Week",
                description=f"**{sessions}** sessions • **{thc:.0f}mg** THC • **{daily_avg:.0f}mg** daily avg",
                color=0x9C27B0
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)

class QuickLogFollowUpView(discord.ui.View):
    """Follow-up actions after quick logging."""
    
    def __init__(self, user_id: int, method: str):
        super().__init__(timeout=180)
        self.user_id = user_id
        self.method = method
    
    @discord.ui.button(label="🔄 Log Another", style=discord.ButtonStyle.secondary, emoji="🔄")
    async def log_another(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Use `/quick` again for another quick log!", ephemeral=True)
    
    @discord.ui.button(label="📊 Status", style=discord.ButtonStyle.primary, emoji="📊")
    async def view_status(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Check `/now` for quick status or `/status` for detailed view!", ephemeral=True)

class MobileQuickActionsView(discord.ui.View):
    """Quick actions for mobile users."""
    
    def __init__(self, user_id: int):
        super().__init__(timeout=300)
        self.user_id = user_id
    
    @discord.ui.button(label="⚡ Quick Log", style=discord.ButtonStyle.success, emoji="⚡")
    async def quick_log(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Use `/quick` for super-fast logging with presets!", ephemeral=True)
    
    @discord.ui.button(label="📦 Stash", style=discord.ButtonStyle.secondary, emoji="📦")
    async def check_stash(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Use `/go action:Check Stash` for quick stash overview!", ephemeral=True)

class QuickStrainSearchModal(discord.ui.Modal):
    """Quick strain search for mobile."""
    
    def __init__(self):
        super().__init__(title="🔍 Quick Strain Search")
    
    strain_query = discord.ui.TextInput(
        label="Strain Name or Effect",
        placeholder="Blue Dream, relaxing, energetic...",
        required=True,
        max_length=50
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"🔍 Search for '{self.strain_query.value}' using `/strain action:search query:{self.strain_query.value}`",
            ephemeral=True
        )

class QuickLogOptionsView(discord.ui.View):
    """Quick logging options."""
    
    def __init__(self, user_id: int):
        super().__init__(timeout=300)
        self.user_id = user_id
    
    @discord.ui.button(label="💨 Smoke", style=discord.ButtonStyle.primary, emoji="💨")
    async def quick_smoke(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Use `/quick preset:Quick Smoke` for fast smoking log!", ephemeral=True)
    
    @discord.ui.button(label="🍪 Edible", style=discord.ButtonStyle.primary, emoji="🍪")
    async def quick_edible(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Use `/quick preset:Standard Edible` for edible logging!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(MobileOptimizedCommands(bot))
