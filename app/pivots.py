"""
Pivot Table Components for Variant Analytics Dashboard
- AG Grid with sparklines
- Proper alignment: Headers center, App/Plan/Metric left, Dates right
- Auto-fit columns
- Title and menu on same line
"""

import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
from config import METRICS_CONFIG
from theme import get_theme_colors
from colors import build_plan_color_map


def render_pivot_table(data, metrics, title, key_prefix=""):
    """
    Render a pivot table with AG Grid and sparklines
    
    Alignment rules:
    - Row 1 headers: Center
    - App/Plan/Metric: Left
    - Trend: Center
    - Date values: Right
    - Auto-fit columns
    
    Args:
        data: Dict with App_Name, Plan_Name, Reporting_Date, and metric columns
        metrics: List of metric column names to display
        title: Table title
        key_prefix: Unique key prefix for widgets
    """
    colors = get_theme_colors()
    
    # Title row with menu on same line
    title_col, menu_col = st.columns([6, 1])
    
    with title_col:
        st.markdown(f'''
        <div style="
            font-size: 18px;
            font-weight: 600;
            color: {colors['text_primary']};
            margin-bottom: 12px;
        ">{title}</div>
        ''', unsafe_allow_html=True)
    
    with menu_col:
        with st.popover("⋮"):
            if st.button("📄 Export PDF", key=f"{key_prefix}_pdf", use_container_width=True):
                st.info("PDF export - Coming soon")
            if st.button("📥 Export CSV", key=f"{key_prefix}_csv", use_container_width=True):
                st.info("CSV export - Coming soon")
    
    # Check for empty data
    if not data or "Plan_Name" not in data or len(data["Plan_Name"]) == 0:
        st.info("No data available for selected filters.")
        return
    
    # Build DataFrame for pivot
    df = pd.DataFrame(data)
    
    # Convert dates to string for display
    if "Reporting_Date" in df.columns:
        df["Reporting_Date"] = pd.to_datetime(df["Reporting_Date"]).dt.strftime("%Y-%m-%d")
    
    # Create pivot structure: App, Plan, Metric, Trend, then date columns
    pivot_rows = []
    
    # Get unique plans
    unique_plans = df[["App_Name", "Plan_Name"]].drop_duplicates().values.tolist()
    
    # Get unique dates sorted
    unique_dates = sorted(df["Reporting_Date"].unique())
    
    # Build color map for sparklines
    plan_names = [p[1] for p in unique_plans]
    color_map = build_plan_color_map(plan_names)
    
    for app, plan in unique_plans:
        plan_df = df[df["Plan_Name"] == plan]
        
        for metric in metrics:
            if metric not in plan_df.columns:
                continue
            
            row = {
                "App": app,
                "Plan": plan,
                "Metric": METRICS_CONFIG.get(metric, {}).get("display", metric),
                "_metric_key": metric,
                "_plan_color": color_map.get(plan, "#6B7280")
            }
            
            # Get values for each date
            values_for_trend = []
            for date in unique_dates:
                date_data = plan_df[plan_df["Reporting_Date"] == date]
                if len(date_data) > 0:
                    val = date_data[metric].iloc[0]
                    row[date] = val
                    values_for_trend.append(val if val is not None else 0)
                else:
                    row[date] = None
                    values_for_trend.append(0)
            
            row["_trend_data"] = values_for_trend
            pivot_rows.append(row)
    
    if not pivot_rows:
        st.info("No data to display for selected metrics.")
        return
    
    pivot_df = pd.DataFrame(pivot_rows)
    
    # Configure AG Grid
    gb = GridOptionsBuilder.from_dataframe(pivot_df)
    
    # Hide internal columns
    gb.configure_column("_metric_key", hide=True)
    gb.configure_column("_plan_color", hide=True)
    gb.configure_column("_trend_data", hide=True)
    
    # Configure visible columns - LEFT aligned
    gb.configure_column("App", pinned="left", width=80, cellStyle={"textAlign": "left"})
    gb.configure_column("Plan", pinned="left", width=120, cellStyle={"textAlign": "left"})
    gb.configure_column("Metric", pinned="left", width=150, cellStyle={"textAlign": "left"})
    
    # Sparkline renderer for Trend column
    sparkline_renderer = JsCode("""
    class SparklineRenderer {
        init(params) {
            this.eGui = document.createElement('div');
            this.eGui.style.width = '100%';
            this.eGui.style.height = '100%';
            this.eGui.style.display = 'flex';
            this.eGui.style.alignItems = 'center';
            this.eGui.style.justifyContent = 'center';
            
            const data = params.data._trend_data || [];
            const color = params.data._plan_color || '#6B7280';
            
            if (data.length > 0) {
                const canvas = document.createElement('canvas');
                canvas.width = 80;
                canvas.height = 24;
                this.eGui.appendChild(canvas);
                
                const ctx = canvas.getContext('2d');
                const max = Math.max(...data);
                const min = Math.min(...data);
                const range = max - min || 1;
                
                ctx.beginPath();
                ctx.strokeStyle = color;
                ctx.lineWidth = 1.5;
                
                data.forEach((val, i) => {
                    const x = (i / (data.length - 1)) * 76 + 2;
                    const y = 22 - ((val - min) / range) * 20;
                    if (i === 0) ctx.moveTo(x, y);
                    else ctx.lineTo(x, y);
                });
                
                ctx.stroke();
            }
        }
        getGui() { return this.eGui; }
    }
    """)
    
    # Value formatter for date columns - RIGHT aligned
    value_formatter = JsCode("""
    function(params) {
        if (params.value === null || params.value === undefined) return '--';
        const metric = params.data._metric_key;
        if (metric && (metric.includes('Rate') || metric.includes('Retention'))) {
            return (params.value * 100).toFixed(2) + '%';
        } else if (metric && (metric.includes('CAC') || metric.includes('ARPU') || metric.includes('LTV'))) {
            return '$' + params.value.toFixed(2);
        }
        return params.value.toLocaleString();
    }
    """)
    
    # Configure date columns (right-aligned)
    for date in unique_dates:
        display_date = pd.to_datetime(date).strftime("%b %d")
        gb.configure_column(
            date,
            headerName=display_date,
            width=90,
            cellStyle={"textAlign": "right"},
            valueFormatter=value_formatter
        )
    
    # Grid options
    gb.configure_default_column(
        resizable=True,
        sortable=True,
        filter=True
    )
    
    gb.configure_grid_options(
        domLayout='autoHeight',
        rowHeight=36,
        headerHeight=40,
        suppressHorizontalScroll=False,
        enableRangeSelection=True
    )
    
    grid_options = gb.build()
    
    # Inject Trend column into column definitions
    col_defs = grid_options.get("columnDefs", [])
    
    # Find Metric column index and insert Trend after it
    metric_idx = next((i for i, c in enumerate(col_defs) if c.get("field") == "Metric"), -1)
    if metric_idx >= 0:
        trend_col = {
            "headerName": "Trend",
            "field": "Trend",
            "width": 100,
            "cellRenderer": sparkline_renderer,
            "cellStyle": {"textAlign": "center"},
            "sortable": False,
            "filter": False
        }
        col_defs.insert(metric_idx + 1, trend_col)
    
    grid_options["columnDefs"] = col_defs
    
    # Render AG Grid
    AgGrid(
        pivot_df,
        gridOptions=grid_options,
        allow_unsafe_jscode=True,
        theme="alpine-dark" if colors["background"] == "#0F172A" else "alpine",
        fit_columns_on_grid_load=True,
        height=min(400, 60 + len(pivot_rows) * 36),
        key=f"{key_prefix}_grid"
    )
