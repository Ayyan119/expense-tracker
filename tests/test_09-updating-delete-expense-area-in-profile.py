import os
import tempfile
import pytest
from app import app
import database.db
from database.db import init_db, seed_db, get_db


@pytest.fixture
def client():
    """Fixture to set up an isolated temporary SQLite database for each test."""
    db_fd, temp_db_path = tempfile.mkstemp()
    original_db_path = database.db.DB_PATH
    database.db.DB_PATH = temp_db_path

    app.config["TESTING"] = True

    with app.app_context():
        init_db()
        seed_db()

    with app.test_client() as client:
        yield client

    os.close(db_fd)
    try:
        os.unlink(temp_db_path)
    except OSError:
        pass
    database.db.DB_PATH = original_db_path


def login_user(client, email="demo@spendly.com", password="demo123"):
    """Helper to log in the default seed user."""
    return client.post(
        "/login",
        data={"email": email, "password": password},
        follow_redirects=True,
    )


# ------------------------------------------------------------------ #
# 1. Profile Delete Action & Flash Message                           #
# ------------------------------------------------------------------ #


def test_delete_expense_from_profile_redirects_and_flashes(client):
    """Test deleting an expense with return_to=profile redirects to /profile and shows flash message."""
    login_user(client)

    with app.app_context():
        db = get_db()
        expense = db.execute(
            "SELECT id, description FROM expenses WHERE user_id = 1 LIMIT 1"
        ).fetchone()
        expense_id = expense["id"]
        description = expense["description"]

    # Delete with return_to=profile
    response = client.get(
        f"/expenses/{expense_id}/delete?return_to=profile",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Expense deleted successfully." in response.data
    assert description.encode() not in response.data

    # Verify deleted from DB
    with app.app_context():
        db = get_db()
        check = db.execute(
            "SELECT * FROM expenses WHERE id = ?", (expense_id,)
        ).fetchone()
        assert check is None


# ------------------------------------------------------------------ #
# 2. Filter State Preservation on Deletion                           #
# ------------------------------------------------------------------ #


def test_delete_expense_from_profile_preserves_preset_filter(client):
    """Test that deleting an expense preserves active preset filter in the redirect."""
    login_user(client)

    with app.app_context():
        db = get_db()
        expense = db.execute(
            "SELECT id FROM expenses WHERE user_id = 1 LIMIT 1"
        ).fetchone()
        expense_id = expense["id"]

    response = client.get(
        f"/expenses/{expense_id}/delete?return_to=profile&preset=last_3_months",
        follow_redirects=False,
    )

    assert response.status_code == 302
    location = response.headers["Location"]
    assert "/profile" in location
    assert "preset=last_3_months" in location


def test_delete_expense_from_profile_preserves_custom_date_filter(client):
    """Test that deleting an expense preserves custom start_date and end_date filters."""
    login_user(client)

    with app.app_context():
        db = get_db()
        expense = db.execute(
            "SELECT id FROM expenses WHERE user_id = 1 LIMIT 1"
        ).fetchone()
        expense_id = expense["id"]

    response = client.get(
        f"/expenses/{expense_id}/delete?return_to=profile&start_date=2026-03-01&end_date=2026-03-15",
        follow_redirects=False,
    )

    assert response.status_code == 302
    location = response.headers["Location"]
    assert "/profile" in location
    assert "start_date=2026-03-01" in location
    assert "end_date=2026-03-15" in location


def test_delete_expense_from_dashboard_preserves_dashboard_filters(client):
    """Test that deleting from dashboard preserves dashboard query and category filters."""
    login_user(client)

    with app.app_context():
        db = get_db()
        expense = db.execute(
            "SELECT id FROM expenses WHERE user_id = 1 LIMIT 1"
        ).fetchone()
        expense_id = expense["id"]

    response = client.get(
        f"/expenses/{expense_id}/delete?return_to=dashboard&category=Bills&query=rent",
        follow_redirects=False,
    )

    assert response.status_code == 302
    location = response.headers["Location"]
    assert "/dashboard" in location
    assert "category=Bills" in location
    assert "query=rent" in location


# ------------------------------------------------------------------ #
# 3. Profile Metric Recalculation after Deletion                     #
# ------------------------------------------------------------------ #


def test_delete_expense_updates_profile_metrics(client):
    """Test that deleting an expense immediately updates profile totals and counts."""
    login_user(client)

    # Initial profile view
    res_before = client.get("/profile")
    assert res_before.status_code == 200
    assert b"16,850.00" in res_before.data  # Total spent of 8 seed expenses

    # Delete 4500.00 Bills expense (id=1)
    client.get("/expenses/1/delete?return_to=profile", follow_redirects=True)

    # Check updated profile
    res_after = client.get("/profile")
    assert res_after.status_code == 200
    # 16,850 - 4,500 = 12,350.00
    assert b"12,350.00" in res_after.data
    # 7 transactions remain
    assert b"7" in res_after.data


# ------------------------------------------------------------------ #
# 4. POST Method Support                                             #
# ------------------------------------------------------------------ #


def test_delete_expense_via_post_method(client):
    """Test that POST request to /expenses/<id>/delete successfully deletes the expense."""
    login_user(client)

    with app.app_context():
        db = get_db()
        expense = db.execute(
            "SELECT id FROM expenses WHERE user_id = 1 LIMIT 1"
        ).fetchone()
        expense_id = expense["id"]

    response = client.post(
        f"/expenses/{expense_id}/delete",
        data={"return_to": "profile", "preset": "this_month"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Expense deleted successfully." in response.data

    with app.app_context():
        db = get_db()
        check = db.execute(
            "SELECT * FROM expenses WHERE id = ?", (expense_id,)
        ).fetchone()
        assert check is None


# ------------------------------------------------------------------ #
# 5. Security & Ownership Verification                               #
# ------------------------------------------------------------------ #


def test_delete_expense_unauthorized_user_blocked(client):
    """Test that a user cannot delete another user's expense."""
    with app.app_context():
        db = get_db()
        from werkzeug.security import generate_password_hash

        db.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("User Two", "usertwo@spendly.com", generate_password_hash("password123")),
        )
        db.commit()

    login_user(client, email="usertwo@spendly.com", password="password123")

    # Attempt to delete user 1's expense (id=1)
    response = client.get("/expenses/1/delete?return_to=profile")
    assert response.status_code == 404

    # Ensure expense still exists
    with app.app_context():
        db = get_db()
        check = db.execute("SELECT * FROM expenses WHERE id = 1").fetchone()
        assert check is not None


def test_delete_expense_unauthenticated_redirects(client):
    """Test that unauthenticated access to delete expense redirects to /login."""
    response = client.get("/expenses/1/delete", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]

    response_post = client.post("/expenses/1/delete", follow_redirects=False)
    assert response_post.status_code == 302
    assert "/login" in response_post.headers["Location"]


# ------------------------------------------------------------------ #
# 6. Profile Template Render with Filter Query Params                #
# ------------------------------------------------------------------ #


def test_profile_renders_delete_links_with_active_filters(client):
    """Test that profile template generates delete links including active filter params."""
    login_user(client)

    # Insert an expense for today so it appears under this_month filter
    from datetime import datetime

    today = datetime.today().strftime("%Y-%m-%d")
    with app.app_context():
        db = get_db()
        db.execute(
            "INSERT INTO expenses (user_id, category, amount, date, description) VALUES (?, ?, ?, ?, ?)",
            (1, "Food", 150.0, today, "Today Lunch"),
        )
        db.commit()

    response = client.get("/profile?preset=this_month")
    assert response.status_code == 200
    assert b"preset=this_month" in response.data
    assert b"btn-delete" in response.data
    assert b"confirm(" in response.data
    assert b"Today Lunch" in response.data
