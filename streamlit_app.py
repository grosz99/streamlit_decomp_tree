"""
Decomposition Tree - Power BI Style with D3.js Collapsible Tree
A drill-down analysis tool using st.components.v1.html for interactive D3 visualization
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

        # OTP (On-Time Performance) - percentage metric
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
# BUILD HIERARCHICAL DATA
# ============================================

def build_hierarchy(df: pd.DataFrame, dimensions: List[str], metric: str) -> Dict:
    """Build a nested hierarchical structure for D3 tree"""

    def calc_metric(subset):
        if metric == "OTP":
            if len(subset) == 0 or subset['Trips'].sum() == 0:
                return 0
            return round(np.average(subset['OTP'], weights=subset['Trips']), 1)
        else:
            return int(subset['Trips'].sum())

    def get_color(value, min_val, max_val):
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

    def build_level(data, dims_remaining, parent_path=""):
        if not dims_remaining or len(data) == 0:
            return []

        current_dim = dims_remaining[0]
        next_dims = dims_remaining[1:]

        groups = data.groupby(current_dim)
        children = []

        values = []
        for name, group in groups:
            values.append(calc_metric(group))

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
                node["_children"] = build_level(group, next_dims, f"{parent_path}/{name}")

            children.append(node)

        # Sort by value descending
        children.sort(key=lambda x: x["value"], reverse=True)
        return children

    # Root node
    root_value = calc_metric(df)
    root = {
        "name": "CJTP",
        "dimension": "Total",
        "value": root_value,
        "color": "#1976D2",
        "count": len(df),
        "_children": build_level(df, dimensions)
    }

    return root


def create_d3_collapsible_tree(tree_data: Dict, metric: str) -> str:
    """Create the D3.js collapsible tree visualization"""

    tree_json = json.dumps(tree_data)
    format_type = "percent" if metric == "OTP" else "number"

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
                background: #ffffff;
                overflow: auto;
            }}
            .node {{
                cursor: pointer;
            }}
            .node circle {{
                stroke-width: 2px;
            }}
            .node text {{
                font-size: 12px;
                fill: #333;
            }}
            .node .value-text {{
                font-size: 11px;
                fill: #666;
            }}
            .node .bar-bg {{
                fill: #e0e0e0;
            }}
            .link {{
                fill: none;
                stroke: #1976D2;
                stroke-opacity: 0.4;
                stroke-width: 1.5px;
            }}
            .tooltip {{
                position: absolute;
                background: rgba(0,0,0,0.8);
                color: white;
                padding: 8px 12px;
                border-radius: 4px;
                font-size: 12px;
                pointer-events: none;
                z-index: 1000;
            }}
        </style>
    </head>
    <body>
        <div id="tree-container"></div>
        <div id="tooltip" class="tooltip" style="display:none;"></div>

        <script>
            const treeData = {tree_json};
            const formatType = "{format_type}";

            function formatValue(val) {{
                if (formatType === "percent") {{
                    return val.toFixed(1) + "%";
                }} else {{
                    return val.toLocaleString();
                }}
            }}

            // Set dimensions
            const margin = {{top: 20, right: 200, bottom: 20, left: 100}};
            const width = 1200;
            const barWidth = 60;
            const barHeight = 8;

            // Calculate dynamic height based on expanded nodes
            let nodeCount = 0;
            function countNodes(node) {{
                nodeCount++;
                if (node.children) {{
                    node.children.forEach(countNodes);
                }}
            }}

            // Create SVG
            const svg = d3.select("#tree-container")
                .append("svg")
                .attr("width", width)
                .attr("height", 800)
                .append("g")
                .attr("transform", `translate(${{margin.left}},${{margin.top}})`);

            // Create tooltip
            const tooltip = d3.select("#tooltip");

            // Tree layout
            const treeLayout = d3.tree().nodeSize([35, 200]);

            // Create hierarchy
            const root = d3.hierarchy(treeData);
            root.x0 = 0;
            root.y0 = 0;

            // Initially expand first two levels
            root.descendants().forEach((d, i) => {{
                if (d.depth < 1) {{
                    d._children = d.children || d.data._children?.map(c => d3.hierarchy(c));
                    if (d.data._children && !d.children) {{
                        d.children = d.data._children.map(c => {{
                            const node = d3.hierarchy(c);
                            node.parent = d;
                            node.depth = d.depth + 1;
                            return node;
                        }});
                    }}
                }} else {{
                    if (d.children) {{
                        d._children = d.children;
                        d.children = null;
                    }} else if (d.data._children) {{
                        d._children = d.data._children.map(c => {{
                            const node = d3.hierarchy(c);
                            node.parent = d;
                            node.depth = d.depth + 1;
                            return node;
                        }});
                    }}
                }}
            }});

            // Collapse function
            function collapse(d) {{
                if (d.children) {{
                    d._children = d.children;
                    d._children.forEach(collapse);
                    d.children = null;
                }}
            }}

            // Process initial data - expand root, collapse others
            function processNode(node, depth = 0) {{
                if (node.data._children && depth < 1) {{
                    node.children = node.data._children.map(childData => {{
                        const child = d3.hierarchy(childData);
                        child.parent = node;
                        child.depth = depth + 1;
                        processNode(child, depth + 1);
                        return child;
                    }});
                }} else if (node.data._children) {{
                    node._children = node.data._children;
                }}
                return node;
            }}

            const rootNode = d3.hierarchy(treeData);
            processNode(rootNode);
            rootNode.x0 = 0;
            rootNode.y0 = 0;

            let i = 0;
            const duration = 400;

            update(rootNode);

            function update(source) {{
                // Compute the new tree layout
                const treeData = treeLayout(rootNode);
                const nodes = treeData.descendants();
                const links = treeData.links();

                // Normalize for fixed-depth
                nodes.forEach(d => {{
                    d.y = d.depth * 220;
                }});

                // Calculate SVG height
                let minX = Infinity, maxX = -Infinity;
                nodes.forEach(d => {{
                    if (d.x < minX) minX = d.x;
                    if (d.x > maxX) maxX = d.x;
                }});
                const height = Math.max(400, maxX - minX + 100);

                d3.select("#tree-container svg")
                    .attr("height", height + margin.top + margin.bottom);

                // Shift tree to center vertically
                const yOffset = -minX + 50;
                svg.attr("transform", `translate(${{margin.left}},${{yOffset}})`);

                // ****************** Nodes section ***************************
                const node = svg.selectAll("g.node")
                    .data(nodes, d => d.id || (d.id = ++i));

                // Enter new nodes at the parent's previous position
                const nodeEnter = node.enter().append("g")
                    .attr("class", "node")
                    .attr("transform", d => `translate(${{source.y0}},${{source.x0}})`)
                    .on("click", (event, d) => click(event, d))
                    .on("mouseover", (event, d) => {{
                        tooltip.style("display", "block")
                            .html(`<strong>${{d.data.name}}</strong><br/>
                                   ${{d.data.dimension}}<br/>
                                   Value: ${{formatValue(d.data.value)}}<br/>
                                   Records: ${{d.data.count?.toLocaleString() || 'N/A'}}`)
                            .style("left", (event.pageX + 10) + "px")
                            .style("top", (event.pageY - 10) + "px");
                    }})
                    .on("mouseout", () => {{
                        tooltip.style("display", "none");
                    }});

                // Add colored bar indicator
                nodeEnter.append("rect")
                    .attr("class", "bar-indicator")
                    .attr("x", -4)
                    .attr("y", -12)
                    .attr("width", 4)
                    .attr("height", 24)
                    .attr("rx", 2)
                    .attr("fill", d => d.data.color || "#1976D2");

                // Add Circle for the nodes
                nodeEnter.append("circle")
                    .attr("r", 1e-6)
                    .style("fill", d => d._children || d.data._children ? "#1976D2" : "#fff")
                    .style("stroke", d => d.data.color || "#1976D2");

                // Add labels for the nodes
                nodeEnter.append("text")
                    .attr("dy", "-0.5em")
                    .attr("x", 15)
                    .attr("text-anchor", "start")
                    .text(d => d.data.name)
                    .style("font-weight", d => d.depth === 0 ? "bold" : "normal");

                // Add value labels
                nodeEnter.append("text")
                    .attr("class", "value-text")
                    .attr("dy", "1em")
                    .attr("x", 15)
                    .attr("text-anchor", "start")
                    .text(d => formatValue(d.data.value));

                // Add bar background
                nodeEnter.append("rect")
                    .attr("class", "bar-bg")
                    .attr("x", 15)
                    .attr("y", 18)
                    .attr("width", barWidth)
                    .attr("height", barHeight)
                    .attr("rx", 2);

                // Add bar fill
                nodeEnter.append("rect")
                    .attr("class", "bar-fill")
                    .attr("x", 15)
                    .attr("y", 18)
                    .attr("width", 0)
                    .attr("height", barHeight)
                    .attr("rx", 2)
                    .attr("fill", d => d.data.color || "#1976D2");

                // UPDATE
                const nodeUpdate = nodeEnter.merge(node);

                // Transition to the proper position for the node
                nodeUpdate.transition()
                    .duration(duration)
                    .attr("transform", d => `translate(${{d.y}},${{d.x}})`);

                // Update the node attributes and style
                nodeUpdate.select("circle")
                    .attr("r", 6)
                    .style("fill", d => d._children || d.data._children ? "#1976D2" : "#fff")
                    .style("stroke", d => d.data.color || "#1976D2")
                    .attr("cursor", d => (d._children || d.data._children) ? "pointer" : "default");

                // Update bar fill width based on relative value
                nodeUpdate.select(".bar-fill")
                    .transition()
                    .duration(duration)
                    .attr("width", d => {{
                        // Find siblings to calculate relative width
                        const siblings = d.parent ? d.parent.children || [] : [d];
                        const values = siblings.map(s => s.data.value);
                        const maxVal = Math.max(...values);
                        const minVal = Math.min(...values);
                        const range = maxVal - minVal || 1;
                        return ((d.data.value - minVal) / range) * barWidth || 5;
                    }});

                // Remove any exiting nodes
                const nodeExit = node.exit().transition()
                    .duration(duration)
                    .attr("transform", d => `translate(${{source.y}},${{source.x}})`)
                    .remove();

                nodeExit.select("circle")
                    .attr("r", 1e-6);

                nodeExit.select("text")
                    .style("fill-opacity", 1e-6);

                // ****************** Links section ***************************
                const link = svg.selectAll("path.link")
                    .data(links, d => d.target.id);

                // Enter any new links at the parent's previous position
                const linkEnter = link.enter().insert("path", "g")
                    .attr("class", "link")
                    .attr("d", d => {{
                        const o = {{x: source.x0, y: source.y0}};
                        return diagonal(o, o);
                    }});

                // UPDATE
                const linkUpdate = linkEnter.merge(link);

                // Transition back to the parent element position
                linkUpdate.transition()
                    .duration(duration)
                    .attr("d", d => diagonal(d.source, d.target));

                // Remove any exiting links
                link.exit().transition()
                    .duration(duration)
                    .attr("d", d => {{
                        const o = {{x: source.x, y: source.y}};
                        return diagonal(o, o);
                    }})
                    .remove();

                // Store the old positions for transition
                nodes.forEach(d => {{
                    d.x0 = d.x;
                    d.y0 = d.y;
                }});

                // Creates a curved path from parent to child
                function diagonal(s, d) {{
                    return `M ${{s.y}} ${{s.x}}
                            C ${{(s.y + d.y) / 2}} ${{s.x}},
                              ${{(s.y + d.y) / 2}} ${{d.x}},
                              ${{d.y}} ${{d.x}}`;
                }}

                // Toggle children on click
                function click(event, d) {{
                    if (d._children) {{
                        // Expand: convert stored data to hierarchy nodes
                        d.children = d._children.map ? d._children :
                            d._children.map(c => {{
                                const node = d3.hierarchy(c);
                                node.parent = d;
                                node.depth = d.depth + 1;
                                return node;
                            }});

                        // If _children was raw data, convert it
                        if (d.data._children && !d._children.map) {{
                            d.children = d.data._children.map(childData => {{
                                const child = d3.hierarchy(childData);
                                child.parent = d;
                                child.depth = d.depth + 1;
                                // Process nested children
                                if (childData._children) {{
                                    child._children = childData._children;
                                }}
                                return child;
                            }});
                        }}
                        d._children = null;
                    }} else if (d.children) {{
                        // Collapse
                        d._children = d.children;
                        d.children = null;
                    }} else if (d.data._children) {{
                        // First expansion from raw data
                        d.children = d.data._children.map(childData => {{
                            const child = d3.hierarchy(childData);
                            child.parent = d;
                            child.depth = d.depth + 1;
                            if (childData._children) {{
                                child._children = childData._children;
                            }}
                            return child;
                        }});
                    }}
                    update(d);
                }}
            }}
        </script>
    </body>
    </html>
    """

    return html


