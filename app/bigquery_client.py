"""
BigQuery Client for Variant Analytics Dashboard
Persistent Caching with Debugging

Cache Strategy:
1. Streamlit session_state (fastest - same session)
2. GCS Parquet file (persistent - survives restarts)
3. BigQuery (source - only when cache expired)
"""

from google.cloud import bigquery
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq
import streamlit as st
from datetime import datetime, timedelta
import io
import os

from config import BIGQUERY_FULL_TABLE, CACHE_TTL

# =============================================================================
# GCS CONFIGURATION
# =============================================================================
GCS_BUCKET_NAME = os.environ.get("GCS_CACHE_BUCKET", "")
GCS_CACHE_FILE = "cache/master_data.parquet"
GCS_METADATA_FILE = "cache/last_updated.txt"

# Debug flag - set to True to see what's happening
DEBUG = True

def log_debug(message):
    """Log debug message"""
    if DEBUG:
        print(f"[CACHE DEBUG] {datetime.now().strftime('%H:%M:%S')} - {message}")


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
        # Check if bucket exists
        if bucket.exists():
            log_debug(f"GCS bucket found: {GCS_BUCKET_NAME}")
            return bucket
        else:
            log_debug(f"GCS bucket does not exist: {GCS_BUCKET_NAME}")
            return None
    except Exception as e:
        log_debug(f"GCS error: {e}")
        return None


def get_gcs_cache_age(bucket):
    """Get age of GCS cache in hours"""
    if bucket is None:
        return None
    
    try:
        blob = bucket.blob(GCS_METADATA_FILE)
        if not blob.exists():
            return None
        
        content = blob.download_as_text()
        last_updated = datetime.fromisoformat(content.strip())
        age = datetime.now() - last_updated
        return age.total_seconds() / 3600  # Return hours
    except Exception as e:
        log_debug(f"Error getting cache age: {e}")
        return None


def is_cache_fresh(bucket):
    """Check if GCS cache is less than 24 hours old"""
    age_hours = get_gcs_cache_age(bucket)
    if age_hours is None:
        return False
    
    is_fresh = age_hours < (CACHE_TTL / 3600)
    log_debug(f"Cache age: {age_hours:.1f} hours, Fresh: {is_fresh}")
    return is_fresh


def load_from_gcs(bucket):
    """Load data from GCS Parquet file"""
    if bucket is None:
        return None
    
    try:
        blob = bucket.blob(GCS_CACHE_FILE)
        if not blob.exists():
            log_debug("GCS cache file not found")
            return None
        
        log_debug("Loading from GCS...")
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


def save_to_gcs(bucket, data):
    """Save PyArrow table to GCS as Parquet"""
    if bucket is None:
        log_debug("No GCS bucket - skipping save")
        return False
    
    try:
        log_debug("Saving to GCS...")
        start = datetime.now()
        
        buffer = io.BytesIO()
        pq.write_table(data, buffer, compression='snappy')
        buffer.seek(0)
        
        blob = bucket.blob(GCS_CACHE_FILE)
        blob.upload_from_file(buffer, content_type='application/octet-stream')
        
        meta_blob = bucket.blob(GCS_METADATA_FILE)
        meta_blob.upload_from_string(datetime.now().isoformat())
        
        elapsed = (datetime.now() - start).total_seconds()
        log_debug(f"GCS save complete in {elapsed:.2f}s")
        
        return True
    except Exception as e:
        log_debug(f"GCS save error: {e}")
        return False


def delete_gcs_cache(bucket):
    """Delete GCS cache files"""
    if bucket is None:
        return False
    
    try:
        blob = bucket.blob(GCS_CACHE_FILE)
        if blob.exists():
            blob.delete()
        
        meta_blob = bucket.blob(GCS_METADATA_FILE)
        if meta_blob.exists():
            meta_blob.delete()
        
        log_debug("GCS cache deleted")
        return True
    except Exception as e:
        log_debug(f"GCS delete error: {e}")
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
# MASTER DATA LOADER - With Session State + GCS Caching
# =============================================================================

def get_master_data():
    """
    Get master data with multi-level caching:
    1. Session state (instant - same session)
    2. GCS (fast - 1-2 seconds)
    3. BigQuery (slow - 10-30 seconds)
    """
    log_debug(f"loading data...")
    # Level 1: Check session state (same browser session)
    if "master_data" in st.session_state and st.session_state.master_data is not None:
        if "master_data_time" in st.session_state:
            age = (datetime.now() - st.session_state.master_data_time).total_seconds()
            if age < CACHE_TTL:
                log_debug(f"Using session state cache (age: {age/3600:.1f}h)")
                return st.session_state.master_data
    
    # Level 2: Check GCS cache
    bucket = get_gcs_bucket()
    
    if bucket and is_cache_fresh(bucket):
        data = load_from_gcs(bucket)
        if data is not None:
            # Store in session state for even faster access
            st.session_state.master_data = data
            st.session_state.master_data_time = datetime.now()
            st.session_state.master_data_source = "GCS"
            return data
    
    # Level 3: Load from BigQuery
    log_debug("Cache miss - loading from BigQuery")
    data = load_from_bigquery()
    
    # Save to GCS for future sessions
    if bucket:
        save_to_gcs(bucket, data)
    
    # Store in session state
    st.session_state.master_data = data
    st.session_state.master_data_time = datetime.now()
    st.session_state.master_data_source = "BigQuery"
    
    return data


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


# =============================================================================
# CACHE MANAGEMENT
# =============================================================================

def clear_all_cache():
    """Clear all cached data"""
    log_debug("Clearing all caches...")
    
    # Clear session state
    if "master_data" in st.session_state:
        del st.session_state.master_data
    if "master_data_time" in st.session_state:
        del st.session_state.master_data_time
    if "master_data_source" in st.session_state:
        del st.session_state.master_data_source
    
    # Clear GCS
    bucket = get_gcs_bucket()
    if bucket:
        delete_gcs_cache(bucket)

    get_master_data()
    
    log_debug("All caches cleared")


def get_cache_info():
    """Get information about cache status"""
    info = {
        "loaded": False,
        "source": "Not loaded",
        "last_updated": None,
        "rows": 0,
        "size_mb": 0,
        "gcs_configured": bool(GCS_BUCKET_NAME),
        "gcs_bucket": GCS_BUCKET_NAME or "Not set"
    }
    
    try:
        # Check session state
        if "master_data" in st.session_state and st.session_state.master_data is not None:
            info["loaded"] = True
            info["rows"] = st.session_state.master_data.num_rows
            info["source"] = st.session_state.get("master_data_source", "Session")
            
            if "master_data_time" in st.session_state:
                info["last_updated"] = st.session_state.master_data_time.isoformat()
        
        # Check GCS
        bucket = get_gcs_bucket()
        if bucket:
            info["gcs_available"] = True
            age = get_gcs_cache_age(bucket)
            if age is not None:
                info["gcs_age_hours"] = round(age, 1)
        else:
            info["gcs_available"] = False
        
        return info
    
    except Exception as e:
        info["error"] = str(e)
        return info
