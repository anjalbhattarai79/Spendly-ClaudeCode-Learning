"""
Tests for the Add Expense feature (Step 6).

Covers:
- Happy path: valid expense submission
- Authentication guard: unauthenticated access redirects to login
- Validation errors: empty fields, negative amount, invalid category, future date, description too long
- Form value persistence: values preserved when errors occur
- Database side effects: expense correctly inserted with user_id
- Redirect behavior: to login when unauthenticated, to profile on success
"""

import pytest
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
import uuid


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def app():
    """Create a test Flask app with real database."""
    from app import app as flask_app
    from database.db import init_db

    flask_app.config.update({
        'TESTING': True,
        'SECRET_KEY': 'test-secret-key',
        'WTF_CSRF_ENABLED': False,
    })

    with flask_app.app_context():
        init_db()
        yield flask_app


@pytest.fixture
def client(app):
    """Test client for making requests."""
    return app.test_client()


@pytest.fixture
def auth_client(app, client):
    """A test client with a logged-in user."""
    from database.db import get_db

    conn = get_db()
    cursor = conn.cursor()

    # Insert test user with unique email
    unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    password_hash = generate_password_hash("testpass123")
    cursor.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Test User", unique_email, password_hash)
    )
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()

    # Log in the user
    client.post('/login', data={'email': unique_email, 'password': 'testpass123'})

    yield client

    # Cleanup test data
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM expenses WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()


# =============================================================================
# Test Classes
# =============================================================================

class TestAddExpenseAuthGuard:
    """Tests for authentication requirement on /expenses/add."""

    def test_get_unauthenticated_redirects_to_login(self, client):
        """GET /expenses/add without login should redirect to /login."""
        response = client.get('/expenses/add')
        assert response.status_code == 302
        assert '/login' in response.headers['Location'], \
            'Expected redirect to /login for unauthenticated GET request'

    def test_post_unauthenticated_redirects_to_login(self, client):
        """POST /expenses/add without login should redirect to /login."""
        response = client.post('/expenses/add', data={
            'amount': '50.00',
            'category': 'Food',
            'date': datetime.now().strftime('%Y-%m-%d'),
            'description': 'Test expense'
        })
        assert response.status_code == 302
        assert '/login' in response.headers['Location'], \
            'Expected redirect to /login for unauthenticated POST request'


class TestAddExpenseGetForm:
    """Tests for GET /expenses/add form rendering."""

    def test_get_authenticated_returns_form(self, auth_client):
        """GET /expenses/add for logged-in user should return form with 200."""
        response = auth_client.get('/expenses/add')
        assert response.status_code == 200, 'Expected 200 status for authenticated GET request'

    def test_get_returns_form_with_csrf_token(self, auth_client):
        """Form should include CSRF token for security."""
        response = auth_client.get('/expenses/add')
        assert b'csrf' in response.data or b'token' in response.data.lower(), \
            'Expected CSRF token in form'

    def test_get_form_includes_amount_input(self, auth_client):
        """Form should include amount input field."""
        response = auth_client.get('/expenses/add')
        assert b'amount' in response.data.lower(), \
            'Expected amount field in form'

    def test_get_form_includes_category_dropdown(self, auth_client):
        """Form should include category dropdown with all required options."""
        response = auth_client.get('/expenses/add')
        assert b'category' in response.data.lower(), \
            'Expected category field in form'
        # Check for all allowed categories
        categories = ['Food', 'Transport', 'Bills', 'Health', 'Entertainment', 'Shopping', 'Other']
        for category in categories:
            assert category.encode() in response.data, \
                f'Expected category "{category}" in dropdown'

    def test_get_form_includes_date_input(self, auth_client):
        """Form should include date input field."""
        response = auth_client.get('/expenses/add')
        assert b'date' in response.data.lower(), \
            'Expected date field in form'

    def test_get_form_date_defaults_to_today(self, auth_client):
        """Date input should default to today's date."""
        response = auth_client.get('/expenses/add')
        today = datetime.now().strftime('%Y-%m-%d')
        assert today.encode() in response.data, \
            f'Expected date field to default to today: {today}'

    def test_get_form_includes_description_textarea(self, auth_client):
        """Form should include optional description textarea."""
        response = auth_client.get('/expenses/add')
        assert b'description' in response.data.lower(), \
            'Expected description field in form'


