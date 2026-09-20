import os
import sqlite3


def get_db_connection():
    """Open the SQLite database built by notebooks/01_exploration.ipynb."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # project root
    db_path = os.path.join(base_dir, "database", "patient_journey.db")

    if not os.path.exists(db_path):
        raise FileNotFoundError(
            f"Database not found: {db_path}. Generate it by running notebooks/01_exploration.ipynb."
        )

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn
