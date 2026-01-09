"""
Chart Components for Variant Analytics Dashboard
- Scroll zoom DISABLED (page scrolls instead)
- Zoom only in Fullscreen mode
- Toolbar: Fullscreen, PDF Export, PNG Download
"""

import plotly.graph_objects as go
import streamlit as st
from colors import build_plan_color_map
from theme import get_theme_colors


def hex_to_rgba(hex_color, opacity=1.0):
    """Convert hex color to rgba string"""
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return f"rgba({r}, {g}, {b}, {opacity})"


def build_legend_html(plans, color_map):
    """Build HTML for legend box"""
    colors = get_theme_colors()
    
    legend_items = []
    for plan in plans:
        color = color_map.get(plan, "#6B7280")
        legend_items.append(
            f'<span style="display: inline-flex; align-items: center; gap: 6px; font-size: 12px;">'
            f'<span style="width: 10px; height: 10px; border-radius: 50%; background-color: {color};"></span>'
            f'{plan}'
            f'</span>'
        )
    
    return f'''
    <div style="
        background: {colors['surface']};
        border: 1px solid {colors['border']};
        border-radius: 8px;
        padding: 10px 16px;
        margin-bottom: 12px;
        max-height: 60px;
        overflow-y: auto;
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        color: {colors['text_primary']};
    ">
        {"".join(legend_items)}
    </div>
    '''


def build_line_chart(data, display_name, format_type="dollar", date_range=None):
    """Build a line chart for a metric by Plan over time"""
    
    colors = get_theme_colors()
    
    # Empty data check
    if not data or "Plan_Name" not in data or len(data["Plan_Name"]) == 0:
        fig = go.Figure()
        fig.update_layout(
            height=350,
            paper_bgcolor=colors["card_bg"],
            plot_bgcolor=colors["card_bg"],
            font=dict(family="Inter, sans-serif", size=12, color=colors["text_primary"]),
            annotations=[{
                "text": "No data available",
                "xref": "paper", "yref": "paper",
                "x": 0.5, "y": 0.5,
                "showarrow": False,
                "font": {"size": 14, "color": colors["text_secondary"]}
            }]
        )
        return fig, []
    
    # Get unique plans and colors
    unique_plans = sorted(set(data["Plan_Name"]))
    color_map = build_plan_color_map(unique_plans)
    
    # Organize data by plan
    plan_data = {}
    for i in range(len(data["Plan_Name"])):
        plan = data["Plan_Name"][i]
        date = data["Reporting_Date"][i]
        value = data["metric_value"][i]
        
        if plan not in plan_data:
            plan_data[plan] = {"dates": [], "values": []}
        plan_data[plan]["dates"].append(date)
        plan_data[plan]["values"].append(value if value is not None else 0)
    
    fig = go.Figure()
    
    LINE_OPACITY = 0.7
    LINE_WIDTH = 1
    
    for plan in unique_plans:
        if plan in plan_data:
            sorted_pairs = sorted(zip(plan_data[plan]["dates"], plan_data[plan]["values"]))
            dates = [p[0] for p in sorted_pairs]
            values = [p[1] for p in sorted_pairs]
            
            base_color = color_map.get(plan, "#6B7280")
            line_color = hex_to_rgba(base_color, LINE_OPACITY)
            
            # Hover template
            if format_type == "dollar":
                hover_template = f'<b>{plan}</b><br>Date: %{{x|%B %d, %Y}}<br>Value: $%{{y:,.2f}}<extra></extra>'
            elif format_type == "percent":
                hover_template = f'<b>{plan}</b><br>Date: %{{x|%B %d, %Y}}<br>Value: %{{y:.2%}}<extra></extra>'
            else:
                hover_template = f'<b>{plan}</b><br>Date: %{{x|%B %d, %Y}}<br>Value: %{{y:,.0f}}<extra></extra>'
            
            fig.add_trace(go.Scatter(
                x=dates,
                y=values,
                mode='lines',
                name=plan,
                line=dict(color=line_color, width=LINE_WIDTH),
                hovertemplate=hover_template,
                showlegend=False
            ))
    
    # Y-axis formatting
    if format_type == "dollar":
        yaxis_tickprefix = "$"
        yaxis_tickformat = ",.2f"
    elif format_type == "percent":
        yaxis_tickprefix = ""
        yaxis_tickformat = ".1%"
    else:
        yaxis_tickprefix = ""
        yaxis_tickformat = ",d"
    
    # X-axis range
    xaxis_range = [date_range[0], date_range[1]] if date_range else None
    
    fig.update_layout(
        height=350,
        margin=dict(l=60, r=20, t=20, b=50),
        hovermode="x unified",
        paper_bgcolor=colors["card_bg"],
        plot_bgcolor=colors["card_bg"],
        font=dict(family="Inter, sans-serif", size=12, color=colors["text_primary"]),
        xaxis=dict(
            gridcolor=colors["border"],
            linecolor=colors["border"],
            tickfont=dict(color=colors["text_secondary"]),
            tickformat="%b %Y",
            range=xaxis_range,
            fixedrange=True  # DISABLE zoom
        ),
        yaxis=dict(
            gridcolor=colors["border"],
            linecolor=colors["border"],
            tickfont=dict(color=colors["text_secondary"]),
            tickprefix=yaxis_tickprefix,
            tickformat=yaxis_tickformat,
            fixedrange=True  # DISABLE zoom
        ),
        dragmode=False
    )
    
    return fig, unique_plans


