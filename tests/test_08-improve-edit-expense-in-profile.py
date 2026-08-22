import os
import tempfile
import pytest
from app import app, CATEGORIES
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
# 1. Profile Actions Column & Action Links Tests                     #
# ------------------------------------------------------------------ #


def test_profile_renders_actions_column_and_buttons(client):
    """Test that /profile displays an Actions column with Edit and Delete links."""
    login_user(client)
    response = client.get("/profile")
    assert response.status_code == 200
    assert b"Actions" in response.data

    # Check for Edit and Delete buttons targeting return_to=profile
    assert (
        b"edit?return_to=profile" in response.data
        or b"return_to=profile" in response.data
    )
    assert b"Edit" in response.data
    assert b"Delete" in response.data
    assert b"btn-action" in response.data
    assert b"btn-delete" in response.data


# ------------------------------------------------------------------ #
# 2. Edit Expense Page & Form Tests                                  #
# ------------------------------------------------------------------ #


def test_edit_expense_page_from_profile_has_all_categories_and_cancel_to_profile(
    client,
):
    """Test that editing from profile includes all 7 categories and cancel returns to profile."""
    login_user(client)

    # Get an expense ID for user 1
    with app.app_context():
        db = get_db()
        expense = db.execute(
            "SELECT id FROM expenses WHERE user_id = 1 LIMIT 1"
        ).fetchone()
        expense_id = expense["id"]

    response = client.get(f"/expenses/{expense_id}/edit?return_to=profile")
    assert response.status_code == 200

    # Verify all standard categories are available in the dropdown
    for cat in CATEGORIES:
        assert cat.encode() in response.data

    # Verify Cancel button links to /profile
    assert b'href="/profile"' in response.data


def test_edit_expense_page_from_dashboard_cancel_points_to_dashboard(client):
    """Test that editing from dashboard has cancel link pointing to /dashboard."""
    login_user(client)

    with app.app_context():
        db = get_db()
        expense = db.execute(
            "SELECT id FROM expenses WHERE user_id = 1 LIMIT 1"
        ).fetchone()
        expense_id = expense["id"]

    response = client.get(f"/expenses/{expense_id}/edit?return_to=dashboard")
    assert response.status_code == 200
    assert b'href="/dashboard"' in response.data


# ------------------------------------------------------------------ #
# 3. Edit Submission & Contextual Redirects                          #
# ------------------------------------------------------------------ #


