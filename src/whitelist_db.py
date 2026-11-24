"""SQLite persistence for Minecraft whitelist ↔ Discord identity mappings."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path


class WhitelistDB:
    """Persist whitelist links under data/ (Docker bind-mount friendly)."""

    def __init__(self, db_path: str = "data/whitelist/whitelist.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS whitelisted_users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    discord_user_id TEXT NOT NULL,
                    discord_tag TEXT NOT NULL,
                    minecraft_username TEXT NOT NULL,
                    ticket_id TEXT,
                    source TEXT NOT NULL,
                    whitelisted_at TEXT NOT NULL,
                    UNIQUE(discord_user_id)
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_whitelist_mc
                ON whitelisted_users (minecraft_username COLLATE NOCASE)
                """
            )
            conn.commit()

    def record(
        self,
        *,
        discord_user_id: str | int,
        discord_tag: str,
        minecraft_username: str,
        source: str,
        ticket_id: str | None = None,
    ) -> dict:
        """Insert or update a whitelist record for a Discord user."""
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO whitelisted_users (
                    discord_user_id,
                    discord_tag,
                    minecraft_username,
                    ticket_id,
                    source,
                    whitelisted_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(discord_user_id) DO UPDATE SET
                    discord_tag = excluded.discord_tag,
                    minecraft_username = excluded.minecraft_username,
                    ticket_id = COALESCE(excluded.ticket_id, whitelisted_users.ticket_id),
                    source = excluded.source,
                    whitelisted_at = excluded.whitelisted_at
                """,
                (
                    str(discord_user_id),
                    discord_tag,
                    minecraft_username,
                    ticket_id,
                    source,
                    now,
                ),
            )
            conn.commit()
            row = conn.execute(
                "SELECT * FROM whitelisted_users WHERE discord_user_id = ?",
                (str(discord_user_id),),
            ).fetchone()
        return dict(row) if row else {}

    def get_by_discord(self, discord_user_id: str | int) -> dict | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM whitelisted_users WHERE discord_user_id = ?",
                (str(discord_user_id),),
            ).fetchone()
        return dict(row) if row else None

    def get_by_minecraft(self, minecraft_username: str) -> dict | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT * FROM whitelisted_users
                WHERE minecraft_username = ? COLLATE NOCASE
                """,
                (minecraft_username,),
            ).fetchone()
        return dict(row) if row else None


whitelist_db = WhitelistDB()
print("loaded WhitelistDB")
