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


# ------------------------------------------------------------------ #
# 1. Authentication Guard Tests                                     #
# ------------------------------------------------------------------ #


def test_add_expense_unauthenticated_get_redirects_to_login(client):
    """Test that accessing GET /expenses/add while unauthenticated redirects to /login."""
    response = client.get("/expenses/add", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_add_expense_unauthenticated_post_redirects_to_login(client):
    """Test that submitting POST /expenses/add while unauthenticated redirects to /login."""
    response = client.post(
        "/expenses/add",
        data={
            "category": "Food",
            "amount": "150.00",
            "date": "2026-03-20",
            "description": "Unauthenticated attempt",
        },
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


# ------------------------------------------------------------------ #
# 2. Form Rendering & Category Options Tests                         #
# ------------------------------------------------------------------ #


def test_add_expense_form_renders_required_fields_and_all_categories(client):
    """Test that GET /expenses/add renders the Add Expense form with all 7 standard categories and inputs."""
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})

    response = client.get("/expenses/add")
    assert response.status_code == 200
    assert b"Add Expense" in response.data
    assert b"Log a new transaction to your account" in response.data

    # Form field inputs verification
    assert b'name="category"' in response.data
    assert b'name="amount"' in response.data
    assert b'name="date"' in response.data
    assert b'name="description"' in response.data

    # All 7 standard categories verification
    standard_categories = [
        "Bills",
        "Entertainment",
        "Food",
        "Health",
        "Other",
        "Shopping",
        "Transport",
    ]
    for cat in standard_categories:
        assert f'<option value="{cat}"'.encode() in response.data


def test_add_expense_cancel_link_present(client):
    """Test that the Add Expense form provides a cancel navigation link back to the dashboard."""
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})

    response = client.get("/expenses/add")
    assert response.status_code == 200
    assert b'href="/dashboard"' in response.data or b"Cancel" in response.data


# ------------------------------------------------------------------ #
# 3. Happy Path: Expense Creation Tests                              #
# ------------------------------------------------------------------ #


def test_add_expense_valid_submission_redirects_and_persists(client):
    """Test submitting a valid expense persists to the database and redirects to /dashboard."""
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})

    response = client.post(
        "/expenses/add",
        data={
            "category": "Shopping",
            "amount": "1299.99",
            "date": "2026-03-25",
            "description": "Wireless Noise-Cancelling Headphones",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Wireless Noise-Cancelling Headphones" in response.data
    assert b"1,299.99" in response.data

    # Direct database verification
    with app.app_context():
        db = get_db()
        row = db.execute(
            "SELECT * FROM expenses WHERE description = ?",
            ("Wireless Noise-Cancelling Headphones",),
        ).fetchone()
        assert row is not None
        assert row["category"] == "Shopping"
        assert row["amount"] == 1299.99
        assert row["date"] == "2026-03-25"


def test_add_expense_all_seven_categories_supported(client):
    """Test that all 7 standard categories (Food, Transport, Bills, Health, Entertainment, Shopping, Other) can be logged."""
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})

    categories = [
        "Food",
        "Transport",
        "Bills",
        "Health",
        "Entertainment",
        "Shopping",
        "Other",
    ]
    for idx, category in enumerate(categories, start=1):
        desc = f"Unique item for {category} test {idx}"
        amount = f"{25.50 * idx:.2f}"

        response = client.post(
            "/expenses/add",
            data={
                "category": category,
                "amount": amount,
                "date": "2026-03-26",
                "description": desc,
            },
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert desc.encode() in response.data

        # Verify DB entry for category
        with app.app_context():
            db = get_db()
            row = db.execute(
                "SELECT * FROM expenses WHERE description = ?", (desc,)
            ).fetchone()
            assert row is not None
            assert row["category"] == category


def test_add_expense_optional_description_omitted(client):
    """Test adding an expense with an empty description succeeds since description is optional."""
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})

    response = client.post(
        "/expenses/add",
        data={
            "category": "Transport",
            "amount": "42.00",
            "date": "2026-03-27",
            "description": "",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"42.00" in response.data

    with app.app_context():
        db = get_db()
        row = db.execute(
            "SELECT * FROM expenses WHERE category = 'Transport' AND amount = 42.00 AND date = '2026-03-27'"
        ).fetchone()
        assert row is not None
        assert row["description"] == ""


def test_add_expense_whitespace_trimming(client):
    """Test that leading/trailing whitespaces in category, amount, date, and description are trimmed."""
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})

    response = client.post(
        "/expenses/add",
        data={
            "category": "  Food  ",
            "amount": "  88.50  ",
            "date": "  2026-03-28  ",
            "description": "  Trimmed Lunch  ",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Trimmed Lunch" in response.data

    with app.app_context():
        db = get_db()
        row = db.execute(
            "SELECT * FROM expenses WHERE description = 'Trimmed Lunch'"
        ).fetchone()
        assert row is not None
        assert row["category"] == "Food"
        assert row["amount"] == 88.50
        assert row["date"] == "2026-03-28"


# ------------------------------------------------------------------ #
# 4. Edge Cases & Boundary Value Tests                               #
# ------------------------------------------------------------------ #


def test_add_expense_minimum_positive_float_amount(client):
    """Test logging an expense with the smallest supported positive fractional currency amount (0.01)."""
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})

    response = client.post(
        "/expenses/add",
        data={
            "category": "Other",
            "amount": "0.01",
            "date": "2026-03-29",
            "description": "Smallest penny transaction",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"0.01" in response.data

    with app.app_context():
        db = get_db()
        row = db.execute(
            "SELECT * FROM expenses WHERE description = 'Smallest penny transaction'"
        ).fetchone()
        assert row is not None
        assert row["amount"] == 0.01


def test_add_expense_large_amount(client):
    """Test logging a high value expense transaction."""
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})

    response = client.post(
        "/expenses/add",
        data={
            "category": "Bills",
            "amount": "999999.99",
            "date": "2026-03-29",
            "description": "Annual Commercial Rent",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"999,999.99" in response.data

    with app.app_context():
        db = get_db()
        row = db.execute(
            "SELECT * FROM expenses WHERE description = 'Annual Commercial Rent'"
        ).fetchone()
        assert row is not None
        assert row["amount"] == 999999.99


def test_add_expense_boundary_dates(client):
    """Test adding expenses with boundary dates such as leap day, year start/end, and distant past/future dates."""
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})

    test_dates = [
        ("2024-02-29", "Leap Day 2024"),
        ("2026-12-31", "End of Year 2026"),
        ("2020-01-01", "Past Decade Start"),
        ("2035-05-15", "Future Projection"),
    ]

    for date_val, desc in test_dates:
        response = client.post(
            "/expenses/add",
            data={
                "category": "Health",
                "amount": "150.00",
                "date": date_val,
                "description": desc,
            },
            follow_redirects=True,
        )

        assert response.status_code == 200

        with app.app_context():
            db = get_db()
            row = db.execute(
                "SELECT * FROM expenses WHERE description = ?", (desc,)
            ).fetchone()
            assert row is not None
            assert row["date"] == date_val


