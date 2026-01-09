"""
Theme System for Variant Analytics Dashboard
- Full screen layout (0 margins)
- Dark (default) and Light modes
- Adaptive logo based on theme
- Loading animation with logo fade
"""

import streamlit as st
import base64
import os
from config import THEME_COLORS


def get_current_theme():
    """Get the current theme from session state"""
    if "theme" not in st.session_state:
        st.session_state.theme = "dark"
    return st.session_state.theme


def toggle_theme():
    """Toggle between dark and light theme"""
    current = get_current_theme()
    st.session_state.theme = "light" if current == "dark" else "dark"


def get_theme_colors():
    """Get the color palette for current theme"""
    theme = get_current_theme()
    return THEME_COLORS[theme]


def get_logo_base64():
    """Get the logo as base64 encoded string"""
    logo_path = os.path.join(os.path.dirname(__file__), "assets", "variant_logo.png")
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None


def render_logo_header(size="large", show_title=True, show_welcome=False, username=""):
    """
    Render the Variant logo header centered
    
    Args:
        size: 'large' for landing/login, 'small' for dashboard pages
        show_title: Show 'VARIANT GROUP' text
        show_welcome: Show welcome message
        username: Username for welcome message
    """
    colors = get_theme_colors()
    theme = get_current_theme()
    
    logo_size = "80px" if size == "large" else "50px"
    title_size = "28px" if size == "large" else "20px"
    
    logo_base64 = get_logo_base64()
    
    if logo_base64:
        # Invert logo for dark mode (assuming logo is dark on transparent)
        filter_style = "invert(1)" if theme == "dark" else "invert(0)"
        logo_html = f'''
        <img src="data:image/png;base64,{logo_base64}" 
             style="width: {logo_size}; height: auto; filter: {filter_style};" 
             alt="Variant Logo"/>
        '''
    else:
        # Fallback: Styled V
        logo_html = f'''
        <div style="
            width: {logo_size};
            height: {logo_size};
            background: {colors['accent']};
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 36px;
            font-weight: bold;
            color: white;
        ">V</div>
        '''
    
    welcome_html = ""
    if show_welcome and username:
        welcome_html = f'''
        <p style="
            font-size: 16px;
            color: {colors['text_secondary']};
            margin: 8px 0 0 0;
            font-weight: 400;
        ">Welcome back, {username}</p>
        '''
    
    title_html = ""
    if show_title:
        title_html = f'''
        <h1 style="
            font-size: {title_size};
            font-weight: 700;
            color: {colors['text_primary']};
            margin: 16px 0 0 0;
            letter-spacing: 3px;
        ">VARIANT GROUP</h1>
        '''
    
    st.markdown(f'''
    <div style="
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 30px 0;
        text-align: center;
    ">
        {logo_html}
        {title_html}
        {welcome_html}
    </div>
    ''', unsafe_allow_html=True)


def render_loading_animation(progress=50):
    """
    Render loading screen with Variant logo fading animation
    Logo fades from 10% to 100% opacity based on progress
    """
    colors = get_theme_colors()
    theme = get_current_theme()
    
    opacity = 0.1 + (progress / 100) * 0.9
    logo_base64 = get_logo_base64()
    
    if logo_base64:
        filter_style = "invert(1)" if theme == "dark" else "invert(0)"
        logo_html = f'''
        <img src="data:image/png;base64,{logo_base64}" 
             style="width: 120px; height: auto; opacity: {opacity}; 
                    filter: {filter_style}; transition: opacity 0.5s ease;" 
             alt="Loading..."/>
        '''
    else:
        logo_html = f'''
        <div style="
            width: 120px; height: 120px;
            background: {colors['accent']};
            border-radius: 20px;
            opacity: {opacity};
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 48px;
            font-weight: bold;
            color: white;
            transition: opacity 0.5s ease;
        ">V</div>
        '''
    
    st.markdown(f'''
    <div style="
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        background: {colors['background']};
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        z-index: 9999;
    ">
        {logo_html}
    </div>
    ''', unsafe_allow_html=True)


