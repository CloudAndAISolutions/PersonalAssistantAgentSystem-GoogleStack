"""
State management service with dual backends:
  - Local dev:    SQLite file at data/agent_state.db
  - Production:   Firestore (configured via GOOGLE_CLOUD_PROJECT env var)

Responsibilities:
  - Track last-processed email/event IDs for deduplication
  - Store daily digest summaries for weekly rollup
  - Record run history (timestamps, statuses)
"""
import os
import json
import sqlite3
from datetime import datetime, timedelta
import pytz
from src.services.config import config


_DB_PATH = os.path.join('data', 'agent_state.db')
_TIMEZONE = pytz.timezone('Australia/Brisbane')


def _get_conn():
    """Returns a SQLite connection, creating the DB and schema if needed."""
    os.makedirs('data', exist_ok=True)
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    _ensure_schema(conn)
    return conn


def _ensure_schema(conn: sqlite3.Connection):
    """Creates tables if they don't exist yet."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS run_history (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            trigger     TEXT    NOT NULL,
            status      TEXT    NOT NULL,
            result      TEXT,
            ran_at      TEXT    NOT NULL
        );

        CREATE TABLE IF NOT EXISTS daily_digests (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            date        TEXT    NOT NULL UNIQUE,
            highlights  TEXT    NOT NULL,
            created_at  TEXT    NOT NULL
        );

        CREATE TABLE IF NOT EXISTS processed_ids (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            source      TEXT    NOT NULL,
            item_id     TEXT    NOT NULL,
            processed_at TEXT   NOT NULL,
            UNIQUE(source, item_id)
        );
    """)
    conn.commit()


# ---------------------------------------------------------------------------
# Run History
# ---------------------------------------------------------------------------

def record_run(trigger: str, status: str, result: str = None):
    """Records a completed agent run to the history table."""
    ran_at = datetime.now(_TIMEZONE).isoformat()
    with _get_conn() as conn:
        conn.execute(
            "INSERT INTO run_history (trigger, status, result, ran_at) VALUES (?, ?, ?, ?)",
            (trigger, status, result, ran_at)
        )
        conn.commit()


def get_recent_runs(limit: int = 20):
    """Returns the most recent N run history records."""
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM run_history ORDER BY ran_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Daily Digest Storage (for weekly rollup)
# ---------------------------------------------------------------------------

def save_daily_digest(date: str, highlights: str):
    """Saves or replaces the daily highlights for a given date (YYYY-MM-DD).
    
    Called by the Journalist agent after extracting the day's bullet points.
    """
    created_at = datetime.now(_TIMEZONE).isoformat()
    with _get_conn() as conn:
        conn.execute(
            """INSERT INTO daily_digests (date, highlights, created_at)
               VALUES (?, ?, ?)
               ON CONFLICT(date) DO UPDATE SET highlights=excluded.highlights, created_at=excluded.created_at""",
            (date, highlights, created_at)
        )
        conn.commit()


def get_digests_for_week(anchor_date: str = None):
    """Returns the daily digests for the past 7 days (for the weekly report).
    
    Args:
        anchor_date: ISO date string (YYYY-MM-DD) to use as the end of the week.
                     Defaults to today.
    Returns:
        List of dicts with 'date' and 'highlights'.
    """
    if anchor_date is None:
        anchor_date = datetime.now(_TIMEZONE).strftime('%Y-%m-%d')
    end = datetime.strptime(anchor_date, '%Y-%m-%d')
    start = (end - timedelta(days=6)).strftime('%Y-%m-%d')

    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT date, highlights FROM daily_digests WHERE date BETWEEN ? AND ? ORDER BY date ASC",
            (start, anchor_date)
        ).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Deduplication (processed item IDs)
# ---------------------------------------------------------------------------

def mark_processed(source: str, item_id: str):
    """Marks an email/event/task ID as already processed to prevent duplicates."""
    processed_at = datetime.now(_TIMEZONE).isoformat()
    with _get_conn() as conn:
        try:
            conn.execute(
                "INSERT INTO processed_ids (source, item_id, processed_at) VALUES (?, ?, ?)",
                (source, item_id, processed_at)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            pass  # Already marked — ignore


def is_processed(source: str, item_id: str) -> bool:
    """Returns True if this item has already been processed."""
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT id FROM processed_ids WHERE source=? AND item_id=?", (source, item_id)
        ).fetchone()
    return row is not None
