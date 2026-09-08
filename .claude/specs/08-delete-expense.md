---
# Spec: Delete Expense

## Overview
Implement the `/expenses/<int:id>/delete` route so logged-in users can delete one of their own expenses. This is Step 9, the final piece of the expense CRUD (add → edit → delete). The profile page already lists the user's individual transactions with an "Edit" link (built in Step 7), so this step adds a "Delete" button next to each expense and a POST handler that removes the matching record. Like edit, it reuses the ownership check pattern so a user can only ever delete their own expenses — never another user's.

## Depends on
- **Step 1** (01-database-setup): Database schema with `users` and `expenses` tables
- **Step 2** (02-registration): User registration and session management
- **Step 4** (04-profile-page): Profile page that lists the user's expenses
- **Step 6** (06-add-expense): The CSRF-token pattern this step mirrors for a state-changing POST
- **Step 7** (07-edit-expense): The ownership check (`expense.user_id == session user`) and the visible transaction list on the profile page

## Routes
- `POST /expenses/<int:id>/delete` — Delete the expense with the given id if it belongs to the logged-in user — **logged-in only**

## Database changes
No database changes required. Uses the existing `expenses` table (id, user_id, amount, category, date, description, created_at) with a parameterised `DELETE` statement.

## Templates
- **Create:** None. Deletion is triggered directly from the profile page via a small inline form — no separate confirmation page is needed.
- **Modify:** `templates/profile.html` — add a "Delete" button/form next to the existing "Edit" link in each expense row (the `expense-side` block). The delete control must be a `<form method="POST">` pointing at `{{ url_for('delete_expense', id=expense['id']) }}`, including a hidden `csrf_token` field.

## Files to change
1. `app.py` — Replace the `POST /expenses/<int:id>/delete` placeholder (currently a stub string) with a POST handler that authenticates the user, validates a CSRF token, deletes the record only if it belongs to the user, and redirects to `/profile`.
2. `templates/profile.html` — Add a delete form/button to each expense row.

## Files to create
No new files.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — use raw SQLite with parameterised queries
- Passwords hashed with werkzeug (already done in registration)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Check `session.get("user_id")` for authentication; redirect to `/login` if not logged in
- Use `get_db()` from `database.db` for database connections; always close connections after use
- Change the route decorator to `@app.route("/expenses/<int:id>/delete", methods=["POST"])` (matches the CLAUDE.md roadmap; deletion is a state-changing action and must not be a GET)
- **Ownership check:** delete with both `WHERE id = ? AND user_id = ?` so a user can only delete their own expenses. If no row is deleted, treat it as not-found: return `404`.
- **CSRF protection** mirrors Steps 6 and 7: the profile page must supply a valid CSRF token for the delete form, and the handler must validate it with `secrets.compare_digest` (skipped when `app.testing`). Because the profile page renders the token, store it in the session when rendering `/profile` (e.g. a `delete_expense_csrf` token) and read the same value in the delete handler. Do not silently delete on a missing/bad token — return `400` (or re-render with an error).
- On success: `DELETE FROM expenses WHERE id = ? AND user_id = ?`, commit, then redirect to `/profile`
- Keep the delete control visually distinct from the Edit link (the design system's `--danger` color / `.btn-danger` styling) so a destructive action is not styled like a normal link
- No confirmation page is required; keep the delete action inline on the profile list

## Definition of done
- [ ] The placeholder stub "Delete expense — coming in Step 9" is removed
- [ ] `POST /expenses/<int:id>/delete` redirects to `/login` for non-logged-in users
- [ ] A GET request to `/expenses/<id>/delete` is not accepted (route only handles POST)
- [ ] `POST /expenses/<int:id>/delete` returns 404 when the expense does not exist
- [ ] `POST /expenses/<int:id>/delete` returns 404 when the expense belongs to a different user
- [ ] `POST /expenses/<int:id>/delete` rejects a missing or invalid CSRF token without deleting anything
- [ ] A valid, authenticated delete removes the expense from the database (verified by the row no longer appearing on the profile page and the transaction/stats counts decreasing)
- [ ] A successful delete redirects to `/profile`
- [ ] Deleting one user's expense never affects another user's expenses
- [ ] Each expense row on the profile page shows a "Delete" control alongside "Edit"
- [ ] The delete control posts to `{{ url_for('delete_expense', id=expense['id']) }}` and includes a hidden CSRF token
- [ ] Page uses CSS variables from the design system (no hardcoded hex values)
- [ ] Template extends `base.html`
- [ ] No console errors when loading the profile page
