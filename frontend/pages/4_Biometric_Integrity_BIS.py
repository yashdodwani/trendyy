"""
Biometric Integrity BIS Page
============================
Biometric Integrity Score analysis for monitoring capture gaps and data quality.
"""

import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.api_client import fetch_biometric_alerts
from components.charts import (
    create_horizontal_bar_chart,
    create_pie_donut_chart,
    create_scatter_plot,
    create_histogram,
)
from components.theme import apply_custom_css, TIER_DISTRIBUTION_COLORS
from utils.helpers import (
    json_to_dataframe,
    filter_dataframe,
    get_unique_states,
    format_list_field,
    create_download_button,
    display_error_with_retry,
)

# Page config
st.set_page_config(
    page_title="Biometric Integrity BIS | Aadhaar Analytics",
    page_icon="🧬",
    layout="wide"
)

apply_custom_css()

st.title("🧬 Biometric Integrity Analysis (BIS)")
st.markdown("""
Biometric Integrity Score analytics for monitoring capture gaps, enrollment-biometric 
imbalances, and data quality issues across enrollment centers.
""")

# Get filter values from session state
month = st.session_state.get("selected_month", "Latest")
month_param = None if month == "Latest" else month
search_text = st.session_state.get("search_text", "")
top_n = st.session_state.get("top_n", 10)

# Load data
@st.cache_data(ttl=300)
def load_biometric_data(month_param):
    return fetch_biometric_alerts(month_param)

