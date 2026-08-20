# Implementation Plan - 04 Profile Page Redesign

Implement the fully designed profile page for Spendly according to the specification in `specs/04-profile-page-redesign.md`.

## Goal Description
This feature implements a dedicated, modern profile page (`/profile`) in Spendly to establish a complete UI layout with clean component hierarchy. As specified in Step 04 of the Spendly roadmap, this step implements the full UI layout — user info card, summary stats row, transaction history table, and category breakdown — using hardcoded context data in `app.py` and pure CSS classes in `static/css/style.css` (no inline styles, no hardcoded hex values, no ORMs).

Key components:
1. **Authentication Guard**: Protect `/profile` so unauthenticated requests redirect to `/login`.
2. **Context Data in `app.py`**: Prepare hardcoded dictionaries and lists for user info, summary statistics, recent transactions, and category breakdown.
3. **Template Structure in `templates/profile.html`**:
   - Extends `base.html`.
   - **User Info Card**: Display initials avatar, user's name, email, and member-since date.
   - **Summary Stats Row**: Display total spent, transaction count, and top spending category.
   - **Transaction History Table**: Clean tabular layout displaying recent transactions with date, description, category badge, and amount.
   - **Category Breakdown Section**: Visual list/progress rows showing per-category totals and percentages.
4. **Pure CSS Styling in `static/css/style.css`**:
   - Define reusable, responsive profile layout classes (`.profile-container`, `.profile-card`, `.profile-avatar`, `.profile-stat-card`, etc.).
   - Strictly utilize CSS custom properties (`var(--ink)`, `var(--accent)`, `var(--paper-card)`, `var(--radius-md)`, etc.) without any inline styles or hardcoded hex values.
5. **Test Suite in `test_app.py`**:
   - Add integration tests verifying route protection, HTTP 200 response for logged-in users, rendering of user card, summary stats, transaction table, and category breakdown.

---

## User Review Required

> [!NOTE]
> Per Step 04 specifications, all data passed to `profile.html` will be hardcoded Python data structures in `app.py` to decouple frontend design validation from backend database integration (which follows in Step 05).

> [!IMPORTANT]
> `profile.html` will contain **zero inline styles** and **no hardcoded hex colors**, strictly adhering to Spendly's CSS variable token system and class-based design in `static/css/style.css`.

---

## Open Questions
None. All layout sections, badges, data structures, and styling rules are defined in `specs/04-profile-page-redesign.md` and `.agents/skills/spendly-frontend-ui/SKILL.md`.

---

## Proposed Changes

### Backend Application

#### [MODIFY] [app.py](file:///home/jiggra/expense-tracker/app.py)

- Update `@app.route("/profile")` with `@login_required`.
- Construct hardcoded context data structures:
  - `user`: `{"name": "Demo User", "email": "demo@spendly.com", "initials": "DU", "member_since": "March 2026"}`
  - `stats`: `{"total_spent": 16050.00, "transaction_count": 8, "top_category": "Bills"}`
  - `recent_transactions`: list of dictionaries with `date`, `description`, `category`, `amount`, and `badge_class`.
  - `category_breakdown`: list of category items with `name`, `amount`, and `percentage`.
- Pass these data structures to `render_template("profile.html", ...)`.

```python
@app.route("/profile")
@login_required
def profile():
    """Renders the redesigned profile page with user details and financial statistics."""
    user = {
        "name": "Demo User",
        "email": "demo@spendly.com",
        "initials": "DU",
        "member_since": "March 2026"
    }

    stats = {
        "total_spent": 16050.00,
        "transaction_count": 8,
        "top_category": "Bills"
    }

    recent_transactions = [
        {"date": "2026-03-20", "description": "Dinner with friends", "category": "Food", "badge_class": "badge-food", "amount": 650.00},
        {"date": "2026-03-18", "description": "Bookstore purchase", "category": "Other", "badge_class": "badge-other", "amount": 950.00},
        {"date": "2026-03-16", "description": "New running shoes", "category": "Shopping", "badge_class": "badge-shopping", "amount": 2500.00},
        {"date": "2026-03-14", "description": "Movie tickets & snacks", "category": "Entertainment", "badge_class": "badge-entertainment", "amount": 1200.00},
        {"date": "2026-03-12", "description": "Metro card reload", "category": "Transport", "badge_class": "badge-transport", "amount": 1800.00},
        {"date": "2026-03-10", "description": "Medicines & checkup", "category": "Health", "badge_class": "badge-health", "amount": 2050.00},
        {"date": "2026-03-05", "description": "Weekly groceries", "category": "Food", "badge_class": "badge-food", "amount": 3200.00},
        {"date": "2026-03-01", "description": "Rent & electricity", "category": "Bills", "badge_class": "badge-bills", "amount": 4500.00}
    ]

    category_breakdown = [
        {"category": "Bills", "amount": 4500.00, "percentage": 28, "badge_class": "badge-bills"},
        {"category": "Food", "amount": 3850.00, "percentage": 24, "badge_class": "badge-food"},
        {"category": "Shopping", "amount": 2500.00, "percentage": 16, "badge_class": "badge-shopping"},
        {"category": "Health", "amount": 2050.00, "percentage": 13, "badge_class": "badge-health"},
        {"category": "Transport", "amount": 1800.00, "percentage": 11, "badge_class": "badge-transport"},
        {"category": "Entertainment", "amount": 1200.00, "percentage": 8, "badge_class": "badge-entertainment"}
    ]

    return render_template(
        "profile.html",
        user=user,
        stats=stats,
        recent_transactions=recent_transactions,
        category_breakdown=category_breakdown
    )
```

---

### Stylesheet & Design System

