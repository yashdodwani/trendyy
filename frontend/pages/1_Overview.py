"""
Overview Page - Executive Summary Dashboard
===========================================
Displays KPIs, tier distributions, and cross-module insights.
"""

import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.api_client import (
    fetch_migration_alerts,
    fetch_infrastructure_alerts,
    fetch_biometric_alerts,
    fetch_lost_generation_alerts,
)
from components.charts import create_pie_donut_chart
from components.theme import apply_custom_css, TIER_DISTRIBUTION_COLORS
from utils.helpers import (
    json_to_dataframe,
    filter_dataframe,
    count_by_tier,
    display_error_with_retry,
)

# Page config
st.set_page_config(
    page_title="Overview | Aadhaar Analytics",
    page_icon="📈",
    layout="wide"
)

apply_custom_css()

st.title("📈 Overview Dashboard")
st.markdown("Executive summary of all alert modules with key performance indicators.")


def load_all_data():
    """Load data from all endpoints."""
    month = st.session_state.get("selected_month", "Latest")
    month_param = None if month == "Latest" else month

    data = {}
    errors = []

    # Load Migration data
    try:
        data["migration"] = fetch_migration_alerts(month_param)
    except Exception as e:
        errors.append(f"Migration: {str(e)}")
        data["migration"] = {"alerts": []}

    # Load Infrastructure data
    try:
        data["infrastructure"] = fetch_infrastructure_alerts(month_param)
    except Exception as e:
        errors.append(f"Infrastructure: {str(e)}")
        data["infrastructure"] = {"alerts": []}

    # Load Biometric data
    try:
        data["biometric"] = fetch_biometric_alerts(month_param)
    except Exception as e:
        errors.append(f"Biometric: {str(e)}")
        data["biometric"] = {"alerts": []}

    # Load Lost Generation data
    try:
        data["lost_generation"] = fetch_lost_generation_alerts(month_param)
    except Exception as e:
        errors.append(f"Lost Generation: {str(e)}")
        data["lost_generation"] = {"alerts": []}

    return data, errors


# Load all data
with st.spinner("Loading data from all modules..."):
    all_data, load_errors = load_all_data()

# Show any loading errors
if load_errors:
    with st.expander("⚠️ Some data could not be loaded", expanded=False):
        for error in load_errors:
            st.warning(error)

# Convert to DataFrames
df_migration = json_to_dataframe(all_data["migration"])
df_infrastructure = json_to_dataframe(all_data["infrastructure"])
df_biometric = json_to_dataframe(all_data["biometric"])
df_lost_gen = json_to_dataframe(all_data["lost_generation"])

# Apply filters
search_text = st.session_state.get("search_text", "")
if search_text:
    df_migration = filter_dataframe(df_migration, search_text=search_text)
    df_infrastructure = filter_dataframe(df_infrastructure, search_text=search_text, search_columns=["district", "pincode"])
    df_biometric = filter_dataframe(df_biometric, search_text=search_text, search_columns=["district", "pincode"])
    df_lost_gen = filter_dataframe(df_lost_gen, search_text=search_text)

st.markdown("---")

# KPI Cards Section
st.subheader("🎯 Key Performance Indicators")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    total_alerts = len(df_migration) + len(df_infrastructure) + len(df_biometric) + len(df_lost_gen)
    st.metric(
        label="📊 Total Alerts",
        value=total_alerts,
        help="Total alerts across all modules"
    )

with col2:
    surge_count = count_by_tier(df_migration, "level", "SURGE")
    st.metric(
        label="🚨 SURGE Districts",
        value=surge_count,
        delta=f"{(surge_count/len(df_migration)*100):.1f}%" if len(df_migration) > 0 else "0%",
        delta_color="inverse",
        help="Districts with SURGE level migration"
    )

with col3:
    critical_count = count_by_tier(df_infrastructure, "tier", "CRITICAL")
    st.metric(
        label="⚠️ CRITICAL Pincodes",
        value=critical_count,
        delta=f"{(critical_count/len(df_infrastructure)*100):.1f}%" if len(df_infrastructure) > 0 else "0%",
        delta_color="inverse",
        help="Pincodes with CRITICAL infrastructure stress"
    )

with col4:
    high_fafi = count_by_tier(df_lost_gen, "tier", "HIGH")
    st.metric(
        label="👶 HIGH FAFI Districts",
        value=high_fafi,
        delta=f"{(high_fafi/len(df_lost_gen)*100):.1f}%" if len(df_lost_gen) > 0 else "0%",
        delta_color="inverse",
        help="Districts with HIGH FAFI (child enrollment gap)"
    )

with col5:
    high_gap = count_by_tier(df_biometric, "capture_gap_tier", "HIGH")
    st.metric(
        label="🧬 HIGH Capture Gap",
        value=high_gap,
        delta=f"{(high_gap/len(df_biometric)*100):.1f}%" if len(df_biometric) > 0 else "0%",
        delta_color="inverse",
        help="Pincodes with HIGH capture gap ratio"
    )

st.markdown("---")

