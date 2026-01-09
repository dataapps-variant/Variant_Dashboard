"""
Pivot Table Components for Variant Analytics Dashboard

Features:
- Sparkline trend column (4th column)
- Virtual scrolling for performance
- Export to CSV and Excel (in dropdown menu)
- Collapsible groups by App (click to expand/collapse)
- No merged cells - names repeated in all rows
- Frozen columns: App, Plan, Metric, Trend
- Date format: MM/DD/YYYY
- Excel-like filtering and sorting
- Scroll to top button
"""

import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode
import pandas as pd
import json
import io
from config import METRICS_CONFIG
from theme import get_theme_colors, get_current_theme


def format_metric_value(value, metric_name):
    """Format value based on metric type"""
    if value is None or pd.isna(value):
        return None
    
    config = METRICS_CONFIG.get(metric_name, {})
    format_type = config.get("format", "number")
    
    try:
        if format_type == "number":
            return float(value)
        elif format_type == "percent":
            return float(value) * 100  # Convert to percentage
        elif format_type == "dollar":
            return float(value)
        else:
            return float(value)
    except:
        return None


def get_display_metric_name(metric_name):
    """Get display name with suffix"""
    config = METRICS_CONFIG.get(metric_name, {})
    display = config.get("display", metric_name)
    suffix = config.get("suffix", "")
    return f"{display}{suffix}"


def process_pivot_data_for_aggrid(pivot_data, selected_metrics):
    """
    Process pivot data into flat DataFrame for AG Grid
    
    Returns:
        DataFrame with columns: App, Plan, Metric, Trend, Date1, Date2, ...
    """
    
    if not pivot_data or "Reporting_Date" not in pivot_data or len(pivot_data["Reporting_Date"]) == 0:
        return None, []
    
    # Get unique dates sorted newest first
    unique_dates = sorted(set(pivot_data["Reporting_Date"]), reverse=True)
    
    # Format dates as MM/DD/YYYY for column headers
    date_columns = []
    date_map = {}  # Original date -> formatted date
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
    
    # Sort by App_Name then Plan_Name
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
    
    # Build rows for DataFrame
    rows = []
    for app_name, plan_name in plan_combos:
        for metric in selected_metrics:
            row = {
                "App": app_name,
                "Plan": plan_name,
                "Metric": get_display_metric_name(metric),
                "_metric_key": metric  # Hidden column for formatting
            }
            
            # Collect values for sparkline (oldest to newest for trend)
            sparkline_values = []
            
            # Add date columns (newest first in table, but oldest first for sparkline)
            for date in unique_dates:
                formatted_date = date_map[date]
                key = (app_name, plan_name, date)
                raw_value = lookup.get(key, {}).get(metric, None)
                formatted_value = format_metric_value(raw_value, metric)
                row[formatted_date] = formatted_value
                sparkline_values.insert(0, formatted_value)  # Insert at beginning for chronological order
            
            # Store sparkline data as JSON string (fixes the array issue)
            row["Trend"] = json.dumps([v for v in sparkline_values if v is not None])
            
            rows.append(row)
    
    # Create DataFrame
    df = pd.DataFrame(rows)
    
    # Reorder columns: App, Plan, Metric, Trend, then dates
    column_order = ["App", "Plan", "Metric", "Trend"] + date_columns
    if "_metric_key" in df.columns:
        column_order.append("_metric_key")
    
    df = df[[c for c in column_order if c in df.columns]]
    
    return df, date_columns


