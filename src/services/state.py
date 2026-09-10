"""
State management service with dual backends:
  - Local dev:    SQLite file at data/agent_state.db
  - Production:   Firestore (enabled via USE_FIRESTORE=true in env)

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

_TIMEZONE = pytz.timezone('Australia/Brisbane')

# ---------------------------------------------------------------------------
# SQLite Backend
# ---------------------------------------------------------------------------

class SQLiteBackend:
    def __init__(self, db_path: str):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path) or '.', exist_ok=True)
        self._ensure_schema()

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self):
        with self._get_conn() as conn:
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

    def record_run(self, trigger: str, status: str, result: str = None):
        ran_at = datetime.now(_TIMEZONE).isoformat()
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO run_history (trigger, status, result, ran_at) VALUES (?, ?, ?, ?)",
                (trigger, status, result, ran_at)
            )
            conn.commit()

    def get_recent_runs(self, limit: int = 20):
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM run_history ORDER BY ran_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]

    def save_daily_digest(self, date: str, highlights: str):
        created_at = datetime.now(_TIMEZONE).isoformat()
        with self._get_conn() as conn:
            conn.execute(
                """INSERT INTO daily_digests (date, highlights, created_at)
                   VALUES (?, ?, ?)
                   ON CONFLICT(date) DO UPDATE SET highlights=excluded.highlights, created_at=excluded.created_at""",
                (date, highlights, created_at)
            )
            conn.commit()

    def get_digests_for_week(self, anchor_date: str = None):
        if anchor_date is None:
            anchor_date = datetime.now(_TIMEZONE).strftime('%Y-%m-%d')
        end = datetime.strptime(anchor_date, '%Y-%m-%d')
        start = (end - timedelta(days=6)).strftime('%Y-%m-%d')

        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT date, highlights FROM daily_digests WHERE date BETWEEN ? AND ? ORDER BY date ASC",
                (start, anchor_date)
            ).fetchall()
        return [dict(r) for r in rows]

    def mark_processed(self, source: str, item_id: str):
        processed_at = datetime.now(_TIMEZONE).isoformat()
        with self._get_conn() as conn:
            try:
                conn.execute(
                    "INSERT INTO processed_ids (source, item_id, processed_at) VALUES (?, ?, ?)",
                    (source, item_id, processed_at)
                )
                conn.commit()
            except sqlite3.IntegrityError:
                pass  # Already marked — ignore

    def is_processed(self, source: str, item_id: str) -> bool:
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT id FROM processed_ids WHERE source=? AND item_id=?", (source, item_id)
            ).fetchone()
        return row is not None


# ---------------------------------------------------------------------------
# Firestore Backend
# ---------------------------------------------------------------------------

class FirestoreBackend:
    def __init__(self, project_id: str):
        try:
            from google.cloud import firestore
            self.db = firestore.Client(project=project_id)
        except ImportError:
            raise ImportError("google-cloud-firestore is required for Firestore state backend")

    def record_run(self, trigger: str, status: str, result: str = None):
        ran_at = datetime.now(_TIMEZONE).isoformat()
        self.db.collection('run_history').add({
            'trigger': trigger,
            'status': status,
            'result': result,
            'ran_at': ran_at
        })

    def get_recent_runs(self, limit: int = 20):
        try:
            from google.cloud.firestore_v1.base_query import FieldFilter
            docs = self.db.collection('run_history').order_by(
                'ran_at', direction=firestore.Query.DESCENDING
            ).limit(limit).stream()
            return [doc.to_dict() for doc in docs]
        except Exception:
            return []

    def save_daily_digest(self, date: str, highlights: str):
        created_at = datetime.now(_TIMEZONE).isoformat()
        doc_ref = self.db.collection('daily_digests').document(date)
        doc_ref.set({
            'date': date,
            'highlights': highlights,
            'created_at': created_at
        }, merge=True)

    def get_digests_for_week(self, anchor_date: str = None):
        if anchor_date is None:
            anchor_date = datetime.now(_TIMEZONE).strftime('%Y-%m-%d')
        end = datetime.strptime(anchor_date, '%Y-%m-%d')
        start = (end - timedelta(days=6)).strftime('%Y-%m-%d')

        docs = self.db.collection('daily_digests')\
            .where('date', '>=', start)\
            .where('date', '<=', anchor_date)\
            .order_by('date')\
            .stream()
        
        return [doc.to_dict() for doc in docs]

    def mark_processed(self, source: str, item_id: str):
        processed_at = datetime.now(_TIMEZONE).isoformat()
        doc_id = f"{source}_{item_id}".replace('/', '_') # basic sanitization
        doc_ref = self.db.collection('processed_ids').document(doc_id)
        doc_ref.set({
            'source': source,
            'item_id': item_id,
            'processed_at': processed_at
        })

    def is_processed(self, source: str, item_id: str) -> bool:
        doc_id = f"{source}_{item_id}".replace('/', '_')
        doc_ref = self.db.collection('processed_ids').document(doc_id)
        return doc_ref.get().exists


# ---------------------------------------------------------------------------
# Global State Access
# ---------------------------------------------------------------------------

if config.USE_FIRESTORE:
    _backend = FirestoreBackend(project_id=config.FIRESTORE_PROJECT_ID)
else:
    _backend = SQLiteBackend(db_path=config.LOCAL_DB_PATH)


def record_run(trigger: str, status: str, result: str = None):
    return _backend.record_run(trigger, status, result)

def get_recent_runs(limit: int = 20):
    return _backend.get_recent_runs(limit)

def save_daily_digest(date: str, highlights: str):
    return _backend.save_daily_digest(date, highlights)

def get_digests_for_week(anchor_date: str = None):
    return _backend.get_digests_for_week(anchor_date)

def mark_processed(source: str, item_id: str):
    return _backend.mark_processed(source, item_id)

def is_processed(source: str, item_id: str) -> bool:
    return _backend.is_processed(source, item_id)
