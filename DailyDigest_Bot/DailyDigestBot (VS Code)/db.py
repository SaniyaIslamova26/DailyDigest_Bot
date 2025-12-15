# Mодуль работы с базой данных SQLite
# db.py
import sqlite3
import json

DB_NAME = "daily_digest.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            categories TEXT DEFAULT '[]',
            subscribed INTEGER DEFAULT 1,
            referrer_id INTEGER DEFAULT 0,
            unlimited_until TEXT DEFAULT NULL
        )
    ''')
    conn.commit()
    conn.close()

def add_user(user_id: int):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (user_id,))
    conn.commit()
    conn.close()

def update_categories(user_id: int, categories: list):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('UPDATE users SET categories = ? WHERE user_id = ?', (json.dumps(categories), user_id))
    conn.commit()
    conn.close()

def get_user_categories(user_id: int) -> list:
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT categories FROM users WHERE user_id = ?', (user_id,))
    row = cur.fetchone()
    conn.close()
    return json.loads(row[0]) if row and row[0] else []

def get_all_subscribers() -> list:
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT user_id FROM users WHERE subscribed = 1')
    rows = cur.fetchall()
    conn.close()
    return [r[0] for r in rows]

def unsubscribe_user(user_id: int):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('UPDATE users SET subscribed = 0, categories = "[]" WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()