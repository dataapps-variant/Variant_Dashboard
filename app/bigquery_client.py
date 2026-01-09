"""
BigQuery Client for Variant Analytics Dashboard
Two-Stage Caching with Separate BQ and GCS Refresh

Cache Strategy:
1. Active Cache (GCS) - What dashboards use
2. Staging Cache (GCS) - Where BQ refresh goes
3. Session State - Fast access for current session
4. Auto-refresh at 10:15 UTC daily (background)

Refresh Flow:
- Refresh BQ: BigQuery → Staging (dashboards unaffected)
- Refresh GCS: Staging → Active (dashboards update)
"""

from google.cloud import bigquery
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq
import streamlit as st
from datetime import datetime, timezone
import io
import os
import threading

from config import (
    BIGQUERY_FULL_TABLE, 
    CACHE_TTL,
    AUTO_REFRESH_HOUR,
    AUTO_REFRESH_MINUTE,
    GCS_ACTIVE_CACHE,
    GCS_STAGING_CACHE,
    GCS_BQ_REFRESH_METADATA,
    GCS_GCS_REFRESH_METADATA,
)

# =============================================================================
# GCS CONFIGURATION
# =============================================================================
GCS_BUCKET_NAME = os.environ.get("GCS_CACHE_BUCKET", "")
DEBUG = True


def log_debug(message):
    """Log debug message"""
    if DEBUG:
        print(f"[CACHE] {datetime.now().strftime('%H:%M:%S')} - {message}")


# =============================================================================
# GCS HELPER FUNCTIONS
# =============================================================================

def get_gcs_bucket():
    """Get GCS bucket for caching"""
    if not GCS_BUCKET_NAME:
        log_debug("GCS_CACHE_BUCKET not set - GCS caching disabled")
        return None
    
    try:
        from google.cloud import storage
        client = storage.Client()
        bucket = client.bucket(GCS_BUCKET_NAME)
        if bucket.exists():
            log_debug(f"GCS bucket found: {GCS_BUCKET_NAME}")
            return bucket
        else:
            log_debug(f"GCS bucket does not exist: {GCS_BUCKET_NAME}")
            return None
    except Exception as e:
        log_debug(f"GCS error: {e}")
        return None


def get_metadata_timestamp(bucket, metadata_file):
    """Get timestamp from metadata file"""
    if bucket is None:
        return None
    
    try:
        blob = bucket.blob(metadata_file)
        if not blob.exists():
            return None
        
        content = blob.download_as_text()
        return datetime.fromisoformat(content.strip())
    except Exception as e:
        log_debug(f"Error getting metadata: {e}")
        return None


def set_metadata_timestamp(bucket, metadata_file, timestamp=None):
    """Set timestamp in metadata file"""
    if bucket is None:
        return False
    
    try:
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        
        blob = bucket.blob(metadata_file)
        blob.upload_from_string(timestamp.isoformat())
        return True
    except Exception as e:
        log_debug(f"Error setting metadata: {e}")
        return False


def load_parquet_from_gcs(bucket, cache_file):
    """Load parquet data from GCS"""
    if bucket is None:
        return None
    
    try:
        blob = bucket.blob(cache_file)
        if not blob.exists():
            log_debug(f"Cache file not found: {cache_file}")
            return None
        
        log_debug(f"Loading from GCS: {cache_file}")
        start = datetime.now()
        
        parquet_bytes = blob.download_as_bytes()
        buffer = io.BytesIO(parquet_bytes)
        table = pq.read_table(buffer)
        
        elapsed = (datetime.now() - start).total_seconds()
        log_debug(f"GCS load complete: {table.num_rows} rows in {elapsed:.2f}s")
        
        return table
    except Exception as e:
        log_debug(f"GCS load error: {e}")
        return None


def save_parquet_to_gcs(bucket, cache_file, data):
    """Save PyArrow table to GCS as Parquet with Snappy compression"""
    if bucket is None:
        log_debug("No GCS bucket - skipping save")
        return False
    
    try:
        log_debug(f"Saving to GCS: {cache_file}")
        start = datetime.now()
        
        buffer = io.BytesIO()
        pq.write_table(data, buffer, compression='snappy')
        buffer.seek(0)
        
        blob = bucket.blob(cache_file)
        blob.upload_from_file(buffer, content_type='application/octet-stream')
        
        elapsed = (datetime.now() - start).total_seconds()
        log_debug(f"GCS save complete in {elapsed:.2f}s")
        
        return True
    except Exception as e:
        log_debug(f"GCS save error: {e}")
        return False


# =============================================================================
# BIGQUERY LOADER
# =============================================================================

