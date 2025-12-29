"""
Data loading and calculation utilities for NCC Decomposition Tree
"""

import streamlit as st
import pandas as pd
from typing import Dict, List
from snowflake.snowpark.context import get_active_session


@st.cache_data(ttl=300)
def load_data(table_name: str) -> pd.DataFrame:
    """Load NCC data from Snowflake table"""
    session = get_active_session()
    df = session.table(table_name).to_pandas()
    return df


def calculate_metric(df: pd.DataFrame, metric: str) -> float:
    """Calculate the specified metric for a dataframe"""
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
    """Get color based on value - using Surge/Beacon green palette"""
    if max_val == min_val:
        normalized = 0.5
    else:
        normalized = (value - min_val) / (max_val - min_val)

    if metric == "YoY_Growth":
        if value >= 10:
            return "#1B5E3F"  # Primary green (high)
        elif value >= 0:
            return "#2D8B5E"  # Medium green
        elif value >= -10:
            return "#F59E0B"  # Amber (warning)
        else:
            return "#DC2626"  # Red (low)

    if normalized >= 0.7:
        return "#1B5E3F"
    elif normalized >= 0.5:
        return "#2D8B5E"
    elif normalized >= 0.3:
        return "#F59E0B"
    else:
        return "#DC2626"


def build_hierarchy(df: pd.DataFrame, dimensions: List[str], metric: str) -> Dict:
    """Build hierarchical tree structure from dataframe"""

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
        "color": "#1B5E3F",
        "count": len(df),
        "children": build_level(df, dimensions)
    }


def flatten_tree_for_selector(node: Dict, path: str = "") -> List[Dict]:
    """Flatten tree structure into a list for the selector dropdown"""
    results = []
    current_path = f"{path} > {node['name']}" if path else node['name']

    results.append({
        'label': f"{node['dimension']}: {node['name']}",
        'path': current_path,
        'data': node
    })

    if 'children' in node and node['children']:
        for child in node['children']:
            results.extend(flatten_tree_for_selector(child, current_path))

    return results
