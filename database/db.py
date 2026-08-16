import sqlite3
import os
from datetime import datetime
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "spendly.db")


def get_db():
    """Return a SQLite connection with row_factory and foreign keys enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create all tables using CREATE TABLE IF NOT EXISTS."""
    conn = get_db()
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # Expenses table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL,
            description TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()


def seed_db():
    """Insert sample data for development."""
    conn = get_db()
    cursor = conn.cursor()

    # Check if already seeded
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return

    # Seed demo user (password: demo123)
    demo_password_hash = generate_password_hash("demo123")
    cursor.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Demo User", "demo@spendly.com", demo_password_hash)
    )
    demo_user_id = cursor.lastrowid

    # Current month for dates
    current_year = datetime.now().year
    current_month = datetime.now().month

    # Seed 8 sample expenses across categories
    categories = [
        "Food",
        "Transport",
        "Bills",
        "Health",
        "Entertainment",
        "Shopping",
        "Other",
    ]

    expenses = [
        (demo_user_id, 45.50, "Food", f"{current_year}-{current_month:02d}-02", "Groceries at supermarket"),
        (demo_user_id, 15.00, "Transport", f"{current_year}-{current_month:02d}-03", "Bus pass"),
        (demo_user_id, 89.99, "Shopping", f"{current_year}-{current_month:02d}-05", "New headphones"),
        (demo_user_id, 120.00, "Bills", f"{current_year}-{current_month:02d}-08", "Electricity bill"),
        (demo_user_id, 35.00, "Health", f"{current_year}-{current_month:02d}-10", "Pharmacy"),
        (demo_user_id, 29.99, "Entertainment", f"{current_year}-{current_month:02d}-12", "Netflix subscription"),
        (demo_user_id, 22.50, "Food", f"{current_year}-{current_month:02d}-15", "Lunch with friends"),
        (demo_user_id, 18.00, "Other", f"{current_year}-{current_month:02d}-18", "Miscellaneous"),
    ]

    cursor.executemany(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        expenses
    )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    seed_db()
    print("Database initialized and seeded successfully!")