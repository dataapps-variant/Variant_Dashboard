"""
Theme System for Variant Analytics Dashboard
Handles dark/light mode and all CSS styling
"""

import streamlit as st
from config import THEME_COLORS


def get_current_theme():
    """Get the current theme from session state"""
    if "theme" not in st.session_state:
        st.session_state.theme = "dark"  # Default to dark mode
    return st.session_state.theme


def toggle_theme():
    """Toggle between dark and light theme"""
    current = get_current_theme()
    st.session_state.theme = "light" if current == "dark" else "dark"


def get_theme_colors():
    """Get the color palette for current theme"""
    theme = get_current_theme()
    return THEME_COLORS[theme]


def apply_theme():
    """Apply the current theme CSS to the application"""
    theme = get_current_theme()
    colors = THEME_COLORS[theme]
    
    css = f"""
    <style>
    /* ========================================
       ROOT VARIABLES
       ======================================== */
    :root {{
        --bg-primary: {colors['background']};
        --bg-surface: {colors['surface']};
        --bg-card: {colors['card_bg']};
        --bg-input: {colors['input_bg']};
        --bg-hover: {colors['hover']};
        --border-color: {colors['border']};
        --text-primary: {colors['text_primary']};
        --text-secondary: {colors['text_secondary']};
        --accent: {colors['accent']};
        --accent-hover: {colors['accent_hover']};
        --success: {colors['success']};
        --warning: {colors['warning']};
        --danger: {colors['danger']};
    }}
    
    /* ========================================
       GLOBAL STYLES
       ======================================== */
    html, body, .stApp {{
        background-color: var(--bg-primary) !important;
        color: var(--text-primary) !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }}
    
    .stApp > header {{
        background-color: var(--bg-primary) !important;
    }}
    
    /* Main container */
    .main .block-container {{
        padding: 2rem 3rem !important;
        max-width: 100% !important;
    }}
    
    /* ========================================
       TYPOGRAPHY
       ======================================== */
    h1 {{
        color: var(--text-primary) !important;
        font-size: 24px !important;
        font-weight: 600 !important;
        margin-bottom: 0.5rem !important;
    }}
    
    h2 {{
        color: var(--text-primary) !important;
        font-size: 20px !important;
        font-weight: 600 !important;
    }}
    
    h3 {{
        color: var(--text-primary) !important;
        font-size: 18px !important;
        font-weight: 600 !important;
    }}
    
    p, span, label {{
        color: var(--text-primary) !important;
    }}
    
    /* ========================================
       CARDS & CONTAINERS
       ======================================== */
    .card {{
        background: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 12px !important;
        padding: 20px !important;
        margin-bottom: 16px !important;
        transition: all 0.2s ease !important;
    }}
    
    .card:hover {{
        border-color: var(--accent) !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
    }}
    
    /* Filter container */
    .filter-container {{
        background: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 12px !important;
        padding: 20px !important;
        margin-bottom: 20px !important;
    }}
    
    .filter-title {{
        font-size: 13px !important;
        font-weight: 600 !important;
        color: var(--text-secondary) !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
        margin-bottom: 10px !important;
        padding-bottom: 8px !important;
        border-bottom: 1px solid var(--border-color) !important;
    }}
    
    /* Chart container */
    .chart-container {{
        background: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 12px !important;
        padding: 20px !important;
        margin-bottom: 16px !important;
    }}
    
    .chart-title {{
        font-size: 16px !important;
        font-weight: 600 !important;
        color: var(--text-primary) !important;
        margin-bottom: 16px !important;
    }}
    
    /* Legend box */
    .legend-box {{
        background: var(--bg-surface) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px !important;
        padding: 10px 16px !important;
        margin-bottom: 16px !important;
        max-height: 60px !important;
        overflow-y: auto !important;
        display: flex !important;
        flex-wrap: wrap !important;
        gap: 12px !important;
    }}
    
    .legend-item {{
        display: flex !important;
        align-items: center !important;
        gap: 6px !important;
        font-size: 12px !important;
        color: var(--text-primary) !important;
    }}
    
    .legend-dot {{
        width: 10px !important;
        height: 10px !important;
        border-radius: 50% !important;
    }}
    
    /* ========================================
       BUTTONS
       ======================================== */
    .stButton > button {{
        background: var(--accent) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 8px 16px !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
    }}
    
    .stButton > button:hover {{
        background: var(--accent-hover) !important;
        box-shadow: 0 2px 8px rgba(20, 184, 166, 0.3) !important;
    }}
    
    /* Secondary button */
    .secondary-btn > button {{
        background: transparent !important;
        color: var(--accent) !important;
        border: 1px solid var(--accent) !important;
    }}
    
    .secondary-btn > button:hover {{
        background: var(--accent) !important;
        color: white !important;
    }}
    
    /* ========================================
       INPUTS & FORM ELEMENTS
       ======================================== */
    .stTextInput > div > div > input {{
        background: var(--bg-input) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px !important;
    }}
    
    .stTextInput > div > div > input:focus {{
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 2px rgba(20, 184, 166, 0.2) !important;
    }}
    
    .stSelectbox > div > div {{
        background: var(--bg-input) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px !important;
    }}
    
    .stDateInput > div > div > input {{
        background: var(--bg-input) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px !important;
    }}
    
    /* Checkbox */
    .stCheckbox {{
        margin-bottom: -10px !important;
    }}
    
    .stCheckbox > label {{
        color: var(--text-primary) !important;
        font-size: 13px !important;
    }}
    
    .stCheckbox > label > span[data-testid="stCheckboxLabel"] {{
        color: var(--text-primary) !important;
    }}
    
    /* Radio */
    .stRadio > div {{
        gap: 8px !important;
    }}
    
    .stRadio > label {{
        color: var(--text-primary) !important;
    }}
    
    /* ========================================
       TABS
       ======================================== */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 0 !important;
        background: var(--bg-surface) !important;
        border-radius: 10px !important;
        padding: 4px !important;
        border: 1px solid var(--border-color) !important;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        background: transparent !important;
        color: var(--text-secondary) !important;
        border-radius: 8px !important;
        padding: 8px 24px !important;
        font-weight: 500 !important;
    }}
    
    .stTabs [data-baseweb="tab"][aria-selected="true"] {{
        background: var(--accent) !important;
        color: white !important;
    }}
    
    .stTabs [data-baseweb="tab-highlight"] {{
        display: none !important;
    }}
    
    .stTabs [data-baseweb="tab-border"] {{
        display: none !important;
    }}
    
    /* ========================================
       EXPANDER
       ======================================== */
    .streamlit-expanderHeader {{
        background: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px !important;
        color: var(--text-primary) !important;
        font-weight: 500 !important;
    }}
    
    .streamlit-expanderContent {{
        background: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
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
        background: var(--bg-primary) !important;
        border-radius: 4px !important;
    }}
    
    ::-webkit-scrollbar-thumb {{
        background: var(--border-color) !important;
        border-radius: 4px !important;
    }}
    
    ::-webkit-scrollbar-thumb:hover {{
        background: var(--text-secondary) !important;
    }}
    
    /* ========================================
       DASHBOARD CARDS (Landing Page)
       ======================================== */
    .dashboard-card {{
        background: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 12px !important;
        padding: 24px !important;
        cursor: pointer !important;
        transition: all 0.2s ease !important;
        text-align: center !important;
    }}
    
    .dashboard-card:hover {{
        border-color: var(--accent) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15) !important;
    }}
    
    .dashboard-card-icon {{
        font-size: 32px !important;
        margin-bottom: 12px !important;
    }}
    
    .dashboard-card-title {{
        font-size: 14px !important;
        font-weight: 600 !important;
        color: var(--text-primary) !important;
    }}
    
    .dashboard-card-disabled {{
        opacity: 0.5 !important;
        cursor: not-allowed !important;
    }}
    
    /* ========================================
       LOGIN PAGE
       ======================================== */
    .login-container {{
        max-width: 400px !important;
        margin: 80px auto !important;
        padding: 40px !important;
        background: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 16px !important;
    }}
    
    .login-title {{
        font-size: 24px !important;
        font-weight: 600 !important;
        color: var(--text-primary) !important;
        text-align: center !important;
        margin-bottom: 8px !important;
    }}
    
    .login-subtitle {{
        font-size: 14px !important;
        color: var(--text-secondary) !important;
        text-align: center !important;
        margin-bottom: 32px !important;
    }}
    
    /* ========================================
       POPOVER / MENU
       ======================================== */
    [data-testid="stPopover"] {{
        background: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px !important;
    }}
    
    /* ========================================
       METRIC DISPLAY
       ======================================== */
    [data-testid="stMetricValue"] {{
        color: var(--text-primary) !important;
    }}
    
    [data-testid="stMetricLabel"] {{
        color: var(--text-secondary) !important;
    }}
    
    /* ========================================
       ALERTS & MESSAGES
       ======================================== */
    .stAlert {{
        background: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px !important;
    }}
    
    /* Success */
    .stSuccess {{
        border-left: 4px solid var(--success) !important;
    }}
    
    /* Warning */
    .stWarning {{
        border-left: 4px solid var(--warning) !important;
    }}
    
    /* Error */
    .stError {{
        border-left: 4px solid var(--danger) !important;
    }}
    
    /* ========================================
       HIDE STREAMLIT DEFAULTS
       ======================================== */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    
    /* ========================================
       PIVOT TABLE STYLES
       ======================================== */
    .pivot-container {{
        background: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 12px !important;
        padding: 20px !important;
        margin-bottom: 20px !important;
        overflow: hidden !important;
    }}
    
    .pivot-title {{
        font-size: 16px !important;
        font-weight: 600 !important;
        color: var(--text-primary) !important;
        margin-bottom: 16px !important;
    }}
    
    .pivot-wrapper {{
        max-height: 450px !important;
        overflow: auto !important;
    }}
    
    .pivot-table {{
        width: 100% !important;
        border-collapse: separate !important;
        border-spacing: 0 !important;
        font-size: 13px !important;
    }}
    
    .pivot-table th {{
        background: {'#334155' if theme == 'dark' else '#F3F4F6'} !important;
        color: var(--text-primary) !important;
        font-weight: 600 !important;
        padding: 12px 16px !important;
        text-align: left !important;
        position: sticky !important;
        top: 0 !important;
        z-index: 10 !important;
        border-bottom: 2px solid var(--border-color) !important;
        white-space: nowrap !important;
    }}
    
    .pivot-table td {{
        background: var(--bg-card) !important;
        color: var(--text-primary) !important;
        padding: 10px 16px !important;
        border-bottom: 1px solid var(--border-color) !important;
        white-space: nowrap !important;
    }}
    
    .pivot-table tr:hover td {{
        background: var(--bg-hover) !important;
    }}
    
    /* Frozen columns */
    .pivot-table th:nth-child(1),
    .pivot-table td:nth-child(1) {{
        position: sticky !important;
        left: 0 !important;
        z-index: 11 !important;
        min-width: 80px !important;
    }}
    
    .pivot-table th:nth-child(2),
    .pivot-table td:nth-child(2) {{
        position: sticky !important;
        left: 80px !important;
        z-index: 11 !important;
        min-width: 100px !important;
    }}
    
    .pivot-table th:nth-child(3),
    .pivot-table td:nth-child(3) {{
        position: sticky !important;
        left: 180px !important;
        z-index: 11 !important;
        min-width: 150px !important;
        border-right: 2px solid var(--border-color) !important;
    }}
    
    .pivot-table th:nth-child(1),
    .pivot-table th:nth-child(2),
    .pivot-table th:nth-child(3) {{
        z-index: 12 !important;
    }}
    
    .pivot-table td:nth-child(n+4) {{
        text-align: right !important;
    }}
    
    .pivot-table th:nth-child(n+4) {{
        text-align: right !important;
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
