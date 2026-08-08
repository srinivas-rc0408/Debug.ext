"""
Debug.ext — SQLite Persistence Layer
Stores every analyzed bug in a local database for history and audit trails.
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, List

logger = logging.getLogger("debug_ext.db")

_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "history.db")


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")  # Better concurrent read performance
    return conn


def init_db() -> None:
    """Create the bug_history table if it does not exist."""
    try:
        conn = _get_connection()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS bug_history (
                id          TEXT PRIMARY KEY,
                timestamp   TEXT NOT NULL,
                url         TEXT DEFAULT 'Unknown',
                source      TEXT DEFAULT 'extension',
                summary     TEXT NOT NULL,
                category    TEXT NOT NULL,
                severity    TEXT NOT NULL,
                priority    TEXT NOT NULL,
                confidence  REAL DEFAULT 0.5,
                component   TEXT DEFAULT 'Unknown',
                full_json   TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()
        logger.info("SQLite database initialized at %s", os.path.abspath(_DB_PATH))
    except Exception as exc:
        logger.error("Failed to initialize SQLite: %s", exc, exc_info=True)


def insert_result(result_dict: Dict[str, Any], url: str = "Unknown", source: str = "extension") -> None:
    """Insert a single analysis result into the history database."""
    try:
        conn = _get_connection()
        conn.execute(
            """
            INSERT OR REPLACE INTO bug_history
                (id, timestamp, url, source, summary, category, severity, priority, confidence, component, full_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                result_dict.get("bug_id", ""),
                result_dict.get("timestamp", datetime.now(timezone.utc).isoformat()),
                url,
                source,
                result_dict.get("bug_summary", ""),
                result_dict.get("category", ""),
                result_dict.get("severity", ""),
                result_dict.get("priority", ""),
                float(result_dict.get("confidence_score", 0.5)),
                result_dict.get("affected_component", "Unknown"),
                json.dumps(result_dict, default=str),
            ),
        )
        conn.commit()
        conn.close()
        logger.info("Persisted bug %s to SQLite", result_dict.get("bug_id", "?"))
    except Exception as exc:
        logger.error("SQLite insert failed: %s", exc, exc_info=True)


def get_history(limit: int = 200) -> List[Dict[str, Any]]:
    """Fetch all history records, most recent first."""
    try:
        conn = _get_connection()
        rows = conn.execute(
            "SELECT * FROM bug_history ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        ).fetchall()
        conn.close()

        results = []
        for row in rows:
            record = {
                "id": row["id"],
                "timestamp": row["timestamp"],
                "url": row["url"],
                "source": row["source"],
                "summary": row["summary"],
                "category": row["category"],
                "severity": row["severity"],
                "priority": row["priority"],
                "confidence": row["confidence"],
                "component": row["component"],
            }
            # Parse full_json for detail views
            try:
                record["full_analysis"] = json.loads(row["full_json"])
            except (json.JSONDecodeError, TypeError):
                record["full_analysis"] = {}
            results.append(record)
        return results
    except Exception as exc:
        logger.error("SQLite query failed: %s", exc, exc_info=True)
        return []


def get_history_count() -> int:
    """Return total number of records in the history database."""
    try:
        conn = _get_connection()
        count = conn.execute("SELECT COUNT(*) FROM bug_history").fetchone()[0]
        conn.close()
        return count
    except Exception:
        return 0
