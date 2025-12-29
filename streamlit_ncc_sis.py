"""
NCC Decomposition Tree - Streamlit in Snowflake
Source: MY_WORKFLOW_DB.PUBLIC.NCC_TEST
Drill down: Region → System → Profit Center → Practice Area
"""

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import json
from typing import Dict, List
from snowflake.snowpark.context import get_active_session

st.set_page_config(
    page_title="NCC Decomposition Tree",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# CUSTOM CSS - SURGE/BEACON DESIGN SYSTEM
# ============================================

st.markdown("""
<style>
    /* Global styles */
    .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }

    /* Header styling */
    h1 {
        color: #1B5E3F !important;
        font-weight: 700 !important;
        font-size: 1.75rem !important;
        margin-bottom: 0.25rem !important;
    }

    /* Subheader */
    .subtitle {
        color: #6B7280;
        font-size: 0.95rem;
        margin-bottom: 1.5rem;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #F9FAFB;
        border-right: 1px solid #E5E7EB;
    }

    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #1B5E3F !important;
    }

    /* Card styling for metrics */
    [data-testid="stMetric"] {
        background-color: white;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }

    [data-testid="stMetricLabel"] {
        color: #6B7280 !important;
        font-size: 0.85rem !important;
    }

    [data-testid="stMetricValue"] {
        color: #1B5E3F !important;
        font-weight: 600 !important;
    }

    /* Button styling */
    .stButton > button {
        background-color: #1B5E3F;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        transition: background-color 0.2s;
    }

    .stButton > button:hover {
        background-color: #154a32;
        color: white;
    }

    /* Selectbox styling */
    .stSelectbox > div > div {
        border-radius: 8px;
        border-color: #E5E7EB;
    }

    /* Multiselect styling */
    .stMultiSelect > div > div {
        border-radius: 8px;
        border-color: #E5E7EB;
    }

    /* Divider */
    hr {
        border-color: #E5E7EB;
        margin: 1.5rem 0;
    }

    /* Category badge styling */
    .category-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        background-color: #E8F5EE;
        color: #1B5E3F;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 500;
        margin-bottom: 0.5rem;
    }

    /* Info box */
    .info-box {
        background-color: #F9FAFB;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 1rem;
        margin: 1rem 0;
    }

    .info-box h4 {
        color: #1B5E3F;
        font-size: 0.9rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }

    .info-box p, .info-box li {
        color: #6B7280;
        font-size: 0.85rem;
        margin: 0.25rem 0;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Legend items */
    .legend-item {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin: 0.25rem 0;
        font-size: 0.85rem;
        color: #4B5563;
    }

    .legend-dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
    }

    /* Source caption styling */
    .source-caption {
        color: #9CA3AF;
        font-size: 0.75rem;
        margin-top: -0.5rem;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=300)
def load_data() -> pd.DataFrame:
    """Load NCC data from Snowflake table"""
    session = get_active_session()
    df = session.table("MY_WORKFLOW_DB.PUBLIC.NCC_TEST").to_pandas()
    return df


def calculate_metric(df: pd.DataFrame, metric: str) -> float:
    if len(df) == 0:
        return 0.0
    if metric == "NCC":
        return round(df['NCC'].sum(), 2)
    elif metric == "NCC_PY":
        return round(df['NCC_PY'].sum(), 2)
    elif metric == "YoY_Growth":
        ncc = df['NCC'].sum()
        ncc_py = df['NCC_PY'].sum()
        if ncc_py == 0:
            return 0.0
        return round(((ncc - ncc_py) / ncc_py) * 100, 1)
    elif metric == "Avg_NCC":
        return round(df['NCC'].mean(), 2)
    return 0.0


def get_color(value: float, min_val: float, max_val: float, metric: str) -> str:
    """Get color based on value - using Surge/Beacon green palette"""
    if max_val == min_val:
        normalized = 0.5
    else:
        normalized = (value - min_val) / (max_val - min_val)

    if metric == "YoY_Growth":
        if value >= 10:
            return "#1B5E3F"  # Primary green (high)
        elif value >= 0:
            return "#2D8B5E"  # Medium green
        elif value >= -10:
            return "#F59E0B"  # Amber (warning)
        else:
            return "#DC2626"  # Red (low)

    if normalized >= 0.7:
        return "#1B5E3F"  # Primary green (high)
    elif normalized >= 0.5:
        return "#2D8B5E"  # Medium green
    elif normalized >= 0.3:
        return "#F59E0B"  # Amber (warning)
    else:
        return "#DC2626"  # Red (low)


def build_hierarchy(df: pd.DataFrame, dimensions: List[str], metric: str) -> Dict:
    def build_level(data: pd.DataFrame, dims_remaining: List[str]) -> List[Dict]:
        if not dims_remaining or len(data) == 0:
            return []

        current_dim = dims_remaining[0]
        next_dims = dims_remaining[1:]
        groups = list(data.groupby(current_dim))
        children = []

        values = [calculate_metric(group, metric) for _, group in groups]
        min_val = min(values) if values else 0
        max_val = max(values) if values else 1

        for (name, group), value in zip(groups, values):
            node = {
                "name": str(name),
                "dimension": current_dim,
                "value": value,
                "color": get_color(value, min_val, max_val, metric),
                "count": len(group)
            }
            if next_dims:
                node["children"] = build_level(group, next_dims)
            children.append(node)

        children.sort(key=lambda x: x["value"], reverse=True)
        return children

    root_value = calculate_metric(df, metric)
    return {
        "name": "Total NCC",
        "dimension": "Total",
        "value": root_value,
        "color": "#1B5E3F",  # Primary green
        "count": len(df),
        "children": build_level(df, dimensions)
    }


def create_tree_visualization(tree_data: Dict, metric: str) -> str:
    """Create pure JavaScript/SVG collapsible tree with Surge/Beacon styling"""
    tree_json = json.dumps(tree_data)
    format_type = "percent" if metric == "YoY_Growth" else "currency"

    return f'''
<!DOCTYPE html>
<html>
<head>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}

body {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: #FFFFFF;
    color: #1F2937;
}}

.tree-container {{
    padding: 24px;
    background: #FFFFFF;
    border-radius: 12px;
    border: 1px solid #E5E7EB;
    margin: 8px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}}

svg {{ overflow: visible; }}

.node {{ cursor: pointer; }}

.node-rect {{
    fill: #FFFFFF;
    stroke: #E5E7EB;
    stroke-width: 1px;
    rx: 8px;
    transition: all 0.2s;
}}

.node:hover .node-rect {{
    stroke: #1B5E3F;
    stroke-width: 2px;
    filter: drop-shadow(0 2px 4px rgba(27, 94, 63, 0.1));
}}

.node-text {{
    font-family: 'Inter', -apple-system, sans-serif;
    font-size: 13px;
    font-weight: 500;
    fill: #1F2937;
    pointer-events: none;
}}

.node-value {{
    font-family: 'Inter', -apple-system, sans-serif;
    font-size: 12px;
    font-weight: 600;
    fill: #1B5E3F;
    pointer-events: none;
}}

.node-dimension {{
    font-family: 'Inter', -apple-system, sans-serif;
    font-size: 10px;
    font-weight: 500;
    fill: #9CA3AF;
    pointer-events: none;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}

.node-bar-bg {{
    fill: #F3F4F6;
    rx: 3px;
}}

.node-bar {{
    rx: 3px;
    transition: width 0.3s;
}}

.link {{
    fill: none;
    stroke: #D1D5DB;
    stroke-width: 1.5px;
}}

.tooltip {{
    position: fixed;
    background: #1F2937;
    color: #FFFFFF;
    padding: 12px 16px;
    border-radius: 8px;
    font-size: 13px;
    font-family: 'Inter', -apple-system, sans-serif;
    pointer-events: none;
    z-index: 1000;
    display: none;
    max-width: 250px;
    box-shadow: 0 10px 25px rgba(0,0,0,0.2);
    line-height: 1.5;
}}

.tooltip strong {{
    color: #FFFFFF;
    font-weight: 600;
}}

.tooltip .label {{
    color: #9CA3AF;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-top: 8px;
    display: block;
}}

.tooltip .value {{
    color: #10B981;
    font-weight: 600;
}}

.expand-icon {{
    font-family: 'Inter', -apple-system, sans-serif;
    font-size: 14px;
    font-weight: 600;
    pointer-events: none;
}}
</style>
</head>
<body>
<div class="tree-container">
    <svg id="tree-svg"></svg>
</div>
<div id="tooltip" class="tooltip"></div>

<script>
(function() {{
    "use strict";

    const data = {tree_json};
    const formatType = "{format_type}";

    const config = {{
        nodeWidth: 170,
        nodeHeight: 68,
        levelGap: 210,
        siblingGap: 12,
        barWidth: 90,
        barHeight: 6,
        margin: {{ top: 40, right: 160, bottom: 40, left: 60 }}
    }};

    let nodeId = 0;
    let root = null;

    function formatValue(val) {{
        if (formatType === "percent") return (val >= 0 ? "+" : "") + val.toFixed(1) + "%";
        if (val >= 1e9) return "$" + (val / 1e9).toFixed(1) + "B";
        if (val >= 1e6) return "$" + (val / 1e6).toFixed(1) + "M";
        if (val >= 1e3) return "$" + (val / 1e3).toFixed(1) + "K";
        return "$" + val.toLocaleString();
    }}

    function processNode(node, depth) {{
        node.id = ++nodeId;
        node.depth = depth;
        node.expanded = depth < 1;

        if (node.children && node.children.length > 0) {{
            node.children.forEach(child => {{
                child.parent = node;
                processNode(child, depth + 1);
            }});
        }}
        return node;
    }}

    function calculateLayout(node) {{
        let yOffset = 0;

        function layoutNode(n, x) {{
            n.x = x;

            if (n.expanded && n.children && n.children.length > 0) {{
                n.children.forEach(child => {{
                    layoutNode(child, x + config.levelGap);
                }});
                const firstChild = n.children[0];
                const lastChild = n.children[n.children.length - 1];
                n.y = (firstChild.y + lastChild.y) / 2;
            }} else {{
                n.y = yOffset;
                yOffset += config.nodeHeight + config.siblingGap;
            }}
        }}

        layoutNode(node, config.margin.left);
        return yOffset;
    }}

    function getVisibleNodes(node, nodes) {{
        nodes = nodes || [];
        nodes.push(node);
        if (node.expanded && node.children) {{
            node.children.forEach(child => getVisibleNodes(child, nodes));
        }}
        return nodes;
    }}

    function getVisibleLinks(node, links) {{
        links = links || [];
        if (node.expanded && node.children) {{
            node.children.forEach(child => {{
                links.push({{ source: node, target: child }});
                getVisibleLinks(child, links);
            }});
        }}
        return links;
    }}

    function linkPath(source, target) {{
        const midX = (source.x + config.nodeWidth/2 + target.x) / 2;
        const sy = source.y + config.nodeHeight/2;
        const ty = target.y + config.nodeHeight/2;
        const sx = source.x + config.nodeWidth;
        const tx = target.x;

        return `M${{sx}},${{sy}} C${{midX}},${{sy}} ${{midX}},${{ty}} ${{tx}},${{ty}}`;
    }}

    function render() {{
        const height = calculateLayout(root);
        const svg = document.getElementById("tree-svg");
        const totalHeight = Math.max(500, height + config.margin.top + config.margin.bottom);
        const totalWidth = 1200;

        svg.setAttribute("width", totalWidth);
        svg.setAttribute("height", totalHeight);
        svg.innerHTML = "";

        const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
        g.setAttribute("transform", `translate(0,${{config.margin.top}})`);
        svg.appendChild(g);

        const nodes = getVisibleNodes(root);
        const links = getVisibleLinks(root);

        // Draw links
        links.forEach(link => {{
            const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
            path.setAttribute("class", "link");
            path.setAttribute("d", linkPath(link.source, link.target));
            g.appendChild(path);
        }});

        // Draw nodes
        nodes.forEach(node => {{
            const nodeGroup = document.createElementNS("http://www.w3.org/2000/svg", "g");
            nodeGroup.setAttribute("class", "node");
            nodeGroup.setAttribute("transform", `translate(${{node.x}},${{node.y}})`);

            const hasChildren = node.children && node.children.length > 0;

            if (hasChildren) {{
                nodeGroup.onclick = function(e) {{
                    e.stopPropagation();
                    node.expanded = !node.expanded;
                    render();
                }};
                nodeGroup.style.cursor = "pointer";
            }} else {{
                nodeGroup.style.cursor = "default";
            }}

            // Tooltip
            nodeGroup.onmouseenter = function(e) {{
                const tooltip = document.getElementById("tooltip");
                tooltip.innerHTML = `
                    <strong>${{node.name}}</strong>
                    <span class="label">${{node.dimension}}</span>
                    <span class="label">Value</span>
                    <span class="value">${{formatValue(node.value)}}</span>
                    <span class="label">Records</span>
                    ${{node.count ? node.count.toLocaleString() : 'N/A'}}
                `;
                tooltip.style.display = "block";
                tooltip.style.left = (e.clientX + 15) + "px";
                tooltip.style.top = (e.clientY - 10) + "px";
            }};
            nodeGroup.onmouseleave = function() {{
                document.getElementById("tooltip").style.display = "none";
            }};
            nodeGroup.onmousemove = function(e) {{
                const tooltip = document.getElementById("tooltip");
                tooltip.style.left = (e.clientX + 15) + "px";
                tooltip.style.top = (e.clientY - 10) + "px";
            }};

            // Card background
            const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
            rect.setAttribute("class", "node-rect");
            rect.setAttribute("width", config.nodeWidth);
            rect.setAttribute("height", config.nodeHeight);
            rect.setAttribute("rx", 8);
            nodeGroup.appendChild(rect);

            // Color indicator (left edge)
            const indicator = document.createElementNS("http://www.w3.org/2000/svg", "rect");
            indicator.setAttribute("x", 0);
            indicator.setAttribute("y", 0);
            indicator.setAttribute("width", 4);
            indicator.setAttribute("height", config.nodeHeight);
            indicator.setAttribute("rx", "4 0 0 4");
            indicator.setAttribute("fill", node.color);
            nodeGroup.appendChild(indicator);

            // Dimension label
            const dimText = document.createElementNS("http://www.w3.org/2000/svg", "text");
            dimText.setAttribute("class", "node-dimension");
            dimText.setAttribute("x", 14);
            dimText.setAttribute("y", 18);
            dimText.textContent = node.dimension;
            nodeGroup.appendChild(dimText);

            // Name
            const nameText = document.createElementNS("http://www.w3.org/2000/svg", "text");
            nameText.setAttribute("class", "node-text");
            nameText.setAttribute("x", 14);
            nameText.setAttribute("y", 36);
            nameText.textContent = node.name.length > 18 ? node.name.substring(0, 16) + "..." : node.name;
            nodeGroup.appendChild(nameText);

            // Value
            const valueText = document.createElementNS("http://www.w3.org/2000/svg", "text");
            valueText.setAttribute("class", "node-value");
            valueText.setAttribute("x", 14);
            valueText.setAttribute("y", 52);
            valueText.textContent = formatValue(node.value);
            nodeGroup.appendChild(valueText);

            // Bar background
            const barBg = document.createElementNS("http://www.w3.org/2000/svg", "rect");
            barBg.setAttribute("class", "node-bar-bg");
            barBg.setAttribute("x", 14);
            barBg.setAttribute("y", 58);
            barBg.setAttribute("width", config.barWidth);
            barBg.setAttribute("height", config.barHeight);
            nodeGroup.appendChild(barBg);

            // Bar fill
            const siblings = node.parent ? node.parent.children : [node];
            const values = siblings.map(s => Math.abs(s.value));
            const maxVal = Math.max(...values);
            const minVal = Math.min(...values);
            const range = maxVal - minVal || 1;
            const barFillWidth = Math.max(4, ((Math.abs(node.value) - minVal) / range) * config.barWidth);

            const barFill = document.createElementNS("http://www.w3.org/2000/svg", "rect");
            barFill.setAttribute("class", "node-bar");
            barFill.setAttribute("x", 14);
            barFill.setAttribute("y", 58);
            barFill.setAttribute("width", barFillWidth);
            barFill.setAttribute("height", config.barHeight);
            barFill.setAttribute("fill", node.color);
            nodeGroup.appendChild(barFill);

            // Expand/collapse button
            if (hasChildren) {{
                const btnGroup = document.createElementNS("http://www.w3.org/2000/svg", "g");
                btnGroup.setAttribute("transform", `translate(${{config.nodeWidth - 26}}, ${{config.nodeHeight/2 - 10}})`);

                const btnBg = document.createElementNS("http://www.w3.org/2000/svg", "rect");
                btnBg.setAttribute("width", 20);
                btnBg.setAttribute("height", 20);
                btnBg.setAttribute("rx", 4);
                btnBg.setAttribute("fill", node.expanded ? "#F3F4F6" : "#1B5E3F");
                btnGroup.appendChild(btnBg);

                const btnText = document.createElementNS("http://www.w3.org/2000/svg", "text");
                btnText.setAttribute("class", "expand-icon");
                btnText.setAttribute("x", 10);
                btnText.setAttribute("y", 14);
                btnText.setAttribute("text-anchor", "middle");
                btnText.setAttribute("fill", node.expanded ? "#6B7280" : "#FFFFFF");
                btnText.textContent = node.expanded ? "−" : "+";
                btnGroup.appendChild(btnText);

                nodeGroup.appendChild(btnGroup);
            }}

            g.appendChild(nodeGroup);
        }});
    }}

    root = processNode(data, 0);
    render();
}})();
</script>
</body>
</html>
'''


DATA_CONFIG = {
    "table": "MY_WORKFLOW_DB.PUBLIC.NCC_TEST",
    "metrics": {
        "NCC": {"label": "Net Client Contribution ($)"},
        "NCC_PY": {"label": "Prior Year NCC ($)"},
        "YoY_Growth": {"label": "Year-over-Year Growth (%)"},
        "Avg_NCC": {"label": "Average NCC ($)"}
    },
    "dimensions": ["REGION", "SYSTEM", "PROFIT_CENTER", "PRACTICE_AREA"],
    "dimension_labels": {
        "REGION": "Region",
        "SYSTEM": "System",
        "PROFIT_CENTER": "Profit Center",
        "PRACTICE_AREA": "Practice Area"
    }
}

if 'selected_metric' not in st.session_state:
    st.session_state.selected_metric = 'NCC'
if 'selected_dimensions' not in st.session_state:
    st.session_state.selected_dimensions = DATA_CONFIG["dimensions"].copy()
if 'data_scenario' not in st.session_state:
    st.session_state.data_scenario = 'Actuals'


def main():
    df = load_data()

    with st.sidebar:
        st.markdown("### Settings")
        st.markdown(f'<p class="source-caption">Source: {DATA_CONFIG["table"]}</p>', unsafe_allow_html=True)

        scenarios = df['DATA_SCENARIO'].unique().tolist()
        selected_scenario = st.selectbox(
            "Data Scenario", options=scenarios,
            index=scenarios.index(st.session_state.data_scenario) if st.session_state.data_scenario in scenarios else 0
        )
        st.session_state.data_scenario = selected_scenario

        st.markdown("---")
        selected_metric = st.selectbox(
            "Metric",
            options=list(DATA_CONFIG["metrics"].keys()),
            format_func=lambda x: DATA_CONFIG["metrics"][x]["label"],
            index=list(DATA_CONFIG["metrics"].keys()).index(st.session_state.selected_metric)
        )
        st.session_state.selected_metric = selected_metric

        st.markdown("---")
        st.markdown("### Hierarchy")
        selected_dims = st.multiselect(
            "Select drill-down levels",
            options=DATA_CONFIG["dimensions"],
            default=st.session_state.selected_dimensions,
            format_func=lambda x: DATA_CONFIG["dimension_labels"].get(x, x),
            help="Order determines drill-down hierarchy"
        )
        if selected_dims:
            st.session_state.selected_dimensions = selected_dims

        st.markdown("---")
        st.markdown("### Time Filters")
        years = sorted(df['YEAR'].unique())
        selected_years = st.multiselect("Year(s)", years, default=years)
        months = sorted(df['MONTH_OF_YEAR'].unique())
        selected_months = st.multiselect("Month(s)", months, default=months)

        st.markdown("---")

        # Info box with how to use
        st.markdown("""
        <div class="info-box">
            <h4>How to Use</h4>
            <p>Click <strong>+</strong> to expand a node</p>
            <p>Click <strong>-</strong> to collapse</p>
            <p>Hover for detailed tooltips</p>
        </div>
        """, unsafe_allow_html=True)

        # Performance legend
        st.markdown("""
        <div class="info-box">
            <h4>Performance Legend</h4>
            <div class="legend-item">
                <div class="legend-dot" style="background: #1B5E3F;"></div>
                <span>High Performance</span>
            </div>
            <div class="legend-item">
                <div class="legend-dot" style="background: #2D8B5E;"></div>
                <span>Good Performance</span>
            </div>
            <div class="legend-item">
                <div class="legend-dot" style="background: #F59E0B;"></div>
                <span>Needs Attention</span>
            </div>
            <div class="legend-item">
                <div class="legend-dot" style="background: #DC2626;"></div>
                <span>Low Performance</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    filtered_df = df[
        (df['DATA_SCENARIO'] == selected_scenario) &
        (df['YEAR'].isin(selected_years)) &
        (df['MONTH_OF_YEAR'].isin(selected_months))
    ]

    # Main content
    st.title("NCC Decomposition Tree")
    st.markdown(f'<p class="subtitle">Analyzing {DATA_CONFIG["metrics"][selected_metric]["label"]} | Scenario: {selected_scenario}</p>', unsafe_allow_html=True)

    # Category badge
    st.markdown('<span class="category-badge">Financial</span>', unsafe_allow_html=True)

    # Metrics row
    col1, col2, col3, col4, col5 = st.columns(5)
    total_ncc = filtered_df['NCC'].sum()
    total_ncc_py = filtered_df['NCC_PY'].sum()
    yoy_growth = ((total_ncc - total_ncc_py) / total_ncc_py * 100) if total_ncc_py > 0 else 0

    col1.metric("Total NCC", f"${total_ncc/1e6:.1f}M")
    col2.metric("Prior Year", f"${total_ncc_py/1e6:.1f}M")
    col3.metric("YoY Growth", f"{yoy_growth:+.1f}%")
    col4.metric("Records", f"{len(filtered_df):,}")
    col5.metric("Drill Levels", len(st.session_state.selected_dimensions))

    st.markdown("---")

    # Tree visualization
    if st.session_state.selected_dimensions and len(filtered_df) > 0:
        tree_data = build_hierarchy(filtered_df, st.session_state.selected_dimensions, selected_metric)
        components.html(create_tree_visualization(tree_data, selected_metric), height=700, scrolling=True)
    else:
        st.warning("Please select at least one dimension in the sidebar.")


if __name__ == "__main__":
    main()
