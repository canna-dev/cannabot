"""Help and tutorial command for the consolidated CannaBot."""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class HelpCommands(commands.Cog):
    """Help and tutorial commands."""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="help", description="Get help with CannaBot commands and features")
    @app_commands.describe(
        category="Get help for a specific category of commands"
    )
    @app_commands.choices(category=[
        app_commands.Choice(name="🌿 Getting Started", value="start"),
        app_commands.Choice(name="� Quick Setup Tutorial", value="tutorial"),
        app_commands.Choice(name="�🚬 Consumption Logging", value="consume"),
        app_commands.Choice(name="🔍 Strain Information", value="strain"),
        app_commands.Choice(name="📦 Stash Management", value="stash"),
        app_commands.Choice(name="📊 Reports & Analytics", value="reports"),
        app_commands.Choice(name="💊 Medical Features", value="medical"),
        app_commands.Choice(name="🎯 All Commands", value="all")
    ])
    async def help_command(
        self,
        interaction: discord.Interaction,
        category: Optional[app_commands.Choice[str]] = None
    ):
        """Show help information."""
        try:
            if not category or category.value == "start":
                embed = self._create_getting_started_embed()
            elif category.value == "tutorial":
                embed = self._create_tutorial_embed()
            elif category.value == "consume":
                embed = self._create_consume_help_embed()
            elif category.value == "strain":
                embed = self._create_strain_help_embed()
            elif category.value == "stash":
                embed = self._create_stash_help_embed()
            elif category.value == "reports":
                embed = self._create_reports_help_embed()
            elif category.value == "medical":
                embed = self._create_medical_help_embed()
            elif category.value == "all":
                embed = self._create_all_commands_embed()
            else:
                embed = self._create_getting_started_embed()
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in help command: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while showing help.",
                ephemeral=True
            )
    
    def _create_getting_started_embed(self) -> discord.Embed:
        """Create getting started embed."""
        embed = discord.Embed(
            title="🌿 Welcome to CannaBot!",
            description="Your personal cannabis tracking companion. Here's how to get started:",
            color=0x4CAF50
        )
        
        embed.add_field(
            name="1️⃣ Add to Your Stash",
            value="```/stash add flower 3.5 Blue Dream 22```\n*Add 3.5g of Blue Dream (22% THC) to your stash*",
            inline=False
        )
        
        embed.add_field(
            name="2️⃣ Log Consumption",
            value="```/consume method:Smoking amount:0.5 strain:Blue Dream```\n*Log smoking 0.5g of Blue Dream*",
            inline=False
        )
        
        embed.add_field(
            name="3️⃣ View Your Data",
            value="```/dashboard```\n*See your consumption trends and stats*",
            inline=False
        )
        
        embed.add_field(
            name="🔍 Learn More",
            value="Use `/help category:` to explore specific features:\n" +
                  "• 🚬 Consumption Logging\n" +
                  "• 🔍 Strain Information\n" +
                  "• 📦 Stash Management\n" +
                  "• 📊 Reports & Analytics\n" +
                  "• 💊 Medical Features",
            inline=False
        )
        
        embed.set_footer(text="💡 Tip: Most commands have autocomplete - just start typing!")
        return embed
    
    def _create_tutorial_embed(self) -> discord.Embed:
        """Create interactive tutorial embed."""
        embed = discord.Embed(
            title="🚀 Quick Setup Tutorial",
            description="Follow these steps to get the most out of CannaBot:",
            color=0xFF5722
        )
        
        embed.add_field(
            name="Step 1: Add Your First Strain 📦",
            value="```/stash add flower 3.5 Blue Dream 22```\n" +
                  "**What this does:**\n" +
                  "• Adds 3.5g of Blue Dream flower (22% THC)\n" +
                  "• Enables strain autocomplete in other commands\n" +
                  "• Allows automatic THC% detection",
            inline=False
        )
        
        embed.add_field(
            name="Step 2: Log Your First Session 🚬",
            value="```/consume method:Smoking amount:0.5 strain:Blue Dream effect_rating:4```\n" +
                  "**What this does:**\n" +
                  "• Records consumption with bioavailability calculations\n" +
                  "• Auto-deducts from your stash\n" +
                  "• Tracks effectiveness for future recommendations",
            inline=False
        )
        
        embed.add_field(
            name="Step 3: Explore Strains 🔍",
            value="```/strain action:search query:relaxing```\n" +
                  "**What this does:**\n" +
                  "• Searches 2000+ strain database\n" +
                  "• Shows real user effect percentages\n" +
                  "• Includes photos and detailed descriptions",
            inline=False
        )
        
        embed.add_field(
            name="Step 4: Check Your Progress 📊",
            value="```/dashboard```\n" +
                  "**What this does:**\n" +
                  "• Shows consumption trends and patterns\n" +
                  "• Tracks your most effective strains\n" +
                  "• Displays achievements and milestones",
            inline=False
        )
        
        embed.add_field(
            name="🎯 Pro Tips",
            value="• Use `/help category:` for detailed guides\n" +
                  "• Strain names autocomplete from YOUR stash\n" +
                  "• Rate effects 1-5 to improve recommendations\n" +
                  "• All your data is private and secure",
            inline=False
        )
        
        embed.set_footer(text="🎉 You're ready to go! Try the commands above to get started.")
        return embed
    
    def _create_consume_help_embed(self) -> discord.Embed:
        """Create consumption help embed."""
        embed = discord.Embed(
            title="🚬 Consumption Logging",
            description="Log any type of cannabis consumption with one universal command:",
            color=0xFF9800
        )
        
        embed.add_field(
            name="🔥 Basic Usage",
            value="```/consume method:Smoking amount:0.5```\n*Choose method from dropdown, specify amount*",
            inline=False
        )
        
        embed.add_field(
            name="🌿 With Strain Info",
            value="```/consume method:Edible amount:10 strain:Blue Dream effect_rating:4```\n*Include strain, THC%, and rate the effects*",
            inline=False
        )
        
        embed.add_field(
            name="📋 Available Methods",
            value="• 💨 **Smoking** - Joints, pipes, bongs (grams)\n" +
                  "• 💨 **Vaporizer** - Dry herb vaping (grams)\n" +
                  "• 🔥 **Dabbing** - Concentrates (grams)\n" +
                  "• 🍪 **Edible** - Food products (mg THC)\n" +
                  "• 💧 **Tincture** - Liquid drops (mg THC)\n" +
                  "• 💊 **Capsule** - Pills (mg THC)",
            inline=False
        )
        
        embed.add_field(
            name="🎯 Smart Features",
            value="• **Strain Autocomplete** - Shows your stash strains\n" +
                  "• **Auto THC%** - Fills from stash data\n" +
                  "• **Bioavailability** - Calculates absorbed THC\n" +
                  "• **Effect Rating** - Rate 1-5 stars\n" +
                  "• **Auto Deduction** - Updates your stash automatically",
            inline=False
        )
        
        embed.set_footer(text="💡 Tip: Strain autocomplete shows only strains you have in your stash!")
        return embed
    
    def _create_strain_help_embed(self) -> discord.Embed:
        """Create strain help embed."""
        embed = discord.Embed(
            title="🔍 Strain Information",
            description="Explore our database of 2000+ cannabis strains:",
            color=0x9C27B0
        )
        
        embed.add_field(
            name="🔍 Lookup Specific Strain",
            value="```/strain action:lookup query:Blue Dream```\n*Get detailed info, effects, and photos*",
            inline=False
        )
        
        embed.add_field(
            name="🔎 Search by Effects",
            value="```/strain action:search query:relaxing strain_type:indica```\n*Find strains for specific effects or conditions*",
            inline=False
        )
        
        embed.add_field(
            name="💡 Get Recommendations",
            value="```/strain action:recommend query:pain strain_type:hybrid```\n*Personalized strain suggestions*",
            inline=False
        )
        
        embed.add_field(
            name="🎲 Random Discovery",
            value="```/strain action:random limit:5```\n*Discover new strains randomly*",
            inline=False
        )
        
        embed.add_field(
            name="📊 Database Stats",
            value="```/strain action:stats```\n*View database statistics and top effects*",
            inline=False
        )
        
        embed.add_field(
            name="🎁 Special Features",
            value="• **Daily Featured** - `/strain action:featured`\n" +
                  "• **Surprise Me** - `/strain action:surprise`\n" +
                  "• **Effect Percentages** - Real user data from Leafly\n" +
                  "• **Photos** - Real strain images when available",
            inline=False
        )
        
        embed.set_footer(text="🗃️ Data sourced from Leafly Cannabis Database")
        return embed
    
    def _create_stash_help_embed(self) -> discord.Embed:
        """Create stash help embed."""
        embed = discord.Embed(
            title="📦 Stash Management",
            description="Keep track of your cannabis inventory:",
            color=0x2196F3
        )
        
        embed.add_field(
            name="➕ Add to Stash",
            value="```/stash add flower 3.5 Blue Dream 22```\n*Add product type, amount, strain, THC%*",
            inline=False
        )
        
        embed.add_field(
            name="👀 View Your Stash",
            value="```/stash view```\n*See all your inventory with values and stats*",
            inline=False
        )
        
        embed.add_field(
            name="🎲 Random Picker",
            value="```/stash random```\n*Let the bot pick a random strain from your stash*",
            inline=False
        )
        
        embed.add_field(
            name="🔄 Update Amounts",
            value="```/stash update flower Blue Dream 2.0```\n*Set exact amounts or add/remove*",
            inline=False
        )
        
        embed.add_field(
            name="📋 Product Types",
            value="• **flower** - Dried cannabis buds\n" +
                  "• **concentrate** - Wax, shatter, rosin\n" +
                  "• **edible** - Food products\n" +
                  "• **tincture** - Liquid extracts\n" +
                  "• **capsule** - Pills and capsules",
            inline=False
        )
        
        embed.set_footer(text="💡 Tip: THC% is optional but helps with consumption calculations!")
        return embed
    
    def _create_reports_help_embed(self) -> discord.Embed:
        """Create reports help embed."""
        embed = discord.Embed(
            title="📊 Reports & Analytics",
            description="Track your consumption patterns and trends:",
            color=0x4CAF50
        )
        
        embed.add_field(
            name="📈 Dashboard Overview",
            value="```/dashboard```\n*Your main hub with recent activity and quick stats*",
            inline=False
        )
        
        embed.add_field(
            name="📋 Detailed Reports",
            value="```/reports daily```\n```/reports weekly```\n```/reports monthly```\n*Consumption summaries and trends*",
            inline=False
        )
        
        embed.add_field(
            name="🏆 Achievements",
            value="```/achievements```\n*View progress, milestones, and leaderboards*",
            inline=False
        )
        
        embed.add_field(
            name="📤 Export Data",
            value="```/export csv```\n*Download your data in various formats*",
            inline=False
        )
        
        embed.add_field(
            name="📈 Visualizations",
            value="```/visualization consumption```\n*Charts and graphs of your usage patterns*",
            inline=False
        )
        
        embed.set_footer(text="📊 All your data stays private and secure!")
        return embed
    
    def _create_medical_help_embed(self) -> discord.Embed:
        """Create medical help embed."""
        embed = discord.Embed(
            title="💊 Medical Features",
            description="Track symptoms and find effective strains:",
            color=0xE91E63
        )
        
        embed.add_field(
            name="🏥 Symptom Tracking",
            value="```/symptoms track pain 7 Blue Dream```\n*Track symptoms with severity and effective strains*",
            inline=False
        )
        
        embed.add_field(
            name="🔍 Medical Strain Search",
            value="```/strain action:search query:pain```\n*Find strains reported to help with specific conditions*",
            inline=False
        )
        
        embed.add_field(
            name="📋 Medical Reports",
            value="```/medical-report```\n*Generate reports correlating strains with symptom relief*",
            inline=False
        )
        
        embed.add_field(
            name="🎯 Effectiveness Tracking",
            value="```/effectiveness track```\n*Monitor how well different strains work for you*",
            inline=False
        )
        
        embed.add_field(
            name="⚕️ Common Conditions",
            value="• **Pain** - Chronic pain, headaches\n" +
                  "• **Anxiety** - Stress, panic, PTSD\n" +
                  "• **Insomnia** - Sleep disorders\n" +
                  "• **Depression** - Mood disorders\n" +
                  "• **Inflammation** - Joint pain, arthritis",
            inline=False
        )
        
        embed.set_footer(text="⚠️ This is for tracking only - consult healthcare providers for medical advice")
        return embed
    
    def _create_all_commands_embed(self) -> discord.Embed:
        """Create all commands embed."""
        embed = discord.Embed(
            title="🎯 All CannaBot Commands",
            description="Complete command reference:",
            color=0x607D8B
        )
        
        embed.add_field(
            name="🌿 Core Commands",
            value="• `/consume` - Universal consumption logging\n" +
                  "• `/strain` - All strain operations\n" +
                  "• `/stash` - Stash management\n" +
                  "• `/dashboard` - Main overview",
            inline=True
        )
        
        embed.add_field(
            name="📊 Tracking & Analysis",
            value="• `/symptoms` - Medical symptom tracking\n" +
                  "• `/reports` - Generate reports\n" +
                  "• `/alerts` - Set up alerts\n" +
                  "• `/achievements` - View progress",
            inline=True
        )
        
        embed.add_field(
            name="🔧 Advanced Features",
            value="• `/export` - Data export\n" +
                  "• `/automation` - Batch operations\n" +
                  "• `/visualization` - Charts & graphs\n" +
                  "• `/help` - This help system",
            inline=True
        )
        
        embed.add_field(
            name="💡 Quick Tips",
            value="• Most commands have **autocomplete** - start typing!\n" +
                  "• Use `/help category:` for detailed help\n" +
                  "• Strain names autocomplete from your stash\n" +
                  "• All data is private and secure",
            inline=False
        )
        
        embed.set_footer(text="🚀 CannaBot v2.0 - Now with 59% fewer commands!")
        return embed

async def setup(bot):
    """Setup the cog."""
    await bot.add_cog(HelpCommands(bot))
