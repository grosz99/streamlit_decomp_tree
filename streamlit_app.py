"""
Decomposition Tree - Power BI Style with D3.js
A drill-down analysis tool using st.components.v1.html for D3 visualization
Compatible with Streamlit in Snowflake (Custom UI feature GA August 2024)
"""

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import json
from typing import Dict, List, Tuple

# Page config
st.set_page_config(
    page_title="Decomposition Tree",
    page_icon="🌳",
    layout="wide"
)

# ============================================
# MOCK DATA GENERATION
# ============================================

@st.cache_data
def generate_mock_data() -> pd.DataFrame:
    """Generate realistic mock transit data similar to Power BI example"""
    np.random.seed(42)

    # Structure similar to the Power BI image (Transit/Bus data)
    divisions = ['Brooklyn', 'Queens South', 'Staten Island', 'Bronx', 'Queens North', 'Manhattan']

    depots = {
        'Brooklyn': ['Jackie Gleason', 'Fresh Pond', 'East New York', 'Ulmer Park', 'Flatbush'],
        'Queens South': ['Jamaica', 'JFK', 'Rockaways'],
        'Staten Island': ['Castleton', 'Charleston', 'Yukon'],
        'Bronx': ['Gun Hill', 'Kingsbridge', 'West Farms'],
        'Queens North': ['Casey Stengel', 'LaGuardia', 'College Point'],
        'Manhattan': ['Mother Clara Hale', 'Manhattanville', 'Michael Quill']
    }

    routes_per_depot = ['B37', 'B68', 'B16', 'B11', 'B4', 'B43', 'B70', 'B8', 'B61', 'B63']
    directions = ['SB', 'NB']
    periods = ['Overnight', 'Midday', 'PM', 'AM']

    data = []
    for _ in range(2000):
        division = np.random.choice(divisions, p=[0.25, 0.18, 0.12, 0.15, 0.15, 0.15])
        depot = np.random.choice(depots[division])
        route = np.random.choice(routes_per_depot)
        direction = np.random.choice(directions, p=[0.52, 0.48])
        period = np.random.choice(periods, p=[0.15, 0.30, 0.30, 0.25])

        # OTP (On-Time Performance) - percentage metric
        base_otp = np.random.uniform(55, 78)
        # Adjust by various factors
        if division == 'Manhattan':
            base_otp += 5
        if period == 'Overnight':
            base_otp -= 8
        if period == 'AM':
            base_otp += 3

        otp = min(max(base_otp + np.random.uniform(-5, 5), 50), 85)

        data.append({
            'Division': division,
            'Depot': depot,
            'Route': route,
            'Direction': direction,
            'Period': period,
            'OTP': round(otp, 1),
            'Trips': np.random.randint(50, 500)
        })

    return pd.DataFrame(data)

# ============================================
# DATA CONFIGURATION
# ============================================

DATA_CONFIG = {
    "metrics": {
        "OTP": {"column": "OTP", "format": "percent", "label": "On-Time Performance"},
        "Trips": {"column": "Trips", "format": "number", "label": "Total Trips"}
    },
    "dimensions": ["Division", "Depot", "Route", "Direction", "Period"]
}

# ============================================
# HELPER FUNCTIONS
# ============================================

def filter_data(df: pd.DataFrame, drill_path: List[Tuple[str, str]]) -> pd.DataFrame:
    """Filter dataframe based on drill path"""
    filtered_df = df.copy()
    for dimension, value in drill_path:
        filtered_df = filtered_df[filtered_df[dimension] == value]
    return filtered_df

def get_available_dimensions(drill_path: List[Tuple[str, str]]) -> List[str]:
    """Get dimensions not yet drilled into"""
    used_dimensions = {dim for dim, _ in drill_path}
    return [dim for dim in DATA_CONFIG["dimensions"] if dim not in used_dimensions]

def calculate_decomposition(df: pd.DataFrame, dimension: str, metric: str) -> List[Dict]:
    """Calculate decomposition breakdown for a dimension"""
    metric_config = DATA_CONFIG["metrics"][metric]
    metric_col = metric_config["column"]

    if metric == "OTP":
        # Weighted average for OTP
        decomp = df.groupby(dimension).apply(
            lambda x: np.average(x[metric_col], weights=x['Trips'])
        ).reset_index()
        decomp.columns = ['name', 'value']
    else:
        decomp = df.groupby(dimension)[metric_col].sum().reset_index()
        decomp.columns = ['name', 'value']

    decomp = decomp.sort_values('value', ascending=True)  # Sort ascending for horizontal bars

    return decomp.to_dict('records')

