"""
BigQuery Client - OPTIMIZED VERSION
Performance improvements:
1. Pre-aggregated data loading
2. Efficient caching with TTL
3. Lazy loading patterns
4. Reduced redundant processing
"""

from google.cloud import bigquery
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq
import streamlit as st
from datetime import datetime, timezone, timedelta
import io
import os
import hashlib

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
    if DEBUG:
        print(f"[CACHE] {datetime.now().strftime('%H:%M:%S')} - {message}")


# =============================================================================
# GCS HELPER FUNCTIONS (unchanged)
# =============================================================================

def get_gcs_bucket():
    if not GCS_BUCKET_NAME:
        return None
    try:
        from google.cloud import storage
        client = storage.Client()
        bucket = client.bucket(GCS_BUCKET_NAME)
        return bucket if bucket.exists() else None
    except Exception as e:
        log_debug(f"GCS error: {e}")
        return None


def get_metadata_timestamp(bucket, metadata_file):
    if bucket is None:
        return None
    try:
        blob = bucket.blob(metadata_file)
        if not blob.exists():
            return None
        return datetime.fromisoformat(blob.download_as_text().strip())
    except:
        return None


def set_metadata_timestamp(bucket, metadata_file, timestamp=None):
    if bucket is None:
        return False
    try:
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        bucket.blob(metadata_file).upload_from_string(timestamp.isoformat())
        return True
    except:
        return False


def load_parquet_from_gcs(bucket, cache_file):
    if bucket is None:
        return None
    try:
        blob = bucket.blob(cache_file)
        if not blob.exists():
            return None
        
        log_debug(f"Loading from GCS: {cache_file}")
        start = datetime.now()
        
        parquet_bytes = blob.download_as_bytes()
        table = pq.read_table(io.BytesIO(parquet_bytes))
        
        log_debug(f"GCS load: {table.num_rows} rows in {(datetime.now() - start).total_seconds():.2f}s")
        return table
    except Exception as e:
        log_debug(f"GCS load error: {e}")
        return None


def save_parquet_to_gcs(bucket, cache_file, data):
    if bucket is None:
        return False
    try:
        buffer = io.BytesIO()
        pq.write_table(data, buffer, compression='snappy')
        buffer.seek(0)
        bucket.blob(cache_file).upload_from_file(buffer, content_type='application/octet-stream')
        return True
    except Exception as e:
        log_debug(f"GCS save error: {e}")
        return False


# =============================================================================
# OPTIMIZED BIGQUERY LOADER
# =============================================================================

def load_from_bigquery():
    """
    Load data from BigQuery with optimizations:
    - Only select needed columns
    - Consider partitioning/clustering in BQ table
    """
    log_debug("Loading from BigQuery...")
    start = datetime.now()
    
    client = bigquery.Client()
    
    # TIP: Add date filter if you have a partition column
    # WHERE Reporting_Date >= DATE_SUB(CURRENT_DATE(), INTERVAL 2 YEAR)
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
    
    # Use query job for better control
    job_config = bigquery.QueryJobConfig(
        use_query_cache=True,  # Enable BQ cache
    )
    
    result = client.query(query, job_config=job_config).to_arrow()
    
    log_debug(f"BigQuery: {result.num_rows} rows in {(datetime.now() - start).total_seconds():.2f}s")
    return result


# =============================================================================
# MASTER DATA LOADER - WITH APP-LEVEL CACHE
# =============================================================================

# App-level cache (persists across sessions within same instance)
_app_cache = {
    "data": None,
    "loaded_at": None,
    "date_bounds": None,
    "plan_groups_active": None,
    "plan_groups_inactive": None,
}


def _is_cache_valid():
    """Check if app-level cache is still valid"""
    if _app_cache["data"] is None or _app_cache["loaded_at"] is None:
        return False
    age = (datetime.now() - _app_cache["loaded_at"]).total_seconds()
    return age < CACHE_TTL


def get_master_data():
    """
    Get master data with multi-level caching:
    1. App-level cache (fastest - same process)
    2. Session state (same session)
    3. GCS cache (persistent across instances)
    4. BigQuery (fallback)
    """
    global _app_cache
    
    # Level 1: App-level cache (fastest)
    if _is_cache_valid():
        log_debug("Using app-level cache")
        return _app_cache["data"]
    
    # Level 2: Session state
    if "master_data" in st.session_state and st.session_state.master_data is not None:
        if "master_data_time" in st.session_state:
            age = (datetime.now() - st.session_state.master_data_time).total_seconds()
            if age < CACHE_TTL:
                log_debug(f"Using session cache (age: {age/3600:.1f}h)")
                # Populate app cache
                _app_cache["data"] = st.session_state.master_data
                _app_cache["loaded_at"] = st.session_state.master_data_time
                return st.session_state.master_data
    
    # Level 3: GCS cache
    bucket = get_gcs_bucket()
    if bucket:
        data = load_parquet_from_gcs(bucket, GCS_ACTIVE_CACHE)
        if data is not None:
            _app_cache["data"] = data
            _app_cache["loaded_at"] = datetime.now()
            st.session_state.master_data = data
            st.session_state.master_data_time = datetime.now()
            st.session_state.master_data_source = "GCS"
            return data
    
    # Level 4: BigQuery (slowest)
    log_debug("No cache - loading from BigQuery")
    data = load_from_bigquery()
    
    # Save to all cache levels
    _app_cache["data"] = data
    _app_cache["loaded_at"] = datetime.now()
    
    if bucket:
        save_parquet_to_gcs(bucket, GCS_ACTIVE_CACHE, data)
        save_parquet_to_gcs(bucket, GCS_STAGING_CACHE, data)
        set_metadata_timestamp(bucket, GCS_BQ_REFRESH_METADATA)
        set_metadata_timestamp(bucket, GCS_GCS_REFRESH_METADATA)
    
    st.session_state.master_data = data
    st.session_state.master_data_time = datetime.now()
    st.session_state.master_data_source = "BigQuery"
    
    return data


