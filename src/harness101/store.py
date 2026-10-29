import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from harness101.settings import settings
from harness101.model.anthropic.message import Message, Role

SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    model TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    seq INTEGER NOT NULL,
    role TEXT NOT NULL,
    type TEXT NOT NULL,
    turn INTEGER,
    conversation_id TEXT,
    usage TEXT,
    stop_reason TEXT,
    content_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(id),
    UNIQUE (session_id, seq)
);
"""

MIGRATE_COLUMNS = (
    ("type", "ALTER TABLE messages ADD COLUMN type TEXT"),
    ("turn", "ALTER TABLE messages ADD COLUMN turn INTEGER"),
    ("conversation_id", "ALTER TABLE messages ADD COLUMN conversation_id TEXT"),
    ("usage", "ALTER TABLE messages ADD COLUMN usage TEXT"),
    ("stop_reason", "ALTER TABLE messages ADD COLUMN stop_reason TEXT"),
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _dump_json(value: object) -> str | None:
    if value is None:
        return None
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json")
    return json.dumps(value, ensure_ascii=False)


def _infer_type(message: Message) -> str:
    if message.role == Role.ASSISTANT:
        return "assistant"
    content = message.content
    if isinstance(content, list) and content:
        first = content[0]
        block_type = (
            first.get("type")
            if isinstance(first, dict)
            else getattr(first, "type", None)
        )
        if block_type == "tool_result":
            return "tool_result"
    return "user"


def _dump_content(content: object) -> str:
    if hasattr(content, "model_dump"):
        content = content.model_dump(mode="json", exclude_none=True)
    elif isinstance(content, list):
        content = [
            (
                item.model_dump(mode="json", exclude_none=True)
                if hasattr(item, "model_dump")
                else item
            )
            for item in content
        ]
    return json.dumps(content, ensure_ascii=False)


class ConversationStore:
    """Persist chat messages in SQLite. Append on every message."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(SCHEMA)
            self._migrate(conn)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _migrate(self, conn: sqlite3.Connection) -> None:
        existing = {row["name"] for row in conn.execute("PRAGMA table_info(messages)")}
        for name, ddl in MIGRATE_COLUMNS:
            if name not in existing:
                conn.execute(ddl)

    def create_session(self, model: str) -> str:
        session_id = str(uuid4())
        now = _now()
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO sessions (id, model, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (session_id, model, now, now),
            )
        return session_id

    def append(
        self,
        session_id: str,
        message: Message,
        *,
        type: str | None = None,
        conversation_id: str | None = None,
        usage: object | None = None,
        turn: int | None = None,
        stop_reason: str | None = None,
    ) -> None:
        now = _now()
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COALESCE(MAX(seq), -1) + 1 AS next_seq FROM messages WHERE session_id = ?",
                (session_id,),
            ).fetchone()
            conn.execute(
                """
                INSERT INTO messages (
                    session_id, seq, role, type, turn, conversation_id, usage, stop_reason, content_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    row["next_seq"],
                    message.role.value,
                    type or _infer_type(message),
                    turn,
                    conversation_id,
                    _dump_json(usage),
                    stop_reason,
                    _dump_content(message.content),
                    now,
                ),
            )
            conn.execute(
                "UPDATE sessions SET updated_at = ? WHERE id = ?",
                (now, session_id),
            )

    def load(self, session_id: str) -> list[Message]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT role, content_json FROM messages
                WHERE session_id = ?
                ORDER BY seq ASC
                """,
                (session_id,),
            ).fetchall()
        return [
            Message(role=Role(row["role"]), content=json.loads(row["content_json"]))
            for row in rows
        ]

    def next_turn(self, session_id: str) -> int:
        """Next 1-based turn index for this session."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COALESCE(MAX(turn), 0) + 1 AS next_turn FROM messages WHERE session_id = ?",
                (session_id,),
            ).fetchone()
        return int(row["next_turn"])

    def latest_session_id(self) -> str | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id FROM sessions ORDER BY updated_at DESC LIMIT 1"
            ).fetchone()
        return None if row is None else row["id"]

store = ConversationStore(settings.db_path)