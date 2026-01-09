"""
Landing Page (Dashboard Hub) for Variant Analytics Dashboard
Table-based dashboard list with centered layout
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
    
    # Centered content
    st.markdown(f'<div style="max-width: 900px; margin: 0 auto;">', unsafe_allow_html=True)
    
    # Logo and header
    render_logo_header(
        size="large",
        show_title=True,
        show_welcome=True,
        username=user['name']
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Dashboard table
    bq_refresh = cache_info.get("last_bq_refresh", "--")
    gcs_refresh = cache_info.get("last_gcs_refresh", "--")
    
    table_rows = ""
    for dashboard in DASHBOARDS:
        is_enabled = dashboard.get("enabled", False)
        cursor = "pointer" if is_enabled else "not-allowed"
        opacity = "1" if is_enabled else "0.6"
        
        bq_display = bq_refresh if is_enabled else "--"
        gcs_display = gcs_refresh if is_enabled else "--"
        
        table_rows += f'''
        <tr style="cursor: {cursor}; opacity: {opacity};" data-dashboard="{dashboard['id']}" data-enabled="{is_enabled}">
            <td style="text-align: left; font-weight: 500;">{dashboard['name']}</td>
            <td style="text-align: center;">{bq_display}</td>
            <td style="text-align: center;">{gcs_display}</td>
        </tr>
        '''
    
    st.markdown(f'''
    <style>
        .landing-table {{
            width: 100%;
            border-collapse: collapse;
            background: {colors['card_bg']};
            border: 1px solid {colors['border']};
            border-radius: 12px;
            overflow: hidden;
        }}
        .landing-table th {{
            background: {colors['table_header_bg']};
            color: {colors['text_primary']};
            font-weight: 600;
            padding: 16px 24px;
            text-align: center;
            border-bottom: 2px solid {colors['border']};
            font-size: 14px;
        }}
        .landing-table td {{
            padding: 16px 24px;
            border-bottom: 1px solid {colors['border']};
            font-size: 14px;
            color: {colors['text_primary']};
        }}
        .landing-table tr:hover {{
            background: {colors['hover']};
        }}
    </style>
    
    <table class="landing-table">
        <thead>
            <tr>
                <th style="text-align: left;">Dashboard Name</th>
                <th>Last Refresh BQ</th>
                <th>Last Refresh GCS</th>
            </tr>
        </thead>
        <tbody>
            {table_rows}
        </tbody>
    </table>
    ''', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Navigation buttons
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f'''
    <p style="text-align: center; color: {colors['text_secondary']}; font-size: 13px;">
        Select a dashboard to open:
    </p>
    ''', unsafe_allow_html=True)
    
    enabled_dashboards = [d for d in DASHBOARDS if d.get("enabled", False)]
    
    if enabled_dashboards:
        cols = st.columns(min(len(enabled_dashboards), 4))
        for idx, dashboard in enumerate(enabled_dashboards):
            with cols[idx % 4]:
                if st.button(
                    f"📊 {dashboard['name']}",
                    key=f"nav_{dashboard['id']}",
                    use_container_width=True
                ):
                    st.session_state.current_page = dashboard['id']
                    st.rerun()
    
    # Check for admin panel
    if st.session_state.get("show_admin_panel", False):
        from admin_panel import render_admin_panel
        render_admin_panel()