def load_from_bigquery():
    """Load ALL data from BigQuery"""
    log_debug("Loading from BigQuery...")
    start = datetime.now()
    
    client = bigquery.Client()
    
    query = f"""
        SELECT
            Reporting_Date,
            App_Name,
            Plan_Name,
            BC,
            Cohort,
            Active_Inactive,
            `Table`,
            Subscriptions,
            Rebills,
            Churn_Rate,
            Refund_Rate,
            Gross_ARPU_Retention_Rate,
            Net_ARPU_Retention_Rate,
            Cohort_CAC,
            Recent_CAC,
            Gross_ARPU_Discounted,
            Net_ARPU_Discounted,
            Net_LTV_Discounted,
            BC4_CAC_Ceiling
        FROM `{BIGQUERY_FULL_TABLE}`
    """
    
    result = client.query(query).to_arrow()
    
    elapsed = (datetime.now() - start).total_seconds()
    log_debug(f"BigQuery load complete: {result.num_rows} rows in {elapsed:.2f}s")
    
    return result


# =============================================================================
# REFRESH BQ - Save to Staging
# =============================================================================

def refresh_bq_to_staging():
    """
    Query BigQuery and save to staging cache.
    Does NOT affect active cache - dashboards continue using existing data.
    
    Returns: (success: bool, message: str)
    """
    try:
        log_debug("Starting BQ refresh to staging...")
        
        # Query BigQuery
        data = load_from_bigquery()
        
        # Save to staging cache
        bucket = get_gcs_bucket()
        if bucket:
            save_parquet_to_gcs(bucket, GCS_STAGING_CACHE, data)
            set_metadata_timestamp(bucket, GCS_BQ_REFRESH_METADATA)
            
            log_debug("BQ refresh to staging complete")
            return True, "BQ refresh complete. Data saved to staging."
        else:
            log_debug("No GCS bucket - BQ refresh failed")
            return False, "GCS bucket not configured"
            
    except Exception as e:
        log_debug(f"BQ refresh error: {e}")
        return False, f"BQ refresh failed: {str(e)}"


def refresh_bq_background():
    """Run BQ refresh in background thread"""
    thread = threading.Thread(target=refresh_bq_to_staging)
    thread.daemon = True
    thread.start()
    return thread


# =============================================================================
# REFRESH GCS - Swap Staging to Active
# =============================================================================

def refresh_gcs_from_staging():
    """
    Copy staging cache to active cache.
    Dashboards will now use the fresh data.
    
    Returns: (success: bool, message: str)
    """
    try:
        log_debug("Starting GCS refresh from staging...")
        
        bucket = get_gcs_bucket()
        if not bucket:
            return False, "GCS bucket not configured"
        
        # Check if staging exists
        staging_blob = bucket.blob(GCS_STAGING_CACHE)
        if not staging_blob.exists():
            return False, "No staging data available. Run Refresh BQ first."
        
        # Load staging data
        data = load_parquet_from_gcs(bucket, GCS_STAGING_CACHE)
        if data is None:
            return False, "Failed to load staging data"
        
        # Save to active cache
        save_parquet_to_gcs(bucket, GCS_ACTIVE_CACHE, data)
        set_metadata_timestamp(bucket, GCS_GCS_REFRESH_METADATA)
        
        # Clear session state to force reload
        if "master_data" in st.session_state:
            del st.session_state.master_data
        if "master_data_time" in st.session_state:
            del st.session_state.master_data_time
        
        log_debug("GCS refresh from staging complete")
        return True, "GCS refresh complete. Dashboards now using fresh data."
        
    except Exception as e:
        log_debug(f"GCS refresh error: {e}")
        return False, f"GCS refresh failed: {str(e)}"


# =============================================================================
# AUTO REFRESH - Runs at 10:15 UTC
# =============================================================================

def check_and_run_auto_refresh():
    """
    Check if auto refresh should run.
    Runs if current time is past 10:15 UTC and hasn't run today.
    Runs in background - user sees old cache while new data loads.
    """
    now_utc = datetime.now(timezone.utc)
    refresh_time_today = now_utc.replace(
        hour=AUTO_REFRESH_HOUR, 
        minute=AUTO_REFRESH_MINUTE, 
        second=0, 
        microsecond=0
    )
    
    # Check if we're past refresh time
    if now_utc < refresh_time_today:
        log_debug("Before auto-refresh time")
        return
    
    # Check last BQ refresh
    bucket = get_gcs_bucket()
    if not bucket:
        return
    
    last_bq_refresh = get_metadata_timestamp(bucket, GCS_BQ_REFRESH_METADATA)
    
    # If never refreshed or last refresh was before today's refresh time
    if last_bq_refresh is None or last_bq_refresh < refresh_time_today:
        log_debug("Auto-refresh triggered")
        
        # Mark that auto-refresh is in progress
        if "auto_refresh_running" not in st.session_state:
            st.session_state.auto_refresh_running = True
            
            # Run BQ refresh in background
            def auto_refresh_task():
                success, msg = refresh_bq_to_staging()
                if success:
                    # Automatically apply to active
                    refresh_gcs_from_staging()
                st.session_state.auto_refresh_running = False
            
            thread = threading.Thread(target=auto_refresh_task)
            thread.daemon = True
            thread.start()
    else:
        log_debug("Auto-refresh already done today")


