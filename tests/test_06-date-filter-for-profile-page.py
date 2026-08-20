import os
import tempfile
import pytest
from datetime import datetime, timedelta, date
from app import app
import database.db
from database.db import init_db, seed_db, get_db

@pytest.fixture
def client():
    """Fixture to set up an isolated temporary SQLite database for each test."""
    db_fd, temp_db_path = tempfile.mkstemp()
    original_db_path = database.db.DB_PATH
    database.db.DB_PATH = temp_db_path
    
    app.config['TESTING'] = True
    
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

def test_date_filter_auth_guard(client):
    """Test that accessing GET /profile with date filters while unauthenticated redirects to /login."""
    response = client.get('/profile?start_date=2026-01-01&end_date=2026-01-31', follow_redirects=False)
    assert response.status_code == 302
    assert '/login' in response.headers['Location']


# ------------------------------------------------------------------ #
# 2. Form Rendering & Input Persistence Tests                        #
# ------------------------------------------------------------------ #

def test_date_filter_form_rendering_and_persistence(client):
    """Test that date filter controls are rendered on the profile page and retain selected input values."""
    # Authenticate user
    client.post('/login', data={'email': 'demo@spendly.com', 'password': 'demo123'})
    
    # Request profile with date range parameters
    response = client.get('/profile?start_date=2026-02-01&end_date=2026-02-28')
    assert response.status_code == 200
    
    # Verify presence of form controls
    assert b'start_date' in response.data
    assert b'end_date' in response.data
    assert b'value="2026-02-01"' in response.data
    assert b'value="2026-02-28"' in response.data
    
    # Verify submit/filter button and clear/reset button/link exist
    assert b'Apply' in response.data or b'Filter' in response.data or b'Submit' in response.data
    assert b'Clear' in response.data or b'Reset' in response.data or b'All Time' in response.data


# ------------------------------------------------------------------ #
# 3. Happy Path: Date Range Filtering Tests                         #
# ------------------------------------------------------------------ #

def test_date_filter_range_happy_path(client):
    """Test date range filtering accurately recalculates stats, transactions, and category breakdown within range."""
    # Create isolated user with specific dated transactions
    client.post('/register', data={
        'name': 'Date Range Tester',
        'email': 'daterange@example.com',
        'password': 'password123',
        'confirm_password': 'password123'
    })
    
    # Add expenses across different months
    client.post('/expenses/add', data={
        'category': 'Food', 'amount': '50.00', 'date': '2026-01-10', 'description': 'January Snack'
    })
    client.post('/expenses/add', data={
        'category': 'Bills', 'amount': '200.00', 'date': '2026-02-14', 'description': 'February Electricity'
    })
    client.post('/expenses/add', data={
        'category': 'Food', 'amount': '100.00', 'date': '2026-02-20', 'description': 'February Dinner'
    })
    client.post('/expenses/add', data={
        'category': 'Shopping', 'amount': '300.00', 'date': '2026-03-05', 'description': 'March Jacket'
    })
    
    # Filter for February 2026
    response = client.get('/profile?start_date=2026-02-01&end_date=2026-02-28')
    assert response.status_code == 200
    
    # Summary stats verification: Total spent = 300.00 (200 + 100)
    assert b"300.00" in response.data
    
    # Recent transactions verification
    assert b"February Electricity" in response.data
    assert b"February Dinner" in response.data
    assert b"January Snack" not in response.data
    assert b"March Jacket" not in response.data
    
    # Category breakdown verification (Bills & Food present, Shopping absent)
    assert b"Bills" in response.data
    assert b"Food" in response.data
    assert b"200.00" in response.data
    assert b"100.00" in response.data


def test_date_filter_start_date_only(client):
    """Test filtering with start_date only includes expenses on or after start_date."""
    client.post('/register', data={
        'name': 'Start Date Tester',
        'email': 'startdate@example.com',
        'password': 'password123',
        'confirm_password': 'password123'
    })
    
    client.post('/expenses/add', data={'category': 'Food', 'amount': '40.00', 'date': '2026-01-15', 'description': 'Early Jan Food'})
    client.post('/expenses/add', data={'category': 'Bills', 'amount': '120.00', 'date': '2026-02-15', 'description': 'Mid Feb Bill'})
    client.post('/expenses/add', data={'category': 'Entertainment', 'amount': '80.00', 'date': '2026-03-15', 'description': 'Mid Mar Concert'})
    
    # Filter from 2026-02-01 onwards
    response = client.get('/profile?start_date=2026-02-01')
    assert response.status_code == 200
    
    # Total spent = 200.00 (120 + 80)
    assert b"200.00" in response.data
    assert b"Mid Feb Bill" in response.data
    assert b"Mid Mar Concert" in response.data
    assert b"Early Jan Food" not in response.data


