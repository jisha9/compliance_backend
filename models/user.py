# backend/models/user.py  ← FULL FINAL VERSION (COPY-PASTE THIS ENTIRE FILE)

import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

# Path to database
DB_NAME = os.path.join(os.path.dirname(__file__), "../database.db")

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL
                )''')
    
    # Document uploads table
    c.execute('''CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    country TEXT,
                    entity_type TEXT,
                    product_category TEXT,
                    document_name TEXT,
                    file_path TEXT,
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )''')
    conn.commit()
    conn.close()

class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

    @staticmethod
    def get(user_id):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT id, username FROM users WHERE id = ?", (user_id,))
        row = c.fetchone()
        conn.close()
        return User(row[0], row[1]) if row else None

    @staticmethod
    def create(username, password):
        hashed = generate_password_hash(password)
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed))
            conn.commit()
            user_id = c.lastrowid
            conn.close()
            return User(user_id, username)
        except sqlite3.IntegrityError:
            conn.close()
            return None

    @staticmethod
    def validate(username, password):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT id, username, password FROM users WHERE username = ?", (username,))
        row = c.fetchone()
        conn.close()
        if row and check_password_hash(row[2], password):
            return User(row[0], row[1])
        return None

    # NEW: Get all uploaded document names for this user
    @staticmethod
    def get_uploaded_docs(user_id):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT document_name FROM documents WHERE user_id = ?", (user_id,))
        uploaded = [row[0] for row in c.fetchall()]
        conn.close()
        return uploaded

    # NEW: Save uploaded document info
    @staticmethod
    def save_document(user_id, country, entity_type, product_category, document_name, file_path):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("""INSERT INTO documents 
                     (user_id, country, entity_type, product_category, document_name, file_path) 
                     VALUES (?, ?, ?, ?, ?, ?)""",
                  (user_id, country, entity_type, product_category, document_name, file_path))
        conn.commit()
        conn.close()