# Variant Analytics Dashboard v2.0

Enterprise-grade analytics dashboard for subscription, LTV, ARPU, churn, and cohort analytics.

---

## ⚠️ First Time Setup (Important!)

After downloading/cloning, run the setup script to create hidden config files:

```bash
cd variant_dashboard
chmod +x setup.sh
./setup.sh
```

---

## 🚀 Quick Start

### Local Development
```bash
# Setup
cd variant_dashboard
chmod +x setup.sh && ./setup.sh

# Install
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set credentials
export GOOGLE_APPLICATION_CREDENTIALS="path/to/credentials.json"
export GCS_CACHE_BUCKET="your-cache-bucket-name"

# Run
streamlit run app/main.py
```

---

## 🔐 Default Login Credentials

| Role | Username | Password |
|------|----------|----------|
| Admin | admin | admin123 |
| Viewer | viewer | viewer123 |

⚠️ Change these in production!

---

## ⚡ Data Loading & Two-Stage Caching

### How It Works

Data refresh is split into two stages for zero-downtime updates:

```
┌─────────────────────────────────────────────────────────────────┐
│                    🔄 REFRESH BQ (Stage 1)                      │
├─────────────────────────────────────────────────────────────────┤
│  1. Query BigQuery → Load ALL data                              │
│  2. Save to STAGING cache (GCS)                                 │
│  3. Dashboards continue using OLD data                          │
│  4. No interruption to users!                                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    🔥 REFRESH GCS (Stage 2)                     │
├─────────────────────────────────────────────────────────────────┤
│  1. Copy STAGING → ACTIVE cache                                 │
│  2. Dashboards now use FRESH data                               │
│  3. Instant switch!                                             │
└─────────────────────────────────────────────────────────────────┘
```

### Auto-Refresh
- **Time**: 10:15 UTC daily
- **Behavior**: Runs both stages automatically in background

---

## 📋 Features

### Authentication & Access Control
- Username/password authentication
- Admin and Read Only roles
- Dashboard-level access control
- Full Admin Panel for user management

### ICARUS - Plan (Historical) Dashboard
- **Active/Inactive tabs** for plan filtering
- **Collapsible filters:** Date Range, Billing Cycle, Cohort, Plan Groups, Metrics
- **Pivot Tables:** Regular & Crystal Ball with sparklines
- **Charts:** 10 metrics × 2 versions = 20 line charts

### Design System
- Dark mode (default) / Light mode toggle
- Full-screen layout (0 margins)
- Universal App-based color scheme
- Inter font family

---

## 🛠 Tech Stack

- **Frontend:** Streamlit
- **Charts:** Plotly
- **Tables:** AG Grid with sparklines
- **Data Processing:** PyArrow
- **Data Source:** BigQuery
- **Cache Storage:** Google Cloud Storage (GCS)
- **Deployment:** Cloud Run (Docker)

---

## 📁 Project Structure

```
variant_dashboard/
├── app/
│   ├── __init__.py
│   ├── main.py              # Entry point & routing
│   ├── config.py            # Configuration & constants
│   ├── bigquery_client.py   # Data loading with two-stage caching
│   ├── theme.py             # Dark/Light theme with logo
│   ├── auth.py              # Authentication
│   ├── colors.py            # App color scheme
│   ├── filters.py           # Filter components (checkbox style)
│   ├── charts.py            # Chart builders (zoom disabled)
│   ├── pivots.py            # Pivot table with AG Grid
│   ├── admin_panel.py       # Admin panel modal
│   ├── assets/
│   │   └── variant_logo.png # Place your logo here
│   └── pages/
│       ├── __init__.py
│       ├── login.py
│       ├── landing.py
│       └── icarus_historical.py
├── cloudbuild.yaml          # CI/CD config
├── Dockerfile
├── requirements.txt
├── setup.sh
├── gitignore.txt            # Run setup.sh to rename
├── dockerignore.txt
├── gcloudignore.txt
├── DEPLOYMENT.md
└── README.md
```

---

## ⚙️ Configuration

### Environment Variables
| Variable | Description | Required |
|----------|-------------|----------|
| `GCS_CACHE_BUCKET` | GCS bucket for caching | No (but recommended) |
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

## 🔑 User Roles

| Role | Access | Can Manage Users |
|------|--------|------------------|
| Admin | All dashboards | Yes |
| Read Only | Selected dashboards | No |

---

## 📝 License

Proprietary - Variant Group
