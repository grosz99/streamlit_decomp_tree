# 🌳 Decomposition Tree for Streamlit in Snowflake

A Power BI-style decomposition tree that lets you drill into any metric by any dimension to understand what's driving performance.

## Features

- **Multi-dimensional drilling**: Drill into any dimension (Region → Category → Channel → Product)
- **AI Splits**: Automatic suggestions for high-value and low-value drill paths
- **Interactive visualization**: Horizontal bar charts with contribution percentages
- **Breadcrumb navigation**: Easy navigation up/down the drill hierarchy
- **Metric switching**: Analyze Revenue, Profit, Cost, or Units
- **Snowflake native**: Runs directly in Streamlit in Snowflake with session caching

## Screenshots

```
┌─────────────────────────────────────────────────────────────────┐
│  🌳 Decomposition Tree                                          │
│  ───────────────────                                            │
│  📊 All Data → Region: North → Category: Electronics            │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Total Revenue    Records    Average    Drill Levels Left │  │
│  │   $12.4M          48        $258K           2            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  💡 AI Splits                                                   │
│  ┌────────────────────┬─────────────────────┐                  │
│  │ High: Online 42%   │ Low: Wholesale 18%  │                  │
│  │ [🔼 Drill]         │ [🔽 Drill]          │                  │
│  └────────────────────┴─────────────────────┘                  │
│                                                                 │
│  [Channel] [Product]                                            │
│  ═══════════════════════════════════════════════════            │
│  Online      ████████████████████████  $5.2M (42%)              │
│  Retail      ██████████████████        $4.1M (33%)              │
│  Wholesale   ████████████              $3.1M (25%)              │
│                                                                 │
│  [Online $5.2M] [Retail $4.1M] [Wholesale $3.1M]  ← Click!     │
└─────────────────────────────────────────────────────────────────┘
```

## Files

| File | Purpose |
|------|---------|
| `streamlit_app.py` | Demo version with mock data (works locally) |
| `streamlit_app_snowflake.py` | Production version with Snowflake connection |
| `environment.yml` | Snowflake Anaconda channel dependencies |

## Deployment to Streamlit in Snowflake

### Option 1: Snowsight UI

1. Go to Snowsight → Streamlit → + Streamlit App
2. Paste the contents of `streamlit_app_snowflake.py`
3. Update the `DATA_CONFIG` section with your table/columns
4. Add `environment.yml` to the app files
5. Click Run

### Option 2: SQL Commands

```sql
-- Create the Streamlit app
CREATE OR REPLACE STREAMLIT MY_DB.MY_SCHEMA.DECOMPOSITION_TREE
  ROOT_LOCATION = '@MY_DB.MY_SCHEMA.MY_STAGE/decomposition_tree'
  MAIN_FILE = 'streamlit_app_snowflake.py'
  QUERY_WAREHOUSE = 'MY_WAREHOUSE';

-- Grant access
GRANT USAGE ON STREAMLIT MY_DB.MY_SCHEMA.DECOMPOSITION_TREE TO ROLE MY_ROLE;
```

## Configuration

Update the `DATA_CONFIG` dictionary in `streamlit_app_snowflake.py`:

```python
DATA_CONFIG = {
    "source_table": "YOUR_DATABASE.YOUR_SCHEMA.YOUR_TABLE",
    
    "metrics": {
        "Revenue": "REVENUE_COLUMN",      # Display name: Snowflake column
        "Profit": "PROFIT_COLUMN",
        "Units": "UNITS_COLUMN"
    },
    
    "dimensions": {
        "Region": "REGION_COLUMN",        # Display name: Snowflake column
        "Category": "CATEGORY_COLUMN",
        "Channel": "CHANNEL_COLUMN",
        "Product": "PRODUCT_COLUMN"
    },
    
    "date_column": "ORDER_DATE",          # Optional for filtering
    "pre_aggregated": False               # Set True if data is already aggregated
}
```

## How It Works

### Drill Path State
The app tracks your drill path in `st.session_state.drill_path` as a list of (dimension, value) tuples:

```python
# Example: Drilled into North region, then Electronics category
drill_path = [("Region", "North"), ("Category", "Electronics")]
```

### AI Splits
The app analyzes all remaining dimensions to find:
- **High Value**: The dimension/value combination with the highest contribution %
- **Low Value**: The dimension/value combination with the lowest contribution %

### Data Flow
1. Load data from Snowflake (cached for 5 minutes)
2. Filter based on current drill path
3. Calculate decomposition for each available dimension
4. Render charts and drill buttons

## Performance Tips

1. **Use aggregated views**: Pre-aggregate your data if you have millions of rows
2. **Limit dimensions**: Start with 4-5 key dimensions
3. **Cache aggressively**: Adjust `@st.cache_data(ttl=600)` based on data freshness needs
4. **Add date filters**: Filter to recent data to reduce query size

## Example Snowflake View

```sql
CREATE OR REPLACE VIEW ANALYTICS.DECOMPOSITION_SOURCE AS
SELECT
    REGION,
    PRODUCT_CATEGORY,
    SALES_CHANNEL,
    PRODUCT_NAME,
    CUSTOMER_SEGMENT,
    TO_CHAR(ORDER_DATE, 'YYYY-MM') AS FISCAL_PERIOD,
    SUM(REVENUE) AS REVENUE,
    SUM(PROFIT) AS PROFIT,
    SUM(COST) AS COST,
    SUM(UNITS_SOLD) AS UNITS_SOLD
FROM SALES.FACT_ORDERS
GROUP BY 1, 2, 3, 4, 5, 6;
```

## Customization

### Add New Metrics
Add to the `metrics` dict in `DATA_CONFIG`:
```python
"metrics": {
    ...
    "Margin %": "MARGIN_PCT",
    "AOV": "AVG_ORDER_VALUE"
}
```

### Add New Dimensions
Add to the `dimensions` dict:
```python
"dimensions": {
    ...
    "Sales Rep": "SALES_REP_NAME",
    "Quarter": "FISCAL_QUARTER"
}
```

### Change Color Scheme
Modify the `colorscale` parameter in `create_decomposition_chart()`:
```python
marker=dict(
    color=decomp_df[metric],
    colorscale='Viridis',  # or 'Reds', 'Greens', 'RdYlGn'
    showscale=False
)
```

## Limitations

- Plotly click events don't work in SiS (hence explicit drill buttons)
- 32MB message limit (pre-aggregate large datasets)
- No external CDN (D3.js must be inline if used)
- Custom components can't call external services

## Requirements

- Snowflake account with Streamlit in Snowflake enabled
- Read access to source table/view
- Warehouse for query execution

## License

MIT - Use freely in your organization.
