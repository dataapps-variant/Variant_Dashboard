"""
Filter Components for Variant Analytics Dashboard
"""

import streamlit as st
from config import BC_OPTIONS, COHORT_OPTIONS, METRICS_CONFIG, DEFAULT_BC, DEFAULT_COHORT, DEFAULT_PLAN


def get_plans_by_app(plan_groups):
    """
    Group plans by App_Name
    
    Input: {"App_Name": [...], "Plan_Name": [...]}
    Output: {"AT": ["AT001", "AT002"], "CL": ["CL001"], ...}
    """
    result = {}
    for app, plan in zip(plan_groups["App_Name"], plan_groups["Plan_Name"]):
        if app not in result:
            result[app] = []
        if plan not in result[app]:
            result[app].append(plan)
    return result


def handle_select_all(all_key, item_keys):
    """Handle Select All checkbox behavior"""
    if all_key in st.session_state:
        all_checked = st.session_state[all_key]
        for key in item_keys:
            st.session_state[key] = all_checked


def render_plan_group(app_name, plans, key_prefix=""):
    """Render a single plan group with All checkbox"""
    
    all_key = f"{key_prefix}plan_all_{app_name}"
    item_keys = [f"{key_prefix}plan_{app_name}_{plan}" for plan in plans]
    
    # Initialize session state
    for key in item_keys:
        if key not in st.session_state:
            st.session_state[key] = False
    
    if all_key not in st.session_state:
        st.session_state[all_key] = False
    
    # App name header
    st.markdown(f'<div class="filter-title">{app_name}</div>', unsafe_allow_html=True)
    
    with st.container(height=180):
        # All checkbox
        st.checkbox(
            "All",
            key=all_key,
            on_change=handle_select_all,
            args=(all_key, item_keys)
        )
        
        # Individual checkboxes
        selected = []
        for plan in plans:
            key = f"{key_prefix}plan_{app_name}_{plan}"
            # Set default for JF2788ST
            if plan == DEFAULT_PLAN and key not in st.session_state:
                st.session_state[key] = True
            
            checked = st.checkbox(plan, key=key)
            if checked:
                selected.append(plan)
    
    return selected


def render_metrics_filter(key_prefix=""):
    """Render metrics filter with All checkbox"""
    
    all_key = f"{key_prefix}metrics_all"
    metrics_list = list(METRICS_CONFIG.keys())
    item_keys = [f"{key_prefix}metric_{metric}" for metric in metrics_list]
    
    # Initialize - default all selected
    for key in item_keys:
        if key not in st.session_state:
            st.session_state[key] = True
    
    if all_key not in st.session_state:
        st.session_state[all_key] = True
    
    st.markdown('<div class="filter-title">Metrics</div>', unsafe_allow_html=True)
    
    with st.container(height=350):
        # All checkbox
        st.checkbox(
            "All",
            key=all_key,
            on_change=handle_select_all,
            args=(all_key, item_keys)
        )
        
        # Individual checkboxes
        selected = []
        for metric in metrics_list:
            key = f"{key_prefix}metric_{metric}"
            display_name = METRICS_CONFIG[metric]["display"]
            checked = st.checkbox(display_name, key=key)
            if checked:
                selected.append(metric)
    
    return selected


def render_filters(plan_groups, min_date, max_date, key_prefix=""):
    """
    Render all filters in collapsible container
    
    Returns: (from_date, to_date, selected_bc, selected_cohort, selected_metrics, selected_plans)
    """
    
    # Group plans by App
    plans_by_app = get_plans_by_app(plan_groups)
    app_names = sorted(plans_by_app.keys())
    
    selected_plans = []
    
    # Create expander for filters
    with st.expander("📊 Filters", expanded=True):
        
        # Row 1: Date Range, BC, Cohort, Reset
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        
        with col1:
            st.markdown('<div class="filter-title">Date Range</div>', unsafe_allow_html=True)
            date_cols = st.columns(2)
            with date_cols[0]:
                from_date = st.date_input(
                    "From",
                    value=min_date,
                    min_value=min_date,
                    max_value=max_date,
                    key=f"{key_prefix}from_date",
                    label_visibility="collapsed"
                )
            with date_cols[1]:
                to_date = st.date_input(
                    "To",
                    value=max_date,
                    min_value=min_date,
                    max_value=max_date,
                    key=f"{key_prefix}to_date",
                    label_visibility="collapsed"
                )
        
        with col2:
            st.markdown('<div class="filter-title">Billing Cycle</div>', unsafe_allow_html=True)
            selected_bc = st.selectbox(
                "BC",
                options=BC_OPTIONS,
                index=BC_OPTIONS.index(DEFAULT_BC),
                key=f"{key_prefix}bc",
                label_visibility="collapsed"
            )
        
        with col3:
            st.markdown('<div class="filter-title">Cohort</div>', unsafe_allow_html=True)
            selected_cohort = st.selectbox(
                "Cohort",
                options=COHORT_OPTIONS,
                index=COHORT_OPTIONS.index(DEFAULT_COHORT),
                key=f"{key_prefix}cohort",
                label_visibility="collapsed"
            )
        
        with col4:
            st.markdown('<div class="filter-title">&nbsp;</div>', unsafe_allow_html=True)
            if st.button("🔄 Reset", key=f"{key_prefix}reset_btn", use_container_width=True):
                reset_filters(plan_groups, key_prefix)
                st.rerun()
        
        st.markdown("---")
        
        # Row 2: Plan Groups + Metrics
        # Calculate columns: up to 6 app columns + 1 metrics column
        num_apps = len(app_names)
        apps_per_row = min(6, num_apps)
        
        # Plans section header
        st.markdown('<div class="filter-title">Plan Groups</div>', unsafe_allow_html=True)
        
        # Create columns for apps
        main_cols = st.columns([4, 1])
        
        with main_cols[0]:
            # Render app groups in rows of 6
            for row_start in range(0, num_apps, 6):
                row_apps = app_names[row_start:row_start + 6]
                cols = st.columns(6)
                
                for i, app_name in enumerate(row_apps):
                    with cols[i]:
                        plans = sorted(plans_by_app.get(app_name, []))
                        selected = render_plan_group(app_name, plans, key_prefix)
                        selected_plans.extend(selected)
        
        with main_cols[1]:
            selected_metrics = render_metrics_filter(key_prefix)
    
    return from_date, to_date, selected_bc, selected_cohort, selected_metrics, selected_plans


def reset_filters(plan_groups, key_prefix=""):
    """Reset all filters to default values"""
    
    # Reset plan selections
    plans_by_app = get_plans_by_app(plan_groups)
    for app_name, plans in plans_by_app.items():
        all_key = f"{key_prefix}plan_all_{app_name}"
        if all_key in st.session_state:
            st.session_state[all_key] = False
        
        for plan in plans:
            key = f"{key_prefix}plan_{app_name}_{plan}"
            if key in st.session_state:
                st.session_state[key] = (plan == DEFAULT_PLAN)
    
    # Reset metrics to all selected
    for metric in METRICS_CONFIG.keys():
        key = f"{key_prefix}metric_{metric}"
        if key in st.session_state:
            st.session_state[key] = True
    
    all_key = f"{key_prefix}metrics_all"
    if all_key in st.session_state:
        st.session_state[all_key] = True
