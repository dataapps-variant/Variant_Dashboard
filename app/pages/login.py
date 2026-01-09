"""
Login Page for Variant Analytics Dashboard
- Full screen layout
- Variant "V" logo
- "VARIANT GROUP" title
- "Sign in to access your dashboards" subtitle
- Username, Password, Remember Me, Sign In
- Demo Credentials box
- Theme toggle in menu
"""

import streamlit as st
from auth import authenticate
from theme import get_theme_colors, toggle_theme, get_current_theme, render_logo_header


def render_login_page():
    """Render the login page"""
    
    colors = get_theme_colors()
    current_theme = get_current_theme()
    
    # Theme toggle in corner menu
    col_spacer, col_menu = st.columns([12, 1])
    with col_menu:
        with st.popover("⋮"):
            theme_icon = "☀️" if current_theme == "dark" else "🌙"
            theme_text = "Light Mode" if current_theme == "dark" else "Dark Mode"
            if st.button(f"{theme_icon} {theme_text}", use_container_width=True):
                toggle_theme()
                st.rerun()
    
    # Centered content
    st.markdown(f'''
    <div style="max-width: 400px; margin: 0 auto; padding: 40px 20px;">
    ''', unsafe_allow_html=True)
    
    # Logo and header
    render_logo_header(
        size="large",
        show_title=True,
        show_welcome=False
    )
    
    # Subtitle
    st.markdown(f'''
    <p style="
        text-align: center;
        color: {colors['text_secondary']};
        font-size: 14px;
        margin: 0 0 40px 0;
    ">Sign in to access your dashboards</p>
    ''', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Login form - centered
    col1, col2, col3 = st.columns([1, 1.5, 1])
    
    with col2:
        # Form container
        st.markdown(f'''
        <div style="
            background: {colors['card_bg']};
            border: 1px solid {colors['border']};
            border-radius: 12px;
            padding: 30px;
        ">
        ''', unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            
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
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Demo credentials box
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
