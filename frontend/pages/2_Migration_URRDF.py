"""
Migration URRDF Page
====================
District-level migration inflow analysis with URRDF (Urban-Rural Redistribution Factor).
"""

import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.api_client import fetch_migration_alerts
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
    page_title="Migration URRDF | Aadhaar Analytics",
    page_icon="🚚",
    layout="wide"
)

apply_custom_css()

st.title("🚚 Migration Analysis (URRDF)")
st.markdown("""
Urban-Rural Redistribution Factor analysis for tracking population movement patterns 
and predicting migration pressure at district level.
""")

# Get filter values from session state
month = st.session_state.get("selected_month", "Latest")
month_param = None if month == "Latest" else month
search_text = st.session_state.get("search_text", "")
top_n = st.session_state.get("top_n", 10)

# Load data
@st.cache_data(ttl=300)
def load_migration_data(month_param):
    return fetch_migration_alerts(month_param)

try:
    with st.spinner("Loading migration data..."):
        data = load_migration_data(month_param)

    df = json_to_dataframe(data)

    if df.empty:
        st.warning("No migration data available for the selected period.")
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
            key="migration_state_filter"
        )
        if selected_states:
            df = filter_dataframe(df, states=selected_states)

    # Apply search filter
    if search_text:
        df = filter_dataframe(df, search_text=search_text)

    if df.empty:
        st.warning("No data matches the current filters.")
        st.stop()

    st.markdown("---")

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Districts", len(df))

    with col2:
        if "level" in df.columns:
            surge_count = len(df[df["level"].str.upper() == "SURGE"])
            st.metric("SURGE Districts", surge_count, delta_color="inverse")

    with col3:
        if "inflow_score" in df.columns:
            avg_score = df["inflow_score"].mean()
            st.metric("Avg Inflow Score", f"{avg_score:.2f}")

    with col4:
        if "level" in df.columns:
            heavy_count = len(df[df["level"].str.upper() == "HEAVY"])
            st.metric("HEAVY Districts", heavy_count)

    st.markdown("---")

    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["📊 Charts", "📋 Data Table", "💡 Policy Suggestions"])

    with tab1:
        # Chart 1: Horizontal bar chart - Top districts by inflow_score
        st.subheader("📊 Top Districts by Inflow Score")

        if "inflow_score" in df.columns:
            col1, col2 = st.columns([2, 1])

            with col1:
                fig_bar = create_horizontal_bar_chart(
                    df,
                    x_col="inflow_score",
                    y_col="district",
                    color_col="level" if "level" in df.columns else None,
                    title=f"Top {top_n} Districts by Inflow Score",
                    x_label="Inflow Score",
                    y_label="District",
                    top_n=top_n,
                    height=450
                )
                st.plotly_chart(fig_bar, use_container_width=True)

            with col2:
                # Pie/Donut chart - Level distribution
                if "level" in df.columns:
                    level_counts = df["level"].value_counts().reset_index()
                    level_counts.columns = ["level", "count"]

                    fig_pie = create_pie_donut_chart(
                        level_counts,
                        values_col="count",
                        names_col="level",
                        title="Distribution of Levels",
                        color_map=TIER_DISTRIBUTION_COLORS["migration"],
                        height=400
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)

        st.markdown("---")

        # Chart 3: Scatter plot
        st.subheader("🔵 Inflow Score Distribution")

        if "inflow_score" in df.columns:
            # Create a numeric index for x-axis
            df_scatter = df.copy()
            df_scatter["district_index"] = range(len(df_scatter))

            fig_scatter = create_scatter_plot(
                df_scatter,
                x_col="district_index",
                y_col="inflow_score",
                color_col="level" if "level" in df_scatter.columns else None,
                size_col="inflow_score",
                hover_name="district",
                title="Inflow Score by District (marker size = score)",
                x_label="District Index",
                y_label="Inflow Score",
                height=400
            )
            st.plotly_chart(fig_scatter, use_container_width=True)

    with tab2:
        st.subheader("📋 Migration Alerts Data")

        # Prepare display DataFrame
        df_display = df.copy()

        # Format list columns for display
        if "recommendations" in df_display.columns:
            df_display["recommendations_text"] = df_display["recommendations"].apply(
                lambda x: format_list_field(x, compact=True)
            )

        if "predicted_pressure" in df_display.columns:
            df_display["predicted_pressure_text"] = df_display["predicted_pressure"].apply(
                lambda x: format_list_field(x, compact=True)
            )

        # Select columns for display
        display_cols = ["state", "district", "month", "inflow_score", "level"]
        if "recommendations_text" in df_display.columns:
            display_cols.append("recommendations_text")

        available_cols = [c for c in display_cols if c in df_display.columns]

        # Sorting options
        sort_col = st.selectbox(
            "Sort by",
            options=available_cols,
            index=available_cols.index("inflow_score") if "inflow_score" in available_cols else 0
        )
        sort_order = st.radio("Order", ["Descending", "Ascending"], horizontal=True)

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
            filename=f"migration_alerts_{data.get('month', 'latest')}.csv",
            label="📥 Download Full Data as CSV"
        )

    with tab3:
        st.subheader("💡 Policy Suggestion Generator")
        st.markdown("Select a district to view detailed recommendations and predicted pressure analysis.")

        # District selector
        district_options = df["district"].unique().tolist()
        selected_district = st.selectbox(
            "Select District",
            options=district_options,
            key="policy_district_selector"
        )

        if selected_district:
            district_data = df[df["district"] == selected_district].iloc[0]

            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"""
                <div class="info-box">
                    <h4>📍 District Profile</h4>
                    <ul>
                        <li><strong>State:</strong> {district_data.get('state', 'N/A')}</li>
                        <li><strong>District:</strong> {district_data.get('district', 'N/A')}</li>
                        <li><strong>Month:</strong> {district_data.get('month', 'N/A')}</li>
                        <li><strong>Inflow Score:</strong> {district_data.get('inflow_score', 'N/A'):.2f if isinstance(district_data.get('inflow_score'), (int, float)) else 'N/A'}</li>
                        <li><strong>Level:</strong> <span style="color: {'red' if district_data.get('level', '').upper() == 'SURGE' else 'orange' if district_data.get('level', '').upper() == 'HEAVY' else 'green'}; font-weight: bold;">{district_data.get('level', 'N/A')}</span></li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                # Predicted Pressure
                predicted_pressure = district_data.get("predicted_pressure", [])
                if predicted_pressure:
                    st.markdown("""
                    <div class="warning-box">
                        <h4>📈 Predicted Pressure</h4>
                    </div>
                    """, unsafe_allow_html=True)
                    if isinstance(predicted_pressure, list):
                        for item in predicted_pressure:
                            st.markdown(f"- {item}")
                    else:
                        st.markdown(f"- {predicted_pressure}")
                else:
                    st.info("No predicted pressure data available for this district.")

            # Recommendations
            st.markdown("### 📋 Recommendations")
            recommendations = district_data.get("recommendations", [])
            if recommendations:
                if isinstance(recommendations, list):
                    for i, rec in enumerate(recommendations, 1):
                        st.markdown(f"""
                        <div style="background-color: #f0f2f6; padding: 10px; margin: 5px 0; border-radius: 5px; border-left: 4px solid #4CAF50;">
                            <strong>{i}.</strong> {rec}
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown(f"- {recommendations}")
            else:
                st.info("No specific recommendations available for this district.")

            # Action priority based on level
            level = district_data.get("level", "").upper()
            if level == "SURGE":
                st.error("""
                🚨 **URGENT ACTION REQUIRED**
                
                This district is experiencing SURGE level migration. Immediate interventions recommended:
                - Deploy additional mobile enrollment units
                - Coordinate with state migration authorities
                - Prepare infrastructure for increased demand
                - Monitor daily trends closely
                """)
            elif level == "HEAVY":
                st.warning("""
                ⚠️ **ELEVATED ATTENTION NEEDED**
                
                This district shows HEAVY migration activity. Proactive measures suggested:
                - Increase enrollment center capacity
                - Review resource allocation
                - Establish communication with neighboring districts
                """)
            else:
                st.success("""
                ✅ **NORMAL OPERATIONS**
                
                This district is operating within normal parameters. Continue standard monitoring.
                """)

except Exception as e:
    display_error_with_retry(str(e), "migration_retry")

