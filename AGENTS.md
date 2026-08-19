# Agent Guide & Repository Architecture

Welcome to **Spendly** — a lightweight personal finance and expense tracking web application built with Python (Flask) and SQLite.

This document serves as a guide for AI agents and developers working on this codebase.

---

## 1. Project Overview

Spendly allows users to log expenses, categorize spending, track monthly budgets, and analyze financial patterns.

- **Backend Framework**: Python 3.10+, Flask
- **Database**: SQLite3
- **Frontend**: Jinja2 HTML templates, Vanilla CSS / JS (No heavy client-side JS frameworks)
- **Testing Framework**: `pytest` & `pytest-flask`

---

## 2. Directory Structure

```
expense-tracker/
├── app.py                  # Main Flask application entrypoint & routing
├── test_app.py             # Integration test suite using pytest
├── requirements.txt        # Python dependencies
├── AGENTS.md               # Developer & AI agent workflow instructions
├── database/
│   ├── db.py               # Database initialization, schema setup, & seed data logic
│   └── spendly.db          # SQLite database file
├── static/
│   ├── css/
│   │   ├── style.css       # Core global stylesheet & design system CSS variables
│   │   └── landing.css     # Redesigned hero section & landing page component styles
│   └── js/
│       └── main.js         # Base client-side scripts
└── templates/
    ├── base.html           # Shared layout template (navbar, footer, script blocks)
    ├── landing.html        # Public hero page with interactive video modal & mock UI
    ├── dashboard.html      # Authenticated user dashboard & transaction list
    ├── login.html          # Authentication - Sign in page
    ├── register.html       # Authentication - Registration page
    ├── profile.html        # User profile & account statistics
    ├── add_expense.html    # Form to record a new transaction
    ├── edit_expense.html   # Form to update an existing expense entry
    ├── terms.html          # Terms and Conditions static page
    └── privacy.html        # Privacy Policy static page
```

---

## 3. Environment & Setup

### Virtual Environment
A Python virtual environment is located at `.venv`:
- Activate in shell: `source .venv/bin/activate`
- Run via direct virtualenv binary: `.venv/bin/python`

### Dependencies
Installed via `pip`:
- `flask`
- `werkzeug`
- `pytest`
- `pytest-flask`

---

## 4. Verification & Testing Instructions

Whenever modifying code or templates, you **MUST** run the test suite to confirm that no regressions were introduced.

### Running Tests
Execute pytest using the virtualenv runner:
```bash
.venv/bin/python -m pytest
```

### Key Test Coverage
- Landing page rendering & header link verification (`test_landing_page`)
- User registration & authentication (`test_registration`, `test_login_logout`)
- Expense CRUD workflows (`test_add_expense`, `test_edit_expense`, `test_delete_expense`)
- Static page accessibility (`test_terms_page`, `test_privacy_page`)

---

## 5. Coding & Architectural Guidelines

1. **Vanilla JavaScript Only**: Do NOT introduce heavy JS frameworks (React, Vue, Alpine, etc.). Keep interactive features lightweight using plain DOM manipulation.
2. **HTML Autoescaping in Tests**: Jinja automatically escapes HTML characters (e.g. `&` becomes `&amp;`). Take this into account when writing or updating assertions in `test_app.py`.
3. **Design System & CSS Variables**: Reuse variables defined in `static/css/style.css` (`--ink`, `--accent`, `--paper-card`, `--font-display`, etc.) for UI consistency across static pages and components.
4. **Preserve Database Cleanliness**: Integration tests use temporary SQLite databases via fixtures (`tempfile.mkstemp()`). Avoid hardcoding paths outside `database/db.py`.

---

## 6. Code Style & Formatting Standards

### Python (Backend & Tests)
- **PEP 8 Compliance**: Use 4-space indentation, `snake_case` for function and variable names, and `UPPER_CASE` for global constants.
- **SQL Safety**: Always use parameterized queries (e.g., `db.execute("SELECT * FROM users WHERE email = ?", (email,))`) to prevent SQL injection vulnerabilities.
- **Docstrings & Comments**: Include concise docstrings for all route handlers, helper functions, and test cases.
- **Test Assertions**: Assert HTML response data using byte strings (e.g., `assert b"Spendly" in response.data`).

### HTML & Jinja2 Templates
- **Semantic Structure**: Use standard HTML5 structural tags (`<main>`, `<nav>`, `<section>`, `<footer>`).
- **Template Inheritance**: Extend `base.html` for all user-facing views and place custom page styles/scripts inside `{% block head %}` and `{% block scripts %}`.
- **Indentation**: Use 4-space indentation for HTML structure and Jinja control flow tags.

### CSS & Styling
- **Naming Conventions**: Use `kebab-case` for CSS class names (e.g., `.btn-hero-primary`, `.legal-container`).
- **Design Tokens**: Standardize colors, typography, and spacing using CSS custom properties (`var(--ink)`, `var(--accent)`, `var(--font-display)`).
- **Responsive Media Queries**: Group responsive media queries (`@media (max-width: ...)` ) at the bottom of the relevant stylesheet module (e.g., `static/css/landing.css`).

### JavaScript
- **ES6+ Standards**: Write modern vanilla JS using `const`/`let`, arrow functions, and native DOM APIs (`querySelector`, `addEventListener`).
- **Lifecycle Guards**: Wrap page-specific scripts inside `DOMContentLoaded` listeners and verify element existence prior to binding events.

---

## 7. Useful Development Commands

### Environment & Server Management
- **Activate Virtual Environment**:
  ```bash
  source .venv/bin/activate
  ```
- **Run Flask Application**:
  ```bash
  .venv/bin/python app.py
  ```
- **Install Dependencies**:
  ```bash
  .venv/bin/pip install -r requirements.txt
  ```

### Testing Commands
- **Run All Tests**:
  ```bash
  .venv/bin/python -m pytest
  ```
- **Run Specific Test Function**:
  ```bash
  .venv/bin/python -m pytest test_app.py -k test_landing_page
  ```
- **Run Tests with Verbose Output**:
  ```bash
  .venv/bin/python -m pytest -v
  ```

---

## 8. Critical Rules & Constraints

> [!IMPORTANT]
> All developers and AI agents MUST strictly comply with these rules at all times.

1. **Verify Before Declaring Completion**: NEVER claim a task or bug fix is complete without running `.venv/bin/python -m pytest` and demonstrating a 100% clean test run.
2. **No Heavy JS Frameworks**: Use vanilla JavaScript only. Do NOT introduce React, Vue, Alpine, or jQuery dependencies.
3. **Parameterized SQL Queries**: NEVER construct SQL strings using Python string formatting or concatenation (`f"SELECT ..."`). Always use `?` parameter placeholders.
4. **Preserve Design Token System**: Always reuse defined CSS custom properties (`var(--ink)`, `var(--accent)`, `var(--paper-card)`, `var(--font-display)`) to ensure UI consistency.
5. **No Blind Exception Swallowing**: Do not wrap broken code in silent `try/except` blocks or mask failing test assertions. Diagnose and resolve underlying root causes.
6. **Isolated Test Execution**: Integration tests MUST continue using temporary SQLite database files via `tempfile.mkstemp()` fixtures to preserve local database state.


