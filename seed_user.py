#!/usr/bin/env python3
"""
Seed a realistic random Indian user into the Spendly database.
"""

import os
import sys
import random
from datetime import datetime
from werkzeug.security import generate_password_hash

# Add the database module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "database"))
from db import get_db

# Realistic Indian first names (across regions)
INDIAN_FIRST_NAMES = [
    # North Indian
    "Aarav", "Aditya", "Arjun", "Dev", "Ishaan", "Kabir", "Krish", "Rohan", "Vivaan", "Yuvraj",
    "Ananya", "Diya", "Ishita", "Kiara", "Myra", "Navya", "Prisha", "Saanvi", "Tara", "Zara",
    # South Indian
    "Advik", "Arnav", "Dhruv", "Karthik", "Nikhil", "Pranav", "Rohit", "Siddharth", "Vikram", "Varun",
    "Aishwarya", "Anjali", "Deepika", "Kavya", "Meera", "Nithya", "Priya", "Shreya", "Swathi", "Vidya",
    # East Indian
    "Abhijit", "Anirban", "Debashish", "Indranil", "Kaushik", "Mainak", "Ritwik", "Sourav", "Subham", "Tamal",
    "Anindita", "Debjani", "Ipsita", "Madhurima", "Nandini", "Poulomi", "Rituparna", "Shruti", "Susmita", "Tiyasha",
    # West Indian
    "Amit", "Chintan", "Dhruvin", "Harsh", "Jay", "Ketan", "Meet", "Nirav", "Parth", "Yash",
    "Ayesha", "Bhavya", "Disha", "Isha", "Kinjal", "Mitali", "Neha", "Pooja", "Riya", "Tanya",
]

# Realistic Indian last names (across regions)
INDIAN_LAST_NAMES = [
    # Common pan-Indian
    "Sharma", "Verma", "Gupta", "Singh", "Kumar", "Patel", "Shah", "Mehta", "Jain", "Agarwal",
    # South Indian
    "Reddy", "Nair", "Iyer", "Menon", "Pillai", "Rao", "Naidu", "Gowda", "Shetty", "Hegde",
    # Bengali
    "Banerjee", "Chatterjee", "Mukherjee", "Ghosh", "Das", "Roy", "Bose", "Sengupta", "Pal", "Mitra",
    # Gujarati/Marwari
    "Shah", "Mehta", "Patel", "Desai", "Modi", "Sanghvi", "Doshi", "Vora", "Gandhi", "Ambani",
    # Punjabi
    "Singh", "Kaur", "Bajwa", "Dhillon", "Gill", "Sidhu", "Brar", "Mann", "Aulakh", "Sandhu",
]

# Email domains
EMAIL_DOMAINS = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "protonmail.com"]


def generate_indian_name():
    """Generate a realistic Indian first + last name."""
    first = random.choice(INDIAN_FIRST_NAMES)
    last = random.choice(INDIAN_LAST_NAMES)
    return f"{first} {last}"


def generate_email_from_name(name):
    """Generate email from name with random 2-3 digit suffix."""
    # Convert name to lowercase, replace spaces with dots, remove special chars
    base = name.lower().replace(" ", ".").replace("'", "").replace("-", "")
    suffix = random.randint(10, 999)
    domain = random.choice(EMAIL_DOMAINS)
    return f"{base}{suffix}@{domain}"


def email_exists(conn, email):
    """Check if email already exists in users table."""
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM users WHERE email = ?", (email,))
    return cursor.fetchone() is not None


def seed_random_user():
    """Generate and insert a unique random Indian user."""
    conn = get_db()

    try:
        # Generate unique user
        max_attempts = 100
        for attempt in range(max_attempts):
            name = generate_indian_name()
            email = generate_email_from_name(name)

            if not email_exists(conn, email):
                # Found unique email
                password_hash = generate_password_hash("password123")
                created_at = datetime.now().isoformat()

                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO users (name, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
                    (name, email, password_hash, created_at)
                )
                user_id = cursor.lastrowid
                conn.commit()

                print(f"✅ User created successfully!")
                print(f"   ID: {user_id}")
                print(f"   Name: {name}")
                print(f"   Email: {email}")
                print(f"   Password: password123 (hashed)")
                return

        print(f"❌ Failed to generate unique email after {max_attempts} attempts")
        sys.exit(1)

    finally:
        conn.close()


if __name__ == "__main__":
    seed_random_user()