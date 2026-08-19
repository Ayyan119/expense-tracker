# Spec: Registration

## Overview
The Registration feature allows new users to create an account on Spendly with their full name, email address, and a secure password (at least 8 characters). Upon registration, the user's password is securely hashed using `werkzeug.security`, their details are stored in the SQLite database, their session is initialized,a message of successfully register shown and they are redirected directly to the dashboard. This feature serves as the entry point for individual user authentication and personalized expense tracking.

## Depends on
- 01 Database Setup (`specs/01_database_setup.md`)

## Routes
- `GET /register` — Display registration form — Public (redirects to `/dashboard` if logged in)
- `POST /register` — Process registration form submission, validate input, hash password, create user account, and establish session — Public

## Database changes
No database changes (uses existing `users` table schema: `id`, `name`, `email`, `password_hash`, `created_at`).

## Templates
- **Create:** None
- **Modify:** `templates/register.html` — Ensure layout extends `base.html`, includes form input fields for `name`, `email`, and `password`, and renders error notifications using standard CSS variables.

## Files to change
- `app.py` — Validate registration inputs, check email uniqueness using parameterized queries, hash passwords with `generate_password_hash`, set session variables, and handle error responses.
- `templates/register.html` — Update or refine template structure and error presentation.
- `test_app.py` — Ensure comprehensive test coverage for registration flows and edge cases (`test_registration`).

## Files to create
- `specs/02-registration.md`

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`

## Definition of done
- [ ] GET `/register` renders the user registration form extending `base.html`
- [ ] Submitting empty fields returns an error: "All fields are required."
- [ ] Submitting a password shorter than 8 characters returns an error: "Password must be at least 8 characters long."
- [ ] Submitting an existing email returns an error: "An account with this email already exists."
- [ ] Submitting valid data inserts a user record with a hashed password into the database using parameterized SQL
- [ ] Successful registration sets `session['user_id']`, `session['user_name']`, `session['user_email']` and redirects to `/dashboard`
- [ ] Already authenticated users accessing `/register` are redirected to `/dashboard`
- [ ] Pytest integration test `pytest test_app.py -k test_registration` passes cleanly with 100% success rate
