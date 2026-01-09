"""
BigQuery Client for Variant Analytics Dashboard
Two-Stage Caching with Separate BQ and GCS Refresh
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

GCS_BUCKET_NAME = os.environ.get("GCS_CACHE_BUCKET", "")
DEBUG = True


def log_debug(message):
    """Log debug message"""
    if DEBUG:
        print(f"[CACHE] {datetime.now().strftime('%H:%M:%S')} - {message}")


# =============================================================================
# GCS HELPERS
# =============================================================================

def get_gcs_bucket():
    """Get GCS bucket for caching"""
    if not GCS_BUCKET_NAME:
        return None
    
    try:
        from google.cloud import storage
        client = storage.Client()
        bucket = client.bucket(GCS_BUCKET_NAME)
        if bucket.exists():
            return bucket
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
    except Exception:
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
    except Exception:
        return False


def load_parquet_from_gcs(bucket, cache_file):
    """Load parquet data from GCS"""
    if bucket is None:
        return None
    
    try:
        blob = bucket.blob(cache_file)
        if not blob.exists():
            return None
        
        parquet_bytes = blob.download_as_bytes()
        buffer = io.BytesIO(parquet_bytes)
        table = pq.read_table(buffer)
        return table
    except Exception as e:
        log_debug(f"GCS load error: {e}")
        return None


def save_parquet_to_gcs(bucket, cache_file, data):
    """Save PyArrow table to GCS as Parquet"""
    if bucket is None:
        return False
    
    try:
        buffer = io.BytesIO()
        pq.write_table(data, buffer, compression='snappy')
        buffer.seek(0)
        
        blob = bucket.blob(cache_file)
        blob.upload_from_file(buffer, content_type='application/octet-stream')
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
    log_debug(f"BigQuery loaded: {result.num_rows} rows")
    return result


# =============================================================================
# REFRESH FUNCTIONS
# =============================================================================

def refresh_bq_to_staging():
    """Query BigQuery and save to staging cache"""
    try:
        data = load_from_bigquery()
        bucket = get_gcs_bucket()
        
        if bucket:
            save_parquet_to_gcs(bucket, GCS_STAGING_CACHE, data)
            set_metadata_timestamp(bucket, GCS_BQ_REFRESH_METADATA)
            return True, "BQ refresh complete. Data saved to staging."
        else:
            return False, "GCS bucket not configured"
            
    except Exception as e:
        return False, f"BQ refresh failed: {str(e)}"


def refresh_gcs_from_staging():
    """Copy staging cache to active cache"""
    try:
        bucket = get_gcs_bucket()
        if not bucket:
            return False, "GCS bucket not configured"
        
        staging_blob = bucket.blob(GCS_STAGING_CACHE)
        if not staging_blob.exists():
            return False, "No staging data available. Run Refresh BQ first."
        
        data = load_parquet_from_gcs(bucket, GCS_STAGING_CACHE)
        if data is None:
            return False, "Failed to load staging data"
        
        save_parquet_to_gcs(bucket, GCS_ACTIVE_CACHE, data)
        set_metadata_timestamp(bucket, GCS_GCS_REFRESH_METADATA)
        
        # Clear session state to force reload
        if "master_data" in st.session_state:
            del st.session_state.master_data
        
        return True, "GCS refresh complete. Dashboards now using fresh data."
        
    except Exception as e:
        return False, f"GCS refresh failed: {str(e)}"


def check_and_run_auto_refresh():
    """Check if auto refresh should run at 10:15 UTC"""
    now_utc = datetime.now(timezone.utc)
    refresh_time_today = now_utc.replace(
        hour=AUTO_REFRESH_HOUR, 
        minute=AUTO_REFRESH_MINUTE, 
        second=0, 
        microsecond=0
    )
    
    if now_utc < refresh_time_today:
        return
    
    bucket = get_gcs_bucket()
    if not bucket:
        return
    
    last_bq_refresh = get_metadata_timestamp(bucket, GCS_BQ_REFRESH_METADATA)
    
    if last_bq_refresh is None or last_bq_refresh < refresh_time_today:
        if "auto_refresh_running" not in st.session_state:
            st.session_state.auto_refresh_running = True
            
            def auto_refresh_task():
                success, _ = refresh_bq_to_staging()
                if success:
                    refresh_gcs_from_staging()
                st.session_state.auto_refresh_running = False
            
            thread = threading.Thread(target=auto_refresh_task)
            thread.daemon = True
            thread.start()


# =============================================================================
# REFRESH TIMESTAMPS
# =============================================================================

def get_last_bq_refresh():
    """Get timestamp of last BQ refresh"""
    bucket = get_gcs_bucket()
    return get_metadata_timestamp(bucket, GCS_BQ_REFRESH_METADATA) if bucket else None


def get_last_gcs_refresh():
    """Get timestamp of last GCS refresh"""
    bucket = get_gcs_bucket()
    return get_metadata_timestamp(bucket, GCS_GCS_REFRESH_METADATA) if bucket else None


def format_refresh_timestamp(timestamp):
    """Format timestamp for display"""
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
# MASTER DATA LOADER
# =============================================================================

def get_master_data():
    """Get master data from cache hierarchy"""
    
    check_and_run_auto_refresh()
    
    # Session state cache
    if "master_data" in st.session_state and st.session_state.master_data is not None:
        return st.session_state.master_data
    
    # GCS cache
    bucket = get_gcs_bucket()
    if bucket:
        data = load_parquet_from_gcs(bucket, GCS_ACTIVE_CACHE)
        if data is not None:
            st.session_state.master_data = data
            st.session_state.master_data_source = "GCS"
            return data
    
    # BigQuery fallback
    data = load_from_bigquery()
    
    if bucket:
        save_parquet_to_gcs(bucket, GCS_ACTIVE_CACHE, data)
        save_parquet_to_gcs(bucket, GCS_STAGING_CACHE, data)
        set_metadata_timestamp(bucket, GCS_BQ_REFRESH_METADATA)
        set_metadata_timestamp(bucket, GCS_GCS_REFRESH_METADATA)
    
    st.session_state.master_data = data
    st.session_state.master_data_source = "BigQuery"
    
    return data


def get_cache_info():
    """Get information about cache status"""
    info = {
        "loaded": False,
        "source": "Not loaded",
        "last_bq_refresh": "--",
        "last_gcs_refresh": "--",
        "staging_ready": False,
        "rows": 0,
    }
    
    try:
        bq_ts = get_last_bq_refresh()
        gcs_ts = get_last_gcs_refresh()
        
        info["last_bq_refresh"] = format_refresh_timestamp(bq_ts)
        info["last_gcs_refresh"] = format_refresh_timestamp(gcs_ts)
        info["staging_ready"] = is_staging_ready()
        
        if "master_data" in st.session_state and st.session_state.master_data is not None:
            info["loaded"] = True
            info["rows"] = st.session_state.master_data.num_rows
            info["source"] = st.session_state.get("master_data_source", "Session")
        
        return info
    except Exception as e:
        info["error"] = str(e)
        return info


# =============================================================================
# DATA QUERIES
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


def load_plan_groups(active_inactive="Active"):
    """Get unique App_Name and Plan_Name"""
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
