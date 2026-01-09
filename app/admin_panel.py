"""
Admin Panel - Full Screen Modal
- Users management table
- Dashboard access table (Read Only users only)
- Add new user form (collapsible)
"""

import streamlit as st
from auth import (
    get_all_users, add_user, delete_user, update_user,
    get_role_display, get_readonly_users_for_dashboard
)
from theme import get_theme_colors, render_logo_header
from config import DASHBOARDS, ROLE_OPTIONS, ROLE_DISPLAY


def render_admin_panel():
    """Render the admin panel as a full-screen modal"""
    
    colors = get_theme_colors()
    
    # Close button at top right
    col_spacer, col_close = st.columns([12, 1])
    with col_close:
        if st.button("✕ Close", key="close_admin"):
            st.session_state.show_admin_panel = False
            st.rerun()
    
    # Centered content wrapper
    st.markdown(f'<div style="max-width: 1000px; margin: 0 auto;">', unsafe_allow_html=True)
    
    # Logo and header
    render_logo_header(size="large", show_title=True, show_welcome=False)
    
    st.markdown(f'''
    <h2 style="
        text-align: center;
        color: {colors['text_primary']};
        font-size: 20px;
        font-weight: 600;
        margin: 0 0 40px 0;
    ">Admin Panel</h2>
    ''', unsafe_allow_html=True)
    
    # Users Section
    render_users_section(colors)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Dashboard Access Section
    render_dashboard_access_section(colors)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Add New User Section
    render_add_user_section(colors)
    
    # Close centered wrapper
    st.markdown('</div>', unsafe_allow_html=True)


def render_users_section(colors):
    """Render the users table with edit/delete actions"""
    
    st.markdown(f'''
    <h3 style="
        color: {colors['text_primary']};
        font-size: 16px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 16px;
    ">Users</h3>
    ''', unsafe_allow_html=True)
    
    users = get_all_users()
    
    # Build table HTML
    table_rows = ""
    for user_id, user_data in users.items():
        role_display = get_role_display(user_data["role"])
        table_rows += f'''
        <tr>
            <td style="text-align: left;">{user_data["name"]}</td>
            <td style="text-align: left;">{user_id}</td>
            <td style="text-align: center;">••••••••</td>
            <td style="text-align: center;">{role_display}</td>
            <td style="text-align: center;">—</td>
        </tr>
        '''
    
    st.markdown(f'''
    <style>
        .admin-table {{
            width: 100%;
            border-collapse: collapse;
            background: {colors['card_bg']};
            border: 1px solid {colors['border']};
            border-radius: 12px;
            overflow: hidden;
        }}
        .admin-table th {{
            background: {colors['table_header_bg']};
            color: {colors['text_primary']};
            font-weight: 600;
            padding: 14px 20px;
            text-align: center;
            border-bottom: 2px solid {colors['border']};
            font-size: 13px;
        }}
        .admin-table td {{
            padding: 12px 20px;
            border-bottom: 1px solid {colors['border']};
            font-size: 14px;
            color: {colors['text_primary']};
        }}
        .admin-table tr:hover {{
            background: {colors['hover']};
        }}
    </style>
    
    <table class="admin-table">
        <thead>
            <tr>
                <th style="text-align: left;">User Name</th>
                <th style="text-align: left;">User ID</th>
                <th>Password</th>
                <th>Role</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
            {table_rows}
        </tbody>
    </table>
    ''', unsafe_allow_html=True)
    
    # Action buttons using Streamlit (HTML buttons don't work)
    st.markdown("<br>", unsafe_allow_html=True)
    
    user_list = list(users.keys())
    if user_list:
        # Create columns for each user's actions
        num_cols = min(len(user_list), 6)
        cols = st.columns(num_cols)
        for idx, user_id in enumerate(user_list):
            with cols[idx % num_cols]:
                st.markdown(f"**{user_id}**")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✏️", key=f"edit_{user_id}", help=f"Edit {user_id}"):
                        st.session_state.editing_user = user_id
                        st.rerun()
                with col2:
                    if user_id != "admin":
                        if st.button("🗑️", key=f"del_{user_id}", help=f"Delete {user_id}"):
                            success, msg = delete_user(user_id)
                            if success:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)
    
    # Edit user form (if editing)
    if st.session_state.get("editing_user"):
        render_edit_user_form(colors)


