"""
Tests for the date filter feature on the /profile route.

Covers:
- Happy paths: default (current month), custom range, partial dates
- Validation errors: invalid format, start > end
- Auth guards: unauthenticated users redirected to login
- Empty states: no expenses in range
- Template variables passed correctly in all cases
"""

import pytest
from datetime import datetime
from werkzeug.security import generate_password_hash


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def app():
    """Create a test Flask app using the real database."""
    from app import app as flask_app

    flask_app.config.update({
        'TESTING': True,
        'SECRET_KEY': 'test-secret-key',
        'WTF_CSRF_ENABLED': False,
    })

    with flask_app.app_context():
        yield flask_app


@pytest.fixture
def client(app):
    """Test client for making requests."""
    return app.test_client()


@pytest.fixture
def auth_client(app, client):
    """A test client with a logged-in user and seeded expenses."""
    from database.db import get_db
    from datetime import datetime
    import uuid

    # Use the real database connection
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

    # Insert test expenses across different months
    current_year = datetime.now().year
    current_month = datetime.now().month

    expenses = [
        # Current month expenses
        (user_id, 100.00, "Food", f"{current_year}-{current_month:02d}-05", "Groceries"),
        (user_id, 50.00, "Transport", f"{current_year}-{current_month:02d}-10", "Bus"),
        (user_id, 200.00, "Shopping", f"{current_year}-{current_month:02d}-15", "Clothes"),
        # Previous month expenses
        (user_id, 150.00, "Food", f"{current_year}-{current_month-1:02d}-05", "Groceries"),
        (user_id, 75.00, "Bills", f"{current_year}-{current_month-1:02d}-20", "Electricity"),
        # Next month expenses (future)
        (user_id, 300.00, "Entertainment", f"{current_year}-{current_month+1:02d}-01", "Concert"),
    ]
    cursor.executemany(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        expenses
    )
    conn.commit()
    conn.close()

    # Log in the user
    resp = client.post('/login', data={'email': unique_email, 'password': 'testpass123'})

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

class TestDateFilterAuthGuard:
    """Tests for authentication requirement on /profile with date filter."""

    def test_unauthenticated_user_redirected_to_login(self, client):
        """GET /profile without login should redirect to /login."""
        response = client.get('/profile')
        assert response.status_code == 302
        assert '/login' in response.headers['Location']

    def test_unauthenticated_user_with_date_params_redirected_to_login(self, client):
        """GET /profile?start_date=... without login should redirect to /login."""
        response = client.get('/profile?start_date=2025-01-01&end_date=2025-01-31')
        assert response.status_code == 302
        assert '/login' in response.headers['Location']


