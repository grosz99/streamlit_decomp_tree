"""
Unit tests for Decomposition Tree
Tests data processing, hierarchy building, and metric calculations
"""

import pytest
import pandas as pd
import numpy as np
import json

# Import functions from main app (without running Streamlit)
import sys
from unittest.mock import MagicMock

# Mock streamlit before importing
mock_st = MagicMock()
# Make cache_data a passthrough decorator
mock_st.cache_data = lambda func: func
mock_st.set_page_config = MagicMock()
sys.modules['streamlit'] = mock_st
sys.modules['streamlit.components'] = MagicMock()
sys.modules['streamlit.components.v1'] = MagicMock()

# Now we can import our functions
from streamlit_app import (
    calculate_metric,
    get_color,
    build_hierarchy,
    create_tree_visualization,
    generate_mock_data
)


# ============================================
# FIXTURES
# ============================================

@pytest.fixture
def sample_df():
    """Create a small sample DataFrame for testing"""
    return pd.DataFrame({
        'Division': ['Brooklyn', 'Brooklyn', 'Manhattan', 'Manhattan', 'Bronx'],
        'Depot': ['Jackie Gleason', 'Fresh Pond', 'Harlem', 'Midtown', 'Gun Hill'],
        'Route': ['B1', 'B2', 'M1', 'M2', 'Bx1'],
        'Direction': ['SB', 'NB', 'SB', 'NB', 'SB'],
        'Period': ['AM', 'PM', 'AM', 'PM', 'AM'],
        'OTP': [70.0, 65.0, 80.0, 75.0, 60.0],
        'Trips': [100, 100, 100, 100, 100]
    })


@pytest.fixture
def empty_df():
    """Create an empty DataFrame"""
    return pd.DataFrame({
        'Division': [],
        'Depot': [],
        'Route': [],
        'Direction': [],
        'Period': [],
        'OTP': [],
        'Trips': []
    })


@pytest.fixture
def single_row_df():
    """Create a single-row DataFrame"""
    return pd.DataFrame({
        'Division': ['Brooklyn'],
        'Depot': ['Jackie Gleason'],
        'Route': ['B1'],
        'Direction': ['SB'],
        'Period': ['AM'],
        'OTP': [70.0],
        'Trips': [100]
    })


# ============================================
# METRIC CALCULATION TESTS
# ============================================

class TestCalculateMetric:
    """Tests for calculate_metric function"""

    def test_otp_weighted_average(self, sample_df):
        """OTP should be weighted by Trips"""
        result = calculate_metric(sample_df, "OTP")
        # All trips are equal (100), so simple average
        expected = (70 + 65 + 80 + 75 + 60) / 5
        assert result == expected

    def test_otp_with_different_weights(self):
        """OTP calculation with different trip weights"""
        df = pd.DataFrame({
            'OTP': [60.0, 80.0],
            'Trips': [100, 300]  # 80% OTP has 3x weight
        })
        result = calculate_metric(df, "OTP")
        expected = (60 * 100 + 80 * 300) / 400  # 75.0
        assert result == expected

    def test_trips_sum(self, sample_df):
        """Trips should be summed"""
        result = calculate_metric(sample_df, "Trips")
        assert result == 500  # 5 rows × 100 trips

    def test_empty_df_otp(self, empty_df):
        """Empty DataFrame should return 0 for OTP"""
        result = calculate_metric(empty_df, "OTP")
        assert result == 0.0

    def test_empty_df_trips(self, empty_df):
        """Empty DataFrame should return 0 for Trips"""
        result = calculate_metric(empty_df, "Trips")
        assert result == 0

    def test_single_row(self, single_row_df):
        """Single row should return that row's value"""
        otp_result = calculate_metric(single_row_df, "OTP")
        trips_result = calculate_metric(single_row_df, "Trips")
        assert otp_result == 70.0
        assert trips_result == 100

    def test_zero_trips_otp(self):
        """Zero trips should return 0 OTP (avoid division by zero)"""
        df = pd.DataFrame({
            'OTP': [70.0],
            'Trips': [0]
        })
        result = calculate_metric(df, "OTP")
        assert result == 0.0


