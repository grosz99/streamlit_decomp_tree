"""
CSS styles for NCC Decomposition Tree - Surge/Beacon Design System
"""

CUSTOM_CSS = """
<style>
    /* Global styles */
    .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }

    /* Header styling */
    h1 {
        color: #1B5E3F !important;
        font-weight: 700 !important;
        font-size: 1.75rem !important;
        margin-bottom: 0.25rem !important;
    }

    /* Subheader */
    .subtitle {
        color: #6B7280;
        font-size: 0.95rem;
        margin-bottom: 1.5rem;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #F9FAFB;
        border-right: 1px solid #E5E7EB;
    }

    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #1B5E3F !important;
    }

    /* Card styling for metrics */
    [data-testid="stMetric"] {
        background-color: white;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }

    [data-testid="stMetricLabel"] {
        color: #6B7280 !important;
        font-size: 0.85rem !important;
    }

    [data-testid="stMetricValue"] {
        color: #1B5E3F !important;
        font-weight: 600 !important;
    }

    /* Button styling */
    .stButton > button {
        background-color: #1B5E3F;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        transition: background-color 0.2s;
    }

    .stButton > button:hover {
        background-color: #154a32;
        color: white;
    }

    /* Selectbox styling */
    .stSelectbox > div > div {
        border-radius: 8px;
        border-color: #E5E7EB;
    }

    /* Multiselect styling */
    .stMultiSelect > div > div {
        border-radius: 8px;
        border-color: #E5E7EB;
    }

    /* Divider */
    hr {
        border-color: #E5E7EB;
        margin: 1.5rem 0;
    }

    /* Category badge styling */
    .category-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        background-color: #E8F5EE;
        color: #1B5E3F;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 500;
        margin-bottom: 0.5rem;
    }

    /* Info box */
    .info-box {
        background-color: #F9FAFB;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 1rem;
        margin: 1rem 0;
    }

    .info-box h4 {
        color: #1B5E3F;
        font-size: 0.9rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }

    .info-box p, .info-box li {
        color: #6B7280;
        font-size: 0.85rem;
        margin: 0.25rem 0;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Legend items */
    .legend-item {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin: 0.25rem 0;
        font-size: 0.85rem;
        color: #4B5563;
    }

    .legend-dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
    }

    /* Source caption styling */
    .source-caption {
        color: #9CA3AF;
        font-size: 0.75rem;
        margin-top: -0.5rem;
    }

    /* AI Insights Panel */
    .ai-insights-panel {
        background: linear-gradient(135deg, #F0FDF4 0%, #ECFDF5 100%);
        border: 1px solid #86EFAC;
        border-radius: 12px;
        padding: 1.25rem;
        margin: 1rem 0;
    }

    .ai-insights-header {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 0.75rem;
    }

    .ai-insights-header h4 {
        color: #1B5E3F;
        font-size: 1rem;
        font-weight: 600;
        margin: 0;
    }

    .ai-badge {
        background-color: #1B5E3F;
        color: white;
        padding: 0.15rem 0.5rem;
        border-radius: 4px;
        font-size: 0.65rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .ai-insights-content {
        color: #374151;
        font-size: 0.9rem;
        line-height: 1.6;
    }

    .ai-insights-content p {
        margin: 0.5rem 0;
    }

    .node-selector-container {
        background-color: #F9FAFB;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
    }

    .node-selector-container h4 {
        color: #1B5E3F;
        font-size: 0.9rem;
        font-weight: 600;
        margin-bottom: 0.75rem;
    }
</style>
"""


# Reusable HTML components
INFO_BOX_HOW_TO_USE = """
<div class="info-box">
    <h4>How to Use</h4>
    <p>Click <strong>+</strong> to expand a node</p>
    <p>Click <strong>-</strong> to collapse</p>
    <p>Hover for detailed tooltips</p>
    <p>Use <strong>AI Insights</strong> panel for analysis</p>
</div>
"""

PERFORMANCE_LEGEND = """
<div class="info-box">
    <h4>Performance Legend</h4>
    <div class="legend-item">
        <div class="legend-dot" style="background: #1B5E3F;"></div>
        <span>High Performance</span>
    </div>
    <div class="legend-item">
        <div class="legend-dot" style="background: #2D8B5E;"></div>
        <span>Good Performance</span>
    </div>
    <div class="legend-item">
        <div class="legend-dot" style="background: #F59E0B;"></div>
        <span>Needs Attention</span>
    </div>
    <div class="legend-item">
        <div class="legend-dot" style="background: #DC2626;"></div>
        <span>Low Performance</span>
    </div>
</div>
"""
