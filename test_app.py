import os
import tempfile
import pytest
from app import app
import database.db
from database.db import init_db, seed_db

@pytest.fixture
def client():
    # Create a temporary file to use as the test database
    db_fd, temp_db_path = tempfile.mkstemp()
    
    # Save the original database path and update it to the temp path
    original_db_path = database.db.DB_PATH
    database.db.DB_PATH = temp_db_path
    
    app.config['TESTING'] = True
    
    # Initialize and seed the temporary test database
    with app.app_context():
        init_db()
        seed_db()
        
    with app.test_client() as client:
        yield client
        
    # Clean up the temporary database file after tests finish
    os.close(db_fd)
    try:
        os.unlink(temp_db_path)
    except OSError:
        pass
    database.db.DB_PATH = original_db_path

def test_landing_page(client):
    """Test that the landing page renders correctly."""
    response = client.get('/')
    assert response.status_code == 200
    assert b"Spendly" in response.data
    assert b"Know where it goes" in response.data
    assert b"Terms and Conditions" in response.data
    assert b"Privacy Policy" in response.data

def test_terms_page(client):
    """Test that the terms page renders correctly with required sections."""
    response = client.get('/terms')
    assert response.status_code == 200
    assert b"Terms and Conditions" in response.data
    assert b"Acceptance of Terms" in response.data
    assert b"Use of Service" in response.data
    assert b"User Data" in response.data
    assert b"Limitations of Liability" in response.data
    assert b"Changes to Terms" in response.data
def test_privacy_page(client):
    """Test that the privacy policy page renders correctly with required sections."""
    response = client.get('/privacy')
    assert response.status_code == 200
    assert b"Privacy Policy" in response.data
    assert b"Data We Collect" in response.data
    assert b"How We Use Your Data" in response.data
    assert b"Data Storage" in response.data
    assert b"Third Party Services" in response.data
    assert b"Contact Us" in response.data


def test_register_page_render(client):
    """Test that the GET /register page renders correctly."""
    response = client.get('/register')
    assert response.status_code == 200
    assert b"Create your account" in response.data
    assert b"Start tracking your expenses today" in response.data