# =============================================================================
# OPTIMIZED: CACHED DERIVED DATA
# =============================================================================

@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_date_bounds():
    """Get min and max dates - CACHED"""
    data = get_master_data()
    dates = data.column("Reporting_Date")
    min_date = pc.min(dates).as_py()
    max_date = pc.max(dates).as_py()
    
    if hasattr(min_date, 'date'):
        min_date = min_date.date()
    if hasattr(max_date, 'date'):
        max_date = max_date.date()
    
    return {"min_date": min_date, "max_date": max_date}


@st.cache_data(ttl=3600)
def load_plan_groups(active_inactive="Active"):
    """Get unique plans - CACHED"""
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
    
    sorted_pairs = sorted(zip(unique_apps, unique_plans))
    
    return {
        "App_Name": [p[0] for p in sorted_pairs],
        "Plan_Name": [p[1] for p in sorted_pairs]
    }


def _create_filter_hash(start_date, end_date, bc, cohort, plans, table_type, active_inactive):
    """Create hash for filter combination"""
    key = f"{start_date}_{end_date}_{bc}_{cohort}_{sorted(plans) if plans else 'all'}_{table_type}_{active_inactive}"
    return hashlib.md5(key.encode()).hexdigest()[:16]


@st.cache_data(ttl=1800)  # Cache for 30 min
def load_pivot_data(start_date, end_date, bc, cohort, plans, metrics, table_type, active_inactive="Active"):
    """Filter data for pivot table - CACHED"""
    data = get_master_data()
    
    reporting_dates = data.column("Reporting_Date")
    
    # Build filter mask
    mask = pc.and_(
        pc.greater_equal(reporting_dates, start_date),
        pc.less_equal(reporting_dates, end_date)
    )
    mask = pc.and_(mask, pc.equal(data.column("BC"), bc))
    mask = pc.and_(mask, pc.equal(data.column("Cohort"), cohort))
    mask = pc.and_(mask, pc.equal(data.column("Active_Inactive"), active_inactive))
    mask = pc.and_(mask, pc.equal(data.column("Table"), table_type))
    
    if plans:
        plan_mask = pc.is_in(data.column("Plan_Name"), value_set=pa.array(plans))
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


@st.cache_data(ttl=1800)
def load_chart_data(start_date, end_date, bc, cohort, plans, metric, table_type, active_inactive="Active"):
    """Filter and aggregate data for charts - CACHED"""
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
        plan_mask = pc.is_in(data.column("Plan_Name"), value_set=pa.array(plans))
        mask = pc.and_(mask, plan_mask)
    
    filtered = data.filter(mask)
    
    if filtered.num_rows == 0:
        return {"Plan_Name": [], "Reporting_Date": [], "metric_value": []}
    
    plan_names = filtered.column("Plan_Name").to_pylist()
    dates = filtered.column("Reporting_Date").to_pylist()
    values = filtered.column(metric).to_pylist()
    
    # Aggregate
    aggregated = {}
    for plan, date, value in zip(plan_names, dates, values):
        key = (plan, date)
        if key not in aggregated:
            aggregated[key] = 0
        if value is not None:
            aggregated[key] += value
    
    result_plans, result_dates, result_values = [], [], []
    for (plan, date), total in sorted(aggregated.items()):
        result_plans.append(plan)
        result_dates.append(date)
        result_values.append(total)
    
    return {
        "Plan_Name": result_plans,
        "Reporting_Date": result_dates,
        "metric_value": result_values
    }


# =============================================================================
# BATCH LOADING FOR CHARTS (MAJOR OPTIMIZATION)
# =============================================================================

