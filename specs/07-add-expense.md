# Spec: Add Expense

## Overview
The Add Expense feature allows authenticated users to log new expense transactions by specifying the category, amount, transaction date, and an optional description. Recording new transactions is a foundational capability of the Spendly personal finance tracker that feeds into user dashboards, profile financial analytics, category breakdowns, and transaction histories.

## Depends on
- Step 1: Database setup
- Step 2: User registration
- Step 3: Login & Logout

## Routes
- `GET /expenses/add` — Renders the Add Expense form with category selection, amount, date, and description inputs — Logged-in
- `POST /expenses/add` — Validates form data, inserts the expense record linked to the authenticated user into SQLite, and redirects to the dashboard — Logged-in

## Database changes
No database changes.

## Templates
- **Create:** None
- **Modify:** `templates/add_expense.html` — Update category dropdown to include all standard Spendly categories (Food, Transport, Bills, Health, Entertainment, Shopping, Other), preserve form values upon validation errors, ensure modern design system token usage and auto-fill today's date.

## Files to change
- `app.py` — Verify and refine `/expenses/add` route handler for input validation (positive amount, valid date, required category), parameterized SQL insertion, and flash/error messaging.
- `templates/add_expense.html` — Ensure all categories are available, inputs styled consistently with Spendly CSS variables, and date defaulted to current date.
- `test_app.py` — Add and enhance integration test coverage for adding expenses (GET form display, valid POST creation, error validation on invalid/negative amounts or missing inputs, login protection).

## Files to create
No new files created.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — use raw sqlite3 via `get_db()`
- Parameterised queries only — use `?` placeholders for SQL statements
- Passwords hashed with werkzeug
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Strict input validation: amount must be a positive float (`amount > 0`), category and date must not be empty
- Support all standard categories: `Food`, `Transport`, `Bills`, `Health`, `Entertainment`, `Shopping`, `Other`
- Unauthenticated access must redirect to `/login` via `@login_required`

## Definition of done
- [ ] Navigating to `/expenses/add` while logged in renders the Add Expense form
- [ ] Category dropdown contains all standard categories: Food, Transport, Bills, Health, Entertainment, Shopping, Other
- [ ] Date input automatically defaults to the current date if empty
- [ ] Submitting valid data inserts the expense record in the database associated with the logged-in `user_id` and redirects to `/dashboard`
- [ ] Newly created expense immediately appears in the user dashboard and profile transaction lists and updates total spend calculations
- [ ] Submitting with missing required fields displays an informative error message without crashing
- [ ] Submitting negative, zero, or non-numeric amount values displays a validation error message
- [ ] Accessing `/expenses/add` (GET or POST) without being logged in redirects to `/login`
- [ ] All integration tests pass with 100% clean test run (`.venv/bin/python -m pytest`)