#### [MODIFY] [static/css/style.css](file:///home/jiggra/expense-tracker/static/css/style.css)

- Add CSS variables for badge colors if missing (e.g. `--badge-shopping`, `--badge-entertainment`).
- Add profile page component styles:
  - `.profile-container`
  - `.profile-header`, `.profile-header-title`, `.profile-header-sub`
  - `.profile-user-card`, `.profile-avatar`, `.profile-user-details`, `.profile-meta-item`
  - `.profile-stats-grid`, `.profile-stat-card`, `.profile-stat-val`, `.profile-stat-lbl`
  - `.profile-content-grid` (responsive layout for transaction history and category breakdown)
  - `.profile-section-card`, `.profile-section-title`
  - Category breakdown bars: `.category-bar-bg`, `.category-bar-fill`
  - Responsive media queries for mobile/tablet screens.

---

### Templates

#### [MODIFY] [templates/profile.html](file:///home/jiggra/expense-tracker/templates/profile.html)

- Completely replace previous inline styles with clean, semantic markup extending `base.html`:
  - User profile header and avatar card.
  - Summary metrics grid (3 stat cards).
  - Transaction history table with formatted currency and category badges.
  - Category breakdown list with progress bars.

```html
{% extends "base.html" %}

{% block title %}My Profile — Spendly{% endblock %}

{% block content %}
<section class="profile-section">
    <div class="profile-container">
        <!-- Page Header -->
        <div class="profile-header">
            <h1 class="profile-header-title">My Profile</h1>
            <p class="profile-header-sub">Manage your account information and view your spending summary</p>
        </div>

        <!-- User Information Card -->
        <div class="profile-user-card">
            <div class="profile-avatar">{{ user.initials }}</div>
            <div class="profile-user-details">
                <h2 class="profile-user-name">{{ user.name }}</h2>
                <div class="profile-user-meta">
                    <div class="profile-meta-item">
                        <span class="profile-meta-label">Email:</span>
                        <span class="profile-meta-value">{{ user.email }}</span>
                    </div>
                    <div class="profile-meta-item">
                        <span class="profile-meta-label">Member since:</span>
                        <span class="profile-meta-value">{{ user.member_since }}</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Summary Stats Row -->
        <div class="profile-stats-grid">
            <div class="profile-stat-card">
                <div class="profile-stat-label">Total Spent</div>
                <div class="profile-stat-value accent-stat">₹{{ "{:,.2f}".format(stats.total_spent) }}</div>
            </div>
            <div class="profile-stat-card">
                <div class="profile-stat-label">Transactions</div>
                <div class="profile-stat-value">{{ stats.transaction_count }}</div>
            </div>
            <div class="profile-stat-card">
                <div class="profile-stat-label">Top Category</div>
                <div class="profile-stat-value">{{ stats.top_category }}</div>
            </div>
        </div>

        <!-- Two Column Content Grid -->
        <div class="profile-content-grid">
            <!-- Transaction History -->
            <div class="profile-card">
                <h3 class="profile-card-title">Recent Transactions</h3>
                <div class="table-responsive">
                    <table class="expense-table">
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Description</th>
                                <th>Category</th>
                                <th class="text-right">Amount</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for tx in recent_transactions %}
                            <tr>
                                <td class="table-date">{{ tx.date }}</td>
                                <td class="table-desc">{{ tx.description }}</td>
                                <td><span class="badge {{ tx.badge_class }}">{{ tx.category }}</span></td>
                                <td class="table-amount text-right">₹{{ "{:,.2f}".format(tx.amount) }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Category Breakdown -->
            <div class="profile-card">
                <h3 class="profile-card-title">Spending by Category</h3>
                <div class="profile-breakdown-list">
                    {% for cat in category_breakdown %}
                    <div class="category-item">
                        <div class="category-info">
                            <span class="category-name">{{ cat.category }}</span>
                            <span class="category-amt">₹{{ "{:,.2f}".format(cat.amount) }} ({{ cat.percentage }}%)</span>
                        </div>
                        <div class="category-bar-bg">
                            <div class="category-bar-fill" style="width: {{ cat.percentage }}%;"></div>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>
</section>
{% endblock %}
```

---

### Test Suite

#### [MODIFY] [test_app.py](file:///home/jiggra/expense-tracker/test_app.py)

Add test cases for Profile Page Redesign:
- `test_profile_requires_login`: Unauthenticated request to `/profile` redirects to `/login`.
- `test_profile_page_authenticated`: Authenticated request returns HTTP 200 and renders user card ("Demo User", "demo@spendly.com", "Member since").
- `test_profile_summary_stats`: Verifies total spent, transaction count, and top category are present in HTML response.
- `test_profile_transaction_history_table`: Verifies recent transaction rows, category badges, and currency values are present.
- `test_profile_category_breakdown`: Verifies category names and percentage breakdowns are rendered.

---

## Verification Plan

### Automated Tests
Run pytest across the entire test suite and profile-specific tests:
```bash
.venv/bin/python -m pytest test_app.py -k "profile" -v
.venv/bin/python -m pytest -v
```

### Manual Verification
1. Start the Flask application: `.venv/bin/python app.py`.
2. Visit `http://127.0.0.1:5001/profile` when logged out → confirm redirect to `/login`.
3. Sign in using `demo@spendly.com` / `demo123`.
4. Navigate to `/profile` via the top navigation bar.
5. Verify visual design:
   - User initials avatar (`DU`) and user metadata card.
   - Three summary stat cards (`Total Spent`, `Transactions`, `Top Category`).
   - Recent transactions table with category badges.
   - Category breakdown list with progress bars.
   - Test responsive layout on mobile viewport (<768px).
