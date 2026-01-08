# Deployment Guide: Google Cloud Run

This guide walks you through deploying the Variant Analytics Dashboard to Google Cloud Run via GitHub.

---

## Prerequisites

- Google Cloud account with billing enabled
- GitHub account
- `gcloud` CLI installed locally (optional, for manual steps)

---

## Step 1: Set Up Google Cloud Project

### 1.1 Create or Select Project
```bash
# Set your project ID
export PROJECT_ID="your-project-id"

# Create new project (or skip if using existing)
gcloud projects create $PROJECT_ID

# Set as active project
gcloud config set project $PROJECT_ID
```

### 1.2 Enable Required APIs
```bash
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    containerregistry.googleapis.com \
    bigquery.googleapis.com \
    storage.googleapis.com
```

---

## Step 2: Create GCS Bucket for Data Caching (IMPORTANT!)

This bucket stores the cached data so it persists across logins and container restarts.

### 2.1 Create the Cache Bucket
```bash
# Create bucket (name must be globally unique)
gsutil mb -l us-central1 gs://variant-dashboard-cache-$PROJECT_ID

# Set lifecycle rule to auto-delete old cache files (optional, keeps bucket clean)
echo '{"rule": [{"action": {"type": "Delete"}, "condition": {"age": 7}}]}' > lifecycle.json
gsutil lifecycle set lifecycle.json gs://variant-dashboard-cache-$PROJECT_ID
rm lifecycle.json
```

### 2.2 Verify Bucket
```bash
gsutil ls gs://variant-dashboard-cache-$PROJECT_ID
```

---

## Step 3: Create Service Account

### 3.1 Create Service Account
```bash
gcloud iam service-accounts create variant-dashboard-sa \
    --display-name="Variant Dashboard Service Account"
```

### 3.2 Grant BigQuery Permissions
```bash
# BigQuery Data Viewer (read data)
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:variant-dashboard-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/bigquery.dataViewer"

# BigQuery Job User (run queries)
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:variant-dashboard-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/bigquery.jobUser"
```

### 3.3 Grant GCS Permissions (for caching)
```bash
# Storage Object Admin (read/write cache files)
gsutil iam ch serviceAccount:variant-dashboard-sa@$PROJECT_ID.iam.gserviceaccount.com:objectAdmin \
    gs://variant-dashboard-cache-$PROJECT_ID
```

### 3.4 Verify Permissions
```bash
gcloud projects get-iam-policy $PROJECT_ID \
    --filter="bindings.members:variant-dashboard-sa" \
    --format="table(bindings.role)"
```

---

## Step 4: Push Code to GitHub

### 4.1 Run Setup Script First
```bash
cd variant_dashboard

# Make setup script executable and run it
chmod +x setup.sh
./setup.sh
```
This renames `gitignore.txt` → `.gitignore`, etc.

