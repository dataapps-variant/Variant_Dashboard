"""
Filter Components for Variant Analytics Dashboard
- Date range picker
- BC and Cohort selectors
- Metrics multi-select
- Plans multi-select with quick actions
"""

import streamlit as st
from datetime import timedelta
from config import BC_OPTIONS, COHORT_OPTIONS, METRICS_LIST, METRICS_CONFIG, DEFAULT_BC, DEFAULT_COHORT
from theme import get_theme_colors


def render_filters(plan_groups, min_date, max_date, key_prefix=""):
    """
    Render all filter controls
    
    Args:
        plan_groups: Dict with App_Name and Plan_Name lists
        min_date: Minimum available date
        max_date: Maximum available date
        key_prefix: Unique prefix for widget keys
    
    Returns:
        Tuple of (from_date, to_date, selected_bc, selected_cohort, selected_metrics, selected_plans)
    """
    colors = get_theme_colors()
    
    # Initialize defaults
    default_to = max_date
    default_from = max_date - timedelta(days=365) if max_date else min_date
    if default_from < min_date:
        default_from = min_date
    
    # Filter section header
    st.markdown(f'''
    <div class="filter-title">Filters</div>
    ''', unsafe_allow_html=True)
    
    # Row 1: Date range, BC, Cohort
    col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
    
    with col1:
        from_date = st.date_input(
            "From Date",
            value=default_from,
            min_value=min_date,
            max_value=max_date,
            key=f"{key_prefix}from_date"
        )
    
    with col2:
        to_date = st.date_input(
            "To Date",
            value=default_to,
            min_value=min_date,
            max_value=max_date,
            key=f"{key_prefix}to_date"
        )
    
    with col3:
        selected_bc = st.selectbox(
            "BC",
            options=BC_OPTIONS,
            index=BC_OPTIONS.index(DEFAULT_BC) if DEFAULT_BC in BC_OPTIONS else 0,
            key=f"{key_prefix}bc"
        )
    
    with col4:
        selected_cohort = st.selectbox(
            "Cohort",
            options=COHORT_OPTIONS,
            index=COHORT_OPTIONS.index(DEFAULT_COHORT) if DEFAULT_COHORT in COHORT_OPTIONS else 0,
            key=f"{key_prefix}cohort"
        )
    
    # Row 2: Metrics multi-select
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Default to first 6 metrics
    default_metrics = METRICS_LIST[:6]
    
    selected_metrics = st.multiselect(
        "Metrics",
        options=METRICS_LIST,
        default=default_metrics,
        format_func=lambda x: METRICS_CONFIG.get(x, {}).get("display", x),
        key=f"{key_prefix}metrics"
    )
    
    # Row 3: Plan selection
    st.markdown("<br>", unsafe_allow_html=True)
    
    plan_list = plan_groups.get("Plan_Name", [])
    
    # Group plans by App for better organization
    app_groups = {}
    for i, plan in enumerate(plan_list):
        app = plan_groups["App_Name"][i] if i < len(plan_groups["App_Name"]) else "Unknown"
        if app not in app_groups:
            app_groups[app] = []
        app_groups[app].append(plan)
    
    # Create plan options sorted by app
    plan_options = []
    for app in sorted(app_groups.keys()):
        for plan in sorted(app_groups[app]):
            plan_options.append(plan)
    
    # Default to first 5 plans
    default_plans = plan_options[:5] if plan_options else []
    
    selected_plans = st.multiselect(
        "Plans",
        options=plan_options,
        default=default_plans,
        key=f"{key_prefix}plans"
    )
    
    # Quick select buttons
    col_all, col_clear, col_spacer = st.columns([1, 1, 4])
    
    with col_all:
        if st.button("Select All", key=f"{key_prefix}select_all_plans"):
            st.session_state[f"{key_prefix}plans"] = plan_options
            st.rerun()
    
    with col_clear:
        if st.button("Clear All", key=f"{key_prefix}clear_all_plans"):
            st.session_state[f"{key_prefix}plans"] = []
            st.rerun()
    
    return from_date, to_date, selected_bc, selected_cohort, selected_metrics, selected_plans


def render_app_filter(plan_groups, key_prefix=""):
    """
    Render app-level filter for quick plan selection by app
    
    Args:
        plan_groups: Dict with App_Name and Plan_Name lists
        key_prefix: Unique prefix for widget keys
    
    Returns:
        Selected app name or None for 'All'
    """
    colors = get_theme_colors()
    
    # Get unique apps
    apps = sorted(set(plan_groups.get("App_Name", [])))
    
    if not apps:
        return None
    
    selected_app = st.selectbox(
        "Filter by App",
        options=["All"] + apps,
        key=f"{key_prefix}app_filter"
    )
    
    return None if selected_app == "All" else selected_app
