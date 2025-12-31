"""
CSS styles for NCC Decomposition Tree - Surge/Beacon Design System
"""

CUSTOM_CSS = """
<style>
    .stApp { font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }
    h1 { color: #1B5E3F !important; font-weight: 700 !important; font-size: 1.75rem !important; }
    .subtitle { color: #6B7280; font-size: 0.95rem; margin-bottom: 1.5rem; }
    [data-testid="stSidebar"] { background-color: #F9FAFB; border-right: 1px solid #E5E7EB; }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 { color: #1B5E3F !important; }
    [data-testid="stMetric"] { background-color: white; border: 1px solid #E5E7EB; border-radius: 12px; padding: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
    [data-testid="stMetricLabel"] { color: #6B7280 !important; font-size: 0.85rem !important; }
    [data-testid="stMetricValue"] { color: #1B5E3F !important; font-weight: 600 !important; }
    .stButton > button { background-color: #1B5E3F; color: white; border: none; border-radius: 8px; padding: 0.5rem 1rem; font-weight: 500; }
    .stButton > button:hover { background-color: #154a32; color: white; }
    .stSelectbox > div > div, .stMultiSelect > div > div { border-radius: 8px; border-color: #E5E7EB; }
    hr { border-color: #E5E7EB; margin: 1.5rem 0; }
    .category-badge { display: inline-block; padding: 0.25rem 0.75rem; background-color: #E8F5EE; color: #1B5E3F; border-radius: 4px; font-size: 0.75rem; font-weight: 500; }
    .info-box { background-color: #F9FAFB; border: 1px solid #E5E7EB; border-radius: 12px; padding: 1rem; margin: 1rem 0; }
    .info-box h4 { color: #1B5E3F; font-size: 0.9rem; font-weight: 600; margin-bottom: 0.5rem; }
    .info-box p { color: #6B7280; font-size: 0.85rem; margin: 0.25rem 0; }
    .legend-item { display: flex; align-items: center; gap: 0.5rem; margin: 0.25rem 0; font-size: 0.85rem; color: #4B5563; }
    .legend-dot { width: 12px; height: 12px; border-radius: 50%; }
    .ai-insights-panel { background: linear-gradient(135deg, #F0FDF4 0%, #ECFDF5 100%); border: 1px solid #86EFAC; border-radius: 12px; padding: 1.25rem; margin: 1rem 0; }
    .ai-insights-header { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.75rem; }
    .ai-insights-header h4 { color: #1B5E3F; font-size: 1rem; font-weight: 600; margin: 0; }
    .ai-badge { background-color: #1B5E3F; color: white; padding: 0.15rem 0.5rem; border-radius: 4px; font-size: 0.65rem; font-weight: 600; text-transform: uppercase; }
    .ai-insights-content { color: #374151; font-size: 0.9rem; line-height: 1.6; }
    .child-insight { background: #F9FAFB; border-left: 3px solid #1B5E3F; padding: 0.75rem; margin: 0.5rem 0; border-radius: 0 8px 8px 0; }
    .child-insight-title { font-weight: 600; color: #1B5E3F; font-size: 0.9rem; }
    .child-insight-value { color: #6B7280; font-size: 0.85rem; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
</style>
"""

INFO_BOX_HOW_TO_USE = """
<div class="info-box">
    <h4>How to Use</h4>
    <p>Click <strong>+</strong> to expand nodes</p>
    <p>Click <strong>−</strong> to collapse</p>
    <p><strong>Double-click</strong> a node to analyze</p>
</div>
"""

PERFORMANCE_LEGEND = """
<div class="info-box">
    <h4>Legend</h4>
    <div class="legend-item"><div class="legend-dot" style="background:#1B5E3F"></div><span>High Performance</span></div>
    <div class="legend-item"><div class="legend-dot" style="background:#2D8B5E"></div><span>Good Performance</span></div>
    <div class="legend-item"><div class="legend-dot" style="background:#F59E0B"></div><span>Needs Attention</span></div>
    <div class="legend-item"><div class="legend-dot" style="background:#DC2626"></div><span>Low Performance</span></div>
</div>
"""
