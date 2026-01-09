"""
Pivot Table Components for Variant Analytics Dashboard

OPTIMIZED VERSION - Changes made:
1. Removed sparklines/Trend column
2. Removed Excel export (CSV only)
3. Removed JsCode valueFormatter (using built-in)
4. Added @st.cache_data for data processing
5. Set animateRows=False
6. Set enableRangeSelection=False
7. Simplified CSS (removed 2 minor rules)
8. Kept frozen columns (App, Plan, Metric) with built-in pinned="left"
9. 2 decimal places for all numbers
10. Right-aligned date columns
11. Flex sizing for frozen columns (auto-adjust width)
"""

import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
import pandas as pd
from config import METRICS_CONFIG
from theme import get_theme_colors, get_current_theme


def format_metric_value(value, metric_name):
    """Format value based on metric type - rounded to 2 decimal places"""
    if value is None or pd.isna(value):
        return None
    
    config = METRICS_CONFIG.get(metric_name, {})
    format_type = config.get("format", "number")
    
    try:
        if format_type == "percent":
            return round(float(value) * 100, 2)  # 2 decimal places
        return round(float(value), 2)  # 2 decimal places
    except:
        return None


def get_display_metric_name(metric_name):
    """Get display name with suffix"""
    config = METRICS_CONFIG.get(metric_name, {})
    display = config.get("display", metric_name)
    suffix = config.get("suffix", "")
    return f"{display}{suffix}"


@st.cache_data(ttl=1800)
def process_pivot_data_for_aggrid(_pivot_data, selected_metrics):
    """
    Process pivot data into flat DataFrame for AG Grid
    CACHED for 30 minutes
    
    Note: _pivot_data has underscore prefix to tell Streamlit not to hash it
    """
    pivot_data = _pivot_data
    
    if not pivot_data or "Reporting_Date" not in pivot_data or len(pivot_data["Reporting_Date"]) == 0:
        return None, []
    
    # Get unique dates sorted newest first
    unique_dates = sorted(set(pivot_data["Reporting_Date"]), reverse=True)
    
    # Format dates as MM/DD/YYYY for column headers
    date_columns = []
    date_map = {}
    for d in unique_dates:
        if hasattr(d, 'strftime'):
            formatted = d.strftime("%m/%d/%Y")
        else:
            formatted = str(d)
        date_columns.append(formatted)
        date_map[d] = formatted
    
    # Get unique App_Name + Plan_Name combinations
    plan_combos = []
    seen = set()
    for i in range(len(pivot_data["App_Name"])):
        combo = (pivot_data["App_Name"][i], pivot_data["Plan_Name"][i])
        if combo not in seen:
            plan_combos.append(combo)
            seen.add(combo)
    
    plan_combos.sort(key=lambda x: (x[0], x[1]))
    
    # Build lookup dictionary
    lookup = {}
    for i in range(len(pivot_data["Reporting_Date"])):
        app = pivot_data["App_Name"][i]
        plan = pivot_data["Plan_Name"][i]
        date = pivot_data["Reporting_Date"][i]
        
        key = (app, plan, date)
        if key not in lookup:
            lookup[key] = {}
        
        for metric in selected_metrics:
            if metric in pivot_data:
                lookup[key][metric] = pivot_data[metric][i]
    
    # Build rows for DataFrame (NO Trend column)
    rows = []
    for app_name, plan_name in plan_combos:
        for metric in selected_metrics:
            row = {
                "App": app_name,
                "Plan": plan_name,
                "Metric": get_display_metric_name(metric),
                "_metric_key": metric
            }
            
            for date in unique_dates:
                formatted_date = date_map[date]
                key = (app_name, plan_name, date)
                raw_value = lookup.get(key, {}).get(metric, None)
                formatted_value = format_metric_value(raw_value, metric)
                row[formatted_date] = formatted_value
            
            rows.append(row)
    
    df = pd.DataFrame(rows)
    
    # Column order: App, Plan, Metric, then date columns (NO Trend)
    column_order = ["App", "Plan", "Metric"] + date_columns
    if "_metric_key" in df.columns:
        column_order.append("_metric_key")
    
    df = df[[c for c in column_order if c in df.columns]]
    
    return df, date_columns


