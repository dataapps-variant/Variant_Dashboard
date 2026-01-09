# Variant Analytics Dashboard v2.0

A complete redesign of the Variant Analytics Dashboard with enhanced UI/UX, staged data refresh system, and improved theming.

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables (optional for GCS caching)
export GCS_CACHE_BUCKET=your-bucket-name
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

# Run the app
streamlit run app/main.py
```

## 🔐 Default Login Credentials

| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | Admin (all access) |
| viewer | viewer123 | Read Only |

---

## 📋 Features Overview

### 🎨 Design System

#### Full Screen Layout
- **0 margins** on all pages
- No sidebar, maximized content area

#### Adaptive Theme
| Mode | Background | Text | Accent |
|------|------------|------|--------|
| Dark (default) | #0F172A | #F1F5F9 | #14B8A6 |
| Light | #F8FAFC | #0F172A | #0F766E |

- Logo automatically adapts to theme (inverts in dark mode)
- Toggle via ⋮ menu on any page

#### Loading Animation
- Variant logo fades from 10% → 100% opacity
- Centered, theme-aware
- Triggers on navigation and data loads

---

### 🔄 Data Refresh System

#### Two-Button Staged Refresh
| Button | Action | Effect on Dashboard |
|--------|--------|---------------------|
| 🔄 Refresh BQ | BigQuery → Staging cache | None (dashboards unaffected) |
| 📥 Refresh GCS | Staging → Active cache | Dashboards update |

#### Auto-Refresh
- **Time**: 10:15 UTC daily
- **Trigger**: First login after scheduled time
- **Behavior**: Background process, old cache shown while loading
- **Failure**: Continues with previous cache

#### Status Display
Each dashboard shows:
- Last BQ Refresh timestamp
- Last GCS Refresh timestamp
- Staging Ready indicator (if new data waiting)

---

### 📄 Pages

#### Login Page
- Variant "V" logo (centered)
- "VARIANT GROUP" title
- "Sign in to access your dashboards" subtitle
- Username, Password, Remember Me, Sign In
- Demo Credentials box
- Theme toggle in ⋮ menu

#### Landing Page
- Logo + "VARIANT GROUP" + "Welcome back, {username}"
- Dashboard table (not cards):
  - Dashboard Name (clickable for enabled)
  - Last Refresh BQ
  - Last Refresh GCS
- Disabled dashboards: same appearance, cursor: not-allowed
- Settings menu (⋮): Light Mode toggle, Admin Panel, User info, Logout

#### Dashboard Pages
- **Header**: [← Back] (left) | Title (center) | [⋮] (right)
- **Menu**: "Export full dashboard as PDF" only
- **Refresh Box**: Right-aligned with both buttons and timestamps
- **Tabs**: Active / Inactive
- **Filters**: Date range, BC, Cohort, Metrics, Plans
- **Pivot Tables**: AG Grid with sparklines, auto-fit columns
  - Alignment: Headers center, App/Plan/Metric left, Dates right
- **Charts**: 10 metrics × 2 versions = 20 charts
  - No section header
  - Scroll = page scroll (zoom disabled)
  - Zoom only in Fullscreen mode
  - Toolbar: Fullscreen, PDF Export, PNG Download

#### Admin Panel (Modal)
- Full screen modal (opens from ⋮ menu)
- Users Table: User Name, User ID, Password (masked), Role, Actions
- Dashboard Access Table: Dashboard Name, Read Only Users only
  - Note: "Admin users have access to all dashboards"
- Add New User (collapsible form):
  - User Name, User ID, Password
  - Role dropdown (Admin/Read Only)
  - Dashboard Access multi-select (hidden for Admin role)

---

## 📁 Project Structure

```
variant_dashboard/
├── app/
│   ├── __init__.py
│   ├── main.py              # Entry point
│   ├── config.py            # All configuration
│   ├── theme.py             # Theme system
│   ├── auth.py              # Authentication
│   ├── bigquery_client.py   # Data layer + caching
│   ├── colors.py            # Chart colors
│   ├── filters.py           # Filter components
│   ├── pivots.py            # AG Grid pivot tables
│   ├── charts.py            # Plotly charts
│   ├── admin_panel.py       # Admin panel modal
│   ├── assets/
│   │   └── variant_logo.png
│   └── pages/
│       ├── __init__.py
│       ├── login.py
│       ├── landing.py
│       └── icarus_historical.py
└── requirements.txt
```

---

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GCS_CACHE_BUCKET` | GCS bucket for caching | No |
| `GOOGLE_APPLICATION_CREDENTIALS` | Service account JSON path | Yes |

### config.py Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `CACHE_TTL` | 86400 (24h) | Cache time-to-live |
| `AUTO_REFRESH_HOUR` | 10 | Auto-refresh hour (UTC) |
| `AUTO_REFRESH_MINUTE` | 15 | Auto-refresh minute |

---

## 🎨 App Colors (14 Apps)

| App | Color | Hex |
|-----|-------|-----|
| AT | Orange | #F97316 |
| CL | Blue | #3B82F6 |
| CN | Green | #22C55E |
| CT-Non-JP | Teal | #14B8A6 |
| CT-JP | Pink | #EC4899 |
| CV | Purple | #A855F7 |
| DT | Amber | #F59E0B |
| EN | Lime | #84CC16 |
| FS | Red | #EF4444 |
| IQ | Indigo | #6366F1 |
| JF | Emerald | #10B981 |
| PD | Rose | #F43F5E |
| RL | Sky | #0EA5E9 |
| RT | Violet | #8B5CF6 |

---

## 📊 Chart Metrics (10)

1. Recent LTV ($)
2. Gross ARPU ($)
3. Net ARPU ($)
4. Subscriptions
5. Rebills
6. Churn (%)
7. Gross Retention (%)
8. Refund (%)
9. Net ARPU Retention (%)
10. Recent CAC ($)

Each metric has Regular and Crystal Ball versions = 20 charts total.

---

## 🔒 User Roles

| Role | Access | Can Manage Users |
|------|--------|------------------|
| Admin | All dashboards | Yes |
| Read Only | Selected dashboards | No |

---

## 📝 License

Proprietary - Variant Group
