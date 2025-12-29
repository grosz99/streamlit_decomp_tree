"""
Snowflake Cortex AI integration for NCC Decomposition Tree

Available Cortex Models (2025):
- claude-3-5-sonnet: Best for reasoning and multimodal (200K context)
- llama3.3-70b: Strong general purpose
- mistral-large2: Top-tier reasoning, code, multilingual
- snowflake-llama-3.3-70b: Cost-optimized (75% cheaper)
- openai-gpt-4.1: OpenAI's latest on Cortex
- deepseek-r1: DeepSeek's reasoning model
"""

from typing import Dict
import pandas as pd
from snowflake.snowpark.context import get_active_session
from snowflake.cortex import Complete

from config import CORTEX_MODEL


def generate_ai_summary(
    node_data: Dict,
    filtered_df: pd.DataFrame,
    metric_label: str
) -> str:
    """Generate AI summary for selected node using Snowflake Cortex"""

    # Build context about the node
    node_name = node_data.get('name', 'Unknown')
    dimension = node_data.get('dimension', 'Unknown')
    value = node_data.get('value', 0)
    record_count = node_data.get('count', 0)

    # Get comparison data if we have children
    children_summary = ""
    if 'children' in node_data and node_data['children']:
        top_children = node_data['children'][:5]
        children_summary = "Top segments: " + ", ".join([
            f"{c['name']} (${c['value']/1e6:.1f}M)" for c in top_children
        ])

    # Calculate YoY if available
    yoy_info = ""
    if len(filtered_df) > 0:
        total_ncc = filtered_df['NCC'].sum()
        total_py = filtered_df['NCC_PY'].sum()
        if total_py > 0:
            yoy = ((total_ncc - total_py) / total_py) * 100
            yoy_info = f"Year-over-year growth: {yoy:+.1f}%"

    prompt = f"""You are a financial analyst assistant. Provide a brief, insightful summary (3-4 sentences) about this NCC (Net Client Contribution) data segment.

Segment: {node_name}
Dimension: {dimension}
Metric: {metric_label}
Value: ${value/1e6:.2f}M
Records: {record_count:,}
{yoy_info}
{children_summary}

Focus on:
1. Performance assessment (is this strong/weak?)
2. One actionable insight or area to investigate
3. Keep it concise and business-focused"""

    try:
        response = Complete(
            model=CORTEX_MODEL,
            prompt=prompt,
            session=get_active_session()
        )
        return response
    except Exception as e:
        return f"Unable to generate AI insights: {str(e)}"