# ============================================
# DATA CONFIGURATION
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
    st.session_state.selected_dimensions = ["Division", "Depot", "Route", "Direction", "Period"]

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
        st.caption("Drag to reorder (use multiselect)")

        selected_dims = st.multiselect(
            "Select dimensions to include",
            options=DATA_CONFIG["dimensions"],
            default=st.session_state.selected_dimensions,
            help="Order matters - first dimension is the first level"
        )

        if selected_dims:
            st.session_state.selected_dimensions = selected_dims

        st.markdown("---")
        st.markdown("### How to Use")
        st.markdown("""
        - **Click** filled circles to expand/collapse
        - **Hover** over nodes for details
        - Blue circles have children to explore
        - Bars show relative performance within each level
        """)

        st.markdown("---")
        st.markdown("### Legend")
        cols = st.columns(2)
        with cols[0]:
            st.markdown("🟢 High")
            st.markdown("🟡 Medium")
        with cols[1]:
            st.markdown("🟠 Low")
            st.markdown("🔵 Root/Branch")

    # Header
    st.title("Decomposition Tree")
    st.caption("Click nodes to expand/collapse - Power BI style interactive drill-down")

    # Build hierarchical data
    if st.session_state.selected_dimensions:
        tree_data = build_hierarchy(
            df,
            st.session_state.selected_dimensions,
            selected_metric
        )

        # Create and display D3 visualization
        html_content = create_d3_collapsible_tree(tree_data, selected_metric)
        components.html(html_content, height=700, scrolling=True)

        # Summary stats
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)

        if selected_metric == "OTP":
            total_value = np.average(df['OTP'], weights=df['Trips'])
            display_value = f"{total_value:.1f}%"
        else:
            total_value = df['Trips'].sum()
            display_value = f"{total_value:,}"

        with col1:
            st.metric("Total Value", display_value)
        with col2:
            st.metric("Records", f"{len(df):,}")
        with col3:
            st.metric("Dimensions", len(st.session_state.selected_dimensions))
        with col4:
            st.metric("Metric", selected_metric)
    else:
        st.warning("Please select at least one dimension in the sidebar.")

if __name__ == "__main__":
    main()
