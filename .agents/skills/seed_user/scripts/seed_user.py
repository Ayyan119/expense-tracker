#!/usr/bin/env python3
import os
import sys
import random
import sqlite3
from werkzeug.security import generate_password_hash

# Ensure project root is in sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

PAKISTANI_FIRST_NAMES = [
    "Muhammad", "Ali", "Ahmed", "Fatima", "Ayesha", "Zainab", "Hassan", "Hussain",
    "Bilal", "Sara", "Sana", "Usman", "Hamza", "Tariq", "Zain", "Hiba", "Omer",
    "Maryam", "Saad", "Aisha", "Mustafa", "Ibrahim", "Mahnoor", "Haris", "Laiba",
    "Shahid", "Khadija", "Rehan", "Amna", "Faisal", "Sidra", "Kamran", "Anum"
]

PAKISTANI_LAST_NAMES = [
    "Khan", "Ahmed", "Malik", "Chaudhry", "Shah", "Qureshi", "Butt", "Sheikh",
    "Iqbal", "Hashmi", "Siddiqui", "Raza", "Hussain", "Abbasi", "Mirza", "Ansari",
    "Farooq", "Baig", "Zaman", "Tahir"
]

EMAIL_DOMAINS = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com"]

def seed_random_pakistani_user(count=1):
    db_path = os.environ.get('DB_PATH', os.path.join(PROJECT_ROOT, 'database', 'spendly.db'))
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    
    # Ensure users table exists
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        )
    ''')
    conn.commit()
    
    seeded_users = []
    
    for _ in range(count):
        inserted = False
        attempts = 0
        max_retries = 100
        
        while not inserted and attempts < max_retries:
            attempts += 1
            first_name = random.choice(PAKISTANI_FIRST_NAMES)
            last_name = random.choice(PAKISTANI_LAST_NAMES)
            name = f"{first_name} {last_name}"
            
            domain = random.choice(EMAIL_DOMAINS)
            rand_num = random.randint(10, 9999)
            email = f"{first_name.lower()}.{last_name.lower()}{rand_num}@{domain}"
            
            password = "Password123!"
            hashed_password = generate_password_hash(password)
            
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                    (name, email, hashed_password)
                )
                conn.commit()
                user_id = cursor.lastrowid
                seeded_users.append({"id": user_id, "name": name, "email": email})
                print(f"[SUCCESS] Seeded user ID {user_id}: {name} <{email}> (Attempt #{attempts})")
                inserted = True
            except sqlite3.IntegrityError:
                # Email collision occurred, retrying with new random email
                continue
                
        if not inserted:
            print(f"[ERROR] Failed to seed user after {max_retries} retries due to email collisions.")

    conn.close()
    return seeded_users

if __name__ == "__main__":
    count = 1
    if len(sys.argv) > 1:
        try:
            count = int(sys.argv[1])
        except ValueError:
            count = 1
    seed_random_pakistani_user(count)