# ============================================
# COLOR SCALE TESTS
# ============================================

class TestGetColor:
    """Tests for get_color function - Surge/Beacon color palette"""

    def test_high_value_green(self):
        """High values (>70% normalized) should be primary green"""
        result = get_color(90, 0, 100)
        assert result == "#1B5E3F"  # Surge primary green

    def test_medium_high_light_green(self):
        """Medium-high values (50-70%) should be medium green"""
        result = get_color(60, 0, 100)
        assert result == "#2D8B5E"  # Surge medium green

    def test_medium_low_yellow(self):
        """Medium-low values (30-50%) should be amber"""
        result = get_color(40, 0, 100)
        assert result == "#F59E0B"  # Amber warning

    def test_low_value_red(self):
        """Low values (<30%) should be red"""
        result = get_color(20, 0, 100)
        assert result == "#DC2626"  # Red for low

    def test_equal_min_max(self):
        """When min equals max, should return middle color"""
        result = get_color(50, 50, 50)
        assert result == "#2D8B5E"  # 0.5 normalized → medium green

    def test_boundary_70_percent(self):
        """Test exact 70% boundary"""
        result = get_color(70, 0, 100)
        assert result == "#1B5E3F"  # Primary green

    def test_boundary_50_percent(self):
        """Test exact 50% boundary"""
        result = get_color(50, 0, 100)
        assert result == "#2D8B5E"  # Medium green

    def test_boundary_30_percent(self):
        """Test exact 30% boundary"""
        result = get_color(30, 0, 100)
        assert result == "#F59E0B"  # Amber


# ============================================
# HIERARCHY BUILDING TESTS
# ============================================

class TestBuildHierarchy:
    """Tests for build_hierarchy function"""

    def test_root_node_structure(self, sample_df):
        """Root node should have correct structure"""
        result = build_hierarchy(sample_df, ["Division"], "OTP")

        assert "name" in result
        assert "dimension" in result
        assert "value" in result
        assert "color" in result
        assert "count" in result
        assert "children" in result

        assert result["name"] == "Total"
        assert result["dimension"] == "All Data"
        assert result["count"] == 5

    def test_single_dimension_children(self, sample_df):
        """Single dimension should create correct children"""
        result = build_hierarchy(sample_df, ["Division"], "OTP")

        children = result["children"]
        assert len(children) == 3  # Brooklyn, Manhattan, Bronx

        # Children should be sorted by value descending
        values = [c["value"] for c in children]
        assert values == sorted(values, reverse=True)

    def test_multi_dimension_nesting(self, sample_df):
        """Multiple dimensions should create nested structure"""
        result = build_hierarchy(sample_df, ["Division", "Depot"], "OTP")

        # Check first level
        assert len(result["children"]) == 3

        # Check second level exists for Brooklyn
        brooklyn = next(c for c in result["children"] if c["name"] == "Brooklyn")
        assert "children" in brooklyn
        assert len(brooklyn["children"]) == 2  # Jackie Gleason, Fresh Pond

    def test_empty_dimensions(self, sample_df):
        """Empty dimensions list should return root with no children"""
        result = build_hierarchy(sample_df, [], "OTP")

        assert result["name"] == "Total"
        assert result["children"] == []

    def test_child_counts(self, sample_df):
        """Child counts should reflect filtered data"""
        result = build_hierarchy(sample_df, ["Division"], "OTP")

        brooklyn = next(c for c in result["children"] if c["name"] == "Brooklyn")
        manhattan = next(c for c in result["children"] if c["name"] == "Manhattan")
        bronx = next(c for c in result["children"] if c["name"] == "Bronx")

        assert brooklyn["count"] == 2
        assert manhattan["count"] == 2
        assert bronx["count"] == 1

    def test_trips_metric(self, sample_df):
        """Trips metric should sum correctly"""
        result = build_hierarchy(sample_df, ["Division"], "Trips")

        brooklyn = next(c for c in result["children"] if c["name"] == "Brooklyn")
        assert brooklyn["value"] == 200  # 2 rows × 100 trips

    def test_color_assignment(self, sample_df):
        """Colors should be assigned based on relative values"""
        result = build_hierarchy(sample_df, ["Division"], "OTP")

        # All children should have color assigned
        for child in result["children"]:
            assert child["color"].startswith("#")


