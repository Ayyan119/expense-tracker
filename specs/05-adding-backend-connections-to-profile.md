# Spec: Profile Page Backend Connections

## Overview
This feature replaces the hardcoded mock data in the `/profile` view route with dynamic database queries connected to SQLite. It fetches the authenticated user's actual profile details, calculates aggregate metrics (total spending, total transaction count, top spending category), retrieves real recent transaction entries, and computes category breakdown percentages dynamically from the database.

## Depends on
- Step 1: Database setup
- Step 2: User registration
- Step 3: Login & Logout
- Step 4: Profile Page Redesign (UI layout)

## Routes
- `GET /profile` — renders the user profile with dynamic database metrics — logged-in only (redirects to `/login` if unauthenticated)

## Database changes
No database changes. The existing `users` and `expenses` tables are sufficient.

## Templates
- **Create:** None
- **Modify:** `templates/profile.html` (if necessary to accommodate empty state handling or minor variable format adjustments; ensure badge classes map cleanly to categories)

## Files to change
- `app.py` — update `profile()` route handler to query `users` and `expenses` tables for logged-in `session["user_id"]`
- `test_app.py` — update/add unit tests verifying dynamic database profile rendering for authenticated users

## Files to create
No new files created.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — use raw sqlite3 via `get_db()`
- Parameterised queries only — always use `?` placeholders to protect against SQL injection
- Passwords hashed with werkzeug
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Derive user initials dynamically from user's full name (e.g. "Demo User" -> "DU")
- Format `member_since` date from `created_at` timestamp in `users` table (e.g., "March 2026")
- Compute `total_spent`, `transaction_count`, and `top_category` dynamically from `expenses` table for `user_id`
- Handle empty expense history gracefully (e.g., total_spent = 0.00, transaction_count = 0, top_category = "N/A" or "None")
- Map expense categories to proper badge CSS classes (e.g. `badge-food`, `badge-bills`, `badge-shopping`, `badge-health`, `badge-transport`, `badge-entertainment`, `badge-other`)

## Definition of done
- [ ] Unauthenticated requests to `/profile` redirect to `/login`
- [ ] Authenticated requests to `/profile` return status code 200
- [ ] User details (name, email, initials, member since date) reflect actual `users` DB table records
- [ ] Summary metrics (`total_spent`, `transaction_count`, `top_category`) accurately reflect user's `expenses` DB entries
- [ ] Recent transactions list displays user's latest recorded expenses from DB sorted by date descending
- [ ] Category breakdown calculates actual sum amounts and percentages per category from DB
- [ ] Accounts with zero logged expenses render cleanly without zero-division or null rendering errors
- [ ] `pytest` test suite passes with 100% success rate