def render_pivot_table(pivot_data, selected_metrics, title, table_id="pivot"):
    """
    Render pivot table using AG Grid
    
    Features:
    - Frozen columns: App, Plan, Metric (built-in pinned="left")
    - Filtering on App, Plan, Metric (built-in agSetColumnFilter)
    - Sorting enabled
    - CSV export only
    - No sparklines
    - No animations (animateRows=False)
    - No range selection (enableRangeSelection=False)
    - 2 decimal places for numbers
    - Right-aligned date columns
    - Flex sizing for frozen columns
    """
    
    colors = get_theme_colors()
    theme = get_current_theme()
    
    # Process data (CACHED)
    df, date_columns = process_pivot_data_for_aggrid(pivot_data, selected_metrics)
    
    if df is None or df.empty:
        st.subheader(title)
        st.info("No data available for selected filters.")
        return
    
    # Prepare CSV export data
    df_export = df.drop(columns=["_metric_key"], errors='ignore')
    csv_data = df_export.to_csv(index=False)
    
    # Title and menu row
    col_title, col_menu = st.columns([10, 1])
    
    with col_title:
        st.subheader(title)
    
    with col_menu:
        with st.popover("⋮"):
            st.markdown("**Export**")
            
            clean_title = title.replace('📊', '').replace('🔮', '').strip().replace(' ', '_')
            
            st.download_button(
                label="📥 Download CSV",
                data=csv_data,
                file_name=f"{clean_title}.csv",
                mime="text/csv",
                key=f"{table_id}_csv_export",
                use_container_width=True
            )
    
    # Configure AG Grid
    gb = GridOptionsBuilder.from_dataframe(df.drop(columns=["_metric_key"], errors='ignore'))
    
    # Default column settings - NO JsCode
    gb.configure_default_column(
        resizable=True,
        filterable=False,
        sortable=False,
        suppressMenu=True,
        wrapText=False,
        autoHeight=False
    )
    
    # App column - frozen, with filter/sort, flex sizing
    gb.configure_column(
        "App",
        pinned="left",
        flex=1,  # Flex sizing - auto adjusts
        filter="agSetColumnFilter",
        sortable=True,
        suppressMenu=False,
        filterParams={
            'buttons': ['reset', 'apply'],
            'closeOnApply': True
        }
    )
    
    # Plan column - frozen, with filter/sort, flex sizing
    gb.configure_column(
        "Plan",
        pinned="left",
        flex=2,  # Flex sizing - auto adjusts
        filter="agSetColumnFilter",
        sortable=True,
        suppressMenu=False,
        filterParams={
            'buttons': ['reset', 'apply'],
            'closeOnApply': True
        }
    )
    
    # Metric column - frozen, with filter/sort, flex sizing
    gb.configure_column(
        "Metric",
        pinned="left",
        flex=2,  # Flex sizing - auto adjusts
        filter="agSetColumnFilter",
        sortable=True,
        suppressMenu=False,
        filterParams={
            'buttons': ['reset', 'apply'],
            'closeOnApply': True
        }
    )
    
    # Date columns - right aligned, numeric type
    for date_col in date_columns:
        gb.configure_column(
            date_col,
            type=["numericColumn"],
            minWidth=85,
            maxWidth=120,
            cellStyle={"textAlign": "right"}  # Right-aligned
        )
    
    # Grid options - OPTIMIZED (no animations, no range selection)
    gb.configure_grid_options(
        domLayout='normal',
        rowHeight=35,
        headerHeight=40,
        suppressRowClickSelection=True,
        enableCellTextSelection=True,
        ensureDomOrder=True,
        # DISABLED for performance:
        animateRows=False,
        enableRangeSelection=False,
    )
    
    gb.configure_pagination(enabled=False)
    gb.configure_selection(selection_mode="disabled")
    
    grid_options = gb.build()
    
    # Custom CSS - SIMPLIFIED (removed .ag-icon and .ag-header-cell-menu-button)
    custom_css = {
        ".ag-root-wrapper": {
            "border-radius": "8px !important",
            "border": f"1px solid {colors['border']} !important"
        },
        ".ag-header": {
            "background-color": f"{colors['surface']} !important",
            "border-bottom": f"2px solid {colors['border']} !important"
        },
        ".ag-header-cell-text": {
            "color": f"{colors['text_primary']} !important",
            "font-weight": "600 !important",
            "font-size": "12px !important"
        },
        ".ag-cell": {
            "color": f"{colors['text_primary']} !important",
            "font-size": "12px !important",
            "border-right": f"1px solid {colors['border']} !important",
            "display": "flex !important",
            "align-items": "center !important"
        },
        ".ag-row": {
            "border-bottom": f"1px solid {colors['border']} !important"
        },
        ".ag-row-odd": {
            "background-color": f"{colors['surface']} !important"
        },
        ".ag-row-even": {
            "background-color": f"{colors['card_bg']} !important"
        },
        ".ag-row-hover": {
            "background-color": f"{colors['hover']} !important"
        },
        ".ag-pinned-left-header, .ag-pinned-left-cols-container": {
            "border-right": f"2px solid {colors['border']} !important"
        }
    }
    
    ag_theme = "ag-theme-alpine-dark" if theme == "dark" else "ag-theme-alpine"
    
    # Dynamic height (max 500px)
    row_count = len(df)
    calculated_height = min(40 + (row_count * 35) + 20, 500)
    
    AgGrid(
        df.drop(columns=["_metric_key"], errors='ignore'),
        gridOptions=grid_options,
        custom_css=custom_css,
        height=calculated_height,
        theme=ag_theme,
        allow_unsafe_jscode=True,
        key=f"{table_id}_aggrid",
        update_mode=GridUpdateMode.NO_UPDATE
    )
