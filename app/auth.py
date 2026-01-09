"""
Authentication System for Variant Analytics Dashboard
- Simple username/password auth
- Roles: admin (all access) and readonly (selected dashboards)
- Admin functions for user management
"""

import streamlit as st
from config import DEFAULT_USERS, DASHBOARDS, ROLE_DISPLAY


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
    
    # Check if dashboard is enabled
    dashboard = next((d for d in DASHBOARDS if d["id"] == dashboard_id), None)
    if not dashboard or not dashboard.get("enabled", False):
        return False
    
    # Admin has access to all
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


def get_dashboard_access_for_user(username):
    """Get list of dashboard IDs a user has access to"""
    init_auth()
    users = st.session_state.users_db
    
    if username not in users:
        return []
    
    user_data = users[username]
    if user_data["role"] == "admin" or user_data["dashboards"] == "all":
        return "all"
    
    return user_data.get("dashboards", [])


def get_readonly_users_for_dashboard(dashboard_id):
    """Get list of readonly users who have access to a specific dashboard"""
    init_auth()
    users = st.session_state.users_db
    
    readonly_users = []
    for username, user_data in users.items():
        if user_data["role"] == "readonly":
            if user_data["dashboards"] == "all" or dashboard_id in user_data.get("dashboards", []):
                readonly_users.append(user_data["name"])
    
    return readonly_users


# =============================================================================
# ADMIN FUNCTIONS
# =============================================================================

def get_all_users():
    """Get all users (admin only)"""
    init_auth()
    return st.session_state.users_db


def add_user(user_id, password, role, name, dashboards):
    """Add a new user (admin only)"""
    init_auth()
    
    if user_id in st.session_state.users_db:
        return False, "User ID already exists"
    
    st.session_state.users_db[user_id] = {
        "password": password,
        "role": role,
        "name": name,
        "dashboards": dashboards if role == "readonly" else "all"
    }
    return True, "User created successfully"


def update_user(user_id, password=None, role=None, name=None, dashboards=None):
    """Update existing user (admin only)"""
    init_auth()
    
    if user_id not in st.session_state.users_db:
        return False, "User not found"
    
    if password:
        st.session_state.users_db[user_id]["password"] = password
    if role:
        st.session_state.users_db[user_id]["role"] = role
        # If role changed to admin, set dashboards to all
        if role == "admin":
            st.session_state.users_db[user_id]["dashboards"] = "all"
    if name:
        st.session_state.users_db[user_id]["name"] = name
    if dashboards is not None and st.session_state.users_db[user_id]["role"] == "readonly":
        st.session_state.users_db[user_id]["dashboards"] = dashboards
    
    return True, "User updated successfully"


def delete_user(user_id):
    """Delete a user (admin only)"""
    init_auth()
    
    if user_id not in st.session_state.users_db:
        return False, "User not found"
    
    if user_id == "admin":
        return False, "Cannot delete admin user"
    
    # Check if trying to delete self
    current_user = get_current_user()
    if current_user and current_user["username"] == user_id:
        return False, "Cannot delete yourself"
    
    del st.session_state.users_db[user_id]
    return True, "User deleted successfully"


def get_role_display(role):
    """Get display name for role"""
    return ROLE_DISPLAY.get(role, role)
