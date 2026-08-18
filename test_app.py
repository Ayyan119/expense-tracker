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
    assert b"Know where your" in response.data
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


def test_registration(client):
    """Test user registration process."""
    response = client.post('/register', data={
        'name': 'Test User',
        'email': 'testuser@example.com',
        'password': 'password123'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Welcome, Test User" in response.data
    assert b"Recent Transactions" in response.data

def test_login_logout(client):
    """Test logging in and logging out."""
    # Login with the seeded test user
    response = client.post('/login', data={
        'email': 'nitish@example.com',
        'password': 'password123'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Welcome, Nitish Kumar" in response.data
    
    # Logout
    response = client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b"Sign in" in response.data

def test_add_expense(client):
    """Test adding a new expense."""
    client.post('/login', data={
        'email': 'nitish@example.com',
        'password': 'password123'
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
        'email': 'nitish@example.com',
        'password': 'password123'
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
        'email': 'nitish@example.com',
        'password': 'password123'
    })
    
    # Delete expense id 1 (seeded 'Bills' expense)
    response = client.get('/expenses/1/delete', follow_redirects=True)
    assert response.status_code == 200
    assert b"Rent & electricity" not in response.data
