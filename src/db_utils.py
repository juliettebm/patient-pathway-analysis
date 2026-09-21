import os
import sqlite3


def get_db_connection(database_path=None):
    """Open the SQLite database built by scripts/build_database.py."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # project root
    db_path = database_path or os.environ.get(
        "PATIENT_PATHWAY_DB", os.path.join(base_dir, "database", "patient_journey.db")
    )

    if not os.path.exists(db_path):
        raise FileNotFoundError(
            f"Database not found: {db_path}. Generate it with: python scripts/build_database.py"
        )

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn
