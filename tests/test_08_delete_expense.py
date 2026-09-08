"""
Tests for the Delete Expense feature (Step 8).

Covers:
- Happy path: valid POST deletes the expense and redirects to profile
- Authentication guard: unauthenticated POST redirects to login
- Method guard: GET is not accepted (405)
- Ownership: cannot delete another user's expense (404)
- Not found: deleting a nonexistent expense returns 404
- CSRF: missing or invalid token is rejected without deleting
- Side effects: the expense row and profile counts reflect the deletion
- Profile UI: each expense row shows a Delete form/control alongside Edit
"""

import pytest
from datetime import datetime
from werkzeug.security import generate_password_hash
import uuid

# =============================================================================
# Helpers
# =============================================================================


def create_user(conn, cursor, name="Test User"):
    """Insert a test user and return their id."""
    unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    password_hash = generate_password_hash("testpass123")
    cursor.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        (name, unique_email, password_hash),
    )
    user_id = cursor.lastrowid
    conn.commit()
    return user_id, unique_email


def create_expense(conn, cursor, user_id, amount=100.0, category="Food"):
    """Insert an expense for a user and return its id."""
    cursor.execute(
        "INSERT INTO expenses (user_id, amount, category, date, description) "
        "VALUES (?, ?, ?, ?, ?)",
        (
            user_id,
            amount,
            category,
            datetime.now().strftime("%Y-%m-%d"),
            "Test expense",
        ),
    )
    expense_id = cursor.lastrowid
    conn.commit()
    return expense_id


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def app():
    """Create a test Flask app with real database."""
    from app import app as flask_app
    from database.db import init_db

    flask_app.config.update(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret-key",
            "WTF_CSRF_ENABLED": False,
        }
    )

    with flask_app.app_context():
        init_db()
        yield flask_app


@pytest.fixture
def app_no_testing():
    """A Flask app with TESTING disabled so CSRF validation is exercised."""
    from app import app as flask_app
    from database.db import init_db

    flask_app.config.update(
        {
            "TESTING": False,
            "SECRET_KEY": "test-secret-key",
            "WTF_CSRF_ENABLED": False,
        }
    )

    with flask_app.app_context():
        init_db()
        yield flask_app


@pytest.fixture
def client(app):
    """Test client for making requests."""
    return app.test_client()


@pytest.fixture
def auth_client(app, client):
    """A test client with a logged-in user and a fresh expense."""
    from database.db import get_db

    conn = get_db()
    cursor = conn.cursor()
    user_id, email = create_user(conn, cursor)
    expense_id = create_expense(conn, cursor, user_id)

    client.post("/login", data={"email": email, "password": "testpass123"})

    yield client, user_id, expense_id

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


class TestDeleteExpenseAuthGuard:
    """Tests for authentication and method requirements."""

    def test_post_unauthenticated_redirects_to_login(self, client, app):
        """POST delete without login should redirect to /login."""
        from database.db import get_db

        conn = get_db()
        cursor = conn.cursor()
        user_id, _ = create_user(conn, cursor)
        expense_id = create_expense(conn, cursor, user_id)
        conn.close()

        response = client.post(f"/expenses/{expense_id}/delete", data={})
        assert response.status_code == 302
        assert (
            "/login" in response.headers["Location"]
        ), "Expected redirect to /login for unauthenticated POST"

        # Cleanup
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()

    def test_get_returns_method_not_allowed(self, auth_client):
        """GET /expenses/<id>/delete should be rejected (405)."""
        client, _, expense_id = auth_client
        response = client.get(f"/expenses/{expense_id}/delete")
        assert (
            response.status_code == 405
        ), "Expected 405 Method Not Allowed for GET on delete route"


class TestDeleteExpenseNotFound:
    """Tests for nonexistent or non-owned expenses."""

    def test_delete_nonexistent_returns_404(self, auth_client):
        """Deleting an expense that does not exist should return 404."""
        client, _, _ = auth_client
        response = client.post("/expenses/999999/delete", data={})
        assert response.status_code == 404, "Expected 404 for nonexistent expense"

    def test_delete_another_users_expense_returns_404(self, app, client):
        """Deleting another user's expense should return 404 and not delete it."""
        from database.db import get_db

        conn = get_db()
        cursor = conn.cursor()
        owner_id, owner_email = create_user(conn, cursor, name="Owner User")
        other_id, other_email = create_user(conn, cursor, name="Other User")
        expense_id = create_expense(conn, cursor, owner_id)
        conn.close()

        # Log in as the OTHER user (not the owner)
        response = client.post(
            "/login", data={"email": other_email, "password": "testpass123"}
        )
        assert response.status_code == 302

        # Attempt to delete the owner's expense
        response = client.post(f"/expenses/{expense_id}/delete", data={})
        assert (
            response.status_code == 404
        ), "Expected 404 when user tries to delete another user’s expense"

        # Owner's expense must still exist
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM expenses WHERE id = ?", (expense_id,))
        assert (
            cursor.fetchone()[0] == 1
        ), "Expense owned by another user must not be deleted"
        conn.close()

        # Cleanup
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        cursor.execute("DELETE FROM users WHERE id IN (?, ?)", (owner_id, other_id))
        conn.commit()
        conn.close()


class TestDeleteExpenseCsrf:
    """Tests for CSRF protection on the delete route."""

    def test_missing_csrf_token_rejected(self, app_no_testing):
        """POST without a CSRF token should be rejected without deleting."""
        from database.db import get_db

        conn = get_db()
        cursor = conn.cursor()
        user_id, email = create_user(conn, cursor)
        expense_id = create_expense(conn, cursor, user_id)
        conn.close()

        client = app_no_testing.test_client()
        client.post("/login", data={"email": email, "password": "testpass123"})

        response = client.post(f"/expenses/{expense_id}/delete", data={})
        assert response.status_code == 400, "Expected 400 for missing CSRF token"

        # Expense must still exist
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM expenses WHERE id = ?", (expense_id,))
        assert (
            cursor.fetchone()[0] == 1
        ), "Expense must not be deleted when CSRF token is missing"
        conn.close()

        # Cleanup
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()

    def test_invalid_csrf_token_rejected(self, app_no_testing):
        """POST with a wrong CSRF token should be rejected without deleting."""
        from database.db import get_db

        conn = get_db()
        cursor = conn.cursor()
        user_id, email = create_user(conn, cursor)
        expense_id = create_expense(conn, cursor, user_id)
        conn.close()

        client = app_no_testing.test_client()
        client.post("/login", data={"email": email, "password": "testpass123"})

        response = client.post(
            f"/expenses/{expense_id}/delete", data={"csrf_token": "totally-wrong-token"}
        )
        assert response.status_code == 400, "Expected 400 for invalid CSRF token"

        # Expense must still exist
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM expenses WHERE id = ?", (expense_id,))
        assert (
            cursor.fetchone()[0] == 1
        ), "Expense must not be deleted when CSRF token is invalid"
        conn.close()

        # Cleanup
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()


class TestDeleteExpenseHappyPath:
    """Tests for a successful delete."""

    def test_successful_delete_removes_expense(self, auth_client):
        """A valid delete should remove the expense from the database."""
        client, user_id, expense_id = auth_client
        response = client.post(f"/expenses/{expense_id}/delete", data={})
        assert response.status_code == 302
        assert (
            "/profile" in response.headers["Location"]
        ), "Expected redirect to /profile after successful delete"

        from database.db import get_db

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM expenses WHERE id = ?", (expense_id,))
        assert cursor.fetchone()[0] == 0, "Expense should be deleted from database"
        conn.close()

    def test_delete_updates_profile_counts(self, auth_client):
        """After deleting, the profile transaction count should decrease."""
        client, user_id, expense_id = auth_client

        # Count before
        from database.db import get_db

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM expenses WHERE user_id = ?", (user_id,))
        before = cursor.fetchone()[0]
        conn.close()

        client.post(f"/expenses/{expense_id}/delete", data={})

        # Count after
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM expenses WHERE user_id = ?", (user_id,))
        after = cursor.fetchone()[0]
        conn.close()

        assert (
            after == before - 1
        ), "Transaction count should decrease by 1 after delete"

    def test_deleting_other_expenses_unaffected(self, auth_client):
        """Deleting one expense must not affect the user's other expenses."""
        from database.db import get_db

        client, user_id, expense_id = auth_client

        # Create a second expense that should survive
        conn = get_db()
        cursor = conn.cursor()
        other_id = create_expense(conn, cursor, user_id, amount=50.0, category="Bills")
        conn.close()

        client.post(f"/expenses/{expense_id}/delete", data={})

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM expenses WHERE id = ?", (other_id,))
        assert (
            cursor.fetchone()[0] == 1
        ), "The other expense must remain after deleting one"
        conn.close()


class TestDeleteProfileUi:
    """Tests for the delete control on the profile page."""

    def test_profile_has_delete_control_per_expense(self, auth_client):
        """Each expense row on the profile page should include a Delete control."""
        client, user_id, expense_id = auth_client
        response = client.get("/profile")
        assert response.status_code == 200

        # The delete form posts to the delete URL for this expense
        expected_url = f"/expenses/{expense_id}/delete"
        assert (
            expected_url.encode() in response.data
        ), "Expected a delete form action pointing at the delete URL"

        # A hidden CSRF token field should be present
        assert (
            b"csrf_token" in response.data
        ), "Expected a hidden csrf_token field in the delete form"

    def test_profile_has_edit_control_too(self, auth_client):
        """Each expense row should still include the Edit link alongside Delete."""
        client, user_id, expense_id = auth_client
        response = client.get("/profile")
        assert response.status_code == 200
        assert (
            f"/expenses/{expense_id}/edit".encode() in response.data
        ), "Expected the Edit link to remain alongside Delete"
