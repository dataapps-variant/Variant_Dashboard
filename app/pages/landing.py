"""
Landing Page (Dashboard Hub) for Variant Analytics Dashboard
"""

import streamlit as st
from auth import get_current_user, logout, is_admin, get_ordered_dashboards, set_user_dashboard_order
from theme import get_theme_colors, toggle_theme, get_current_theme
from config import APP_NAME


def render_landing_page():
    """Render the landing page with dashboard cards"""
    
    colors = get_theme_colors()
    current_theme = get_current_theme()
    user = get_current_user()
    dashboards = get_ordered_dashboards()
    
    # Initialize edit mode
    if "edit_mode" not in st.session_state:
        st.session_state.edit_mode = False
    
    # Header
    header_col1, header_col2 = st.columns([4, 1])
    
    with header_col1:
        st.markdown(f'''
        <div style="display: flex; align-items: center; gap: 16px;">
            <span style="font-size: 32px;">📊</span>
            <div>
                <h1 style="
                    font-size: 24px;
                    font-weight: 600;
                    color: {colors['text_primary']};
                    margin: 0;
                ">{APP_NAME}</h1>
                <p style="
                    font-size: 14px;
                    color: {colors['text_secondary']};
                    margin: 0;
                ">Welcome back, {user['name']}</p>
            </div>
        </div>
        ''', unsafe_allow_html=True)
    
    with header_col2:
        col_edit, col_menu = st.columns([1, 1])
        
        with col_edit:
            if st.button("✏️ Edit", use_container_width=True, key="edit_btn"):
                st.session_state.edit_mode = not st.session_state.edit_mode
                st.rerun()
        
        with col_menu:
            with st.popover("⋮"):
                st.markdown("**Settings**")
                
                # Theme toggle
                theme_icon = "☀️" if current_theme == "dark" else "🌙"
                theme_text = "Light Mode" if current_theme == "dark" else "Dark Mode"
                if st.button(f"{theme_icon} {theme_text}", use_container_width=True, key="theme_toggle"):
                    toggle_theme()
                    st.rerun()
                
                st.markdown("---")
                
                # User info
                st.markdown(f"**User:** {user['name']}")
                st.markdown(f"**Role:** {user['role'].title()}")
                
                st.markdown("---")
                
                # Logout
                if st.button("🚪 Logout", use_container_width=True, key="logout_btn"):
                    logout()
                    st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Edit mode banner
    if st.session_state.edit_mode:
        st.info("📝 **Edit Mode:** Drag and drop cards to reorder. Click 'Save Order' when done.")
        
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("💾 Save Order", use_container_width=True):
                # Save current order
                current_order = [d["id"] for d in dashboards]
                set_user_dashboard_order(current_order)
                st.session_state.edit_mode = False
                st.success("Order saved!")
                st.rerun()
    
    # Dashboard cards
    st.markdown(f'''
    <h2 style="
        font-size: 18px;
        font-weight: 600;
        color: {colors['text_primary']};
        margin-bottom: 20px;
    ">Your Dashboards</h2>
    ''', unsafe_allow_html=True)
    
    # Create grid of cards (4 per row)
    num_cols = 4
    rows = [dashboards[i:i + num_cols] for i in range(0, len(dashboards), num_cols)]
    
    for row in rows:
        cols = st.columns(num_cols)
        
        for idx, dashboard in enumerate(row):
            with cols[idx]:
                render_dashboard_card(dashboard, colors)
        
        # Fill empty columns in last row
        for idx in range(len(row), num_cols):
            with cols[idx]:
                st.empty()
    
    # Admin section
    if is_admin():
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("---")
        
        with st.expander("🔧 Admin Panel"):
            render_admin_panel(colors)


def render_dashboard_card(dashboard, colors):
    """Render a single dashboard card"""
    
    is_enabled = dashboard.get("enabled", False)
    opacity = "1" if is_enabled else "0.5"
    cursor = "pointer" if is_enabled else "not-allowed"
    
    # Card click handler
    if is_enabled:
        if st.button(
            f"{dashboard['icon']}\n\n{dashboard['name']}",
            key=f"card_{dashboard['id']}",
            use_container_width=True,
            help=f"Open {dashboard['name']}"
        ):
            st.session_state.current_page = dashboard['id']
            st.rerun()
    else:
        st.markdown(f'''
        <div style="
            background: {colors['card_bg']};
            border: 1px solid {colors['border']};
            border-radius: 12px;
            padding: 24px;
            text-align: center;
            opacity: {opacity};
            cursor: {cursor};
            min-height: 120px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
        ">
            <div style="font-size: 32px; margin-bottom: 12px;">{dashboard['icon']}</div>
            <div style="
                font-size: 14px;
                font-weight: 600;
                color: {colors['text_primary']};
            ">{dashboard['name']}</div>
            <div style="
                font-size: 11px;
                color: {colors['text_secondary']};
                margin-top: 8px;
            ">Coming Soon</div>
        </div>
        ''', unsafe_allow_html=True)


def render_admin_panel(colors):
    """Render admin panel for user management"""
    
    from auth import get_all_users, add_user, delete_user, update_user
    from config import DASHBOARDS
    
    st.markdown("### User Management")
    
    # Get all users
    users = get_all_users()
    
    # Display users table
    st.markdown("**Current Users:**")
    
    for username, user_data in users.items():
        with st.container():
            col1, col2, col3, col4 = st.columns([2, 2, 3, 1])
            
            with col1:
                st.text(f"👤 {username}")
            
            with col2:
                role_badge = "🔑 Admin" if user_data["role"] == "admin" else "👁️ Viewer"
                st.text(role_badge)
            
            with col3:
                if user_data["dashboards"] == "all":
                    st.text("All dashboards")
                else:
                    st.text(f"{len(user_data['dashboards'])} dashboards")
            
            with col4:
                if username != "admin":
                    if st.button("🗑️", key=f"delete_{username}", help=f"Delete {username}"):
                        success, msg = delete_user(username)
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
    
    st.markdown("---")
    
    # Add new user form
    st.markdown("**Add New User:**")
    
    with st.form("add_user_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_username = st.text_input("Username")
            new_password = st.text_input("Password", type="password")
        
        with col2:
            new_role = st.selectbox("Role", ["viewer", "admin"])
            new_name = st.text_input("Display Name")
        
        # Dashboard selection for viewers
        if new_role == "viewer":
            st.markdown("**Assign Dashboards:**")
            selected_dashboards = []
            cols = st.columns(3)
            for idx, dashboard in enumerate(DASHBOARDS):
                with cols[idx % 3]:
                    if st.checkbox(dashboard["name"], key=f"new_dash_{dashboard['id']}"):
                        selected_dashboards.append(dashboard["id"])
        else:
            selected_dashboards = "all"
        
        if st.form_submit_button("Add User"):
            if new_username and new_password and new_name:
                dashboards = selected_dashboards if new_role == "viewer" else "all"
                success, msg = add_user(new_username, new_password, new_role, new_name, dashboards)
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
            else:
                st.warning("Please fill all fields")
