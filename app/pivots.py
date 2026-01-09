"""
Pivot Table Components for Variant Analytics Dashboard

Column Widths:
- App: 150px
- Plan: 150px
- Metric: 180px
- Trend: 180px
- Date columns: 100px each

Features:
- First 4 columns frozen
- No text wrapping by default, wraps if user resizes smaller
- Excel-like filter/sort ONLY on App, Plan, Metric
- Single scrollable table (no pagination)
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
            return float(value) * 100
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
    """Process pivot data into flat DataFrame for AG Grid"""
    
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
    
    # Build rows for DataFrame
    rows = []
    for app_name, plan_name in plan_combos:
        for metric in selected_metrics:
            row = {
                "App": app_name,
                "Plan": plan_name,
                "Metric": get_display_metric_name(metric),
                "_metric_key": metric
            }
            
            sparkline_values = []
            
            for date in unique_dates:
                formatted_date = date_map[date]
                key = (app_name, plan_name, date)
                raw_value = lookup.get(key, {}).get(metric, None)
                formatted_value = format_metric_value(raw_value, metric)
                row[formatted_date] = formatted_value
                sparkline_values.insert(0, formatted_value)
            
            row["Trend"] = json.dumps([v for v in sparkline_values if v is not None])
            rows.append(row)
    
    df = pd.DataFrame(rows)
    
    column_order = ["App", "Plan", "Metric", "Trend"] + date_columns
    if "_metric_key" in df.columns:
        column_order.append("_metric_key")
    
    df = df[[c for c in column_order if c in df.columns]]
    
    return df, date_columns


def render_pivot_table(pivot_data, selected_metrics, title, table_id="pivot"):
    """Render pivot table using AG Grid"""
    
    colors = get_theme_colors()
    theme = get_current_theme()
    
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
    
    # Prepare export data
    df_export = df.drop(columns=["_metric_key", "Trend"], errors='ignore')
    csv_data = df_export.to_csv(index=False)
    
    buffer = io.BytesIO()
    df_export.to_excel(buffer, index=False, engine='openpyxl')
    buffer.seek(0)
    excel_data = buffer.getvalue()
    
    # Title row with menu on same line
    title_col, menu_col = st.columns([6, 1])
    
    with title_col:
        st.markdown(f'''
        <div style="
            font-size: 16px;
            font-weight: 600;
            color: {colors['text_primary']};
            margin-bottom: 8px;
        ">{title}</div>
        ''', unsafe_allow_html=True)
    
    with menu_col:
        with st.popover("⋮"):
            st.markdown("**Export Options**")
            
            clean_title = title.replace('📊', '').replace('🔮', '').strip().replace(' ', '_')
            
            st.download_button(
                label="📥 Download CSV",
                data=csv_data,
                file_name=f"{clean_title}.csv",
                mime="text/csv",
                key=f"{table_id}_csv_export",
                use_container_width=True
            )
            
            st.download_button(
                label="📥 Download Excel",
                data=excel_data,
                file_name=f"{clean_title}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"{table_id}_excel_export",
                use_container_width=True
            )
    
    # Configure AG Grid
    gb = GridOptionsBuilder.from_dataframe(df.drop(columns=["_metric_key"], errors='ignore'))
    
    # Default column settings - NO filter/sort
    gb.configure_default_column(
        resizable=True,
        filterable=False,
        sortable=False,
        suppressMenu=True,
        wrapText=True,
        autoHeight=False
    )
    
    # Sparkline renderer
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
            
            const validValues = values.filter(v => v !== null && v !== undefined && !isNaN(v)).map(Number);
            
            if (validValues.length < 2) {
                this.eGui.innerHTML = '<span style="color: #666;">-</span>';
                return;
            }
            
            const width = 100;
            const height = 24;
            const padding = 3;
            
            const min = Math.min(...validValues);
            const max = Math.max(...validValues);
            const range = max - min || 1;
            
            const points = validValues.map((v, i) => {
                const x = padding + (i / (validValues.length - 1)) * (width - 2 * padding);
                const y = height - padding - ((v - min) / range) * (height - 2 * padding);
                return `${x},${y}`;
            }).join(' ');
            
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
    
    # App column - 150px, frozen, with filter/sort, LEFT aligned
    gb.configure_column(
        "App",
        pinned="left",
        width=150,
        minWidth=100,
        filter="agSetColumnFilter",
        sortable=True,
        suppressMenu=False,
        wrapText=True,
        autoHeight=False,
        cellStyle={'textAlign': 'left', 'white-space': 'nowrap', 'overflow': 'hidden', 'text-overflow': 'ellipsis'},
        filterParams={
            'buttons': ['reset', 'apply'],
            'closeOnApply': True
        }
    )
    
    # Plan column - 150px, frozen, with filter/sort, LEFT aligned
    gb.configure_column(
        "Plan",
        pinned="left",
        width=150,
        minWidth=100,
        filter="agSetColumnFilter",
        sortable=True,
        suppressMenu=False,
        wrapText=True,
        autoHeight=False,
        cellStyle={'textAlign': 'left', 'white-space': 'nowrap', 'overflow': 'hidden', 'text-overflow': 'ellipsis'},
        filterParams={
            'buttons': ['reset', 'apply'],
            'closeOnApply': True
        }
    )
    
    # Metric column - 180px, frozen, with filter/sort, LEFT aligned
    gb.configure_column(
        "Metric",
        pinned="left",
        width=180,
        minWidth=120,
        filter="agSetColumnFilter",
        sortable=True,
        suppressMenu=False,
        wrapText=True,
        autoHeight=False,
        cellStyle={'textAlign': 'left', 'white-space': 'nowrap', 'overflow': 'hidden', 'text-overflow': 'ellipsis'},
        filterParams={
            'buttons': ['reset', 'apply'],
            'closeOnApply': True
        }
    )
    
    # Trend column - 180px, frozen, NO filter/sort, CENTER aligned
    gb.configure_column(
        "Trend",
        pinned="left",
        width=180,
        minWidth=100,
        filter=False,
        sortable=False,
        suppressMenu=True,
        cellRenderer=sparkline_renderer,
        headerName="Trend"
    )
    
    # Number formatter for values
    number_formatter = JsCode("""
        function(params) {
            if (params.value === null || params.value === undefined || params.value === '') return '';
            const num = Number(params.value);
            if (isNaN(num)) return params.value;
            return num.toLocaleString('en-IN', {maximumFractionDigits: 2});
        }
    """)
    
    # Date columns - 100px each, NO filter/sort, RIGHT aligned
    for date_col in date_columns:
        gb.configure_column(
            date_col,
            type=["numericColumn"],
            filter=False,
            sortable=False,
            suppressMenu=True,
            valueFormatter=number_formatter,
            width=100,
            minWidth=80,
            wrapText=True,
            autoHeight=False,
            cellStyle={'textAlign': 'right', 'white-space': 'nowrap', 'overflow': 'hidden', 'text-overflow': 'ellipsis'}
        )
    
    # Grid options - NO pagination
    gb.configure_grid_options(
        domLayout='normal',
        enableRangeSelection=True,
        animateRows=True,
        rowHeight=35,
        headerHeight=40,
        suppressRowClickSelection=True,
        enableCellTextSelection=True,
        ensureDomOrder=True,
        suppressPaginationPanel=True
    )
    
    gb.configure_pagination(enabled=False)
    gb.configure_selection(selection_mode="disabled")
    
    grid_options = gb.build()
    
    # Custom CSS
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
            "font-size": "12px !important",
            "white-space": "nowrap !important"
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
        },
        ".ag-icon": {
            "color": f"{colors['text_secondary']} !important"
        },
        ".ag-header-cell-menu-button": {
            "opacity": "0.7 !important"
        },
        ".ag-header-cell-menu-button:hover": {
            "opacity": "1 !important"
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
