# Spec: Logout

## Overview
Implement user logout functionality for Spendly. This step adds a `/logout` route that clears the user's session, ending their authenticated state and redirecting them to the landing page. This is a simple but essential auth feature that completes the basic authentication flow (register → login → logout).

## Depends on
- **Step 1: Database Setup** — requires `users` table and working database
- **Step 2: Registration** — requires session management (`session['user_id']`) to be working

## Routes
- `GET /logout` — clear session, redirect to `/` — logged-in access only

## Database changes
No database changes. Uses existing `users` table and session.

## Templates
- **Create:** None
- **Modify:** None (no template needed for logout — it's a redirect-only action)

## Files to change
- `app.py` — implement GET `/logout` handler to clear session and redirect

## Files to create
- None

## New dependencies
No new dependencies. Uses Flask's built-in `session`.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only — no string formatting in SQL
- Passwords hashed with werkzeug
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Session cleared via `session.clear()` or `session.pop('user_id', None)`
- Redirect to landing page (`/`) after logout
- Logout should be accessible via GET (link in navbar) or POST (form submission)

## Definition of done
- [ ] `GET /logout` clears `session['user_id']`
- [ ] `GET /logout` redirects to `/` (landing page)
- [ ] After logout, accessing `/profile` (or any protected route) redirects to login
- [ ] Navbar shows "Sign in" and "Get started" links after logout (not user-specific links)
- [ ] No errors when logging out without an active session