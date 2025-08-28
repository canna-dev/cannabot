import aiosqlite
import logging
from typing import Optional, Any, List
from bot.config import Config

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages database connections and operations for SQLite."""
    
    def __init__(self):
        self.db_path: Optional[str] = None
    
    async def initialize(self) -> bool:
        """Initialize the database connection."""
        try:
            # Extract database path from URL
            database_url = Config.DATABASE_URL
            if database_url.startswith("sqlite:///"):
                self.db_path = database_url.replace("sqlite:///", "")
            else:
                # Fallback for development
                self.db_path = "cannabot.db"
            
            # Test connection
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("SELECT 1")
            
            logger.info(f"Database connection initialized: {self.db_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            return False
    
    async def close(self):
        """Close the database connection."""
        logger.info("Database connection closed")
    
    async def execute(self, query: str, *args) -> Any:
        """Execute a query that doesn't return results."""
        if not self.db_path:
            raise RuntimeError("Database not initialized")
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(query, args)
            await db.commit()
    
    async def fetch(self, query: str, *args) -> List[Any]:
        """Execute a query that returns multiple rows."""
        if not self.db_path:
            raise RuntimeError("Database not initialized")
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(query, args)
            rows = await cursor.fetchall()
            # Convert rows to dict and handle datetime conversion
            result = []
            for row in rows:
                row_dict = dict(row)
                # Convert timestamp strings back to datetime objects
                for key, value in row_dict.items():
                    if key in ['timestamp', 'created_at', 'updated_at'] and isinstance(value, str):
                        try:
                            from datetime import datetime
                            row_dict[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                        except:
                            pass
                result.append(row_dict)
            return result
    
    async def fetchrow(self, query: str, *args) -> Optional[Any]:
        """Execute a query that returns a single row."""
        if not self.db_path:
            raise RuntimeError("Database not initialized")
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(query, args)
            row = await cursor.fetchone()
            if row:
                row_dict = dict(row)
                # Convert timestamp strings back to datetime objects
                for key, value in row_dict.items():
                    if key in ['timestamp', 'created_at', 'updated_at'] and isinstance(value, str):
                        try:
                            from datetime import datetime
                            row_dict[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                        except:
                            pass
                return row_dict
            return None
    
    async def fetchval(self, query: str, *args) -> Any:
        """Execute a query that returns a single value."""
        if not self.db_path:
            raise RuntimeError("Database not initialized")
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(query, args)
            result = await cursor.fetchone()
            return result[0] if result else None

# Global database manager instance
db = DatabaseManager()
