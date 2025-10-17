import sqlite3
import uuid
import os

DB_FILE = "tokens.db"

# ✅ Ensure table exists
def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tokens (
                chat_id TEXT PRIMARY KEY,
                token TEXT NOT NULL,
                name TEXT
            )
        """)
init_db()

# ✅ Generate new token
def generate_token(chat_id):
    return str(uuid.uuid4())

# ✅ Store token → chat_id + name
def store_token_for_chat(token, chat_id):
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""
            INSERT OR REPLACE INTO tokens (chat_id, token)
            VALUES (?, ?)
        """, (chat_id, token))

def store_chat_to_token(chat_id, token):
    store_token_for_chat(token, chat_id)

def store_name(token, name):
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""
            UPDATE tokens SET name = ?
            WHERE token = ?
        """, (name, token))

# ✅ Get chat_id from token
def get_chat_id(token):
    with sqlite3.connect(DB_FILE) as conn:
        row = conn.execute("""
            SELECT chat_id FROM tokens WHERE token = ?
        """, (token,)).fetchone()
        return row[0] if row else None

# ✅ Get token from chat_id
def get_token_for_chat(chat_id):
    with sqlite3.connect(DB_FILE) as conn:
        row = conn.execute("""
            SELECT token FROM tokens WHERE chat_id = ?
        """, (chat_id,)).fetchone()
        return row[0] if row else None

# ✅ Get name from token
def get_name(token):
    with sqlite3.connect(DB_FILE) as conn:
        row = conn.execute("""
            SELECT name FROM tokens WHERE token = ?
        """, (token,)).fetchone()
        return row[0] if row else None