# ------------------------------------------------------------------ #
# 5. Form Validation & Error Handling Tests                          #
# ------------------------------------------------------------------ #


def test_add_expense_missing_category(client):
    """Test validation error and form input preservation when category is omitted."""
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})

    response = client.post(
        "/expenses/add",
        data={
            "category": "",
            "amount": "250.00",
            "date": "2026-03-20",
            "description": "Omitted category test",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Category, Amount, and Date are required." in response.data
    assert b'value="250.00"' in response.data
    assert b'value="Omitted category test"' in response.data


def test_add_expense_missing_amount(client):
    """Test validation error and form input preservation when amount is omitted."""
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})

    response = client.post(
        "/expenses/add",
        data={
            "category": "Food",
            "amount": "",
            "date": "2026-03-20",
            "description": "Omitted amount test",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Category, Amount, and Date are required." in response.data
    assert b'value="Omitted amount test"' in response.data


def test_add_expense_missing_date(client):
    """Test validation error and form input preservation when date is omitted."""
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})

    response = client.post(
        "/expenses/add",
        data={
            "category": "Food",
            "amount": "300.00",
            "date": "",
            "description": "Omitted date test",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Category, Amount, and Date are required." in response.data
    assert b'value="300.00"' in response.data


def test_add_expense_zero_amount(client):
    """Test validation error when submitting an amount of 0."""
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})

    response = client.post(
        "/expenses/add",
        data={
            "category": "Food",
            "amount": "0",
            "date": "2026-03-20",
            "description": "Zero amount test",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Amount must be a positive number." in response.data


def test_add_expense_negative_amount(client):
    """Test validation error when submitting a negative amount."""
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})

    response = client.post(
        "/expenses/add",
        data={
            "category": "Food",
            "amount": "-75.50",
            "date": "2026-03-20",
            "description": "Negative amount test",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Amount must be a positive number." in response.data


def test_add_expense_non_numeric_amount(client):
    """Test validation error when submitting a non-numeric string amount."""
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})

    response = client.post(
        "/expenses/add",
        data={
            "category": "Food",
            "amount": "twenty-five",
            "date": "2026-03-20",
            "description": "Text amount test",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Amount must be a positive number." in response.data


def test_add_expense_invalid_category(client):
    """Test validation error when submitting an unsupported or unrecognized category."""
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})

    response = client.post(
        "/expenses/add",
        data={
            "category": "Cryptocurrency",
            "amount": "500.00",
            "date": "2026-03-20",
            "description": "Invalid category test",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Please select a valid category." in response.data


def test_add_expense_invalid_date_format(client):
    """Test validation error when submitting malformed or invalid date strings."""
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})

    invalid_dates = [
        "2026/03/20",
        "20-03-2026",
        "not-a-date",
        "2026-02-31",
        "2026-13-01",
    ]
    for bad_date in invalid_dates:
        response = client.post(
            "/expenses/add",
            data={
                "category": "Bills",
                "amount": "500.00",
                "date": bad_date,
                "description": "Invalid date test",
            },
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert b"Please enter a valid date in YYYY-MM-DD format." in response.data


def test_add_expense_validation_failure_does_not_insert_db_record(client):
    """Test that invalid form submissions do not create records in the database."""
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})

    with app.app_context():
        db = get_db()
        count_before = db.execute("SELECT COUNT(*) as cnt FROM expenses").fetchone()[
            "cnt"
        ]

    client.post(
        "/expenses/add",
        data={
            "category": "InvalidCategory",
            "amount": "-99.00",
            "date": "bad-date",
            "description": "Should not be stored",
        },
        follow_redirects=True,
    )

    with app.app_context():
        db = get_db()
        count_after = db.execute("SELECT COUNT(*) as cnt FROM expenses").fetchone()[
            "cnt"
        ]

    assert count_before == count_after


