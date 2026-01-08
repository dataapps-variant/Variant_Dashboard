# Variant Analytics Dashboard

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

## ⚡ Data Loading & Caching

### How It Works

Data is loaded from BigQuery **ONCE PER DAY** and stored in Google Cloud Storage (GCS). All subsequent logins read from GCS cache (instant!).

```
┌─────────────────────────────────────────────────────────────────┐
│                    FIRST LOGIN OF THE DAY                       │
├─────────────────────────────────────────────────────────────────┤
│  1. Check GCS bucket → No cache / Cache expired                 │
│  2. Query BigQuery → Load ALL data (10-30 seconds)              │
│  3. Save to GCS as Parquet file                                 │
│  4. Return data to dashboard                                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              ALL OTHER LOGINS (SAME DAY)                        │
├─────────────────────────────────────────────────────────────────┤
│  1. Check GCS bucket → Cache exists & fresh (<24 hrs)           │
│  2. Load from GCS (1-2 seconds) ✓                               │
│  3. Return data to dashboard                                    │
│  4. NO BigQuery call!                                           │
└─────────────────────────────────────────────────────────────────┘
```

### Why This Matters

| Scenario | Without GCS Cache | With GCS Cache |
|----------|-------------------|----------------|
| First login | 10-30 sec (BigQuery) | 10-30 sec (BigQuery) |
| Second login | 10-30 sec (BigQuery) | **1-2 sec (GCS)** ✓ |
| Container restart | 10-30 sec (BigQuery) | **1-2 sec (GCS)** ✓ |
| New container | 10-30 sec (BigQuery) | **1-2 sec (GCS)** ✓ |
| Daily BigQuery calls | Many | **1 per day** ✓ |

### Cache Storage

- **Location:** Google Cloud Storage bucket
- **Format:** Parquet (compressed, fast to read)
- **Duration:** 24 hours (configurable)
- **Refresh:** Manual button or automatic after 24 hours

---

## Features

### Authentication & Access Control
- Username/password authentication
- Admin and Viewer roles
- Dashboard-level access control

### ICARUS - Plan (Historical) Dashboard
- **Active/Inactive tabs** for plan filtering
- **Collapsible filters:** Date Range, Billing Cycle, Cohort, Plan Groups, Metrics
- **Pivot Tables:** Regular & Crystal Ball (full width, frozen columns)
- **Charts:** 10 metrics × 2 versions = 20 line charts

### Design System
- Dark mode (default) / Light mode toggle
- Universal App-based color scheme
- Inter font family

---

## Tech Stack

- **Frontend:** Streamlit
- **Charts:** Plotly
- **Data Processing:** PyArrow (zero pandas!)
- **Data Source:** BigQuery
- **Cache Storage:** Google Cloud Storage (GCS)
- **Deployment:** Cloud Run (Docker)

---

## Project Structure

```
variant_dashboard/
├── app/
│   ├── main.py              # Entry point & routing
│   ├── config.py            # Configuration & constants
│   ├── bigquery_client.py   # Data loading with GCS caching
│   ├── theme.py             # Dark/Light theme
│   ├── auth.py              # Authentication
│   ├── colors.py            # App color scheme
│   ├── filters.py           # Filter components
│   ├── charts.py            # Chart builders
│   ├── pivots.py            # Pivot table builders
│   └── pages/
│       ├── login.py
│       ├── landing.py
│       └── icarus_historical.py
├── cloudbuild.yaml          # CI/CD with GCS bucket config
├── Dockerfile
├── requirements.txt
├── DEPLOYMENT.md            # Detailed deployment guide
└── README.md
```

---

## Quick Start

### Local Development
```bash
# Setup
unzip variant_dashboard.zip
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

### Cloud Run Deployment
See **DEPLOYMENT.md** for complete instructions including:
1. GCS bucket creation for caching
2. Service account setup
3. GitHub → Cloud Build → Cloud Run pipeline

---

## Default Credentials

| Role | Username | Password |
|------|----------|----------|
| Admin | admin | admin123 |
| Viewer | viewer | viewer123 |

⚠️ Change these in production!

---

## Configuration

### Cache Duration
Edit `app/config.py`:
```python
CACHE_TTL = 86400  # 24 hours in seconds
```

### BigQuery Table
Edit `app/config.py`:
```python
BIGQUERY_PROJECT = "your-project-id"
BIGQUERY_DATASET = "your-dataset"
BIGQUERY_TABLE = "your-table"
```

### GCS Bucket
Set environment variable:
```bash
export GCS_CACHE_BUCKET="your-bucket-name"
```

---

## App Color Scheme

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

## License

Proprietary - Variant Group