def test_registration(client):
    """Test successful user registration process."""
    response = client.post('/register', data={
        'name': 'Test User',
        'email': 'testuser@example.com',
        'password': 'password123',
        'confirm_password': 'password123'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Welcome, Test User" in response.data
    assert b"Recent Transactions" in response.data


def test_registration_missing_fields(client):
    """Test registration failure with missing fields."""
    response = client.post('/register', data={
        'name': '',
        'email': 'testuser@example.com',
        'password': 'password123',
        'confirm_password': 'password123'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"All fields are required." in response.data


def test_registration_uncapitalized_name(client):
    """Test registration failure when name does not start with a capital letter."""
    response = client.post('/register', data={
        'name': 'tariq Khan',
        'email': 'tariq@example.com',
        'password': 'password123',
        'confirm_password': 'password123'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Name must start with a capital letter." in response.data


def test_registration_invalid_email_pattern(client):
    """Test registration failure with invalid email pattern (e.g. 123@123)."""
    response = client.post('/register', data={
        'name': 'Valid Name',
        'email': '123@123',
        'password': 'password123',
        'confirm_password': 'password123'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Please enter a valid email address." in response.data


def test_registration_short_password(client):
    """Test registration failure with password less than 8 characters."""
    response = client.post('/register', data={
        'name': 'Short Pass',
        'email': 'shortpass@example.com',
        'password': 'short',
        'confirm_password': 'short'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Password must be at least 8 characters long." in response.data


def test_registration_password_mismatch(client):
    """Test registration failure when password and confirm_password do not match."""
    response = client.post('/register', data={
        'name': 'Mismatch User',
        'email': 'mismatch@example.com',
        'password': 'password123',
        'confirm_password': 'differentpassword'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Passwords do not match." in response.data
    # Verify name and email are preserved in the response form
    assert b'value="Mismatch User"' in response.data
    assert b'value="mismatch@example.com"' in response.data


def test_registration_duplicate_email(client):
    """Test registration failure with an existing email address."""
    response = client.post('/register', data={
        'name': 'Duplicate User',
        'email': 'demo@spendly.com',
        'password': 'password123',
        'confirm_password': 'password123'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"An account with this email already exists." in response.data


def test_registration_redirect_if_logged_in(client):
    """Test that an authenticated user accessing /register is redirected to dashboard."""
    # Login first
    client.post('/login', data={
        'email': 'demo@spendly.com',
        'password': 'demo123'
    })
    
    # Access GET /register
    response = client.get('/register', follow_redirects=True)
    assert response.status_code == 200
    assert b"Welcome, Demo User" in response.data


def test_login_page_render(client):
    """Test that GET /login page renders correctly."""
    response = client.get('/login')
    assert response.status_code == 200
    assert b"Welcome back" in response.data
    assert b"Sign in to your Spendly account" in response.data


def test_login_logout(client):
    """Test logging in with valid credentials and logging out."""
    # Login with the seeded test user
    response = client.post('/login', data={
        'email': 'demo@spendly.com',
        'password': 'demo123'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"My Profile" in response.data
    assert b"Demo User" in response.data
    
    # Logout
    response = client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b"Sign in" in response.data


def test_login_missing_fields(client):
    """Test login failure when submitting missing email or password."""
    response = client.post('/login', data={
        'email': '',
        'password': 'demo123'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Please provide email and password." in response.data

    response = client.post('/login', data={
        'email': 'demo@spendly.com',
        'password': ''
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Please provide email and password." in response.data


def test_login_invalid_password(client):
    """Test login failure when providing wrong password for existing user."""
    response = client.post('/login', data={
        'email': 'demo@spendly.com',
        'password': 'wrongpassword'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Invalid email or password." in response.data
    assert b'value="demo@spendly.com"' in response.data


def test_login_nonexistent_email(client):
    """Test login failure when providing non-existent email."""
    response = client.post('/login', data={
        'email': 'nonexistent@spendly.com',
        'password': 'demo123'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Invalid email or password." in response.data


def test_login_success(client):
    """Test successful login with valid credentials redirects to profile page."""
    response = client.post('/login', data={
        'email': 'demo@spendly.com',
        'password': 'demo123'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"My Profile" in response.data
    assert b"Demo User" in response.data


def test_logout_clears_session(client):
    """Test that logging out clears user session and redirects to landing page."""
    # Login first
    client.post('/login', data={
        'email': 'demo@spendly.com',
        'password': 'demo123'
    })
    # Logout
    response = client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b"Know where it goes" in response.data
    # Verify session is cleared by attempting to access protected route profile
    protected_response = client.get('/profile', follow_redirects=False)
    assert protected_response.status_code == 302
    assert '/login' in protected_response.headers['Location']


def test_login_redirect_if_logged_in(client):
    """Test that an authenticated user accessing GET /login is redirected to profile."""
    client.post('/login', data={
        'email': 'demo@spendly.com',
        'password': 'demo123'
    })
    response = client.get('/login', follow_redirects=True)
    assert response.status_code == 200
    assert b"My Profile" in response.data

def test_add_expense(client):
    """Test adding a new expense."""
    client.post('/login', data={
        'email': 'demo@spendly.com',
        'password': 'demo123'
    })
    
    response = client.post('/expenses/add', data={
        'category': 'Food',
        'amount': '450.50',
        'date': '2026-03-20',
        'description': 'Lunch with team'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Lunch with team" in response.data
    assert b"450.50" in response.data

def test_edit_expense(client):
    """Test editing an existing expense."""
    client.post('/login', data={
        'email': 'demo@spendly.com',
        'password': 'demo123'
    })
    
    response = client.post('/expenses/1/edit', data={
        'category': 'Bills',
        'amount': '5000.00', # changed from 4500.00
        'date': '2026-03-01',
        'description': 'Rent & electricity (updated)'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Rent &amp; electricity (updated)" in response.data
    assert b"5,000.00" in response.data

def test_delete_expense(client):
    """Test deleting an expense."""
    client.post('/login', data={
        'email': 'demo@spendly.com',
        'password': 'demo123'
    })
    
    # Delete expense id 1 (seeded 'Bills' expense)
    response = client.get('/expenses/1/delete', follow_redirects=True)
    assert response.status_code == 200
    assert b"Rent & electricity" not in response.data

def test_seed_db_idempotency(client):
    """Test calling seed_db multiple times does not duplicate data."""
    with app.app_context():
        seed_db()
        seed_db()
        db = database.db.get_db()
        user_count = db.execute("SELECT COUNT(*) as count FROM users").fetchone()["count"]
        expense_count = db.execute("SELECT COUNT(*) as count FROM expenses").fetchone()["count"]
        assert user_count == 1
        assert expense_count == 8

def test_foreign_key_enforcement(client):
    """Test foreign key constraint enforcement on expenses table."""
    import sqlite3
    with app.app_context():
        db = database.db.get_db()
        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                "INSERT INTO expenses (user_id, category, amount, date) VALUES (?, ?, ?, ?)",
                (9999, "Food", 100.0, "2026-03-01")
            )


def test_profile_requires_login(client):
    """Test accessing GET /profile when unauthenticated redirects to /login."""
    response = client.get('/profile', follow_redirects=False)
    assert response.status_code == 302
    assert '/login' in response.headers['Location']


def test_profile_page_authenticated(client):
    """Test authenticated GET /profile renders user card, summary stats, recent transactions, and category breakdown."""
    client.post('/login', data={
        'email': 'demo@spendly.com',
        'password': 'demo123'
    })
    response = client.get('/profile')
    assert response.status_code == 200
    # User info card assertions
    assert b"Demo User" in response.data
    assert b"demo@spendly.com" in response.data
    assert b"Member Since" in response.data
    assert b"DU" in response.data

    # Summary stats row assertions
    assert b"Total Spent" in response.data
    assert b"Transactions" in response.data
    assert b"Top Category" in response.data

    # Recent transactions table assertions
    assert b"Recent Transactions" in response.data
    assert b"Dinner with friends" in response.data
    assert b"Rent &amp; electricity" in response.data

    # Category breakdown assertions
    assert b"Category Breakdown" in response.data
    assert b"Bills" in response.data
    assert b"Food" in response.data


def test_profile_dynamic_user_details(client):
    """Test dynamic user details (name, email, initials, member_since) from database."""
    client.post('/register', data={
        'name': 'Sarah Connor',
        'email': 'sarah@skynet.com',
        'password': 'password123',
        'confirm_password': 'password123'
    })
    response = client.get('/profile')
    assert response.status_code == 200
    assert b"Sarah Connor" in response.data
    assert b"sarah@skynet.com" in response.data
    assert b"SC" in response.data


def test_profile_user_info_and_initials(client):
    """Test multi-part name initials ('Ali Tariq Khan' -> 'AK')."""
    client.post('/register', data={
        'name': 'Ali Tariq Khan',
        'email': 'ali@example.com',
        'password': 'password123',
        'confirm_password': 'password123'
    })
    response = client.get('/profile')
    assert response.status_code == 200
    assert b"Ali Tariq Khan" in response.data
    assert b"ali@example.com" in response.data
    assert b"AK" in response.data


def test_profile_single_name_initials(client):
    """Test single name initials ('Ahmed' -> 'A')."""
    client.post('/register', data={
        'name': 'Ahmed',
        'email': 'ahmed@example.com',
        'password': 'password123',
        'confirm_password': 'password123'
    })
    response = client.get('/profile')
    assert response.status_code == 200
    assert b"Ahmed" in response.data
    assert b"A" in response.data


def test_profile_recent_transactions_live_db(client):
    """Test recent transactions table on /profile queries database sorted by date DESC, id DESC with max 10 items."""
    client.post('/register', data={
        'name': 'Recent Tx User',
        'email': 'recenttx@example.com',
        'password': 'password123',
        'confirm_password': 'password123'
    })

    for i in range(1, 13):
        date_str = f"2026-03-{i:02d}"
        client.post('/expenses/add', data={
            'category': 'Food' if i % 2 == 0 else 'Bills',
            'amount': str(100.0 * i),
            'date': date_str,
            'description': f"Expense item {i:02d}"
        })

    response = client.get('/profile')
    assert response.status_code == 200

    assert b"Expense item 12" in response.data
    assert b"Expense item 03" in response.data
    assert b"Expense item 01" not in response.data
    assert b"Expense item 02" not in response.data
    assert b"badge-food" in response.data
    assert b"badge-bills" in response.data


def test_profile_empty_expenses_state(client):
    """Test /profile renders clean empty state when user has no recorded transactions."""
    client.post('/register', data={
        'name': 'Empty Tx User',
        'email': 'emptytx@example.com',
        'password': 'password123',
        'confirm_password': 'password123'
    })

    response = client.get('/profile')
    assert response.status_code == 200
    assert b"0.00" in response.data
    assert b"N/A" in response.data
    assert b"No transactions recorded yet." in response.data
    assert b"No spending categories to display." in response.data


def test_profile_category_breakdown_dynamic(client):
    """Test category breakdown percentage and amount calculations from database."""
    client.post('/register', data={
        'name': 'Breakdown User',
        'email': 'breakdown@example.com',
        'password': 'password123',
        'confirm_password': 'password123'
    })
    # Add 750 in Bills (75%), 250 in Food (25%)
    client.post('/expenses/add', data={'category': 'Bills', 'amount': '750.00', 'date': '2026-03-10', 'description': 'Electric bill'})
    client.post('/expenses/add', data={'category': 'Food', 'amount': '250.00', 'date': '2026-03-11', 'description': 'Lunch'})

    response = client.get('/profile')
    assert response.status_code == 200
    assert b"750.00" in response.data
    assert b"75%" in response.data
    assert b"250.00" in response.data
    assert b"25%" in response.data



