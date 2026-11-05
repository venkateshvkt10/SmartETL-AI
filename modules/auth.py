
import os
import sqlite3
import bcrypt

from pathlib import Path
from dotenv import load_dotenv


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data"
DATABASE_PATH = DATA_DIR / "auth.db"

load_dotenv(PROJECT_DIR / ".env")


# --------------------------------------------------
# DATABASE CONNECTION
# --------------------------------------------------

def get_auth_connection():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    return connection


# --------------------------------------------------
# INITIALIZE AUTHENTICATION DATABASE
# --------------------------------------------------

def initialize_auth_db():

    with get_auth_connection() as connection:

        connection.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        connection.commit()

    bootstrap_admin()


# --------------------------------------------------
# CREATE INITIAL ADMIN ACCOUNT
# --------------------------------------------------

def bootstrap_admin():

    admin_username = os.getenv("ADMIN_USERNAME")
    admin_password = os.getenv("ADMIN_PASSWORD")

    if not admin_username or not admin_password:
        raise RuntimeError(
            "ADMIN_USERNAME and ADMIN_PASSWORD "
            "must be configured in your .env file."
        )

    admin_username = admin_username.strip().lower()

    if len(admin_password) < 12:
        raise ValueError(
            "Admin password must contain at least 12 characters."
        )

    with get_auth_connection() as connection:

        existing_admin = connection.execute(
            "SELECT id FROM users WHERE role = 'admin' LIMIT 1"
        ).fetchone()

        if existing_admin:
            return

        password_hash = bcrypt.hashpw(
            admin_password.encode("utf-8"),
            bcrypt.gensalt(rounds=12)
        ).decode("utf-8")

        connection.execute("""
            INSERT INTO users (
                username,
                password_hash,
                role,
                is_active
            )
            VALUES (?, ?, 'admin', 1)
        """, (admin_username, password_hash))

        connection.commit()


# --------------------------------------------------
# AUTHENTICATE USER
# --------------------------------------------------

def authenticate_user(username, password):

    if not username or not password:
        return None

    username = username.strip().lower()

    with get_auth_connection() as connection:

        user = connection.execute("""
            SELECT id, username, password_hash, role, is_active
            FROM users
            WHERE username = ?
        """, (username,)).fetchone()

    if not user or not user["is_active"]:
        return None

    try:
        password_matches = bcrypt.checkpw(
            password.encode("utf-8"),
            user["password_hash"].encode("utf-8")
        )
    except (ValueError, TypeError):
        return None

    if not password_matches:
        return None

    return {
        "id": user["id"],
        "username": user["username"],
        "role": user["role"]
    }


# --------------------------------------------------
# CREATE USER - ADMIN ONLY
# --------------------------------------------------

def create_user(username, password):

    username = (username or "").strip().lower()

    if not 3 <= len(username) <= 32:
        raise ValueError(
            "Username must contain 3 to 32 characters."
        )

    if not username.replace("_", "").replace("-", "").isalnum():
        raise ValueError(
            "Username can contain letters, numbers, "
            "underscores and hyphens only."
        )

    if len(password or "") < 12:
        raise ValueError(
            "Password must contain at least 12 characters."
        )

    password_hash = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(rounds=12)
    ).decode("utf-8")

    with get_auth_connection() as connection:

        try:
            connection.execute("""
                INSERT INTO users (
                    username,
                    password_hash,
                    role,
                    is_active
                )
                VALUES (?, ?, 'user', 1)
            """, (username, password_hash))

            connection.commit()

        except sqlite3.IntegrityError:
            raise ValueError("This username already exists.")


# --------------------------------------------------
# LIST USERS
# --------------------------------------------------

def list_users():

    with get_auth_connection() as connection:

        users = connection.execute("""
            SELECT id, username, role, is_active, created_at
            FROM users
            ORDER BY id
        """).fetchall()

    return [dict(user) for user in users]


# --------------------------------------------------
# ACTIVATE / DEACTIVATE USER
# --------------------------------------------------

def set_user_active(user_id, is_active):

    with get_auth_connection() as connection:

        result = connection.execute("""
            UPDATE users
            SET is_active = ?
            WHERE id = ? AND role = 'user'
        """, (1 if is_active else 0, user_id))

        connection.commit()

    return result.rowcount == 1