# ============================================
# VISUALIZATION TESTS
# ============================================

class TestCreateTreeVisualization:
    """Tests for create_tree_visualization function"""

    def test_returns_html_string(self, sample_df):
        """Should return valid HTML string"""
        tree_data = build_hierarchy(sample_df, ["Division"], "OTP")
        result = create_tree_visualization(tree_data, "OTP")

        assert isinstance(result, str)
        assert "<!DOCTYPE html>" in result
        assert "</html>" in result

    def test_contains_no_external_scripts(self, sample_df):
        """Should not contain external script sources (CSP compliance)"""
        tree_data = build_hierarchy(sample_df, ["Division"], "OTP")
        result = create_tree_visualization(tree_data, "OTP")

        # Check no external script tags
        assert 'src="http' not in result
        assert 'src="https' not in result
        assert "d3js.org" not in result
        assert "cdn" not in result.lower()

    def test_contains_inline_javascript(self, sample_df):
        """Should contain inline JavaScript"""
        tree_data = build_hierarchy(sample_df, ["Division"], "OTP")
        result = create_tree_visualization(tree_data, "OTP")

        assert "<script>" in result
        assert "</script>" in result

    def test_contains_svg_elements(self, sample_df):
        """Should reference SVG element creation"""
        tree_data = build_hierarchy(sample_df, ["Division"], "OTP")
        result = create_tree_visualization(tree_data, "OTP")

        assert "createElementNS" in result
        assert "http://www.w3.org/2000/svg" in result

    def test_contains_tree_data(self, sample_df):
        """Should embed tree data as JSON"""
        tree_data = build_hierarchy(sample_df, ["Division"], "OTP")
        result = create_tree_visualization(tree_data, "OTP")

        # Data should be embedded
        assert "Total" in result
        assert "Brooklyn" in result

    def test_percent_format_type(self, sample_df):
        """OTP metric should use percent format"""
        tree_data = build_hierarchy(sample_df, ["Division"], "OTP")
        result = create_tree_visualization(tree_data, "OTP")

        assert 'formatType = "percent"' in result

    def test_number_format_type(self, sample_df):
        """Trips metric should use number format"""
        tree_data = build_hierarchy(sample_df, ["Division"], "Trips")
        result = create_tree_visualization(tree_data, "Trips")

        assert 'formatType = "number"' in result

    def test_no_eval_usage(self, sample_df):
        """Should not use eval() (blocked by CSP)"""
        tree_data = build_hierarchy(sample_df, ["Division"], "OTP")
        result = create_tree_visualization(tree_data, "OTP")

        assert "eval(" not in result

    def test_uses_strict_mode(self, sample_df):
        """Should use JavaScript strict mode"""
        tree_data = build_hierarchy(sample_df, ["Division"], "OTP")
        result = create_tree_visualization(tree_data, "OTP")

        assert '"use strict"' in result


# ============================================
# DATA GENERATION TESTS
# ============================================

class TestGenerateMockData:
    """Tests for generate_mock_data function"""

    def test_returns_dataframe(self):
        """Should return a pandas DataFrame"""
        # Call the function directly (mocked cache_data is passthrough)
        result = generate_mock_data()
        assert isinstance(result, pd.DataFrame)

    def test_has_required_columns(self):
        """Should have all required columns"""
        result = generate_mock_data()
        required_cols = ['Division', 'Depot', 'Route', 'Direction', 'Period', 'OTP', 'Trips']

        for col in required_cols:
            assert col in result.columns

    def test_otp_in_valid_range(self):
        """OTP values should be between 50 and 85"""
        result = generate_mock_data()

        assert result['OTP'].min() >= 50
        assert result['OTP'].max() <= 85

    def test_trips_positive(self):
        """Trips should be positive integers"""
        result = generate_mock_data()

        assert (result['Trips'] > 0).all()

    def test_consistent_output(self):
        """Should produce consistent output (seeded random)"""
        result1 = generate_mock_data()
        result2 = generate_mock_data()

        pd.testing.assert_frame_equal(result1, result2)

    def test_has_sufficient_rows(self):
        """Should generate sufficient data"""
        result = generate_mock_data()
        assert len(result) == 3000