def render_edit_user_form(colors):
    """Render form to edit existing user"""
    
    user_id = st.session_state.editing_user
    users = get_all_users()
    
    if user_id not in users:
        st.session_state.editing_user = None
        return
    
    user_data = users[user_id]
    
    st.markdown("---")
    st.markdown(f"**Editing User: {user_id}**")
    
    with st.form(f"edit_form_{user_id}"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_name = st.text_input("User Name", value=user_data["name"])
            new_password = st.text_input("New Password (leave blank to keep)", type="password")
        
        with col2:
            current_role_idx = ROLE_OPTIONS.index(user_data["role"]) if user_data["role"] in ROLE_OPTIONS else 0
            new_role = st.selectbox(
                "Role",
                options=ROLE_OPTIONS,
                index=current_role_idx,
                format_func=lambda x: ROLE_DISPLAY.get(x, x)
            )
            
            # Dashboard selection for readonly only
            if new_role == "readonly":
                current_dashboards = user_data.get("dashboards", [])
                if current_dashboards == "all":
                    current_dashboards = [d["id"] for d in DASHBOARDS]
                
                new_dashboards = st.multiselect(
                    "Dashboard Access",
                    options=[d["id"] for d in DASHBOARDS],
                    default=current_dashboards,
                    format_func=lambda x: next((d["name"] for d in DASHBOARDS if d["id"] == x), x)
                )
            else:
                new_dashboards = "all"
        
        col_save, col_cancel = st.columns(2)
        with col_save:
            if st.form_submit_button("💾 Save Changes", use_container_width=True):
                kwargs = {"name": new_name, "role": new_role}
                if new_password:
                    kwargs["password"] = new_password
                if new_role == "readonly":
                    kwargs["dashboards"] = new_dashboards
                
                success, msg = update_user(user_id, **kwargs)
                if success:
                    st.success(msg)
                    st.session_state.editing_user = None
                    st.rerun()
                else:
                    st.error(msg)
        
        with col_cancel:
            if st.form_submit_button("Cancel", use_container_width=True):
                st.session_state.editing_user = None
                st.rerun()


def render_dashboard_access_section(colors):
    """
    Render the dashboard access table
    Shows only Read Only users (Admin users have access to all dashboards)
    """
    
    st.markdown(f'''
    <h3 style="
        color: {colors['text_primary']};
        font-size: 16px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 8px;
    ">Dashboard Access</h3>
    
    <p style="
        color: {colors['text_secondary']};
        font-size: 13px;
        font-style: italic;
        margin-bottom: 16px;
    ">Note: Admin users have access to all dashboards.</p>
    ''', unsafe_allow_html=True)
    
    # Build table rows
    table_rows = ""
    for dashboard in DASHBOARDS:
        readonly_users = get_readonly_users_for_dashboard(dashboard["id"])
        users_display = ", ".join(readonly_users) if readonly_users else "--"
        
        table_rows += f'''
        <tr>
            <td style="text-align: left;">{dashboard["name"]}</td>
            <td style="text-align: left;">{users_display}</td>
        </tr>
        '''
    
    st.markdown(f'''
    <table class="admin-table">
        <thead>
            <tr>
                <th style="text-align: left;">Dashboard Name</th>
                <th style="text-align: left;">Read Only Users</th>
            </tr>
        </thead>
        <tbody>
            {table_rows}
        </tbody>
    </table>
    ''', unsafe_allow_html=True)


def render_add_user_section(colors):
    """Render the collapsible add new user form"""
    
    with st.expander("➕ Add New User", expanded=False):
        with st.form("add_user_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_name = st.text_input("User Name", placeholder="Display Name")
                new_user_id = st.text_input("User ID", placeholder="Login ID")
            
            with col2:
                new_password = st.text_input("Password", type="password")
                new_role = st.selectbox(
                    "Role",
                    options=ROLE_OPTIONS,
                    format_func=lambda x: ROLE_DISPLAY.get(x, x)
                )
            
            # Dashboard selection for readonly only (hidden for admin)
            if new_role == "readonly":
                new_dashboards = st.multiselect(
                    "Dashboard Access",
                    options=[d["id"] for d in DASHBOARDS],
                    format_func=lambda x: next((d["name"] for d in DASHBOARDS if d["id"] == x), x)
                )
            else:
                new_dashboards = "all"
                st.info("Admin users automatically have access to all dashboards.")
            
            if st.form_submit_button("Create User", use_container_width=True):
                if new_name and new_user_id and new_password:
                    dashboards = new_dashboards if new_role == "readonly" else "all"
                    success, msg = add_user(new_user_id, new_password, new_role, new_name, dashboards)
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.warning("Please fill all required fields")
