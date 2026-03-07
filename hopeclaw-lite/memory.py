import os
import sqlite3
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'hopeclaw.db')

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT NOT NULL,
            value TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            when_iso TEXT NOT NULL,
            chat_id TEXT NOT NULL,
            sent INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def save_memory(key: str, value: str):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO memories (key, value, created_at) VALUES (?, ?, ?)",
        (key, value, datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()

def list_memories(limit: int = 20):
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT key, value, created_at FROM memories ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return rows

def add_reminder(text: str, when_iso: str, chat_id: str):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO reminders (text, when_iso, chat_id, created_at) VALUES (?, ?, ?, ?)",
        (text, when_iso, str(chat_id), datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()

def list_reminders(limit: int = 20):
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT id, text, when_iso, chat_id, sent FROM reminders ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return rows

def get_due_reminders(now_iso: str):
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT id, text, when_iso, chat_id FROM reminders WHERE sent=0 AND when_iso <= ?", (now_iso,)
    ).fetchall()
    conn.close()
    return rows

def mark_reminder_sent(reminder_id: int):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE reminders SET sent=1 WHERE id=?", (reminder_id,))
    conn.commit()
    conn.close()