# Tier Distribution Charts
st.subheader("📊 Tier Distributions")

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Migration Levels")
    if not df_migration.empty and "level" in df_migration.columns:
        # Create count DataFrame
        level_counts = df_migration["level"].value_counts().reset_index()
        level_counts.columns = ["level", "count"]

        fig = create_pie_donut_chart(
            level_counts,
            values_col="count",
            names_col="level",
            title="Distribution of Migration Levels",
            color_map=TIER_DISTRIBUTION_COLORS["migration"]
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No migration data available")

with col2:
    st.markdown("#### Infrastructure Tiers")
    if not df_infrastructure.empty and "tier" in df_infrastructure.columns:
        tier_counts = df_infrastructure["tier"].value_counts().reset_index()
        tier_counts.columns = ["tier", "count"]

        fig = create_pie_donut_chart(
            tier_counts,
            values_col="count",
            names_col="tier",
            title="Distribution of Infrastructure Tiers",
            color_map=TIER_DISTRIBUTION_COLORS["infrastructure"]
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No infrastructure data available")

col3, col4 = st.columns(2)

with col3:
    st.markdown("#### Biometric Capture Gap Tiers")
    if not df_biometric.empty and "capture_gap_tier" in df_biometric.columns:
        bio_counts = df_biometric["capture_gap_tier"].value_counts().reset_index()
        bio_counts.columns = ["capture_gap_tier", "count"]

        fig = create_pie_donut_chart(
            bio_counts,
            values_col="count",
            names_col="capture_gap_tier",
            title="Distribution of Capture Gap Tiers",
            color_map=TIER_DISTRIBUTION_COLORS["biometric"]
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No biometric data available")

with col4:
    st.markdown("#### FAFI Tiers (Lost Generation)")
    if not df_lost_gen.empty and "tier" in df_lost_gen.columns:
        fafi_counts = df_lost_gen["tier"].value_counts().reset_index()
        fafi_counts.columns = ["tier", "count"]

        fig = create_pie_donut_chart(
            fafi_counts,
            values_col="count",
            names_col="tier",
            title="Distribution of FAFI Tiers",
            color_map=TIER_DISTRIBUTION_COLORS["fafi"]
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No lost generation data available")

st.markdown("---")

# Top 5 Tables Preview
st.subheader("📋 Top 5 Alerts by Module")

tab1, tab2, tab3, tab4 = st.tabs(["🚚 Migration", "🏗️ Infrastructure", "🧬 Biometric", "👶 Lost Generation"])

with tab1:
    if not df_migration.empty:
        display_cols = ["state", "district", "month", "inflow_score", "level"]
        available_cols = [c for c in display_cols if c in df_migration.columns]
        if "inflow_score" in df_migration.columns:
            st.dataframe(
                df_migration.nlargest(5, "inflow_score")[available_cols],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.dataframe(df_migration.head(5)[available_cols], use_container_width=True, hide_index=True)
    else:
        st.info("No migration alerts available")

with tab2:
    if not df_infrastructure.empty:
        display_cols = ["state", "district", "pincode", "month", "stress_score", "tier"]
        available_cols = [c for c in display_cols if c in df_infrastructure.columns]
        if "stress_score" in df_infrastructure.columns:
            st.dataframe(
                df_infrastructure.nlargest(5, "stress_score")[available_cols],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.dataframe(df_infrastructure.head(5)[available_cols], use_container_width=True, hide_index=True)
    else:
        st.info("No infrastructure alerts available")

with tab3:
    if not df_biometric.empty:
        display_cols = ["state", "district", "pincode", "month", "capture_gap_ratio", "capture_gap_tier"]
        available_cols = [c for c in display_cols if c in df_biometric.columns]
        if "capture_gap_ratio" in df_biometric.columns:
            st.dataframe(
                df_biometric.nlargest(5, "capture_gap_ratio")[available_cols],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.dataframe(df_biometric.head(5)[available_cols], use_container_width=True, hide_index=True)
    else:
        st.info("No biometric alerts available")

with tab4:
    if not df_lost_gen.empty:
        display_cols = ["state", "district", "month", "fafi_ratio", "tier"]
        available_cols = [c for c in display_cols if c in df_lost_gen.columns]
        if "fafi_ratio" in df_lost_gen.columns:
            st.dataframe(
                df_lost_gen.nlargest(5, "fafi_ratio")[available_cols],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.dataframe(df_lost_gen.head(5)[available_cols], use_container_width=True, hide_index=True)
    else:
        st.info("No lost generation alerts available")

# Summary insights
st.markdown("---")
st.subheader("💡 Quick Insights")

insight_cols = st.columns(2)

with insight_cols[0]:
    st.markdown("""
    <div class="info-box">
        <h4>📊 Data Summary</h4>
        <ul>
            <li><strong>Migration Alerts:</strong> {} districts monitored</li>
            <li><strong>Infrastructure Alerts:</strong> {} pincodes tracked</li>
            <li><strong>Biometric Alerts:</strong> {} records analyzed</li>
            <li><strong>Lost Generation:</strong> {} districts assessed</li>
        </ul>
    </div>
    """.format(len(df_migration), len(df_infrastructure), len(df_biometric), len(df_lost_gen)),
    unsafe_allow_html=True)

with insight_cols[1]:
    # Generate dynamic insights
    insights = []
    if surge_count > 0:
        insights.append(f"🚨 {surge_count} district(s) showing SURGE level migration - immediate attention required")
    if critical_count > 0:
        insights.append(f"⚠️ {critical_count} pincode(s) with CRITICAL infrastructure stress")
    if high_fafi > 0:
        insights.append(f"👶 {high_fafi} district(s) with HIGH child enrollment gaps (FAFI)")
    if high_gap > 0:
        insights.append(f"🧬 {high_gap} pincode(s) with HIGH biometric capture gaps")

    if not insights:
        insights.append("✅ All systems operating within normal parameters")

    st.markdown("""
    <div class="warning-box">
        <h4>⚡ Priority Actions</h4>
        <ul>
            {}
        </ul>
    </div>
    """.format("".join(f"<li>{i}</li>" for i in insights)),
    unsafe_allow_html=True)

