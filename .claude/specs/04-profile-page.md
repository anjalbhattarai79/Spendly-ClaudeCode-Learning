---
# Spec: Profile Page Design

## Overview
Implement the `/profile` route to display the logged-in user's profile information and spending summary. This is Step 4 of the Spendly tutorial progression, building on the authentication foundation (Steps 1-3). The profile page shows user details, account information, and a summary of their expenses with category breakdown.

## Depends on
- **Step 1** (01-database-setup): Database schema with `users` and `expenses` tables
- **Step 2** (02-registration): User registration and session management
- **Step 3** (03-logout): Logout functionality to clear session

## Routes
- `GET /profile` — Display user profile with spending summary — **logged-in only**

## Database changes
No database changes required. Uses existing:
- `users` table: id, name, email, created_at
- `expenses` table: user_id, amount, category, date, description

## Templates
- **Create:** `templates/profile.html` — User profile page extending `base.html`
- **Modify:** `templates/base.html` — Update navbar to show user-specific links when logged in (profile, logout) vs public links (login, register)

## Files to change
1. `app.py` — Implement `/profile` route with authentication check and expense queries
2. `templates/base.html` — Conditional navbar based on session state
3. `templates/profile.html` — New template (created)

## Files to create
1. `templates/profile.html` — Profile page template

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

## Definition of done
- [ ] `/profile` route returns 200 for logged-in users
- [ ] `/profile` redirects to `/login` for non-logged-in users
- [ ] Profile page displays: user name, email, member since date
- [ ] Profile page shows total spending (sum of all expenses)
- [ ] Profile page shows expense count
- [ ] Profile page shows category breakdown with amounts
- [ ] Navbar shows "Profile" and "Logout" when logged in
- [ ] Navbar shows "Sign in" and "Get started" when logged out
- [ ] Page uses CSS variables from design system
- [ ] Template extends `base.html`
- [ ] No console errors when loading the page