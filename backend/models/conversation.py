"""SQLite-backed conversation history with tiered memory support."""

from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path

import aiosqlite


class ConversationStore:
    def __init__(self, db_path: Path) -> None:
        self._db_path = str(db_path)
        self._db: aiosqlite.Connection | None = None

    async def init(self) -> None:
        self._db = await aiosqlite.connect(self._db_path)
        await self._db.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                persona_id TEXT DEFAULT '',
                title TEXT DEFAULT '新对话',
                created_at TEXT,
                updated_at TEXT
            )
        """)
        await self._db.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT,
                role TEXT,
                content TEXT,
                created_at TEXT,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
            )
        """)
        # Mid-term memory: conversation summaries
        await self._db.execute("""
            CREATE TABLE IF NOT EXISTS summaries (
                id TEXT PRIMARY KEY,
                conversation_id TEXT,
                content TEXT,
                message_position INTEGER,
                created_at TEXT,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
            )
        """)
        await self._db.commit()

    async def close(self) -> None:
        if self._db:
            await self._db.close()

    async def create_conversation(self, persona_id: str = "") -> str:
        cid = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        await self._db.execute(
            "INSERT INTO conversations (id, persona_id, title, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (cid, persona_id, "新对话", now, now),
        )
        await self._db.commit()
        return cid

    async def add_message(self, conversation_id: str, role: str, content: str) -> str:
        mid = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        await self._db.execute(
            "INSERT INTO messages (id, conversation_id, role, content, created_at) VALUES (?, ?, ?, ?, ?)",
            (mid, conversation_id, role, content, now),
        )
        await self._db.execute(
            "UPDATE conversations SET updated_at = ? WHERE id = ?",
            (now, conversation_id),
        )
        await self._db.commit()
        return mid

    async def get_messages(self, conversation_id: str, limit: int = 50) -> list[dict]:
        cursor = await self._db.execute(
            "SELECT role, content, created_at FROM messages WHERE conversation_id = ? ORDER BY created_at ASC LIMIT ?",
            (conversation_id, limit),
        )
        rows = await cursor.fetchall()
        return [{"role": r[0], "content": r[1], "created_at": r[2]} for r in rows]

    async def get_message_count(self, conversation_id: str) -> int:
        cursor = await self._db.execute(
            "SELECT COUNT(*) FROM messages WHERE conversation_id = ?",
            (conversation_id,),
        )
        row = await cursor.fetchone()
        return row[0] if row else 0

    async def list_conversations(self) -> list[dict]:
        cursor = await self._db.execute(
            "SELECT id, persona_id, title, created_at, updated_at FROM conversations ORDER BY updated_at DESC"
        )
        rows = await cursor.fetchall()
        return [
            {"id": r[0], "persona_id": r[1], "title": r[2], "created_at": r[3], "updated_at": r[4]}
            for r in rows
        ]

    async def update_title(self, conversation_id: str, title: str) -> None:
        await self._db.execute(
            "UPDATE conversations SET title = ? WHERE id = ?", (title, conversation_id)
        )
        await self._db.commit()

    async def delete_conversation(self, conversation_id: str) -> None:
        await self._db.execute("DELETE FROM summaries WHERE conversation_id = ?", (conversation_id,))
        await self._db.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
        await self._db.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
        await self._db.commit()

    # --- Summary (mid-term memory) ---
    async def add_summary(self, conversation_id: str, content: str, message_position: int) -> str:
        sid = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        await self._db.execute(
            "INSERT INTO summaries (id, conversation_id, content, message_position, created_at) VALUES (?, ?, ?, ?, ?)",
            (sid, conversation_id, content, message_position, now),
        )
        await self._db.commit()
        return sid

    async def get_summaries(self, conversation_id: str) -> list[dict]:
        cursor = await self._db.execute(
            "SELECT content, message_position, created_at FROM summaries WHERE conversation_id = ? ORDER BY message_position ASC",
            (conversation_id,),
        )
        rows = await cursor.fetchall()
        return [{"content": r[0], "message_position": r[1], "created_at": r[2]} for r in rows]

    async def get_last_summary_position(self, conversation_id: str) -> int:
        cursor = await self._db.execute(
            "SELECT MAX(message_position) FROM summaries WHERE conversation_id = ?",
            (conversation_id,),
        )
        row = await cursor.fetchone()
        return row[0] if row and row[0] is not None else 0
