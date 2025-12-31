"""
Configuration settings for NCC Decomposition Tree
"""

# Data configuration
DATA_CONFIG = {
    "table": "MY_WORKFLOW_DB.PUBLIC.NCC_TEST",
    "metrics": {
        "NCC": {"label": "Net Client Contribution ($)"},
        "NCC_PY": {"label": "Prior Year NCC ($)"},
        "YoY_Growth": {"label": "Year-over-Year Growth (%)"},
        "Avg_NCC": {"label": "Average NCC ($)"}
    },
    "dimensions": ["REGION", "SYSTEM", "PROFIT_CENTER", "PRACTICE_AREA"],
    "dimension_labels": {
        "REGION": "Region",
        "SYSTEM": "System",
        "PROFIT_CENTER": "Profit Center",
        "PRACTICE_AREA": "Practice Area"
    }
}

# Cortex AI configuration - Latest models (2025)
# Available: claude-4-opus, claude-4-sonnet, claude-3-7-sonnet, llama4-maverick, llama4-scout
CORTEX_MODEL = "claude-3-7-sonnet"

# Color palette - Surge/Beacon design system
COLORS = {
    "primary": "#1B5E3F",
    "primary_dark": "#154a32",
    "secondary": "#2D8B5E",
    "warning": "#F59E0B",
    "danger": "#DC2626",
    "success": "#10B981",
}