def render_chart_pair(chart_data_regular, chart_data_crystal, display_name, format_type="dollar", date_range=None, chart_key=""):
    """Render a pair of charts (Regular and Crystal Ball) side by side"""
    
    colors = get_theme_colors()
    
    # Chart config - scroll zoom DISABLED
    chart_config = {
        'displayModeBar': True,
        'displaylogo': False,
        'modeBarButtonsToRemove': ['zoom2d', 'pan2d', 'select2d', 'lasso2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d'],
        'toImageButtonOptions': {
            'format': 'png',
            'filename': f'{display_name}_chart',
            'height': 600,
            'width': 1000,
            'scale': 2
        },
        'scrollZoom': False
    }
    
    col1, col2 = st.columns(2)
    
    # Regular chart
    with col1:
        title_col, btn_col = st.columns([5, 1])
        
        with title_col:
            st.markdown(f'''
            <div style="font-size: 16px; font-weight: 600; color: {colors['text_primary']}; margin-bottom: 8px;">
                {display_name}
            </div>
            ''', unsafe_allow_html=True)
        
        with btn_col:
            with st.popover("⋮"):
                if st.button("⛶ Fullscreen", key=f"{chart_key}_r_fs", use_container_width=True):
                    st.session_state[f"{chart_key}_r_fullscreen"] = True
                if st.button("📄 Export PDF", key=f"{chart_key}_r_pdf", use_container_width=True):
                    st.info("PDF export - Coming soon")
                if st.button("📥 Download PNG", key=f"{chart_key}_r_png", use_container_width=True):
                    st.info("Use camera icon on chart")
        
        fig_regular, plans_regular = build_line_chart(
            chart_data_regular, display_name, format_type, date_range
        )
        
        if plans_regular:
            color_map = build_plan_color_map(plans_regular)
            st.markdown(build_legend_html(plans_regular, color_map), unsafe_allow_html=True)
        
        st.plotly_chart(fig_regular, use_container_width=True, config=chart_config, key=f"{chart_key}_r")
    
    # Crystal Ball chart
    with col2:
        title_col, btn_col = st.columns([5, 1])
        
        with title_col:
            st.markdown(f'''
            <div style="font-size: 16px; font-weight: 600; color: {colors['text_primary']}; margin-bottom: 8px;">
                {display_name} (Crystal Ball)
            </div>
            ''', unsafe_allow_html=True)
        
        with btn_col:
            with st.popover("⋮"):
                if st.button("⛶ Fullscreen", key=f"{chart_key}_c_fs", use_container_width=True):
                    st.session_state[f"{chart_key}_c_fullscreen"] = True
                if st.button("📄 Export PDF", key=f"{chart_key}_c_pdf", use_container_width=True):
                    st.info("PDF export - Coming soon")
                if st.button("📥 Download PNG", key=f"{chart_key}_c_png", use_container_width=True):
                    st.info("Use camera icon on chart")
        
        fig_crystal, plans_crystal = build_line_chart(
            chart_data_crystal, f"{display_name} (Crystal Ball)", format_type, date_range
        )
        
        if plans_crystal:
            color_map = build_plan_color_map(plans_crystal)
            st.markdown(build_legend_html(plans_crystal, color_map), unsafe_allow_html=True)
        
        st.plotly_chart(fig_crystal, use_container_width=True, config=chart_config, key=f"{chart_key}_c")