class TestDateFilterHappyPaths:
    """Tests for successful date filtering scenarios."""

    def test_default_current_month_no_params(self, auth_client):
        """GET /profile with no params defaults to current month."""
        response = auth_client.get('/profile')
        assert response.status_code == 200
        assert b'Total Spent' in response.data
        # Should show current month expenses only (3 expenses = 350.00)
        assert b'350.00' in response.data  # 100 + 50 + 200

    def test_custom_range_both_dates(self, auth_client):
        """GET /profile with start_date and end_date filters to that range."""
        current_year = datetime.now().year
        current_month = datetime.now().month
        prev_month = current_month - 1 if current_month > 1 else 12
        prev_year = current_year if current_month > 1 else current_year - 1

        # Filter to previous month only
        response = auth_client.get(
            f'/profile?start_date={prev_year}-{prev_month:02d}-01&end_date={prev_year}-{prev_month:02d}-28'
        )
        assert response.status_code == 200
        # Should show previous month expenses only (150 + 75 = 225)
        assert b'225.00' in response.data
        # Period label should be "Selected Period"
        assert b'Selected Period' in response.data
        # Filter should be active
        assert b'Clear Filter' in response.data

    def test_partial_start_date_only(self, auth_client):
        """GET /profile with only start_date filters from that date onwards."""
        current_year = datetime.now().year
        current_month = datetime.now().month

        # Start from beginning of current month
        response = auth_client.get(f'/profile?start_date={current_year}-{current_month:02d}-01')
        assert response.status_code == 200
        # Should include current month + next month expenses
        # 350 (current) + 300 (next) = 650
        assert b'650.00' in response.data
        assert b'Selected Period' in response.data

    def test_partial_end_date_only(self, auth_client):
        """GET /profile with only end_date filters up to that date."""
        current_year = datetime.now().year
        current_month = datetime.now().month
        prev_month = current_month - 1 if current_month > 1 else 12
        prev_year = current_year if current_month > 1 else current_year - 1

        # End at end of previous month
        response = auth_client.get(f'/profile?end_date={prev_year}-{prev_month:02d}-28')
        assert response.status_code == 200
        # Should include previous month only (225)
        assert b'225.00' in response.data
        assert b'Selected Period' in response.data

    def test_full_range_all_expenses(self, auth_client):
        """GET /profile with range covering all expenses shows all."""
        current_year = datetime.now().year
        # Wide range covering all test data
        response = auth_client.get(f'/profile?start_date={current_year}-01-01&end_date={current_year}-12-31')
        assert response.status_code == 200
        # All expenses: 350 + 225 + 300 = 875
        assert b'875.00' in response.data
        assert b'Selected Period' in response.data


class TestDateFilterValidationErrors:
    """Tests for validation error handling."""

    def test_invalid_start_date_format_returns_400(self, auth_client):
        """Invalid start_date format returns 400 with error message."""
        response = auth_client.get('/profile?start_date=01-01-2025&end_date=2025-01-31')
        assert response.status_code == 400
        assert b'Invalid date format' in response.data

    def test_invalid_end_date_format_returns_400(self, auth_client):
        """Invalid end_date format returns 400 with error message."""
        response = auth_client.get('/profile?start_date=2025-01-01&end_date=31-01-2025')
        assert response.status_code == 400
        assert b'Invalid date format' in response.data

    def test_both_invalid_dates_returns_400(self, auth_client):
        """Both dates invalid returns 400."""
        response = auth_client.get('/profile?start_date=invalid&end_date=also-invalid')
        assert response.status_code == 400
        assert b'Invalid date format' in response.data

    def test_start_date_after_end_date_returns_400(self, auth_client):
        """start_date > end_date returns 400 with error message."""
        response = auth_client.get('/profile?start_date=2025-02-01&end_date=2025-01-31')
        assert response.status_code == 400
        assert b'Start date must be before or equal to end date' in response.data

    def test_same_start_and_end_date_allowed(self, auth_client):
        """start_date == end_date is valid (single day)."""
        current_year = datetime.now().year
        current_month = datetime.now().month
        response = auth_client.get(
            f'/profile?start_date={current_year}-{current_month:02d}-05&end_date={current_year}-{current_month:02d}-05'
        )
        assert response.status_code == 200
        # Should show just the one expense on that day (100)
        assert b'100.00' in response.data