def test_date_filter_end_date_only(client):
    """Test filtering with end_date only includes expenses on or before end_date."""
    client.post('/register', data={
        'name': 'End Date Tester',
        'email': 'enddate@example.com',
        'password': 'password123',
        'confirm_password': 'password123'
    })
    
    client.post('/expenses/add', data={'category': 'Food', 'amount': '40.00', 'date': '2026-01-15', 'description': 'Early Jan Food'})
    client.post('/expenses/add', data={'category': 'Bills', 'amount': '120.00', 'date': '2026-02-15', 'description': 'Mid Feb Bill'})
    client.post('/expenses/add', data={'category': 'Entertainment', 'amount': '80.00', 'date': '2026-03-15', 'description': 'Mid Mar Concert'})
    
    # Filter up to 2026-02-28
    response = client.get('/profile?end_date=2026-02-28')
    assert response.status_code == 200
    
    # Total spent = 160.00 (40 + 120)
    assert b"160.00" in response.data
    assert b"Early Jan Food" in response.data
    assert b"Mid Feb Bill" in response.data
    assert b"Mid Mar Concert" not in response.data


# ------------------------------------------------------------------ #
# 4. Boundary & Edge Case Tests                                     #
# ------------------------------------------------------------------ #

def test_date_filter_inclusive_boundaries(client):
    """Test that start_date and end_date filtering includes expenses matching exact boundary dates."""
    client.post('/register', data={
        'name': 'Boundary Tester',
        'email': 'boundary@example.com',
        'password': 'password123',
        'confirm_password': 'password123'
    })
    
    # Expenses exactly on boundary dates and outside
    client.post('/expenses/add', data={'category': 'Food', 'amount': '25.00', 'date': '2026-01-31', 'description': 'Day Before Start'})
    client.post('/expenses/add', data={'category': 'Food', 'amount': '100.00', 'date': '2026-02-01', 'description': 'Exact Start Date'})
    client.post('/expenses/add', data={'category': 'Bills', 'amount': '150.00', 'date': '2026-02-28', 'description': 'Exact End Date'})
    client.post('/expenses/add', data={'category': 'Shopping', 'amount': '45.00', 'date': '2026-03-01', 'description': 'Day After End'})
    
    response = client.get('/profile?start_date=2026-02-01&end_date=2026-02-28')
    assert response.status_code == 200
    
    # Total spent = 250.00 (100 + 150)
    assert b"250.00" in response.data
    assert b"Exact Start Date" in response.data
    assert b"Exact End Date" in response.data
    assert b"Day Before Start" not in response.data
    assert b"Day After End" not in response.data


def test_date_filter_zero_results_empty_state(client):
    """Test filtering for a date range with no transactions renders clean empty states without errors or crashes."""
    client.post('/register', data={
        'name': 'Empty Window Tester',
        'email': 'emptywindow@example.com',
        'password': 'password123',
        'confirm_password': 'password123'
    })
    
    client.post('/expenses/add', data={'category': 'Food', 'amount': '50.00', 'date': '2026-01-10', 'description': 'Jan Food'})
    
    # Query future date range with 0 transactions
    response = client.get('/profile?start_date=2027-06-01&end_date=2027-06-30')
    assert response.status_code == 200
    
    # Zero totals, N/A top category, and clean empty state messages
    assert b"0.00" in response.data
    assert b"N/A" in response.data
    assert b"No transactions recorded yet." in response.data or b"No transactions" in response.data
    assert b"No spending categories to display." in response.data or b"No spending categories" in response.data


def test_date_filter_inverted_range(client):
    """Test handling of inverted date range (start_date > end_date) gracefully without crashing."""
    client.post('/register', data={
        'name': 'Inverted Tester',
        'email': 'inverted@example.com',
        'password': 'password123',
        'confirm_password': 'password123'
    })
    client.post('/expenses/add', data={'category': 'Food', 'amount': '50.00', 'date': '2026-02-15', 'description': 'Feb Food'})
    
    # Start date is after end date
    response = client.get('/profile?start_date=2026-12-31&end_date=2026-01-01')
    assert response.status_code == 200
    assert b"0.00" in response.data


