# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Spendly** — A Flask-based personal finance tracker (expense tracking app) built as a learning exercise. The project follows a step-by-step tutorial structure where students implement features incrementally.

## Architecture

- **Framework**: Flask 3.1.3
- **Database**: SQLite (to be implemented in `database/db.py`)
- **Templating**: Jinja2 with base template inheritance
- **Frontend**: Vanilla HTML/CSS/JS (no framework)
- **Auth**: Session-based (to be implemented)

### Key Files

| File | Purpose |
|------|---------|
| `app.py` | Main Flask app with routes (landing, register, login + placeholders) |
| `database/db.py` | **Student exercise** — implements `get_db()`, `init_db()`, `seed_db()` |
| `templates/base.html` | Base layout with navbar, footer, blocks for title/content/scripts |
| `templates/landing.html` | Marketing page with hero, features, CTA |
| `templates/login.html` | Sign in form (POST to `/login`) |
| `templates/register.html` | Registration form (POST to `/register`) |
| `static/css/style.css` | Complete design system with CSS variables |
| `static/js/main.js` | Placeholder for future JS features |

## Development Commands

```bash
# Activate venv
source .venv/bin/activate

# Run development server (port 5001)
python app.py

# Run tests
pytest -v

# Run single test file
pytest tests/test_specific.py -v
```

## Route Map (from `app.py`)

| Route | Method | Status | Template |
|-------|--------|--------|----------|
| `/` | GET | ✅ Done | `landing.html` |
| `/register` | GET/POST | ✅ Done | `register.html` |
| `/login` | GET/POST | ✅ Done | `login.html` |
| `/logout` | GET | ✅ Done | — |
| `/profile` | GET | ✅ Done | `profile.html` |
| `/expenses/add` | GET/POST | ✅ Done | `add_expense.html` |
| `/expenses/<id>/edit` | GET/POST | ✅ Done | `edit_expense.html` |
| `/expenses/<id>/delete` | POST | ✅ Done | — |
| `/terms` | GET | ✅ Done | `terms.html` |
| `/privacy` | GET | ✅ Done | `privacy.html` |

## Database Schema (implemented in `database/db.py`)

- **users** table (id, name, email, password_hash, created_at)
- **expenses** table (id, user_id, category, amount, date, description, created_at) — `user_id` has `ON DELETE CASCADE`
- No `categories` table — the predefined category list lives as `EXPENSE_CATEGORIES` in `app.py`

## CSS Design System

The stylesheet (`static/css/style.css`) uses CSS custom properties for:
- Colors: `--ink`, `--paper`, `--accent` (green), `--accent-2` (gold), `--danger`
- Typography: `--font-display` (DM Serif Display), `--font-body` (DM Sans)
- Spacing/radius: `--radius-sm/md/lg`, `--max-width`, `--auth-width`

All components use these variables — no hardcoded values.

## Tutorial Progression (Complete ✅)

1. **Step 1** — `database/db.py`: SQLite connection, table creation, seeding
2. **Step 2** — Auth logic for `/register` and `/login` (hash passwords, sessions)
3. **Step 3** — `/logout`
4. **Step 4** — `/profile` page
5. **Step 5** — Date filtering on `/profile`
6. **Step 6** — Add expense (`/expenses/add`)
7. **Step 7** — Edit expense (`/expenses/<id>/edit`)
8. **Step 8** — Delete expense (`/expenses/<id>/delete`)

The project is feature-complete: full expense CRUD, session auth, CSRF protection, and a profile dashboard with category breakdowns and date filtering.

## Notes for Future Work

- Password hashing: use `werkzeug.security.generate_password_hash` / `check_password_hash`
- Sessions: Flask's built-in `session` (requires `app.secret_key`)
- Database: Use `sqlite3.Row` row_factory and enable foreign keys via `PRAGMA foreign_keys=ON`
- The `database/__init__.py` exists but is empty — `db.py` is the main module