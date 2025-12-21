"""
Decomposition Tree - Power BI Style
Pure JavaScript/SVG implementation (no external dependencies)
Fully compatible with Streamlit in Snowflake CSP restrictions
"""

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import json
from typing import Dict, List, Optional

# Page config
st.set_page_config(
    page_title="Decomposition Tree",
    page_icon="🌳",
    layout="wide"
)


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
    """Get color based on value relative to min/max"""
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


def build_hierarchy(df: pd.DataFrame, dimensions: List[str], metric: str) -> Dict:
    """Build a nested hierarchical structure for the tree"""

    def build_level(data: pd.DataFrame, dims_remaining: List[str]) -> List[Dict]:
        if not dims_remaining or len(data) == 0:
            return []

        current_dim = dims_remaining[0]
        next_dims = dims_remaining[1:]

        groups = list(data.groupby(current_dim))
        children = []

        # Calculate values for color scaling
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

            # Recursively build children
            if next_dims:
                node["children"] = build_level(group, next_dims)

            children.append(node)

        # Sort by value descending
        children.sort(key=lambda x: x["value"], reverse=True)
        return children

    # Root node
    root_value = calculate_metric(df, metric)
    root = {
        "name": "CJTP",
        "dimension": "Total",
        "value": root_value,
        "color": "#1976D2",
        "count": len(df),
        "children": build_level(df, dimensions)
    }

    return root


# ============================================
# PURE JS/SVG VISUALIZATION (NO EXTERNAL DEPS)
# ============================================