class TestAddExpenseCSRF:
    """Tests for production CSRF validation."""

    def test_post_rejects_forged_csrf_token(self, auth_client, app):
        """A token that was not issued by the GET form should be rejected."""
        today = datetime.now().strftime('%Y-%m-%d')
        app.config['TESTING'] = False
        try:
            response = auth_client.post('/expenses/add', data={
                'csrf_token': 'forged-token',
                'amount': '50.00',
                'category': 'Food',
                'date': today,
                'description': 'Test'
            })
        finally:
            app.config['TESTING'] = True

        assert response.status_code == 400
        assert b'Invalid form submission' in response.data


class TestAddExpensePostHappyPath:
    """Tests for successful POST /expenses/add submission."""

    def test_post_valid_expense_redirects_to_profile(self, auth_client):
        """Valid expense submission should redirect to /profile."""
        today = datetime.now().strftime('%Y-%m-%d')
        response = auth_client.post('/expenses/add', data={
            'amount': '50.00',
            'category': 'Food',
            'date': today,
            'description': 'Lunch'
        }, follow_redirects=False)
        assert response.status_code == 302, \
            'Expected 302 redirect after successful submission'
        assert '/profile' in response.headers['Location'], \
            'Expected redirect to /profile'

    def test_post_valid_expense_inserts_into_database(self, app, auth_client):
        """Valid expense should be inserted into expenses table."""
        from database.db import get_db

        today = datetime.now().strftime('%Y-%m-%d')
        auth_client.post('/expenses/add', data={
            'amount': '75.50',
            'category': 'Transport',
            'date': today,
            'description': 'Bus ticket'
        })

        # Verify the expense was inserted
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT amount, category, date, description FROM expenses WHERE amount = ? AND category = ?",
            (75.50, 'Transport')
        )
        expense = cursor.fetchone()
        conn.close()

        assert expense is not None, 'Expected expense to be inserted into database'
        assert expense['amount'] == 75.50, 'Expected correct amount in database'
        assert expense['category'] == 'Transport', 'Expected correct category in database'
        assert expense['date'] == today, 'Expected correct date in database'
        assert expense['description'] == 'Bus ticket', 'Expected correct description in database'

    def test_post_valid_expense_associates_with_user_id(self, app, auth_client):
        """Inserted expense should have correct user_id."""
        from database.db import get_db

        # Get the logged-in user_id from session
        with auth_client.session_transaction() as sess:
            logged_in_user_id = sess.get('user_id')

        today = datetime.now().strftime('%Y-%m-%d')
        auth_client.post('/expenses/add', data={
            'amount': '100.00',
            'category': 'Food',
            'date': today,
            'description': 'Groceries'
        })

        # Verify the expense has correct user_id
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT user_id FROM expenses WHERE amount = ? AND category = ?",
            (100.00, 'Food')
        )
        expense = cursor.fetchone()
        conn.close()

        assert expense is not None, 'Expected expense to be inserted'
        assert expense['user_id'] == logged_in_user_id, \
            'Expected expense to be associated with correct user_id'

    def test_post_valid_expense_with_minimal_data(self, auth_client):
        """Expense submission with only required fields should succeed."""
        today = datetime.now().strftime('%Y-%m-%d')
        response = auth_client.post('/expenses/add', data={
            'amount': '25.00',
            'category': 'Shopping',
            'date': today
        }, follow_redirects=False)
        assert response.status_code == 302, \
            'Expected successful submission with minimal required data'

    def test_post_valid_expense_with_all_fields(self, auth_client):
        """Expense submission with all fields (including optional) should succeed."""
        today = datetime.now().strftime('%Y-%m-%d')
        response = auth_client.post('/expenses/add', data={
            'amount': '55.75',
            'category': 'Entertainment',
            'date': today,
            'description': 'Movie tickets and popcorn at the cinema'
        }, follow_redirects=False)
        assert response.status_code == 302, \
            'Expected successful submission with all fields'


