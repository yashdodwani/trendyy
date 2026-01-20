"""
Lost Generation FAFI Page
=========================
FAFI (First Aadhaar First Identity) analysis for identifying child enrollment gaps.
"""

import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.api_client import fetch_lost_generation_alerts
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

st.set_page_config(page_title="Lost Generation FAFI | Aadhaar Analytics", page_icon="👶", layout="wide")
apply_custom_css()

st.title("👶 Lost Generation Analysis (FAFI)")
st.markdown("First Aadhaar First Identity analysis for identifying child enrollment gaps across districts.")

month = st.session_state.get("selected_month", "Latest")
month_param = None if month == "Latest" else month
search_text = st.session_state.get("search_text", "")
top_n = st.session_state.get("top_n", 10)

@st.cache_data(ttl=300)
def load_data(month_param):
    return fetch_lost_generation_alerts(month_param)

try:
    with st.spinner("Loading lost generation data..."):
        data = load_data(month_param)

    df = json_to_dataframe(data)
    if df.empty:
        st.warning("No lost generation data available.")
        st.stop()

    st.info(f"📅 Data Month: **{data.get('month', 'Unknown')}**")

    states = get_unique_states(df)
    if states:
        selected_states = st.sidebar.multiselect("🗺️ Filter by State", options=states, default=[], key="fafi_state_filter")
        if selected_states:
            df = filter_dataframe(df, states=selected_states)

    if "tier" in df.columns:
        tier_options = df["tier"].unique().tolist()
        selected_tiers = st.sidebar.multiselect("⚡ Filter by Tier", options=tier_options, default=[], key="fafi_tier_filter")
        if selected_tiers:
            df = df[df["tier"].isin(selected_tiers)]

    if search_text:
        df = filter_dataframe(df, search_text=search_text)

    if df.empty:
        st.warning("No data matches the current filters.")
        st.stop()

    st.markdown("---")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Districts", len(df))
    with col2:
        if "tier" in df.columns:
            high_count = len(df[df["tier"].str.upper() == "HIGH"])
            st.metric("HIGH FAFI Districts", high_count, delta_color="inverse")
    with col3:
        if "fafi_ratio" in df.columns:
            avg_ratio = df["fafi_ratio"].mean()
            st.metric("Avg FAFI Ratio", f"{avg_ratio:.3f}")
    with col4:
        if "fafi_value" in df.columns:
            total_fafi = df["fafi_value"].sum()
            st.metric("Total FAFI Value", f"{total_fafi:,.0f}")

    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["📊 Charts", "📋 Data Table", "🎯 Intervention Planner"])

    with tab1:
        col1, col2 = st.columns([2, 1])
        with col1:
            if "fafi_ratio" in df.columns:
                fig_bar = create_horizontal_bar_chart(
                    df, x_col="fafi_ratio", y_col="district",
                    color_col="tier" if "tier" in df.columns else None,
                    title=f"Top {top_n} Districts by FAFI Ratio",
                    x_label="FAFI Ratio", y_label="District", top_n=top_n, height=450
                )
                st.plotly_chart(fig_bar, use_container_width=True)

        with col2:
            if "tier" in df.columns:
                tier_counts = df["tier"].value_counts().reset_index()
                tier_counts.columns = ["tier", "count"]
                fig_pie = create_pie_donut_chart(
                    tier_counts, values_col="count", names_col="tier",
                    title="FAFI Tier Distribution",
                    color_map=TIER_DISTRIBUTION_COLORS["fafi"], height=400
                )
                st.plotly_chart(fig_pie, use_container_width=True)

        st.markdown("---")
        st.subheader("🔵 Enrollment Gap Analysis")

        if "enrol_age_0_5" in df.columns and "bio_age_5_17" in df.columns:
            fig_scatter = create_scatter_plot(
                df, x_col="enrol_age_0_5", y_col="bio_age_5_17",
                color_col="tier" if "tier" in df.columns else None,
                hover_name="district",
                title="Enrollment (0-5) vs Biometric (5-17) - Gap Highlighted",
                x_label="Enrollment Age 0-5", y_label="Biometric Age 5-17", height=400
            )
            st.plotly_chart(fig_scatter, use_container_width=True)

    with tab2:
        df_display = df.copy()
        if "recommendations" in df_display.columns:
            df_display["recommendations_text"] = df_display["recommendations"].apply(lambda x: format_list_field(x, compact=True))

        display_cols = ["state", "district", "month", "enrol_age_0_5", "bio_age_5_17", "fafi_value", "fafi_ratio", "tier", "impact_statement"]
        if "recommendations_text" in df_display.columns:
            display_cols.append("recommendations_text")
        available_cols = [c for c in display_cols if c in df_display.columns]

        sort_col = st.selectbox("Sort by", options=available_cols, index=available_cols.index("fafi_ratio") if "fafi_ratio" in available_cols else 0)
        sort_order = st.radio("Order", ["Descending", "Ascending"], horizontal=True, key="fafi_sort")
        df_sorted = df_display.sort_values(sort_col, ascending=(sort_order == "Ascending"))

        st.dataframe(df_sorted[available_cols], use_container_width=True, hide_index=True, height=400)
        st.markdown("---")
        create_download_button(df_sorted, filename=f"lost_generation_{data.get('month', 'latest')}.csv")

    with tab3:
        st.subheader("🎯 Intervention Planner")

        if "tier" in df.columns:
            priority_df = df[df["tier"].str.upper().isin(["HIGH", "MEDIUM"])]

            if len(priority_df) > 0:
                st.warning(f"⚠️ **{len(priority_df)} districts require intervention**")

                selected_district = st.selectbox("Select District", options=priority_df["district"].tolist(), key="fafi_district")

                if selected_district:
                    district_data = priority_df[priority_df["district"] == selected_district].iloc[0]
                    tier = district_data.get("tier", "").upper()

                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"""
                        <div class="{'danger-box' if tier == 'HIGH' else 'warning-box'}">
                            <h4>📍 District Profile</h4>
                            <ul>
                                <li><strong>State:</strong> {district_data.get('state', 'N/A')}</li>
                                <li><strong>District:</strong> {district_data.get('district', 'N/A')}</li>
                                <li><strong>FAFI Ratio:</strong> {district_data.get('fafi_ratio', 0):.3f}</li>
                                <li><strong>Tier:</strong> <span style="color: {'red' if tier == 'HIGH' else 'orange'}; font-weight: bold;">{tier}</span></li>
                            </ul>
                        </div>
                        """, unsafe_allow_html=True)

                    with col2:
                        impact = district_data.get("impact_statement", "No impact statement available.")
                        st.markdown(f"""
                        <div class="info-box">
                            <h4>📢 Impact Statement</h4>
                            <p>{impact}</p>
                        </div>
                        """, unsafe_allow_html=True)

                    st.markdown("### 📋 Recommended Interventions")

                    if tier == "HIGH":
                        st.error("**HIGH PRIORITY ACTIONS:**")
                        actions = ["Deploy mobile enrollment camps in underserved areas", "Partner with schools for enrollment drives",
                                   "Engage community health workers (ASHA/ANM)", "Set up temporary enrollment centers"]
                    else:
                        st.warning("**MEDIUM PRIORITY ACTIONS:**")
                        actions = ["Increase awareness campaigns", "Coordinate with local panchayats",
                                   "Schedule periodic enrollment camps", "Monitor progress monthly"]

                    for action in actions:
                        st.checkbox(action, key=f"action_{action[:20]}")

                    recs = district_data.get("recommendations", [])
                    if recs and isinstance(recs, list):
                        st.markdown("### 💡 System Recommendations")
                        for rec in recs:
                            st.markdown(f"- {rec}")
            else:
                st.success("✅ No districts requiring immediate intervention.")

except Exception as e:
    display_error_with_retry(str(e), "fafi_retry")

