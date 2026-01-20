"""
ML Forecast Page
================
Machine learning based migration predictions complementing rule-based alerts.
"""

import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.api_client import fetch_ml_alerts, fetch_migration_alerts
from components.charts import (
    create_horizontal_bar_chart,
    create_pie_donut_chart,
    create_comparison_bar_chart,
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

st.set_page_config(page_title="ML Forecast | Aadhaar Analytics", page_icon="🤖", layout="wide")
apply_custom_css()

st.title("🤖 ML-Based Migration Forecast")
st.markdown("Machine learning predictions for migration trends, complementing the rule-based URRDF early warning system.")

month = st.session_state.get("selected_month", "Latest")
month_param = None if month == "Latest" else month
search_text = st.session_state.get("search_text", "")
top_n = st.session_state.get("top_n", 10)

@st.cache_data(ttl=300)
def load_ml_data(month_param):
    return fetch_ml_alerts(month_param)

@st.cache_data(ttl=300)
def load_urrdf_data(month_param):
    return fetch_migration_alerts(month_param)

try:
    with st.spinner("Loading ML forecast data..."):
        ml_data = load_ml_data(month_param)

    df_ml = json_to_dataframe(ml_data)
    if df_ml.empty:
        st.warning("No ML forecast data available.")
        st.stop()

    st.info(f"📅 Data Month: **{ml_data.get('month', 'Unknown')}**")

    # Load URRDF for comparison
    df_urrdf = pd.DataFrame()
    try:
        urrdf_data = load_urrdf_data(month_param)
        df_urrdf = json_to_dataframe(urrdf_data)
    except:
        pass

    states = get_unique_states(df_ml)
    if states:
        selected_states = st.sidebar.multiselect("🗺️ Filter by State", options=states, default=[], key="ml_state_filter")
        if selected_states:
            df_ml = filter_dataframe(df_ml, states=selected_states)
            if not df_urrdf.empty:
                df_urrdf = filter_dataframe(df_urrdf, states=selected_states)

    if search_text:
        df_ml = filter_dataframe(df_ml, search_text=search_text)

    if df_ml.empty:
        st.warning("No data matches filters.")
        st.stop()

    st.markdown("---")

    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Districts Analyzed", len(df_ml))
    with col2:
        if "tier" in df_ml.columns:
            high_count = len(df_ml[df_ml["tier"].str.upper().isin(["HIGH", "SURGE"])])
            st.metric("High Risk Districts", high_count, delta_color="inverse")
    with col3:
        if "ml_inflow_score" in df_ml.columns:
            avg_score = df_ml["ml_inflow_score"].mean()
            st.metric("Avg ML Score", f"{avg_score:.2f}")
    with col4:
        if not df_urrdf.empty and "inflow_score" in df_urrdf.columns:
            urrdf_avg = df_urrdf["inflow_score"].mean()
            st.metric("Avg URRDF Score", f"{urrdf_avg:.2f}")

    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["📊 Charts", "📋 Data Table", "🔬 Model Insights"])

    with tab1:
        col1, col2 = st.columns([2, 1])

        with col1:
            if "ml_inflow_score" in df_ml.columns:
                fig_bar = create_horizontal_bar_chart(
                    df_ml, x_col="ml_inflow_score", y_col="district",
                    color_col="tier" if "tier" in df_ml.columns else None,
                    title=f"Top {top_n} Districts by ML Inflow Score",
                    x_label="ML Inflow Score", y_label="District", top_n=top_n, height=450
                )
                st.plotly_chart(fig_bar, use_container_width=True)

        with col2:
            if "tier" in df_ml.columns:
                tier_counts = df_ml["tier"].value_counts().reset_index()
                tier_counts.columns = ["tier", "count"]
                fig_pie = create_pie_donut_chart(
                    tier_counts, values_col="count", names_col="tier",
                    title="ML Tier Distribution",
                    color_map=TIER_DISTRIBUTION_COLORS.get("migration", {}), height=400
                )
                st.plotly_chart(fig_pie, use_container_width=True)

        # Comparison chart
        if not df_urrdf.empty and "inflow_score" in df_urrdf.columns and "ml_inflow_score" in df_ml.columns:
            st.markdown("---")
            st.subheader("📊 ML vs URRDF Score Comparison")

            merged = pd.merge(
                df_ml[["district", "ml_inflow_score"]],
                df_urrdf[["district", "inflow_score"]],
                on="district", how="inner"
            )

            if not merged.empty:
                fig_compare = create_comparison_bar_chart(
                    merged, category_col="district",
                    value_cols=["ml_inflow_score", "inflow_score"],
                    title="ML Score vs URRDF Score by District", height=400, top_n=top_n
                )
                st.plotly_chart(fig_compare, use_container_width=True)

    with tab2:
        df_display = df_ml.copy()
        if "recommendations" in df_display.columns:
            df_display["recommendations_text"] = df_display["recommendations"].apply(lambda x: format_list_field(x, compact=True))

        display_cols = ["state", "district", "month", "ml_inflow_score", "tier"]
        if "recommendations_text" in df_display.columns:
            display_cols.append("recommendations_text")
        available_cols = [c for c in display_cols if c in df_display.columns]

        sort_col = st.selectbox("Sort by", options=available_cols, index=available_cols.index("ml_inflow_score") if "ml_inflow_score" in available_cols else 0)
        df_sorted = df_display.sort_values(sort_col, ascending=False)

        st.dataframe(df_sorted[available_cols], use_container_width=True, hide_index=True, height=400)
        st.markdown("---")
        create_download_button(df_sorted, filename=f"ml_forecast_{ml_data.get('month', 'latest')}.csv")

    with tab3:
        st.subheader("🔬 Model Insights")

        st.markdown("""
        <div class="info-box">
            <h4>About ML-Based Forecasting</h4>
            <p>The ML model complements the rule-based URRDF system by:</p>
            <ul>
                <li>Learning complex patterns from historical migration data</li>
                <li>Incorporating seasonal and demographic factors</li>
                <li>Providing probabilistic predictions for future trends</li>
                <li>Identifying emerging patterns before they trigger rule-based alerts</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            <div class="success-box">
                <h4>✅ Model Advantages</h4>
                <ul>
                    <li>Early detection of migration shifts</li>
                    <li>Captures non-linear relationships</li>
                    <li>Adaptable to new patterns</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div class="warning-box">
                <h4>⚠️ Considerations</h4>
                <ul>
                    <li>Predictions are probabilistic estimates</li>
                    <li>Should be used with rule-based alerts</li>
                    <li>Regular retraining recommended</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

        if "tier" in df_ml.columns:
            high_risk = df_ml[df_ml["tier"].str.upper().isin(["HIGH", "SURGE"])]
            if len(high_risk) > 0:
                st.markdown("### 🚨 High-Risk Districts (ML Predicted)")
                for _, row in high_risk.head(5).iterrows():
                    recs = row.get("recommendations", [])
                    rec_text = ", ".join(recs[:2]) if isinstance(recs, list) and recs else "Monitor closely"
                    st.markdown(f"- **{row.get('district', 'Unknown')}** ({row.get('state', '')}) - Score: {row.get('ml_inflow_score', 0):.2f} | {rec_text}")

except Exception as e:
    display_error_with_retry(str(e), "ml_retry")

