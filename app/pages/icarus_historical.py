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
    load_all_chart_data,
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
    header_col1, header_col2, header_col3 = st.columns([1, 6, 1])
    
    with header_col1:
        if st.button("← Back", key="back_btn"):
            st.session_state.current_page = "landing"
            st.rerun()
    
    with header_col2:
        st.markdown(
            f'<h1 style="text-align:center;font-size:28px;font-weight:700;color:{colors["text_primary"]};margin:0;padding:10px 0;">ICARUS - Plan (Historical)</h1>',
            unsafe_allow_html=True
        )
    
    with header_col3:
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            theme_icon = "☀️" if current_theme == "dark" else "🌙"
            if st.button(theme_icon, key="theme_toggle"):
                toggle_theme()
                st.rerun()
        with btn_col2:
            if st.button("Logout", key="logout_btn"):
                logout()
                st.rerun()
    
    # ==========================================================================
    # REFRESH SECTION
    # ==========================================================================
    refresh_col1, refresh_col2, refresh_col3 = st.columns([1, 4, 1])
    
    with refresh_col1:
        bq_btn_col, bq_txt_col = st.columns([1, 4])
        with bq_btn_col:
            if st.button("🔄", key="refresh_bq"):
                with st.spinner("Querying BigQuery..."):
                    success, msg = refresh_bq_to_staging()
                    if success:
                        st.success(msg)
                    else:
                        st.error(msg)
                    st.rerun()
        with bq_txt_col:
            st.markdown(
                f'<span style="font-size:13px;color:{colors["text_secondary"]};">BQ: {cache_info.get("last_bq_refresh", "--")}</span>',
                unsafe_allow_html=True
            )
    
    with refresh_col3:
        gcs_txt_col, gcs_btn_col = st.columns([4, 1])
        with gcs_txt_col:
            st.markdown(
                f'<span style="font-size:13px;color:{colors["text_secondary"]};text-align:right;display:block;">GCS: {cache_info.get("last_gcs_refresh", "--")}</span>',
                unsafe_allow_html=True
            )
        with gcs_btn_col:
            if st.button("🔄", key="refresh_gcs"):
                with st.spinner("Loading from staging..."):
                    success, msg = refresh_gcs_from_staging()
                    if success:
                        st.success(msg)
                    else:
                        st.error(msg)
                    st.rerun()
    
    # ========
