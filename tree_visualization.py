"""
Tree visualization component for NCC Decomposition Tree
Larger nodes and click-to-analyze functionality
"""

import json
from typing import Dict


def create_tree_html(tree_data: Dict, metric: str) -> str:
    """Create interactive SVG tree visualization with larger nodes and double-click analysis"""
    tree_json = json.dumps(tree_data)
    fmt = "percent" if metric == "YoY_Growth" else "currency"

    return f'''<!DOCTYPE html>
<html>
<head>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #FFF; color: #1F2937; }}
.tree-container {{ padding: 24px; background: #FFF; border-radius: 12px; border: 1px solid #E5E7EB; margin: 8px; }}
svg {{ overflow: visible; }}
.node {{ cursor: pointer; }}
.node-rect {{ fill: #FFF; stroke: #E5E7EB; stroke-width: 1px; rx: 10px; transition: all 0.2s; }}
.node:hover .node-rect {{ stroke: #1B5E3F; stroke-width: 2px; box-shadow: 0 4px 12px rgba(27, 94, 63, 0.15); }}
.node.selected .node-rect {{ stroke: #1B5E3F; stroke-width: 3px; fill: #F0FDF4; }}
.node-text {{ font-size: 15px; font-weight: 600; fill: #1F2937; pointer-events: none; }}
.node-value {{ font-size: 14px; font-weight: 700; fill: #1B5E3F; pointer-events: none; }}
.node-dimension {{ font-size: 11px; fill: #9CA3AF; pointer-events: none; text-transform: uppercase; letter-spacing: 0.5px; }}
.node-bar-bg {{ fill: #F3F4F6; rx: 4px; }}
.node-bar {{ rx: 4px; transition: width 0.3s; }}
.link {{ fill: none; stroke: #D1D5DB; stroke-width: 2px; }}
.tooltip {{ position: fixed; background: #1F2937; color: #FFF; padding: 14px 18px; border-radius: 10px; font-size: 14px; pointer-events: none; z-index: 1000; display: none; max-width: 280px; box-shadow: 0 4px 20px rgba(0,0,0,0.25); }}
.tooltip .label {{ color: #9CA3AF; font-size: 11px; text-transform: uppercase; margin-top: 10px; display: block; letter-spacing: 0.5px; }}
.tooltip .value {{ color: #10B981; font-weight: 600; font-size: 15px; }}
.tooltip .hint {{ color: #60A5FA; font-size: 11px; margin-top: 12px; padding-top: 10px; border-top: 1px solid #374151; }}
.analyze-indicator {{ position: fixed; background: #1B5E3F; color: #FFF; padding: 10px 16px; border-radius: 8px; font-size: 13px; font-weight: 500; z-index: 1001; display: none; animation: fadeIn 0.2s; }}
@keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(-10px); }} to {{ opacity: 1; transform: translateY(0); }} }}
</style>
</head>
<body>
<div class="tree-container">
    <svg id="tree-svg"></svg>
</div>
<div id="tooltip" class="tooltip"></div>
<div id="analyze-indicator" class="analyze-indicator">Analyzing node...</div>
<script>
(function() {{
const data = {tree_json};
const formatType = "{fmt}";

// Larger node configuration for better readability
const config = {{
    nodeWidth: 220,
    nodeHeight: 88,
    levelGap: 280,
    siblingGap: 16,
    barWidth: 120,
    barHeight: 8,
    margin: {{ top: 50, right: 200, bottom: 50, left: 80 }}
}};

let nodeId = 0;
let root = null;
let selectedNodeId = null;

function formatValue(val) {{
    if (formatType === "percent") return (val >= 0 ? "+" : "") + val.toFixed(1) + "%";
    if (val >= 1e9) return "$" + (val/1e9).toFixed(1) + "B";
    if (val >= 1e6) return "$" + (val/1e6).toFixed(1) + "M";
    if (val >= 1e3) return "$" + (val/1e3).toFixed(1) + "K";
    return "$" + val.toLocaleString();
}}

function processNode(node, depth) {{
    node.id = ++nodeId;
    node.depth = depth;
    node.expanded = depth < 1;
    if (node.children) {{
        node.children.forEach(c => {{
            c.parent = node;
            processNode(c, depth + 1);
        }});
    }}
    return node;
}}

function calculateLayout(node) {{
    let yOffset = 0;
    function layoutNode(n, x) {{
        n.x = x;
        if (n.expanded && n.children && n.children.length > 0) {{
            n.children.forEach(c => layoutNode(c, x + config.levelGap));
            n.y = (n.children[0].y + n.children[n.children.length - 1].y) / 2;
        }} else {{
            n.y = yOffset;
            yOffset += config.nodeHeight + config.siblingGap;
        }}
    }}
    layoutNode(node, config.margin.left);
    return yOffset;
}}

function getVisibleNodes(node, nodes = []) {{
    nodes.push(node);
    if (node.expanded && node.children) {{
        node.children.forEach(c => getVisibleNodes(c, nodes));
    }}
    return nodes;
}}

function getVisibleLinks(node, links = []) {{
    if (node.expanded && node.children) {{
        node.children.forEach(c => {{
            links.push({{ source: node, target: c }});
            getVisibleLinks(c, links);
        }});
    }}
    return links;
}}

function linkPath(s, t) {{
    const midX = (s.x + config.nodeWidth/2 + t.x) / 2;
    return `M${{s.x + config.nodeWidth}},${{s.y + config.nodeHeight/2}} C${{midX}},${{s.y + config.nodeHeight/2}} ${{midX}},${{t.y + config.nodeHeight/2}} ${{t.x}},${{t.y + config.nodeHeight/2}}`;
}}

// Send selected node to Streamlit
function selectNodeForAnalysis(node) {{
    selectedNodeId = node.id;
    const indicator = document.getElementById("analyze-indicator");
    indicator.style.display = "block";
    indicator.style.left = "50%";
    indicator.style.top = "20px";
    indicator.style.transform = "translateX(-50%)";

    // Post message to parent Streamlit
    const nodeInfo = {{
        name: node.name,
        dimension: node.dimension,
        value: node.value,
        count: node.count,
        hasChildren: !!(node.children && node.children.length > 0),
        childCount: node.children ? node.children.length : 0
    }};

    window.parent.postMessage({{
        type: 'streamlit:setComponentValue',
        value: JSON.stringify(nodeInfo)
    }}, '*');

    setTimeout(() => {{
        indicator.style.display = "none";
    }}, 1500);

    render();
}}

function render() {{
    const height = calculateLayout(root);
    const svg = document.getElementById("tree-svg");
    const totalWidth = Math.max(1400, config.margin.left + config.margin.right + (4 * config.levelGap));
    svg.setAttribute("width", totalWidth);
    svg.setAttribute("height", Math.max(600, height + config.margin.top + config.margin.bottom));
    svg.innerHTML = "";

    const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
    g.setAttribute("transform", `translate(0,${{config.margin.top}})`);
    svg.appendChild(g);

    // Draw links
    getVisibleLinks(root).forEach(link => {{
        const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
        path.setAttribute("class", "link");
        path.setAttribute("d", linkPath(link.source, link.target));
        g.appendChild(path);
    }});

    // Draw nodes
    getVisibleNodes(root).forEach(node => {{
        const ng = document.createElementNS("http://www.w3.org/2000/svg", "g");
        ng.setAttribute("class", "node" + (node.id === selectedNodeId ? " selected" : ""));
        ng.setAttribute("transform", `translate(${{node.x}},${{node.y}})`);

        const hasChildren = node.children && node.children.length > 0;

        // Single click: expand/collapse
        ng.onclick = e => {{
            e.stopPropagation();
            if (hasChildren) {{
                node.expanded = !node.expanded;
                render();
            }}
        }};

        // Double click: select for AI analysis
        ng.ondblclick = e => {{
            e.stopPropagation();
            selectNodeForAnalysis(node);
        }};

        ng.style.cursor = "pointer";

        // Tooltip
        ng.onmouseenter = e => {{
            const tt = document.getElementById("tooltip");
            let tooltipHtml = `<strong style="font-size: 15px;">${{node.name}}</strong>`;
            tooltipHtml += `<span class="label">${{node.dimension}}</span>`;
            tooltipHtml += `<span class="label">Value</span><span class="value">${{formatValue(node.value)}}</span>`;
            tooltipHtml += `<span class="label">Records</span>${{node.count ? node.count.toLocaleString() : 'N/A'}}`;
            if (hasChildren) {{
                tooltipHtml += `<span class="label">Children</span>${{node.children.length}} segments`;
            }}
            tooltipHtml += `<div class="hint">Double-click to analyze this node</div>`;
            tt.innerHTML = tooltipHtml;
            tt.style.display = "block";
            tt.style.left = (e.clientX + 15) + "px";
            tt.style.top = (e.clientY - 10) + "px";
        }};

        ng.onmouseleave = () => {{
            document.getElementById("tooltip").style.display = "none";
        }};

        ng.onmousemove = e => {{
            const tt = document.getElementById("tooltip");
            tt.style.left = (e.clientX + 15) + "px";
            tt.style.top = (e.clientY - 10) + "px";
        }};

        // Node background
        const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
        rect.setAttribute("class", "node-rect");
        rect.setAttribute("width", config.nodeWidth);
        rect.setAttribute("height", config.nodeHeight);
        rect.setAttribute("rx", 10);
        ng.appendChild(rect);

        // Color indicator bar
        const ind = document.createElementNS("http://www.w3.org/2000/svg", "rect");
        ind.setAttribute("x", 0);
        ind.setAttribute("y", 0);
        ind.setAttribute("width", 5);
        ind.setAttribute("height", config.nodeHeight);
        ind.setAttribute("fill", node.color);
        ind.setAttribute("rx", "10 0 0 10");
        ng.appendChild(ind);

        // Dimension label
        const dimText = document.createElementNS("http://www.w3.org/2000/svg", "text");
        dimText.setAttribute("class", "node-dimension");
        dimText.setAttribute("x", 16);
        dimText.setAttribute("y", 22);
        dimText.textContent = node.dimension;
        ng.appendChild(dimText);

        // Node name
        const nameText = document.createElementNS("http://www.w3.org/2000/svg", "text");
        nameText.setAttribute("class", "node-text");
        nameText.setAttribute("x", 16);
        nameText.setAttribute("y", 44);
        nameText.textContent = node.name.length > 20 ? node.name.substring(0, 18) + "..." : node.name;
        ng.appendChild(nameText);

        // Value
        const valueText = document.createElementNS("http://www.w3.org/2000/svg", "text");
        valueText.setAttribute("class", "node-value");
        valueText.setAttribute("x", 16);
        valueText.setAttribute("y", 64);
        valueText.textContent = formatValue(node.value);
        ng.appendChild(valueText);

        // Progress bar background
        const barBg = document.createElementNS("http://www.w3.org/2000/svg", "rect");
        barBg.setAttribute("class", "node-bar-bg");
        barBg.setAttribute("x", 16);
        barBg.setAttribute("y", 74);
        barBg.setAttribute("width", config.barWidth);
        barBg.setAttribute("height", config.barHeight);
        ng.appendChild(barBg);

        // Progress bar fill
        const siblings = node.parent ? node.parent.children : [node];
        const vals = siblings.map(s => Math.abs(s.value));
        const maxV = Math.max(...vals);
        const minV = Math.min(...vals);
        const range = maxV - minV || 1;
        const bw = Math.max(6, ((Math.abs(node.value) - minV) / range) * config.barWidth);

        const barFill = document.createElementNS("http://www.w3.org/2000/svg", "rect");
        barFill.setAttribute("class", "node-bar");
        barFill.setAttribute("x", 16);
        barFill.setAttribute("y", 74);
        barFill.setAttribute("width", bw);
        barFill.setAttribute("height", config.barHeight);
        barFill.setAttribute("fill", node.color);
        ng.appendChild(barFill);

        // Expand/collapse button
        if (hasChildren) {{
            const btnG = document.createElementNS("http://www.w3.org/2000/svg", "g");
            btnG.setAttribute("transform", `translate(${{config.nodeWidth - 32}}, ${{config.nodeHeight/2 - 12}})`);

            const btnBg = document.createElementNS("http://www.w3.org/2000/svg", "rect");
            btnBg.setAttribute("width", 24);
            btnBg.setAttribute("height", 24);
            btnBg.setAttribute("rx", 6);
            btnBg.setAttribute("fill", node.expanded ? "#F3F4F6" : "#1B5E3F");
            btnG.appendChild(btnBg);

            const btnTxt = document.createElementNS("http://www.w3.org/2000/svg", "text");
            btnTxt.setAttribute("x", 12);
            btnTxt.setAttribute("y", 17);
            btnTxt.setAttribute("text-anchor", "middle");
            btnTxt.setAttribute("font-size", "16px");
            btnTxt.setAttribute("font-weight", "700");
            btnTxt.setAttribute("fill", node.expanded ? "#6B7280" : "#FFF");
            btnTxt.setAttribute("pointer-events", "none");
            btnTxt.textContent = node.expanded ? "−" : "+";
            btnG.appendChild(btnTxt);

            ng.appendChild(btnG);
        }}

        g.appendChild(ng);
    }});
}}

root = processNode(data, 0);
render();
}})();
</script>
</body>
</html>'''