def create_tree_visualization(tree_data: Dict, metric: str) -> str:
    """Create pure JavaScript/SVG collapsible tree (Snowflake CSP compliant)"""

    tree_json = json.dumps(tree_data)
    format_type = "percent" if metric == "OTP" else "number"

    html = f'''
<!DOCTYPE html>
<html>
<head>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: "Segoe UI", Arial, sans-serif; background: #fff; }}
.tree-container {{ padding: 20px; overflow: auto; }}
svg {{ overflow: visible; }}
.node {{ cursor: pointer; }}
.node-circle {{ stroke-width: 2px; transition: all 0.2s; }}
.node-circle:hover {{ stroke-width: 3px; }}
.node-text {{ font-size: 12px; fill: #333; pointer-events: none; }}
.node-value {{ font-size: 11px; fill: #666; pointer-events: none; }}
.node-bar-bg {{ fill: #e0e0e0; }}
.node-bar {{ transition: width 0.3s; }}
.link {{ fill: none; stroke: #1976D2; stroke-opacity: 0.4; stroke-width: 1.5px; }}
.tooltip {{
    position: fixed; background: rgba(0,0,0,0.85); color: #fff;
    padding: 8px 12px; border-radius: 4px; font-size: 12px;
    pointer-events: none; z-index: 1000; display: none;
    max-width: 200px; box-shadow: 0 2px 8px rgba(0,0,0,0.3);
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

    // Configuration
    const config = {{
        nodeWidth: 180,
        nodeHeight: 50,
        levelGap: 220,
        siblingGap: 8,
        barWidth: 60,
        barHeight: 6,
        duration: 300,
        margin: {{ top: 40, right: 120, bottom: 40, left: 80 }}
    }};

    // State
    let nodeId = 0;
    let root = null;

    // Utilities
    function formatValue(val) {{
        return formatType === "percent" ? val.toFixed(1) + "%" : val.toLocaleString();
    }}

    // Process tree data - add IDs and collapse state
    function processNode(node, depth) {{
        node.id = ++nodeId;
        node.depth = depth;
        node.expanded = depth < 1; // Expand only root initially

        if (node.children && node.children.length > 0) {{
            node.children.forEach(child => {{
                child.parent = node;
                processNode(child, depth + 1);
            }});
        }}
        return node;
    }}

    // Calculate node positions using simple tree layout
    function calculateLayout(node) {{
        let yOffset = 0;

        function layoutNode(n, x) {{
            n.x = x;

            if (n.expanded && n.children && n.children.length > 0) {{
                const startY = yOffset;
                n.children.forEach(child => {{
                    layoutNode(child, x + config.levelGap);
                }});
                // Center parent among children
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

    // Get all visible nodes
    function getVisibleNodes(node, nodes) {{
        nodes = nodes || [];
        nodes.push(node);
        if (node.expanded && node.children) {{
            node.children.forEach(child => getVisibleNodes(child, nodes));
        }}
        return nodes;
    }}

    // Get all visible links
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

    // Create curved path between nodes
    function linkPath(source, target) {{
        const midX = (source.x + target.x) / 2;
        return "M" + source.x + "," + source.y +
               "C" + midX + "," + source.y +
               " " + midX + "," + target.y +
               " " + target.x + "," + target.y;
    }}

    // Render the tree
    function render() {{
        const height = calculateLayout(root);
        const svg = document.getElementById("tree-svg");
        const totalHeight = Math.max(400, height + config.margin.top + config.margin.bottom);
        const totalWidth = 1200;

        svg.setAttribute("width", totalWidth);
        svg.setAttribute("height", totalHeight);
        svg.innerHTML = "";

        const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
        g.setAttribute("transform", "translate(0," + config.margin.top + ")");
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
            nodeGroup.setAttribute("transform", "translate(" + node.x + "," + node.y + ")");

            // Click handler for expand/collapse
            if (node.children && node.children.length > 0) {{
                nodeGroup.onclick = function(e) {{
                    e.stopPropagation();
                    node.expanded = !node.expanded;
                    render();
                }};
            }}

            // Tooltip handlers
            nodeGroup.onmouseenter = function(e) {{
                const tooltip = document.getElementById("tooltip");
                tooltip.innerHTML = "<strong>" + node.name + "</strong><br>" +
                                   node.dimension + "<br>" +
                                   "Value: " + formatValue(node.value) + "<br>" +
                                   "Records: " + (node.count ? node.count.toLocaleString() : "N/A");
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

            // Color indicator bar
            const indicator = document.createElementNS("http://www.w3.org/2000/svg", "rect");
            indicator.setAttribute("x", -4);
            indicator.setAttribute("y", -15);
            indicator.setAttribute("width", 4);
            indicator.setAttribute("height", 30);
            indicator.setAttribute("rx", 2);
            indicator.setAttribute("fill", node.color);
            nodeGroup.appendChild(indicator);

            // Circle
            const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
            circle.setAttribute("class", "node-circle");
            circle.setAttribute("r", 7);
            const hasChildren = node.children && node.children.length > 0;
            circle.setAttribute("fill", hasChildren ? (node.expanded ? "#fff" : "#1976D2") : "#fff");
            circle.setAttribute("stroke", node.color);
            nodeGroup.appendChild(circle);

            // Name label
            const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
            text.setAttribute("class", "node-text");
            text.setAttribute("x", 15);
            text.setAttribute("y", -5);
            text.textContent = node.name;
            if (node.depth === 0) text.style.fontWeight = "bold";
            nodeGroup.appendChild(text);

            // Value label
            const valueText = document.createElementNS("http://www.w3.org/2000/svg", "text");
            valueText.setAttribute("class", "node-value");
            valueText.setAttribute("x", 15);
            valueText.setAttribute("y", 10);
            valueText.textContent = formatValue(node.value);
            nodeGroup.appendChild(valueText);

            // Bar background
            const barBg = document.createElementNS("http://www.w3.org/2000/svg", "rect");
            barBg.setAttribute("class", "node-bar-bg");
            barBg.setAttribute("x", 15);
            barBg.setAttribute("y", 16);
            barBg.setAttribute("width", config.barWidth);
            barBg.setAttribute("height", config.barHeight);
            barBg.setAttribute("rx", 2);
            nodeGroup.appendChild(barBg);

            // Bar fill (relative to siblings)
            const siblings = node.parent ? node.parent.children : [node];
            const values = siblings.map(s => s.value);
            const maxVal = Math.max(...values);
            const minVal = Math.min(...values);
            const range = maxVal - minVal || 1;
            const barFillWidth = Math.max(4, ((node.value - minVal) / range) * config.barWidth);

            const barFill = document.createElementNS("http://www.w3.org/2000/svg", "rect");
            barFill.setAttribute("class", "node-bar");
            barFill.setAttribute("x", 15);
            barFill.setAttribute("y", 16);
            barFill.setAttribute("width", barFillWidth);
            barFill.setAttribute("height", config.barHeight);
            barFill.setAttribute("rx", 2);
            barFill.setAttribute("fill", node.color);
            nodeGroup.appendChild(barFill);

            // Expand/collapse indicator
            if (hasChildren) {{
                const indicator = document.createElementNS("http://www.w3.org/2000/svg", "text");
                indicator.setAttribute("x", 0);
                indicator.setAttribute("y", 4);
                indicator.setAttribute("text-anchor", "middle");
                indicator.setAttribute("font-size", "10px");
                indicator.setAttribute("fill", node.expanded ? "#1976D2" : "#fff");
                indicator.setAttribute("pointer-events", "none");
                indicator.textContent = node.expanded ? "−" : "+";
                nodeGroup.appendChild(indicator);
            }}

            g.appendChild(nodeGroup);
        }});
    }}

    // Initialize
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
        st.header("Settings")

        selected_metric = st.selectbox(
            "Metric",
            options=list(DATA_CONFIG["metrics"].keys()),
            format_func=lambda x: DATA_CONFIG["metrics"][x]["label"],
            index=list(DATA_CONFIG["metrics"].keys()).index(st.session_state.selected_metric)
        )
        st.session_state.selected_metric = selected_metric

        st.markdown("---")

        st.markdown("### Dimension Order")
        selected_dims = st.multiselect(
            "Select and order dimensions",
            options=DATA_CONFIG["dimensions"],
            default=st.session_state.selected_dimensions,
            help="Order determines hierarchy depth"
        )

        if selected_dims:
            st.session_state.selected_dimensions = selected_dims

        st.markdown("---")
        st.markdown("### How to Use")
        st.markdown("""
        - **Click** nodes with **+** to expand
        - **Click** nodes with **−** to collapse
        - **Hover** for detailed tooltips
        - Blue filled = has children
        - White filled = expanded or leaf
        """)

        st.markdown("---")
        st.markdown("### Performance Legend")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("🟢 High")
            st.markdown("🟡 Medium")
        with col2:
            st.markdown("🟠 Low")
            st.markdown("🔵 Root")

    # Header
    st.title("Decomposition Tree")
    st.caption("Interactive drill-down analysis - Click nodes to expand/collapse")

    # Build and display tree
    if st.session_state.selected_dimensions:
        tree_data = build_hierarchy(
            df,
            st.session_state.selected_dimensions,
            selected_metric
        )

        html_content = create_tree_visualization(tree_data, selected_metric)
        components.html(html_content, height=700, scrolling=True)

        # Summary
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)

        total_value = calculate_metric(df, selected_metric)
        display_value = f"{total_value:.1f}%" if selected_metric == "OTP" else f"{total_value:,}"

        with col1:
            st.metric("Total Value", display_value)
        with col2:
            st.metric("Records", f"{len(df):,}")
        with col3:
            st.metric("Dimensions", len(st.session_state.selected_dimensions))
        with col4:
            st.metric("Metric", selected_metric)
    else:
        st.warning("Please select at least one dimension.")


if __name__ == "__main__":
    main()
