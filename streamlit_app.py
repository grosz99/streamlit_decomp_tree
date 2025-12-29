"""
Decomposition Tree - Power BI Style
Pure JavaScript/SVG implementation (no external dependencies)
Fully compatible with Streamlit in Snowflake CSP restrictions
Styled to match Surge/Beacon design system
"""

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import json
from typing import Dict, List, Optional

# Page config
st.set_page_config(
    page_title="Revenue Tree",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# CUSTOM CSS - SURGE/BEACON DESIGN SYSTEM
# ============================================

st.markdown("""
<style>
    /* Import clean font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* Global styles */
    .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
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
</style>
""", unsafe_allow_html=True)


# ============================================
# DATA GENERATION
# ============================================

@st.cache_data
def generate_mock_data() -> pd.DataFrame:
    """Generate realistic mock transit data similar to Power BI example"""
    np.random.seed(42)

    divisions = ['Brooklyn', 'Queens South', 'Staten Island', 'Bronx', 'Queens North', 'Manhattan']

    depots = {
        'Brooklyn': ['Jackie Gleason', 'Fresh Pond', 'East New York', 'Ulmer Park', 'Flatbush', 'Grand Avenue'],
        'Queens South': ['Jamaica', 'JFK Depot', 'Rockaways'],
        'Staten Island': ['Castleton', 'Charleston', 'Yukon'],
        'Bronx': ['Gun Hill', 'Kingsbridge', 'West Farms'],
        'Queens North': ['Casey Stengel', 'LaGuardia', 'College Point'],
        'Manhattan': ['Mother Clara Hale', 'Manhattanville', 'Michael Quill']
    }

    routes_by_division = {
        'Brooklyn': ['B37', 'B68', 'B16', 'B11', 'B4', 'B43', 'B70', 'B8', 'B61', 'B63'],
        'Queens South': ['Q1', 'Q2', 'Q3', 'Q5', 'Q6'],
        'Staten Island': ['S40', 'S44', 'S46', 'S48', 'S52'],
        'Bronx': ['Bx1', 'Bx2', 'Bx4', 'Bx5', 'Bx6'],
        'Queens North': ['Q15', 'Q16', 'Q17', 'Q19', 'Q20'],
        'Manhattan': ['M1', 'M2', 'M3', 'M4', 'M5']
    }

    directions = ['SB', 'NB']
    periods = ['Overnight', 'Midday', 'PM', 'AM']

    data = []
    for _ in range(3000):
        division = np.random.choice(divisions, p=[0.25, 0.18, 0.12, 0.15, 0.15, 0.15])
        depot = np.random.choice(depots[division])
        route = np.random.choice(routes_by_division[division])
        direction = np.random.choice(directions, p=[0.52, 0.48])
        period = np.random.choice(periods, p=[0.15, 0.30, 0.30, 0.25])

        base_otp = np.random.uniform(55, 78)
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
# HIERARCHY BUILDING
# ============================================

def calculate_metric(df: pd.DataFrame, metric: str) -> float:
    """Calculate metric value for a dataframe subset"""
    if metric == "OTP":
        if len(df) == 0 or df['Trips'].sum() == 0:
            return 0.0
        return round(float(np.average(df['OTP'], weights=df['Trips'])), 1)
    else:
        return int(df['Trips'].sum())


def get_color(value: float, min_val: float, max_val: float) -> str:
    """Get color based on value relative to min/max - using Surge green palette"""
    if max_val == min_val:
        normalized = 0.5
    else:
        normalized = (value - min_val) / (max_val - min_val)

    if normalized >= 0.7:
        return "#1B5E3F"  # Primary green (high)
    elif normalized >= 0.5:
        return "#2D8B5E"  # Medium green
    elif normalized >= 0.3:
        return "#F59E0B"  # Amber (warning)
    else:
        return "#DC2626"  # Red (low)


def build_hierarchy(df: pd.DataFrame, dimensions: List[str], metric: str) -> Dict:
    """Build a nested hierarchical structure for the tree"""

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
                "color": get_color(value, min_val, max_val),
                "count": len(group)
            }

            if next_dims:
                node["children"] = build_level(group, next_dims)

            children.append(node)

        children.sort(key=lambda x: x["value"], reverse=True)
        return children

    root_value = calculate_metric(df, metric)
    root = {
        "name": "Total",
        "dimension": "All Data",
        "value": root_value,
        "color": "#1B5E3F",
        "count": len(df),
        "children": build_level(df, dimensions)
    }

    return root


