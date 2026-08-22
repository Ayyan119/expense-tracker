# Spec: Updating Delete Expense Area in Profile

## Overview
The Updating Delete Expense Area in Profile feature refines and secures the expense deletion workflow on the User Profile page. It introduces robust deletion handling with visual confirmation prompts, user feedback via flash notifications, preservation of active profile date filters (`preset`, `start_date`, `end_date`) upon deletion, and support for secure `POST` deletion methods alongside backward-compatible handling, ensuring seamless account management and data integrity.

## Depends on
- Step 4: Profile page redesign
- Step 5: Adding backend connections to profile
- Step 6: Date filter for profile page
- Step 8: Improve edit expense in profile

## Routes
No new routes.

Existing routes modified/enhanced:
- `POST /expenses/<id>/delete` & `GET /expenses/<id>/delete` — Deletes the specified expense belonging to the authenticated user, displays a flash success notification, and redirects back to the originating page (`profile` or `dashboard`) while preserving active query parameters (e.g. date filter presets or custom date ranges) — Logged-in

## Database changes
No database changes.

## Templates
- **Create:** None
- **Modify:**
  - `templates/profile.html` — Enhance the delete action in the Recent Transactions table with clear danger-state styling, explicit confirmation dialog, accessible markup, and passing current filter query parameters to maintain filtered view after deletion.
  - `templates/base.html` — Ensure flash messages are properly styled and rendered on profile and dashboard views if not already present.

## Files to change
- `templates/profile.html` — Update delete button element, confirmation modal/dialog triggers, and preserve filter query parameters in delete action URLs/forms.
- `app.py` — Update `delete_expense` route handler to accept `POST` and `GET`, support filter query parameter forwarding upon redirect to `profile`, flash informative feedback messages ("Expense deleted successfully"), and ensure strict user ownership checks with 404/403 handling.
- `static/css/style.css` — Refine styling for delete action buttons, confirmation prompts, and flash alerts using CSS custom properties.
- `test_app.py` — Add and update integration tests covering expense deletion from the profile page, filter retention after deletion, ownership verification, and flash messages.

## Files to create
- `tests/test_09-updating-delete-expense-area-in-profile.py` — Dedicated test suite validating delete expense functionality from the profile page under various filter conditions.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — use raw sqlite3 via `get_db()`
- Parameterised queries only — use `?` placeholders for SQL statements
- Passwords hashed with werkzeug
- Use CSS variables — never hardcode hex values (`var(--ink)`, `var(--accent)`, `var(--paper-card)`, `var(--danger)`, etc.)
- All templates extend `base.html`
- Defensive redirection: validate `return_to` against allowed routes (`profile`, `dashboard`) to prevent open redirect vulnerabilities
- Ownership check: always ensure `user_id == session['user_id']` when deleting records
- Unauthenticated requests must redirect to `/login` via `@login_required`

## Definition of done
- [ ] Recent Transactions table on `/profile` provides an intuitive and accessible Delete action button for each expense
- [ ] Clicking "Delete" prompts user confirmation before removing the expense
- [ ] Deleting an expense removes the record from the database and immediately updates profile metrics (Total Spent, Transaction Count, Top Category, and Category Breakdown)
- [ ] Active date filters (`preset`, `start_date`, `end_date`) are preserved when redirected back to `/profile` following deletion
- [ ] Deleting an expense displays a clear flash confirmation message to the user
- [ ] Attempting to delete an expense belonging to another user fails safely with an error and does not delete data
- [ ] Unauthenticated requests to delete an expense redirect to `/login`
- [ ] Dedicated test suite `tests/test_09-updating-delete-expense-area-in-profile.py` passes completely
- [ ] All integration tests pass with 100% clean test run (`.venv/bin/python -m pytest`)
