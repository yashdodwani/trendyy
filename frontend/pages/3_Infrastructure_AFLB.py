"""
Infrastructure AFLB Page
========================
Facility load and infrastructure stress analysis (AFLB - Aadhaar Facility Load Balancer).
"""

import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.api_client import fetch_infrastructure_alerts
from components.charts import (
    create_horizontal_bar_chart,
    create_pie_donut_chart,
    create_scatter_plot,
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
    page_title="Infrastructure AFLB | Aadhaar Analytics",
    page_icon="🏗️",
    layout="wide"
)

apply_custom_css()

st.title("🏗️ Infrastructure Analysis (AFLB)")
st.markdown("""
Aadhaar Facility Load Balancer analytics for monitoring facility stress and 
infrastructure capacity across enrollment centers.
""")

# Get filter values from session state
month = st.session_state.get("selected_month", "Latest")
month_param = None if month == "Latest" else month
search_text = st.session_state.get("search_text", "")
top_n = st.session_state.get("top_n", 10)

# Load data
@st.cache_data(ttl=300)
def load_infrastructure_data(month_param):
    return fetch_infrastructure_alerts(month_param)

try:
    with st.spinner("Loading infrastructure data..."):
        data = load_infrastructure_data(month_param)

    df = json_to_dataframe(data)

    if df.empty:
        st.warning("No infrastructure data available for the selected period.")
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
            key="infra_state_filter"
        )
        if selected_states:
            df = filter_dataframe(df, states=selected_states)

    # Tier filter
    if "tier" in df.columns:
        tier_options = df["tier"].unique().tolist()
        selected_tiers = st.sidebar.multiselect(
            "⚡ Filter by Tier",
            options=tier_options,
            default=[],
            key="infra_tier_filter"
        )
        if selected_tiers:
            df = df[df["tier"].isin(selected_tiers)]

    # Apply search filter
    if search_text:
        df = filter_dataframe(df, search_text=search_text, search_columns=["district", "pincode"])

    if df.empty:
        st.warning("No data matches the current filters.")
        st.stop()

    st.markdown("---")

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Pincodes", len(df))

    with col2:
        if "tier" in df.columns:
            critical_count = len(df[df["tier"].str.upper() == "CRITICAL"])
            st.metric("CRITICAL Pincodes", critical_count, delta_color="inverse")

    with col3:
        if "stress_score" in df.columns:
            avg_stress = df["stress_score"].mean()
            st.metric("Avg Stress Score", f"{avg_stress:.2f}")

    with col4:
        if "total_load" in df.columns:
            total_load = df["total_load"].sum()
            st.metric("Total Load", f"{total_load:,.0f}")

    st.markdown("---")

    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["📊 Charts", "📋 Data Table", "🏥 Facility Planning"])

    with tab1:
        col1, col2 = st.columns([2, 1])

        with col1:
            # Chart 1: Bar chart - Top pincodes by stress_score
            st.subheader("📊 Top Pincodes by Stress Score")

            if "stress_score" in df.columns:
                # Create display label
                df_chart = df.copy()
                if "pincode" in df_chart.columns:
                    df_chart["location"] = df_chart["district"].astype(str) + " - " + df_chart["pincode"].astype(str)
                else:
                    df_chart["location"] = df_chart["district"]

                fig_bar = create_horizontal_bar_chart(
                    df_chart,
                    x_col="stress_score",
                    y_col="location",
                    color_col="tier" if "tier" in df_chart.columns else None,
                    title=f"Top {top_n} Locations by Stress Score",
                    x_label="Stress Score",
                    y_label="Location",
                    top_n=top_n,
                    height=450
                )
                st.plotly_chart(fig_bar, use_container_width=True)

        with col2:
            # Pie/Donut chart - Tier distribution
            if "tier" in df.columns:
                st.subheader("📈 Tier Distribution")
                tier_counts = df["tier"].value_counts().reset_index()
                tier_counts.columns = ["tier", "count"]

                fig_pie = create_pie_donut_chart(
                    tier_counts,
                    values_col="count",
                    names_col="tier",
                    title="Distribution of Infrastructure Tiers",
                    color_map=TIER_DISTRIBUTION_COLORS["infrastructure"],
                    height=400
                )
                st.plotly_chart(fig_pie, use_container_width=True)

        st.markdown("---")

        # Chart 2: Scatter plot - total_load vs stress_score
        st.subheader("🔵 Load vs Stress Analysis")

        if "stress_score" in df.columns and "total_load" in df.columns:
            df_scatter = df.copy()
            if "pincode" in df_scatter.columns:
                df_scatter["location"] = df_scatter["district"].astype(str) + " - " + df_scatter["pincode"].astype(str)
            else:
                df_scatter["location"] = df_scatter["district"]

            fig_scatter = create_scatter_plot(
                df_scatter,
                x_col="total_load",
                y_col="stress_score",
                color_col="tier" if "tier" in df_scatter.columns else None,
                hover_name="location",
                title="Total Load vs Stress Score (dotted marker style)",
                x_label="Total Load",
                y_label="Stress Score",
                height=400,
                marker_style="dot"
            )
            st.plotly_chart(fig_scatter, use_container_width=True)

    with tab2:
        st.subheader("📋 Infrastructure Alerts Data")

        # Prepare display DataFrame
        df_display = df.copy()

        # Format list columns for display
        if "recommendations" in df_display.columns:
            df_display["recommendations_text"] = df_display["recommendations"].apply(
                lambda x: format_list_field(x, compact=True)
            )

        # Select columns for display
        display_cols = ["state", "district", "pincode", "month", "total_load", "stress_score", "tier"]
        if "recommendations_text" in df_display.columns:
            display_cols.append("recommendations_text")

        available_cols = [c for c in display_cols if c in df_display.columns]

        # Sorting options
        col1, col2 = st.columns([1, 1])
        with col1:
            sort_col = st.selectbox(
                "Sort by",
                options=available_cols,
                index=available_cols.index("stress_score") if "stress_score" in available_cols else 0,
                key="infra_sort_col"
            )
        with col2:
            sort_order = st.radio("Order", ["Descending", "Ascending"], horizontal=True, key="infra_sort_order")

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
            filename=f"infrastructure_alerts_{data.get('month', 'latest')}.csv",
            label="📥 Download Full Data as CSV"
        )

    with tab3:
        st.subheader("🏥 Facility Planning Panel")
        st.markdown("Critical infrastructure planning checklist for high-stress facilities.")

        # Filter for CRITICAL tier
        if "tier" in df.columns:
            critical_df = df[df["tier"].str.upper() == "CRITICAL"]

            if len(critical_df) > 0:
                st.error(f"⚠️ **{len(critical_df)} CRITICAL facilities require immediate attention**")

                # Select location
                critical_df_display = critical_df.copy()
                if "pincode" in critical_df_display.columns:
                    critical_df_display["location"] = critical_df_display["district"].astype(str) + " - " + critical_df_display["pincode"].astype(str)
                else:
                    critical_df_display["location"] = critical_df_display["district"]

                selected_location = st.selectbox(
                    "Select CRITICAL Location",
                    options=critical_df_display["location"].tolist(),
                    key="facility_location_selector"
                )

                if selected_location:
                    location_data = critical_df_display[critical_df_display["location"] == selected_location].iloc[0]

                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown(f"""
                        <div class="danger-box">
                            <h4>📍 Location Details</h4>
                            <ul>
                                <li><strong>State:</strong> {location_data.get('state', 'N/A')}</li>
                                <li><strong>District:</strong> {location_data.get('district', 'N/A')}</li>
                                <li><strong>Pincode:</strong> {location_data.get('pincode', 'N/A')}</li>
                                <li><strong>Total Load:</strong> {location_data.get('total_load', 'N/A'):,.0f if isinstance(location_data.get('total_load'), (int, float)) else 'N/A'}</li>
                                <li><strong>Stress Score:</strong> {location_data.get('stress_score', 'N/A'):.2f if isinstance(location_data.get('stress_score'), (int, float)) else 'N/A'}</li>
                                <li><strong>Tier:</strong> <span style="color: red; font-weight: bold;">CRITICAL</span></li>
                            </ul>
                        </div>
                        """, unsafe_allow_html=True)

                    with col2:
                        st.markdown("""
                        <div class="warning-box">
                            <h4>✅ Facility Planning Checklist</h4>
                        </div>
                        """, unsafe_allow_html=True)

                        # Interactive checklist
                        st.checkbox("💧 Water supply availability confirmed", key="check_water")
                        st.checkbox("🏠 Adequate shade/shelter for waiting area", key="check_shade")
                        st.checkbox("🎫 Token management system deployed", key="check_token")
                        st.checkbox("🏥 Medical first-aid station ready", key="check_medical")
                        st.checkbox("🔌 Power backup (UPS/Generator) operational", key="check_power")
                        st.checkbox("📶 Network connectivity verified", key="check_network")
                        st.checkbox("👥 Additional staff allocated", key="check_staff")
                        st.checkbox("📋 Queue management protocol active", key="check_queue")

                    # Recommendations
                    st.markdown("### 📋 System Recommendations")
                    recommendations = location_data.get("recommendations", [])
                    if recommendations:
                        if isinstance(recommendations, list):
                            for i, rec in enumerate(recommendations, 1):
                                st.markdown(f"""
                                <div style="background-color: #fff3cd; padding: 10px; margin: 5px 0; border-radius: 5px; border-left: 4px solid #ffc107;">
                                    <strong>{i}.</strong> {rec}
                                </div>
                                """, unsafe_allow_html=True)
                        else:
                            st.markdown(f"- {recommendations}")
                    else:
                        st.info("No specific recommendations available.")
            else:
                st.success("✅ No CRITICAL facilities currently. All locations operating within acceptable parameters.")

                # Show HIGH tier if no CRITICAL
                high_df = df[df["tier"].str.upper() == "HIGH"]
                if len(high_df) > 0:
                    st.warning(f"⚠️ {len(high_df)} facilities at HIGH stress level - monitor closely")

                    with st.expander("View HIGH stress locations"):
                        display_cols = ["state", "district", "pincode", "stress_score", "total_load"]
                        available = [c for c in display_cols if c in high_df.columns]
                        st.dataframe(high_df[available], use_container_width=True, hide_index=True)
        else:
            st.info("Tier information not available in the data.")

except Exception as e:
    display_error_with_retry(str(e), "infrastructure_retry")

