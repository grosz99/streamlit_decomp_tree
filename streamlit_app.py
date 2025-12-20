"""
Decomposition Tree - Power BI Style
A drill-down analysis tool with mock data for local testing
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from typing import Dict, List, Tuple

# Page config
st.set_page_config(
    page_title="Decomposition Tree",
    page_icon="🌳",
    layout="wide"
)

# Custom CSS for tree styling
st.markdown("""
<style>
    .tree-container {
        display: flex;
        align-items: flex-start;
        gap: 0;
        overflow-x: auto;
        padding: 20px 0;
    }
    .tree-node {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
        color: white;
        border-radius: 8px;
        padding: 15px 20px;
        min-width: 120px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .tree-node-value {
        font-size: 1.4em;
        font-weight: bold;
    }
    .tree-node-label {
        font-size: 0.85em;
        opacity: 0.9;
    }
    .tree-connector {
        width: 40px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #666;
        font-size: 1.5em;
    }
    .dimension-header {
        background-color: #f0f2f6;
        padding: 8px 15px;
        border-radius: 20px;
        font-weight: 600;
        margin-bottom: 10px;
        display: inline-block;
    }
    .child-node {
        background: #ffffff;
        border: 2px solid #e0e0e0;
        border-radius: 8px;
        padding: 12px 15px;
        margin: 5px;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    .child-node:hover {
        border-color: #1e3a5f;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    }
    .child-node-selected {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
        color: white;
        border-color: #1e3a5f;
    }
    .percentage-bar {
        height: 6px;
        background: #e0e0e0;
        border-radius: 3px;
        margin-top: 8px;
        overflow: hidden;
    }
    .percentage-fill {
        height: 100%;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        border-radius: 3px;
    }
    .stButton > button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# MOCK DATA GENERATION
# ============================================

@st.cache_data
def generate_mock_data() -> pd.DataFrame:
    """Generate realistic mock sales data"""
    np.random.seed(42)

    regions = ['North', 'South', 'East', 'West']
    categories = ['Electronics', 'Clothing', 'Home & Garden', 'Sports', 'Food & Beverage']
    channels = ['Online', 'Retail', 'Wholesale', 'Direct Sales']
    products = {
        'Electronics': ['Laptop', 'Smartphone', 'Tablet', 'Headphones', 'Smart Watch'],
        'Clothing': ['T-Shirt', 'Jeans', 'Jacket', 'Sneakers', 'Dress'],
        'Home & Garden': ['Furniture', 'Kitchenware', 'Garden Tools', 'Decor', 'Lighting'],
        'Sports': ['Running Shoes', 'Yoga Mat', 'Weights', 'Bike', 'Tennis Racket'],
        'Food & Beverage': ['Coffee', 'Snacks', 'Beverages', 'Organic Food', 'Supplements']
    }

    data = []
    for _ in range(1000):
        region = np.random.choice(regions, p=[0.3, 0.25, 0.25, 0.2])
        category = np.random.choice(categories, p=[0.35, 0.2, 0.15, 0.15, 0.15])
        channel = np.random.choice(channels, p=[0.4, 0.3, 0.2, 0.1])
        product = np.random.choice(products[category])

        base_revenue = np.random.uniform(1000, 50000)
        if region == 'North':
            base_revenue *= 1.3
        if category == 'Electronics':
            base_revenue *= 1.5
        if channel == 'Online':
            base_revenue *= 1.2

        revenue = base_revenue
        cost = revenue * np.random.uniform(0.5, 0.75)
        profit = revenue - cost
        units = int(revenue / np.random.uniform(50, 500))

        data.append({
            'Region': region,
            'Category': category,
            'Channel': channel,
            'Product': product,
            'Revenue': round(revenue, 2),
            'Cost': round(cost, 2),
            'Profit': round(profit, 2),
            'Units': units
        })

    return pd.DataFrame(data)

# ============================================
# DATA CONFIGURATION
# ============================================

DATA_CONFIG = {
    "metrics": {
        "Revenue": "Revenue",
        "Profit": "Profit",
        "Cost": "Cost",
        "Units": "Units"
    },
    "dimensions": {
        "Region": "Region",
        "Category": "Category",
        "Channel": "Channel",
        "Product": "Product"
    }
}

# ============================================
# HELPER FUNCTIONS
# ============================================

def filter_data(df: pd.DataFrame, drill_path: List[Tuple[str, str]]) -> pd.DataFrame:
    """Filter dataframe based on drill path"""
    filtered_df = df.copy()
    for dimension, value in drill_path:
        col = DATA_CONFIG["dimensions"][dimension]
        filtered_df = filtered_df[filtered_df[col] == value]
    return filtered_df

def get_available_dimensions(drill_path: List[Tuple[str, str]]) -> List[str]:
    """Get dimensions not yet drilled into"""
    used_dimensions = {dim for dim, _ in drill_path}
    return [dim for dim in DATA_CONFIG["dimensions"].keys() if dim not in used_dimensions]

def calculate_decomposition(df: pd.DataFrame, dimension: str, metric: str) -> pd.DataFrame:
    """Calculate decomposition breakdown for a dimension"""
    col = DATA_CONFIG["dimensions"][dimension]
    metric_col = DATA_CONFIG["metrics"][metric]

    decomp = df.groupby(col)[metric_col].sum().reset_index()
    decomp.columns = ['Value', 'MetricValue']
    total = decomp['MetricValue'].sum()
    decomp['Percentage'] = (decomp['MetricValue'] / total * 100).round(1)
    decomp = decomp.sort_values('MetricValue', ascending=False)

    return decomp

def format_currency(value: float) -> str:
    """Format number as currency"""
    if value >= 1_000_000:
        return f"${value/1_000_000:.1f}M"
    elif value >= 1_000:
        return f"${value/1_000:.1f}K"
    else:
        return f"${value:.0f}"

def format_number(value: float) -> str:
    """Format number with commas"""
    if value >= 1_000_000:
        return f"{value/1_000_000:.1f}M"
    elif value >= 1_000:
        return f"{value/1_000:.1f}K"
    else:
        return f"{value:,.0f}"

# ============================================
# SESSION STATE INITIALIZATION
# ============================================

if 'drill_path' not in st.session_state:
    st.session_state.drill_path = []
if 'selected_metric' not in st.session_state:
    st.session_state.selected_metric = 'Revenue'
if 'expanded_dimension' not in st.session_state:
    st.session_state.expanded_dimension = None

# ============================================
# MAIN APP
# ============================================

def main():
    # Load data
    df = generate_mock_data()

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        selected_metric = st.selectbox(
            "Select Metric",
            options=list(DATA_CONFIG["metrics"].keys()),
            index=list(DATA_CONFIG["metrics"].keys()).index(st.session_state.selected_metric)
        )
        st.session_state.selected_metric = selected_metric

        st.markdown("---")
        st.markdown("### 📖 How to Use")
        st.markdown("""
        1. Click a **dimension** to expand it
        2. Click a **value** to drill down
        3. Use the **tree path** to navigate back
        """)

        st.markdown("---")
        if st.button("🔄 Reset Tree", use_container_width=True):
            st.session_state.drill_path = []
            st.session_state.expanded_dimension = None
            st.rerun()

    # Header
    st.title("🌳 Decomposition Tree")

    # Filter data based on drill path
    filtered_df = filter_data(df, st.session_state.drill_path)
    metric_col = DATA_CONFIG["metrics"][selected_metric]
    total_value = filtered_df[metric_col].sum()
    available_dims = get_available_dimensions(st.session_state.drill_path)

    # ============================================
    # TREE VISUALIZATION
    # ============================================

    # Build the tree path display
    st.markdown("---")

    # Create columns for the tree structure
    tree_levels = len(st.session_state.drill_path) + 1  # +1 for root

    # Display tree horizontally
    cols = st.columns([1] * min(tree_levels * 2 - 1, 9))  # Limit columns

    col_idx = 0

    # Root node (Total metric)
    with cols[col_idx]:
        st.markdown(f"""
        <div class="tree-node">
            <div class="tree-node-label">{selected_metric}</div>
            <div class="tree-node-value">{format_currency(total_value) if selected_metric != 'Units' else format_number(total_value)}</div>
        </div>
        """, unsafe_allow_html=True)

        # If at root level, show reset is already at root
        if len(st.session_state.drill_path) == 0:
            st.caption("📍 Root Level")

    col_idx += 1

    # Show drilled path
    for i, (dim, val) in enumerate(st.session_state.drill_path):
        if col_idx < len(cols):
            # Connector
            with cols[col_idx]:
                st.markdown("<div style='text-align:center; padding-top:20px; color:#666;'>→</div>", unsafe_allow_html=True)
            col_idx += 1

        if col_idx < len(cols):
            # Node
            with cols[col_idx]:
                # Calculate value at this level
                path_up_to = st.session_state.drill_path[:i+1]
                level_df = filter_data(df, path_up_to)
                level_value = level_df[metric_col].sum()

                st.markdown(f"""
                <div class="tree-node">
                    <div class="tree-node-label">{dim}</div>
                    <div class="tree-node-value">{val}</div>
                    <div class="tree-node-label" style="margin-top:5px;">{format_currency(level_value) if selected_metric != 'Units' else format_number(level_value)}</div>
                </div>
                """, unsafe_allow_html=True)

                # Button to go back to this level
                if st.button("↩️ Back here", key=f"back_{i}", use_container_width=True):
                    st.session_state.drill_path = st.session_state.drill_path[:i+1]
                    st.session_state.expanded_dimension = None
                    st.rerun()

            col_idx += 1

    st.markdown("---")

    # ============================================
    # DIMENSION SELECTION (Tree branches)
    # ============================================

    if len(available_dims) > 0:
        st.markdown("### 📊 Choose a dimension to explore")

        # Show dimensions as expandable cards
        dim_cols = st.columns(len(available_dims))

        for i, dimension in enumerate(available_dims):
            with dim_cols[i]:
                decomp_df = calculate_decomposition(filtered_df, dimension, selected_metric)
                top_value = decomp_df.iloc[0]['Value'] if len(decomp_df) > 0 else "N/A"
                top_pct = decomp_df.iloc[0]['Percentage'] if len(decomp_df) > 0 else 0

                # Dimension card as expander
                is_expanded = st.session_state.expanded_dimension == dimension

                # Create a button that looks like a card
                button_label = f"📁 {dimension}\nTop: {top_value} ({top_pct}%)"
                if st.button(button_label, key=f"dim_{dimension}", use_container_width=True,
                           type="primary" if is_expanded else "secondary"):
                    if is_expanded:
                        st.session_state.expanded_dimension = None
                    else:
                        st.session_state.expanded_dimension = dimension
                    st.rerun()

        st.markdown("---")

        # Show expanded dimension details
        if st.session_state.expanded_dimension:
            dimension = st.session_state.expanded_dimension
            decomp_df = calculate_decomposition(filtered_df, dimension, selected_metric)

            st.markdown(f"### 🔍 {dimension} Breakdown")
            st.caption(f"Click any value below to drill into it")

            # Create a horizontal bar chart
            fig = go.Figure()

            fig.add_trace(go.Bar(
                y=decomp_df['Value'],
                x=decomp_df['MetricValue'],
                orientation='h',
                marker=dict(
                    color=decomp_df['MetricValue'],
                    colorscale='Blues',
                    showscale=False
                ),
                text=[f"{format_currency(v) if selected_metric != 'Units' else format_number(v)} ({p}%)"
                      for v, p in zip(decomp_df['MetricValue'], decomp_df['Percentage'])],
                textposition='auto',
                hovertemplate=f"<b>%{{y}}</b><br>{selected_metric}: %{{x:,.0f}}<extra></extra>"
            ))

            fig.update_layout(
                xaxis_title=selected_metric,
                yaxis_title="",
                height=max(250, len(decomp_df) * 45),
                showlegend=False,
                yaxis=dict(categoryorder='total ascending'),
                margin=dict(l=20, r=20, t=10, b=40)
            )

            st.plotly_chart(fig, use_container_width=True)

            # Drill buttons as clickable cards
            st.markdown("**🖱️ Click to drill into:**")

            # Arrange buttons in rows
            num_cols = min(len(decomp_df), 4)
            rows = (len(decomp_df) + num_cols - 1) // num_cols

            for row_idx in range(rows):
                button_cols = st.columns(num_cols)
                for col_idx in range(num_cols):
                    item_idx = row_idx * num_cols + col_idx
                    if item_idx < len(decomp_df):
                        row = decomp_df.iloc[item_idx]
                        with button_cols[col_idx]:
                            value_display = format_currency(row['MetricValue']) if selected_metric != 'Units' else format_number(row['MetricValue'])
                            btn_label = f"{row['Value']}\n{value_display} ({row['Percentage']}%)"

                            if st.button(btn_label, key=f"drill_{dimension}_{row['Value']}", use_container_width=True):
                                st.session_state.drill_path.append((dimension, row['Value']))
                                st.session_state.expanded_dimension = None
                                st.rerun()

    else:
        # Deepest level reached
        st.success("🎯 You've reached the deepest drill level!")

        st.markdown("### 📋 Detailed Data at This Level")
        st.dataframe(
            filtered_df.style.format({
                'Revenue': '${:,.2f}',
                'Cost': '${:,.2f}',
                'Profit': '${:,.2f}',
                'Units': '{:,.0f}'
            }),
            use_container_width=True,
            height=400
        )

    # Footer with summary
    st.markdown("---")
    summary_cols = st.columns(4)
    with summary_cols[0]:
        st.metric("Current Level", len(st.session_state.drill_path))
    with summary_cols[1]:
        st.metric("Records", f"{len(filtered_df):,}")
    with summary_cols[2]:
        st.metric("Dimensions Left", len(available_dims))
    with summary_cols[3]:
        pct_of_total = (total_value / df[metric_col].sum() * 100)
        st.metric("% of Total", f"{pct_of_total:.1f}%")

if __name__ == "__main__":
    main()
