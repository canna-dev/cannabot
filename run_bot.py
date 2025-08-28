#!/usr/bin/env python3
"""
CannaBot Launcher Script

This script properly sets up the Python path and launches the bot.
Run this from the project root directory.
"""

import sys
import os
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

# Import and run the bot
if __name__ == "__main__":
    from bot.main import main
    import asyncio
    
    if sys.platform == "win32":
        # Windows-specific event loop policy
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    asyncio.run(main())
