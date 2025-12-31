"""
Data loading and processing utilities for NCC Decomposition Tree
"""

import streamlit as st
import pandas as pd
from typing import Dict, List
from snowflake.snowpark.context import get_active_session


@st.cache_data(ttl=300)
def load_data(table_name: str) -> pd.DataFrame:
    """Load data from Snowflake table with caching"""
    session = get_active_session()
    return session.table(table_name).to_pandas()


def calculate_metric(df: pd.DataFrame, metric: str) -> float:
    """Calculate the specified metric for a dataframe"""
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
    """Determine node color based on value and metric type"""
    normalized = 0.5 if max_val == min_val else (value - min_val) / (max_val - min_val)
    if metric == "YoY_Growth":
        if value >= 10:
            return "#1B5E3F"
        elif value >= 0:
            return "#2D8B5E"
        elif value >= -10:
            return "#F59E0B"
        else:
            return "#DC2626"
    if normalized >= 0.7:
        return "#1B5E3F"
    elif normalized >= 0.5:
        return "#2D8B5E"
    elif normalized >= 0.3:
        return "#F59E0B"
    else:
        return "#DC2626"


def build_hierarchy(df: pd.DataFrame, dimensions: List[str], metric: str) -> Dict:
    """Build hierarchical tree structure from data"""
    def build_level(data: pd.DataFrame, dims_remaining: List[str]) -> List[Dict]:
        if not dims_remaining or len(data) == 0:
            return []
        current_dim, next_dims = dims_remaining[0], dims_remaining[1:]
        groups = list(data.groupby(current_dim))
        values = [calculate_metric(group, metric) for _, group in groups]
        min_val, max_val = (min(values), max(values)) if values else (0, 1)
        children = []
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
        return sorted(children, key=lambda x: x["value"], reverse=True)

    root_value = calculate_metric(df, metric)
    return {
        "name": "Total NCC",
        "dimension": "Total",
        "value": root_value,
        "color": "#1B5E3F",
        "count": len(df),
        "children": build_level(df, dimensions)
    }


def flatten_tree(node: Dict, path: str = "") -> List[Dict]:
    """Flatten tree structure into a list for dropdowns"""
    current_path = f"{path} > {node['name']}" if path else node['name']
    results = [{
        'label': f"{node['dimension']}: {node['name']}",
        'path': current_path,
        'data': node
    }]
    for child in node.get('children', []):
        results.extend(flatten_tree(child, current_path))
    return results


def get_child_nodes(node: Dict, max_depth: int = 2) -> List[Dict]:
    """Get child nodes up to specified depth for AI analysis"""
    children = []

    def collect_children(n: Dict, depth: int):
        if depth > max_depth or not n.get('children'):
            return
        for child in n['children']:
            children.append({
                'name': child['name'],
                'dimension': child['dimension'],
                'value': child['value'],
                'count': child.get('count', 0),
                'depth': depth
            })
            collect_children(child, depth + 1)

    collect_children(node, 1)
    return children
