"""
Login Page for Variant Analytics Dashboard
"""

import streamlit as st
from auth import authenticate
from theme import get_theme_colors, toggle_theme, get_current_theme
from config import APP_TITLE


def render_login_page():
    """Render the login page"""
    
    colors = get_theme_colors()
    current_theme = get_current_theme()
    
    # Theme toggle in corner
    col1, col2, col3 = st.columns([1, 2, 1])
    with col3:
        with st.popover("⋮"):
            theme_icon = "☀️" if current_theme == "dark" else "🌙"
            theme_text = "Light Mode" if current_theme == "dark" else "Dark Mode"
            if st.button(f"{theme_icon} {theme_text}", use_container_width=True):
                toggle_theme()
                st.rerun()
    
    # Center the login form
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    
    with col2:
        # Login container
        st.markdown(f'''
        <div style="
            background: {colors['card_bg']};
            border: 1px solid {colors['border']};
            border-radius: 16px;
            padding: 40px;
            text-align: center;
        ">
            <div style="
                font-size: 48px;
                margin-bottom: 16px;
            ">📊</div>
            <h1 style="
                font-size: 24px;
                font-weight: 600;
                color: {colors['text_primary']};
                margin-bottom: 8px;
            ">{APP_TITLE}</h1>
            <p style="
                font-size: 14px;
                color: {colors['text_secondary']};
                margin-bottom: 32px;
            ">Sign in to access your dashboards</p>
        </div>
        ''', unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Login form
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            
            col_rem, col_btn = st.columns([1, 1])
            with col_rem:
                remember_me = st.checkbox("Remember me")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            submitted = st.form_submit_button("Sign In", use_container_width=True)
            
            if submitted:
                if username and password:
                    if authenticate(username, password):
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
                else:
                    st.warning("Please enter both username and password")
        
        # Demo credentials hint
        st.markdown(f'''
        <div style="
            text-align: center;
            margin-top: 24px;
            padding: 16px;
            background: {colors['surface']};
            border-radius: 8px;
            border: 1px solid {colors['border']};
        ">
            <p style="
                font-size: 12px;
                color: {colors['text_secondary']};
                margin: 0;
            ">
                <strong>Demo Credentials:</strong><br>
                Admin: admin / admin123<br>
                Viewer: viewer / viewer123
            </p>
        </div>
        ''', unsafe_allow_html=True)
