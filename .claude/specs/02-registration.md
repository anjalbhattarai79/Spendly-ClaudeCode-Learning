# Spec: Registration

## Overview
Implement user registration functionality for Spendly. This step adds auth logic to the existing `/register` route — handling form submission, validating input, hashing passwords with werkzeug, creating user records in the database, and establishing a session. This is the first authentication feature and enables all subsequent logged-in functionality (profile, expense CRUD).

## Depends on
- **Step 1: Database Setup** — requires `users` table, `get_db()`, `init_db()`, `seed_db()` working

## Routes
- `POST /register` — process registration form, create user, start session — public access
- `GET /register` — already exists, renders registration form — public access

## Database changes
No new tables or columns. Uses existing `users` table schema from Step 1:
- `id` (INTEGER PK)
- `name` (TEXT NOT NULL)
- `email` (TEXT UNIQUE NOT NULL)
- `password_hash` (TEXT NOT NULL)
- `created_at` (TEXT DEFAULT datetime('now'))

## Templates
- **Modify:** `templates/register.html` — add CSRF token field to form, ensure error display works
- **Create:** None (template already exists from Step 1)

## Files to change
- `app.py` — implement POST `/register` handler, add session config, import werkzeug security
- `templates/register.html` — add CSRF token hidden input to form

## Files to create
- None

## New dependencies
No new dependencies. Uses:
- `werkzeug.security.generate_password_hash` / `check_password_hash` (already installed)
- `flask.session` (built-in)
- `secrets` (stdlib) for secret key generation

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only — no string formatting in SQL
- Passwords hashed with `werkzeug.security.generate_password_hash`
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Set `app.secret_key` from environment variable or generate secure random
- Enable Flask sessions (`session` object)
- Validate: name not empty, email format, password min 8 chars, email uniqueness
- On successful registration: hash password, insert user, set `session['user_id']`, redirect to `/profile` (placeholder)
- On validation error: re-render `register.html` with error message in `auth-error` div
- On duplicate email: catch integrity error, show user-friendly error

## Definition of done
- [ ] `app.secret_key` is configured (from env or secure random)
- [ ] `GET /register` renders the registration form correctly
- [ ] `POST /register` with valid data:
    - Creates user in database with hashed password
    - Sets `session['user_id']` to new user's ID
    - Redirects to `/profile` (shows "Profile page — coming in Step 4")
- [ ] `POST /register` with invalid data shows appropriate error:
    - Empty name → "Full name is required"
    - Invalid email format → "Valid email is required"
    - Password < 8 chars → "Password must be at least 8 characters"
    - Duplicate email → "Email already registered"
- [ ] Form includes CSRF token (hidden input with name `csrf_token`)
- [ ] No SQL injection vulnerabilities (all queries parameterized)
- [ ] Passwords are hashed (verify in DB: `password_hash` column contains werkzeug hash, not plaintext)
- [ ] Session persists across requests (user stays logged in)