from datetime import datetime, timedelta
import functools
import os
import re

from flask import Flask, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from database.db import get_db, init_db, seed_db

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "spendly_secure_developer_secret_key")
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax"
)

# Helper functions
def extract_initials(name: str) -> str:
    """Extract 1 or 2 character uppercase initials from a user's name."""
    parts = (name or "").strip().split()
    if not parts:
        return "?"
    if len(parts) > 1:
        return (parts[0][0] + parts[-1][0]).upper()
    return parts[0][0].upper()

def format_date_display(date_str: str, fmt: str = "%d %b %Y") -> str:
    """Safely convert ISO date string to human-readable format."""
    if not date_str:
        return ""
    try:
        return datetime.strptime(str(date_str)[:10], "%Y-%m-%d").strftime(fmt)
    except (ValueError, TypeError):
        return str(date_str)

def validate_iso_date(date_str: str) -> str:
    """Validate and return normalized YYYY-MM-DD date string, or empty string if invalid."""
    if not date_str:
        return ""
    try:
        return datetime.strptime(str(date_str).strip()[:10], "%Y-%m-%d").strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return ""

# Ensure the database is initialized and seeded on startup
with app.app_context():
    init_db()
    seed_db()

@app.teardown_appcontext
def close_connection(exception):
    """Closes the database connection at the end of the request context."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# ------------------------------------------------------------------ #
# Authentication Decorator                                           #
# ------------------------------------------------------------------ #

def login_required(view):
    """Decorator to protect routes that require authentication."""
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view(**kwargs)
    return wrapped_view

# ------------------------------------------------------------------ #
# Routes                                                             #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    # If already logged in, send directly to dashboard
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return render_template("landing.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")



@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name or not email or not password or not confirm_password:
            return render_template("register.html", error="All fields are required.", name=name, email=email)
        
        if not name[0].isupper():
            return render_template("register.html", error="Name must start with a capital letter.", name=name, email=email)

        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return render_template("register.html", error="Please enter a valid email address.", name=name, email=email)

        if len(password) < 8:
            return render_template("register.html", error="Password must be at least 8 characters long.", name=name, email=email)

        if password != confirm_password:
            return render_template("register.html", error="Passwords do not match.", name=name, email=email)

        db = get_db()
        # Check if the email is already registered
        existing_user = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing_user:
            return render_template("register.html", error="An account with this email already exists.", name=name, email=email)

        hashed_password = generate_password_hash(password)
        try:
            cursor = db.cursor()
            cursor.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                (name, email, hashed_password)
            )
            db.commit()

            # Automatically log in the user after registering
            user_id = cursor.lastrowid
            session["user_id"] = user_id
            session["user_name"] = name
            session["user_email"] = email

            return redirect(url_for("dashboard"))
        except Exception:
            return render_template("register.html", error="An error occurred. Please try again.", name=name, email=email)

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("profile"))

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
            return redirect(url_for("profile"))

        return render_template("login.html", error="Invalid email or password.", email=email)

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))


@app.route("/profile")
@login_required
def profile():
    """Renders the redesigned profile page with dynamic database user details, summary stats, recent transactions, and category breakdown."""
    user_id = session["user_id"]
    db = get_db()

    # Extract date filter parameters and presets
    preset = request.args.get("preset", "").strip()
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()

    today = datetime.today().date()

    if preset == "this_month":
        start_date = today.replace(day=1).strftime("%Y-%m-%d")
        end_date = today.strftime("%Y-%m-%d")
    elif preset == "last_3_months":
        start_date = (today - timedelta(days=90)).strftime("%Y-%m-%d")
        end_date = today.strftime("%Y-%m-%d")
    elif preset == "last_6_months":
        start_date = (today - timedelta(days=180)).strftime("%Y-%m-%d")
        end_date = today.strftime("%Y-%m-%d")
    elif preset == "all":
        start_date, end_date = "", ""
    else:
        preset = "all" if not start_date and not end_date else "custom"

    date_filter_sql = ""
    date_filter_params = []
    
    # Defensive ISO date validation
    valid_start = validate_iso_date(start_date)
    valid_end = validate_iso_date(end_date)

    if valid_start:
        date_filter_sql += " AND date >= ?"
        date_filter_params.append(valid_start)
    if valid_end:
        date_filter_sql += " AND date <= ?"
        date_filter_params.append(valid_end)

    # 1. User Info
    user_row = db.execute("SELECT name, email, created_at FROM users WHERE id = ?", (user_id,)).fetchone()
    name = (user_row["name"] if user_row else session.get("user_name", "")) or ""
    email = (user_row["email"] if user_row else session.get("user_email", "")) or ""
    created_at = user_row["created_at"] if user_row else None

    user = {
        "name": name,
        "email": email,
        "initials": extract_initials(name),
        "member_since": format_date_display(created_at, "%B %Y") or "March 2026"
    }

    # 2. Summary Stats & Category Breakdown
    summary_query = "SELECT COALESCE(SUM(amount), 0.0) as total_spent, COUNT(*) as tx_count FROM expenses WHERE user_id = ?" + date_filter_sql
    summary_row = db.execute(summary_query, [user_id] + date_filter_params).fetchone()

    total_spent = float(summary_row["total_spent"]) if summary_row and summary_row["total_spent"] is not None else 0.0
    transaction_count = summary_row["tx_count"] if summary_row and summary_row["tx_count"] is not None else 0

    # Badge CSS class mapping helper
    badge_class_map = {
        "Food": "badge-food",
        "Transport": "badge-transport",
        "Bills": "badge-bills",
        "Health": "badge-health",
        "Entertainment": "badge-entertainment",
        "Shopping": "badge-shopping",
        "Other": "badge-other"
    }

    # 3. Category Breakdown (also provides Top Category dynamically without redundant query)
    breakdown_query = "SELECT category, SUM(amount) as amount FROM expenses WHERE user_id = ?" + date_filter_sql + " GROUP BY category ORDER BY amount DESC, category ASC"
    breakdown_rows = db.execute(breakdown_query, [user_id] + date_filter_params).fetchall()

    category_breakdown = [
        {
            "category": row["category"],
            "amount": float(row["amount"]),
            "percentage": int(round((row["amount"] / total_spent * 100))) if total_spent > 0 else 0,
            "badge_class": badge_class_map.get(row["category"], "badge-other")
        }
        for row in breakdown_rows
    ]

    top_category = category_breakdown[0]["category"] if category_breakdown else "N/A"

    stats = {
        "total_spent": total_spent,
        "transaction_count": transaction_count,
        "top_category": top_category
    }

    # 4. Recent Transactions
    recent_query = "SELECT id, date, description, category, amount FROM expenses WHERE user_id = ?" + date_filter_sql + " ORDER BY date DESC, id DESC LIMIT 10"
    recent_rows = db.execute(recent_query, [user_id] + date_filter_params).fetchall()

    recent_transactions = [
        {
            "id": row["id"],
            "date": format_date_display(row["date"], "%d %b %Y"),
            "raw_date": row["date"],
            "description": row["description"] or "—",
            "category": row["category"],
            "badge_class": badge_class_map.get(row["category"], "badge-other"),
            "amount": row["amount"]
        }
        for row in recent_rows
    ]

    filters = {
        "start_date": start_date,
        "end_date": end_date,
        "preset": preset
    }

    return render_template(
        "profile.html",
        user=user,
        stats=stats,
        recent_transactions=recent_transactions,
        category_breakdown=category_breakdown,
        filters=filters
    )


@app.route("/dashboard")
@login_required
def dashboard():
    user_id = session["user_id"]
    db = get_db()

    # Available categories (fixed list per spec)
    categories = ['Food', 'Transport', 'Bills', 'Health', 'Entertainment', 'Shopping', 'Other']

    # Retrieve filter arguments
    query = request.args.get("query", "").strip()
    category = request.args.get("category", "").strip()
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()
    order_by = request.args.get("order_by", "newest").strip()

    # Build filtered query dynamically
    sql_query = "SELECT * FROM expenses WHERE user_id = ?"
    params = [user_id]

    if query:
        sql_query += " AND (description LIKE ? OR category LIKE ?)"
        like_pattern = f"%{query}%"
        params.extend([like_pattern, like_pattern])

    if category:
        sql_query += " AND category = ?"
        params.append(category)

    if start_date:
        sql_query += " AND date >= ?"
        params.append(start_date)

    if end_date:
        sql_query += " AND date <= ?"
        params.append(end_date)

    # Apply sorting
    if order_by == "oldest":
        sql_query += " ORDER BY date ASC, id ASC"
    elif order_by == "amount_desc":
        sql_query += " ORDER BY amount DESC"
    elif order_by == "amount_asc":
        sql_query += " ORDER BY amount ASC"
    else: # default: newest
        sql_query += " ORDER BY date DESC, id DESC"

    expenses = db.execute(sql_query, params).fetchall()

    # Calculate metrics for the visible (filtered) expenses
    total_spent = sum(expense["amount"] for expense in expenses)

    # Calculate category breakdown based on all user expenses
    breakdown_rows = db.execute(
        "SELECT category, SUM(amount) as amount FROM expenses WHERE user_id = ? GROUP BY category ORDER BY amount DESC",
        (user_id,)
    ).fetchall()

    total_spent_all = sum(row["amount"] for row in breakdown_rows)
    category_breakdown = []
    for row in breakdown_rows:
        percentage = (row["amount"] / total_spent_all * 100) if total_spent_all > 0 else 0
        category_breakdown.append({
            "category": row["category"],
            "amount": row["amount"],
            "percentage": percentage
        })

    filters = {
        "query": query,
        "category": category,
        "start_date": start_date,
        "end_date": end_date,
        "order_by": order_by
    }

    return render_template(
        "dashboard.html",
        expenses=expenses,
        total_spent=total_spent,
        category_breakdown=category_breakdown,
        categories=categories,
        filters=filters
    )


@app.route("/expenses/add", methods=["GET", "POST"])
@login_required
def add_expense():
    if request.method == "POST":
        category = request.form.get("category", "").strip()
        amount_str = request.form.get("amount", "").strip()
        date = request.form.get("date", "").strip()
        description = request.form.get("description", "").strip()

        if not category or not amount_str or not date:
            return render_template("add_expense.html", error="Category, Amount, and Date are required.")

        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError()
        except ValueError:
            return render_template("add_expense.html", error="Amount must be a positive number.")

        db = get_db()
        db.execute(
            "INSERT INTO expenses (user_id, category, amount, date, description) VALUES (?, ?, ?, ?, ?)",
            (session["user_id"], category, amount, date, description)
        )
        db.commit()
        return redirect(url_for("dashboard"))

    return render_template("add_expense.html")


@app.route("/expenses/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit_expense(id):
    db = get_db()
    user_id = session["user_id"]

    # Retrieve the expense and verify ownership
    expense = db.execute(
        "SELECT * FROM expenses WHERE id = ? AND user_id = ?",
        (id, user_id)
    ).fetchone()

    if not expense:
        return "Expense not found or unauthorized.", 404

    if request.method == "POST":
        category = request.form.get("category", "").strip()
        amount_str = request.form.get("amount", "").strip()
        date = request.form.get("date", "").strip()
        description = request.form.get("description", "").strip()

        if not category or not amount_str or not date:
            return render_template("edit_expense.html", expense=expense, error="Category, Amount, and Date are required.")

        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError()
        except ValueError:
            return render_template("edit_expense.html", expense=expense, error="Amount must be a positive number.")

        db.execute(
            "UPDATE expenses SET category = ?, amount = ?, date = ?, description = ? WHERE id = ? AND user_id = ?",
            (category, amount, date, description, id, user_id)
        )
        db.commit()
        return redirect(url_for("dashboard"))

    return render_template("edit_expense.html", expense=expense)


@app.route("/expenses/<int:id>/delete")
@login_required
def delete_expense(id):
    db = get_db()
    user_id = session["user_id"]

    # Verify ownership and delete
    cursor = db.cursor()
    cursor.execute(
        "DELETE FROM expenses WHERE id = ? AND user_id = ?",
        (id, user_id)
    )
    db.commit()

    if cursor.rowcount == 0:
        return "Expense not found or unauthorized.", 404

    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    import socket

    port = int(os.environ.get("PORT", 5001))
    
    # Automatically find an available port starting from 5001
    for p in range(port, port + 10):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', p)) != 0:
                port = p
                break

    app.run(debug=True, port=port)

