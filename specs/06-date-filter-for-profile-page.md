# Spec: Date Filter for Profile Page

## Overview
This feature introduces date range filtering capabilities to the `/profile` page in Spendly. Users can filter their spending profile by specifying `start_date` and `end_date` parameters via query parameters, dynamically recalculating their summary metrics (Total Spent, Transactions count, Top Category), filtering the recent transactions list, and updating the category breakdown percentages to reflect the chosen timeframe.

## Depends on
- Step 1: Database setup
- Step 2: User registration
- Step 3: Login & Logout
- Step 4: Profile Page Redesign
- Step 5: Profile Page Backend Connections

## Routes
No new routes.
- `GET /profile` — modified to accept optional query parameters (`start_date`, `end_date`) to filter profile financial metrics and transaction lists for the logged-in user.

## Database changes
No database changes.

## Templates
- **Create:** None
- **Modify:** `templates/profile.html` — add a date filter form bar (containing start date input, end date input, filter submit button, and clear/reset button) and maintain active filter state in inputs.

## Files to change
- `app.py` — update `profile()` route handler to parse `start_date` and `end_date` query arguments and apply SQL filtering across summary stats, recent transactions, and category breakdown.
- `templates/profile.html` — incorporate date filter UI controls styled with existing CSS design tokens and persist filter values in input fields.
- `static/css/style.css` — add styles for the profile date filter container and form inputs if needed, reusing CSS variables.
- `test_app.py` — add test cases verifying date filtering functionality on the profile page (e.g. date range match, empty results, clearing filters).

## Files to create
No new files created.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — use raw sqlite3 via `get_db()`
- Parameterised queries only — always use `?` placeholders for `start_date` and `end_date` conditions
- Passwords hashed with werkzeug
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Preserve user info card display (name, email, member since) regardless of date filter applied
- Ensure summary cards (Total Spent, Transactions, Top Category) accurately compute values matching the filtered date range
- Ensure recent transactions and category breakdown strictly reflect expenses within the specified date boundaries (`start_date <= date <= end_date`)
- Handle cases where no transactions exist within the selected date window gracefully without crashes or zero-division errors
- Provide a reset/clear filter link that restores the default view

## Definition of done
- [ ] Profile page displays a date filter form with `start_date`, `end_date`, an Apply/Filter button, and a Clear/Reset button
- [ ] Submitting `start_date` filters expenses where `date >= start_date` across stats, recent transactions, and category breakdown
- [ ] Submitting `end_date` filters expenses where `date <= end_date` across stats, recent transactions, and category breakdown
- [ ] Submitting both `start_date` and `end_date` filters expenses strictly within the date range
- [ ] Filter input fields retain the selected date values upon form submission
- [ ] Clicking the Clear / Reset button resets filters and shows all user transactions
- [ ] Selecting a date range with zero transactions renders clean empty states without errors
- [ ] All existing and new integration tests pass with 100% success rate (`.venv/bin/python -m pytest`)
