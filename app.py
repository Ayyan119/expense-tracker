from flask import Flask, render_template, request, redirect, url_for, session, g
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import get_db, init_db, seed_db
import functools
import os

app = Flask(__name__)
app.secret_key = "spendly_secure_developer_secret_key"

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

        if not name or not email or not password:
            return render_template("register.html", error="All fields are required.")
        
        if len(password) < 8:
            return render_template("register.html", error="Password must be at least 8 characters long.")

        db = get_db()
        # Check if the email is already registered
        existing_user = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing_user:
            return render_template("register.html", error="An account with this email already exists.")

        hashed_password = generate_password_hash(password)
        try:
            cursor = db.cursor()
            cursor.execute(
                "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
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
            return render_template("register.html", error="An error occurred. Please try again.")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not email or not password:
            return render_template("login.html", error="Please provide email and password.")

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["user_email"] = user["email"]
            return redirect(url_for("dashboard"))

        return render_template("login.html", error="Invalid email or password.")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))


@app.route("/profile")
@login_required
def profile():
    db = get_db()
    user_id = session["user_id"]

    # Fetch fresh user details
    user = db.execute("SELECT name, email FROM users WHERE id = ?", (user_id,)).fetchone()

    # Calculate summary stats
    stats = db.execute(
        "SELECT COUNT(id) as count, SUM(amount) as total FROM expenses WHERE user_id = ?",
        (user_id,)
    ).fetchone()

    return render_template("profile.html", user=user, stats=stats)


@app.route("/dashboard")
@login_required
def dashboard():
    user_id = session["user_id"]
    db = get_db()

    # Available categories
    categories = ['Bills', 'Food', 'Health', 'Transport', 'Other']

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
    app.run(debug=True, port=5001)