# ============================================
# INTEGRATION TESTS
# ============================================

class TestIntegration:
    """Integration tests for full pipeline"""

    def test_full_pipeline(self, sample_df):
        """Test complete data → hierarchy → visualization pipeline"""
        # Build hierarchy
        tree_data = build_hierarchy(
            sample_df,
            ["Division", "Depot", "Route"],
            "OTP"
        )

        # Create visualization
        html = create_tree_visualization(tree_data, "OTP")

        # Verify output
        assert isinstance(html, str)
        assert len(html) > 1000  # Should be substantial
        assert "Total" in html

    def test_all_dimensions(self, sample_df):
        """Test with all dimensions"""
        tree_data = build_hierarchy(
            sample_df,
            ["Division", "Depot", "Route", "Direction", "Period"],
            "OTP"
        )

        # Should have deeply nested structure
        assert tree_data["children"][0]["children"][0]["children"] is not None

    def test_json_serializable(self, sample_df):
        """Tree data should be JSON serializable"""
        tree_data = build_hierarchy(sample_df, ["Division"], "OTP")

        # Should not raise
        json_str = json.dumps(tree_data)
        assert isinstance(json_str, str)

        # Should round-trip
        parsed = json.loads(json_str)
        assert parsed["name"] == "Total"


# ============================================
# EDGE CASE TESTS
# ============================================

class TestEdgeCases:
    """Tests for edge cases and error handling"""

    def test_single_group(self):
        """Single group should work correctly"""
        df = pd.DataFrame({
            'Division': ['Brooklyn', 'Brooklyn', 'Brooklyn'],
            'OTP': [70.0, 75.0, 80.0],
            'Trips': [100, 100, 100]
        })

        result = build_hierarchy(df, ["Division"], "OTP")
        assert len(result["children"]) == 1
        assert result["children"][0]["name"] == "Brooklyn"

    def test_unicode_names(self):
        """Unicode characters in names should work"""
        df = pd.DataFrame({
            'Division': ['北京', 'Москва', 'München'],
            'OTP': [70.0, 75.0, 80.0],
            'Trips': [100, 100, 100]
        })

        result = build_hierarchy(df, ["Division"], "OTP")
        html = create_tree_visualization(result, "OTP")

        assert '北京' in html or '\\u' in html  # Either direct or escaped

    def test_special_characters_in_names(self):
        """Special characters should be handled"""
        df = pd.DataFrame({
            'Division': ["Test & Co", "A < B", "C > D"],
            'OTP': [70.0, 75.0, 80.0],
            'Trips': [100, 100, 100]
        })

        result = build_hierarchy(df, ["Division"], "OTP")
        # Should not raise when creating JSON
        json.dumps(result)

    def test_very_large_values(self):
        """Very large values should work"""
        df = pd.DataFrame({
            'Division': ['A', 'B'],
            'OTP': [70.0, 75.0],
            'Trips': [1000000000, 2000000000]
        })

        result = build_hierarchy(df, ["Division"], "Trips")
        assert result["value"] == 3000000000

    def test_very_small_otp_differences(self):
        """Small OTP differences should still produce colors"""
        df = pd.DataFrame({
            'Division': ['A', 'B', 'C'],
            'OTP': [70.001, 70.002, 70.003],
            'Trips': [100, 100, 100]
        })

        result = build_hierarchy(df, ["Division"], "OTP")

        # All should have valid colors
        for child in result["children"]:
            assert child["color"].startswith("#")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
