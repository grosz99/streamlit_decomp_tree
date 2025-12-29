"""
Tree visualization component for NCC Decomposition Tree
Pure JavaScript/SVG implementation with Surge/Beacon styling
"""

import json
from typing import Dict


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

.node-bar-bg {{ fill: #F3F4F6; rx: 3px; }}
.node-bar {{ rx: 3px; transition: width 0.3s; }}
.link {{ fill: none; stroke: #D1D5DB; stroke-width: 1.5px; }}

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

.tooltip strong {{ color: #FFFFFF; font-weight: 600; }}
.tooltip .label {{
    color: #9CA3AF;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-top: 8px;
    display: block;
}}
.tooltip .value {{ color: #10B981; font-weight: 600; }}

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
                n.children.forEach(child => layoutNode(child, x + config.levelGap));
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

            // Tooltip events
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

            // Color indicator
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
