---
name: seed-user
description: >-
  Seeds authentic random Pakistani user records into the SQLite database.
  Generates culturally accurate names, email addresses, and hashed passwords,
  automatically retrying if an email collision occurs.
---

# Seed Pakistani Users (`seed_user`)

This skill provides automated functionality to generate and seed valid random Pakistani user accounts into the application database (`spendly.db`), handling email collision detection with automatic retries.

## Overview

When triggered, this skill inserts user records containing:
- **Name**: Authentic Pakistani first and last name combinations (e.g. *Muhammad Ali*, *Fatima Malik*, *Bilal Chaudhry*, *Zainab Qureshi*).
- **Email**: Formatted as `first.last<random_number>@domain` (e.g. `fatima.malik482@gmail.com`).
- **Password**: Securely hashed password using `werkzeug.security.generate_password_hash`.
- **Duplicate Prevention**: Catches `sqlite3.IntegrityError` upon email collisions and retries automatically until a unique record is created.

---

## Instructions for Execution

### Option 1: Using the Executable Python Helper Script

Run the helper script directly via the virtual environment interpreter:

```bash
# Seed 1 random Pakistani user (default)
.venv/bin/python .agents/skills/seed_user/scripts/seed_user.py

# Seed multiple users (e.g. 5 users)
.venv/bin/python .agents/skills/seed_user/scripts/seed_user.py 5
```

### Option 2: Programmatic Usage in Python

```python
import sqlite3
import random
from werkzeug.security import generate_password_hash

PAKISTANI_FIRST_NAMES = ["Muhammad", "Ali", "Ahmed", "Fatima", "Ayesha", "Zainab", "Hassan", "Hussain", "Bilal", "Sara", "Usman", "Hamza"]
PAKISTANI_LAST_NAMES = ["Khan", "Ahmed", "Malik", "Chaudhry", "Shah", "Qureshi", "Butt", "Sheikh", "Iqbal", "Siddiqui"]
EMAIL_DOMAINS = ["gmail.com", "yahoo.com", "outlook.com"]

def insert_pakistani_user(db_connection):
    max_retries = 100
    for attempt in range(max_retries):
        first = random.choice(PAKISTANI_FIRST_NAMES)
        last = random.choice(PAKISTANI_LAST_NAMES)
        name = f"{first} {last}"
        email = f"{first.lower()}.{last.lower()}{random.randint(10, 9999)}@{random.choice(EMAIL_DOMAINS)}"
        hashed_pwd = generate_password_hash("Password123!")
        
        try:
            cursor = db_connection.cursor()
            cursor.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                (name, email, hashed_pwd)
            )
            db_connection.commit()
            return {"id": cursor.lastrowid, "name": name, "email": email}
        except sqlite3.IntegrityError:
            # Email exists, retry
            continue
    raise RuntimeError("Could not insert unique email after max retries")
```

---

## Verification

To verify that users were added successfully:
```bash
.venv/bin/python -c "import sqlite3; conn = sqlite3.connect('database/spendly.db'); conn.row_factory = sqlite3.Row; print([(r['id'], r['name'], r['email']) for r in conn.execute('SELECT id, name, email FROM users ORDER BY id DESC LIMIT 5').fetchall()])"
```
