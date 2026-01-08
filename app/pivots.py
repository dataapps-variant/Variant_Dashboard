"""
Pivot Table Components for Variant Analytics Dashboard
"""

import streamlit as st
from config import METRICS_CONFIG
from theme import get_theme_colors


def format_indian_number(num):
    """Format number in Indian thousands format (7,00,000)"""
    if num is None or num == "":
        return ""
    try:
        num = int(num)
        s = str(abs(num))
        if len(s) <= 3:
            formatted = s
        else:
            last3 = s[-3:]
            remaining = s[:-3]
            groups = []
            while remaining:
                groups.insert(0, remaining[-2:])
                remaining = remaining[:-2]
            formatted = ",".join(groups) + "," + last3
        return formatted if num >= 0 else "-" + formatted
    except:
        return str(num)


def format_metric_value(value, metric_name):
    """Format value based on metric type"""
    if value is None or value == "":
        return ""
    
    config = METRICS_CONFIG.get(metric_name, {})
    format_type = config.get("format", "number")
    
    try:
        if format_type == "number":
            return format_indian_number(value)
        elif format_type == "percent":
            return f"{float(value) * 100:.2f}"
        elif format_type == "dollar":
            return f"{float(value):.2f}"
        else:
            if isinstance(value, float):
                if value == int(value):
                    return str(int(value))
                return f"{value:.2f}"
            return str(value)
    except:
        return str(value)


def get_display_metric_name(metric_name):
    """Get display name with suffix"""
    config = METRICS_CONFIG.get(metric_name, {})
    display = config.get("display", metric_name)
    suffix = config.get("suffix", "")
    return f"{display}{suffix}"


def process_pivot_data(pivot_data, selected_metrics):
    """Process pivot data and return pivot_rows and date_headers"""
    
    if not pivot_data or "Reporting_Date" not in pivot_data or len(pivot_data["Reporting_Date"]) == 0:
        return None, None
    
    # Get unique dates sorted newest first
    unique_dates = sorted(set(pivot_data["Reporting_Date"]), reverse=True)
    
    # Format dates for column headers
    date_headers = []
    for d in unique_dates:
        if hasattr(d, 'strftime'):
            date_headers.append(d.strftime("%b %d, '%y"))
        else:
            date_headers.append(str(d))
    
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
    
    # Build pivot table rows
    pivot_rows = []
    for app_name, plan_name in plan_combos:
        for metric in selected_metrics:
            row = {
                "App Name": app_name,
                "Plan Name": plan_name,
                "Metric": metric
            }
            # Add date columns
            for date, date_header in zip(unique_dates, date_headers):
                key = (app_name, plan_name, date)
                value = lookup.get(key, {}).get(metric, "")
                row[date_header] = value
            pivot_rows.append(row)
    
    return pivot_rows, date_headers


def build_pivot_html(pivot_rows, date_headers, selected_metrics, title, table_id="pivot"):
    """Build HTML table with frozen columns and proper styling"""
    
    colors = get_theme_colors()
    
    if not pivot_rows:
        return f'''
        <div class="pivot-container" style="
            background: {colors['card_bg']};
            border: 1px solid {colors['border']};
            border-radius: 12px;
            padding: 20px;
        ">
            <div class="pivot-title" style="color: {colors['text_primary']};">{title}</div>
            <p style="color: {colors['text_secondary']};">No data available for selected filters.</p>
        </div>
        '''
    
    # Build table header
    header_html = "<tr>"
    header_html += f'<th style="background: {colors["hover"]}; color: {colors["text_primary"]};">App</th>'
    header_html += f'<th style="background: {colors["hover"]}; color: {colors["text_primary"]};">Plan</th>'
    header_html += f'<th style="background: {colors["hover"]}; color: {colors["text_primary"]};">Metric</th>'
    for date_header in date_headers:
        header_html += f'<th style="background: {colors["hover"]}; color: {colors["text_primary"]}; text-align: right;">{date_header}</th>'
    header_html += "</tr>"
    
    # Organize data for display
    organized_data = {}
    for row in pivot_rows:
        app = row["App Name"]
        plan = row["Plan Name"]
        if app not in organized_data:
            organized_data[app] = {}
        if plan not in organized_data[app]:
            organized_data[app][plan] = []
        organized_data[app][plan].append(row)
    
    # Build table body
    body_html = ""
    
    for app_name in sorted(organized_data.keys()):
        plans = organized_data[app_name]
        app_total_rows = sum(len(metrics) for metrics in plans.values())
        first_app_row = True
        
        for plan_name in sorted(plans.keys()):
            plan_rows = plans[plan_name]
            plan_row_count = len(plan_rows)
            first_plan_row = True
            
            for row in plan_rows:
                metric = row["Metric"]
                
                body_html += "<tr>"
                
                # App Name cell
                if first_app_row:
                    body_html += f'''<td rowspan="{app_total_rows}" style="
                        background: {colors['card_bg']};
                        color: {colors['text_primary']};
                        font-weight: 600;
                        vertical-align: top;
                        border-bottom: 1px solid {colors['border']};
                    ">{app_name}</td>'''
                    first_app_row = False
                
                # Plan Name cell
                if first_plan_row:
                    body_html += f'''<td rowspan="{plan_row_count}" style="
                        background: {colors['card_bg']};
                        color: {colors['text_primary']};
                        font-weight: 500;
                        vertical-align: top;
                        border-bottom: 1px solid {colors['border']};
                    ">{plan_name}</td>'''
                    first_plan_row = False
                
                # Metric cell
                display_metric = get_display_metric_name(metric)
                body_html += f'''<td style="
                    background: {colors['card_bg']};
                    color: {colors['text_primary']};
                    border-bottom: 1px solid {colors['border']};
                ">{display_metric}</td>'''
                
                # Data cells
                for date_header in date_headers:
                    value = row.get(date_header, "")
                    formatted_value = format_metric_value(value, metric)
                    body_html += f'''<td style="
                        background: {colors['card_bg']};
                        color: {colors['text_primary']};
                        text-align: right;
                        border-bottom: 1px solid {colors['border']};
                    ">{formatted_value}</td>'''
                
                body_html += "</tr>"
    
    # Combine all parts
    html = f"""
    <div class="pivot-container" style="
        background: {colors['card_bg']};
        border: 1px solid {colors['border']};
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
    ">
        <div class="pivot-title" style="
            font-size: 16px;
            font-weight: 600;
            color: {colors['text_primary']};
            margin-bottom: 16px;
        ">{title}</div>
        <div class="pivot-wrapper" style="
            max-height: 450px;
            overflow: auto;
        ">
            <table class="pivot-table" style="
                width: 100%;
                border-collapse: separate;
                border-spacing: 0;
                font-size: 13px;
            ">
                <thead>{header_html}</thead>
                <tbody>{body_html}</tbody>
            </table>
        </div>
    </div>
    """
    
    return html


def render_pivot_table(pivot_data, selected_metrics, title, table_id="pivot"):
    """Render a pivot table"""
    pivot_rows, date_headers = process_pivot_data(pivot_data, selected_metrics)
    html = build_pivot_html(pivot_rows, date_headers, selected_metrics, title, table_id)
    st.markdown(html, unsafe_allow_html=True)
