"""
AI Insights generation using Snowflake Cortex
"""

from typing import Dict, List
import pandas as pd
from snowflake.snowpark.context import get_active_session
from config import CORTEX_MODEL


def generate_ai_summary(node_data: Dict, filtered_df: pd.DataFrame, metric_label: str) -> str:
    """Generate AI summary using Snowflake Cortex via SQL"""
    node_name = node_data.get('name', 'Unknown')
    dimension = node_data.get('dimension', 'Unknown')
    value = node_data.get('value', 0)
    record_count = node_data.get('count', 0)

    children_summary = ""
    if node_data.get('children'):
        top_children = node_data['children'][:5]
        children_summary = "Top segments: " + ", ".join(
            [f"{c['name']} (${c['value']/1e6:.1f}M)" for c in top_children]
        )

    yoy_info = ""
    if len(filtered_df) > 0:
        total_ncc = filtered_df['NCC'].sum()
        total_py = filtered_df['NCC_PY'].sum()
        if total_py > 0:
            yoy_info = f"Year-over-year growth: {((total_ncc - total_py) / total_py) * 100:+.1f}%"

    prompt = f"""You are a financial analyst. Provide a brief summary (3-4 sentences) about this NCC segment.
Segment: {node_name} | Dimension: {dimension} | Value: ${value/1e6:.2f}M | Records: {record_count:,}
{yoy_info} {children_summary}
Focus on: 1) Performance assessment 2) One actionable insight"""

    try:
        session = get_active_session()
        prompt_escaped = prompt.replace("'", "''")
        result = session.sql(
            f"SELECT SNOWFLAKE.CORTEX.COMPLETE('{CORTEX_MODEL}', '{prompt_escaped}') as response"
        ).collect()
        return result[0]['RESPONSE'] if result else "No response generated"
    except Exception as e:
        return f"Unable to generate insights: {str(e)}"


def generate_child_insights(node_data: Dict, child_nodes: List[Dict], metric_label: str) -> str:
    """Generate AI insights specifically about child nodes (1-2 levels below)"""
    node_name = node_data.get('name', 'Unknown')
    dimension = node_data.get('dimension', 'Unknown')
    value = node_data.get('value', 0)

    if not child_nodes:
        return "No child segments available for analysis."

    # Build child summary
    level_1_nodes = [c for c in child_nodes if c['depth'] == 1]
    level_2_nodes = [c for c in child_nodes if c['depth'] == 2]

    level_1_summary = ""
    if level_1_nodes:
        top_l1 = sorted(level_1_nodes, key=lambda x: x['value'], reverse=True)[:5]
        level_1_summary = "Direct children: " + ", ".join(
            [f"{c['name']} (${c['value']/1e6:.2f}M, {c['count']:,} records)" for c in top_l1]
        )

    level_2_summary = ""
    if level_2_nodes:
        top_l2 = sorted(level_2_nodes, key=lambda x: x['value'], reverse=True)[:5]
        level_2_summary = "Grandchildren (top 5): " + ", ".join(
            [f"{c['name']} (${c['value']/1e6:.2f}M)" for c in top_l2]
        )

    # Calculate concentration
    total_child_value = sum(c['value'] for c in level_1_nodes) if level_1_nodes else 0
    concentration = ""
    if level_1_nodes and total_child_value > 0:
        top_child_pct = (level_1_nodes[0]['value'] / total_child_value * 100) if level_1_nodes else 0
        concentration = f"Top child concentration: {top_child_pct:.1f}% of segment total"

    prompt = f"""You are a financial analyst. Analyze the breakdown of this segment into its child components.

Parent Segment: {node_name} ({dimension}) - Total: ${value/1e6:.2f}M
{level_1_summary}
{level_2_summary}
{concentration}

Provide insights (4-5 sentences) covering:
1) Which child segments are driving performance
2) Any concentration risks or opportunities
3) Patterns across the hierarchy levels
4) One specific recommendation for this segment"""

    try:
        session = get_active_session()
        prompt_escaped = prompt.replace("'", "''")
        result = session.sql(
            f"SELECT SNOWFLAKE.CORTEX.COMPLETE('{CORTEX_MODEL}', '{prompt_escaped}') as response"
        ).collect()
        return result[0]['RESPONSE'] if result else "No response generated"
    except Exception as e:
        return f"Unable to generate child insights: {str(e)}"


def format_child_insights_html(node_data: Dict, child_nodes: List[Dict]) -> str:
    """Format child nodes as HTML for display below AI insights"""
    if not child_nodes:
        return ""

    level_1_nodes = sorted(
        [c for c in child_nodes if c['depth'] == 1],
        key=lambda x: x['value'],
        reverse=True
    )[:5]

    html = '<div style="margin-top: 1rem;">'
    html += '<h5 style="color: #1B5E3F; font-size: 0.85rem; margin-bottom: 0.5rem;">Top Child Segments</h5>'

    for child in level_1_nodes:
        pct = (child['value'] / node_data['value'] * 100) if node_data['value'] > 0 else 0
        html += f'''<div class="child-insight">
            <div class="child-insight-title">{child['name']}</div>
            <div class="child-insight-value">${child['value']/1e6:.2f}M ({pct:.1f}% of parent)</div>
        </div>'''

    html += '</div>'
    return html
