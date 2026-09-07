---
# Spec: Edit Expense

## Overview
Implement the `/expenses/<int:id>/edit` route to let logged-in users edit one of their own existing expenses. This is Step 7 of the Spendly tutorial progression, building directly on the add-expense form (Step 6). The edit page pre-fills the same amount / category / date / description form with the expense's current values, applies identical validation, and updates the record in place. It also establishes the ownership check pattern (`expense.user_id == session user`) that the future delete step will reuse.

## Depends on
- **Step 1** (01-database-setup): Database schema with `users` and `expenses` tables
- **Step 2** (02-registration): User registration and session management
- **Step 4** (04-profile-page): Profile page showing expense summary
- **Step 6** (06-add-expense): The add-expense form, validation, and CSRF pattern this step mirrors

## Routes
- `GET /expenses/<int:id>/edit` — Display the edit form pre-filled with the expense's current values — **logged-in only**
- `POST /expenses/<int:id>/edit` — Validate the submitted fields and update the expense — **logged-in only**

## Database changes
No database changes required. Uses the existing `expenses` table (id, user_id, amount, category, date, description, created_at) with an `UPDATE` statement.

## Templates
- **Create:** `templates/edit_expense.html` — Edit expense form page extending `base.html`, modeled on `add_expense.html` but with the form action pointing to `{{ url_for('edit_expense', id=expense['id']) }}` and the submit button reading "Save Changes"
- **Modify:** No template changes required. The profile page currently shows only category breakdowns, not individual expense rows, so there is no edit link to wire up yet.

## Files to change
1. `app.py` — Replace the `GET /expenses/<int:id>/edit` placeholder (currently returns a stub string) with GET and POST handlers that include authentication, ownership, and validation logic.

## Files to create
1. `templates/edit_expense.html` — Edit expense form template pre-filled with the existing expense values.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — use raw SQLite with parameterised queries
- Passwords hashed with werkzeug (already done in registration)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Check `session.get("user_id")` for authentication; redirect to `/login` if not logged in
- Use `get_db()` from `database.db` for database connections; always close connections after use
- **Ownership check:** Fetch the expense with both `id = ?` and `user_id = ?` so a logged-in user can only edit their own expenses. If no matching row is found, return 404.
- Update the placeholder route to `@app.route("/expenses/<int:id>/edit", methods=["GET", "POST"])`
- CSRF protection mirrors Step 6: generate a token on GET and store it in the session (e.g. `session["edit_expense_csrf"]`); validate on POST with `secrets.compare_digest` (skipped when `app.testing`)
- Reuse `EXPENSE_CATEGORIES` from `app.py` for the category dropdown
- Validate fields identically to Step 6: amount (required, finite positive number), category (required, from `EXPENSE_CATEGORIES`), date (required, valid YYYY-MM-DD, not in the future), description (optional, max 500 chars)
- On validation error: re-render the form at `400`, keeping the user's submitted values and the currently-edited expense pre-filled
- On success: `UPDATE expenses SET amount = ?, category = ?, date = ?, description = ? WHERE id = ?` and redirect to `/profile`
- Do not add an expense-list view in this step; the edit page is reachable by URL until a list of expenses is built

## Definition of done
- [ ] The placeholder stub "Edit expense — coming in Step 8" is removed
- [ ] `GET /expenses/<int:id>/edit` redirects to `/login` for non-logged-in users
- [ ] `GET /expenses/<int:id>/edit` returns 200 for a logged-in user editing their own expense, with the form showing the expense's current amount, category, date, and description pre-filled
- [ ] `GET /expenses/<int:id>/edit` returns 404 when the expense does not exist
- [ ] `GET /expenses/<int:id>/edit` returns 404 when the expense belongs to a different user
- [ ] Categories dropdown includes: Food, Transport, Bills, Health, Entertainment, Shopping, Other
- [ ] `POST /expenses/<int:id>/edit` rejects a bad or missing CSRF token
- [ ] Invalid amount, category, date (including future dates), or over-length description show inline errors and keep the submitted values
- [ ] A valid submission updates the record in the database (verified by the expense's new values appearing on the profile page)
- [ ] A valid submission redirects to `/profile`
- [ ] Editing one user's expense does not alter another user's expenses
- [ ] Page uses CSS variables from the design system
- [ ] Template extends `base.html`
- [ ] No console errors when loading the page