# =============================================================================
# GET REFRESH TIMESTAMPS
# =============================================================================

def get_last_bq_refresh():
    """Get timestamp of last BQ refresh"""
    bucket = get_gcs_bucket()
    if not bucket:
        return None
    return get_metadata_timestamp(bucket, GCS_BQ_REFRESH_METADATA)


def get_last_gcs_refresh():
    """Get timestamp of last GCS refresh (when active cache was updated)"""
    bucket = get_gcs_bucket()
    if not bucket:
        return None
    return get_metadata_timestamp(bucket, GCS_GCS_REFRESH_METADATA)


def format_refresh_timestamp(timestamp):
    """Format timestamp for display: 09 Jan, 10:15"""
    if timestamp is None:
        return "--"
    
    return timestamp.strftime("%d %b, %H:%M")


def is_staging_ready():
    """Check if staging has newer data than active"""
    bucket = get_gcs_bucket()
    if not bucket:
        return False
    
    bq_refresh = get_metadata_timestamp(bucket, GCS_BQ_REFRESH_METADATA)
    gcs_refresh = get_metadata_timestamp(bucket, GCS_GCS_REFRESH_METADATA)
    
    if bq_refresh is None:
        return False
    
    if gcs_refresh is None:
        return True
    
    return bq_refresh > gcs_refresh


# =============================================================================
# MASTER DATA LOADER - Uses Active Cache
# =============================================================================

def get_master_data():
    """
    Get master data from active cache.
    
    Priority:
    1. Session state (fastest - same session)
    2. GCS Active cache (persistent)
    3. BigQuery (only if no cache exists)
    """
    
    # Check for auto-refresh
    check_and_run_auto_refresh()
    
    # Level 1: Check session state
    if "master_data" in st.session_state and st.session_state.master_data is not None:
        if "master_data_time" in st.session_state:
            age = (datetime.now() - st.session_state.master_data_time).total_seconds()
            if age < CACHE_TTL:
                log_debug(f"Using session state cache (age: {age/3600:.1f}h)")
                return st.session_state.master_data
    
    # Level 2: Check GCS active cache
    bucket = get_gcs_bucket()
    
    if bucket:
        data = load_parquet_from_gcs(bucket, GCS_ACTIVE_CACHE)
        if data is not None:
            st.session_state.master_data = data
            st.session_state.master_data_time = datetime.now()
            st.session_state.master_data_source = "GCS"
            return data
    
    # Level 3: Load from BigQuery (first time only)
    log_debug("No cache found - loading from BigQuery")
    data = load_from_bigquery()
    
    # Save to both staging and active
    if bucket:
        save_parquet_to_gcs(bucket, GCS_ACTIVE_CACHE, data)
        save_parquet_to_gcs(bucket, GCS_STAGING_CACHE, data)
        set_metadata_timestamp(bucket, GCS_BQ_REFRESH_METADATA)
        set_metadata_timestamp(bucket, GCS_GCS_REFRESH_METADATA)
    
    # Store in session state
    st.session_state.master_data = data
    st.session_state.master_data_time = datetime.now()
    st.session_state.master_data_source = "BigQuery"
    
    return data


# =============================================================================
# CACHE INFO
# =============================================================================

def get_cache_info():
    """Get information about cache status"""
    info = {
        "loaded": False,
        "source": "Not loaded",
        "last_bq_refresh": "--",
        "last_gcs_refresh": "--",
        "staging_ready": False,
        "rows": 0,
        "gcs_configured": bool(GCS_BUCKET_NAME),
        "gcs_bucket": GCS_BUCKET_NAME or "Not set"
    }
    
    try:
        # Get refresh timestamps
        info["last_bq_refresh"] = format_refresh_timestamp(get_last_bq_refresh())
        info["last_gcs_refresh"] = format_refresh_timestamp(get_last_gcs_refresh())
        info["staging_ready"] = is_staging_ready()
        
        # Check session state
        if "master_data" in st.session_state and st.session_state.master_data is not None:
            info["loaded"] = True
            info["rows"] = st.session_state.master_data.num_rows
            info["source"] = st.session_state.get("master_data_source", "Session")
        
        return info
    
    except Exception as e:
        info["error"] = str(e)
        return info


# =============================================================================
# DATE BOUNDS
# =============================================================================

