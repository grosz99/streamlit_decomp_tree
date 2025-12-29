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

# Cortex AI configuration
# Available models (2025): claude-3-5-sonnet, llama3.3-70b, mistral-large2,
# snowflake-llama-3.3-70b, openai-gpt-4.1, deepseek-r1
CORTEX_MODEL = "claude-3-5-sonnet"

# Color palette - Surge/Beacon design system
COLORS = {
    "primary": "#1B5E3F",
    "primary_dark": "#154a32",
    "secondary": "#2D8B5E",
    "warning": "#F59E0B",
    "danger": "#DC2626",
    "success": "#10B981",
    "gray_50": "#F9FAFB",
    "gray_100": "#F3F4F6",
    "gray_200": "#E5E7EB",
    "gray_300": "#D1D5DB",
    "gray_400": "#9CA3AF",
    "gray_500": "#6B7280",
    "gray_700": "#374151",
    "gray_900": "#1F2937",
}