# ------------------------------------------------------------------ #
# 6. Database Side Effects & Downstream System Reflections Tests      #
# ------------------------------------------------------------------ #


def test_add_expense_direct_db_verification_and_user_link(client):
    """Test that adding an expense creates a row strictly tied to the logged-in user_id."""
    client.post(
        "/register",
        data={
            "name": "Linked User",
            "email": "linkeduser@spendly.com",
            "password": "password123",
            "confirm_password": "password123",
        },
    )

    with app.app_context():
        db = get_db()
        user = db.execute(
            "SELECT id FROM users WHERE email = 'linkeduser@spendly.com'"
        ).fetchone()
        user_id = user["id"]

    client.post(
        "/expenses/add",
        data={
            "category": "Food",
            "amount": "75.25",
            "date": "2026-03-30",
            "description": "Direct DB Link Check",
        },
        follow_redirects=True,
    )

    with app.app_context():
        db = get_db()
        expense = db.execute(
            "SELECT * FROM expenses WHERE description = 'Direct DB Link Check'"
        ).fetchone()
        assert expense is not None
        assert expense["user_id"] == user_id
        assert expense["category"] == "Food"
        assert expense["amount"] == 75.25
        assert expense["date"] == "2026-03-30"


def test_add_expense_updates_dashboard_and_profile_totals(client):
    """Test that adding a new expense immediately updates totals, recent transactions, and category breakdowns."""
    client.post(
        "/register",
        data={
            "name": "Reflection Tester",
            "email": "reflection@spendly.com",
            "password": "password123",
            "confirm_password": "password123",
        },
    )

    # Initially empty totals
    dash_init = client.get("/dashboard", follow_redirects=True)
    assert b"0.00" in dash_init.data

    # Add first expense
    client.post(
        "/expenses/add",
        data={
            "category": "Health",
            "amount": "450.00",
            "date": "2026-03-30",
            "description": "Medical Checkup",
        },
        follow_redirects=True,
    )

    # Add second expense
    client.post(
        "/expenses/add",
        data={
            "category": "Bills",
            "amount": "150.00",
            "date": "2026-03-31",
            "description": "Broadband Internet",
        },
        follow_redirects=True,
    )

    # Check Dashboard reflection (total = 600.00)
    dash_res = client.get("/dashboard", follow_redirects=True)
    assert dash_res.status_code == 200
    assert b"600.00" in dash_res.data
    assert b"Medical Checkup" in dash_res.data
    assert b"Broadband Internet" in dash_res.data

    # Check Profile reflection (total = 600.00, breakdown contains Health and Bills)
    prof_res = client.get("/profile")
    assert prof_res.status_code == 200
    assert b"600.00" in prof_res.data
    assert b"Medical Checkup" in prof_res.data
    assert b"Broadband Internet" in prof_res.data
    assert b"Health" in prof_res.data
    assert b"Bills" in prof_res.data
    assert b"450.00" in prof_res.data
    assert b"150.00" in prof_res.data


def test_add_expense_multi_user_isolation(client):
    """Test that expenses added by User A are completely isolated from User B's dashboard and profile."""
    # Register User A and create expense
    client.post(
        "/register",
        data={
            "name": "User Alpha",
            "email": "useralpha@spendly.com",
            "password": "password123",
            "confirm_password": "password123",
        },
    )
    client.post(
        "/expenses/add",
        data={
            "category": "Entertainment",
            "amount": "320.00",
            "date": "2026-03-30",
            "description": "Alpha Secret Cinema",
        },
        follow_redirects=True,
    )
    client.get("/logout")

    # Register User B
    client.post(
        "/register",
        data={
            "name": "User Beta",
            "email": "userbeta@spendly.com",
            "password": "password123",
            "confirm_password": "password123",
        },
    )

    # Verify User B's dashboard does not contain User A's expense
    beta_dash = client.get("/dashboard", follow_redirects=True)
    assert b"Alpha Secret Cinema" not in beta_dash.data
    assert b"320.00" not in beta_dash.data
    assert b"0.00" in beta_dash.data

    # Verify User B's profile does not contain User A's expense
    beta_prof = client.get("/profile")
    assert b"Alpha Secret Cinema" not in beta_prof.data
    assert b"320.00" not in beta_prof.data
    assert b"0.00" in beta_prof.data
