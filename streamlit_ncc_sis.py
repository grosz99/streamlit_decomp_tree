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
    layout="wide"
)


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
    if max_val == min_val:
        normalized = 0.5
    else:
        normalized = (value - min_val) / (max_val - min_val)

    if metric == "YoY_Growth":
        if value >= 10:
            return "#2E7D32"
        elif value >= 0:
            return "#8BC34A"
        elif value >= -10:
            return "#FFC107"
        else:
            return "#F44336"

    if normalized >= 0.7:
        return "#2E7D32"
    elif normalized >= 0.5:
        return "#8BC34A"
    elif normalized >= 0.3:
        return "#FFC107"
    else:
        return "#FF9800"


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
        "color": "#1976D2",
        "count": len(df),
        "children": build_level(df, dimensions)
    }


def create_tree_visualization(tree_data: Dict, metric: str) -> str:
    tree_json = json.dumps(tree_data)
    format_type = "percent" if metric == "YoY_Growth" else "currency"

    return f'''
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
    max-width: 250px; box-shadow: 0 2px 8px rgba(0,0,0,0.3);
}}
</style>
</head>
<body>
<div class="tree-container"><svg id="tree-svg"></svg></div>
<div id="tooltip" class="tooltip"></div>
<script>
(function() {{
    "use strict";
    const data = {tree_json};
    const formatType = "{format_type}";
    const config = {{
        nodeWidth: 200, nodeHeight: 55, levelGap: 240, siblingGap: 10,
        barWidth: 70, barHeight: 6,
        margin: {{ top: 40, right: 150, bottom: 40, left: 100 }}
    }};
    let nodeId = 0, root = null;

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
            node.children.forEach(child => {{ child.parent = node; processNode(child, depth + 1); }});
        }}
        return node;
    }}

    function calculateLayout(node) {{
        let yOffset = 0;
        function layoutNode(n, x) {{
            n.x = x;
            if (n.expanded && n.children && n.children.length > 0) {{
                n.children.forEach(child => layoutNode(child, x + config.levelGap));
                n.y = (n.children[0].y + n.children[n.children.length - 1].y) / 2;
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
        if (node.expanded && node.children) node.children.forEach(c => getVisibleNodes(c, nodes));
        return nodes;
    }}

    function getVisibleLinks(node, links) {{
        links = links || [];
        if (node.expanded && node.children) {{
            node.children.forEach(c => {{ links.push({{ source: node, target: c }}); getVisibleLinks(c, links); }});
        }}
        return links;
    }}

    function linkPath(s, t) {{
        const midX = (s.x + t.x) / 2;
        return "M" + s.x + "," + s.y + "C" + midX + "," + s.y + " " + midX + "," + t.y + " " + t.x + "," + t.y;
    }}

    function render() {{
        const height = calculateLayout(root);
        const svg = document.getElementById("tree-svg");
        svg.setAttribute("width", 1400);
        svg.setAttribute("height", Math.max(500, height + config.margin.top + config.margin.bottom));
        svg.innerHTML = "";

        const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
        g.setAttribute("transform", "translate(0," + config.margin.top + ")");
        svg.appendChild(g);

        getVisibleLinks(root).forEach(link => {{
            const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
            path.setAttribute("class", "link");
            path.setAttribute("d", linkPath(link.source, link.target));
            g.appendChild(path);
        }});

        getVisibleNodes(root).forEach(node => {{
            const ng = document.createElementNS("http://www.w3.org/2000/svg", "g");
            ng.setAttribute("class", "node");
            ng.setAttribute("transform", "translate(" + node.x + "," + node.y + ")");

            if (node.children && node.children.length > 0) {{
                ng.onclick = function(e) {{ e.stopPropagation(); node.expanded = !node.expanded; render(); }};
            }}

            ng.onmouseenter = function(e) {{
                const tt = document.getElementById("tooltip");
                tt.innerHTML = "<strong>" + node.name + "</strong><br><em>" + node.dimension + "</em><br>Value: " + formatValue(node.value) + "<br>Records: " + (node.count ? node.count.toLocaleString() : "N/A");
                tt.style.display = "block";
                tt.style.left = (e.clientX + 15) + "px";
                tt.style.top = (e.clientY - 10) + "px";
            }};
            ng.onmouseleave = function() {{ document.getElementById("tooltip").style.display = "none"; }};
            ng.onmousemove = function(e) {{
                const tt = document.getElementById("tooltip");
                tt.style.left = (e.clientX + 15) + "px";
                tt.style.top = (e.clientY - 10) + "px";
            }};

            const ind = document.createElementNS("http://www.w3.org/2000/svg", "rect");
            ind.setAttribute("x", -4); ind.setAttribute("y", -18);
            ind.setAttribute("width", 4); ind.setAttribute("height", 36);
            ind.setAttribute("rx", 2); ind.setAttribute("fill", node.color);
            ng.appendChild(ind);

            const circ = document.createElementNS("http://www.w3.org/2000/svg", "circle");
            circ.setAttribute("class", "node-circle");
            circ.setAttribute("r", 8);
            const hasKids = node.children && node.children.length > 0;
            circ.setAttribute("fill", hasKids ? (node.expanded ? "#fff" : "#1976D2") : "#fff");
            circ.setAttribute("stroke", node.color);
            ng.appendChild(circ);

            const txt = document.createElementNS("http://www.w3.org/2000/svg", "text");
            txt.setAttribute("class", "node-text");
            txt.setAttribute("x", 18); txt.setAttribute("y", -6);
            txt.textContent = node.name;
            if (node.depth === 0) txt.style.fontWeight = "bold";
            ng.appendChild(txt);

            const valTxt = document.createElementNS("http://www.w3.org/2000/svg", "text");
            valTxt.setAttribute("class", "node-value");
            valTxt.setAttribute("x", 18); valTxt.setAttribute("y", 10);
            valTxt.textContent = formatValue(node.value);
            ng.appendChild(valTxt);

            const barBg = document.createElementNS("http://www.w3.org/2000/svg", "rect");
            barBg.setAttribute("class", "node-bar-bg");
            barBg.setAttribute("x", 18); barBg.setAttribute("y", 18);
            barBg.setAttribute("width", config.barWidth); barBg.setAttribute("height", config.barHeight);
            barBg.setAttribute("rx", 2);
            ng.appendChild(barBg);

            const sibs = node.parent ? node.parent.children : [node];
            const maxVal = Math.max(...sibs.map(s => Math.abs(s.value)));
            const bw = maxVal > 0 ? Math.max(4, (Math.abs(node.value) / maxVal) * config.barWidth) : 4;

            const barFill = document.createElementNS("http://www.w3.org/2000/svg", "rect");
            barFill.setAttribute("class", "node-bar");
            barFill.setAttribute("x", 18); barFill.setAttribute("y", 18);
            barFill.setAttribute("width", bw); barFill.setAttribute("height", config.barHeight);
            barFill.setAttribute("rx", 2); barFill.setAttribute("fill", node.color);
            ng.appendChild(barFill);

            if (hasKids) {{
                const expInd = document.createElementNS("http://www.w3.org/2000/svg", "text");
                expInd.setAttribute("x", 0); expInd.setAttribute("y", 4);
                expInd.setAttribute("text-anchor", "middle");
                expInd.setAttribute("font-size", "11px");
                expInd.setAttribute("fill", node.expanded ? "#1976D2" : "#fff");
                expInd.setAttribute("pointer-events", "none");
                expInd.textContent = node.expanded ? "−" : "+";
                ng.appendChild(expInd);
            }}
            g.appendChild(ng);
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
        st.header("Analysis Settings")
        st.caption(f"Source: {DATA_CONFIG['table']}")

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
        st.markdown("### Drill-Down Hierarchy")
        selected_dims = st.multiselect(
            "Select dimensions",
            options=DATA_CONFIG["dimensions"],
            default=st.session_state.selected_dimensions,
            format_func=lambda x: DATA_CONFIG["dimension_labels"].get(x, x)
        )
        if selected_dims:
            st.session_state.selected_dimensions = selected_dims

        st.markdown("---")
        st.markdown("### Time Filters")
        years = sorted(df['YEAR'].unique())
        selected_years = st.multiselect("Year(s)", years, default=years)
        months = sorted(df['MONTH_OF_YEAR'].unique())
        selected_months = st.multiselect("Month(s)", months, default=months)

    filtered_df = df[
        (df['DATA_SCENARIO'] == selected_scenario) &
        (df['YEAR'].isin(selected_years)) &
        (df['MONTH_OF_YEAR'].isin(selected_months))
    ]

    st.title("NCC Decomposition Tree")
    st.caption(f"Analyzing {DATA_CONFIG['metrics'][selected_metric]['label']} | Scenario: {selected_scenario}")

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

    if st.session_state.selected_dimensions and len(filtered_df) > 0:
        tree_data = build_hierarchy(filtered_df, st.session_state.selected_dimensions, selected_metric)
        components.html(create_tree_visualization(tree_data, selected_metric), height=750, scrolling=True)
    else:
        st.warning("Select at least one dimension.")


if __name__ == "__main__":
    main()