def test_date_filter_malformed_input(client):
    """Test resilience against malformed date query parameters (SQL injection / invalid format)."""
    client.post('/register', data={
        'name': 'Malformed Tester',
        'email': 'malformed@example.com',
        'password': 'password123',
        'confirm_password': 'password123'
    })
    
    # Invalid date strings and SQL injection payloads
    response = client.get('/profile?start_date=invalid-date&end_date=\'; DROP TABLE expenses; --')
    assert response.status_code == 200
    
    # Confirm expenses table was not dropped and user can still view page
    with app.app_context():
        db = get_db()
        table_check = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='expenses'").fetchone()
        assert table_check is not None


# ------------------------------------------------------------------ #
# 5. Reset & Data Isolation Tests                                    #
# ------------------------------------------------------------------ #

def test_date_filter_clear_resets_to_all_transactions(client):
    """Test clearing or omitting date filters restores full profile data across all time."""
    client.post('/register', data={
        'name': 'Reset Tester',
        'email': 'reset@example.com',
        'password': 'password123',
        'confirm_password': 'password123'
    })
    
    client.post('/expenses/add', data={'category': 'Food', 'amount': '30.00', 'date': '2026-01-05', 'description': 'Jan Item'})
    client.post('/expenses/add', data={'category': 'Bills', 'amount': '70.00', 'date': '2026-03-05', 'description': 'Mar Item'})
    
    # Filter for Jan first
    filtered_res = client.get('/profile?start_date=2026-01-01&end_date=2026-01-31')
    assert b"30.00" in filtered_res.data
    assert b"Mar Item" not in filtered_res.data
    
    # Clear filter (access /profile without date params)
    unfiltered_res = client.get('/profile')
    assert unfiltered_res.status_code == 200
    assert b"100.00" in unfiltered_res.data
    assert b"Jan Item" in unfiltered_res.data
    assert b"Mar Item" in unfiltered_res.data


def test_date_filter_user_info_preserved(client):
    """Test that profile user info card (name, email, member since, initials) remains intact regardless of date filters."""
    client.post('/register', data={
        'name': 'Eleanor Vance',
        'email': 'eleanor@example.com',
        'password': 'password123',
        'confirm_password': 'password123'
    })
    
    response = client.get('/profile?start_date=2026-01-01&end_date=2026-01-31')
    assert response.status_code == 200
    assert b"Eleanor Vance" in response.data
    assert b"eleanor@example.com" in response.data
    assert b"EV" in response.data
    assert b"Member Since" in response.data


def test_date_filter_multi_user_isolation(client):
    """Test that date filtering for User A never returns or includes expenses from User B."""
    # Register User A
    client.post('/register', data={
        'name': 'User A', 'email': 'usera@example.com', 'password': 'password123', 'confirm_password': 'password123'
    })
    client.post('/expenses/add', data={'category': 'Food', 'amount': '50.00', 'date': '2026-02-15', 'description': 'User A Secret Snack'})
    client.get('/logout')
    
    # Register User B
    client.post('/register', data={
        'name': 'User B', 'email': 'userb@example.com', 'password': 'password123', 'confirm_password': 'password123'
    })
    client.post('/expenses/add', data={'category': 'Bills', 'amount': '500.00', 'date': '2026-02-15', 'description': 'User B Big Rent'})
    
    # Request profile date filter while logged in as User B
    response = client.get('/profile?start_date=2026-02-01&end_date=2026-02-28')
    assert response.status_code == 200
    assert b"User B Big Rent" in response.data
    assert b"500.00" in response.data
    assert b"User A Secret Snack" not in response.data
    assert b"50.00" not in response.data


def test_date_filter_no_db_side_effects(client):
    """Test that applying date filters via GET query parameters does not alter or delete database records."""
    client.post('/register', data={
        'name': 'DB Side Effect Tester',
        'email': 'dbsideeffect@example.com',
        'password': 'password123',
        'confirm_password': 'password123'
    })
    client.post('/expenses/add', data={'category': 'Food', 'amount': '10.00', 'date': '2026-01-01', 'description': 'Item 1'})
    client.post('/expenses/add', data={'category': 'Food', 'amount': '20.00', 'date': '2026-02-01', 'description': 'Item 2'})
    
    # Count expenses in DB before filter request
    with app.app_context():
        db = get_db()
        count_before = db.execute("SELECT COUNT(*) as count FROM expenses").fetchone()["count"]
        
    # Perform GET request with date filters
    client.get('/profile?start_date=2026-01-01&end_date=2026-01-15')
    
    # Count expenses in DB after filter request
    with app.app_context():
        db = get_db()
        count_after = db.execute("SELECT COUNT(*) as count FROM expenses").fetchone()["count"]
        
    assert count_before == count_after