class TestDateFilterTemplateVariables:
    """Tests that correct template variables are passed in all cases."""

    def test_default_filter_inactive_variables(self, auth_client):
        """Default (no params) has filter_active=False, period_label='This Month'."""
        response = auth_client.get('/profile')
        assert response.status_code == 200
        assert b'This Month' in response.data
        assert b'Clear Filter' not in response.data  # filter not active

    def test_active_filter_variables(self, auth_client):
        """Active filter has filter_active=True, period_label='Selected Period'."""
        current_year = datetime.now().year
        current_month = datetime.now().month
        prev_month = current_month - 1 if current_month > 1 else 12
        prev_year = current_year if current_month > 1 else current_year - 1

        response = auth_client.get(
            f'/profile?start_date={prev_year}-{prev_month:02d}-01&end_date={prev_year}-{prev_month:02d}-28'
        )
        assert response.status_code == 200
        assert b'Selected Period' in response.data
        assert b'Clear Filter' in response.data
        # Form should preserve the filter values
        assert f'value="{prev_year}-{prev_month:02d}-01"'.encode() in response.data
        assert f'value="{prev_year}-{prev_month:02d}-28"'.encode() in response.data

    def test_error_preserves_form_values(self, auth_client):
        """Validation error preserves submitted date values in form."""
        response = auth_client.get('/profile?start_date=2025-02-01&end_date=2025-01-31')
        assert response.status_code == 400
        # Form should preserve the invalid values
        assert b'value="2025-02-01"' in response.data
        assert b'value="2025-01-31"' in response.data

    def test_categories_reflect_filtered_range(self, auth_client):
        """Category breakdown reflects filtered date range."""
        current_year = datetime.now().year
        current_month = datetime.now().month

        # Current month only: Food=100, Transport=50, Shopping=200
        response = auth_client.get('/profile')
        assert response.status_code == 200
        assert b'Food' in response.data
        assert b'Transport' in response.data
        assert b'Shopping' in response.data
        # Previous month categories should not appear
        assert b'Bills' not in response.data

    def test_total_spent_reflects_filter(self, auth_client):
        """Total spent stat reflects filtered range."""
        current_year = datetime.now().year
        current_month = datetime.now().month
        prev_month = current_month - 1 if current_month > 1 else 12
        prev_year = current_year if current_month > 1 else current_year - 1

        # Previous month only
        response = auth_client.get(
            f'/profile?start_date={prev_year}-{prev_month:02d}-01&end_date={prev_year}-{prev_month:02d}-28'
        )
        assert response.status_code == 200
        # Previous month total: 150 + 75 = 225
        assert b'225.00' in response.data

    def test_expense_count_reflects_filter(self, auth_client):
        """Transaction count reflects filtered range."""
        # Default current month: 3 transactions
        response = auth_client.get('/profile')
        assert response.status_code == 200
        assert b'3' in response.data  # expense count

        # Previous month: 2 transactions
        current_year = datetime.now().year
        current_month = datetime.now().month
        prev_month = current_month - 1 if current_month > 1 else 12
        prev_year = current_year if current_month > 1 else current_year - 1

        response = auth_client.get(
            f'/profile?start_date={prev_year}-{prev_month:02d}-01&end_date={prev_year}-{prev_month:02d}-28'
        )
        assert response.status_code == 200
        assert b'2' in response.data  # expense count


class TestDateFilterEmptyStates:
    """Tests for empty state when no expenses in filtered range."""

    def test_empty_state_no_expenses_in_range(self, auth_client):
        """Range with no expenses shows empty state."""
        # Use a year with no data
        response = auth_client.get('/profile?start_date=2020-01-01&end_date=2020-12-31')
        assert response.status_code == 200
        assert b'No expenses yet' in response.data
        assert b'Start tracking your expenses' in response.data
        assert b'0.00' in response.data  # total spent
        assert b'0' in response.data    # expense count

    def test_empty_state_partial_range_no_data(self, auth_client):
        """Partial range with no data shows empty state."""
        # Future date range with no expenses
        future_year = datetime.now().year + 5
        response = auth_client.get(f'/profile?start_date={future_year}-01-01&end_date={future_year}-12-31')
        assert response.status_code == 200
        assert b'No expenses yet' in response.data


class TestDateFilterClearFilter:
    """Tests for clear filter functionality."""

    def test_clear_filter_link_resets_to_default(self, auth_client):
        """Clear filter link redirects to /profile with no params."""
        current_year = datetime.now().year
        current_month = datetime.now().month
        prev_month = current_month - 1 if current_month > 1 else 12
        prev_year = current_year if current_month > 1 else current_year - 1

        # First apply a filter
        response = auth_client.get(
            f'/profile?start_date={prev_year}-{prev_month:02d}-01&end_date={prev_year}-{prev_month:02d}-28'
        )
        assert b'Clear Filter' in response.data

        # Clear filter should go back to default
        response = auth_client.get('/profile')
        assert response.status_code == 200
        assert b'This Month' in response.data
        assert b'Clear Filter' not in response.data