def get_color_scale(value: float, min_val: float, max_val: float) -> str:
    """Get color based on value - green for high, yellow for mid, orange/red for low"""
    if max_val == min_val:
        normalized = 0.5
    else:
        normalized = (value - min_val) / (max_val - min_val)

    if normalized >= 0.7:
        return "#2E7D32"  # Green
    elif normalized >= 0.5:
        return "#8BC34A"  # Light green
    elif normalized >= 0.3:
        return "#FFC107"  # Yellow/Amber
    else:
        return "#FF9800"  # Orange

def build_tree_data(df: pd.DataFrame, drill_path: List[Tuple[str, str]], metric: str) -> Dict:
    """Build the complete tree data structure for D3"""
    metric_config = DATA_CONFIG["metrics"][metric]

    # Calculate root value
    if metric == "OTP":
        root_value = np.average(df['OTP'], weights=df['Trips'])
    else:
        root_value = df[metric_config["column"]].sum()

    tree_data = {
        "name": "CJTP",  # Root node name
        "value": round(root_value, 1),
        "dimension": None,
        "path": [],
        "children": []
    }

    # Build each level of the tree based on drill path and available dimensions
    available_dims = get_available_dimensions(drill_path)

    for i, dim in enumerate(available_dims[:5]):  # Max 5 levels
        # Get filtered data up to current path
        current_path = drill_path[:] if i == 0 else drill_path + [(available_dims[j], None) for j in range(i)]
        filtered = filter_data(df, drill_path)

        decomp = calculate_decomposition(filtered, dim, metric)

        level_data = {
            "dimension": dim,
            "items": decomp
        }
        tree_data["children"].append(level_data)

    return tree_data

# ============================================
# D3 VISUALIZATION COMPONENT
# ============================================

