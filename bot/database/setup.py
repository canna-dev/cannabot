"""Database schema creation and migration scripts."""

import asyncio
import logging
from bot.database.connection import db
from bot.config import BIOAVAILABILITY_RATES

logger = logging.getLogger(__name__)

# SQL statements for creating tables
CREATE_TABLES_SQL = """
-- Users table
CREATE TABLE IF NOT EXISTS Users (
    user_id BIGINT PRIMARY KEY,
    timezone TEXT DEFAULT 'UTC',
    share_global BOOLEAN DEFAULT FALSE,
    max_daily_thc_mg FLOAT DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Servers table
CREATE TABLE IF NOT EXISTS Servers (
    server_id BIGINT PRIMARY KEY,
    name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User-Server link table
CREATE TABLE IF NOT EXISTS UserServerLink (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES Users(user_id) ON DELETE CASCADE,
    server_id BIGINT REFERENCES Servers(server_id) ON DELETE CASCADE,
    share_enabled BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, server_id)
);

-- Method absorption rates
CREATE TABLE IF NOT EXISTS MethodAbsorption (
    method TEXT PRIMARY KEY,
    default_absorption FLOAT NOT NULL,
    notes TEXT
);

-- Stash inventory
CREATE TABLE IF NOT EXISTS Stash (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES Users(user_id) ON DELETE CASCADE,
    type TEXT NOT NULL,
    strain TEXT,
    amount FLOAT NOT NULL DEFAULT 0,
    thc_percent FLOAT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Consumption log
CREATE TABLE IF NOT EXISTS ConsumptionLog (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES Users(user_id) ON DELETE CASCADE,
    type TEXT NOT NULL,
    strain TEXT,
    amount FLOAT NOT NULL,
    thc_percent FLOAT,
    method TEXT NOT NULL,
    absorbed_thc_mg FLOAT NOT NULL,
    notes TEXT,
    symptom TEXT,
    effect_rating INTEGER CHECK (effect_rating >= 1 AND effect_rating <= 5),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    shared_in_servers BOOLEAN DEFAULT FALSE
);

-- Strain notes and reviews
CREATE TABLE IF NOT EXISTS StrainNotes (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES Users(user_id) ON DELETE CASCADE,
    strain TEXT NOT NULL,
    effect_rating INTEGER CHECK (effect_rating >= 1 AND effect_rating <= 5),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User alerts
CREATE TABLE IF NOT EXISTS Alerts (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES Users(user_id) ON DELETE CASCADE,
    type TEXT NOT NULL,
    target_type TEXT,
    threshold FLOAT,
    message TEXT,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Symptom tracking (optional)
CREATE TABLE IF NOT EXISTS SymptomTracking (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES Users(user_id) ON DELETE CASCADE,
    symptom TEXT NOT NULL,
    severity INTEGER CHECK (severity >= 1 AND severity <= 10),
    notes TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Enhanced medical entries
CREATE TABLE IF NOT EXISTS MedicalEntries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    entry_type TEXT NOT NULL,
    symptoms TEXT,
    severity INTEGER,
    effectiveness_rating INTEGER,
    symptoms_improved TEXT,
    side_effects TEXT,
    consumption_id INTEGER,
    notes TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users (user_id),
    FOREIGN KEY (consumption_id) REFERENCES ConsumptionLog (id)
);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_consumption_user_timestamp ON ConsumptionLog(user_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_stash_user_type ON Stash(user_id, type);
CREATE INDEX IF NOT EXISTS idx_strain_notes_user_strain ON StrainNotes(user_id, strain);
CREATE INDEX IF NOT EXISTS idx_alerts_user_active ON Alerts(user_id, active);
CREATE INDEX IF NOT EXISTS idx_symptom_tracking_user_timestamp ON SymptomTracking(user_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_medical_entries_user_timestamp ON MedicalEntries(user_id, timestamp);
"""

# Insert default bioavailability rates
INSERT_BIOAVAILABILITY_SQL = """
INSERT INTO MethodAbsorption (method, default_absorption, notes) VALUES
    ('smoke', $1, 'Average bioavailability for smoking cannabis'),
    ('vaporizer', $2, 'Average bioavailability for vaporizing cannabis'),  
    ('dab', $3, 'Average bioavailability for dabbing concentrates'),
    ('edible', $4, 'Average bioavailability for oral consumption'),
    ('tincture', $5, 'Average bioavailability for sublingual tinctures'),
    ('capsule', $6, 'Average bioavailability for oral capsules')
ON CONFLICT (method) DO UPDATE SET
    default_absorption = EXCLUDED.default_absorption,
    notes = EXCLUDED.notes;
"""

async def create_tables():
    """Create all database tables."""
    try:
        await db.execute(CREATE_TABLES_SQL)
        logger.info("Database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        return False

async def insert_default_data():
    """Insert default bioavailability rates."""
    try:
        await db.execute(
            INSERT_BIOAVAILABILITY_SQL,
            BIOAVAILABILITY_RATES['smoke'],
            BIOAVAILABILITY_RATES['vaporizer'],
            BIOAVAILABILITY_RATES['dab'],
            BIOAVAILABILITY_RATES['edible'],
            BIOAVAILABILITY_RATES['tincture'],
            BIOAVAILABILITY_RATES['capsule']
        )
        logger.info("Default bioavailability data inserted successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to insert default data: {e}")
        return False

async def setup_database():
    """Setup the complete database schema."""
    logger.info("Setting up database...")
    
    # Initialize database connection
    if not await db.initialize():
        logger.error("Failed to initialize database connection")
        return False
    
    # Create tables
    if not await create_tables():
        logger.error("Failed to create database tables")
        return False
    
    # Insert default data
    if not await insert_default_data():
        logger.error("Failed to insert default data")
        return False
    
    logger.info("Database setup completed successfully")
    return True

if __name__ == "__main__":
    asyncio.run(setup_database())
