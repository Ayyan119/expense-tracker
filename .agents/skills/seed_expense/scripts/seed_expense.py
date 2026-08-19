#!/usr/bin/env python3
import os
import sys
import random
import sqlite3
from datetime import date, timedelta

# Ensure project root is in sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

CATEGORIES_DESCRIPTIONS = {
    "Food": [
        ("Weekly groceries", (800.0, 4500.0)),
        ("Dinner with friends", (500.0, 3000.0)),
        ("Coffee & pastries", (150.0, 800.0)),
        ("Lunch meeting", (350.0, 1500.0)),
        ("Supermarket shopping", (1200.0, 5500.0)),
        ("Fast food order", (250.0, 1200.0))
    ],
    "Transport": [
        ("Metro card reload", (200.0, 1000.0)),
        ("Fuel refill", (1500.0, 6000.0)),
        ("Taxi ride", (300.0, 1800.0)),
        ("Car maintenance", (2000.0, 8500.0)),
        ("Parking fee", (50.0, 300.0)),
        ("Bus ticket", (100.0, 500.0))
    ],
    "Bills": [
        ("Electricity bill", (2500.0, 12000.0)),
        ("Internet subscription", (1200.0, 3500.0)),
        ("Mobile recharge", (300.0, 1500.0)),
        ("Water utility payment", (400.0, 2000.0)),
        ("Gas bill payment", (800.0, 3500.0)),
        ("House rent portion", (5000.0, 25000.0))
    ],
    "Health": [
        ("Pharmacy medicines", (200.0, 2500.0)),
        ("Doctor consultation", (1000.0, 3500.0)),
        ("Dental checkup", (1500.0, 5000.0)),
        ("Multivitamins & supplements", (800.0, 3000.0)),
        ("Diagnostic lab test", (1200.0, 4500.0))
    ],
    "Entertainment": [
        ("Movie tickets & snacks", (400.0, 2000.0)),
        ("Gaming subscription", (300.0, 1500.0)),
        ("Concert ticket", (1500.0, 6000.0)),
        ("Streaming service", (250.0, 1000.0)),
        ("Amusement park visit", (800.0, 3000.0))
    ],
    "Shopping": [
        ("New clothes & apparel", (1200.0, 7500.0)),
        ("Electronic accessories", (500.0, 4500.0)),
        ("Footwear purchase", (1500.0, 6000.0)),
        ("Home decor item", (800.0, 3500.0)),
        ("Gift for family", (1000.0, 5000.0))
    ],
    "Other": [
        ("Bookstore purchase", (300.0, 2000.0)),
        ("Courier & shipping fee", (150.0, 800.0)),
        ("Stationery items", (100.0, 600.0)),
        ("Dry cleaning service", (200.0, 1200.0)),
        ("Miscellaneous item", (150.0, 1500.0))
    ]
}

def seed_expenses_for_user(user_id, n_expenses, n_last_months):
    """
    Seeds `n_expenses` random expense records for `user_id` spanning the last `n_last_months` months.
    """
    db_path = os.environ.get('DB_PATH', os.path.join(PROJECT_ROOT, 'database', 'spendly.db'))
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    
    # Check if target user exists
    user = conn.execute("SELECT id, name, email FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        print(f"[ERROR] User ID {user_id} does not exist in the database.")
        conn.close()
        sys.exit(1)
        
    print(f"Adding {n_expenses} expense(s) for User ID {user_id} ({user['name']} <{user['email']}>) across past {n_last_months} month(s)...")
    
    today = date.today()
    max_days_back = max(1, n_last_months * 30)
    categories = list(CATEGORIES_DESCRIPTIONS.keys())
    
    seeded_records = []
    
    for _ in range(n_expenses):
        category = random.choice(categories)
        desc_list = CATEGORIES_DESCRIPTIONS[category]
        description, (min_amt, max_amt) = random.choice(desc_list)
        amount = round(random.uniform(min_amt, max_amt), 2)
        
        random_days = random.randint(0, max_days_back)
        expense_date = (today - timedelta(days=random_days)).strftime("%Y-%m-%d")
        
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO expenses (user_id, category, amount, date, description) VALUES (?, ?, ?, ?, ?)",
            (user_id, category, amount, expense_date, description)
        )
        conn.commit()
        expense_id = cursor.lastrowid
        seeded_records.append({
            "id": expense_id,
            "category": category,
            "amount": amount,
            "date": expense_date,
            "description": description
        })
        print(f"  [+] Added Expense #{expense_id}: {category} | RS {amount:.2f} | {expense_date} | '{description}'")

    conn.close()
    print(f"[SUCCESS] Successfully added {len(seeded_records)} expense(s) for User ID {user_id}.")
    return seeded_records

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python seed_expense.py <user_id> <n_expenses> <n_last_months>")
        print("Example: python seed_expense.py 1 10 3")
        sys.exit(1)
        
    try:
        user_id = int(sys.argv[1])
        n_expenses = int(sys.argv[2])
        n_last_months = int(sys.argv[3])
    except ValueError:
        print("[ERROR] Arguments must be integers: <user_id> <n_expenses> <n_last_months>")
        sys.exit(1)

    seed_expenses_for_user(user_id, n_expenses, n_last_months)