def test_edit_expense_post_from_profile_redirects_to_profile(client):
    """Test that submitting an edit initiated from profile redirects back to /profile."""
    login_user(client)

    with app.app_context():
        db = get_db()
        expense = db.execute(
            "SELECT id FROM expenses WHERE user_id = 1 LIMIT 1"
        ).fetchone()
        expense_id = expense["id"]

    response = client.post(
        f"/expenses/{expense_id}/edit?return_to=profile",
        data={
            "category": "Shopping",
            "amount": "999.50",
            "date": "2026-03-25",
            "description": "Updated from Profile Test",
            "return_to": "profile",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert "/profile" in response.headers["Location"]

    # Verify update in database
    with app.app_context():
        db = get_db()
        updated = db.execute(
            "SELECT * FROM expenses WHERE id = ?", (expense_id,)
        ).fetchone()
        assert updated["category"] == "Shopping"
        assert updated["amount"] == 999.50
        assert updated["description"] == "Updated from Profile Test"


def test_edit_expense_post_from_dashboard_redirects_to_dashboard(client):
    """Test that submitting an edit initiated from dashboard redirects back to /dashboard."""
    login_user(client)

    with app.app_context():
        db = get_db()
        expense = db.execute(
            "SELECT id FROM expenses WHERE user_id = 1 LIMIT 1"
        ).fetchone()
        expense_id = expense["id"]

    response = client.post(
        f"/expenses/{expense_id}/edit",
        data={
            "category": "Bills",
            "amount": "250.00",
            "date": "2026-03-22",
            "description": "Updated from Dashboard",
            "return_to": "dashboard",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert "/dashboard" in response.headers["Location"]


# ------------------------------------------------------------------ #
# 4. Validation Errors in Edit Form                                  #
# ------------------------------------------------------------------ #


def test_edit_expense_validation_errors(client):
    """Test validation errors for invalid category, negative amount, and invalid date."""
    login_user(client)

    with app.app_context():
        db = get_db()
        expense = db.execute(
            "SELECT id FROM expenses WHERE user_id = 1 LIMIT 1"
        ).fetchone()
        expense_id = expense["id"]

    # Invalid amount
    res_amt = client.post(
        f"/expenses/{expense_id}/edit?return_to=profile",
        data={
            "category": "Food",
            "amount": "-50.00",
            "date": "2026-03-25",
            "description": "Invalid Negative",
            "return_to": "profile",
        },
    )
    assert res_amt.status_code == 200
    assert b"Amount must be a positive number" in res_amt.data

    # Invalid category
    res_cat = client.post(
        f"/expenses/{expense_id}/edit?return_to=profile",
        data={
            "category": "InvalidCategoryName",
            "amount": "50.00",
            "date": "2026-03-25",
            "description": "Invalid Category",
            "return_to": "profile",
        },
    )
    assert res_cat.status_code == 200
    assert b"Please select a valid category" in res_cat.data

    # Invalid date
    res_date = client.post(
        f"/expenses/{expense_id}/edit?return_to=profile",
        data={
            "category": "Food",
            "amount": "50.00",
            "date": "not-a-date",
            "description": "Invalid Date",
            "return_to": "profile",
        },
    )
    assert res_date.status_code == 200
    assert b"Please enter a valid date in YYYY-MM-DD format" in res_date.data


# ------------------------------------------------------------------ #
# 5. Delete Expense & Profile Contextual Redirect                    #
# ------------------------------------------------------------------ #


def test_delete_expense_from_profile_redirects_to_profile(client):
    """Test that deleting an expense with return_to=profile redirects back to /profile."""
    login_user(client)

    with app.app_context():
        db = get_db()
        expense = db.execute(
            "SELECT id FROM expenses WHERE user_id = 1 LIMIT 1"
        ).fetchone()
        expense_id = expense["id"]

    response = client.get(
        f"/expenses/{expense_id}/delete?return_to=profile",
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert "/profile" in response.headers["Location"]

    # Verify expense is deleted
    with app.app_context():
        db = get_db()
        deleted = db.execute(
            "SELECT * FROM expenses WHERE id = ?", (expense_id,)
        ).fetchone()
        assert deleted is None


def test_delete_expense_from_dashboard_redirects_to_dashboard(client):
    """Test that deleting an expense from dashboard redirects to /dashboard."""
    login_user(client)

    with app.app_context():
        db = get_db()
        expense = db.execute(
            "SELECT id FROM expenses WHERE user_id = 1 LIMIT 1"
        ).fetchone()
        expense_id = expense["id"]

    response = client.get(
        f"/expenses/{expense_id}/delete?return_to=dashboard", follow_redirects=False
    )
    assert response.status_code == 302
    assert "/dashboard" in response.headers["Location"]


# ------------------------------------------------------------------ #
# 6. Authorization & Security Checks                                 #
# ------------------------------------------------------------------ #


def test_edit_and_delete_unauthorized_user_blocked(client):
    """Test that a user cannot edit or delete another user's expense."""
    # Create user 2 and log in as user 2
    with app.app_context():
        db = get_db()
        # Ensure user 1 has an expense
        user1_exp = db.execute(
            "SELECT id FROM expenses WHERE user_id = 1 LIMIT 1"
        ).fetchone()
        user1_exp_id = user1_exp["id"]

        # Insert user 2
        from werkzeug.security import generate_password_hash

        db.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (
                "User Two",
                "usertwo@spendly.com",
                generate_password_hash("password123"),
            ),
        )
        db.commit()

    login_user(client, email="usertwo@spendly.com", password="password123")

    # Try to edit user 1's expense
    res_edit_get = client.get(f"/expenses/{user1_exp_id}/edit")
    assert res_edit_get.status_code == 404

    res_edit_post = client.post(
        f"/expenses/{user1_exp_id}/edit",
        data={
            "category": "Food",
            "amount": "100.00",
            "date": "2026-03-20",
        },
    )
    assert res_edit_post.status_code == 404

    # Try to delete user 1's expense
    res_delete = client.get(f"/expenses/{user1_exp_id}/delete")
    assert res_delete.status_code == 404
