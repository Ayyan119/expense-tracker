# Implementation Plan - 01 Database Setup

Establish the core SQLite data layer foundation for Spendly according to the specification in `specs/01_database_setup.md`.

## Goal Description
Implement full SQLite database management in `database/db.py` and integrate it into `app.py`. This includes schema creation for `users` and `expenses` tables with foreign keys and timestamp defaults, connection configuration (`Row` factory & `PRAGMA foreign_keys = ON`), and an idempotent seeding function (`seed_db`) that inserts a demo user and 8 sample expenses covering all categories.

---

## User Review Required

> [!IMPORTANT]
> **Column Name Alignment**: The spec document specifies `password_hash` as the column name for user passwords in the `users` table (previously named `password`). `app.py` and `test_app.py` will be updated accordingly.

> [!NOTE]
> **Demo Account Seed Credentials**: `seed_db()` will seed `demo@spendly.com` with password `demo123` as specified in the spec document.

---

## Open Questions
None. All requirements are explicitly detailed in `specs/01_database_setup.md`.

---

## Proposed Changes

### Database Layer

#### [MODIFY] [db.py](file:///home/jiggra/expense-tracker/expense-tracker/database/db.py)

- Ensure `get_db()` sets `row_factory = sqlite3.Row` and executes `PRAGMA foreign_keys = ON;`.
- Update `init_db()` schema definition:
  - `users` table:
    - `id` INTEGER PRIMARY KEY AUTOINCREMENT
    - `name` TEXT NOT NULL
    - `email` TEXT UNIQUE NOT NULL
    - `password_hash` TEXT NOT NULL
    - `created_at` TEXT DEFAULT (datetime('now'))
  - `expenses` table:
    - `id` INTEGER PRIMARY KEY AUTOINCREMENT
    - `user_id` INTEGER NOT NULL (FOREIGN KEY -> `users.id` ON DELETE CASCADE)
    - `amount` REAL NOT NULL
    - `category` TEXT NOT NULL
    - `date` TEXT NOT NULL
    - `description` TEXT
    - `created_at` TEXT DEFAULT (datetime('now'))
- Update `seed_db()`:
  - Check `SELECT 1 FROM users LIMIT 1`. If data exists, return early without inserting duplicates.
  - Insert Demo User: `Demo User`, `demo@spendly.com`, `generate_password_hash("demo123")`.
  - Insert 8 sample expenses spread across all fixed categories (`Food`, `Transport`, `Bills`, `Health`, `Entertainment`, `Shopping`, `Other`) with valid `YYYY-MM-DD` dates.

```python
# Draft snippet for db.py schema
def init_db():
    db = get_db()
    db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        )
    ''')
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
    db.commit()
```

---

### Backend Application

#### [MODIFY] [app.py](file:///home/jiggra/expense-tracker/expense-tracker/app.py)

- Update user query columns from `password` to `password_hash` in `register` and `login` functions.
- Update fixed category list to include all 7 categories: `['Food', 'Transport', 'Bills', 'Health', 'Entertainment', 'Shopping', 'Other']`.
- Verify `init_db()` and `seed_db()` run inside `app.app_context()`.

---

### Test Suite

#### [MODIFY] [test_app.py](file:///home/jiggra/expense-tracker/expense-tracker/test_app.py)

- Update assertions and helper data in `test_login_logout`, `test_add_expense`, `test_edit_expense`, `test_delete_expense` to account for the `password_hash` column name and `demo@spendly.com` seed data.
- Add test `test_seed_db_idempotency` to verify calling `seed_db()` multiple times does not insert duplicate records.
- Add test `test_foreign_key_enforcement` to verify inserting an expense with a non-existent `user_id` fails.

---

## Verification Plan

### Automated Tests
Run the test suite using pytest in the virtual environment:
```bash
.venv/bin/python -m pytest
```

### Manual Verification
1. Verify database initialization by starting Flask or inspecting the created SQLite file:
   ```bash
   .venv/bin/python -c "from database.db import get_db, init_db, seed_db; init_db(); seed_db()"
   ```
2. Verify foreign key enforcement and seed user data exist in the database.
