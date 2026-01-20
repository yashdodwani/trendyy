"""
Helper utilities for the Aadhaar Analytics Dashboard.
Contains data transformation, formatting, and common operations.
"""

import pandas as pd
import streamlit as st
from typing import List, Dict, Any, Optional, Union


def json_to_dataframe(data: Dict[str, Any], alerts_key: str = "alerts") -> pd.DataFrame:
    """
    Convert API JSON response to pandas DataFrame.

    Args:
        data: API response dictionary
        alerts_key: Key containing the alerts list

    Returns:
        DataFrame with alert data
    """
    if not data or alerts_key not in data:
        return pd.DataFrame()

    alerts = data.get(alerts_key, [])
    if not alerts:
        return pd.DataFrame()

    return pd.DataFrame(alerts)


def format_list_field(items: Union[List[str], str, None], compact: bool = True, max_items: int = 3) -> str:
    """
    Format a list field (recommendations, tags, etc.) into readable text.

    Args:
        items: List of items or string
        compact: If True, show abbreviated version
        max_items: Max items to show in compact mode

    Returns:
        Formatted string
    """
    if items is None:
        return ""

    if isinstance(items, str):
        return items

    if not isinstance(items, list) or len(items) == 0:
        return ""

    if compact and len(items) > max_items:
        shown = items[:max_items]
        return "• " + "\n• ".join(shown) + f"\n... +{len(items) - max_items} more"

    return "• " + "\n• ".join(str(item) for item in items)


def format_list_as_bullets(items: Union[List[str], str, None]) -> str:
    """
    Format a list as HTML bullet points.

    Args:
        items: List of items or string

    Returns:
        HTML formatted bullet list
    """
    if items is None:
        return ""

    if isinstance(items, str):
        return f"<li>{items}</li>"

    if not isinstance(items, list) or len(items) == 0:
        return ""

    return "<ul>" + "".join(f"<li>{item}</li>" for item in items) + "</ul>"


def filter_dataframe(
    df: pd.DataFrame,
    states: Optional[List[str]] = None,
    search_text: Optional[str] = None,
    search_columns: List[str] = ["district", "pincode"]
) -> pd.DataFrame:
    """
    Apply filters to a DataFrame.

    Args:
        df: Input DataFrame
        states: List of states to filter by
        search_text: Text to search in specified columns
        search_columns: Columns to search in

    Returns:
        Filtered DataFrame
    """
    if df.empty:
        return df

    filtered = df.copy()

    # State filter
    if states and "state" in filtered.columns:
        filtered = filtered[filtered["state"].isin(states)]

    # Search filter
    if search_text:
        search_text = search_text.lower().strip()
        mask = pd.Series([False] * len(filtered))
        for col in search_columns:
            if col in filtered.columns:
                mask |= filtered[col].astype(str).str.lower().str.contains(search_text, na=False)
        filtered = filtered[mask]

    return filtered


def get_unique_states(df: pd.DataFrame) -> List[str]:
    """Extract unique states from DataFrame."""
    if df.empty or "state" not in df.columns:
        return []
    return sorted(df["state"].dropna().unique().tolist())


def get_unique_months(data: Dict[str, Any]) -> List[str]:
    """Extract unique months from API response."""
    months = set()
    if "month" in data:
        months.add(data["month"])

    alerts = data.get("alerts", [])
    for alert in alerts:
        if "month" in alert:
            months.add(alert["month"])

    return sorted(list(months), reverse=True)


def create_download_button(df: pd.DataFrame, filename: str, label: str = "📥 Download CSV"):
    """
    Create a download button for DataFrame.

    Args:
        df: DataFrame to download
        filename: Output filename
        label: Button label
    """
    if df.empty:
        st.warning("No data to download")
        return

    # Convert list columns to strings for CSV
    df_download = df.copy()
    for col in df_download.columns:
        if df_download[col].apply(lambda x: isinstance(x, list)).any():
            df_download[col] = df_download[col].apply(
                lambda x: "; ".join(str(i) for i in x) if isinstance(x, list) else x
            )

    csv = df_download.to_csv(index=False)
    st.download_button(
        label=label,
        data=csv,
        file_name=filename,
        mime="text/csv"
    )


def display_error_with_retry(error_message: str, retry_key: str):
    """
    Display error message with a retry button.

    Args:
        error_message: Error message to display
        retry_key: Unique key for the retry button
    """
    st.error(error_message)
    if st.button("🔄 Retry", key=retry_key):
        st.cache_data.clear()
        st.rerun()


def count_by_tier(df: pd.DataFrame, tier_col: str, tier_value: str) -> int:
    """Count records with a specific tier value."""
    if df.empty or tier_col not in df.columns:
        return 0
    return len(df[df[tier_col].str.upper() == tier_value.upper()])


def safe_get_column(df: pd.DataFrame, col: str, default: Any = None) -> pd.Series:
    """Safely get a column from DataFrame with default."""
    if col in df.columns:
        return df[col]
    return pd.Series([default] * len(df))


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text with ellipsis."""
    if not text or len(text) <= max_length:
        return text
    return text[:max_length] + "..."


def create_info_box(content: str, box_type: str = "info"):
    """
    Create a styled info box.

    Args:
        content: Box content (can be HTML)
        box_type: One of 'info', 'warning', 'danger', 'success'
    """
    st.markdown(f'<div class="{box_type}-box">{content}</div>', unsafe_allow_html=True)


def format_number(value: float, decimals: int = 2) -> str:
    """Format number with thousands separator."""
    if pd.isna(value):
        return "N/A"
    return f"{value:,.{decimals}f}"


def calculate_tier_distribution(df: pd.DataFrame, tier_col: str) -> pd.DataFrame:
    """
    Calculate tier distribution counts.

    Args:
        df: Input DataFrame
        tier_col: Column containing tier values

    Returns:
        DataFrame with tier counts
    """
    if df.empty or tier_col not in df.columns:
        return pd.DataFrame(columns=[tier_col, "count"])

    return df.groupby(tier_col).size().reset_index(name="count")