def apply_theme():
    """Apply the current theme CSS - FULL SCREEN with NO MARGINS"""
    theme = get_current_theme()
    colors = THEME_COLORS[theme]
    
    css = f"""
    <style>
    /* ========================================
       FULL SCREEN LAYOUT - NO MARGINS
       ======================================== */
    html, body, .stApp {{
        background-color: {colors['background']} !important;
        color: {colors['text_primary']} !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        margin: 0 !important;
        padding: 0 !important;
    }}
    
    .stApp > header {{
        background-color: {colors['background']} !important;
    }}
    
    /* Main container - NO MARGINS */
    .main .block-container {{
        padding: 1rem 2rem !important;
        margin: 0 !important;
        max-width: 100% !important;
        width: 100% !important;
    }}
    
    /* Hide sidebar */
    section[data-testid="stSidebar"] {{
        display: none !important;
    }}
    
    /* ========================================
       TYPOGRAPHY
       ======================================== */
    h1, h2, h3 {{
        color: {colors['text_primary']} !important;
    }}
    
    p, span, label, div {{
        color: {colors['text_primary']};
    }}
    
    /* ========================================
       CARDS & CONTAINERS
       ======================================== */
    .card {{
        background: {colors['card_bg']} !important;
        border: 1px solid {colors['border']} !important;
        border-radius: 12px !important;
        padding: 20px !important;
    }}
    
    /* Filter title */
    .filter-title {{
        font-size: 13px !important;
        font-weight: 600 !important;
        color: {colors['text_secondary']} !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
        margin-bottom: 10px !important;
        padding-bottom: 8px !important;
        border-bottom: 1px solid {colors['border']} !important;
    }}
    
    /* ========================================
       TABLES
       ======================================== */
    .dashboard-table, .admin-table, .landing-table {{
        width: 100%;
        border-collapse: collapse;
        background: {colors['card_bg']};
        border: 1px solid {colors['border']};
        border-radius: 12px;
        overflow: hidden;
    }}
    
    .dashboard-table th, .admin-table th, .landing-table th {{
        background: {colors['table_header_bg']};
        color: {colors['text_primary']};
        font-weight: 600;
        padding: 16px 24px;
        text-align: center;
        border-bottom: 2px solid {colors['border']};
        font-size: 14px;
    }}
    
    .dashboard-table td, .admin-table td, .landing-table td {{
        padding: 14px 24px;
        border-bottom: 1px solid {colors['border']};
        font-size: 14px;
        color: {colors['text_primary']};
    }}
    
    .dashboard-table tr:hover, .admin-table tr:hover, .landing-table tr:hover {{
        background: {colors['hover']};
    }}
    
    /* ========================================
       BUTTONS
       ======================================== */
    .stButton > button {{
        background: {colors['accent']} !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 8px 16px !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
    }}
    
    .stButton > button:hover {{
        background: {colors['accent_hover']} !important;
        box-shadow: 0 2px 8px rgba(20, 184, 166, 0.3) !important;
    }}
    
    /* ========================================
       INPUTS & FORM ELEMENTS
       ======================================== */
    .stTextInput > div > div > input,
    .stSelectbox > div > div,
    .stDateInput > div > div > input,
    .stMultiSelect > div > div {{
        background: {colors['input_bg']} !important;
        color: {colors['text_primary']} !important;
        border: 1px solid {colors['border']} !important;
        border-radius: 8px !important;
    }}
    
    .stTextInput > div > div > input:focus {{
        border-color: {colors['accent']} !important;
        box-shadow: 0 0 0 2px rgba(20, 184, 166, 0.2) !important;
    }}
    
    .stCheckbox > label {{
        color: {colors['text_primary']} !important;
    }}
    
    .stCheckbox > label > span[data-testid="stCheckboxLabel"] {{
        color: {colors['text_primary']} !important;
    }}
    
    /* ========================================
       TABS
       ======================================== */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 0 !important;
        background: {colors['surface']} !important;
        border-radius: 10px !important;
        padding: 4px !important;
        border: 1px solid {colors['border']} !important;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        background: transparent !important;
        color: {colors['text_secondary']} !important;
        border-radius: 8px !important;
        padding: 8px 24px !important;
        font-weight: 500 !important;
    }}
    
    .stTabs [data-baseweb="tab"][aria-selected="true"] {{
        background: {colors['accent']} !important;
        color: white !important;
    }}
    
    .stTabs [data-baseweb="tab-highlight"],
    .stTabs [data-baseweb="tab-border"] {{
        display: none !important;
    }}
    
    /* ========================================
       EXPANDER
       ======================================== */
    .streamlit-expanderHeader {{
        background: {colors['card_bg']} !important;
        border: 1px solid {colors['border']} !important;
        border-radius: 8px !important;
        color: {colors['text_primary']} !important;
        font-weight: 500 !important;
    }}
    
    .streamlit-expanderContent {{
        background: {colors['card_bg']} !important;
        border: 1px solid {colors['border']} !important;
        border-top: none !important;
        border-radius: 0 0 8px 8px !important;
    }}
    
    /* ========================================
       SCROLLBAR
       ======================================== */
    ::-webkit-scrollbar {{
        width: 8px !important;
        height: 8px !important;
    }}
    
    ::-webkit-scrollbar-track {{
        background: {colors['background']} !important;
        border-radius: 4px !important;
    }}
    
    ::-webkit-scrollbar-thumb {{
        background: {colors['border']} !important;
        border-radius: 4px !important;
    }}
    
    ::-webkit-scrollbar-thumb:hover {{
        background: {colors['text_secondary']} !important;
    }}
    
    /* ========================================
       POPOVER / MENU
       ======================================== */
    [data-testid="stPopover"] {{
        background: {colors['card_bg']} !important;
        border: 1px solid {colors['border']} !important;
        border-radius: 8px !important;
    }}
    
    /* ========================================
       ALERTS
       ======================================== */
    .stAlert {{
        background: {colors['card_bg']} !important;
        border: 1px solid {colors['border']} !important;
        border-radius: 8px !important;
    }}
    
    /* ========================================
       HIDE STREAMLIT DEFAULTS
       ======================================== */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    
    /* ========================================
       AG GRID THEME
       ======================================== */
    .ag-root-wrapper {{
        border-radius: 8px !important;
        border: 1px solid {colors['border']} !important;
    }}
    
    .ag-header {{
        background-color: {colors['table_header_bg']} !important;
        border-bottom: 2px solid {colors['border']} !important;
    }}
    
    .ag-header-cell-text {{
        color: {colors['text_primary']} !important;
        font-weight: 600 !important;
    }}
    
    .ag-cell {{
        color: {colors['text_primary']} !important;
        border-right: 1px solid {colors['border']} !important;
    }}
    
    .ag-row {{
        border-bottom: 1px solid {colors['border']} !important;
    }}
    
    .ag-row-odd {{
        background-color: {colors['table_row_odd']} !important;
    }}
    
    .ag-row-even {{
        background-color: {colors['table_row_even']} !important;
    }}
    
    .ag-row-hover {{
        background-color: {colors['hover']} !important;
    }}
    
    </style>
    """
    
    st.markdown(css, unsafe_allow_html=True)


def get_plotly_theme():
    """Get Plotly theme configuration based on current theme"""
    theme = get_current_theme()
    colors = THEME_COLORS[theme]
    
    return {
        "paper_bgcolor": colors["card_bg"],
        "plot_bgcolor": colors["card_bg"],
        "font": {
            "family": "Inter, sans-serif",
            "size": 12,
            "color": colors["text_primary"]
        },
        "xaxis": {
            "gridcolor": colors["border"],
            "linecolor": colors["border"],
            "tickfont": {"color": colors["text_secondary"]},
            "title": {"font": {"color": colors["text_secondary"]}}
        },
        "yaxis": {
            "gridcolor": colors["border"],
            "linecolor": colors["border"],
            "tickfont": {"color": colors["text_secondary"]},
            "title": {"font": {"color": colors["text_secondary"]}}
        },
        "legend": {
            "font": {"color": colors["text_primary"]},
            "bgcolor": "rgba(0,0,0,0)"
        }
    }
