"""
ICARUS - Plan (Historical) Dashboard Page - OPTIMIZED VERSION

Key optimizations:
1. Batch loading for all chart data (1 query instead of 20)
2. Lazy loading with tabs
3. Reduced re-renders
"""

import streamlit as st
from datetime import datetime

from auth import get_current_user, logout
from theme import get_theme_colors, toggle_theme, get_current_theme
from config import CHART_METRICS
from bigquery_client import (
    load_date_bounds,
    load_plan_groups,
    load_pivot_data,
    load_all_chart_data,  # NEW: Batch loading function
    refresh_bq_to_staging,
    refresh_gcs_from_staging,
    get_cache_info
)
from filters import render_filters
from pivots import render_pivot_table
from charts import render_chart_pair


def render_icarus_historical():
    """Render the ICARUS Historical dashboard"""
    
    colors = get_theme_colors()
    current_theme = get_current_theme()
    user = get_current_user()
    cache_info = get_cache_info()
    
    # ==========================================================================
    # HEADER
    # ==========================================================================
    header_col1, header_col2, header_col3 = st.columns([1, 4, 1])
    
    with header_col1:
        if st.button("← Back", key="back_btn"):
            st.session_state.current_page = "landing"
            st.rerun()
    
    with header_col2:
        st.markdown(
            f'<h1 style="text-align:center;font-size:22px;font-weight:600;color:{colors["text_primary"]};margin:0;padding:10px 0;">ICARUS - Plan (Historical)</h1>',
            unsafe_allow_html=True
        )
    
    with header_col3:
        with st.popover("⋮"):
            st.markdown("**Export**")
            if st.button("📄 Export Full Dashboard as PDF", use_container_width=True, key="export_pdf"):
                st.info("PDF export - Coming soon")
            
            st.markdown("---")
            theme_icon = "☀️" if current_theme == "dark" else "🌙"
            theme_text = "Light Mode" if current_theme == "dark" else "Dark Mode"
            if st.button(f"{theme_icon} {theme_text}", use_container_width=True, key="theme_toggle"):
                toggle_theme()
                st.rerun()
            
            st.markdown("---")
            st.markdown(f"**User:** {user['name']}")
            if st.button("🚪 Logout", use_container_width=True, key="logout_btn"):
                logout()
                st.rerun()
    
    # ==========================================================================
    # REFRESH SECTION
    # ==========================================================================
    st.markdown("<br>", unsafe_allow_html=True)
    
    refresh_col1, refresh_col2 = st.columns([3, 2])
    
    with refresh_col2:
        with st.container():
            st.markdown("**🔄 Data Refresh**")
            
            bq_col1, bq_col2 = st.columns([1, 1])
            with bq_col1:
                if st.button("Refresh BQ", key="refresh_bq", use_container_width=True):
                    with st.spinner("Querying BigQuery..."):
                        success, msg = refresh_bq_to_staging()
                        if success:
                            st.success(msg)
                        else:
                            st.error(msg)
                        st.rerun()
            with bq_col2:
                st.caption(f"Last: {cache_info.get('last_bq_refresh', '--')}")
            
            gcs_col1, gcs_col2 = st.columns([1, 1])
            with gcs_col1:
                if st.button("Refresh GCS", key="refresh_gcs", use_container_width=True):
                    with st.spinner("Loading from staging..."):
                        success, msg = refresh_gcs_from_staging()
                        if success:
                            st.success(msg)
                        else:
                            st.error(msg)
                        st.rerun()
            with gcs_col2:
                st.caption(f"Last: {cache_info.get('last_gcs_refresh', '--')}")
    
    # ==========================================================================
    # TABS
    # ==========================================================================
    st.markdown("<br>", unsafe_allow_html=True)
    
    tab_active, tab_inactive = st.tabs(["📈 Active", "📉 Inactive"])
    
    with tab_active:
        render_dashboard_content_optimized("Active", "active_")
    
    with tab_inactive:
        render_dashboard_content_optimized("Inactive", "inactive_")


