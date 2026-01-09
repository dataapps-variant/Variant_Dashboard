"""
Variant Analytics Dashboard - Main Entry Point
Version 2.0 - Complete Redesign

To run:
    streamlit run app/main.py

Environment Variables:
    GCS_CACHE_BUCKET - GCS bucket name for caching (optional)
    GOOGLE_APPLICATION_CREDENTIALS - Path to service account JSON
"""

import streamlit as st
import sys
import os

# Add app directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import APP_NAME
from theme import apply_theme
from auth import is_authenticated, init_auth


def main():
    """Main application entry point"""
    
    # Page config - must be first Streamlit command
    st.set_page_config(
        page_title=APP_NAME,
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Initialize authentication
    init_auth()
    
    # Apply theme CSS
    apply_theme()
    
    # Initialize page state
    if "current_page" not in st.session_state:
        st.session_state.current_page = "landing"
    
    # Route based on authentication state
    if not is_authenticated():
        from pages.login import render_login_page
        render_login_page()
    else:
        # Check if admin panel should be shown
        if st.session_state.get("show_admin_panel", False):
            from admin_panel import render_admin_panel
            render_admin_panel()
        else:
            # Route to appropriate page
            current_page = st.session_state.current_page
            
            if current_page == "landing":
                from pages.landing import render_landing_page
                render_landing_page()
            elif current_page == "icarus_historical":
                from pages.icarus_historical import render_icarus_historical
                render_icarus_historical()
            else:
                # Default to landing
                st.session_state.current_page = "landing"
                from pages.landing import render_landing_page
                render_landing_page()


if __name__ == "__main__":
    main()