# ============================================
# VISUALIZATION - SURGE/BEACON THEMED
# ============================================

def create_tree_visualization(tree_data: Dict, metric: str) -> str:
    """Create pure JavaScript/SVG collapsible tree with Surge/Beacon styling"""

    tree_json = json.dumps(tree_data)
    format_type = "percent" if metric == "OTP" else "number"

    html = f'''
<!DOCTYPE html>
<html>
<head>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

* {{ margin: 0; padding: 0; box-sizing: border-box; }}

body {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
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

.node-circle {{
    stroke-width: 2px;
    transition: all 0.2s;
}}

.node-text {{
    font-family: 'Inter', sans-serif;
    font-size: 13px;
    font-weight: 500;
    fill: #1F2937;
    pointer-events: none;
}}

.node-value {{
    font-family: 'Inter', sans-serif;
    font-size: 12px;
    font-weight: 600;
    fill: #1B5E3F;
    pointer-events: none;
}}

.node-dimension {{
    font-family: 'Inter', sans-serif;
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

.link-active {{
    stroke: #1B5E3F;
    stroke-opacity: 0.6;
}}

.tooltip {{
    position: fixed;
    background: #1F2937;
    color: #FFFFFF;
    padding: 12px 16px;
    border-radius: 8px;
    font-size: 13px;
    font-family: 'Inter', sans-serif;
    pointer-events: none;
    z-index: 1000;
    display: none;
    max-width: 220px;
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
    font-family: 'Inter', sans-serif;
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
        nodeWidth: 160,
        nodeHeight: 65,
        levelGap: 200,
        siblingGap: 12,
        barWidth: 80,
        barHeight: 6,
        margin: {{ top: 40, right: 160, bottom: 40, left: 60 }}
    }};

    let nodeId = 0;
    let root = null;

    function formatValue(val) {{
        return formatType === "percent" ? val.toFixed(1) + "%" : val.toLocaleString();
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
        const totalHeight = Math.max(400, height + config.margin.top + config.margin.bottom);
        const totalWidth = 1100;

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
            dimText.setAttribute("y", 16);
            dimText.textContent = node.dimension;
            nodeGroup.appendChild(dimText);

            // Name
            const nameText = document.createElementNS("http://www.w3.org/2000/svg", "text");
            nameText.setAttribute("class", "node-text");
            nameText.setAttribute("x", 14);
            nameText.setAttribute("y", 32);
            nameText.textContent = node.name.length > 16 ? node.name.substring(0, 14) + "..." : node.name;
            nodeGroup.appendChild(nameText);

            // Value
            const valueText = document.createElementNS("http://www.w3.org/2000/svg", "text");
            valueText.setAttribute("class", "node-value");
            valueText.setAttribute("x", 14);
            valueText.setAttribute("y", 48);
            valueText.textContent = formatValue(node.value);
            nodeGroup.appendChild(valueText);

            // Bar background
            const barBg = document.createElementNS("http://www.w3.org/2000/svg", "rect");
            barBg.setAttribute("class", "node-bar-bg");
            barBg.setAttribute("x", 14);
            barBg.setAttribute("y", 54);
            barBg.setAttribute("width", config.barWidth);
            barBg.setAttribute("height", config.barHeight);
            nodeGroup.appendChild(barBg);

            // Bar fill
            const siblings = node.parent ? node.parent.children : [node];
            const values = siblings.map(s => s.value);
            const maxVal = Math.max(...values);
            const minVal = Math.min(...values);
            const range = maxVal - minVal || 1;
            const barFillWidth = Math.max(4, ((node.value - minVal) / range) * config.barWidth);

            const barFill = document.createElementNS("http://www.w3.org/2000/svg", "rect");
            barFill.setAttribute("class", "node-bar");
            barFill.setAttribute("x", 14);
            barFill.setAttribute("y", 54);
            barFill.setAttribute("width", barFillWidth);
            barFill.setAttribute("height", config.barHeight);
            barFill.setAttribute("fill", node.color);
            nodeGroup.appendChild(barFill);

            // Expand/collapse button
            if (hasChildren) {{
                const btnGroup = document.createElementNS("http://www.w3.org/2000/svg", "g");
                btnGroup.setAttribute("transform", `translate(${{config.nodeWidth - 24}}, ${{config.nodeHeight/2 - 10}})`);

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
    return html


# ============================================
# CONFIG
# ============================================

DATA_CONFIG = {
    "metrics": {
        "OTP": {"label": "On-Time Performance (%)"},
        "Trips": {"label": "Total Trips"}
    },
    "dimensions": ["Division", "Depot", "Route", "Direction", "Period"]
}


# ============================================
# SESSION STATE
# ============================================

if 'selected_metric' not in st.session_state:
    st.session_state.selected_metric = 'OTP'
if 'selected_dimensions' not in st.session_state:
    st.session_state.selected_dimensions = DATA_CONFIG["dimensions"].copy()


# ============================================
# MAIN APP
# ============================================

def main():
    df = generate_mock_data()

    # Sidebar
    with st.sidebar:
        st.markdown("### Settings")

        selected_metric = st.selectbox(
            "Metric",
            options=list(DATA_CONFIG["metrics"].keys()),
            format_func=lambda x: DATA_CONFIG["metrics"][x]["label"],
            index=list(DATA_CONFIG["metrics"].keys()).index(st.session_state.selected_metric)
        )
        st.session_state.selected_metric = selected_metric

        st.markdown("---")

        st.markdown("### Dimensions")
        selected_dims = st.multiselect(
            "Select hierarchy levels",
            options=DATA_CONFIG["dimensions"],
            default=st.session_state.selected_dimensions,
            help="Order determines drill-down hierarchy"
        )

        if selected_dims:
            st.session_state.selected_dimensions = selected_dims

        st.markdown("---")

        # Info box with custom styling
        st.markdown("""
        <div class="info-box">
            <h4>How to Use</h4>
            <p>• Click <strong>+</strong> to expand a node</p>
            <p>• Click <strong>−</strong> to collapse</p>
            <p>• Hover for detailed tooltips</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # Legend with custom styling
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

    # Main content
    st.title("Revenue Tree")
    st.markdown('<p class="subtitle">Revenue analysis and growth tracking with intelligent insights.</p>', unsafe_allow_html=True)

    # Category badge
    st.markdown('<span class="category-badge">Financial</span>', unsafe_allow_html=True)

    # Tree visualization
    if st.session_state.selected_dimensions:
        tree_data = build_hierarchy(
            df,
            st.session_state.selected_dimensions,
            selected_metric
        )

        html_content = create_tree_visualization(tree_data, selected_metric)
        components.html(html_content, height=650, scrolling=True)

        # Summary metrics
        st.markdown("---")

        total_value = calculate_metric(df, selected_metric)
        display_value = f"{total_value:.1f}%" if selected_metric == "OTP" else f"{total_value:,}"

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Value", display_value)
        with col2:
            st.metric("Records", f"{len(df):,}")
        with col3:
            st.metric("Hierarchy Levels", len(st.session_state.selected_dimensions))
        with col4:
            st.metric("Current Metric", selected_metric)
    else:
        st.warning("Please select at least one dimension in the sidebar.")


if __name__ == "__main__":
    main()
