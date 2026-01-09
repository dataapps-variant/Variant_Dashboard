"""
ICARUS - Plan (Historical) Dashboard Page
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
    load_chart_data,
    clear_all_cache,
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
    
    # ==========================================================================
    # SCROLL ANCHOR (for scroll to top button)
    # ==========================================================================
    st.markdown('<div id="top"></div>', unsafe_allow_html=True)
    
    # ==========================================================================
    # HEADER
    # ==========================================================================
    header_col1, header_col2 = st.columns([4, 1])
    
    with header_col1:
        col_back, col_title = st.columns([0.5, 4])
        
        with col_back:
            if st.button("← Back", key="back_btn"):
                st.session_state.current_page = "landing"
                st.rerun()
        
        with col_title:
            st.markdown(f'''
            <h1 style="
                font-size: 24px;
                font-weight: 600;
                color: {colors['text_primary']};
                margin: 0;
            ">ICARUS - Plan (Historical)</h1>
            ''', unsafe_allow_html=True)
    
    with header_col2:
        with st.popover("⋮"):
            st.markdown("**Data Settings**")
            
            # Refresh button
            if st.button("🔄 Refresh Data", use_container_width=True, key="refresh_btn"):
                clear_all_cache()
                st.success("Cache cleared!")
                st.rerun()
            
            st.markdown("---")
            
            # Theme toggle
            theme_icon = "☀️" if current_theme == "dark" else "🌙"
            theme_text = "Light Mode" if current_theme == "dark" else "Dark Mode"
            if st.button(f"{theme_icon} {theme_text}", use_container_width=True, key="theme_toggle"):
                toggle_theme()
                st.rerun()
            
            st.markdown("---")
            
            # Cache Status
            st.markdown("**📊 Cache Status:**")
            cache_info = get_cache_info()
            
            if cache_info.get("loaded"):
                st.markdown(f"✅ **Data Loaded**")
                st.markdown(f"📦 Source: `{cache_info.get('source', 'Unknown')}`")
                st.markdown(f"📊 Rows: {cache_info.get('rows', 0):,}")
                
                if cache_info.get("last_updated"):
                    try:
                        last_updated = datetime.fromisoformat(cache_info["last_updated"])
                        age_minutes = (datetime.now() - last_updated).total_seconds() / 60
                        st.markdown(f"⏱️ Age: {age_minutes:.0f} min")
                    except:
                        pass
            else:
                st.markdown(f"⚠️ **Data Not Loaded**")
            
            st.markdown("---")
            
            # GCS Status
            st.markdown("**☁️ GCS Cache:**")
            if cache_info.get("gcs_configured"):
                st.markdown(f"✅ Configured")
                if cache_info.get("gcs_available"):
                    if cache_info.get("gcs_age_hours") is not None:
                        st.markdown(f"📁 Age: {cache_info.get('gcs_age_hours')}h")
                else:
                    st.markdown(f"⚠️ Not accessible")
            else:
                st.markdown(f"❌ Not Configured")
            
            st.markdown("---")
            
            st.markdown(f"**User:** {user['name']}")
            
            if st.button("🚪 Logout", use_container_width=True, key="logout_btn"):
                logout()
                st.rerun()
    
    # ==========================================================================
    # DATA SOURCE INDICATOR
    # ==========================================================================
    cache_info = get_cache_info()
    if cache_info.get("loaded"):
        source = cache_info.get("source", "Unknown")
        if source == "BigQuery":
            st.info(f"📊 Data loaded from **BigQuery** (first load)")
        elif source == "GCS":
            st.success(f"⚡ Data loaded from **GCS Cache** (fast!)")
    
    # ==========================================================================
    # TABS
    # ==========================================================================
    tab_active, tab_inactive = st.tabs(["📈 Active", "📉 Inactive"])
    
    with tab_active:
        render_dashboard_content("Active", "active_")
    
    with tab_inactive:
        render_dashboard_content("Inactive", "inactive_")
    
    # ==========================================================================
    # FLOATING SCROLL TO TOP BUTTON
    # ==========================================================================
    st.markdown(f'''
    <style>
    .scroll-top-btn {{
        position: fixed;
        bottom: 30px;
        right: 30px;
        z-index: 9999;
        background: {colors['accent']};
        color: white;
        border: none;
        border-radius: 50%;
        width: 50px;
        height: 50px;
        font-size: 20px;
        cursor: pointer;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        transition: all 0.3s ease;
    }}
    .scroll-top-btn:hover {{
        background: {colors['accent_hover']};
        transform: translateY(-3px);
    }}
    </style>
    <a href="#top">
        <button class="scroll-top-btn">⬆️</button>
    </a>
    ''', unsafe_allow_html=True)


def render_dashboard_content(active_inactive, key_prefix):
    """Render dashboard content for Active or Inactive tab"""
    
    colors = get_theme_colors()
    
    # ==========================================================================
    # LOAD DATA
    # ==========================================================================
    try:
        date_bounds = load_date_bounds()
        min_date = date_bounds["min_date"]
        max_date = date_bounds["max_date"]
    except Exception as e:
        st.error(f"Error loading date bounds: {str(e)}")
        st.info("Check BigQuery connection and GCS bucket configuration.")
        return
    
    try:
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
        from_date,
        to_date,
        selected_bc,
        selected_cohort,
        selected_metrics,
        selected_plans
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
    # PIVOT TABLES (with AG Grid features)
    # ==========================================================================
    st.markdown("<br>", unsafe_allow_html=True)
    
    try:
        pivot_data_regular = load_pivot_data(
            from_date, to_date, selected_bc, selected_cohort,
            selected_plans, selected_metrics, "Regular", active_inactive
        )
        render_pivot_table(pivot_data_regular, selected_metrics, "📊 Plan Overview (Regular)", f"{key_prefix}regular")
    except Exception as e:
        st.error(f"Error loading Regular pivot data: {str(e)}")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    try:
        pivot_data_crystal = load_pivot_data(
            from_date, to_date, selected_bc, selected_cohort,
            selected_plans, selected_metrics, "Crystal Ball", active_inactive
        )
        render_pivot_table(pivot_data_crystal, selected_metrics, "🔮 Plan Overview (Crystal Ball)", f"{key_prefix}crystal")
    except Exception as e:
        st.error(f"Error loading Crystal Ball pivot data: {str(e)}")
    
    # ==========================================================================
    # CHARTS
    # ==========================================================================
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f'''
    <div style="
        font-size: 18px;
        font-weight: 600;
        color: {colors['text_primary']};
        margin: 20px 0;
    ">📈 Trend Charts</div>
    ''', unsafe_allow_html=True)
    
    # Prepare date range for x-axis
    date_range = (from_date, to_date)
    
    for idx, chart_config in enumerate(CHART_METRICS):
        display_name = chart_config["display"]
        metric = chart_config["metric"]
        format_type = chart_config["format"]
        
        # Add format suffix to display name
        if format_type == "dollar":
            display_title = f"{display_name} ($)"
        elif format_type == "percent":
            display_title = f"{display_name} (%)"
        else:
            display_title = display_name
        
        try:
            # Load chart data
            chart_data_regular = load_chart_data(
                from_date, to_date, selected_bc, selected_cohort,
                selected_plans, metric, "Regular", active_inactive
            )
            
            chart_data_crystal = load_chart_data(
                from_date, to_date, selected_bc, selected_cohort,
                selected_plans, metric, "Crystal Ball", active_inactive
            )
            
            # Create unique key for this chart pair
            chart_key = f"{key_prefix}chart_{idx}_{metric}"
            
            # Render chart pair with date range and unique key
            render_chart_pair(
                chart_data_regular, 
                chart_data_crystal, 
                display_title, 
                format_type,
                date_range=date_range,
                chart_key=chart_key
            )
            
        except Exception as e:
            st.error(f"Error loading chart data for {display_name}: {str(e)}")
        
        st.markdown("<br>", unsafe_allow_html=True)
