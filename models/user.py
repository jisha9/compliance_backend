# backend/models/user.py  ← FINAL NO-CIRCULAR VERSION (Dec 2025)

import os
import pymysql
from pymysql.cursors import DictCursor
from pymysql.err import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from dotenv import load_dotenv

load_dotenv()

# FULLY INDEPENDENT DB CONNECTION (NO IMPORT FROM app.py!)
def get_db_connection():
    host = os.getenv("DB_HOST", "localhost")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    database = os.getenv("DB_NAME", "compliance_isha")
    port = int(os.getenv("DB_PORT", 3306))

    if not all([host, user, password, database]):
        raise RuntimeError("Missing DB env vars!")

    return pymysql.connect(
        host=host, user=user, password=password,
        database=database, port=port,
        charset="utf8mb4", cursorclass=DictCursor, autocommit=True
    )

def init_db():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""")

            cur.execute("""CREATE TABLE IF NOT EXISTS documents (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                country VARCHAR(255),
                entity_type VARCHAR(255),
                product_category VARCHAR(255),
                document_name VARCHAR(255),
                file_path VARCHAR(500),
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""")
        conn.commit()
    finally:
        conn.close()

class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

    @staticmethod
    def get(user_id):
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id, username FROM users WHERE id = %s", (user_id,))
                row = cur.fetchone()
                return User(row["id"], row["username"]) if row else None
        finally:
            conn.close()

    @staticmethod
    def create(username, password):
        hashed = generate_password_hash(password)
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed))
            conn.commit()
            return User(cur.lastrowid, username)
        except IntegrityError:
            return None
        finally:
            conn.close()

    @staticmethod
    def validate(username, password):
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id, username, password FROM users WHERE username = %s", (username,))
                row = cur.fetchone()
                if row and check_password_hash(row["password"], password):
                    return User(row["id"], row["username"])
        finally:
            conn.close()
        return None

    @staticmethod
    def get_uploaded_docs(user_id):
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT document_name, file_path FROM documents WHERE user_id = %s ORDER BY uploaded_at DESC", (user_id,))
                return [{"document_name": r["document_name"], "file_path": r["file_path"]} for r in cur.fetchall()]
        finally:
            conn.close()

    @staticmethod
    def save_document(user_id, country, entity_type, product_category, document_name, full_filename):
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""INSERT INTO documents 
                    (user_id, country, entity_type, product_category, document_name, file_path)
                    VALUES (%s, %s, %s, %s, %s, %s)""",
                    (user_id, country, entity_type, product_category, document_name, full_filename))
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def delete_document(user_id, document_name):
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM documents WHERE user_id = %s AND document_name = %s", (user_id, document_name))
            conn.commit()
        finally:
            conn.close()