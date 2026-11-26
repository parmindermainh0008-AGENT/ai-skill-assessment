"""
Database layer — stores users and their quiz history using SQLite.
Every quiz attempt (domain, level, questions, answers, score) is saved
so the user can track their progress over time.
"""

import sqlite3
import json
from datetime import datetime
from contextlib import contextmanager

from config import DB_PATH


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """Creates the tables on app startup (if they don't already exist)."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                name TEXT,
                created_at TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS quiz_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_email TEXT NOT NULL,
                domain TEXT NOT NULL,
                level TEXT NOT NULL,
                questions_json TEXT NOT NULL,
                answers_json TEXT,
                evaluation_json TEXT,
                total_score REAL,
                max_score REAL,
                created_at TEXT
            )
        """)


def upsert_user(email: str, name: str):
    with get_connection() as conn:
        existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if not existing:
            conn.execute(
                "INSERT INTO users (email, name, created_at) VALUES (?, ?, ?)",
                (email, name, datetime.utcnow().isoformat()),
            )


def create_quiz_session(user_email: str, domain: str, level: str, questions: list) -> int:
    with get_connection() as conn:
        cursor = conn.execute(
            """INSERT INTO quiz_sessions
               (user_email, domain, level, questions_json, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (user_email, domain, level, json.dumps(questions), datetime.utcnow().isoformat()),
        )
        return cursor.lastrowid


def save_evaluation(session_id: int, answers: list, evaluation: list, total_score: float, max_score: float):
    with get_connection() as conn:
        conn.execute(
            """UPDATE quiz_sessions
               SET answers_json = ?, evaluation_json = ?, total_score = ?, max_score = ?
               WHERE id = ?""",
            (json.dumps(answers), json.dumps(evaluation), total_score, max_score, session_id),
        )


def get_user_history(user_email: str):
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT * FROM quiz_sessions
               WHERE user_email = ? AND total_score IS NOT NULL
               ORDER BY created_at DESC""",
            (user_email,),
        ).fetchall()
        return [dict(row) for row in rows]