@st.cache_data(ttl=1800)
def load_all_chart_data(start_date, end_date, bc, cohort, plans, metrics, table_type, active_inactive="Active"):
    """
    Load ALL chart data in ONE pass instead of 20 separate queries.
    This is a MAJOR performance improvement.
    """
    data = get_master_data()
    
    reporting_dates = data.column("Reporting_Date")
    
    # Single filter pass
    mask = pc.and_(
        pc.greater_equal(reporting_dates, start_date),
        pc.less_equal(reporting_dates, end_date)
    )
    mask = pc.and_(mask, pc.equal(data.column("BC"), bc))
    mask = pc.and_(mask, pc.equal(data.column("Cohort"), cohort))
    mask = pc.and_(mask, pc.equal(data.column("Active_Inactive"), active_inactive))
    mask = pc.and_(mask, pc.equal(data.column("Table"), table_type))
    
    if plans:
        plan_mask = pc.is_in(data.column("Plan_Name"), value_set=pa.array(plans))
        mask = pc.and_(mask, plan_mask)
    
    filtered = data.filter(mask)
    
    if filtered.num_rows == 0:
        return {metric: {"Plan_Name": [], "Reporting_Date": [], "metric_value": []} for metric in metrics}
    
    plan_names = filtered.column("Plan_Name").to_pylist()
    dates = filtered.column("Reporting_Date").to_pylist()
    
    results = {}
    for metric in metrics:
        if metric not in filtered.column_names:
            results[metric] = {"Plan_Name": [], "Reporting_Date": [], "metric_value": []}
            continue
            
        values = filtered.column(metric).to_pylist()
        
        # Aggregate
        aggregated = {}
        for plan, date, value in zip(plan_names, dates, values):
            key = (plan, date)
            if key not in aggregated:
                aggregated[key] = 0
            if value is not None:
                aggregated[key] += value
        
        result_plans, result_dates, result_values = [], [], []
        for (plan, date), total in sorted(aggregated.items()):
            result_plans.append(plan)
            result_dates.append(date)
            result_values.append(total)
        
        results[metric] = {
            "Plan_Name": result_plans,
            "Reporting_Date": result_dates,
            "metric_value": result_values
        }
    
    return results


# =============================================================================
# REFRESH FUNCTIONS (unchanged but with better error handling)
# =============================================================================

def refresh_bq_to_staging():
    """Query BigQuery and save to staging cache."""
    try:
        log_debug("Starting BQ refresh...")
        data = load_from_bigquery()
        
        bucket = get_gcs_bucket()
        if bucket:
            save_parquet_to_gcs(bucket, GCS_STAGING_CACHE, data)
            set_metadata_timestamp(bucket, GCS_BQ_REFRESH_METADATA)
            return True, "BQ refresh complete. Data saved to staging."
        return False, "GCS bucket not configured"
    except Exception as e:
        log_debug(f"BQ refresh error: {e}")
        return False, f"BQ refresh failed: {str(e)}"


def refresh_gcs_from_staging():
    """Copy staging cache to active cache."""
    global _app_cache
    
    try:
        bucket = get_gcs_bucket()
        if not bucket:
            return False, "GCS bucket not configured"
        
        staging_blob = bucket.blob(GCS_STAGING_CACHE)
        if not staging_blob.exists():
            return False, "No staging data. Run Refresh BQ first."
        
        data = load_parquet_from_gcs(bucket, GCS_STAGING_CACHE)
        if data is None:
            return False, "Failed to load staging data"
        
        save_parquet_to_gcs(bucket, GCS_ACTIVE_CACHE, data)
        set_metadata_timestamp(bucket, GCS_GCS_REFRESH_METADATA)
        
        # Clear ALL caches
        _app_cache = {"data": None, "loaded_at": None, "date_bounds": None, 
                      "plan_groups_active": None, "plan_groups_inactive": None}
        
        for key in ["master_data", "master_data_time"]:
            if key in st.session_state:
                del st.session_state[key]
        
        # Clear Streamlit's cache
        st.cache_data.clear()
        
        return True, "GCS refresh complete."
    except Exception as e:
        return False, f"GCS refresh failed: {str(e)}"


def get_last_bq_refresh():
    return get_metadata_timestamp(get_gcs_bucket(), GCS_BQ_REFRESH_METADATA)


def get_last_gcs_refresh():
    return get_metadata_timestamp(get_gcs_bucket(), GCS_GCS_REFRESH_METADATA)


def format_refresh_timestamp(timestamp):
    return timestamp.strftime("%d %b, %H:%M") if timestamp else "--"


def is_staging_ready():
    bucket = get_gcs_bucket()
    if not bucket:
        return False
    bq = get_metadata_timestamp(bucket, GCS_BQ_REFRESH_METADATA)
    gcs = get_metadata_timestamp(bucket, GCS_GCS_REFRESH_METADATA)
    return bq is not None and (gcs is None or bq > gcs)


def get_cache_info():
    info = {
        "loaded": False, "source": "Not loaded",
        "last_bq_refresh": "--", "last_gcs_refresh": "--",
        "staging_ready": False, "rows": 0,
        "gcs_configured": bool(GCS_BUCKET_NAME),
        "gcs_bucket": GCS_BUCKET_NAME or "Not set"
    }
    try:
        info["last_bq_refresh"] = format_refresh_timestamp(get_last_bq_refresh())
        info["last_gcs_refresh"] = format_refresh_timestamp(get_last_gcs_refresh())
        info["staging_ready"] = is_staging_ready()
        
        if "master_data" in st.session_state and st.session_state.master_data is not None:
            info["loaded"] = True
            info["rows"] = st.session_state.master_data.num_rows
            info["source"] = st.session_state.get("master_data_source", "Session")
        return info
    except Exception as e:
        info["error"] = str(e)
        return info