def render_pivot_table(pivot_data, selected_metrics, title, table_id="pivot"):
    """Render pivot table using AG Grid with all features"""
    
    colors = get_theme_colors()
    theme = get_current_theme()
    
    # Process data
    df, date_columns = process_pivot_data_for_aggrid(pivot_data, selected_metrics)
    
    if df is None or df.empty:
        st.markdown(f'''
        <div style="
            background: {colors['card_bg']};
            border: 1px solid {colors['border']};
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
        ">
            <div style="
                font-size: 16px;
                font-weight: 600;
                color: {colors['text_primary']};
                margin-bottom: 16px;
            ">{title}</div>
            <p style="color: {colors['text_secondary']};">No data available for selected filters.</p>
        </div>
        ''', unsafe_allow_html=True)
        return
    
    # Title and Menu
    col1, col2 = st.columns([6, 1])
    
    with col1:
        st.markdown(f'''
        <div style="
            font-size: 16px;
            font-weight: 600;
            color: {colors['text_primary']};
            margin-bottom: 12px;
        ">{title}</div>
        ''', unsafe_allow_html=True)
    
    with col2:
        # Three-dot menu with export options
        with st.popover("⋮"):
            st.markdown("**Export Options**")
            
            # CSV Export
            csv_data = df.drop(columns=["_metric_key", "Trend"], errors='ignore').to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv_data,
                file_name=f"{title.replace(' ', '_').replace('📊', '').replace('🔮', '').strip()}.csv",
                mime="text/csv",
                key=f"{table_id}_csv_export",
                use_container_width=True
            )
            
            # Excel Export
            buffer = io.BytesIO()
            df_export = df.drop(columns=["_metric_key", "Trend"], errors='ignore')
            df_export.to_excel(buffer, index=False, engine='openpyxl')
            buffer.seek(0)
            st.download_button(
                label="📥 Download Excel",
                data=buffer,
                file_name=f"{title.replace(' ', '_').replace('📊', '').replace('🔮', '').strip()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"{table_id}_excel_export",
                use_container_width=True
            )
            
            st.markdown("---")
            
            # Scroll to top
            st.markdown(f'''
            <a href="#top" style="text-decoration: none;">
                <div style="
                    background: {colors['accent']};
                    color: white;
                    padding: 8px 16px;
                    border-radius: 4px;
                    text-align: center;
                    cursor: pointer;
                ">⬆️ Scroll to Top</div>
            </a>
            ''', unsafe_allow_html=True)
    
    # Configure AG Grid
    gb = GridOptionsBuilder.from_dataframe(df.drop(columns=["_metric_key"], errors='ignore'))
    
    # General settings
    gb.configure_default_column(
        resizable=True,
        filterable=True,
        sortable=True,
        filter="agTextColumnFilter"
    )
    
    # Sparkline renderer for Trend column - parses JSON string
    sparkline_renderer = JsCode("""
    class SparklineRenderer {
        init(params) {
            this.eGui = document.createElement('div');
            this.eGui.style.width = '100%';
            this.eGui.style.height = '100%';
            this.eGui.style.display = 'flex';
            this.eGui.style.alignItems = 'center';
            this.eGui.style.justifyContent = 'center';
            
            let values = [];
            try {
                // Parse JSON string to array
                if (typeof params.value === 'string') {
                    values = JSON.parse(params.value);
                } else if (Array.isArray(params.value)) {
                    values = params.value;
                }
            } catch (e) {
                values = [];
            }
            
            if (!values || values.length === 0) {
                this.eGui.innerHTML = '<span style="color: #666;">-</span>';
                return;
            }
            
            // Filter out nulls and convert to numbers
            const validValues = values.filter(v => v !== null && v !== undefined && !isNaN(v)).map(Number);
            
            if (validValues.length < 2) {
                this.eGui.innerHTML = '<span style="color: #666;">-</span>';
                return;
            }
            
            // Create SVG sparkline
            const width = 80;
            const height = 25;
            const padding = 3;
            
            const min = Math.min(...validValues);
            const max = Math.max(...validValues);
            const range = max - min || 1;
            
            // Calculate points
            const points = validValues.map((v, i) => {
                const x = padding + (i / (validValues.length - 1)) * (width - 2 * padding);
                const y = height - padding - ((v - min) / range) * (height - 2 * padding);
                return `${x},${y}`;
            }).join(' ');
            
            // Determine color based on trend (first vs last)
            const firstVal = validValues[0];
            const lastVal = validValues[validValues.length - 1];
            const color = lastVal >= firstVal ? '#10B981' : '#EF4444';
            
            this.eGui.innerHTML = `
                <svg width="${width}" height="${height}" style="overflow: visible;">
                    <polyline
                        points="${points}"
                        fill="none"
                        stroke="${color}"
                        stroke-width="1.5"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                    />
                </svg>
            `;
        }
        
        getGui() {
            return this.eGui;
        }
        
        refresh(params) {
            return false;
        }
    }
    """)
    
    # Configure fixed columns
    gb.configure_column(
        "App",
        pinned="left",
        width=100,
        filter="agSetColumnFilter",
        rowGroup=True,
        hide=True
    )
    
    gb.configure_column(
        "Plan",
        pinned="left",
        width=130,
        filter="agSetColumnFilter"
    )
    
    gb.configure_column(
        "Metric",
        pinned="left",
        width=180,
        filter="agSetColumnFilter"
    )
    
    gb.configure_column(
        "Trend",
        pinned="left",
        width=100,
        filter=False,
        sortable=False,
        cellRenderer=sparkline_renderer,
        headerName="Trend 📈"
    )
    
    # Number formatter for Indian number system
    number_formatter = JsCode("""
        function(params) {
            if (params.value === null || params.value === undefined || params.value === '') return '';
            const num = Number(params.value);
            if (isNaN(num)) return params.value;
            return num.toLocaleString('en-IN', {maximumFractionDigits: 2});
        }
    """)
    
    # Configure date columns with number formatting
    for date_col in date_columns:
        gb.configure_column(
            date_col,
            type=["numericColumn"],
            filter="agNumberColumnFilter",
            valueFormatter=number_formatter,
            width=110
        )
    
    # Grid options
    gb.configure_grid_options(
        domLayout='normal',
        enableRangeSelection=True,
        groupDisplayType='groupRows',
        groupDefaultExpanded=1,
        animateRows=True,
        rowHeight=35,
        headerHeight=40,
        suppressRowClickSelection=True,
        enableCellTextSelection=True,
        ensureDomOrder=True
    )
    
    # Pagination for virtual scrolling
    gb.configure_pagination(enabled=True, paginationAutoPageSize=False, paginationPageSize=50)
    
    # Selection disabled
    gb.configure_selection(selection_mode="disabled")
    
    # Build grid options
    grid_options = gb.build()
    
    # Custom CSS for theme
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
            "font-size": "13px !important"
        },
        ".ag-cell": {
            "color": f"{colors['text_primary']} !important",
            "font-size": "13px !important",
            "border-right": f"1px solid {colors['border']} !important"
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
        ".ag-group-expanded, .ag-group-contracted": {
            "color": f"{colors['accent']} !important",
            "cursor": "pointer !important"
        },
        ".ag-group-value": {
            "font-weight": "600 !important",
            "color": f"{colors['text_primary']} !important"
        },
        ".ag-paging-panel": {
            "background-color": f"{colors['surface']} !important",
            "color": f"{colors['text_primary']} !important",
            "border-top": f"1px solid {colors['border']} !important"
        },
        ".ag-pinned-left-header, .ag-pinned-left-cols-container": {
            "border-right": f"2px solid {colors['border']} !important"
        },
        ".ag-icon": {
            "color": f"{colors['text_secondary']} !important"
        },
        ".ag-header-cell-menu-button": {
            "opacity": "1 !important"
        }
    }
    
    # AG Grid Theme
    ag_theme = "ag-theme-alpine-dark" if theme == "dark" else "ag-theme-alpine"
    
    # Render AG Grid
    AgGrid(
        df.drop(columns=["_metric_key"], errors='ignore'),
        gridOptions=grid_options,
        custom_css=custom_css,
        height=450,
        theme=ag_theme,
        allow_unsafe_jscode=True,
        key=f"{table_id}_aggrid",
        update_mode=GridUpdateMode.NO_UPDATE
    )
