"""
Database connection and helpers.
Uses psycopg2 with a simple connection pool.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager

import psycopg2
import psycopg2.extras

from ingestion.config import DATABASE_URL

logger = logging.getLogger(__name__)

# Register UUID adapter
psycopg2.extras.register_uuid()


def get_connection():
    """Get a new database connection."""
    return psycopg2.connect(DATABASE_URL)


@contextmanager
def get_cursor(commit: bool = True):
    """Context manager that yields a cursor and handles commit/rollback."""
    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        yield cur
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def execute(sql: str, params: tuple = ()) -> list[dict]:
    """Execute a query and return all rows as dicts."""
    with get_cursor(commit=False) as cur:
        cur.execute(sql, params)
        if cur.description:
            return [dict(row) for row in cur.fetchall()]
        return []


def execute_write(sql: str, params: tuple = ()) -> int:
    """Execute a write query. Returns rowcount."""
    with get_cursor(commit=True) as cur:
        cur.execute(sql, params)
        return cur.rowcount
