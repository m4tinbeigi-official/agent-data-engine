import sqlite3
import json
import time
from pathlib import Path
from typing import Optional, List, Dict, Any

DB_PATH = Path.home() / "Desktop" / "agent-data-engine" / "catalog.db"

def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS endpoints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                url TEXT NOT NULL,
                task TEXT NOT NULL,
                category TEXT DEFAULT 'general',
                tags TEXT DEFAULT '',
                scraper_code TEXT NOT NULL,
                schema_json TEXT NOT NULL,
                sample_output TEXT,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            );
        """)
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS endpoints_fts USING fts5(
                slug, name, task, tags, content='endpoints', content_rowid='id'
            );
        """)
        # Drop trigger if causing issues, simple FTS sync
        conn.execute("DROP TRIGGER IF EXISTS endpoints_ai;")
        conn.execute("DROP TRIGGER IF EXISTS endpoints_ad;")
        conn.execute("DROP TRIGGER IF EXISTS endpoints_au;")


def save_endpoint(slug: str, name: str, url: str, task: str, category: str, tags: list[str], scraper_code: str, schema: dict, sample_output: Any) -> int:
    init_db()
    now = time.time()
    tags_str = ",".join(tags) if isinstance(tags, list) else str(tags)
    schema_str = json.dumps(schema, ensure_ascii=False)
    sample_str = json.dumps(sample_output, ensure_ascii=False)
    with get_conn() as conn:
        cursor = conn.execute("""
            INSERT INTO endpoints (slug, name, url, task, category, tags, scraper_code, schema_json, sample_output, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(slug) DO UPDATE SET
                name=excluded.name,
                url=excluded.url,
                task=excluded.task,
                category=excluded.category,
                tags=excluded.tags,
                scraper_code=excluded.scraper_code,
                schema_json=excluded.schema_json,
                sample_output=excluded.sample_output,
                updated_at=excluded.updated_at
        """, (slug, name, url, task, category, tags_str, scraper_code, schema_str, sample_str, now, now))
        row_id = cursor.lastrowid
        conn.execute("INSERT INTO endpoints_fts(endpoints_fts) VALUES('rebuild');")
        return row_id

def get_endpoint(slug: str) -> Optional[Dict[str, Any]]:
    init_db()
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM endpoints WHERE slug = ?", (slug,)).fetchone()
        if not row:
            return None
        d = dict(row)
        d["schema"] = json.loads(d["schema_json"])
        if d["sample_output"]:
            try:
                d["sample_output"] = json.loads(d["sample_output"])
            except Exception:
                pass
        return d

def list_endpoints() -> List[Dict[str, Any]]:
    init_db()
    with get_conn() as conn:
        rows = conn.execute("SELECT id, slug, name, url, task, category, tags, updated_at FROM endpoints ORDER BY updated_at DESC").fetchall()
        return [dict(r) for r in rows]

def search_endpoints(query: str) -> List[Dict[str, Any]]:
    init_db()
    with get_conn() as conn:
        # Try FTS first
        try:
            rows = conn.execute("""
                SELECT e.id, e.slug, e.name, e.url, e.task, e.category, e.tags, e.updated_at
                FROM endpoints_fts f
                JOIN endpoints e ON f.rowid = e.id
                WHERE endpoints_fts MATCH ?
                ORDER BY rank
            """, (query,)).fetchall()
            if rows:
                return [dict(r) for r in rows]
        except Exception:
            pass
        # Fallback LIKE
        like = f"%{query}%"
        rows = conn.execute("""
            SELECT id, slug, name, url, task, category, tags, updated_at
            FROM endpoints
            WHERE slug LIKE ? OR name LIKE ? OR task LIKE ? OR tags LIKE ?
            ORDER BY updated_at DESC
        """, (like, like, like, like)).fetchall()
        return [dict(r) for r in rows]