def load_date_bounds():
    """Get min and max dates from cached data"""
    data = get_master_data()
    
    dates = data.column("Reporting_Date")
    min_date = pc.min(dates).as_py()
    max_date = pc.max(dates).as_py()
    
    if hasattr(min_date, 'date'):
        min_date = min_date.date()
    if hasattr(max_date, 'date'):
        max_date = max_date.date()
    
    return {"min_date": min_date, "max_date": max_date}


# =============================================================================
# PLAN GROUPS
# =============================================================================

def load_plan_groups(active_inactive="Active"):
    """Get unique App_Name and Plan_Name for Active or Inactive"""
    data = get_master_data()
    
    mask = pc.equal(data.column("Active_Inactive"), active_inactive)
    filtered = data.filter(mask)
    
    app_names = filtered.column("App_Name").to_pylist()
    plan_names = filtered.column("Plan_Name").to_pylist()
    
    seen = set()
    unique_apps = []
    unique_plans = []
    
    for app, plan in zip(app_names, plan_names):
        if (app, plan) not in seen:
            seen.add((app, plan))
            unique_apps.append(app)
            unique_plans.append(plan)
    
    sorted_pairs = sorted(zip(unique_apps, unique_plans), key=lambda x: (x[0], x[1]))
    
    return {
        "App_Name": [p[0] for p in sorted_pairs],
        "Plan_Name": [p[1] for p in sorted_pairs]
    }


# =============================================================================
# PIVOT DATA
# =============================================================================

def load_pivot_data(start_date, end_date, bc, cohort, plans, metrics, table_type, active_inactive="Active"):
    """Filter cached data for pivot table"""
    data = get_master_data()
    
    reporting_dates = data.column("Reporting_Date")
    
    mask = pc.and_(
        pc.greater_equal(reporting_dates, start_date),
        pc.less_equal(reporting_dates, end_date)
    )
    mask = pc.and_(mask, pc.equal(data.column("BC"), bc))
    mask = pc.and_(mask, pc.equal(data.column("Cohort"), cohort))
    mask = pc.and_(mask, pc.equal(data.column("Active_Inactive"), active_inactive))
    mask = pc.and_(mask, pc.equal(data.column("Table"), table_type))
    
    if plans:
        plans_set = pa.array(plans)
        plan_mask = pc.is_in(data.column("Plan_Name"), value_set=plans_set)
        mask = pc.and_(mask, plan_mask)
    
    filtered = data.filter(mask)
    
    result = {
        "App_Name": filtered.column("App_Name").to_pylist(),
        "Plan_Name": filtered.column("Plan_Name").to_pylist(),
        "Reporting_Date": filtered.column("Reporting_Date").to_pylist()
    }
    
    for metric in metrics:
        if metric in filtered.column_names:
            result[metric] = filtered.column(metric).to_pylist()
    
    return result


# =============================================================================
# CHART DATA
# =============================================================================

def load_chart_data(start_date, end_date, bc, cohort, plans, metric, table_type, active_inactive="Active"):
    """Filter and aggregate cached data for charts"""
    data = get_master_data()
    
    reporting_dates = data.column("Reporting_Date")
    
    mask = pc.and_(
        pc.greater_equal(reporting_dates, start_date),
        pc.less_equal(reporting_dates, end_date)
    )
    mask = pc.and_(mask, pc.equal(data.column("BC"), bc))
    mask = pc.and_(mask, pc.equal(data.column("Cohort"), cohort))
    mask = pc.and_(mask, pc.equal(data.column("Active_Inactive"), active_inactive))
    mask = pc.and_(mask, pc.equal(data.column("Table"), table_type))
    
    if plans:
        plans_set = pa.array(plans)
        plan_mask = pc.is_in(data.column("Plan_Name"), value_set=plans_set)
        mask = pc.and_(mask, plan_mask)
    
    filtered = data.filter(mask)
    
    if filtered.num_rows == 0:
        return {"Plan_Name": [], "Reporting_Date": [], "metric_value": []}
    
    plan_names = filtered.column("Plan_Name").to_pylist()
    dates = filtered.column("Reporting_Date").to_pylist()
    values = filtered.column(metric).to_pylist()
    
    # Aggregate by plan + date
    aggregated = {}
    for plan, date, value in zip(plan_names, dates, values):
        key = (plan, date)
        if key not in aggregated:
            aggregated[key] = 0
        if value is not None:
            aggregated[key] += value
    
    result_plans = []
    result_dates = []
    result_values = []
    
    for (plan, date), total in sorted(aggregated.items(), key=lambda x: (x[0][0], x[0][1])):
        result_plans.append(plan)
        result_dates.append(date)
        result_values.append(total)
    
    return {
        "Plan_Name": result_plans,
        "Reporting_Date": result_dates,
        "metric_value": result_values
    }
