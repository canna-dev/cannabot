"""Main Discord bot entry point."""

import asyncio
import logging
import sys
from pathlib import Path

import discord
from discord.ext import commands

from bot.config import Config
from bot.database.connection import db

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log')
    ]
)

logger = logging.getLogger(__name__)

class CannabotBot(commands.Bot):
    """Main bot class for Cannabis Stash Tracker."""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = False  # Don't require privileged intent
        
        super().__init__(
            command_prefix="!",  # Prefix for text commands (we'll mainly use slash commands)
            intents=intents,
            help_command=None
        )
    
    async def setup_hook(self):
        """Setup hook called when bot is starting up."""
        logger.info("Setting up bot...")
        
        # Initialize database
        if not await db.initialize():
            logger.error("Failed to initialize database connection")
            await self.close()
            return
        
        # Load command cogs
        await self.load_extensions()
        
        # Sync slash commands in development
        if Config.DEBUG and Config.DISCORD_GUILD_ID:
            guild = discord.Object(id=Config.DISCORD_GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            logger.info(f"Synced commands to guild {Config.DISCORD_GUILD_ID}")
        else:
            await self.tree.sync()
            logger.info("Synced commands globally")
    
    async def load_extensions(self):
        """Load minimal command set - CONSOLIDATED VERSION."""
        extensions = [
            # 🚀 MINIMAL SETUP - ONLY 3 ESSENTIAL COMMANDS!
            "bot.commands.core",            # 📱 ALL CORE: help + consume + strain + stash + analytics
            # 
            # � ALL OTHER COMMANDS DISABLED FOR MINIMAL SETUP
            # (Total reduction: 31 commands → 1 mega-command!)
            #
            # Disabled old commands:
            # "bot.commands.help", "bot.commands.consume", "bot.commands.strain", "bot.commands.stash",
            # "bot.commands.dashboard", "bot.commands.analytics", "bot.commands.onboarding",
            # "bot.commands.smart_automation", "bot.commands.advanced_analytics", "bot.commands.visual_polish",
            # "bot.commands.privacy", "bot.commands.enhanced_medical", "bot.commands.reports", 
            # "bot.commands.alerts", "bot.commands.achievements", "bot.commands.export",
            # "bot.commands.automation", "bot.commands.visualization", "bot.commands.performance",
            # "bot.commands.branding", "bot.commands.security", "bot.commands.ai_predictions",
            # "bot.commands.community", "bot.commands.mobile_optimized", "bot.commands.quick_actions"
        ]
        
        for extension in extensions:
            try:
                await self.load_extension(extension)
                logger.info(f"Loaded extension: {extension}")
            except Exception as e:
                logger.error(f"Failed to load extension {extension}: {e}")
    
    async def on_ready(self):
        """Called when bot is ready."""
        logger.info(f"Bot is ready! Logged in as {self.user}")
        logger.info(f"Bot is in {len(self.guilds)} guilds")
        
        # Set bot status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="your stash 🌿"
            )
        )
    
    async def on_command_error(self, ctx, error):
        """Handle command errors."""
        if isinstance(error, commands.CommandNotFound):
            return  # Ignore command not found errors
        
        logger.error(f"Command error: {error}")
        
        if ctx.interaction:
            if not ctx.interaction.response.is_done():
                await ctx.interaction.response.send_message(
                    f"❌ An error occurred: {str(error)}", 
                    ephemeral=True
                )
    
    async def close(self):
        """Clean shutdown."""
        logger.info("Shutting down bot...")
        await db.close()
        await super().close()

async def main():
    """Main bot function."""
    # Validate configuration
    if not Config.validate():
        logger.error("Invalid configuration, exiting")
        return
    
    # Create and run bot
    bot = CannabotBot()
    
    try:
        await bot.start(Config.DISCORD_TOKEN)
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
    finally:
        await bot.close()

if __name__ == "__main__":
    if sys.platform == "win32":
        # Windows-specific event loop policy
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    asyncio.run(main())