class TestAddExpensePostValidationAmount:
    """Tests for amount field validation."""

    @pytest.mark.parametrize('invalid_amount', ['nan', 'inf', '-inf'])
    def test_post_non_finite_amount_shows_error(self, auth_client, invalid_amount):
        """POST with a non-finite amount should show an error."""
        today = datetime.now().strftime('%Y-%m-%d')
        response = auth_client.post('/expenses/add', data={
            'amount': invalid_amount,
            'category': 'Food',
            'date': today,
            'description': 'Test'
        })
        assert response.status_code != 302
        assert b'error' in response.data.lower() or b'greater than zero' in response.data.lower()

    def test_post_missing_amount_shows_error(self, auth_client):
        """POST without amount field should show error."""
        today = datetime.now().strftime('%Y-%m-%d')
        response = auth_client.post('/expenses/add', data={
            'category': 'Food',
            'date': today,
            'description': 'Test'
        })
        assert response.status_code != 302, \
            'Expected form to be re-rendered with error (not 302 redirect)'
        assert b'amount' in response.data.lower() and (
            b'required' in response.data.lower() or
            b'error' in response.data.lower()
        ), 'Expected error message for missing amount'

    def test_post_empty_amount_shows_error(self, auth_client):
        """POST with empty amount should show error."""
        today = datetime.now().strftime('%Y-%m-%d')
        response = auth_client.post('/expenses/add', data={
            'amount': '',
            'category': 'Food',
            'date': today,
            'description': 'Test'
        })
        assert response.status_code != 302, \
            'Expected form to be re-rendered with error (not 302 redirect)'
        assert b'error' in response.data.lower() or b'required' in response.data.lower(), \
            'Expected error message for empty amount'

    def test_post_negative_amount_shows_error(self, auth_client):
        """POST with negative amount should show error."""
        today = datetime.now().strftime('%Y-%m-%d')
        response = auth_client.post('/expenses/add', data={
            'amount': '-50.00',
            'category': 'Food',
            'date': today,
            'description': 'Test'
        })
        assert response.status_code != 302, \
            'Expected form to be re-rendered with error (not 302 redirect)'
        assert b'error' in response.data.lower() or b'positive' in response.data.lower(), \
            'Expected error message for negative amount'

    def test_post_zero_amount_shows_error(self, auth_client):
        """POST with zero amount should show error."""
        today = datetime.now().strftime('%Y-%m-%d')
        response = auth_client.post('/expenses/add', data={
            'amount': '0',
            'category': 'Food',
            'date': today,
            'description': 'Test'
        })
        assert response.status_code != 302, \
            'Expected form to be re-rendered with error (not 302 redirect)'
        assert b'error' in response.data.lower() or b'positive' in response.data.lower(), \
            'Expected error message for zero amount'

    def test_post_non_numeric_amount_shows_error(self, auth_client):
        """POST with non-numeric amount should show error."""
        today = datetime.now().strftime('%Y-%m-%d')
        response = auth_client.post('/expenses/add', data={
            'amount': 'abc',
            'category': 'Food',
            'date': today,
            'description': 'Test'
        })
        assert response.status_code != 302, \
            'Expected form to be re-rendered with error (not 302 redirect)'
        assert b'error' in response.data.lower(), \
            'Expected error message for non-numeric amount'


class TestAddExpensePostValidationCategory:
    """Tests for category field validation."""

    def test_post_missing_category_shows_error(self, auth_client):
        """POST without category field should show error."""
        today = datetime.now().strftime('%Y-%m-%d')
        response = auth_client.post('/expenses/add', data={
            'amount': '50.00',
            'date': today,
            'description': 'Test'
        })
        assert response.status_code != 302, \
            'Expected form to be re-rendered with error (not 302 redirect)'
        assert b'category' in response.data.lower() and (
            b'required' in response.data.lower() or
            b'error' in response.data.lower()
        ), 'Expected error message for missing category'

    def test_post_empty_category_shows_error(self, auth_client):
        """POST with empty category should show error."""
        today = datetime.now().strftime('%Y-%m-%d')
        response = auth_client.post('/expenses/add', data={
            'amount': '50.00',
            'category': '',
            'date': today,
            'description': 'Test'
        })
        assert response.status_code != 302, \
            'Expected form to be re-rendered with error (not 302 redirect)'
        assert b'error' in response.data.lower() or b'required' in response.data.lower(), \
            'Expected error message for empty category'

    def test_post_invalid_category_shows_error(self, auth_client):
        """POST with category not in allowed list should show error."""
        today = datetime.now().strftime('%Y-%m-%d')
        response = auth_client.post('/expenses/add', data={
            'amount': '50.00',
            'category': 'InvalidCategory',
            'date': today,
            'description': 'Test'
        })
        assert response.status_code != 302, \
            'Expected form to be re-rendered with error (not 302 redirect)'
        assert b'error' in response.data.lower() or b'category' in response.data.lower(), \
            'Expected error message for invalid category'

    @pytest.mark.parametrize('valid_category', [
        'Food', 'Transport', 'Bills', 'Health', 'Entertainment', 'Shopping', 'Other'
    ])
    def test_post_valid_categories_accepted(self, auth_client, valid_category):
        """Each allowed category should be accepted."""
        today = datetime.now().strftime('%Y-%m-%d')
        response = auth_client.post('/expenses/add', data={
            'amount': '50.00',
            'category': valid_category,
            'date': today,
            'description': 'Test'
        }, follow_redirects=False)
        assert response.status_code == 302, \
            f'Expected category "{valid_category}" to be accepted'


