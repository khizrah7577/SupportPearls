"""Per-user conversation and message persistence."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from src.auth.db import get_connection, init_db


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


@dataclass
class Conversation:
    id: int
    user_id: int
    title: str
    category: str
    created_at: str
    updated_at: str
    message_count: int = 0

    @classmethod
    def from_row(cls, row: sqlite3.Row | dict[str, Any]) -> Conversation:
        data = dict(row)
        return cls(
            id=int(data["id"]),
            user_id=int(data["user_id"]),
            title=str(data["title"]),
            category=str(data.get("category") or "general"),
            created_at=str(data["created_at"]),
            updated_at=str(data["updated_at"]),
            message_count=int(data.get("message_count") or 0),
        )


@dataclass
class Message:
    id: int
    conversation_id: int
    role: str
    content: str
    meta: dict[str, Any] | None
    feedback: int | None
    created_at: str

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> Message:
        meta_raw = row["meta_json"]
        meta = json.loads(meta_raw) if meta_raw else None
        return cls(
            id=int(row["id"]),
            conversation_id=int(row["conversation_id"]),
            role=str(row["role"]),
            content=str(row["content"]),
            meta=meta,
            feedback=row["feedback"],
            created_at=str(row["created_at"]),
        )


class ConversationStore:
    def __init__(self) -> None:
        init_db()

    def create(self, user_id: int, title: str = "New conversation") -> Conversation:
        conn = get_connection()
        try:
            cur = conn.execute(
                """
                INSERT INTO conversations (user_id, title)
                VALUES (?, ?)
                """,
                (user_id, title.strip() or "New conversation"),
            )
            conn.commit()
            row = conn.execute(
                "SELECT *, 0 AS message_count FROM conversations WHERE id = ?",
                (cur.lastrowid,),
            ).fetchone()
            return Conversation.from_row(row)
        finally:
            conn.close()

    def list_for_user(
        self,
        user_id: int,
        *,
        query: str | None = None,
        limit: int = 50,
    ) -> list[Conversation]:
        conn = get_connection()
        try:
            sql = """
                SELECT c.*,
                       (SELECT COUNT(*) FROM messages m WHERE m.conversation_id = c.id)
                         AS message_count
                FROM conversations c
                WHERE c.user_id = ?
            """
            params: list[Any] = [user_id]
            if query:
                sql += " AND (c.title LIKE ? OR EXISTS (" \
                       "SELECT 1 FROM messages m WHERE m.conversation_id = c.id " \
                       "AND m.content LIKE ?))"
                like = f"%{query.strip()}%"
                params.extend([like, like])
            sql += " ORDER BY c.updated_at DESC LIMIT ?"
            params.append(limit)
            rows = conn.execute(sql, params).fetchall()
            return [Conversation.from_row(r) for r in rows]
        finally:
            conn.close()

    def get(self, conversation_id: int, user_id: int) -> Conversation | None:
        conn = get_connection()
        try:
            row = conn.execute(
                """
                SELECT c.*,
                       (SELECT COUNT(*) FROM messages m WHERE m.conversation_id = c.id)
                         AS message_count
                FROM conversations c
                WHERE c.id = ? AND c.user_id = ?
                """,
                (conversation_id, user_id),
            ).fetchone()
            return Conversation.from_row(row) if row else None
        finally:
            conn.close()

    def rename(self, conversation_id: int, user_id: int, title: str) -> bool:
        conn = get_connection()
        try:
            cur = conn.execute(
                """
                UPDATE conversations
                SET title = ?, updated_at = ?
                WHERE id = ? AND user_id = ?
                """,
                (title.strip()[:120] or "Untitled", _now(), conversation_id, user_id),
            )
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()

    def set_category(self, conversation_id: int, user_id: int, category: str) -> bool:
        conn = get_connection()
        try:
            cur = conn.execute(
                """
                UPDATE conversations
                SET category = ?, updated_at = ?
                WHERE id = ? AND user_id = ?
                """,
                (category.strip()[:40] or "general", _now(), conversation_id, user_id),
            )
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()

    def delete(self, conversation_id: int, user_id: int) -> bool:
        conn = get_connection()
        try:
            cur = conn.execute(
                "DELETE FROM conversations WHERE id = ? AND user_id = ?",
                (conversation_id, user_id),
            )
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()

    def add_message(
        self,
        conversation_id: int,
        user_id: int,
        *,
        role: str,
        content: str,
        meta: dict[str, Any] | None = None,
    ) -> Message | None:
        if not self.get(conversation_id, user_id):
            return None
        conn = get_connection()
        try:
            cur = conn.execute(
                """
                INSERT INTO messages (conversation_id, role, content, meta_json)
                VALUES (?, ?, ?, ?)
                """,
                (
                    conversation_id,
                    role,
                    content,
                    json.dumps(meta) if meta is not None else None,
                ),
            )
            conn.execute(
                "UPDATE conversations SET updated_at = ? WHERE id = ?",
                (_now(), conversation_id),
            )
            # Auto-title from first user message
            if role == "user":
                count = conn.execute(
                    "SELECT COUNT(*) AS n FROM messages WHERE conversation_id = ?",
                    (conversation_id,),
                ).fetchone()["n"]
                if count == 1:
                    title = content.strip().replace("\n", " ")[:60]
                    conn.execute(
                        "UPDATE conversations SET title = ? WHERE id = ?",
                        (title or "New conversation", conversation_id),
                    )
            conn.commit()
            row = conn.execute(
                "SELECT * FROM messages WHERE id = ?", (cur.lastrowid,)
            ).fetchone()
            return Message.from_row(row)
        finally:
            conn.close()

    def list_messages(self, conversation_id: int, user_id: int) -> list[Message]:
        if not self.get(conversation_id, user_id):
            return []
        conn = get_connection()
        try:
            rows = conn.execute(
                """
                SELECT * FROM messages
                WHERE conversation_id = ?
                ORDER BY id ASC
                """,
                (conversation_id,),
            ).fetchall()
            return [Message.from_row(r) for r in rows]
        finally:
            conn.close()

    def set_feedback(
        self, message_id: int, conversation_id: int, user_id: int, feedback: int
    ) -> bool:
        if not self.get(conversation_id, user_id):
            return False
        conn = get_connection()
        try:
            cur = conn.execute(
                """
                UPDATE messages SET feedback = ?
                WHERE id = ? AND conversation_id = ?
                """,
                (feedback, message_id, conversation_id),
            )
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()

    def stats_for_user(self, user_id: int) -> dict[str, Any]:
        conn = get_connection()
        try:
            conv_count = conn.execute(
                "SELECT COUNT(*) AS n FROM conversations WHERE user_id = ?",
                (user_id,),
            ).fetchone()["n"]
            msg_count = conn.execute(
                """
                SELECT COUNT(*) AS n
                FROM messages m
                JOIN conversations c ON c.id = m.conversation_id
                WHERE c.user_id = ?
                """,
                (user_id,),
            ).fetchone()["n"]
            user_msgs = conn.execute(
                """
                SELECT COUNT(*) AS n
                FROM messages m
                JOIN conversations c ON c.id = m.conversation_id
                WHERE c.user_id = ? AND m.role = 'user'
                """,
                (user_id,),
            ).fetchone()["n"]
            by_day = conn.execute(
                """
                SELECT date(m.created_at) AS day, COUNT(*) AS n
                FROM messages m
                JOIN conversations c ON c.id = m.conversation_id
                WHERE c.user_id = ?
                GROUP BY date(m.created_at)
                ORDER BY day DESC
                LIMIT 14
                """,
                (user_id,),
            ).fetchall()
            return {
                "conversations": int(conv_count),
                "messages": int(msg_count),
                "questions": int(user_msgs),
                "activity": [
                    {"day": r["day"], "count": int(r["n"])} for r in reversed(list(by_day))
                ],
            }
        finally:
            conn.close()

    def export_text(self, conversation_id: int, user_id: int) -> str | None:
        conv = self.get(conversation_id, user_id)
        if not conv:
            return None
        messages = self.list_messages(conversation_id, user_id)
        lines = [
            f"SupportPearlz conversation: {conv.title}",
            f"Exported: {_now()} UTC",
            "=" * 60,
            "",
        ]
        for msg in messages:
            label = "You" if msg.role == "user" else "SupportPearlz"
            lines.append(f"[{label}] {msg.created_at}")
            lines.append(msg.content)
            lines.append("")
        return "\n".join(lines)
