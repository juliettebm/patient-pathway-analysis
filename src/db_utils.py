import os
import sqlite3

def get_db_connection():
    """
    Calcule dynamiquement le chemin absolu de la base de données.
    """
    # Remonte au dossier racine du projet
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, "database", "patient_journey.db")
    
    # Fallback si lancé depuis un autre endroit
    if not os.path.exists(db_path):
        db_path = os.path.join("database", "patient_journey.db")
        
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn