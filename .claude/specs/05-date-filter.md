---
# Spec: Date Filter for Profile Page

## Overview
Add a date range filter to the profile page that allows logged-in users to filter their expense summary and category breakdown by a custom date range (start date to end date). This builds on Step 4 (profile page) and enables users to analyze their spending over specific periods (e.g., last month, last quarter, custom range).

## Depends on
- **Step 1** (01-database-setup): Database schema with `expenses` table including `date` column
- **Step 2** (02-registration): User registration and session management
- **Step 3** (03-logout): Logout functionality
- **Step 4** (04-profile-page): Profile page with spending summary and category breakdown

## Routes
- `GET /profile` — Existing route, enhanced with optional query parameters `?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD` — **logged-in only**

## Database changes
No database changes required. Uses existing `expenses` table with `date` column (TEXT format YYYY-MM-DD).

## Templates
- **Modify:** `templates/profile.html` — Add date filter form above summary stats; update stats/category breakdown to reflect filtered data; add clear filter link when filter is active
- **Modify:** `templates/base.html` — No changes needed (navbar already handles auth state)

## Files to change
1. `app.py` — Update `/profile` route to accept and validate `start_date` and `end_date` query parameters; modify SQL queries to filter by date range when provided
2. `templates/profile.html` — Add date filter form, display filtered results, show "clear filter" link

## Files to create
None.

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
- Validate date format (YYYY-MM-DD) and ensure start_date <= end_date
- Default to current month if no dates provided (maintain existing behavior)
- Preserve filter values in form after submit

## Definition of done
- [ ] `/profile` accepts `start_date` and `end_date` query parameters
- [ ] Invalid date format returns 400 with error message
- [ ] start_date > end_date returns 400 with error message
- [ ] Date filter form appears above summary stats on profile page
- [ ] Form uses `<input type="date">` for both fields
- [ ] Form submits via GET to `/profile` preserving current filter
- [ ] Summary stats (total spent, transaction count, this month) reflect filtered range
- [ ] Category breakdown reflects filtered range
- [ ] "This Month" stat label updates to "Selected Period" when filter is active
- [ ] Clear filter link appears when filter is active, resets to default (current month)
- [ ] Empty state shows when no expenses in filtered range
- [ ] Page uses CSS variables from design system
- [ ] Template extends `base.html`
- [ ] No console errors when loading the page