### 4.2 Create GitHub Repository
1. Go to [GitHub](https://github.com) and create a new repository
2. Name it `variant-dashboard` (or your preferred name)
3. Keep it private if needed

### 4.3 Push Code
```bash
# Initialize git
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit: Variant Analytics Dashboard"

# Add remote
git remote add origin https://github.com/YOUR_USERNAME/variant-dashboard.git

# Push
git branch -M main
git push -u origin main
```

### 4.4 Alternative: Upload via GitHub Web Interface
If uploading via GitHub web interface (without terminal):
1. Create repository on GitHub
2. Upload all files from the `variant_dashboard` folder
3. **Manually create** `.gitignore`, `.dockerignore`, `.gcloudignore`:
   - Click "Add file" → "Create new file"
   - Name it `.gitignore` (with the dot)
   - Copy content from `gitignore.txt`
   - Repeat for other files
4. Delete the `.txt` versions after creating hidden files

---

## Step 5: Connect GitHub to Cloud Build

### 5.1 Connect Repository
1. Go to [Cloud Build Triggers](https://console.cloud.google.com/cloud-build/triggers)
2. Click **"Connect Repository"**
3. Select **GitHub** as the source
4. Authenticate with GitHub
5. Select your `variant-dashboard` repository
6. Click **"Connect"**

### 5.2 Create Build Trigger
1. Click **"Create Trigger"**
2. Configure:
   - **Name:** `deploy-variant-dashboard`
   - **Event:** Push to a branch
   - **Branch:** `^main$`
   - **Configuration:** Cloud Build configuration file
   - **Location:** `cloudbuild.yaml`
3. Click **"Create"**

---

## Step 6: Grant Cloud Build Permissions

```bash
# Get Cloud Build service account
export CLOUDBUILD_SA=$(gcloud projects describe $PROJECT_ID \
    --format='value(projectNumber)')@cloudbuild.gserviceaccount.com

# Grant Cloud Run Admin
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$CLOUDBUILD_SA" \
    --role="roles/run.admin"

# Grant Service Account User
gcloud iam service-accounts add-iam-policy-binding \
    variant-dashboard-sa@$PROJECT_ID.iam.gserviceaccount.com \
    --member="serviceAccount:$CLOUDBUILD_SA" \
    --role="roles/iam.serviceAccountUser"
```

---

## Step 7: Deploy

### Option A: Automatic (Push to GitHub)
```bash
git add .
git commit -m "Your changes"
git push origin main
```
Cloud Build will automatically build and deploy.

### Option B: Manual Deploy via CLI
```bash
# Build and push image
gcloud builds submit --tag gcr.io/$PROJECT_ID/variant-dashboard

# Deploy to Cloud Run
gcloud run deploy variant-dashboard \
    --image gcr.io/$PROJECT_ID/variant-dashboard \
    --platform managed \
    --region us-central1 \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --allow-unauthenticated \
    --service-account variant-dashboard-sa@$PROJECT_ID.iam.gserviceaccount.com \
    --set-env-vars "GCS_CACHE_BUCKET=variant-dashboard-cache-$PROJECT_ID"
```

---

## Step 8: Verify Deployment

### 8.1 Check Cloud Run Service
1. Go to [Cloud Run](https://console.cloud.google.com/run)
2. Click on `variant-dashboard`
3. Copy the service URL

### 8.2 Test the Dashboard
1. Open the URL in your browser
2. Login with default credentials:
   - Admin: `admin` / `admin123`
   - Viewer: `viewer` / `viewer123`

### 8.3 Verify Caching Works
1. First login: Data loads from BigQuery (may take 10-30 seconds)
2. Logout and login again: Data loads instantly from GCS cache!
3. Check GCS bucket for cache files:
   ```bash
   gsutil ls gs://variant-dashboard-cache-$PROJECT_ID/cache/
   ```

---

## How Caching Works

```
First Login of Day (e.g., 9:00 AM)
├── Check GCS bucket for cache file
├── No cache found OR cache is >24 hours old
├── Query BigQuery (10-30 seconds)
├── Save data to GCS as Parquet file
└── Display dashboard

All Other Logins (Same Day)
├── Check GCS bucket for cache file
├── Cache exists AND is <24 hours old
├── Load from GCS (1-2 seconds) ✓
└── Display dashboard (NO BigQuery query!)

Next Day (After 24 Hours)
├── Cache is stale (>24 hours old)
├── Query BigQuery (fresh data)
├── Replace GCS cache file
└── Display dashboard
```

---

## Troubleshooting

### Cache Not Working
1. Check GCS bucket exists:
   ```bash
   gsutil ls gs://variant-dashboard-cache-$PROJECT_ID
   ```

2. Check service account has GCS permissions:
   ```bash
   gsutil iam get gs://variant-dashboard-cache-$PROJECT_ID
   ```

3. Check environment variable is set in Cloud Run:
   ```bash
   gcloud run services describe variant-dashboard \
       --region us-central1 \
       --format="value(spec.template.spec.containers[0].env)"
   ```

### BigQuery Permission Error
```bash
gcloud projects get-iam-policy $PROJECT_ID \
    --filter="bindings.members:variant-dashboard-sa" \
    --format="table(bindings.role)"
```

### Container Crashes
```bash
gcloud run services logs read variant-dashboard --region=us-central1 --limit=50
```

### Force Data Refresh
Click the **"🔄 Refresh Data"** button in the dashboard menu to clear cache and reload from BigQuery.

---

## Configuration

### Change Cache Bucket Name
Update in Cloud Run environment variables:
```bash
gcloud run services update variant-dashboard \
    --set-env-vars "GCS_CACHE_BUCKET=your-custom-bucket-name" \
    --region us-central1
```

### Change Cache Duration
Edit `app/config.py`:
```python
CACHE_TTL = 86400  # 24 hours (in seconds)
# Change to 43200 for 12 hours, etc.
```

---

## Security Recommendations

1. **Change default passwords** immediately after deployment
2. Create GCS bucket in same region as Cloud Run for faster access
3. Enable Cloud Audit Logs to track data access
4. Consider enabling IAP (Identity-Aware Proxy) for additional authentication

---

## Costs Estimate

| Resource | Estimated Monthly Cost |
|----------|----------------------|
| Cloud Run (2 vCPU, 2GB) | ~$20-50 |
| BigQuery (queries) | ~$5-10 (once/day now!) |
| GCS Storage | ~$0.50-2 |
| **Total** | **~$25-60/month** |

*Note: BigQuery costs reduced significantly since data loads only once per day!*

