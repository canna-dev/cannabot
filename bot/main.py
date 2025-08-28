"""Main Discord bot entry point."""

import asyncio
import logging
import sys
import os
from pathlib import Path

import discord
from discord.ext import commands

from bot.config import Config
from bot.database.connection import db

# Fix Unicode encoding issues on Windows
if sys.platform == "win32":
    # Set console output to UTF-8 for Windows
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except (AttributeError, OSError):
        # Fallback for older Python versions or restricted environments
        os.environ['PYTHONIOENCODING'] = 'utf-8'

# Configure logging with UTF-8 encoding for Windows compatibility
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log', encoding='utf-8')
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
        """Load ULTRA-STREAMLINED user-friendly commands - ONLY 1 EXTENSION!"""
        extensions = [
            # 🌿 ONLY Essential Commands - Maximum User-Friendliness!
            "bot.commands.core",  # Contains all 5 essential commands
            
            # 🚫 ALL OTHER EXTENSIONS DISABLED FOR USER-FRIENDLINESS
            # Want more features? Uncomment individual extensions below:
            # "bot.commands.quick",      # Quick actions
            # "bot.commands.voice",      # Voice commands  
            # "bot.commands.mobile",     # Mobile optimization
            # "bot.commands.automation", # Smart automation
            # "bot.commands.achievements", # Community features
        ]
        
        for extension in extensions:
            try:
                await self.load_extension(extension)
                logger.info(f"[SUCCESS] Loaded STREAMLINED extension: {extension}")
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
                name="your stash"
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