def create_d3_decomposition_tree(df: pd.DataFrame, drill_path: List[Tuple[str, str]],
                                  selected_metric: str) -> str:
    """Create the D3.js visualization HTML"""

    metric_config = DATA_CONFIG["metrics"][selected_metric]
    available_dims = get_available_dimensions(drill_path)

    # Calculate root value
    root_df = filter_data(df, drill_path)
    if selected_metric == "OTP":
        root_value = np.average(root_df['OTP'], weights=root_df['Trips'])
    else:
        root_value = root_df[metric_config["column"]].sum()

    # Build columns data
    columns_data = []

    # Add drilled path nodes
    path_nodes = [{"name": "CJTP", "value": round(root_value, 1), "dimension": None}]

    current_df = df.copy()
    for dim, val in drill_path:
        current_df = current_df[current_df[dim] == val]
        if selected_metric == "OTP":
            node_value = np.average(current_df['OTP'], weights=current_df['Trips'])
        else:
            node_value = current_df[metric_config["column"]].sum()
        path_nodes.append({"name": val, "value": round(node_value, 1), "dimension": dim})

    # Build decomposition columns for available dimensions
    filtered_df = filter_data(df, drill_path)

    for dim in available_dims[:5]:
        decomp = calculate_decomposition(filtered_df, dim, selected_metric)
        values = [item['value'] for item in decomp]
        min_val, max_val = min(values), max(values)

        for item in decomp:
            item['color'] = get_color_scale(item['value'], min_val, max_val)

        columns_data.append({
            "dimension": dim,
            "items": decomp
        })

    # Convert to JSON for JavaScript
    path_json = json.dumps(path_nodes)
    columns_json = json.dumps(columns_data)
    drill_path_json = json.dumps(drill_path)
    format_type = metric_config["format"]

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://d3js.org/d3.v7.min.js"></script>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: #fafafa;
                overflow-x: auto;
            }}
            .container {{
                display: flex;
                align-items: flex-start;
                padding: 20px;
                min-width: max-content;
            }}
            .column {{
                display: flex;
                flex-direction: column;
                margin-right: 5px;
                min-width: 180px;
            }}
            .column-header {{
                font-size: 13px;
                font-weight: 600;
                color: #333;
                padding: 8px 12px;
                border-bottom: 2px solid #ddd;
                margin-bottom: 8px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            .column-header .clear-btn {{
                cursor: pointer;
                color: #999;
                font-size: 16px;
            }}
            .column-header .clear-btn:hover {{
                color: #333;
            }}
            .node {{
                display: flex;
                align-items: center;
                padding: 6px 10px;
                margin: 3px 0;
                border-radius: 4px;
                cursor: pointer;
                transition: all 0.2s;
                position: relative;
            }}
            .node:hover {{
                background: #f0f0f0;
            }}
            .node.selected {{
                background: #e3f2fd;
            }}
            .node-bar {{
                height: 22px;
                border-radius: 2px;
                margin-right: 10px;
                min-width: 5px;
            }}
            .node-content {{
                flex: 1;
                display: flex;
                flex-direction: column;
            }}
            .node-name {{
                font-size: 13px;
                font-weight: 500;
                color: #333;
            }}
            .node-value {{
                font-size: 12px;
                color: #666;
            }}
            .node-bar-bg {{
                position: absolute;
                right: 10px;
                top: 50%;
                transform: translateY(-50%);
                width: 60px;
                height: 8px;
                background: #e0e0e0;
                border-radius: 4px;
                overflow: hidden;
            }}
            .node-bar-fill {{
                height: 100%;
                border-radius: 4px;
            }}
            .path-node {{
                background: linear-gradient(135deg, #1976D2 0%, #1565C0 100%);
                color: white;
                padding: 15px 20px;
                border-radius: 6px;
                margin-right: 10px;
                min-width: 100px;
                text-align: center;
                box-shadow: 0 2px 8px rgba(0,0,0,0.15);
            }}
            .path-node .label {{
                font-size: 11px;
                opacity: 0.9;
                margin-bottom: 4px;
            }}
            .path-node .value {{
                font-size: 18px;
                font-weight: 600;
            }}
            .path-connector {{
                display: flex;
                align-items: center;
                justify-content: center;
                width: 40px;
            }}
            .connector-line {{
                stroke: #1976D2;
                stroke-width: 2;
                fill: none;
            }}
            svg.tree-svg {{
                overflow: visible;
            }}
        </style>
    </head>
    <body>
        <div id="tree-container"></div>

        <script>
            const pathNodes = {path_json};
            const columnsData = {columns_json};
            const drillPath = {drill_path_json};
            const formatType = "{format_type}";

            function formatValue(val) {{
                if (formatType === "percent") {{
                    return val.toFixed(1) + "%";
                }} else {{
                    return val.toLocaleString();
                }}
            }}

            function sendDrillAction(dimension, value) {{
                // Send message to Streamlit parent
                window.parent.postMessage({{
                    type: 'streamlit:setComponentValue',
                    data: {{ action: 'drill', dimension: dimension, value: value }}
                }}, '*');
            }}

            function sendClearAction(dimension) {{
                window.parent.postMessage({{
                    type: 'streamlit:setComponentValue',
                    data: {{ action: 'clear', dimension: dimension }}
                }}, '*');
            }}

            // Build the visualization
            const container = d3.select("#tree-container");
            const mainDiv = container.append("div").attr("class", "container");

            // Render path nodes (drilled items)
            pathNodes.forEach((node, i) => {{
                if (i > 0) {{
                    // Add connector
                    const connectorSvg = mainDiv.append("svg")
                        .attr("width", 40)
                        .attr("height", 60)
                        .attr("class", "tree-svg");

                    connectorSvg.append("path")
                        .attr("d", "M0,30 C20,30 20,30 40,30")
                        .attr("class", "connector-line");
                }}

                const pathNode = mainDiv.append("div")
                    .attr("class", "path-node");

                pathNode.append("div")
                    .attr("class", "label")
                    .text(node.dimension || "Total");

                pathNode.append("div")
                    .attr("class", "value")
                    .text(node.name);

                pathNode.append("div")
                    .attr("class", "label")
                    .style("margin-top", "4px")
                    .text(formatValue(node.value));
            }});

            // Add connector to columns if there are drilled items
            if (pathNodes.length > 0 && columnsData.length > 0) {{
                const connectorSvg = mainDiv.append("svg")
                    .attr("width", 40)
                    .attr("height", 60)
                    .attr("class", "tree-svg");

                connectorSvg.append("path")
                    .attr("d", "M0,30 C20,30 20,30 40,30")
                    .attr("class", "connector-line");
            }}

            // Render decomposition columns
            columnsData.forEach((col, colIndex) => {{
                const column = mainDiv.append("div")
                    .attr("class", "column");

                // Column header
                const header = column.append("div")
                    .attr("class", "column-header");

                header.append("span")
                    .text(col.dimension);

                header.append("span")
                    .attr("class", "clear-btn")
                    .html("&times;")
                    .on("click", () => sendClearAction(col.dimension));

                // Find min/max for bar scaling
                const values = col.items.map(d => d.value);
                const maxVal = Math.max(...values);
                const minVal = Math.min(...values);
                const range = maxVal - minVal || 1;

                // Render items (sorted descending for display)
                const sortedItems = [...col.items].reverse();

                sortedItems.forEach(item => {{
                    const node = column.append("div")
                        .attr("class", "node")
                        .on("click", () => {{
                            // Only first column is clickable for drill-down
                            if (colIndex === 0) {{
                                sendDrillAction(col.dimension, item.name);
                            }}
                        }});

                    // Color bar indicator
                    node.append("div")
                        .attr("class", "node-bar")
                        .style("background-color", item.color)
                        .style("width", "6px");

                    // Content
                    const content = node.append("div")
                        .attr("class", "node-content");

                    content.append("div")
                        .attr("class", "node-name")
                        .text(item.name);

                    content.append("div")
                        .attr("class", "node-value")
                        .text(formatValue(item.value));

                    // Background bar
                    const barBg = node.append("div")
                        .attr("class", "node-bar-bg");

                    const barWidth = ((item.value - minVal) / range) * 100;
                    barBg.append("div")
                        .attr("class", "node-bar-fill")
                        .style("width", Math.max(5, barWidth) + "%")
                        .style("background-color", item.color);
                }});
            }});
        </script>
    </body>
    </html>
    """

    return html

# ============================================
# SESSION STATE INITIALIZATION
# ============================================

if 'drill_path' not in st.session_state:
    st.session_state.drill_path = []
if 'selected_metric' not in st.session_state:
    st.session_state.selected_metric = 'OTP'

# ============================================
# MAIN APP
# ============================================

def main():
    # Load data
    df = generate_mock_data()

    # Sidebar
    with st.sidebar:
        st.header("Settings")

        selected_metric = st.selectbox(
            "Select Metric",
            options=list(DATA_CONFIG["metrics"].keys()),
            format_func=lambda x: DATA_CONFIG["metrics"][x]["label"],
            index=list(DATA_CONFIG["metrics"].keys()).index(st.session_state.selected_metric)
        )
        st.session_state.selected_metric = selected_metric

        st.markdown("---")
        st.markdown("### Current Path")

        if len(st.session_state.drill_path) == 0:
            st.caption("Root level - no filters applied")
        else:
            for i, (dim, val) in enumerate(st.session_state.drill_path):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{dim}:** {val}")
                with col2:
                    if st.button("×", key=f"remove_{i}", help=f"Remove {dim} filter"):
                        st.session_state.drill_path = st.session_state.drill_path[:i]
                        st.rerun()

        st.markdown("---")
        if st.button("Reset All Filters", use_container_width=True):
            st.session_state.drill_path = []
            st.rerun()

        st.markdown("---")
        st.markdown("### How to Use")
        st.markdown("""
        1. **Click** on items in the first column to drill down
        2. Use the **×** buttons to remove filters
        3. The tree shows breakdowns by each dimension
        """)

    # Header
    st.title("Decomposition Tree")
    st.caption("Power BI-style drill-down analysis using D3.js")

    # Drill down controls (since postMessage doesn't work without custom component registration)
    available_dims = get_available_dimensions(st.session_state.drill_path)

    if len(available_dims) > 0:
        filtered_df = filter_data(df, st.session_state.drill_path)

        # Quick drill-down selector
        col1, col2, col3 = st.columns([2, 2, 1])

        with col1:
            next_dim = st.selectbox(
                "Drill into dimension",
                options=available_dims,
                key="drill_dimension"
            )

        with col2:
            # Get available values for selected dimension
            dim_values = filtered_df[next_dim].unique().tolist()
            selected_value = st.selectbox(
                f"Select {next_dim}",
                options=sorted(dim_values),
                key="drill_value"
            )

        with col3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Drill Down", type="primary", use_container_width=True):
                st.session_state.drill_path.append((next_dim, selected_value))
                st.rerun()

    st.markdown("---")

    # Create and display D3 visualization
    html_content = create_d3_decomposition_tree(df, st.session_state.drill_path, selected_metric)

    # Calculate height based on data
    filtered_df = filter_data(df, st.session_state.drill_path)
    max_items = 0
    for dim in available_dims[:5]:
        num_items = filtered_df[dim].nunique()
        max_items = max(max_items, num_items)

    viz_height = max(400, max_items * 40 + 100)

    components.html(html_content, height=viz_height, scrolling=True)

    # Summary stats
    st.markdown("---")

    metric_config = DATA_CONFIG["metrics"][selected_metric]
    filtered_df = filter_data(df, st.session_state.drill_path)

    if selected_metric == "OTP":
        current_value = np.average(filtered_df['OTP'], weights=filtered_df['Trips'])
        total_value = np.average(df['OTP'], weights=df['Trips'])
        display_value = f"{current_value:.1f}%"
    else:
        current_value = filtered_df[metric_config["column"]].sum()
        total_value = df[metric_config["column"]].sum()
        display_value = f"{current_value:,.0f}"

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Current Value", display_value)
    with col2:
        st.metric("Drill Level", len(st.session_state.drill_path))
    with col3:
        st.metric("Records", f"{len(filtered_df):,}")
    with col4:
        pct_of_total = (len(filtered_df) / len(df) * 100)
        st.metric("% of Records", f"{pct_of_total:.1f}%")

    # Show detailed breakdown if at deep level
    if len(st.session_state.drill_path) >= 3:
        st.markdown("---")
        st.markdown("### Detailed Data")

        display_df = filtered_df.copy()
        display_df['OTP'] = display_df['OTP'].apply(lambda x: f"{x:.1f}%")

        st.dataframe(
            display_df,
            use_container_width=True,
            height=300
        )

if __name__ == "__main__":
    main()
