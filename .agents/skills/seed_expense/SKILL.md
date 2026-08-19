---
name: seed_expense
description: >-
  Generates and adds realistic random expenses for a specific user ID across a target timeframe (last N months).
  Accepts target user_id, number of expenses to generate (n_expenses), and past month range (n_last_months).
---

# Seed Expenses for User (`seed_expense`)

This skill generates and inserts realistic expense records for a designated user ID in the Spendly application database (`spendly.db`), distributing dates randomly within the specified past `N` months.

## Requirements & Parameters

- **`user_id`** *(integer, required)*: The target user's ID in the `users` table.
- **`n_expenses`** *(integer, required)*: Total number of expense records to generate.
- **`n_last_months`** *(integer, required)*: Time window in past months (from current date) for randomly assigning expense dates.

Each generated expense will randomly assign:
- **Category**: Picked from fixed categories (`Food`, `Transport`, `Bills`, `Health`, `Entertainment`, `Shopping`, `Other`).
- **Amount**: Category-appropriate realistic numeric amount.
- **Date**: Formatted as `YYYY-MM-DD` within the last `n_last_months` months.
- **Description**: Realistic expense description matched to the chosen category.

---

## Instructions for Execution

### Using the Helper Script

Run the helper script directly via the virtual environment interpreter:

```bash
# Usage: .venv/bin/python .agents/skills/seed_expense/scripts/seed_expense.py <user_id> <n_expenses> <n_last_months>

# Example: Add 10 random expenses for User ID 1 spread over the last 3 months
.venv/bin/python .agents/skills/seed_expense/scripts/seed_expense.py 1 10 3
```

---

## Programmatic Usage in Python

```python
import sqlite3
import random
from datetime import date, timedelta

CATEGORIES = ["Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other"]

def add_user_expenses(user_id, n_expenses, n_last_months, db_path="database/spendly.db"):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    
    # Check user existence
    user = conn.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        raise ValueError(f"User ID {user_id} does not exist.")
        
    today = date.today()
    max_days = n_last_months * 30
    
    for _ in range(n_expenses):
        category = random.choice(CATEGORIES)
        amount = round(random.uniform(200.0, 5000.0), 2)
        exp_date = (today - timedelta(days=random.randint(0, max_days))).strftime("%Y-%m-%d")
        desc = f"Sample {category} expense"
        
        conn.execute(
            "INSERT INTO expenses (user_id, category, amount, date, description) VALUES (?, ?, ?, ?, ?)",
            (user_id, category, amount, exp_date, desc)
        )
    conn.commit()
    conn.close()
```

---

## Verification

Verify expenses added for the target user:
```bash
.venv/bin/python -c "import sqlite3; conn = sqlite3.connect('database/spendly.db'); conn.row_factory = sqlite3.Row; print([(r['id'], r['category'], r['amount'], r['date'], r['description']) for r in conn.execute('SELECT id, category, amount, date, description FROM expenses WHERE user_id = ? ORDER BY date DESC', (1,)).fetchall()])"
```
