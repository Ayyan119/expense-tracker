import sqlite3
import os
from flask import g, has_app_context
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'expense_tracker.db')

def get_db():
    """
    Returns a SQLite database connection with row_factory and foreign keys enabled.
    Checks and caches the connection in the Flask context if one exists.
    """
    if not has_app_context():
        # Fallback for script/CLI command execution outside a request context
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON;")
    return db

def init_db():
    """
    Creates the users and expenses tables if they do not already exist.
    """
    db = get_db()
    
    # Create users table
    db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    
    # Create expenses table
    db.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            date TEXT NOT NULL,
            description TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    db.commit()

def seed_db():
    """
    Seeds the database with sample data matching the landing page's mockup dashboard.
    """
    db = get_db()
    
    # Check if the test user already exists
    user = db.execute("SELECT * FROM users WHERE email = ?", ("nitish@example.com",)).fetchone()
    if not user:
        hashed_password = generate_password_hash("password123")
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
            ("Nitish Kumar", "nitish@example.com", hashed_password)
        )
        user_id = cursor.lastrowid
        
        # Seed sample expenses matching the mock visual in landing.html
        expenses = [
            (user_id, "Bills", 4500.00, "2026-03-01", "Rent & electricity"),
            (user_id, "Food", 3200.00, "2026-03-05", "Groceries"),
            (user_id, "Health", 2050.00, "2026-03-10", "Medicines"),
            (user_id, "Transport", 1800.00, "2026-03-15", "Metro card reload"),
        ]
        db.executemany(
            "INSERT INTO expenses (user_id, category, amount, date, description) VALUES (?, ?, ?, ?, ?)",
            expenses
        )
        db.commit()
