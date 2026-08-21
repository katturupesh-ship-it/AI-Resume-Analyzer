import sqlite3
import os
import json
from datetime import datetime

# Path to the database file in 05-Database folder
DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DB_DIR, "resume_analyzer.db")


def get_db_connection():
    """Establishes connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes the database schema if it doesn't already exist."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            ats_score INTEGER NOT NULL,
            word_count INTEGER NOT NULL,
            skills_detected TEXT,
            ai_summary TEXT,
            created_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def save_analysis(filename, ats_score, word_count, skills_list, ai_summary):
    """Saves a new resume analysis record."""
    conn = get_db_connection()
    cursor = conn.cursor()

    skills_json = json.dumps(skills_list)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO analyses (filename, ats_score, word_count, skills_detected, ai_summary, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (filename, ats_score, word_count, skills_json, ai_summary, timestamp))

    conn.commit()
    conn.close()


def get_recent_analyses(limit=5):
    """Retrieves the latest analysis records."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, filename, ats_score, word_count, skills_detected, ai_summary, created_at
        FROM analyses
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()
    conn.close()

    results = []
    for row in rows:
        results.append({
            "id": row["id"],
            "filename": row["filename"],
            "ats_score": row["ats_score"],
            "word_count": row["word_count"],
            "skills": json.loads(row["skills_detected"]) if row["skills_detected"] else [],
            "ai_summary": row["ai_summary"],
            "created_at": row["created_at"]
        })

    return results


# Initialize table on first import
init_db()