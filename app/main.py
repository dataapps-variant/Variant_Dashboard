"""
Variant Analytics Dashboard
Main Entry Point

This is the main application file that handles routing between pages:
- Login Page
- Landing Page (Dashboard Hub)
- Individual Dashboard Pages
"""

import streamlit as st
from config import APP_NAME
from theme import apply_theme
from auth import is_authenticated, init_auth

# Page config must be the first Streamlit command
st.set_page_config(
    page_title=APP_NAME,
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize authentication
init_auth()

# Apply theme
apply_theme()

# Initialize page state
if "current_page" not in st.session_state:
    st.session_state.current_page = "landing"


def main():
    """Main application entry point"""
    
    # Check authentication
    if not is_authenticated():
        # Show login page
        from pages.login import render_login_page
        render_login_page()
    else:
        # Route to appropriate page
        current_page = st.session_state.get("current_page", "landing")
        
        if current_page == "landing":
            from pages.landing import render_landing_page
            render_landing_page()
        
        elif current_page == "icarus_historical":
            from pages.icarus_historical import render_icarus_historical
            render_icarus_historical()
        
        else:
            # Unknown page, redirect to landing
            st.session_state.current_page = "landing"
            st.rerun()


if __name__ == "__main__":
    main()
