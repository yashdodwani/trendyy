"""Components package for Aadhaar Analytics Dashboard."""
from .api_client import (
    fetch_alerts,
    fetch_migration_alerts,
    fetch_infrastructure_alerts,
    fetch_biometric_alerts,
    fetch_lost_generation_alerts,
    fetch_ml_alerts,
    test_connection,
    clear_cache,
    get_backend_url,
)
from .charts import (
    create_horizontal_bar_chart,
    create_pie_donut_chart,
    create_scatter_plot,
    create_histogram,
    create_comparison_bar_chart,
    create_kpi_indicator,
    create_line_chart,
)
from .theme import (
    TIER_COLORS,
    TIER_DISTRIBUTION_COLORS,
    get_tier_color,
    apply_custom_css,
)

