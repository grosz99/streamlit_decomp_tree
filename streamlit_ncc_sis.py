"""
NCC Decomposition Tree - Streamlit in Snowflake
Source: MY_WORKFLOW_DB.PUBLIC.NCC_TEST
Drill down: Region → System → Profit Center → Practice Area
"""

import streamlit as st
import streamlit.components.v1 as components

# Local module imports
from config import DATA_CONFIG, CORTEX_MODEL
from styles import CUSTOM_CSS, INFO_BOX_HOW_TO_USE, PERFORMANCE_LEGEND
from data_utils import load_data, build_hierarchy, flatten_tree, get_child_nodes
from ai_insights import generate_ai_summary, generate_child_insights, format_child_insights_html
from tree_visualization import create_tree_html

# Page configuration
st.set_page_config(
    page_title="NCC Decomposition Tree",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom styles
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Initialize session state
defaults = {
    'selected_metric': 'NCC',
    'selected_dimensions': DATA_CONFIG["dimensions"].copy(),
    'data_scenario': 'Actuals',
    'selected_node': None,
    'ai_insights': None,
    'child_insights': None,
    'analyze_children': True
}
for key, default in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = default


def main():
    """Main application entry point"""
    df = load_data(DATA_CONFIG["table"])

    # Sidebar controls
    with st.sidebar:
        st.markdown("### Settings")

        # Data scenario selector
        scenarios = df['DATA_SCENARIO'].unique().tolist()
        st.session_state.data_scenario = st.selectbox(
            "Data Scenario",
            scenarios,
            index=scenarios.index(st.session_state.data_scenario)
            if st.session_state.data_scenario in scenarios else 0
        )

        st.markdown("---")

        # Metric selector
        st.session_state.selected_metric = st.selectbox(
            "Metric",
            list(DATA_CONFIG["metrics"].keys()),
            format_func=lambda x: DATA_CONFIG["metrics"][x]["label"],
            index=list(DATA_CONFIG["metrics"].keys()).index(st.session_state.selected_metric)
        )

        st.markdown("---")

        # Hierarchy selector
        st.markdown("### Hierarchy")
        dims = st.multiselect(
            "Select drill-down levels",
            DATA_CONFIG["dimensions"],
            default=st.session_state.selected_dimensions,
            format_func=lambda x: DATA_CONFIG["dimension_labels"].get(x, x)
        )
        if dims:
            st.session_state.selected_dimensions = dims

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

        # Model info
        st.markdown(f"""
        <div class="info-box">
            <h4>AI Model</h4>
            <p>{CORTEX_MODEL}</p>
        </div>
        """, unsafe_allow_html=True)

    # Filter data
    filtered_df = df[
        (df['DATA_SCENARIO'] == st.session_state.data_scenario) &
        (df['YEAR'].isin(selected_years)) &
        (df['MONTH_OF_YEAR'].isin(selected_months))
    ]

    # Header section
    st.title("NCC Decomposition Tree")
    metric_label = DATA_CONFIG["metrics"][st.session_state.selected_metric]["label"]
    st.markdown(
        f'<p class="subtitle">Analyzing {metric_label} | Scenario: {st.session_state.data_scenario}</p>',
        unsafe_allow_html=True
    )
    st.markdown('<span class="category-badge">Financial</span>', unsafe_allow_html=True)

    # Metrics row
    total_ncc = filtered_df['NCC'].sum()
    total_py = filtered_df['NCC_PY'].sum()
    yoy = ((total_ncc - total_py) / total_py * 100) if total_py > 0 else 0

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total NCC", f"${total_ncc/1e6:.1f}M")
    c2.metric("Prior Year", f"${total_py/1e6:.1f}M")
    c3.metric("YoY Growth", f"{yoy:+.1f}%")
    c4.metric("Records", f"{len(filtered_df):,}")
    c5.metric("Drill Levels", len(st.session_state.selected_dimensions))

    st.markdown("---")

    # Main content area
    if st.session_state.selected_dimensions and len(filtered_df) > 0:
        tree_data = build_hierarchy(
            filtered_df,
            st.session_state.selected_dimensions,
            st.session_state.selected_metric
        )

        tree_col, ai_col = st.columns([2, 1])

        with tree_col:
            # Tree visualization with larger size
            components.html(
                create_tree_html(tree_data, st.session_state.selected_metric),
                height=750,
                scrolling=True
            )

        with ai_col:
            st.markdown("### AI Insights")
            st.markdown(
                '<p style="color: #6B7280; font-size: 0.85rem; margin-bottom: 1rem;">'
                'Select a node or double-click in the tree to analyze</p>',
                unsafe_allow_html=True
            )

            # Node selector dropdown
            nodes = flatten_tree(tree_data)
            labels = [n['label'] for n in nodes]
            selected = st.selectbox(
                "Select segment",
                labels,
                help="Choose a node for AI analysis"
            )
            node_data = next((n['data'] for n in nodes if n['label'] == selected), None)

            # Analysis options
            st.session_state.analyze_children = st.checkbox(
                "Include child node analysis",
                value=st.session_state.analyze_children,
                help="Analyze 1-2 levels below the selected node"
            )

            # Generate insights button
            if st.button("Generate AI Insights", type="primary", use_container_width=True):
                with st.spinner("Analyzing with Cortex AI..."):
                    # Generate main summary
                    st.session_state.ai_insights = generate_ai_summary(
                        node_data,
                        filtered_df,
                        metric_label
                    )
                    st.session_state.selected_node = selected

                    # Generate child insights if enabled
                    if st.session_state.analyze_children and node_data.get('children'):
                        child_nodes = get_child_nodes(node_data, max_depth=2)
                        st.session_state.child_insights = generate_child_insights(
                            node_data,
                            child_nodes,
                            metric_label
                        )
                    else:
                        st.session_state.child_insights = None

            # Display AI insights
            if st.session_state.ai_insights:
                node_name = st.session_state.selected_node.split(': ')[-1]
                st.markdown(f"""
                <div class="ai-insights-panel">
                    <div class="ai-insights-header">
                        <h4>{node_name}</h4>
                        <span class="ai-badge">Cortex AI</span>
                    </div>
                    <div class="ai-insights-content">
                        {st.session_state.ai_insights}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Display child insights if available
                if st.session_state.child_insights:
                    st.markdown("""
                    <div class="ai-insights-panel" style="margin-top: 0.75rem; background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%); border-color: #93C5FD;">
                        <div class="ai-insights-header">
                            <h4>Child Segment Analysis</h4>
                            <span class="ai-badge" style="background-color: #3B82F6;">Drill-Down</span>
                        </div>
                        <div class="ai-insights-content">
                    """, unsafe_allow_html=True)
                    st.markdown(st.session_state.child_insights)
                    st.markdown("</div></div>", unsafe_allow_html=True)

                    # Show child node breakdown
                    if node_data and node_data.get('children'):
                        child_nodes = get_child_nodes(node_data, max_depth=1)
                        child_html = format_child_insights_html(node_data, child_nodes)
                        if child_html:
                            st.markdown(child_html, unsafe_allow_html=True)

            # Node details
            if node_data:
                st.markdown("---")
                st.markdown("#### Selected Node Details")
                col_a, col_b = st.columns(2)
                with col_a:
                    value = node_data['value']
                    if value >= 1e6:
                        st.metric("Value", f"${value/1e6:.2f}M")
                    else:
                        st.metric("Value", f"${value:,.0f}")
                with col_b:
                    st.metric("Records", f"{node_data.get('count', 0):,}")

                # Show child count if applicable
                if node_data.get('children'):
                    st.metric("Direct Children", len(node_data['children']))
    else:
        st.warning("Select at least one dimension and ensure data is available.")


if __name__ == "__main__":
    main()
