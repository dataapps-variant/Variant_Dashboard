"""
Landing Page (Dashboard Hub) for Variant Analytics Dashboard
- Logo + "VARIANT GROUP" + "Welcome back, {username}"
- Dashboard table using Streamlit components
- Centered with max-width
- Disabled dashboards: same appearance, cursor: not-allowed
- Settings menu (⋮) with Light Mode toggle, Admin Panel (admin only), User info, Logout

FIXED: Using Streamlit native components instead of raw HTML tables
"""

import streamlit as st
import pandas as pd
from auth import get_current_user, logout, is_admin
from theme import get_theme_colors, toggle_theme, get_current_theme, render_logo_header
from config import DASHBOARDS
from bigquery_client import get_cache_info


def render_landing_page():
    """Render the landing page with dashboard table"""
    
    colors = get_theme_colors()
    current_theme = get_current_theme()
    user = get_current_user()
    cache_info = get_cache_info()
    
    # Top right menu
    col_spacer, col_menu = st.columns([12, 1])
    with col_menu:
        with st.popover("⋮"):
            # Theme toggle
            theme_icon = "☀️" if current_theme == "dark" else "🌙"
            theme_text = "Light Mode" if current_theme == "dark" else "Dark Mode"
            if st.button(f"{theme_icon} {theme_text}", use_container_width=True, key="theme_toggle"):
                toggle_theme()
                st.rerun()
            
            # Admin Panel (admin only)
            if is_admin():
                st.markdown("---")
                if st.button("🔧 Admin Panel", use_container_width=True, key="admin_btn"):
                    st.session_state.show_admin_panel = True
                    st.rerun()
            
            st.markdown("---")
            st.markdown(f"**User:** {user['name']}")
            st.markdown(f"**Role:** {'Admin' if user['role'] == 'admin' else 'Read Only'}")
            
            st.markdown("---")
            if st.button("🚪 Logout", use_container_width=True, key="logout_btn"):
                logout()
                st.rerun()
    
    # Logo and header with welcome message
    render_logo_header(
        size="large",
        show_title=True,
        show_welcome=True,
        username=user['name']
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Dashboard info
    bq_refresh = cache_info.get("last_bq_refresh", "--")
    gcs_refresh = cache_info.get("last_gcs_refresh", "--")
    
    # Build dashboard data
    dashboard_data = []
    for dashboard in DASHBOARDS:
        is_enabled = dashboard.get("enabled", False)
        status = "✅ Active" if is_enabled else "⏸️ Disabled"
        bq_display = bq_refresh if is_enabled else "--"
        gcs_display = gcs_refresh if is_enabled else "--"
        
        dashboard_data.append({
            "Dashboard": dashboard["name"],
            "Status": status,
            "Last BQ Refresh": bq_display,
            "Last GCS Refresh": gcs_display
        })
    
    # Display dashboard table
    st.subheader("📊 Available Dashboards")
    
    df = pd.DataFrame(dashboard_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Navigation section
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        f'<p style="text-align:center;color:{colors["text_secondary"]};font-size:14px;">Click a button below to open a dashboard:</p>',
        unsafe_allow_html=True
    )
    
    # Filter enabled dashboards
    enabled_dashboards = [d for d in DASHBOARDS if d.get("enabled", False)]
    disabled_dashboards = [d for d in DASHBOARDS if not d.get("enabled", False)]
    
    if enabled_dashboards:
        # Create columns for enabled dashboards
        num_cols = min(len(enabled_dashboards), 4)
        cols = st.columns(num_cols)
        
        for idx, dashboard in enumerate(enabled_dashboards):
            with cols[idx % num_cols]:
                if st.button(
                    f"📊 {dashboard['name']}",
                    key=f"nav_{dashboard['id']}",
                    use_container_width=True,
                    type="primary"
                ):
                    st.session_state.current_page = dashboard['id']
                    st.rerun()
    else:
        st.info("No dashboards are currently enabled.")
    
    # Show disabled dashboards info
    if disabled_dashboards:
        st.markdown("<br>", unsafe_allow_html=True)
        st.caption("Disabled dashboards:")
        disabled_names = ", ".join([d["name"] for d in disabled_dashboards])
        st.caption(disabled_names)
