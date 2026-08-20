# Implementation Plan - 03 Login and Logout

Implement user authentication and session termination for Spendly according to the specification in `specs/03-login-and-logout.md`.

## Goal Description
Provide secure authentication and session management allowing registered users to sign in with their email and password, access their personalized dashboard, and log out securely.

Key components:
1. Render a clean login interface extending `templates/base.html` that adheres to Spendly design tokens and CSS variables.
2. Validate user input on submission (verify both email and password are provided).
3. Query the user record from the SQLite database using parameterized SQL (`?` placeholder).
4. Verify submitted credentials against the stored password hash using `werkzeug.security.check_password_hash`.
5. Establish a secure session upon successful authentication (`session['user_id']`, `session['user_name']`, `session['user_email']`) and redirect to `/dashboard`.
6. Handle authentication failures gracefully by rendering specific error messages and preserving entered email values.
7. Redirect already authenticated users away from `/login` to `/dashboard`.
8. Provide a `/logout` route that clears session data (`session.clear()`) and redirects to the landing page `/`.
9. Add full integration test coverage in `test_app.py` for login/logout workflows and edge cases.

---

## User Review Required

> [!NOTE]
> All database queries will strictly utilize parameterized SQL (`SELECT * FROM users WHERE email = ?`) with no ORM or SQLAlchemy dependencies.

> [!IMPORTANT]
> The database schema already contains the `users` table (`id`, `name`, `email`, `password_hash`, `created_at`), and `database/db.py` seeds a demo user (`demo@spendly.com` / `demo123`). No database migrations or schema alterations are required.

---

## Open Questions
None. All requirements, routes, session behaviors, and error messages are specified in `specs/03-login-and-logout.md`.

---

## Proposed Changes

### Backend Application & Session Management

#### [MODIFY] [app.py](file:///home/jiggra/expense-tracker/app.py)

- Refine `/login` route handler:
  - If `"user_id" in session`: redirect immediately to `url_for("dashboard")`.
  - In `POST` request:
    - Extract and sanitize `email` (`strip()`) and extract `password`.
    - If `email` or `password` is missing: render `login.html` with `error="Please provide email and password."` and preserve `email=email`.
    - Query user using parameterized SQL: `SELECT * FROM users WHERE email = ?`.
    - Verify password hash using `check_password_hash(user["password_hash"], password)`.
    - If valid: populate session (`session["user_id"] = user["id"]`, `session["user_name"] = user["name"]`, `session["user_email"] = user["email"]`) and redirect to `url_for("dashboard")`.
    - If invalid or user not found: render `login.html` with `error="Invalid email or password."` and preserve `email=email`.
- Refine `/logout` route handler:
  - Invoke `session.clear()` to completely purge session cookies and user keys.
  - Redirect to `url_for("landing")`.

```python
@app.route("/login", methods=["GET", "POST"])
def login():
    """Handles user login and authentication."""
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not email or not password:
            return render_template("login.html", error="Please provide email and password.", email=email)

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["user_email"] = user["email"]
            return redirect(url_for("dashboard"))

        return render_template("login.html", error="Invalid email or password.", email=email)

    return render_template("login.html")


@app.route("/logout")
def logout():
    """Logs out the user by clearing the session."""
    session.clear()
    return redirect(url_for("landing"))
```

---

### Templates & Frontend

#### [MODIFY] [templates/login.html](file:///home/jiggra/expense-tracker/templates/login.html)

- Ensure template extends `base.html` and uses dynamic URL routing `url_for('login')` and `url_for('register')`.
- Ensure email input preserves value (`value="{{ email or '' }}"`) upon validation failure.
- Ensure error messages render cleanly inside `.auth-error` banner using CSS variables defined in `style.css`.
- Ensure clean semantic form markup with proper `name`, `id`, `type`, and `required` attributes.

```html
{% extends "base.html" %}

{% block title %}Sign in — Spendly{% endblock %}

{% block content %}
<section class="auth-section">
    <div class="auth-container">
        <div class="auth-header">
            <h1 class="auth-title">Welcome back</h1>
            <p class="auth-subtitle">Sign in to your Spendly account</p>
        </div>

        <div class="auth-card">
            {% if error %}
            <div class="auth-error">{{ error }}</div>
            {% endif %}

            <form method="POST" action="{{ url_for('login') }}">
                <div class="form-group">
                    <label for="email">Email address</label>
                    <input type="email" id="email" name="email"
                           class="form-input" placeholder="demo@spendly.com"
                           value="{{ email or '' }}"
                           required autofocus>
                </div>
                <div class="form-group">
                    <label for="password">Password</label>
                    <input type="password" id="password" name="password"
                           class="form-input" placeholder="Your password"
                           required>
                </div>
                <button type="submit" class="btn-submit">Sign in</button>
            </form>
        </div>

        <p class="auth-switch">
            Don't have an account?
            <a href="{{ url_for('register') }}">Create one free</a>
        </p>
    </div>
</section>
{% endblock %}
```

---

### Test Suite

#### [MODIFY] [test_app.py](file:///home/jiggra/expense-tracker/test_app.py)

Add comprehensive tests for login and logout:
- `test_login_page_render`: GET `/login` renders status 200 with title "Welcome back" and email/password inputs.
- `test_login_success`: POST `/login` with valid seeded credentials (`demo@spendly.com` / `demo123`) establishes session and redirects to dashboard with welcome message.
- `test_login_missing_fields`: POST `/login` with empty email or empty password displays `"Please provide email and password."`.
- `test_login_invalid_password`: POST `/login` with valid email but incorrect password displays `"Invalid email or password."`.
- `test_login_nonexistent_email`: POST `/login` with non-existent email displays `"Invalid email or password."`.
- `test_login_redirect_if_logged_in`: Authenticated client accessing `GET /login` gets redirected to `/dashboard`.
- `test_logout_clears_session`: `GET /logout` clears session and redirects to landing page `/`.

---

## Verification Plan

### Automated Tests
Execute the pytest test suite via virtualenv runner:
```bash
.venv/bin/python -m pytest test_app.py -k "login or logout" -v
.venv/bin/python -m pytest -v
```

### Manual Verification
1. Start development server: `.venv/bin/python app.py`.
2. Visit `http://127.0.0.1:5001/login`.
3. Test empty inputs submission → verify "Please provide email and password." error banner.
4. Test invalid password (e.g. `wrongpass`) → verify "Invalid email or password." error banner and verify email field preserves value.
5. Submit valid demo credentials (`demo@spendly.com` / `demo123`) → verify redirect to dashboard with personalized greeting.
6. Attempt to navigate back to `http://127.0.0.1:5001/login` while logged in → verify automatic redirect back to `/dashboard`.
7. Click "Sign out" / navigate to `/logout` → verify session termination and redirect to landing page.