def render_dashboard_content_optimized(active_inactive, key_prefix):
    """
    OPTIMIZED dashboard content rendering:
    1. Single data load for all charts
    2. Progressive rendering
    3. Better caching
    """
    
    colors = get_theme_colors()
    
    # ==========================================================================
    # LOAD INITIAL DATA (cached)
    # ==========================================================================
    try:
        with st.spinner("Loading data bounds..."):
            date_bounds = load_date_bounds()
            min_date = date_bounds["min_date"]
            max_date = date_bounds["max_date"]
    except Exception as e:
        st.error(f"Error loading date bounds: {str(e)}")
        return
    
    try:
        with st.spinner("Loading plan groups..."):
            plan_groups = load_plan_groups(active_inactive)
            if not plan_groups["Plan_Name"]:
                st.warning(f"No {active_inactive.lower()} plans found.")
                return
    except Exception as e:
        st.error(f"Error loading plan groups: {str(e)}")
        return
    
    # ==========================================================================
    # FILTERS
    # ==========================================================================
    (
        from_date, to_date, selected_bc, selected_cohort,
        selected_metrics, selected_plans
    ) = render_filters(plan_groups, min_date, max_date, key_prefix)
    
    # ==========================================================================
    # VALIDATION
    # ==========================================================================
    if not selected_metrics:
        st.warning("⚠️ Please select at least one Metric.")
        return
    
    if not selected_plans:
        st.warning("⚠️ Please select at least one Plan.")
        return
    
    # ==========================================================================
    # PIVOT TABLES (in expander for lazy loading)
    # ==========================================================================
    st.markdown("<br>", unsafe_allow_html=True)
    
    with st.expander("📊 Pivot Tables", expanded=True):
        pivot_col1, pivot_col2 = st.columns(2)
        
        with pivot_col1:
            try:
                pivot_data_regular = load_pivot_data(
                    from_date, to_date, selected_bc, selected_cohort,
                    selected_plans, selected_metrics, "Regular", active_inactive
                )
                render_pivot_table(
                    pivot_data_regular, selected_metrics, 
                    "📊 Regular", f"{key_prefix}regular"
                )
            except Exception as e:
                st.error(f"Error: {str(e)}")
        
        with pivot_col2:
            try:
                pivot_data_crystal = load_pivot_data(
                    from_date, to_date, selected_bc, selected_cohort,
                    selected_plans, selected_metrics, "Crystal Ball", active_inactive
                )
                render_pivot_table(
                    pivot_data_crystal, selected_metrics,
                    "🔮 Crystal Ball", f"{key_prefix}crystal"
                )
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    # ==========================================================================
    # CHARTS - BATCH LOADING (MAJOR OPTIMIZATION)
    # ==========================================================================
    st.markdown("<br>", unsafe_allow_html=True)
    
    with st.expander("📈 Charts", expanded=True):
        # Extract metric names from CHART_METRICS
        chart_metric_names = [cm["metric"] for cm in CHART_METRICS]
        
        # SINGLE batch load for ALL Regular charts
        with st.spinner("Loading chart data..."):
            try:
                all_regular_data = load_all_chart_data(
                    from_date, to_date, selected_bc, selected_cohort,
                    selected_plans, chart_metric_names, "Regular", active_inactive
                )
                
                all_crystal_data = load_all_chart_data(
                    from_date, to_date, selected_bc, selected_cohort,
                    selected_plans, chart_metric_names, "Crystal Ball", active_inactive
                )
            except Exception as e:
                st.error(f"Error loading chart data: {str(e)}")
                return
        
        date_range = (from_date, to_date)
        
        # Render charts using pre-loaded data
        for idx, chart_config in enumerate(CHART_METRICS):
            display_name = chart_config["display"]
            metric = chart_config["metric"]
            format_type = chart_config["format"]
            
            if format_type == "dollar":
                display_title = f"{display_name} ($)"
            elif format_type == "percent":
                display_title = f"{display_name} (%)"
            else:
                display_title = display_name
            
            # Get pre-loaded data (no additional query!)
            chart_data_regular = all_regular_data.get(metric, {"Plan_Name": [], "Reporting_Date": [], "metric_value": []})
            chart_data_crystal = all_crystal_data.get(metric, {"Plan_Name": [], "Reporting_Date": [], "metric_value": []})
            
            chart_key = f"{key_prefix}chart_{idx}_{metric}"
            
            render_chart_pair(
                chart_data_regular,
                chart_data_crystal,
                display_title,
                format_type,
                date_range=date_range,
                chart_key=chart_key
            )
            
            st.markdown("<br>", unsafe_allow_html=True)
