---
# Spec: Add Expense

## Overview
Implement the `/expenses/add` route to allow logged-in users to add new expenses to their tracker. This is Step 6 of the Spendly tutorial progression, building on the authentication foundation (Steps 1-3), profile page (Step 4), and date filtering (Step 5). The add expense page provides a form with fields for amount, category, date, and optional description.

## Depends on
- **Step 1** (01-database-setup): Database schema with `users` and `expenses` tables
- **Step 2** (02-registration): User registration and session management
- **Step 3** (03-logout): Logout functionality to clear session
- **Step 4** (04-profile-page): Profile page showing expense summary
- **Step 5** (05-date-filter): Date filter on profile page (for navigation consistency)

## Routes
- `GET /expenses/add` — Display the add expense form — **logged-in only**
- `POST /expenses/add` — Process the form submission and create new expense — **logged-in only**

## Database changes
No database changes required. Uses existing:
- `expenses` table: id, user_id, amount, category, date, description, created_at
- `users` table: id (for foreign key reference)

## Templates
- **Create:** `templates/add_expense.html` — Add expense form page extending `base.html`
- **Modify:** `templates/profile.html` — Update "Add your first expense" button/link to point to `/expenses/add` (already references `url_for('add_expense')`)
- **Modify:** `templates/base.html` — No changes needed (navbar already handles auth state)

## Files to change
1. `app.py` — Implement `GET /expenses/add` and `POST /expenses/add` routes with authentication check and form handling
2. `templates/add_expense.html` — New template (created)
3. `templates/profile.html` — Already references `url_for('add_expense')` (line 96)

## Files to create
1. `templates/add_expense.html` — Add expense form template

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — use raw SQLite with parameterised queries
- Passwords hashed with werkzeug (already done in registration)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Check `session.get("user_id")` for authentication; redirect to `/login` if not logged in
- Use `get_db()` from `database.db` for database connections
- Close database connections after use
- Validate form inputs: amount (required, positive number), category (required, from predefined list), date (required, valid YYYY-MM-DD, not in future), description (optional, max 500 chars)
- Pre-fill date field with today's date as default
- Show form validation errors inline
- On successful POST, redirect to `/profile` with success flash message (or just redirect)
- CSRF protection: generate token for GET, validate on POST

## Definition of done
- [ ] `GET /expenses/add` returns 200 for logged-in users with form displayed
- [ ] `GET /expenses/add` redirects to `/login` for non-logged-in users
- [ ] Form includes: amount (number input), category (select dropdown), date (date input defaulting to today), description (textarea)
- [ ] Categories dropdown includes: Food, Transport, Bills, Health, Entertainment, Shopping, Other
- [ ] `POST /expenses/add` validates all required fields
- [ ] Invalid amount (non-positive, non-numeric) shows error
- [ ] Invalid category shows error
- [ ] Invalid date format or future date shows error
- [ ] Description over 500 chars shows error
- [ ] Valid submission inserts expense into database with correct user_id
- [ ] Successful submission redirects to `/profile`
- [ ] New expense appears in profile page summary and category breakdown
- [ ] Page uses CSS variables from design system
- [ ] Template extends `base.html`
- [ ] No console errors when loading the page