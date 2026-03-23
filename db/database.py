"""
SQLite database — stores scraped jobs, tracks seen IDs to avoid duplicates.
"""

import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent.parent / "jobs.db"


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS jobs (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id      TEXT NOT NULL,
                company     TEXT NOT NULL,
                title       TEXT,
                location    TEXT,
                department  TEXT,
                url         TEXT,
                ats         TEXT,
                description TEXT,
                scraped_at  TEXT,
                UNIQUE(job_id, company)
            );

            CREATE TABLE IF NOT EXISTS scrape_runs (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                company     TEXT,
                ats         TEXT,
                jobs_found  INTEGER,
                new_jobs    INTEGER,
                ran_at      TEXT
            );
        """)
    print(f"[DB] Initialized at {DB_PATH}")


def upsert_jobs(jobs: list[dict]) -> int:
    """Insert new jobs, skip duplicates. Returns count of new inserts."""
    new_count = 0
    now = datetime.utcnow().isoformat()
    with get_conn() as conn:
        for job in jobs:
            try:
                conn.execute(
                    """
                    INSERT INTO jobs (job_id, company, title, location, department,
                                     url, ats, description, scraped_at)
                    VALUES (:job_id, :company, :title, :location, :department,
                            :url, :ats, :description, :scraped_at)
                    """,
                    {**job, "scraped_at": now},
                )
                new_count += 1
            except sqlite3.IntegrityError:
                pass  # already exists
    return new_count


def log_run(company: str, ats: str, jobs_found: int, new_jobs: int):
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO scrape_runs (company, ats, jobs_found, new_jobs, ran_at)
               VALUES (?, ?, ?, ?, ?)""",
            (company, ats, jobs_found, new_jobs, datetime.utcnow().isoformat()),
        )


def search_jobs(query: str = "", company: str = "", location: str = "",
                limit: int = 50, offset: int = 0) -> list[dict]:
    sql = "SELECT * FROM jobs WHERE 1=1"
    params = []
    if query:
        sql += " AND (title LIKE ? OR description LIKE ?)"
        params += [f"%{query}%", f"%{query}%"]
    if company:
        sql += " AND company = ?"
        params.append(company)
    if location:
        sql += " AND location LIKE ?"
        params.append(f"%{location}%")
    sql += " ORDER BY scraped_at DESC LIMIT ? OFFSET ?"
    params += [limit, offset]
    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def get_stats() -> dict:
    with get_conn() as conn:
        total = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
        companies = conn.execute(
            "SELECT company, COUNT(*) as cnt FROM jobs GROUP BY company ORDER BY cnt DESC"
        ).fetchall()
        recent_runs = conn.execute(
            "SELECT * FROM scrape_runs ORDER BY ran_at DESC LIMIT 10"
        ).fetchall()
    return {
        "total_jobs": total,
        "by_company": [dict(r) for r in companies],
        "recent_runs": [dict(r) for r in recent_runs],
    }
