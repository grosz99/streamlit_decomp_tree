"""
NCC Decomposition Tree - Streamlit in Snowflake
Source: MY_WORKFLOW_DB.PUBLIC.NCC_TEST
Drill down: Region → System → Profit Center → Practice Area
"""

import streamlit as st
import streamlit.components.v1 as components

from config import DATA_CONFIG
from styles import CUSTOM_CSS, INFO_BOX_HOW_TO_USE, PERFORMANCE_LEGEND
from data_utils import load_data, build_hierarchy, flatten_tree_for_selector
from tree_visualization import create_tree_visualization
from ai_insights import generate_ai_summary

# Page configuration
st.set_page_config(
    page_title="NCC Decomposition Tree",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom CSS
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Initialize session state
if 'selected_metric' not in st.session_state:
    st.session_state.selected_metric = 'NCC'
if 'selected_dimensions' not in st.session_state:
    st.session_state.selected_dimensions = DATA_CONFIG["dimensions"].copy()
if 'data_scenario' not in st.session_state:
    st.session_state.data_scenario = 'Actuals'
if 'selected_node' not in st.session_state:
    st.session_state.selected_node = None
if 'ai_insights' not in st.session_state:
    st.session_state.ai_insights = None


def render_sidebar(df):
    """Render the sidebar with filters and settings"""
    with st.sidebar:
        st.markdown("### Settings")
        st.markdown(
            f'<p class="source-caption">Source: {DATA_CONFIG["table"]}</p>',
            unsafe_allow_html=True
        )

        # Data scenario selector
        scenarios = df['DATA_SCENARIO'].unique().tolist()
        selected_scenario = st.selectbox(
            "Data Scenario",
            options=scenarios,
            index=scenarios.index(st.session_state.data_scenario)
            if st.session_state.data_scenario in scenarios else 0
        )
        st.session_state.data_scenario = selected_scenario

        st.markdown("---")

        # Metric selector
        selected_metric = st.selectbox(
            "Metric",
            options=list(DATA_CONFIG["metrics"].keys()),
            format_func=lambda x: DATA_CONFIG["metrics"][x]["label"],
            index=list(DATA_CONFIG["metrics"].keys()).index(
                st.session_state.selected_metric
            )
        )
        st.session_state.selected_metric = selected_metric

        st.markdown("---")

        # Hierarchy selector
        st.markdown("### Hierarchy")
        selected_dims = st.multiselect(
            "Select drill-down levels",
            options=DATA_CONFIG["dimensions"],
            default=st.session_state.selected_dimensions,
            format_func=lambda x: DATA_CONFIG["dimension_labels"].get(x, x),
            help="Order determines drill-down hierarchy"
        )
        if selected_dims:
            st.session_state.selected_dimensions = selected_dims

        st.markdown("---")

        # Time filters
        st.markdown("### Time Filters")
        years = sorted(df['YEAR'].unique())
        selected_years = st.multiselect("Year(s)", years, default=years)
        months = sorted(df['MONTH_OF_YEAR'].unique())
        selected_months = st.multiselect("Month(s)", months, default=months)

        st.markdown("---")

        # Info boxes
        st.markdown(INFO_BOX_HOW_TO_USE, unsafe_allow_html=True)
        st.markdown(PERFORMANCE_LEGEND, unsafe_allow_html=True)

    return selected_scenario, selected_metric, selected_years, selected_months


def render_ai_insights_panel(tree_data, filtered_df, selected_metric):
    """Render the AI insights panel"""
    st.markdown("""
    <div class="node-selector-container">
        <h4>AI Insights</h4>
    </div>
    """, unsafe_allow_html=True)

    # Flatten tree for selector
    node_options = flatten_tree_for_selector(tree_data)
    node_labels = [opt['label'] for opt in node_options]

    selected_label = st.selectbox(
        "Select a segment to analyze",
        options=node_labels,
        index=0,
        help="Choose a node from the tree to get AI-powered insights"
    )

    # Find the selected node data
    selected_node_data = next(
        (opt['data'] for opt in node_options if opt['label'] == selected_label),
        None
    )

    # Generate insights button
    if st.button("Generate AI Insights", type="primary", use_container_width=True):
        if selected_node_data:
            with st.spinner("Analyzing with Cortex AI..."):
                st.session_state.ai_insights = generate_ai_summary(
                    selected_node_data,
                    filtered_df,
                    DATA_CONFIG["metrics"][selected_metric]["label"]
                )
                st.session_state.selected_node = selected_label

    # Display AI insights if available
    if st.session_state.ai_insights and st.session_state.selected_node:
        node_name = st.session_state.selected_node.split(': ')[-1]
        st.markdown(f"""
        <div class="ai-insights-panel">
            <div class="ai-insights-header">
                <h4>Analysis: {node_name}</h4>
                <span class="ai-badge">Cortex AI</span>
            </div>
            <div class="ai-insights-content">
                {st.session_state.ai_insights}
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Quick stats for selected node
    if selected_node_data:
        st.markdown("---")
        st.markdown("**Selected Segment Stats**")

        value = selected_node_data['value']
        if value >= 1e6:
            st.metric("Value", f"${value/1e6:.2f}M")
        else:
            st.metric("Value", f"${value:,.0f}")

        st.metric("Records", f"{selected_node_data.get('count', 0):,}")

        if 'children' in selected_node_data and selected_node_data['children']:
            st.metric("Sub-segments", len(selected_node_data['children']))


def main():
    """Main application entry point"""
    # Load data
    df = load_data(DATA_CONFIG["table"])

    # Render sidebar and get selections
    selected_scenario, selected_metric, selected_years, selected_months = render_sidebar(df)

    # Filter data
    filtered_df = df[
        (df['DATA_SCENARIO'] == selected_scenario) &
        (df['YEAR'].isin(selected_years)) &
        (df['MONTH_OF_YEAR'].isin(selected_months))
    ]

    # Main content header
    st.title("NCC Decomposition Tree")
    st.markdown(
        f'<p class="subtitle">Analyzing {DATA_CONFIG["metrics"][selected_metric]["label"]} '
        f'| Scenario: {selected_scenario}</p>',
        unsafe_allow_html=True
    )

    # Category badge
    st.markdown('<span class="category-badge">Financial</span>', unsafe_allow_html=True)

    # Metrics row
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

    # Tree visualization with AI insights
    if st.session_state.selected_dimensions and len(filtered_df) > 0:
        tree_data = build_hierarchy(
            filtered_df,
            st.session_state.selected_dimensions,
            selected_metric
        )

        # Two column layout: tree and AI insights
        tree_col, insights_col = st.columns([2, 1])

        with tree_col:
            components.html(
                create_tree_visualization(tree_data, selected_metric),
                height=650,
                scrolling=True
            )

        with insights_col:
            render_ai_insights_panel(tree_data, filtered_df, selected_metric)
    else:
        st.warning("Please select at least one dimension in the sidebar.")


if __name__ == "__main__":
    main()
