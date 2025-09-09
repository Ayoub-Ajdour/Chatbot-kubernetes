# app/mcp_context.py

import logging
import sqlite3
import json

DB_PATH = "logs/sessions.db"

def _initialize_db():
    """Crée la table de session si elle n'existe pas."""
    try:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                context_data TEXT
            )
        """)
        conn.commit()
        conn.close()
        logging.info(f"Database initialized at {DB_PATH}")
    except Exception as e:
        logging.error(f"Failed to initialize database: {e}")

_initialize_db()

def get_context(session_id):
    """Récupère le contexte d'une session depuis la base de données."""
    try:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("SELECT context_data FROM sessions WHERE session_id = ?", (session_id,))
        result = cursor.fetchone()
        conn.close()
        return json.loads(result[0]) if result else {}
    except Exception as e:
        logging.error(f"Error getting context for {session_id}: {e}")
        return {}

def update_context(data, session_id):
    """Met à jour le contexte d'une session dans la base de données."""
    try:
        full_context = get_context(session_id)
        full_context.update(data)
        
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO sessions (session_id, context_data) VALUES (?, ?)",
            (session_id, json.dumps(full_context))
        )
        conn.commit()
        conn.close()
        logging.info(f"Updated context for session {session_id}")
    except Exception as e:
        logging.error(f"Error updating context for {session_id}: {e}")

def get_history(session_id):
    """Obtient l'historique de la conversation pour une session."""
    context = get_context(session_id)
    return context.get("history", "")

def update_history(session_id, user_query, bot_response):
    """Ajoute le dernier échange à l'historique de la conversation."""
    context = get_context(session_id)
    current_history = context.get("history", "")
    new_exchange = f"User: {user_query}\nAssistant: {bot_response}\n"
    new_history = f"{current_history}{new_exchange}"
    
    # Limite la taille de l'historique pour éviter qu'il ne devienne trop grand
    history_lines = new_history.strip().split('\n')
    if len(history_lines) > 20: # Garde environ les 10 derniers échanges
        new_history = "\n".join(history_lines[-20:]) + "\n"

    update_context({"history": new_history}, session_id)
