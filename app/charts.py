"""
Chart Components for Variant Analytics Dashboard

Customizations:
- Zoom & Pan enabled
- Download CSV button
- Thin lines (1.5px) with semi-transparency
- X-axis: Month Year format (Jan 2024)
- Tooltip: Date at top, Color-Plan-Value-Subscriptions per row
- Lines break where data is blank (no connecting gaps)
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
            f'<span style="display:inline-flex;align-items:center;gap:6px;font-size:12px;color:{colors["text_primary"]};">'
            f'<span style="width:10px;height:10px;border-radius:50%;background-color:{color};"></span>'
            f'{plan}'
            f'</span>'
        )
    
    html = f'''<div style="background:{colors['surface']};border:1px solid {colors['border']};border-radius:8px;padding:10px 16px;margin-bottom:16px;max-height:60px;overflow-y:auto;display:flex;flex-wrap:wrap;gap:12px;">{"".join(legend_items)}</div>'''
    return html


def build_line_chart(data, display_name, format_type="dollar", date_range=None, subscriptions_data=None, is_subscriptions_chart=False):
    """
    Build a line chart for a metric by Plan over time
    
    Args:
        data: Dict with Plan_Name, Reporting_Date, metric_value lists
        display_name: Chart title
        format_type: 'dollar', 'percent', or 'number'
        date_range: Tuple of (min_date, max_date) for x-axis range
        subscriptions_data: Dict with Plan_Name, Reporting_Date, metric_value for Subscriptions
        is_subscriptions_chart: If True, don't show Subscriptions in tooltip (avoid duplicate)
    
    Returns:
        Plotly figure and list of unique plans
    """
    
    colors = get_theme_colors()
    
    # Check for empty data
    if not data or "Plan_Name" not in data or len(data["Plan_Name"]) == 0:
        fig = go.Figure()
        fig.update_layout(
            height=350,
            paper_bgcolor=colors["card_bg"],
            plot_bgcolor=colors["card_bg"],
            font=dict(family="Inter, sans-serif", size=12, color=colors["text_primary"]),
            annotations=[{
                "text": "No data available for selected filters",
                "xref": "paper",
                "yref": "paper",
                "x": 0.5,
                "y": 0.5,
                "showarrow": False,
                "font": {"size": 14, "color": colors["text_secondary"]}
            }]
        )
        return fig, []
    
    # Get unique plans and build color map
    unique_plans = sorted(set(data["Plan_Name"]))
    color_map = build_plan_color_map(unique_plans)
    
    # Build subscriptions lookup if provided
    subs_lookup = {}
    if subscriptions_data and not is_subscriptions_chart:
        for i in range(len(subscriptions_data.get("Plan_Name", []))):
            plan = subscriptions_data["Plan_Name"][i]
            date = subscriptions_data["Reporting_Date"][i]
            value = subscriptions_data["metric_value"][i]
            subs_lookup[(plan, date)] = value
    
    # Organize data by plan
    plan_data = {}
    for i in range(len(data["Plan_Name"])):
        plan = data["Plan_Name"][i]
        date = data["Reporting_Date"][i]
        value = data["metric_value"][i]
        
        if plan not in plan_data:
            plan_data[plan] = {"dates": [], "values": [], "subs": []}
        plan_data[plan]["dates"].append(date)
        # Keep None as None for line breaks (don't convert to 0)
        plan_data[plan]["values"].append(value)
        # Get subscriptions for this plan/date
        subs_value = subs_lookup.get((plan, date), None)
        plan_data[plan]["subs"].append(subs_value)
    
    # Create figure
    fig = go.Figure()
    
    # Line opacity for semi-transparency
    LINE_OPACITY = 0.7
    LINE_WIDTH = 1.5  # Thin lines
    
    # Add trace for each plan
    for plan in unique_plans:
        if plan in plan_data:
            # Sort by date
            sorted_data = sorted(zip(
                plan_data[plan]["dates"], 
                plan_data[plan]["values"],
                plan_data[plan]["subs"]
            ))
            dates = [p[0] for p in sorted_data]
            values = [p[1] for p in sorted_data]
            subs = [p[2] for p in sorted_data]
            
            base_color = color_map.get(plan, "#6B7280")
            line_color = hex_to_rgba(base_color, LINE_OPACITY)
            
            # Build hover template
            if is_subscriptions_chart:
                # Subscriptions chart - just show value, no duplicate
                hover_template = (
                    f'<b style="color:{base_color};">●</b> {plan} - %{{y:,.0f}}'
                    f'<extra></extra>'
                )
                customdata = None
            else:
                # Other charts - show value and subscriptions
                if format_type == "dollar":
                    hover_template = (
                        f'<b style="color:{base_color};">●</b> {plan} - $%{{y:,.2f}} - %{{customdata:,.0f}} Subs'
                        f'<extra></extra>'
                    )
                elif format_type == "percent":
                    hover_template = (
                        f'<b style="color:{base_color};">●</b> {plan} - %{{y:.2%}} - %{{customdata:,.0f}} Subs'
                        f'<extra></extra>'
                    )
                else:
                    hover_template = (
                        f'<b style="color:{base_color};">●</b> {plan} - %{{y:,.0f}} - %{{customdata:,.0f}} Subs'
                        f'<extra></extra>'
                    )
                customdata = subs
            
            fig.add_trace(
                go.Scatter(
                    x=dates,
                    y=values,
                    mode='lines',
                    name=plan,
                    line=dict(
                        color=line_color,
                        width=LINE_WIDTH,
                        shape='linear'
                    ),
                    hovertemplate=hover_template,
                    customdata=customdata,
                    showlegend=False,
                    connectgaps=False  # Don't connect gaps - line breaks at None
                )
            )
    
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
    
    # X-axis range (full selected range)
    xaxis_range = None
    if date_range:
        xaxis_range = [date_range[0], date_range[1]]
    
    # Update layout
    fig.update_layout(
        height=350,
        margin=dict(l=60, r=20, t=20, b=50),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor=colors["card_bg"],
            bordercolor=colors["border"],
            font=dict(
                family="Inter, sans-serif",
                size=12,
                color=colors["text_primary"]
            ),
            namelength=-1
        ),
        paper_bgcolor=colors["card_bg"],
        plot_bgcolor=colors["card_bg"],
        font=dict(
            family="Inter, sans-serif",
            size=12,
            color=colors["text_primary"]
        ),
        xaxis=dict(
            gridcolor=colors["border"],
            linecolor=colors["border"],
            tickfont=dict(color=colors["text_secondary"]),
            tickformat="%b %Y",
            range=xaxis_range,
            fixedrange=False,
            hoverformat="%B %d, %Y"  # Full date format in tooltip header
        ),
        yaxis=dict(
            gridcolor=colors["border"],
            linecolor=colors["border"],
            tickfont=dict(color=colors["text_secondary"]),
            tickprefix=yaxis_tickprefix,
            tickformat=yaxis_tickformat,
            fixedrange=False
        ),
        legend=dict(
            font=dict(color=colors["text_primary"]),
            bgcolor="rgba(0,0,0,0)"
        ),
        dragmode="zoom"
    )
    
    return fig, unique_plans


def render_chart_pair(chart_data_regular, chart_data_crystal, display_name, format_type="dollar", date_range=None, chart_key="", subscriptions_regular=None, subscriptions_crystal=None):
    """
    Render a pair of charts (Regular and Crystal Ball) side by side
    
    Args:
        chart_data_regular: Data for regular chart
        chart_data_crystal: Data for crystal ball chart
        display_name: Base display name
        format_type: 'dollar', 'percent', or 'number'
        date_range: Tuple of (from_date, to_date) for x-axis
        chart_key: Unique key prefix for this chart pair
        subscriptions_regular: Subscriptions data for regular chart tooltip
        subscriptions_crystal: Subscriptions data for crystal ball chart tooltip
    """
    
    colors = get_theme_colors()
    
    # Check if this is the Subscriptions chart
    is_subscriptions_chart = "Subscriptions" in display_name
    
    col1, col2 = st.columns(2)
    
    # Chart configuration with zoom, pan, and download enabled
    chart_config = {
        'displayModeBar': True,
        'displaylogo': False,
        'modeBarButtonsToAdd': ['downloadCsv'],
        'modeBarButtonsToRemove': ['lasso2d', 'select2d'],
        'toImageButtonOptions': {
            'format': 'png',
            'filename': f'{display_name}_chart',
            'height': 600,
            'width': 800,
            'scale': 2
        },
        'scrollZoom': False
    }
    
    # Regular chart
    with col1:
        st.markdown(
            f'<div style="font-size:16px;font-weight:600;color:{colors["text_primary"]};margin-bottom:12px;">{display_name}</div>',
            unsafe_allow_html=True
        )
        
        fig_regular, plans_regular = build_line_chart(
            chart_data_regular, 
            display_name, 
            format_type,
            date_range,
            subscriptions_data=subscriptions_regular,
            is_subscriptions_chart=is_subscriptions_chart
        )
        
        # Render legend
        if plans_regular:
            color_map = build_plan_color_map(plans_regular)
            st.markdown(build_legend_html(plans_regular, color_map), unsafe_allow_html=True)
        
        st.plotly_chart(
            fig_regular, 
            use_container_width=True, 
            config=chart_config,
            key=f"{chart_key}_regular"
        )
    
    # Crystal Ball chart
    with col2:
        st.markdown(
            f'<div style="font-size:16px;font-weight:600;color:{colors["text_primary"]};margin-bottom:12px;">{display_name} (Crystal Ball)</div>',
            unsafe_allow_html=True
        )
        
        fig_crystal, plans_crystal = build_line_chart(
            chart_data_crystal, 
            f"{display_name} (Crystal Ball)", 
            format_type,
            date_range,
            subscriptions_data=subscriptions_crystal,
            is_subscriptions_chart=is_subscriptions_chart
        )
        
        # Render legend
        if plans_crystal:
            color_map = build_plan_color_map(plans_crystal)
            st.markdown(build_legend_html(plans_crystal, color_map), unsafe_allow_html=True)
        
        st.plotly_chart(
            fig_crystal, 
            use_container_width=True, 
            config=chart_config,
            key=f"{chart_key}_crystal"
        )
