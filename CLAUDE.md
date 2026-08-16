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
| `/logout` | GET | 🔲 Placeholder | — |
| `/profile` | GET | 🔲 Placeholder | — |
| `/expenses/add` | GET/POST | 🔲 Placeholder | — |
| `/expenses/<id>/edit` | GET/POST | 🔲 Placeholder | — |
| `/expenses/<id>/delete` | POST | 🔲 Placeholder | — |

## Database Schema (to implement in `database/db.py`)

Based on the forms and placeholder routes, the schema will need:
- **users** table (id, name, email, password_hash, created_at)
- **expenses** table (id, user_id, category, amount, date, description, created_at)
- **categories** table (id, name, icon, color) — optional, for predefined categories

## CSS Design System

The stylesheet (`static/css/style.css`) uses CSS custom properties for:
- Colors: `--ink`, `--paper`, `--accent` (green), `--accent-2` (gold), `--danger`
- Typography: `--font-display` (DM Serif Display), `--font-body` (DM Sans)
- Spacing/radius: `--radius-sm/md/lg`, `--max-width`, `--auth-width`

All components use these variables — no hardcoded values.

## Next Steps (Tutorial Progression)

1. **Step 1**: Implement `database/db.py` with SQLite connection, table creation, seeding
2. **Step 2**: Add auth logic to `/register` and `/login` routes (hash passwords, sessions)
3. **Step 3**: Implement `/logout`
4. **Step 4**: Build `/profile` page
5. **Steps 7-9**: CRUD for expenses (add, edit, delete)

## Notes for Future Work

- Password hashing: use `werkzeug.security.generate_password_hash` / `check_password_hash`
- Sessions: Flask's built-in `session` (requires `app.secret_key`)
- Database: Use `sqlite3.Row` row_factory and enable foreign keys via `PRAGMA foreign_keys=ON`
- The `database/__init__.py` exists but is empty — `db.py` is the main module