# backend/models/user.py  ← MySQL VERSION

import os
import pymysql
from pymysql.cursors import DictCursor
from pymysql.err import IntegrityError
from dotenv import load_dotenv

from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

load_dotenv()  # load DB configs from .env if present


def get_db_connection():
    """
    Create and return a new MySQL connection using env vars.
    """
    conn = pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "myuser"),
        password=os.getenv("DB_PASSWORD", "mypassword"),
        database=os.getenv("DB_NAME", "compliance_app"),
        charset="utf8mb4",
        cursorclass=DictCursor,
    )
    return conn


def init_db():
    """
    Initialize the MySQL tables if they do not exist.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as c:
            # Users table
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(255) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL
                )
                """
            )

            # Document uploads table
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT,
                    country VARCHAR(255),
                    entity_type VARCHAR(255),
                    product_category VARCHAR(255),
                    document_name VARCHAR(255),
                    file_path VARCHAR(500),
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
                """
            )

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
            with conn.cursor() as c:
                c.execute(
                    "SELECT id, username FROM users WHERE id = %s",
                    (user_id,),
                )
                row = c.fetchone()
            if row:
                return User(row["id"], row["username"])
            return None
        finally:
            conn.close()

    @staticmethod
    def create(username, password):
        hashed = generate_password_hash(password)
        conn = get_db_connection()
        try:
            with conn.cursor() as c:
                c.execute(
                    "INSERT INTO users (username, password) VALUES (%s, %s)",
                    (username, hashed),
                )
                user_id = c.lastrowid
            conn.commit()
            return User(user_id, username)
        except IntegrityError:
            # username already taken (unique constraint)
            return None
        finally:
            conn.close()

    @staticmethod
    def validate(username, password):
        conn = get_db_connection()
        try:
            with conn.cursor() as c:
                c.execute(
                    "SELECT id, username, password FROM users WHERE username = %s",
                    (username,),
                )
                row = c.fetchone()
            if row and check_password_hash(row["password"], password):
                return User(row["id"], row["username"])
            return None
        finally:
            conn.close()

    # Get all uploaded document names for this user
    @staticmethod
    def get_uploaded_docs(user_id):
        conn = get_db_connection()
        try:
            with conn.cursor() as c:
                c.execute(
                    "SELECT document_name FROM documents WHERE user_id = %s",
                    (user_id,),
                )
                rows = c.fetchall()
            uploaded = [row["document_name"] for row in rows]
            return uploaded
        finally:
            conn.close()

    # Save uploaded document info
    @staticmethod
    def save_document(user_id, country, entity_type, product_category, document_name, file_path):
        conn = get_db_connection()
        try:
            with conn.cursor() as c:
                c.execute(
                    """
                    INSERT INTO documents 
                        (user_id, country, entity_type, product_category, document_name, file_path) 
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        user_id,
                        country,
                        entity_type,
                        product_category,
                        document_name,
                        file_path,
                    ),
                )
            conn.commit()
        finally:
            conn.close()
