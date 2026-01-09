"""
Landing Page (Dashboard Hub) for Variant Analytics Dashboard
- Logo + "VARIANT GROUP" + "Welcome back, {username}"
- Dashboard table with clickable names for enabled dashboards
- Centered with max-width
"""

import streamlit as st
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
    
    # Display dashboard table
    st.subheader("📊 Available Dashboards")
    
    # Table header
    header_cols = st.columns([3, 2, 2, 2])
    header_cols[0].markdown(f"**Dashboard**")
    header_cols[1].markdown(f"**Status**")
    header_cols[2].markdown(f"**Last BQ Refresh**")
    header_cols[3].markdown(f"**Last GCS Refresh**")
    
    st.markdown(f"<hr style='margin:5px 0 10px 0;border:none;border-top:1px solid {colors['border']};'>", unsafe_allow_html=True)
    
    # Table rows
    for dashboard in DASHBOARDS:
        is_enabled = dashboard.get("enabled", False)
        status = "✅ Active" if is_enabled else "⏸️ Disabled"
        bq_display = bq_refresh if is_enabled else "--"
        gcs_display = gcs_refresh if is_enabled else "--"
        
        row_cols = st.columns([3, 2, 2, 2])
        
        with row_cols[0]:
            if is_enabled:
                if st.button(dashboard["name"], key=f"nav_{dashboard['id']}"):
                    st.session_state.current_page = dashboard['id']
                    st.rerun()
            else:
                st.markdown(dashboard["name"])
        
        row_cols[1].markdown(status)
        row_cols[2].markdown(bq_display)
        row_cols[3].markdown(gcs_display)