try:
    with st.spinner("Loading biometric integrity data..."):
        data = load_biometric_data(month_param)

    df = json_to_dataframe(data)

    if df.empty:
        st.warning("No biometric integrity data available for the selected period.")
        st.stop()

    # Display data month
    st.info(f"📅 Data Month: **{data.get('month', 'Unknown')}**")

    # State filter in sidebar
    states = get_unique_states(df)
    if states:
        selected_states = st.sidebar.multiselect(
            "🗺️ Filter by State",
            options=states,
            default=st.session_state.get("selected_states", []),
            key="bio_state_filter"
        )
        if selected_states:
            df = filter_dataframe(df, states=selected_states)

    # Capture gap tier filter
    if "capture_gap_tier" in df.columns:
        tier_options = df["capture_gap_tier"].unique().tolist()
        selected_tiers = st.sidebar.multiselect(
            "⚡ Filter by Capture Gap Tier",
            options=tier_options,
            default=[],
            key="bio_tier_filter"
        )
        if selected_tiers:
            df = df[df["capture_gap_tier"].isin(selected_tiers)]

    # Apply search filter
    if search_text:
        df = filter_dataframe(df, search_text=search_text, search_columns=["district", "pincode"])

    if df.empty:
        st.warning("No data matches the current filters.")
        st.stop()

    st.markdown("---")

    # Summary metrics
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Total Records", len(df))

    with col2:
        if "capture_gap_tier" in df.columns:
            high_gap = len(df[df["capture_gap_tier"].str.upper() == "HIGH"])
            st.metric("HIGH Gap Pincodes", high_gap, delta_color="inverse")

    with col3:
        if "capture_gap_ratio" in df.columns:
            avg_gap = df["capture_gap_ratio"].mean()
            st.metric("Avg Gap Ratio", f"{avg_gap:.3f}")

    with col4:
        if "enrol_total" in df.columns:
            total_enrol = df["enrol_total"].sum()
            st.metric("Total Enrollments", f"{total_enrol:,.0f}")

    with col5:
        if "bio_total" in df.columns:
            total_bio = df["bio_total"].sum()
            st.metric("Total Biometrics", f"{total_bio:,.0f}")

    st.markdown("---")

    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["📊 Charts", "📋 Data Table", "🔧 Operational Insights"])

    with tab1:
        col1, col2 = st.columns([2, 1])

        with col1:
            # Chart 1: Bar chart - Top pincodes by capture_gap_ratio
            st.subheader("📊 Top Pincodes by Capture Gap Ratio")

            if "capture_gap_ratio" in df.columns:
                # Create display label
                df_chart = df.copy()
                if "pincode" in df_chart.columns:
                    df_chart["location"] = df_chart["district"].astype(str) + " - " + df_chart["pincode"].astype(str)
                else:
                    df_chart["location"] = df_chart["district"]

                fig_bar = create_horizontal_bar_chart(
                    df_chart,
                    x_col="capture_gap_ratio",
                    y_col="location",
                    color_col="capture_gap_tier" if "capture_gap_tier" in df_chart.columns else None,
                    title=f"Top {top_n} Locations by Capture Gap Ratio",
                    x_label="Capture Gap Ratio",
                    y_label="Location",
                    top_n=top_n,
                    height=450
                )
                st.plotly_chart(fig_bar, use_container_width=True)

        with col2:
            # Pie/Donut chart - Capture gap tier distribution
            if "capture_gap_tier" in df.columns:
                st.subheader("📈 Tier Distribution")
                tier_counts = df["capture_gap_tier"].value_counts().reset_index()
                tier_counts.columns = ["capture_gap_tier", "count"]

                fig_pie = create_pie_donut_chart(
                    tier_counts,
                    values_col="count",
                    names_col="capture_gap_tier",
                    title="Capture Gap Tier Distribution",
                    color_map=TIER_DISTRIBUTION_COLORS["biometric"],
                    height=400
                )
                st.plotly_chart(fig_pie, use_container_width=True)

        st.markdown("---")

        # Chart 2: Scatter plot - enrol_total vs bio_total
        st.subheader("🔵 Enrollment vs Biometric Capture")

        col1, col2 = st.columns(2)

        with col1:
            if "enrol_total" in df.columns and "bio_total" in df.columns:
                df_scatter = df.copy()
                if "pincode" in df_scatter.columns:
                    df_scatter["location"] = df_scatter["district"].astype(str) + " - " + df_scatter["pincode"].astype(str)
                else:
                    df_scatter["location"] = df_scatter["district"]

                fig_scatter = create_scatter_plot(
                    df_scatter,
                    x_col="enrol_total",
                    y_col="bio_total",
                    color_col="capture_gap_tier" if "capture_gap_tier" in df_scatter.columns else None,
                    hover_name="location",
                    title="Enrollment Total vs Biometric Total",
                    x_label="Enrollment Total",
                    y_label="Biometric Total",
                    height=400
                )
                st.plotly_chart(fig_scatter, use_container_width=True)

        with col2:
            # Chart 3: Histogram of imbalance_score (if exists)
            if "imbalance_score" in df.columns:
                # Filter out null values
                df_imbalance = df[df["imbalance_score"].notna()]

                if len(df_imbalance) > 0:
                    st.subheader("📊 Imbalance Score Distribution")
                    fig_hist = create_histogram(
                        df_imbalance,
                        x_col="imbalance_score",
                        title="Distribution of Imbalance Scores",
                        x_label="Imbalance Score",
                        nbins=20,
                        height=400
                    )
                    st.plotly_chart(fig_hist, use_container_width=True)
                else:
                    st.info("No imbalance score data available")
            else:
                st.info("Imbalance score data not available in this dataset")

    with tab2:
        st.subheader("📋 Biometric Integrity Alerts Data")

        # Prepare display DataFrame
        df_display = df.copy()

        # Format list columns for display
        if "tags" in df_display.columns:
            df_display["tags_text"] = df_display["tags"].apply(
                lambda x: format_list_field(x, compact=True)
            )

        if "recommendations" in df_display.columns:
            df_display["recommendations_text"] = df_display["recommendations"].apply(
                lambda x: format_list_field(x, compact=True)
            )

        # Select columns for display
        display_cols = [
            "state", "district", "pincode", "month",
            "enrol_total", "bio_total", "capture_gap_ratio", "capture_gap_tier"
        ]
        if "imbalance_score" in df_display.columns:
            display_cols.append("imbalance_score")
        if "imbalance_tier" in df_display.columns:
            display_cols.append("imbalance_tier")
        if "tags_text" in df_display.columns:
            display_cols.append("tags_text")
        if "recommendations_text" in df_display.columns:
            display_cols.append("recommendations_text")

        available_cols = [c for c in display_cols if c in df_display.columns]

        # Sorting options
        col1, col2 = st.columns([1, 1])
        with col1:
            sort_col = st.selectbox(
                "Sort by",
                options=available_cols,
                index=available_cols.index("capture_gap_ratio") if "capture_gap_ratio" in available_cols else 0,
                key="bio_sort_col"
            )
        with col2:
            sort_order = st.radio("Order", ["Descending", "Ascending"], horizontal=True, key="bio_sort_order")

        df_sorted = df_display.sort_values(
            sort_col,
            ascending=(sort_order == "Ascending")
        )

        st.dataframe(
            df_sorted[available_cols],
            use_container_width=True,
            hide_index=True,
            height=400
        )

        # Download button
        st.markdown("---")
        create_download_button(
            df_sorted,
            filename=f"biometric_alerts_{data.get('month', 'latest')}.csv",
            label="📥 Download Full Data as CSV"
        )

    with tab3:
        st.subheader("🔧 Operational Insight Panel")
        st.markdown("Analyze equipment and operator workflow issues based on imbalance indicators.")

        # Check for imbalance data
        has_imbalance = "imbalance_tier" in df.columns or "imbalance_score" in df.columns

        if has_imbalance and "imbalance_tier" in df.columns:
            # Filter for MEDIUM/HIGH imbalance
            concern_df = df[df["imbalance_tier"].str.upper().isin(["MEDIUM", "HIGH"])]

            if len(concern_df) > 0:
                st.warning(f"⚠️ **{len(concern_df)} locations showing equipment/operator concerns**")

                # Summary by imbalance tier
                col1, col2 = st.columns(2)

                with col1:
                    high_imbalance = len(concern_df[concern_df["imbalance_tier"].str.upper() == "HIGH"])
                    medium_imbalance = len(concern_df[concern_df["imbalance_tier"].str.upper() == "MEDIUM"])

                    st.markdown(f"""
                    <div class="warning-box">
                        <h4>⚡ Imbalance Summary</h4>
                        <ul>
                            <li><strong>HIGH Imbalance:</strong> {high_imbalance} locations</li>
                            <li><strong>MEDIUM Imbalance:</strong> {medium_imbalance} locations</li>
                        </ul>
                    </div>
                    """, unsafe_allow_html=True)

                with col2:
                    st.markdown("""
                    <div class="danger-box">
                        <h4>🔧 Recommended Actions</h4>
                        <ul>
                            <li>Equipment calibration check required</li>
                            <li>Operator workflow audit recommended</li>
                            <li>Biometric device maintenance inspection</li>
                            <li>Training refresh for enrollment operators</li>
                        </ul>
                    </div>
                    """, unsafe_allow_html=True)

                # Select location for detailed view
                st.markdown("### 📍 Location-wise Analysis")

                concern_df_display = concern_df.copy()
                if "pincode" in concern_df_display.columns:
                    concern_df_display["location"] = concern_df_display["district"].astype(str) + " - " + concern_df_display["pincode"].astype(str)
                else:
                    concern_df_display["location"] = concern_df_display["district"]

                selected_location = st.selectbox(
                    "Select Location for Detailed Analysis",
                    options=concern_df_display["location"].tolist(),
                    key="bio_location_selector"
                )

                if selected_location:
                    location_data = concern_df_display[concern_df_display["location"] == selected_location].iloc[0]

                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown(f"""
                        <div class="info-box">
                            <h4>📊 Location Metrics</h4>
                            <ul>
                                <li><strong>State:</strong> {location_data.get('state', 'N/A')}</li>
                                <li><strong>District:</strong> {location_data.get('district', 'N/A')}</li>
                                <li><strong>Pincode:</strong> {location_data.get('pincode', 'N/A')}</li>
                                <li><strong>Enrollment Total:</strong> {location_data.get('enrol_total', 'N/A'):,.0f if isinstance(location_data.get('enrol_total'), (int, float)) else 'N/A'}</li>
                                <li><strong>Biometric Total:</strong> {location_data.get('bio_total', 'N/A'):,.0f if isinstance(location_data.get('bio_total'), (int, float)) else 'N/A'}</li>
                                <li><strong>Capture Gap Ratio:</strong> {location_data.get('capture_gap_ratio', 'N/A'):.4f if isinstance(location_data.get('capture_gap_ratio'), (int, float)) else 'N/A'}</li>
                            </ul>
                        </div>
                        """, unsafe_allow_html=True)

                    with col2:
                        imbalance_tier = location_data.get('imbalance_tier', 'N/A')
                        tier_color = "red" if str(imbalance_tier).upper() == "HIGH" else "orange"

                        st.markdown(f"""
                        <div class="warning-box">
                            <h4>⚠️ Imbalance Status</h4>
                            <ul>
                                <li><strong>Imbalance Tier:</strong> <span style="color: {tier_color}; font-weight: bold;">{imbalance_tier}</span></li>
                                <li><strong>Imbalance Score:</strong> {location_data.get('imbalance_score', 'N/A'):.4f if isinstance(location_data.get('imbalance_score'), (int, float)) else 'N/A'}</li>
                            </ul>
                        </div>
                        """, unsafe_allow_html=True)

                    # Tags
                    tags = location_data.get("tags", [])
                    if tags:
                        st.markdown("### 🏷️ Issue Tags")
                        if isinstance(tags, list):
                            tag_html = " ".join([f'<span style="background-color: #e0e0e0; padding: 4px 8px; margin: 2px; border-radius: 4px; display: inline-block;">{tag}</span>' for tag in tags])
                            st.markdown(tag_html, unsafe_allow_html=True)

                    # Recommendations
                    st.markdown("### 📋 Recommendations")
                    recommendations = location_data.get("recommendations", [])
                    if recommendations:
                        if isinstance(recommendations, list):
                            for i, rec in enumerate(recommendations, 1):
                                st.markdown(f"""
                                <div style="background-color: #e7f3ff; padding: 10px; margin: 5px 0; border-radius: 5px; border-left: 4px solid #2196F3;">
                                    <strong>{i}.</strong> {rec}
                                </div>
                                """, unsafe_allow_html=True)
                        else:
                            st.markdown(f"- {recommendations}")
            else:
                st.success("✅ No significant equipment/operator workflow issues detected.")
        else:
            st.info("Imbalance tier data not available. Showing capture gap analysis.")

            # Show high capture gap locations instead
            if "capture_gap_tier" in df.columns:
                high_gap_df = df[df["capture_gap_tier"].str.upper() == "HIGH"]
                if len(high_gap_df) > 0:
                    st.warning(f"⚠️ {len(high_gap_df)} locations with HIGH capture gap ratio")
                    display_cols = ["state", "district", "pincode", "capture_gap_ratio", "capture_gap_tier"]
                    available = [c for c in display_cols if c in high_gap_df.columns]
                    st.dataframe(high_gap_df[available].head(10), use_container_width=True, hide_index=True)

except Exception as e:
    display_error_with_retry(str(e), "biometric_retry")

