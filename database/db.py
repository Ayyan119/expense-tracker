import sqlite3
import os
from flask import g, has_app_context
from werkzeug.security import generate_password_hash

DB_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(DB_DIR)

# Spec 01_database_setup.md specifies spendly.db (or expense_tracker.db)
DEFAULT_DB_PATH = os.path.join(DB_DIR, 'spendly.db')

def get_db_path():
    """Returns the resolved database path, prioritizing environment variable, spendly.db, or expense_tracker.db."""
    if 'DB_PATH' in os.environ:
        return os.environ['DB_PATH']
    
    # Check for spendly.db or expense_tracker.db in project root or database directory
    candidates = [
        os.path.join(PROJECT_ROOT, 'spendly.db'),
        os.path.join(DB_DIR, 'spendly.db'),
        os.path.join(PROJECT_ROOT, 'expense_tracker.db'),
        os.path.join(DB_DIR, 'expense_tracker.db'),
    ]
    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate
    return DEFAULT_DB_PATH

DB_PATH = get_db_path()

def get_db():
    """
    Returns a SQLite database connection with row_factory and foreign keys enabled.
    Checks and caches the connection in the Flask context if one exists.
    """
    target_path = DB_PATH
    if not has_app_context():
        # Fallback for script/CLI command execution outside a request context
        conn = sqlite3.connect(target_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(target_path)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON;")
    return db

def init_db():
    """
    Creates the users and expenses tables if they do not already exist.
    Ensures schema columns (password_hash, created_at) are present on pre-existing database files.
    """
    db = get_db()
    
    # Create users table
    db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        )
    ''')
    
    # Create expenses table
    db.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL,
            description TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    # Schema migration safeguard for pre-existing database files
    user_columns = [col[1] for col in db.execute("PRAGMA table_info(users)").fetchall()]
    if "password" in user_columns and "password_hash" not in user_columns:
        db.execute("ALTER TABLE users RENAME COLUMN password TO password_hash;")
    if "created_at" not in user_columns:
        db.execute("ALTER TABLE users ADD COLUMN created_at TEXT DEFAULT (datetime('now'));")

    exp_columns = [col[1] for col in db.execute("PRAGMA table_info(expenses)").fetchall()]
    if "created_at" not in exp_columns:
        db.execute("ALTER TABLE expenses ADD COLUMN created_at TEXT DEFAULT (datetime('now'));")

    db.commit()

def seed_db():
    """
    Seeds the database with sample data if the users table is empty.
    """
    db = get_db()
    
    # Check if the users table already contains data
    existing_user = db.execute("SELECT 1 FROM users LIMIT 1").fetchone()
    if existing_user:
        return

    hashed_password = generate_password_hash("demo123")
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Demo User", "demo@spendly.com", hashed_password)
    )
    user_id = cursor.lastrowid
    
    # Seed 8 sample expenses covering all fixed categories
    expenses = [
        (user_id, "Bills", 4500.00, "2026-03-01", "Rent & electricity"),
        (user_id, "Food", 3200.00, "2026-03-05", "Weekly groceries"),
        (user_id, "Health", 2050.00, "2026-03-10", "Medicines & checkup"),
        (user_id, "Transport", 1800.00, "2026-03-12", "Metro card reload"),
        (user_id, "Entertainment", 1200.00, "2026-03-14", "Movie tickets & snacks"),
        (user_id, "Shopping", 2500.00, "2026-03-16", "New running shoes"),
        (user_id, "Other", 950.00, "2026-03-18", "Bookstore purchase"),
        (user_id, "Food", 650.00, "2026-03-20", "Dinner with friends"),
    ]
    db.executemany(
        "INSERT INTO expenses (user_id, category, amount, date, description) VALUES (?, ?, ?, ?, ?)",
        expenses
    )
    db.commit()

if __name__ == '__main__':
    init_db()
    seed_db()
    print("Database initialized and seeded successfully.")
