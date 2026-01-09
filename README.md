# Variant Analytics Dashboard v2.0

A complete redesign of the Variant Analytics Dashboard with enhanced UI/UX, staged data refresh system, and improved theming.

## Features

### 🎨 Design System
- **Full Screen Layout**: No margins on all pages
- **Adaptive Theme**: Dark (default) and Light modes
  - Dark: #0F172A background, #F1F5F9 text, #14B8A6 accent
  - Light: #F8FAFC background, #0F172A text, #0F766E accent
- **Loading Animation**: Variant logo fades from light to dark

### 🔄 Data Refresh System
Two-button staged refresh:
- **Refresh BQ**: BigQuery → Staging cache (dashboards unaffected)
- **Refresh GCS**: Staging → Active cache (dashboards update)
- **Auto-refresh**: Daily at 10:15 UTC (background process)

### 📊 Dashboard Features
- **Landing Page**: Table-based dashboard list with refresh timestamps
- **Dashboard Pages**: 
  - Header: Back (left), Title (center), Menu (right)
  - Refresh section with timestamps
  - Active/Inactive tabs
  - Pivot tables with sparklines (AG Grid)
  - Charts with disabled scroll zoom
- **Login Page**: Centered form with demo credentials
- **Admin Panel**: Full-screen modal with users and dashboard access tables

### 👥 User Management
- **Roles**: Admin (all access) and Read Only (selected dashboards)
- **Admin Panel**: Manage users, edit permissions, view dashboard access

## Project Structure

```
variant_dashboard/
├── app/
│   ├── __init__.py
│   ├── main.py              # Entry point
│   ├── config.py            # Configuration
│   ├── theme.py             # Theme system
│   ├── auth.py              # Authentication
│   ├── bigquery_client.py   # Data layer
│   ├── colors.py            # Color utilities
│   ├── filters.py           # Filter components
│   ├── pivots.py            # Pivot tables
│   ├── charts.py            # Chart components
│   ├── admin_panel.py       # Admin panel
│   ├── assets/
│   │   └── variant_logo.png
│   └── pages/
│       ├── __init__.py
│       ├── login.py
│       ├── landing.py
│       └── icarus_historical.py
└── requirements.txt
```

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variable for GCS bucket (optional)
export GCS_CACHE_BUCKET=your-bucket-name

# Run the app
streamlit run app/main.py
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GCS_CACHE_BUCKET` | GCS bucket for caching | No |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to service account JSON | Yes |

## Default Users

| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | Admin |
| viewer | viewer123 | Read Only |

## Key Design Decisions

1. **Refresh System**: Two-stage (BQ → Staging → Active) prevents dashboard interruption during data refresh
2. **Theme Adaptation**: Logo inverts automatically for dark/light mode
3. **Chart Zoom**: Disabled on page scroll, only available in fullscreen mode
4. **Pivot Tables**: Auto-fit columns with proper alignment (headers center, App/Plan/Metric left, dates right)
5. **Admin Panel**: Shows only Read Only users in dashboard access table (admins have all access by default)

## License

Proprietary - Variant Group
