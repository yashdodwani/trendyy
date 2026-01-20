"""
Aadhaar Alert Analytics Dashboard
=================================
A premium, hackathon-ready Streamlit dashboard for visualizing
UIDAI Aadhaar alert analytics from the FastAPI backend.

Run with: streamlit run app.py
"""

import streamlit as st
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from components.api_client import test_connection, clear_cache, get_backend_url
from components.theme import apply_custom_css

# Page configuration - must be first Streamlit command
st.set_page_config(
    page_title="Aadhaar Alert Analytics",
    page_icon="🆔",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com/uidai/analytics-dashboard",
        "Report a bug": "https://github.com/uidai/analytics-dashboard/issues",
        "About": "# Aadhaar Alert Analytics Dashboard\nA comprehensive analytics platform for UIDAI alerts."
    }
)

# Apply custom CSS
apply_custom_css()

# Initialize session state
if "backend_url" not in st.session_state:
    st.session_state.backend_url = os.environ.get("BACKEND_URL", "http://127.0.0.1:8001")

if "selected_month" not in st.session_state:
    st.session_state.selected_month = "Latest"

if "selected_states" not in st.session_state:
    st.session_state.selected_states = []

if "search_text" not in st.session_state:
    st.session_state.search_text = ""

if "top_n" not in st.session_state:
    st.session_state.top_n = 10


def render_sidebar():
    """Render the global sidebar controls."""
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/en/c/cf/Aadhaar_Logo.svg", width=150)
        st.title("🆔 Aadhaar Analytics")
        st.markdown("---")

        # Backend URL configuration
        st.subheader("🔌 Backend Connection")
        backend_url = st.text_input(
            "Backend URL",
            value=st.session_state.backend_url,
            key="backend_url_input",
            help="FastAPI backend URL"
        )

        if backend_url != st.session_state.backend_url:
            st.session_state.backend_url = backend_url
            clear_cache()

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔗 Test", use_container_width=True):
                with st.spinner("Testing..."):
                    success, message = test_connection(st.session_state.backend_url)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)

        with col2:
            if st.button("🔄 Clear Cache", use_container_width=True):
                clear_cache()
                st.success("Cache cleared!")

        st.markdown("---")

        # Month selector
        st.subheader("📅 Time Period")
        month_options = ["Latest", "2026-01", "2025-12", "2025-11", "2025-10", "2025-09", "2025-08"]
        st.session_state.selected_month = st.selectbox(
            "Select Month",
            options=month_options,
            index=month_options.index(st.session_state.selected_month) if st.session_state.selected_month in month_options else 0,
            key="month_selector",
            help="Filter data by month (YYYY-MM format)"
        )

        st.markdown("---")

        # State filter (populated dynamically from data)
        st.subheader("🗺️ Geographic Filter")
        # Note: States will be populated from data in individual pages
        st.session_state.search_text = st.text_input(
            "🔍 Search District/Pincode",
            value=st.session_state.search_text,
            key="search_input",
            help="Filter by district name or pincode"
        )

        st.markdown("---")

        # Top-N slider
        st.subheader("📊 Display Settings")
        st.session_state.top_n = st.slider(
            "Top N Items",
            min_value=5,
            max_value=50,
            value=st.session_state.top_n,
            step=5,
            key="top_n_slider",
            help="Number of top items to display in charts"
        )

        st.markdown("---")

        # Footer
        st.markdown("""
        <div style="text-align: center; color: #888; font-size: 12px;">
            <p>Aadhaar Analytics Dashboard v1.0</p>
            <p>© 2026 UIDAI Analytics Team</p>
        </div>
        """, unsafe_allow_html=True)


def main():
    """Main application entry point."""
    render_sidebar()

    # Main content area - Welcome page
    st.title("🆔 Aadhaar Alert Analytics Dashboard")
    st.markdown("""
    Welcome to the **Aadhaar Alert Analytics Dashboard** - a comprehensive platform for 
    monitoring and analyzing UIDAI operational alerts across India.
    """)

    # Feature cards
    st.markdown("---")
    st.subheader("📊 Available Analytics Modules")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 20px; border-radius: 10px; color: white; height: 200px;">
            <h3>📈 Overview</h3>
            <p>Executive summary with KPIs, tier distributions, and cross-module insights.</p>
            <p><strong>→ Go to 1_Overview</strong></p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                    padding: 20px; border-radius: 10px; color: white; height: 200px; margin-top: 20px;">
            <h3>🧬 Biometric Integrity (BIS)</h3>
            <p>Monitor capture gaps and data quality issues.</p>
            <p><strong>→ Go to 4_Biometric_Integrity</strong></p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); 
                    padding: 20px; border-radius: 10px; color: white; height: 200px;">
            <h3>🚚 Migration (URRDF)</h3>
            <p>Track population movement patterns and predict migration pressure.</p>
            <p><strong>→ Go to 2_Migration_URRDF</strong></p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); 
                    padding: 20px; border-radius: 10px; color: white; height: 200px; margin-top: 20px;">
            <h3>👶 Lost Generation (FAFI)</h3>
            <p>Identify enrollment gaps in child demographics.</p>
            <p><strong>→ Go to 5_Lost_Generation</strong></p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); 
                    padding: 20px; border-radius: 10px; color: #333; height: 200px;">
            <h3>🏗️ Infrastructure (AFLB)</h3>
            <p>Analyze facility load and infrastructure stress.</p>
            <p><strong>→ Go to 3_Infrastructure_AFLB</strong></p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="background: linear-gradient(135deg, #89f7fe 0%, #66a6ff 100%); 
                    padding: 20px; border-radius: 10px; color: white; height: 200px; margin-top: 20px;">
            <h3>🤖 ML Forecast</h3>
            <p>Machine learning predictions for migration trends.</p>
            <p><strong>→ Go to 6_ML_Forecast</strong></p>
        </div>
        """, unsafe_allow_html=True)

    # Quick start guide
    st.markdown("---")
    st.subheader("🚀 Quick Start Guide")

    with st.expander("How to use this dashboard", expanded=True):
        st.markdown("""
        1. **Configure Backend**: Enter your FastAPI backend URL in the sidebar and test the connection.
        2. **Select Time Period**: Choose a month to filter data or use "Latest" for the most recent data.
        3. **Navigate Pages**: Use the sidebar navigation to explore different analytics modules.
        4. **Apply Filters**: Use state filters and search to narrow down results.
        5. **Download Data**: Export filtered data as CSV from any page.
        
        **Pages Overview:**
        - **Overview**: High-level KPIs and summary statistics
        - **Migration URRDF**: District-level migration inflow analysis
        - **Infrastructure AFLB**: Facility stress and load monitoring
        - **Biometric Integrity BIS**: Data quality and capture gap analysis
        - **Lost Generation FAFI**: Child enrollment gap detection
        - **ML Forecast**: Machine learning based predictions
        """)

    # Status indicator
    st.markdown("---")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Backend URL", st.session_state.backend_url.replace("http://", "").replace("https://", ""))

    with col2:
        st.metric("Selected Month", st.session_state.selected_month)

    with col3:
        st.metric("Display Items", st.session_state.top_n)


if __name__ == "__main__":
    main()

