# Spec: Login and Logout

## Overview
The Login and Logout feature provides secure user session management for Spendly. Registered users can authenticate using their email address and password via the login interface. Upon successful credential verification using `werkzeug.security.check_password_hash`, the application establishes a session containing the user's ID, name, and email, and redirects them to their dashboard. If invalid credentials or empty input fields are submitted, clear error notifications are rendered. Authenticated users can terminate their active session via the `/logout` endpoint, which securely resets session state and redirects to the landing page.

## Depends on
- 01 Database Setup (`specs/01_database_setup.md`)
- 02 Registration (`specs/02-registration.md`)

## Routes
- `GET /login` — Display login form — Public (redirects to `/dashboard` if already logged in)
- `POST /login` — Process login credentials, verify password hash against database, establish user session, and redirect — Public
- `GET /logout` — Clear session state and redirect to landing page — Logged-in / Public

## Database changes
No database changes (uses existing `users` table schema: `id`, `name`, `email`, `password_hash`, `created_at`).

## Templates
- **Create:** None
- **Modify:** `templates/login.html` — Ensure layout extends `base.html`, includes form inputs for `email` and `password`, renders error notifications, links to registration, and utilizes standard CSS variables.

## Files to change
- `app.py` — Verify and refine `/login` (GET/POST) and `/logout` route handlers, session management, and credential validation using parameterized SQL queries.
- `templates/login.html` — Update or refine layout, design token compliance, error handling, and form field bindings.
- `test_app.py` — Ensure full test coverage for login and logout flows (`test_login_logout`).

## Files to create
- `specs/03-login-and-logout.md`

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`

## Definition of done
- [ ] `GET /login` renders the user login form extending `base.html`
- [ ] Submitting empty email or password fields returns an error: "Please provide email and password."
- [ ] Submitting non-existent email or incorrect password returns an error: "Invalid email or password."
- [ ] Submitting valid credentials sets `session['user_id']`, `session['user_name']`, `session['user_email']` and redirects to `/dashboard`
- [ ] Authenticated users accessing `GET /login` are redirected to `/dashboard`
- [ ] Accessing `GET /logout` clears all session data (`session.clear()`) and redirects to `/` (landing page)
- [ ] Pytest integration test `pytest test_app.py -k test_login_logout` passes cleanly with 100% success rate
