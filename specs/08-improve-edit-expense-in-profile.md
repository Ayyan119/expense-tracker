# Spec: Improve Edit Expense Area in Profile

## Overview
The Improve Edit Expense Area in Profile feature enhances the user experience by adding direct transaction management actions (Edit and Delete) to the Recent Transactions table on the User Profile page. Additionally, it updates the edit expense workflow with contextual navigation support (so users editing an expense from Profile return smoothly to the Profile view), expands category coverage in the edit form to match all standard Spendly categories, and ensures robust UI consistency across screens.

## Depends on
- Step 4: Profile page redesign
- Step 5: Adding backend connections to profile
- Step 6: Date filter for profile page
- Step 7: Add expense

## Routes
No new routes.

Existing routes modified/enhanced:
- `GET /expenses/<id>/edit` — Supports an optional `return_to` / `next` query parameter to return users to `/profile` or `/dashboard` — Logged-in
- `POST /expenses/<id>/edit` — Redirects the user back to their origin page (`profile` or `dashboard`) upon successful update or cancellation — Logged-in
- `GET /expenses/<id>/delete` — Supports an optional `return_to` parameter to redirect back to `/profile` when deleted from the profile page — Logged-in

## Database changes
No database changes.

## Templates
- **Create:** None
- **Modify:**
  - `templates/profile.html` — Add an "Actions" column to the Recent Transactions table containing accessible "Edit" and "Delete" action links for each logged transaction.
  - `templates/edit_expense.html` — Ensure all Spendly categories (`Food`, `Transport`, `Bills`, `Health`, `Entertainment`, `Shopping`, `Other`) are present in the dropdown, preserve return redirect path in form action and Cancel button, and maintain design system token styling.

## Files to change
- `templates/profile.html` — Add Actions header and row buttons (Edit / Delete) in Recent Transactions table with contextual `return_to=profile` parameter.
- `templates/edit_expense.html` — Synchronize category options with `CATEGORIES` constant, support contextual cancel/back destination.
- `app.py` — Update `edit_expense` and `delete_expense` route handlers to parse and respect safe return URL targets (`return_to` / `next`), ensuring users return to `/profile` or `/dashboard` appropriately while passing full `CATEGORIES` list to the template.
- `test_app.py` (or `tests/test_08-improve-edit-expense-in-profile.py`) — Integration tests verifying profile transaction action links, edit workflow redirects back to profile, delete workflow from profile, and all category selections.

## Files to create
- `tests/test_08-improve-edit-expense-in-profile.py` — Dedicated test suite validating edit/delete capabilities and flows originating from the profile page.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — use raw sqlite3 via `get_db()`
- Parameterised queries only — use `?` placeholders for SQL statements
- Passwords hashed with werkzeug
- Use CSS variables — never hardcode hex values (`var(--ink)`, `var(--accent)`, `var(--paper-card)`, etc.)
- All templates extend `base.html`
- Defensive redirection: validate `return_to` against allowed internal routes to prevent open redirect vulnerabilities
- Ownership check: always ensure `user_id == session['user_id']` when querying, editing, or deleting expenses
- Unauthenticated requests must redirect to `/login` via `@login_required`

## Definition of done
- [ ] Recent Transactions table on `/profile` contains an "Actions" column with "Edit" and "Delete" buttons for each expense
- [ ] Clicking "Edit" on a profile transaction opens `/expenses/<id>/edit` with `return_to=profile`
- [ ] `edit_expense.html` dropdown contains all standard categories: Food, Transport, Bills, Health, Entertainment, Shopping, Other
- [ ] Submitting the edit form successfully updates the record and redirects back to `/profile` when initiated from profile
- [ ] Clicking "Cancel" on the edit form returns the user to `/profile` when initiated from profile
- [ ] Deleting a transaction from the profile table prompts for confirmation and returns back to `/profile`
- [ ] Total spent, transaction counts, and category breakdowns on `/profile` immediately reflect edited or deleted expense updates
- [ ] Dedicated test suite `tests/test_08-improve-edit-expense-in-profile.py` passes completely
- [ ] All integration tests pass with 100% clean test run (`.venv/bin/python -m pytest`)
