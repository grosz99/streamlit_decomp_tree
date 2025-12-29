"""
NCC Decomposition Tree - Streamlit in Snowflake
Source: MY_WORKFLOW_DB.PUBLIC.NCC_TEST
Drill down: Region → System → Profit Center → Practice Area

Note: Single file required for Streamlit in Snowflake compatibility
"""

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import json
from typing import Dict, List
from snowflake.snowpark.context import get_active_session
from snowflake.cortex import Complete

# =============================================================================
# CONFIGURATION
# =============================================================================

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

# Cortex AI model - Available 2025: claude-3-5-sonnet, llama3.3-70b, mistral-large2
CORTEX_MODEL = "claude-3-5-sonnet"

# =============================================================================
# PAGE CONFIG & STYLES
# =============================================================================

st.set_page_config(
    page_title="NCC Decomposition Tree",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp { font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }
    h1 { color: #1B5E3F !important; font-weight: 700 !important; font-size: 1.75rem !important; }
    .subtitle { color: #6B7280; font-size: 0.95rem; margin-bottom: 1.5rem; }
    [data-testid="stSidebar"] { background-color: #F9FAFB; border-right: 1px solid #E5E7EB; }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 { color: #1B5E3F !important; }
    [data-testid="stMetric"] { background-color: white; border: 1px solid #E5E7EB; border-radius: 12px; padding: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
    [data-testid="stMetricLabel"] { color: #6B7280 !important; font-size: 0.85rem !important; }
    [data-testid="stMetricValue"] { color: #1B5E3F !important; font-weight: 600 !important; }
    .stButton > button { background-color: #1B5E3F; color: white; border: none; border-radius: 8px; padding: 0.5rem 1rem; font-weight: 500; }
    .stButton > button:hover { background-color: #154a32; color: white; }
    .stSelectbox > div > div, .stMultiSelect > div > div { border-radius: 8px; border-color: #E5E7EB; }
    hr { border-color: #E5E7EB; margin: 1.5rem 0; }
    .category-badge { display: inline-block; padding: 0.25rem 0.75rem; background-color: #E8F5EE; color: #1B5E3F; border-radius: 4px; font-size: 0.75rem; font-weight: 500; }
    .info-box { background-color: #F9FAFB; border: 1px solid #E5E7EB; border-radius: 12px; padding: 1rem; margin: 1rem 0; }
    .info-box h4 { color: #1B5E3F; font-size: 0.9rem; font-weight: 600; margin-bottom: 0.5rem; }
    .info-box p { color: #6B7280; font-size: 0.85rem; margin: 0.25rem 0; }
    .legend-item { display: flex; align-items: center; gap: 0.5rem; margin: 0.25rem 0; font-size: 0.85rem; color: #4B5563; }
    .legend-dot { width: 12px; height: 12px; border-radius: 50%; }
    .ai-insights-panel { background: linear-gradient(135deg, #F0FDF4 0%, #ECFDF5 100%); border: 1px solid #86EFAC; border-radius: 12px; padding: 1.25rem; margin: 1rem 0; }
    .ai-insights-header { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.75rem; }
    .ai-insights-header h4 { color: #1B5E3F; font-size: 1rem; font-weight: 600; margin: 0; }
    .ai-badge { background-color: #1B5E3F; color: white; padding: 0.15rem 0.5rem; border-radius: 4px; font-size: 0.65rem; font-weight: 600; text-transform: uppercase; }
    .ai-insights-content { color: #374151; font-size: 0.9rem; line-height: 1.6; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# =============================================================================
# DATA FUNCTIONS
# =============================================================================

@st.cache_data(ttl=300)
def load_data(table_name: str) -> pd.DataFrame:
    session = get_active_session()
    return session.table(table_name).to_pandas()


def calculate_metric(df: pd.DataFrame, metric: str) -> float:
    if len(df) == 0:
        return 0.0
    if metric == "NCC":
        return round(df['NCC'].sum(), 2)
    elif metric == "NCC_PY":
        return round(df['NCC_PY'].sum(), 2)
    elif metric == "YoY_Growth":
        ncc, ncc_py = df['NCC'].sum(), df['NCC_PY'].sum()
        return round(((ncc - ncc_py) / ncc_py) * 100, 1) if ncc_py != 0 else 0.0
    elif metric == "Avg_NCC":
        return round(df['NCC'].mean(), 2)
    return 0.0


def get_color(value: float, min_val: float, max_val: float, metric: str) -> str:
    normalized = 0.5 if max_val == min_val else (value - min_val) / (max_val - min_val)
    if metric == "YoY_Growth":
        if value >= 10: return "#1B5E3F"
        elif value >= 0: return "#2D8B5E"
        elif value >= -10: return "#F59E0B"
        else: return "#DC2626"
    if normalized >= 0.7: return "#1B5E3F"
    elif normalized >= 0.5: return "#2D8B5E"
    elif normalized >= 0.3: return "#F59E0B"
    else: return "#DC2626"


def build_hierarchy(df: pd.DataFrame, dimensions: List[str], metric: str) -> Dict:
    def build_level(data: pd.DataFrame, dims_remaining: List[str]) -> List[Dict]:
        if not dims_remaining or len(data) == 0:
            return []
        current_dim, next_dims = dims_remaining[0], dims_remaining[1:]
        groups = list(data.groupby(current_dim))
        values = [calculate_metric(group, metric) for _, group in groups]
        min_val, max_val = (min(values), max(values)) if values else (0, 1)
        children = []
        for (name, group), value in zip(groups, values):
            node = {"name": str(name), "dimension": current_dim, "value": value,
                    "color": get_color(value, min_val, max_val, metric), "count": len(group)}
            if next_dims:
                node["children"] = build_level(group, next_dims)
            children.append(node)
        return sorted(children, key=lambda x: x["value"], reverse=True)

    root_value = calculate_metric(df, metric)
    return {"name": "Total NCC", "dimension": "Total", "value": root_value,
            "color": "#1B5E3F", "count": len(df), "children": build_level(df, dimensions)}


def flatten_tree(node: Dict, path: str = "") -> List[Dict]:
    current_path = f"{path} > {node['name']}" if path else node['name']
    results = [{'label': f"{node['dimension']}: {node['name']}", 'path': current_path, 'data': node}]
    for child in node.get('children', []):
        results.extend(flatten_tree(child, current_path))
    return results

# =============================================================================
# AI INSIGHTS
# =============================================================================

def generate_ai_summary(node_data: Dict, filtered_df: pd.DataFrame, metric_label: str) -> str:
    node_name, dimension = node_data.get('name', 'Unknown'), node_data.get('dimension', 'Unknown')
    value, record_count = node_data.get('value', 0), node_data.get('count', 0)

    children_summary = ""
    if node_data.get('children'):
        top_children = node_data['children'][:5]
        children_summary = "Top segments: " + ", ".join([f"{c['name']} (${c['value']/1e6:.1f}M)" for c in top_children])

    yoy_info = ""
    if len(filtered_df) > 0:
        total_ncc, total_py = filtered_df['NCC'].sum(), filtered_df['NCC_PY'].sum()
        if total_py > 0:
            yoy_info = f"Year-over-year growth: {((total_ncc - total_py) / total_py) * 100:+.1f}%"

    prompt = f"""You are a financial analyst. Provide a brief summary (3-4 sentences) about this NCC segment.
Segment: {node_name} | Dimension: {dimension} | Value: ${value/1e6:.2f}M | Records: {record_count:,}
{yoy_info} {children_summary}
Focus on: 1) Performance assessment 2) One actionable insight"""

    try:
        return Complete(model=CORTEX_MODEL, prompt=prompt, session=get_active_session())
    except Exception as e:
        return f"Unable to generate insights: {str(e)}"

# =============================================================================
# TREE VISUALIZATION
# =============================================================================

def create_tree_html(tree_data: Dict, metric: str) -> str:
    tree_json = json.dumps(tree_data)
    fmt = "percent" if metric == "YoY_Growth" else "currency"
    return f'''<!DOCTYPE html><html><head><style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: 'Inter', -apple-system, sans-serif; background: #FFF; color: #1F2937; }}
.tree-container {{ padding: 24px; background: #FFF; border-radius: 12px; border: 1px solid #E5E7EB; margin: 8px; }}
svg {{ overflow: visible; }} .node {{ cursor: pointer; }}
.node-rect {{ fill: #FFF; stroke: #E5E7EB; stroke-width: 1px; rx: 8px; transition: all 0.2s; }}
.node:hover .node-rect {{ stroke: #1B5E3F; stroke-width: 2px; }}
.node-text {{ font-size: 13px; font-weight: 500; fill: #1F2937; pointer-events: none; }}
.node-value {{ font-size: 12px; font-weight: 600; fill: #1B5E3F; pointer-events: none; }}
.node-dimension {{ font-size: 10px; fill: #9CA3AF; pointer-events: none; text-transform: uppercase; }}
.node-bar-bg {{ fill: #F3F4F6; rx: 3px; }} .node-bar {{ rx: 3px; transition: width 0.3s; }}
.link {{ fill: none; stroke: #D1D5DB; stroke-width: 1.5px; }}
.tooltip {{ position: fixed; background: #1F2937; color: #FFF; padding: 12px 16px; border-radius: 8px; font-size: 13px; pointer-events: none; z-index: 1000; display: none; max-width: 250px; }}
.tooltip .label {{ color: #9CA3AF; font-size: 11px; text-transform: uppercase; margin-top: 8px; display: block; }}
.tooltip .value {{ color: #10B981; font-weight: 600; }}
</style></head><body>
<div class="tree-container"><svg id="tree-svg"></svg></div>
<div id="tooltip" class="tooltip"></div>
<script>(function() {{
const data = {tree_json}, formatType = "{fmt}";
const config = {{ nodeWidth: 170, nodeHeight: 68, levelGap: 210, siblingGap: 12, barWidth: 90, barHeight: 6, margin: {{ top: 40, right: 160, bottom: 40, left: 60 }} }};
let nodeId = 0, root = null;
function formatValue(val) {{
    if (formatType === "percent") return (val >= 0 ? "+" : "") + val.toFixed(1) + "%";
    if (val >= 1e9) return "$" + (val/1e9).toFixed(1) + "B";
    if (val >= 1e6) return "$" + (val/1e6).toFixed(1) + "M";
    if (val >= 1e3) return "$" + (val/1e3).toFixed(1) + "K";
    return "$" + val.toLocaleString();
}}
function processNode(node, depth) {{
    node.id = ++nodeId; node.depth = depth; node.expanded = depth < 1;
    if (node.children) node.children.forEach(c => {{ c.parent = node; processNode(c, depth + 1); }});
    return node;
}}
function calculateLayout(node) {{
    let yOffset = 0;
    function layoutNode(n, x) {{
        n.x = x;
        if (n.expanded && n.children && n.children.length > 0) {{
            n.children.forEach(c => layoutNode(c, x + config.levelGap));
            n.y = (n.children[0].y + n.children[n.children.length - 1].y) / 2;
        }} else {{ n.y = yOffset; yOffset += config.nodeHeight + config.siblingGap; }}
    }}
    layoutNode(node, config.margin.left);
    return yOffset;
}}
function getVisibleNodes(node, nodes = []) {{
    nodes.push(node);
    if (node.expanded && node.children) node.children.forEach(c => getVisibleNodes(c, nodes));
    return nodes;
}}
function getVisibleLinks(node, links = []) {{
    if (node.expanded && node.children) node.children.forEach(c => {{ links.push({{source: node, target: c}}); getVisibleLinks(c, links); }});
    return links;
}}
function linkPath(s, t) {{
    const midX = (s.x + config.nodeWidth/2 + t.x) / 2;
    return `M${{s.x + config.nodeWidth}},${{s.y + config.nodeHeight/2}} C${{midX}},${{s.y + config.nodeHeight/2}} ${{midX}},${{t.y + config.nodeHeight/2}} ${{t.x}},${{t.y + config.nodeHeight/2}}`;
}}
function render() {{
    const height = calculateLayout(root);
    const svg = document.getElementById("tree-svg");
    svg.setAttribute("width", 1200);
    svg.setAttribute("height", Math.max(500, height + config.margin.top + config.margin.bottom));
    svg.innerHTML = "";
    const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
    g.setAttribute("transform", `translate(0,${{config.margin.top}})`);
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
        ng.setAttribute("transform", `translate(${{node.x}},${{node.y}})`);
        const hasChildren = node.children && node.children.length > 0;
        if (hasChildren) {{ ng.onclick = e => {{ e.stopPropagation(); node.expanded = !node.expanded; render(); }}; ng.style.cursor = "pointer"; }}
        ng.onmouseenter = e => {{
            const tt = document.getElementById("tooltip");
            tt.innerHTML = `<strong>${{node.name}}</strong><span class="label">${{node.dimension}}</span><span class="label">Value</span><span class="value">${{formatValue(node.value)}}</span><span class="label">Records</span>${{node.count ? node.count.toLocaleString() : 'N/A'}}`;
            tt.style.display = "block"; tt.style.left = (e.clientX + 15) + "px"; tt.style.top = (e.clientY - 10) + "px";
        }};
        ng.onmouseleave = () => document.getElementById("tooltip").style.display = "none";
        ng.onmousemove = e => {{ const tt = document.getElementById("tooltip"); tt.style.left = (e.clientX + 15) + "px"; tt.style.top = (e.clientY - 10) + "px"; }};
        const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
        rect.setAttribute("class", "node-rect"); rect.setAttribute("width", config.nodeWidth); rect.setAttribute("height", config.nodeHeight); rect.setAttribute("rx", 8);
        ng.appendChild(rect);
        const ind = document.createElementNS("http://www.w3.org/2000/svg", "rect");
        ind.setAttribute("x", 0); ind.setAttribute("y", 0); ind.setAttribute("width", 4); ind.setAttribute("height", config.nodeHeight); ind.setAttribute("fill", node.color);
        ng.appendChild(ind);
        const dimText = document.createElementNS("http://www.w3.org/2000/svg", "text");
        dimText.setAttribute("class", "node-dimension"); dimText.setAttribute("x", 14); dimText.setAttribute("y", 18); dimText.textContent = node.dimension;
        ng.appendChild(dimText);
        const nameText = document.createElementNS("http://www.w3.org/2000/svg", "text");
        nameText.setAttribute("class", "node-text"); nameText.setAttribute("x", 14); nameText.setAttribute("y", 36);
        nameText.textContent = node.name.length > 18 ? node.name.substring(0, 16) + "..." : node.name;
        ng.appendChild(nameText);
        const valueText = document.createElementNS("http://www.w3.org/2000/svg", "text");
        valueText.setAttribute("class", "node-value"); valueText.setAttribute("x", 14); valueText.setAttribute("y", 52); valueText.textContent = formatValue(node.value);
        ng.appendChild(valueText);
        const barBg = document.createElementNS("http://www.w3.org/2000/svg", "rect");
        barBg.setAttribute("class", "node-bar-bg"); barBg.setAttribute("x", 14); barBg.setAttribute("y", 58); barBg.setAttribute("width", config.barWidth); barBg.setAttribute("height", config.barHeight);
        ng.appendChild(barBg);
        const siblings = node.parent ? node.parent.children : [node];
        const vals = siblings.map(s => Math.abs(s.value));
        const maxV = Math.max(...vals), minV = Math.min(...vals), range = maxV - minV || 1;
        const bw = Math.max(4, ((Math.abs(node.value) - minV) / range) * config.barWidth);
        const barFill = document.createElementNS("http://www.w3.org/2000/svg", "rect");
        barFill.setAttribute("class", "node-bar"); barFill.setAttribute("x", 14); barFill.setAttribute("y", 58); barFill.setAttribute("width", bw); barFill.setAttribute("height", config.barHeight); barFill.setAttribute("fill", node.color);
        ng.appendChild(barFill);
        if (hasChildren) {{
            const btnG = document.createElementNS("http://www.w3.org/2000/svg", "g");
            btnG.setAttribute("transform", `translate(${{config.nodeWidth - 26}}, ${{config.nodeHeight/2 - 10}})`);
            const btnBg = document.createElementNS("http://www.w3.org/2000/svg", "rect");
            btnBg.setAttribute("width", 20); btnBg.setAttribute("height", 20); btnBg.setAttribute("rx", 4); btnBg.setAttribute("fill", node.expanded ? "#F3F4F6" : "#1B5E3F");
            btnG.appendChild(btnBg);
            const btnTxt = document.createElementNS("http://www.w3.org/2000/svg", "text");
            btnTxt.setAttribute("x", 10); btnTxt.setAttribute("y", 14); btnTxt.setAttribute("text-anchor", "middle"); btnTxt.setAttribute("font-size", "14px"); btnTxt.setAttribute("font-weight", "600");
            btnTxt.setAttribute("fill", node.expanded ? "#6B7280" : "#FFF"); btnTxt.setAttribute("pointer-events", "none"); btnTxt.textContent = node.expanded ? "−" : "+";
            btnG.appendChild(btnTxt);
            ng.appendChild(btnG);
        }}
        g.appendChild(ng);
    }});
}}
root = processNode(data, 0);
render();
}})();</script></body></html>'''

# =============================================================================
# SESSION STATE
# =============================================================================

for key, default in [('selected_metric', 'NCC'), ('selected_dimensions', DATA_CONFIG["dimensions"].copy()),
                      ('data_scenario', 'Actuals'), ('selected_node', None), ('ai_insights', None)]:
    if key not in st.session_state:
        st.session_state[key] = default

# =============================================================================
# MAIN APP
# =============================================================================

def main():
    df = load_data(DATA_CONFIG["table"])

    # Sidebar
    with st.sidebar:
        st.markdown("### Settings")
        scenarios = df['DATA_SCENARIO'].unique().tolist()
        st.session_state.data_scenario = st.selectbox("Data Scenario", scenarios,
            index=scenarios.index(st.session_state.data_scenario) if st.session_state.data_scenario in scenarios else 0)
        st.markdown("---")
        st.session_state.selected_metric = st.selectbox("Metric", list(DATA_CONFIG["metrics"].keys()),
            format_func=lambda x: DATA_CONFIG["metrics"][x]["label"],
            index=list(DATA_CONFIG["metrics"].keys()).index(st.session_state.selected_metric))
        st.markdown("---")
        st.markdown("### Hierarchy")
        dims = st.multiselect("Select drill-down levels", DATA_CONFIG["dimensions"],
            default=st.session_state.selected_dimensions,
            format_func=lambda x: DATA_CONFIG["dimension_labels"].get(x, x))
        if dims:
            st.session_state.selected_dimensions = dims
        st.markdown("---")
        st.markdown("### Time Filters")
        years = sorted(df['YEAR'].unique())
        selected_years = st.multiselect("Year(s)", years, default=years)
        months = sorted(df['MONTH_OF_YEAR'].unique())
        selected_months = st.multiselect("Month(s)", months, default=months)
        st.markdown("---")
        st.markdown("""<div class="info-box"><h4>How to Use</h4><p>Click <strong>+</strong> to expand</p><p>Click <strong>−</strong> to collapse</p><p>Use <strong>AI Insights</strong> for analysis</p></div>""", unsafe_allow_html=True)
        st.markdown("""<div class="info-box"><h4>Legend</h4>
            <div class="legend-item"><div class="legend-dot" style="background:#1B5E3F"></div><span>High</span></div>
            <div class="legend-item"><div class="legend-dot" style="background:#2D8B5E"></div><span>Good</span></div>
            <div class="legend-item"><div class="legend-dot" style="background:#F59E0B"></div><span>Warning</span></div>
            <div class="legend-item"><div class="legend-dot" style="background:#DC2626"></div><span>Low</span></div></div>""", unsafe_allow_html=True)

    # Filter data
    filtered_df = df[(df['DATA_SCENARIO'] == st.session_state.data_scenario) &
                     (df['YEAR'].isin(selected_years)) & (df['MONTH_OF_YEAR'].isin(selected_months))]

    # Header
    st.title("NCC Decomposition Tree")
    st.markdown(f'<p class="subtitle">Analyzing {DATA_CONFIG["metrics"][st.session_state.selected_metric]["label"]} | Scenario: {st.session_state.data_scenario}</p>', unsafe_allow_html=True)
    st.markdown('<span class="category-badge">Financial</span>', unsafe_allow_html=True)

    # Metrics
    total_ncc, total_py = filtered_df['NCC'].sum(), filtered_df['NCC_PY'].sum()
    yoy = ((total_ncc - total_py) / total_py * 100) if total_py > 0 else 0
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total NCC", f"${total_ncc/1e6:.1f}M")
    c2.metric("Prior Year", f"${total_py/1e6:.1f}M")
    c3.metric("YoY Growth", f"{yoy:+.1f}%")
    c4.metric("Records", f"{len(filtered_df):,}")
    c5.metric("Drill Levels", len(st.session_state.selected_dimensions))
    st.markdown("---")

    # Tree & AI Panel
    if st.session_state.selected_dimensions and len(filtered_df) > 0:
        tree_data = build_hierarchy(filtered_df, st.session_state.selected_dimensions, st.session_state.selected_metric)
        tree_col, ai_col = st.columns([2, 1])

        with tree_col:
            components.html(create_tree_html(tree_data, st.session_state.selected_metric), height=650, scrolling=True)

        with ai_col:
            st.markdown("### AI Insights")
            nodes = flatten_tree(tree_data)
            labels = [n['label'] for n in nodes]
            selected = st.selectbox("Select segment", labels, help="Choose a node for AI analysis")
            node_data = next((n['data'] for n in nodes if n['label'] == selected), None)

            if st.button("Generate AI Insights", type="primary", use_container_width=True):
                with st.spinner("Analyzing..."):
                    st.session_state.ai_insights = generate_ai_summary(node_data, filtered_df, DATA_CONFIG["metrics"][st.session_state.selected_metric]["label"])
                    st.session_state.selected_node = selected

            if st.session_state.ai_insights:
                st.markdown(f"""<div class="ai-insights-panel"><div class="ai-insights-header"><h4>{st.session_state.selected_node.split(': ')[-1]}</h4><span class="ai-badge">Cortex AI</span></div><div class="ai-insights-content">{st.session_state.ai_insights}</div></div>""", unsafe_allow_html=True)

            if node_data:
                st.markdown("---")
                st.metric("Value", f"${node_data['value']/1e6:.2f}M" if node_data['value'] >= 1e6 else f"${node_data['value']:,.0f}")
                st.metric("Records", f"{node_data.get('count', 0):,}")
    else:
        st.warning("Select at least one dimension.")

if __name__ == "__main__":
    main()
