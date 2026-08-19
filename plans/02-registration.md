# Implementation Plan - 02 Registration

Implement user registration for Spendly according to the specification in `specs/02-registration.md`.

## Goal Description
Provide a secure and seamless user onboarding flow that allows new users to register an account with their full name, email address, and a secure password (minimum 8 characters).

Key components:
1. Render a clean registration view adhering to Spendly's design system tokens and extending `templates/base.html`.
2. Validate user input (presence of all fields, minimum password length >= 8 characters,confirm password input is given and shoudld throw error if not match and uniqueness of email address).
3. User name should be a String and start with Capital letter.
4. Strict implementation of email it should follow the exact email pattern (123@123 this is invalid)
5. whenever something is not match like password, then remove both passwords and show error, if email or name has any problem, then don't remove the text from the input box (user should corrent them, not start writing from start)
6. Safely hash passwords using `werkzeug.security.generate_password_hash`.
7. Persist new user records to the SQLite `users` table via parameterized SQL statements.
8. Initialize the user session (`user_id`, `user_name`, `user_email`) upon successful registration and redirect to the dashboard.
9. Prevent already authenticated users from accessing `/register` by redirecting them to `/dashboard`.
10. Ensure comprehensive automated integration tests in `test_app.py`.

---

## User Review Required

> [!NOTE]
> All database queries will strictly utilize parameterized SQL (`?` placeholders) and no ORM / SQLAlchemy dependencies will be used, per project guidelines.

> [!IMPORTANT]
> The database schema already contains the `users` table (`id`, `name`, `email`, `password_hash`, `created_at`), so no database migration or schema changes are needed.

---

## Open Questions
None. All requirements and error handling rules are explicitly detailed in `specs/02-registration.md`.

---

## Proposed Changes

### Application Layer & Routing

#### [MODIFY] [app.py](file:///home/jiggra/expense-tracker/app.py)

- Review and refine the `/register` handler for both `GET` and `POST` methods:
  - Check if `session.get('user_id')` is set; if so, redirect immediately to `url_for('dashboard')`.
  - In `POST`, extract `name`, `email`, and `password`.
  - Validate that `name`, `email`, and `password` are non-empty. Return error: `"All fields are required."`.
  - Validate `len(password) >= 8`. Return error: `"Password must be at least 8 characters long."`.
  - Check for email uniqueness via parameterized SQL: `SELECT id FROM users WHERE email = ?`. If user exists, return error: `"An account with this email already exists."`.
  - Hash password using `generate_password_hash(password)`.
  - Insert user record: `INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)`.
  - Commit transaction, retrieve `lastrowid`, populate `session` dictionary (`user_id`, `user_name`, `user_email`), and redirect to `url_for('dashboard')`.

```python
@app.route("/register", methods=["GET", "POST"])
def register():
    """Handles new user registration."""
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not name or not email or not password:
            return render_template("register.html", error="All fields are required.")

        if len(password) < 8:
            return render_template("register.html", error="Password must be at least 8 characters long.")

        db = get_db()
        existing_user = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing_user:
            return render_template("register.html", error="An account with this email already exists.")

        hashed_password = generate_password_hash(password)
        try:
            cursor = db.cursor()
            cursor.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                (name, email, hashed_password)
            )
            db.commit()

            user_id = cursor.lastrowid
            session["user_id"] = user_id
            session["user_name"] = name
            session["user_email"] = email

            return redirect(url_for("dashboard"))
        except Exception:
            return render_template("register.html", error="An error occurred. Please try again.")

    return render_template("register.html")
```

---

### Templates & Frontend

#### [MODIFY] [templates/register.html](file:///home/jiggra/expense-tracker/templates/register.html)

- Ensure semantic HTML structure extending `base.html`.
- Provide clean input fields (`name`, `email`, `password`) with appropriate labels, placeholders, and autocomplete attributes.
- Render conditional error container `.auth-error` when `error` context variable is provided.
- Provide a navigation link to `/login` for existing users.

```html
{% extends "base.html" %}

{% block title %}Create account — Spendly{% endblock %}

{% block content %}
<section class="auth-section">
    <div class="auth-container">
        <div class="auth-header">
            <h1 class="auth-title">Create your account</h1>
            <p class="auth-subtitle">Start tracking your expenses today</p>
        </div>

        <div class="auth-card">
            {% if error %}
            <div class="auth-error">{{ error }}</div>
            {% endif %}

            <form method="POST" action="{{ url_for('register') }}">
                <div class="form-group">
                    <label for="name">Full name</label>
                    <input type="text" id="name" name="name"
                           class="form-input" placeholder="e.g. Tariq Khan"
                           required autofocus>
                </div>
                <div class="form-group">
                    <label for="email">Email address</label>
                    <input type="email" id="email" name="email"
                           class="form-input" placeholder="name@example.com"
                           required>
                </div>
                <div class="form-group">
                    <label for="password">Password</label>
                    <input type="password" id="password" name="password"
                           class="form-input" placeholder="Min. 8 characters"
                           required>
                </div>
                <button type="submit" class="btn-submit">Create account</button>
            </form>
        </div>

        <p class="auth-switch">
            Already have an account?
            <a href="{{ url_for('login') }}">Sign in</a>
        </p>
    </div>
</section>
{% endblock %}
```

---

### Test Suite

#### [MODIFY] [test_app.py](file:///home/jiggra/expense-tracker/test_app.py)

- Expand registration test cases to verify:
  1. `test_register_page_render`: GET `/register` returns 200 and renders form fields.
  2. `test_registration_success`: POST `/register` with valid credentials creates user, redirects to `/dashboard`, and establishes session.
  3. `test_registration_missing_fields`: POST `/register` with empty fields returns error `"All fields are required."`.
  4. `test_registration_short_password`: POST `/register` with password < 8 characters returns `"Password must be at least 8 characters long."`.
  5. `test_registration_duplicate_email`: POST `/register` with existing email returns `"An account with this email already exists."`.
  6. `test_registration_redirect_if_logged_in`: Authenticated user accessing `/register` gets redirected to `/dashboard`.

---

## Verification Plan

### Automated Tests
Execute the entire test suite using pytest in the virtual environment:
```bash
.venv/bin/python -m pytest -v
```

Run specific registration tests:
```bash
.venv/bin/python -m pytest test_app.py -k "register" -v
```

### Manual Verification
1. Start Flask development server: `.venv/bin/python app.py`.
2. Open browser at `http://127.0.0.1:5001/register`.
3. Submit form with empty inputs → verify validation message.
4. Submit form with password under 8 characters → verify error alert.
5. Register with an already existing email (`demo@spendly.com`) → verify duplicate email error.
6. Register with new credentials (e.g. `Fatima Ali`, `fatima@example.com`, `supersecure123`) → verify automatic login and redirect to `/dashboard`.
7. Try navigating back to `http://127.0.0.1:5001/register` while logged in → verify immediate redirect back to `/dashboard`.