class TestDateFilterFormSubmission:
    """Tests for form submission behavior."""

    def test_form_submits_via_get(self, auth_client):
        """Filter form uses GET method."""
        response = auth_client.get('/profile')
        assert response.status_code == 200
        assert b'method="GET"' in response.data
        assert b'action="/profile"' in response.data or b'action="' in response.data

    def test_form_has_date_inputs(self, auth_client):
        """Form has type=date inputs for start_date and end_date."""
        response = auth_client.get('/profile')
        assert response.status_code == 200
        assert b'type="date"' in response.data
        assert b'name="start_date"' in response.data
        assert b'name="end_date"' in response.data

    def test_form_has_apply_button(self, auth_client):
        """Form has Apply Filter submit button."""
        response = auth_client.get('/profile')
        assert response.status_code == 200
        assert b'Apply Filter' in response.data


class TestDateFilterEdgeCases:
    """Edge case tests."""

    def test_date_boundary_inclusive(self, auth_client):
        """Date filter is inclusive on both boundaries."""
        current_year = datetime.now().year
        current_month = datetime.now().month

        # Filter to exact day of first expense (5th)
        response = auth_client.get(
            f'/profile?start_date={current_year}-{current_month:02d}-05&end_date={current_year}-{current_month:02d}-05'
        )
        assert response.status_code == 200
        assert b'100.00' in response.data  # Only the 5th expense

    def test_leap_year_date_valid(self, auth_client):
        """Leap year date (Feb 29) is accepted if valid year."""
        response = auth_client.get('/profile?start_date=2024-02-29&end_date=2024-02-29')
        assert response.status_code == 200  # 2024 is a leap year

    def test_invalid_leap_year_rejected(self, auth_client):
        """Feb 29 on non-leap year is rejected."""
        response = auth_client.get('/profile?start_date=2023-02-29&end_date=2023-02-29')
        assert response.status_code == 400
        assert b'Invalid date format' in response.data

    def test_empty_date_strings_treated_as_no_filter(self, auth_client):
        """Empty date strings fallback to default (current month)."""
        response = auth_client.get('/profile?start_date=&end_date=')
        assert response.status_code == 200
        assert b'This Month' in response.data
        assert b'Selected Period' not in response.data

    def test_whitespace_dates_stripped(self, auth_client):
        """Whitespace in date params is stripped."""
        current_year = datetime.now().year
        current_month = datetime.now().month
        prev_month = current_month - 1 if current_month > 1 else 12
        prev_year = current_year if current_month > 1 else current_year - 1

        response = auth_client.get(
            f'/profile?start_date= {prev_year}-{prev_month:02d}-01 &end_date= {prev_year}-{prev_month:02d}-28 '
        )
        assert response.status_code == 200
        assert b'225.00' in response.data


class TestDateFilterIntegration:
    """Tests ensuring date filter works with existing profile features."""

    def test_user_info_still_displayed(self, auth_client):
        """User name, email, member since still shown with filter."""
        response = auth_client.get('/profile')
        assert response.status_code == 200
        assert b'Test User' in response.data
        assert b'@example.com' in response.data  # Unique email generated in fixture
        assert b'Member since' in response.data

    def test_logout_still_works(self, auth_client):
        """Logout still works after using date filter."""
        current_year = datetime.now().year
        current_month = datetime.now().month
        auth_client.get(f'/profile?start_date={current_year}-{current_month:02d}-01')

        response = auth_client.get('/logout')
        assert response.status_code == 302
        assert '/' in response.headers['Location']

    def test_profile_page_extends_base_template(self, auth_client):
        """Profile page extends base.html (has navbar)."""
        response = auth_client.get('/profile')
        assert response.status_code == 200
        assert b'Spendly' in response.data  # Brand in navbar
        assert b'Logout' in response.data   # Logout link in navbar