class TestAddExpensePostValidationDate:
    """Tests for date field validation."""

    def test_post_missing_date_shows_error(self, auth_client):
        """POST without date field should show error."""
        response = auth_client.post('/expenses/add', data={
            'amount': '50.00',
            'category': 'Food',
            'description': 'Test'
        })
        assert response.status_code != 302, \
            'Expected form to be re-rendered with error (not 302 redirect)'
        assert b'date' in response.data.lower() and (
            b'required' in response.data.lower() or
            b'error' in response.data.lower()
        ), 'Expected error message for missing date'

    def test_post_empty_date_shows_error(self, auth_client):
        """POST with empty date should show error."""
        response = auth_client.post('/expenses/add', data={
            'amount': '50.00',
            'category': 'Food',
            'date': '',
            'description': 'Test'
        })
        assert response.status_code != 302, \
            'Expected form to be re-rendered with error (not 302 redirect)'
        assert b'error' in response.data.lower() or b'required' in response.data.lower(), \
            'Expected error message for empty date'

    def test_post_invalid_date_format_shows_error(self, auth_client):
        """POST with invalid date format should show error."""
        response = auth_client.post('/expenses/add', data={
            'amount': '50.00',
            'category': 'Food',
            'date': '01-01-2025',  # Wrong format, should be YYYY-MM-DD
            'description': 'Test'
        })
        assert response.status_code != 302, \
            'Expected form to be re-rendered with error (not 302 redirect)'
        assert b'error' in response.data.lower() or b'date' in response.data.lower(), \
            'Expected error message for invalid date format'

    def test_post_future_date_shows_error(self, auth_client):
        """POST with future date should show error."""
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        response = auth_client.post('/expenses/add', data={
            'amount': '50.00',
            'category': 'Food',
            'date': tomorrow,
            'description': 'Test'
        })
        assert response.status_code != 302, \
            'Expected form to be re-rendered with error (not 302 redirect)'
        assert b'error' in response.data.lower() or b'future' in response.data.lower(), \
            'Expected error message for future date'

    def test_post_far_future_date_shows_error(self, auth_client):
        """POST with date far in the future should show error."""
        far_future = (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')
        response = auth_client.post('/expenses/add', data={
            'amount': '50.00',
            'category': 'Food',
            'date': far_future,
            'description': 'Test'
        })
        assert response.status_code != 302, \
            'Expected form to be re-rendered with error (not 302 redirect)'

    def test_post_today_date_accepted(self, auth_client):
        """POST with today's date should be accepted."""
        today = datetime.now().strftime('%Y-%m-%d')
        response = auth_client.post('/expenses/add', data={
            'amount': '50.00',
            'category': 'Food',
            'date': today,
            'description': 'Test'
        }, follow_redirects=False)
        assert response.status_code == 302, \
            'Expected today\'s date to be accepted'

    def test_post_past_date_accepted(self, auth_client):
        """POST with past date should be accepted."""
        past_date = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
        response = auth_client.post('/expenses/add', data={
            'amount': '50.00',
            'category': 'Food',
            'date': past_date,
            'description': 'Test'
        }, follow_redirects=False)
        assert response.status_code == 302, \
            'Expected past date to be accepted'


class TestAddExpensePostValidationDescription:
    """Tests for description field validation."""

    def test_post_description_is_optional(self, auth_client):
        """POST without description should be accepted (optional field)."""
        today = datetime.now().strftime('%Y-%m-%d')
        response = auth_client.post('/expenses/add', data={
            'amount': '50.00',
            'category': 'Food',
            'date': today
        }, follow_redirects=False)
        assert response.status_code == 302, \
            'Expected submission to succeed without description'

    def test_post_empty_description_accepted(self, auth_client):
        """POST with empty description should be accepted."""
        today = datetime.now().strftime('%Y-%m-%d')
        response = auth_client.post('/expenses/add', data={
            'amount': '50.00',
            'category': 'Food',
            'date': today,
            'description': ''
        }, follow_redirects=False)
        assert response.status_code == 302, \
            'Expected submission to succeed with empty description'

    def test_post_short_description_accepted(self, auth_client):
        """POST with short description should be accepted."""
        today = datetime.now().strftime('%Y-%m-%d')
        response = auth_client.post('/expenses/add', data={
            'amount': '50.00',
            'category': 'Food',
            'date': today,
            'description': 'Lunch'
        }, follow_redirects=False)
        assert response.status_code == 302, \
            'Expected short description to be accepted'

    def test_post_long_description_at_limit_accepted(self, auth_client):
        """POST with description at 500 char limit should be accepted."""
        today = datetime.now().strftime('%Y-%m-%d')
        long_desc = 'x' * 500
        response = auth_client.post('/expenses/add', data={
            'amount': '50.00',
            'category': 'Food',
            'date': today,
            'description': long_desc
        }, follow_redirects=False)
        assert response.status_code == 302, \
            'Expected 500-character description to be accepted'

    def test_post_description_over_limit_shows_error(self, auth_client):
        """POST with description over 500 chars should show error."""
        today = datetime.now().strftime('%Y-%m-%d')
        long_desc = 'x' * 501
        response = auth_client.post('/expenses/add', data={
            'amount': '50.00',
            'category': 'Food',
            'date': today,
            'description': long_desc
        })
        assert response.status_code != 302, \
            'Expected form to be re-rendered with error (not 302 redirect)'
        assert b'error' in response.data.lower() or b'description' in response.data.lower(), \
            'Expected error message for description over 500 chars'

    def test_post_description_way_over_limit_shows_error(self, auth_client):
        """POST with very long description should show error."""
        today = datetime.now().strftime('%Y-%m-%d')
        very_long_desc = 'x' * 1000
        response = auth_client.post('/expenses/add', data={
            'amount': '50.00',
            'category': 'Food',
            'date': today,
            'description': very_long_desc
        })
        assert response.status_code != 302, \
            'Expected form to be re-rendered with error (not 302 redirect)'


class TestAddExpensePostFormValuePersistence:
    """Tests for form value persistence when validation errors occur."""

    def test_form_preserves_amount_on_error(self, auth_client):
        """Form should preserve amount value when error occurs."""
        today = datetime.now().strftime('%Y-%m-%d')
        response = auth_client.post('/expenses/add', data={
            'amount': '75.50',
            'category': '',  # Empty category to trigger error
            'date': today,
            'description': 'Test'
        })
        assert b'75.50' in response.data or b'75' in response.data, \
            'Expected amount value to be preserved in form on error'

    def test_form_preserves_category_on_error(self, auth_client):
        """Form should preserve category value when error occurs."""
        today = datetime.now().strftime('%Y-%m-%d')
        response = auth_client.post('/expenses/add', data={
            'amount': '',  # Empty amount to trigger error
            'category': 'Transport',
            'date': today,
            'description': 'Test'
        })
        assert b'Transport' in response.data, \
            'Expected category value to be preserved in form on error'

    def test_form_preserves_date_on_error(self, auth_client):
        """Form should preserve date value when error occurs."""
        today = datetime.now().strftime('%Y-%m-%d')
        response = auth_client.post('/expenses/add', data={
            'amount': '50.00',
            'category': 'Food',
            'date': today,
            'description': 'x' * 501  # Long description to trigger error
        })
        assert today.encode() in response.data, \
            'Expected date value to be preserved in form on error'

    def test_form_preserves_description_on_error(self, auth_client):
        """Form should preserve description value when error occurs."""
        today = datetime.now().strftime('%Y-%m-%d')
        test_desc = 'This is my lunch'
        response = auth_client.post('/expenses/add', data={
            'amount': '-50',  # Negative to trigger error
            'category': 'Food',
            'date': today,
            'description': test_desc
        })
        assert test_desc.encode() in response.data, \
            'Expected description value to be preserved in form on error'

    def test_form_preserves_all_values_on_error(self, auth_client):
        """Form should preserve all values when error occurs."""
        today = datetime.now().strftime('%Y-%m-%d')
        response = auth_client.post('/expenses/add', data={
            'amount': '-99.99',
            'category': 'Shopping',
            'date': today,
            'description': 'New shoes and belt'
        })
        
        assert response.status_code != 302, \
            'Expected form to be re-rendered, not redirected'
        assert b'-99.99' in response.data
        assert b'Shopping' in response.data
        assert today.encode() in response.data
        assert b'New shoes and belt' in response.data


class TestAddExpensePostMultipleErrors:
    """Tests for handling multiple validation errors simultaneously."""

    def test_post_multiple_errors_shows_all_errors(self, auth_client):
        """POST with multiple validation errors should show form with errors."""
        response = auth_client.post('/expenses/add', data={
            'amount': 'abc',  # Invalid
            'category': '',  # Missing
            'date': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),  # Future
            'description': 'x' * 501  # Too long
        })
        assert response.status_code != 302, \
            'Expected form to be re-rendered with errors (not 302 redirect)'
        # Should show error indication
        assert b'error' in response.data.lower(), \
            'Expected error message to be shown'

    def test_post_empty_all_fields_shows_errors(self, auth_client):
        """POST with all fields empty should show error."""
        response = auth_client.post('/expenses/add', data={
            'amount': '',
            'category': '',
            'date': '',
            'description': ''
        })
        assert response.status_code != 302, \
            'Expected form to be re-rendered with errors (not 302 redirect)'
        assert b'error' in response.data.lower(), \
            'Expected error message to be shown'


class TestAddExpensePostEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_post_very_small_amount_accepted(self, auth_client):
        """POST with very small but positive amount should be accepted."""
        today = datetime.now().strftime('%Y-%m-%d')
        response = auth_client.post('/expenses/add', data={
            'amount': '0.01',
            'category': 'Food',
            'date': today,
            'description': 'Test'
        }, follow_redirects=False)
        assert response.status_code == 302, \
            'Expected very small positive amount to be accepted'

    def test_post_very_large_amount_accepted(self, auth_client):
        """POST with very large amount should be accepted."""
        today = datetime.now().strftime('%Y-%m-%d')
        response = auth_client.post('/expenses/add', data={
            'amount': '999999.99',
            'category': 'Shopping',
            'date': today,
            'description': 'Test'
        }, follow_redirects=False)
        assert response.status_code == 302, \
            'Expected very large amount to be accepted'

    def test_post_amount_with_whitespace_handled(self, auth_client):
        """POST with amount containing whitespace should be handled."""
        today = datetime.now().strftime('%Y-%m-%d')
        response = auth_client.post('/expenses/add', data={
            'amount': '  50.00  ',
            'category': 'Food',
            'date': today,
            'description': 'Test'
        }, follow_redirects=False)
        # Should either strip and accept, or reject with error
        assert response.status_code in [200, 302], \
            'Expected amount with whitespace to be handled gracefully'

    def test_post_description_with_special_characters(self, auth_client):
        """POST with description containing special characters should be accepted."""
        today = datetime.now().strftime('%Y-%m-%d')
        response = auth_client.post('/expenses/add', data={
            'amount': '50.00',
            'category': 'Food',
            'date': today,
            'description': 'Lunch @ café (50% off) & coffee'
        }, follow_redirects=False)
        assert response.status_code == 302, \
            'Expected description with special characters to be accepted'

    def test_post_description_with_unicode_characters(self, auth_client):
        """POST with description containing unicode characters should be accepted."""
        today = datetime.now().strftime('%Y-%m-%d')
        response = auth_client.post('/expenses/add', data={
            'amount': '50.00',
            'category': 'Food',
            'date': today,
            'description': 'Café, naïve, 日本料理'
        }, follow_redirects=False)
        assert response.status_code == 302, \
            'Expected description with unicode characters to be accepted'

    def test_post_oldest_possible_date_accepted(self, auth_client):
        """POST with very old date should be accepted."""
        old_date = '1970-01-01'
        response = auth_client.post('/expenses/add', data={
            'amount': '50.00',
            'category': 'Food',
            'date': old_date,
            'description': 'Test'
        }, follow_redirects=False)
        assert response.status_code == 302, \
            'Expected very old date to be accepted'

    def test_post_recent_past_date_accepted(self, auth_client):
        """POST with date from several months ago should be accepted."""
        old_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
        response = auth_client.post('/expenses/add', data={
            'amount': '50.00',
            'category': 'Food',
            'date': old_date,
            'description': 'Test'
        }, follow_redirects=False)
        assert response.status_code == 302, \
            'Expected date from 6 months ago to be accepted'
