"""SQLite-compatible database models."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from bot.database.connection import db

@dataclass
class User:
    """User model."""
    user_id: int
    timezone: str = "UTC"
    share_global: bool = False
    max_daily_thc_mg: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    async def create(cls, user_id: int, **kwargs) -> 'User':
        """Create a new user."""
        user = cls(user_id=user_id, **kwargs)
        await user.save()
        return user

    @classmethod
    async def get(cls, user_id: int) -> Optional['User']:
        """Get user by ID."""
        row = await db.fetchrow(
            "SELECT * FROM Users WHERE user_id = ?", user_id
        )
        return cls(**dict(row)) if row else None

    @classmethod
    async def get_or_create(cls, user_id: int) -> 'User':
        """Get existing user or create a new one."""
        user = await cls.get(user_id)
        if not user:
            user = await cls.create(user_id)
        return user

    async def save(self):
        """Save user to database."""
        await db.execute("""
            INSERT OR REPLACE INTO Users (user_id, timezone, share_global, max_daily_thc_mg)
            VALUES (?, ?, ?, ?)
        """, self.user_id, self.timezone, self.share_global, self.max_daily_thc_mg)

@dataclass
class StashItem:
    """Stash item model."""
    id: Optional[int] = None
    user_id: Optional[int] = None
    type: str = ""
    strain: Optional[str] = None
    amount: float = 0.0
    thc_percent: Optional[float] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    async def get_user_stash(cls, user_id: int) -> List['StashItem']:
        """Get all stash items for a user."""
        rows = await db.fetch(
            "SELECT * FROM Stash WHERE user_id = ? ORDER BY type, strain", 
            user_id
        )
        return [cls(**dict(row)) for row in rows]

    @classmethod
    async def get_by_type_and_strain(cls, user_id: int, type: str, strain: Optional[str] = None) -> Optional['StashItem']:
        """Get stash item by type and strain."""
        if strain:
            row = await db.fetchrow(
                "SELECT * FROM Stash WHERE user_id = ? AND type = ? AND strain = ?",
                user_id, type, strain
            )
        else:
            row = await db.fetchrow(
                "SELECT * FROM Stash WHERE user_id = ? AND type = ? AND strain IS NULL",
                user_id, type
            )
        return cls(**dict(row)) if row else None

    async def save(self):
        """Save stash item to database."""
        if self.id:
            # Update existing
            await db.execute("""
                UPDATE Stash SET 
                    amount = ?, thc_percent = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, self.amount, self.thc_percent, self.notes, self.id)
        else:
            # Insert new
            await db.execute("""
                INSERT INTO Stash (user_id, type, strain, amount, thc_percent, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, self.user_id, self.type, self.strain, self.amount, self.thc_percent, self.notes)
            
            # Get the ID of the inserted row
            self.id = await db.fetchval("SELECT last_insert_rowid()")

    async def delete(self):
        """Delete stash item."""
        if self.id:
            await db.execute("DELETE FROM Stash WHERE id = ?", self.id)

@dataclass
class ConsumptionEntry:
    """Consumption log entry model."""
    id: Optional[int] = None
    user_id: Optional[int] = None
    type: str = ""
    strain: Optional[str] = None
    amount: float = 0.0
    thc_percent: Optional[float] = None
    method: str = ""
    absorbed_thc_mg: float = 0.0
    notes: Optional[str] = None
    symptom: Optional[str] = None
    effect_rating: Optional[int] = None
    timestamp: Optional[datetime] = None
    shared_in_servers: bool = False

    @classmethod
    async def create(cls, **kwargs) -> 'ConsumptionEntry':
        """Create a new consumption entry."""
        entry = cls(**kwargs)
        await entry.save()
        return entry

    @classmethod
    async def get_user_consumption(cls, user_id: int, limit: int = 50) -> List['ConsumptionEntry']:
        """Get consumption history for a user."""
        rows = await db.fetch("""
            SELECT * FROM ConsumptionLog 
            WHERE user_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        """, user_id, limit)
        return [cls(**dict(row)) for row in rows]

    @classmethod
    async def get_daily_consumption(cls, user_id: int, date: datetime) -> List['ConsumptionEntry']:
        """Get consumption for a specific day."""
        start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        rows = await db.fetch("""
            SELECT * FROM ConsumptionLog 
            WHERE user_id = ? AND timestamp BETWEEN ? AND ?
            ORDER BY timestamp DESC
        """, user_id, start_date, end_date)
        return [cls(**dict(row)) for row in rows]

    async def save(self):
        """Save consumption entry to database."""
        await db.execute("""
            INSERT INTO ConsumptionLog (
                user_id, type, strain, amount, thc_percent, method, 
                absorbed_thc_mg, notes, symptom, effect_rating, shared_in_servers
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, self.user_id, self.type, self.strain, self.amount, self.thc_percent,
             self.method, self.absorbed_thc_mg, self.notes, self.symptom, 
             self.effect_rating, self.shared_in_servers)
        
        # Get the ID of the inserted row
        self.id = await db.fetchval("SELECT last_insert_rowid()")

@dataclass
class StrainNote:
    """Strain note model."""
    id: Optional[int] = None
    user_id: Optional[int] = None
    strain: str = ""
    effect_rating: Optional[int] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None

    @classmethod
    async def create(cls, **kwargs) -> 'StrainNote':
        """Create a new strain note."""
        note = cls(**kwargs)
        await note.save()
        return note

    @classmethod
    async def get_user_notes(cls, user_id: int, strain: Optional[str] = None) -> List['StrainNote']:
        """Get strain notes for a user."""
        if strain:
            rows = await db.fetch(
                "SELECT * FROM StrainNotes WHERE user_id = ? AND strain = ? ORDER BY created_at DESC",
                user_id, strain
            )
        else:
            rows = await db.fetch(
                "SELECT * FROM StrainNotes WHERE user_id = ? ORDER BY created_at DESC",
                user_id
            )
        return [cls(**dict(row)) for row in rows]

    async def save(self):
        """Save strain note to database."""
        await db.execute("""
            INSERT INTO StrainNotes (user_id, strain, effect_rating, notes)
            VALUES (?, ?, ?, ?)
        """, self.user_id, self.strain, self.effect_rating, self.notes)
        
        # Get the ID of the inserted row
        self.id = await db.fetchval("SELECT last_insert_rowid()")

@dataclass
class Alert:
    """Alert model."""
    id: Optional[int] = None
    user_id: Optional[int] = None
    type: str = ""
    target_type: Optional[str] = None
    threshold: Optional[float] = None
    message: Optional[str] = None
    active: bool = True
    created_at: Optional[datetime] = None

    @classmethod
    async def get_user_alerts(cls, user_id: int, active_only: bool = True) -> List['Alert']:
        """Get alerts for a user."""
        if active_only:
            rows = await db.fetch(
                "SELECT * FROM Alerts WHERE user_id = ? AND active = 1 ORDER BY created_at",
                user_id
            )
        else:
            rows = await db.fetch(
                "SELECT * FROM Alerts WHERE user_id = ? ORDER BY created_at",
                user_id
            )
        return [cls(**dict(row)) for row in rows]

    async def save(self):
        """Save alert to database."""
        if self.id:
            await db.execute("""
                UPDATE Alerts SET 
                    threshold = ?, message = ?, active = ?
                WHERE id = ?
            """, self.threshold, self.message, self.active, self.id)
        else:
            await db.execute("""
                INSERT INTO Alerts (user_id, type, target_type, threshold, message, active)
                VALUES (?, ?, ?, ?, ?, ?)
            """, self.user_id, self.type, self.target_type, self.threshold, self.message, self.active)
            
            # Get the ID of the inserted row
            self.id = await db.fetchval("SELECT last_insert_rowid()")

    async def delete(self):
        """Delete alert."""
        if self.id:
            await db.execute("DELETE FROM Alerts WHERE id = ?", self.id)
