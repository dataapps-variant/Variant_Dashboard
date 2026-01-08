"""
Authentication System for Variant Analytics Dashboard
Simple username/password auth with admin/viewer roles
"""

import streamlit as st
from config import DEFAULT_USERS, DASHBOARDS


def init_auth():
    """Initialize authentication session state"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user" not in st.session_state:
        st.session_state.user = None
    if "users_db" not in st.session_state:
        st.session_state.users_db = DEFAULT_USERS.copy()


def authenticate(username, password):
    """
    Authenticate user with username and password
    Returns True if successful, False otherwise
    """
    init_auth()
    users = st.session_state.users_db
    
    if username in users:
        if users[username]["password"] == password:
            st.session_state.authenticated = True
            st.session_state.user = {
                "username": username,
                "role": users[username]["role"],
                "name": users[username]["name"],
                "dashboards": users[username]["dashboards"]
            }
            return True
    return False


def logout():
    """Log out current user"""
    st.session_state.authenticated = False
    st.session_state.user = None


def is_authenticated():
    """Check if user is authenticated"""
    init_auth()
    return st.session_state.authenticated


def get_current_user():
    """Get current logged in user info"""
    init_auth()
    return st.session_state.user


def is_admin():
    """Check if current user is admin"""
    user = get_current_user()
    if user:
        return user["role"] == "admin"
    return False


def can_access_dashboard(dashboard_id):
    """Check if current user can access a specific dashboard"""
    user = get_current_user()
    if not user:
        return False
    
    if user["role"] == "admin" or user["dashboards"] == "all":
        return True
    
    return dashboard_id in user.get("dashboards", [])


def get_accessible_dashboards():
    """Get list of dashboards accessible to current user"""
    user = get_current_user()
    if not user:
        return []
    
    if user["role"] == "admin" or user["dashboards"] == "all":
        return DASHBOARDS
    
    accessible = []
    for dashboard in DASHBOARDS:
        if dashboard["id"] in user.get("dashboards", []):
            accessible.append(dashboard)
    
    return accessible


# =============================================================================
# ADMIN FUNCTIONS
# =============================================================================

def get_all_users():
    """Get all users (admin only)"""
    init_auth()
    return st.session_state.users_db


def add_user(username, password, role, name, dashboards):
    """Add a new user (admin only)"""
    init_auth()
    if username in st.session_state.users_db:
        return False, "Username already exists"
    
    st.session_state.users_db[username] = {
        "password": password,
        "role": role,
        "name": name,
        "dashboards": dashboards
    }
    return True, "User created successfully"


def update_user(username, password=None, role=None, name=None, dashboards=None):
    """Update existing user (admin only)"""
    init_auth()
    if username not in st.session_state.users_db:
        return False, "User not found"
    
    if password:
        st.session_state.users_db[username]["password"] = password
    if role:
        st.session_state.users_db[username]["role"] = role
    if name:
        st.session_state.users_db[username]["name"] = name
    if dashboards is not None:
        st.session_state.users_db[username]["dashboards"] = dashboards
    
    return True, "User updated successfully"


def delete_user(username):
    """Delete a user (admin only)"""
    init_auth()
    if username not in st.session_state.users_db:
        return False, "User not found"
    
    if username == "admin":
        return False, "Cannot delete admin user"
    
    del st.session_state.users_db[username]
    return True, "User deleted successfully"


# =============================================================================
# USER PREFERENCES
# =============================================================================

def get_user_dashboard_order():
    """Get user's custom dashboard order"""
    if "dashboard_order" not in st.session_state:
        st.session_state.dashboard_order = None
    return st.session_state.dashboard_order


def set_user_dashboard_order(order):
    """Set user's custom dashboard order"""
    st.session_state.dashboard_order = order


def get_ordered_dashboards():
    """Get dashboards in user's preferred order"""
    accessible = get_accessible_dashboards()
    custom_order = get_user_dashboard_order()
    
    if not custom_order:
        return accessible
    
    # Sort by custom order
    ordered = []
    for dash_id in custom_order:
        for dash in accessible:
            if dash["id"] == dash_id:
                ordered.append(dash)
                break
    
    # Add any new dashboards not in custom order
    for dash in accessible:
        if dash not in ordered:
            ordered.append(dash)
    
    return ordered
