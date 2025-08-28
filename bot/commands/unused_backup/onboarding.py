"""Smart onboarding and welcome flow for new users."""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
import logging
from datetime import datetime

from bot.services.consumption_service import ConsumptionService
from bot.services.stash_service import StashService

logger = logging.getLogger(__name__)

class OnboardingCommands(commands.Cog):
    """Smart onboarding and welcome flow."""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="welcome", description="🌟 Welcome! Get started with CannaBot in 2 minutes")
    async def welcome(self, interaction: discord.Interaction):
        """Interactive welcome and onboarding flow."""
        user_id = interaction.user.id
        
        # Check if user is new
        try:
            entries = await ConsumptionService.get_consumption_summary(user_id, days=30)
            is_new_user = entries.get('session_count', 0) == 0
        except:
            is_new_user = True
        
        if is_new_user:
            embed = discord.Embed(
                title="🌟 Welcome to CannaBot!",
                description="Your personal cannabis tracking companion. Let's get you set up in just 2 minutes!",
                color=0x4CAF50
            )
            
            embed.add_field(
                name="✨ What CannaBot Does",
                value="• **Track consumption** with automatic THC calculations\n"
                      "• **Manage your stash** inventory\n"
                      "• **Find strain info** from 3000+ strain database\n"
                      "• **Generate reports** and insights\n"
                      "• **Stay organized** with alerts and analytics",
                inline=False
            )
            
            embed.add_field(
                name="🚀 Quick Start Steps",
                value="**1.** Click `Start Setup` below\n"
                      "**2.** Add some stash items\n"
                      "**3.** Log your first session\n"
                      "**4.** Explore features with `/help`",
                inline=False
            )
            
            view = WelcomeSetupView(user_id)
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        else:
            # Returning user
            embed = discord.Embed(
                title="👋 Welcome Back!",
                description="You're already set up with CannaBot. Here's what's new:",
                color=0x2196F3
            )
            
            # Show recent activity
            recent_sessions = entries.get('session_count', 0)
            embed.add_field(
                name="📊 Your Recent Activity",
                value=f"**{recent_sessions}** sessions logged this month\n"
                      f"Use `/status` for a complete overview",
                inline=False
            )
            
            # Show new features
            embed.add_field(
                name="🆕 New Features",
                value="• **Interactive buttons** - Try `/quickbar`\n"
                      "• **Visual status** - Check out `/status`\n"
                      "• **Privacy controls** - See `/privacy`\n"
                      "• **Enhanced help** - Use `/help tutorial`",
                inline=False
            )
            
            view = ReturningUserView(user_id)
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    @app_commands.command(name="setup", description="🔧 Guided setup for new users")
    async def guided_setup(self, interaction: discord.Interaction):
        """Start the guided setup process."""
        embed = discord.Embed(
            title="🔧 Guided Setup",
            description="Let's set up your CannaBot experience step by step!",
            color=0x9C27B0
        )
        
        embed.add_field(
            name="📋 Setup Checklist",
            value="☐ Add stash items\n"
                  "☐ Log first consumption\n"
                  "☐ Set up alerts (optional)\n"
                  "☐ Explore strain database",
            inline=False
        )
        
        view = GuidedSetupView(interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class WelcomeSetupView(discord.ui.View):
    """Interactive welcome setup flow."""
    
    def __init__(self, user_id: int):
        super().__init__(timeout=600)  # 10 minute timeout
        self.user_id = user_id
        self.setup_step = 0
    
    @discord.ui.button(label="🚀 Start Setup", style=discord.ButtonStyle.success, emoji="🚀")
    async def start_setup(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Begin the setup process."""
        embed = discord.Embed(
            title="🚀 Setup Step 1: Add Your First Stash Item",
            description="Let's add some cannabis to your digital stash!",
            color=0x4CAF50
        )
        
        embed.add_field(
            name="💡 How to Add Stash",
            value="Use this command:\n"
                  "```/stash add strain:Blue Dream type:flower amount:3.5 thc:22```",
            inline=False
        )
        
        embed.add_field(
            name="🌿 Example Strains to Try",
            value="• **Blue Dream** (Hybrid)\n"
                  "• **OG Kush** (Indica)\n"
                  "• **Sour Diesel** (Sativa)\n"
                  "• **Girl Scout Cookies** (Hybrid)",
            inline=False
        )
        
        # Update buttons
        button.disabled = True
        self.add_item(SetupNextButton(self.user_id, step=2))
        
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="📚 Learn More", style=discord.ButtonStyle.secondary, emoji="📚")
    async def learn_more(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show more detailed information."""
        embed = discord.Embed(
            title="📚 About CannaBot",
            description="CannaBot helps you track cannabis consumption responsibly",
            color=0x2196F3
        )
        
        embed.add_field(
            name="🧮 Smart Calculations",
            value="Automatic bioavailability calculations:\n"
                  "• Smoking: 27.5% absorption\n"
                  "• Vaping: 30% absorption\n"
                  "• Edibles: 12% absorption\n"
                  "• Dabbing: 65% absorption",
            inline=False
        )
        
        embed.add_field(
            name="🔒 Privacy First",
            value="• All data stored securely\n"
                  "• Commands are private (ephemeral)\n"
                  "• Full data control with `/privacy`\n"
                  "• No sharing without permission",
            inline=False
        )
        
        await interaction.response.edit_message(embed=embed, view=self)

class SetupNextButton(discord.ui.Button):
    """Dynamic next step button."""
    
    def __init__(self, user_id: int, step: int):
        super().__init__(label=f"➡️ Step {step}", style=discord.ButtonStyle.primary)
        self.user_id = user_id
        self.step = step
    
    async def callback(self, interaction: discord.Interaction):
        if self.step == 2:
            embed = discord.Embed(
                title="🍃 Setup Step 2: Log Your First Session",
                description="Now let's log a consumption session!",
                color=0x4CAF50
            )
            
            embed.add_field(
                name="💡 How to Log Consumption",
                value="Use this command:\n"
                      "```/consume method:Smoking amount:0.3 strain:Blue Dream thc:22```",
                inline=False
            )
            
            embed.add_field(
                name="🎯 Pro Tips",
                value="• Start with smaller amounts\n"
                      "• Rate effects 1-5 stars\n"
                      "• Add notes about the experience\n"
                      "• Check `/status` after logging",
                inline=False
            )
            
            # Add final step button
            view = discord.ui.View()
            view.add_item(SetupNextButton(self.user_id, step=3))
            
            await interaction.response.edit_message(embed=embed, view=view)
            
        elif self.step == 3:
            embed = discord.Embed(
                title="🎉 Setup Complete!",
                description="You're all set up with CannaBot! Here's what to explore next:",
                color=0x4CAF50
            )
            
            embed.add_field(
                name="🚀 Quick Commands to Try",
                value="• `/status` - See your tracking overview\n"
                      "• `/quickbar` - Interactive quick actions\n"
                      "• `/strain action:recommend` - Get strain suggestions\n"
                      "• `/dashboard` - View detailed analytics\n"
                      "• `/help` - Get help anytime",
                inline=False
            )
            
            embed.add_field(
                name="💡 Next Steps",
                value="• Set up alerts with `/alerts`\n"
                      "• Explore the strain database\n"
                      "• Try different consumption methods\n"
                      "• Check out reports and insights",
                inline=False
            )
            
            # Final view with useful buttons
            view = PostSetupView(self.user_id)
            await interaction.response.edit_message(embed=embed, view=view)

class PostSetupView(discord.ui.View):
    """Post-setup actions for new users."""
    
    def __init__(self, user_id: int):
        super().__init__(timeout=300)
        self.user_id = user_id
    
    @discord.ui.button(label="📊 View Status", style=discord.ButtonStyle.primary, emoji="📊")
    async def view_status(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Quick access to status command."""
        await interaction.response.send_message(
            "Use `/status` to see your tracking overview with visual indicators!",
            ephemeral=True
        )
    
    @discord.ui.button(label="⚡ Quick Actions", style=discord.ButtonStyle.secondary, emoji="⚡")
    async def quick_actions(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Quick access to quickbar."""
        await interaction.response.send_message(
            "Try `/quickbar` for interactive buttons and quick actions!",
            ephemeral=True
        )
    
    @discord.ui.button(label="📚 Get Help", style=discord.ButtonStyle.secondary, emoji="📚")
    async def get_help(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Quick access to help."""
        await interaction.response.send_message(
            "Use `/help` to explore all features, or `/help tutorial` for guided learning!",
            ephemeral=True
        )

class ReturningUserView(discord.ui.View):
    """Actions for returning users."""
    
    def __init__(self, user_id: int):
        super().__init__(timeout=300)
        self.user_id = user_id
    
    @discord.ui.button(label="📊 Status", style=discord.ButtonStyle.primary, emoji="📊")
    async def view_status(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Check `/status` for your overview!", ephemeral=True)
    
    @discord.ui.button(label="🆕 New Features", style=discord.ButtonStyle.secondary, emoji="🆕")
    async def new_features(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🆕 What's New in CannaBot",
            description="Recent improvements and new features:",
            color=0x9C27B0
        )
        
        embed.add_field(
            name="⚡ Interactive Features",
            value="• `/quickbar` - Quick action buttons\n"
                  "• `/status` - Visual dashboard\n"
                  "• Interactive confirmations and tips",
            inline=False
        )
        
        embed.add_field(
            name="🔒 Privacy & Control",
            value="• `/privacy` - Complete data control\n"
                  "• Data export functionality\n"
                  "• Enhanced privacy settings",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

class GuidedSetupView(discord.ui.View):
    """Full guided setup experience."""
    
    def __init__(self, user_id: int):
        super().__init__(timeout=600)
        self.user_id = user_id
    
    @discord.ui.button(label="📦 Add Stash", style=discord.ButtonStyle.success, emoji="📦")
    async def add_stash_guide(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Guide for adding stash."""
        embed = discord.Embed(
            title="📦 Adding Your Cannabis Stash",
            description="Let's add your first stash item!",
            color=0x2196F3
        )
        
        embed.add_field(
            name="🌿 Basic Command",
            value="```/stash add strain:\"Blue Dream\" type:flower amount:3.5 thc:22```",
            inline=False
        )
        
        embed.add_field(
            name="📋 What Each Part Means",
            value="• **strain**: Name of the cannabis strain\n"
                  "• **type**: flower, edible, concentrate, etc.\n"
                  "• **amount**: How much you have (grams/mg)\n"
                  "• **thc**: THC percentage (if known)",
            inline=False
        )
        
        embed.add_field(
            name="💡 Pro Tips",
            value="• Use quotes for strain names with spaces\n"
                  "• THC% is optional but helpful for tracking\n"
                  "• You can add multiple items anytime\n"
                  "• View your stash with `/stash list`",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="🍃 Log Session", style=discord.ButtonStyle.success, emoji="🍃")
    async def log_session_guide(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Guide for logging consumption."""
        embed = discord.Embed(
            title="🍃 Logging Your First Session",
            description="Track your cannabis consumption accurately!",
            color=0x4CAF50
        )
        
        embed.add_field(
            name="🌿 Basic Command",
            value="```/consume method:Smoking amount:0.3 strain:\"Blue Dream\" thc:22```",
            inline=False
        )
        
        embed.add_field(
            name="⚡ Method Options",
            value="• **Smoking** (27.5% absorption)\n"
                  "• **Vaporizer** (30% absorption)\n"
                  "• **Dabbing** (65% absorption)\n"
                  "• **Edible** (12% absorption)\n"
                  "• **Tincture** (27.5% absorption)\n"
                  "• **Capsule** (12% absorption)",
            inline=False
        )
        
        embed.add_field(
            name="🎯 Optional Enhancements",
            value="• Add `effect_rating:4` (1-5 stars)\n"
                  "• Include `notes:\"Relaxing evening session\"`\n"
                  "• Bot calculates absorbed THC automatically",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(OnboardingCommands(bot))
