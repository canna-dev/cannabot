import os
import logging
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration management for the Cannabis Stash Tracker Bot."""
    
    # Discord Configuration
    DISCORD_TOKEN: str = os.getenv("DISCORD_TOKEN", "")
    DISCORD_GUILD_ID: Optional[int] = int(guild_id) if (guild_id := os.getenv("DISCORD_GUILD_ID")) else None
    
    # Database Configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://localhost/cannabot_db")
    
    # Bot Features
    ENABLE_SHARING: bool = os.getenv("ENABLE_SHARING", "true").lower() == "true"
    MAX_DAILY_THC_DEFAULT: float = float(os.getenv("MAX_DAILY_THC_DEFAULT", "100"))
    
    # Development Settings
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def validate(cls) -> bool:
        """Validate that required configuration is present."""
        if not cls.DISCORD_TOKEN:
            logging.error("DISCORD_TOKEN is required")
            return False
        
        if not cls.DATABASE_URL:
            logging.error("DATABASE_URL is required")
            return False
        
        return True

# Bioavailability rates based on consumption method
BIOAVAILABILITY_RATES = {
    "smoke": 0.275,      # 27.5% average
    "vaporizer": 0.30,   # 30% average  
    "dab": 0.65,         # 65% average
    "edible": 0.12,      # 12% average
    "tincture": 0.275,   # 27.5% average
    "capsule": 0.12      # 12% average
}

# Cannabis product types
PRODUCT_TYPES = [
    "flower",
    "dab", 
    "edible",
    "tincture",
    "cart",
    "capsule",
    "other"
]

# Consumption methods
CONSUMPTION_METHODS = list(BIOAVAILABILITY_RATES.keys())

# Effect rating scale
EFFECT_RATING_MIN = 1
EFFECT_RATING_MAX = 5

# Common symptoms for tracking
COMMON_SYMPTOMS = [
    "pain",
    "anxiety", 
    "insomnia",
    "nausea",
    "depression",
    "appetite",
    "focus",
    "energy",
    "relaxation"
]
