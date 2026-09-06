import os
import secrets
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash
from database.db import init_db, seed_db, get_db

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        # Generate simple CSRF token for form
        csrf_token = secrets.token_hex(16)
        return render_template("register.html", csrf_token=csrf_token)

    # POST - handle registration
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    # Validation
    error = None
    if not name:
        error = "Full name is required"
    elif not email or "@" not in email:
        error = "Valid email is required"
    elif len(password) < 8:
        error = "Password must be at least 8 characters"

    if error:
        return render_template("register.html", error=error, csrf_token=secrets.token_hex(16)), 400

    # Hash password
    password_hash = generate_password_hash(password)

    # Insert user
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, password_hash)
        )
        conn.commit()
        user_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        conn.close()
        return render_template("register.html", error="Email already registered", csrf_token=secrets.token_hex(16)), 400
    finally:
        conn.close()

    # Set session and redirect
    session["user_id"] = user_id
    return redirect(url_for("profile"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    # POST - handle login
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    error = None
    if not email or "@" not in email:
        error = "Valid email is required"
    elif not password:
        error = "Password is required"

    if error:
        return render_template("login.html", error=error), 400

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, password_hash FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
    finally:
        conn.close()

    if not user:
        return render_template("login.html", error="Invalid email or password"), 401

    from werkzeug.security import check_password_hash
    if not check_password_hash(user["password_hash"], password):
        return render_template("login.html", error="Invalid email or password"), 401

    session["user_id"] = user["id"]
    return redirect(url_for("profile"))


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))


@app.route("/profile")
def profile():
    # Check authentication
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    conn = get_db()
    cursor = conn.cursor()

    # Get user info first (needed for error cases)
    cursor.execute("SELECT id, name, email, created_at FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        conn.close()
        session.clear()
        return redirect(url_for("login"))

    # Get and validate date filter parameters
    from datetime import datetime
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()

    filter_active = False
    period_label = "This Month"
    date_filter_sql = ""
    date_filter_params = []

    # Default to current month if no filter provided
    current_month = datetime.now().strftime("%Y-%m")

    if start_date or end_date:
        # Validate date format
        try:
            if start_date:
                datetime.strptime(start_date, "%Y-%m-%d")
            if end_date:
                datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            conn.close()
            return render_template(
                "profile.html",
                user=user,
                total_spent=0,
                expense_count=0,
                categories=[],
                this_month=0,
                filter_active=False,
                start_date=start_date,
                end_date=end_date,
                period_label="This Month",
                error="Invalid date format. Use YYYY-MM-DD."
            ), 400

        # Validate start_date <= end_date
        if start_date and end_date and start_date > end_date:
            conn.close()
            return render_template(
                "profile.html",
                user=user,
                total_spent=0,
                expense_count=0,
                categories=[],
                this_month=0,
                filter_active=False,
                start_date=start_date,
                end_date=end_date,
                period_label="This Month",
                error="Start date must be before or equal to end date."
            ), 400

        filter_active = True
        period_label = "Selected Period"

        # Build WHERE clause for date filtering
        if start_date and end_date:
            date_filter_sql = " AND date BETWEEN ? AND ?"
            date_filter_params = [start_date, end_date]
        elif start_date:
            date_filter_sql = " AND date >= ?"
            date_filter_params = [start_date]
        elif end_date:
            date_filter_sql = " AND date <= ?"
            date_filter_params = [end_date]
    else:
        # Default to current month
        date_filter_sql = " AND date LIKE ?"
        date_filter_params = [f"{current_month}%"]

    # Base WHERE clause for user expenses
    base_where = "WHERE user_id = ?"
    base_params = (user_id,)

    try:
        # Get total spending (filtered)
        cursor.execute(
            f"SELECT COALESCE(SUM(amount), 0) FROM expenses {base_where} {date_filter_sql}",
            base_params + tuple(date_filter_params)
        )
        total_spent = cursor.fetchone()[0]

        # Get transaction count (filtered)
        cursor.execute(
            f"SELECT COUNT(*) FROM expenses {base_where} {date_filter_sql}",
            base_params + tuple(date_filter_params)
        )
        expense_count = cursor.fetchone()[0]

        # Get category breakdown (filtered)
        cursor.execute(
            f"SELECT category, SUM(amount) as total FROM expenses {base_where} {date_filter_sql} GROUP BY category ORDER BY total DESC",
            base_params + tuple(date_filter_params)
        )
        categories_raw = cursor.fetchall()

        # Calculate percentages for each category
        categories = []
        for cat in categories_raw:
            percentage = (cat["total"] / total_spent * 100) if total_spent > 0 else 0
            categories.append({
                "category": cat["category"],
                "total": cat["total"],
                "percentage": round(percentage)
            })

        # Get period spending (filtered - same as total_spent when filter active)
        cursor.execute(
            f"SELECT COALESCE(SUM(amount), 0) FROM expenses {base_where} {date_filter_sql}",
            base_params + tuple(date_filter_params)
        )
        period_total = cursor.fetchone()[0]

    finally:
        conn.close()

    return render_template(
        "profile.html",
        user=user,
        total_spent=total_spent,
        expense_count=expense_count,
        categories=categories,
        this_month=period_total,
        filter_active=filter_active,
        start_date=start_date,
        end_date=end_date,
        period_label=period_label
    )


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    init_db()
    seed_db()
    app.run(debug=True, port=5001)
