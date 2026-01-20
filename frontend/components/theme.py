"""
Theme and styling configuration for the Aadhaar Analytics Dashboard.
Contains color palettes, chart themes, and CSS styling.
"""

# Color palette for tiers and levels
TIER_COLORS = {
    # Migration levels
    "SURGE": "#FF4B4B",
    "HEAVY": "#FFA500",
    "NORMAL": "#00CC96",
    # Infrastructure tiers
    "CRITICAL": "#FF4B4B",
    "HIGH": "#FFA500",
    "WATCH": "#FFCC00",
    "MEDIUM": "#FFA500",
    "LOW": "#00CC96",
}

# Default color for unknown tiers
DEFAULT_COLOR = "#636EFA"

# Chart color sequences
PLOTLY_COLOR_SEQUENCE = [
    "#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A",
    "#19D3F3", "#FF6692", "#B6E880", "#FF97FF", "#FECB52"
]

# Tier distribution colors (ordered)
TIER_DISTRIBUTION_COLORS = {
    "migration": {"NORMAL": "#00CC96", "HEAVY": "#FFA500", "SURGE": "#FF4B4B"},
    "infrastructure": {"NORMAL": "#00CC96", "WATCH": "#FFCC00", "HIGH": "#FFA500", "CRITICAL": "#FF4B4B"},
    "biometric": {"LOW": "#00CC96", "MEDIUM": "#FFA500", "HIGH": "#FF4B4B"},
    "fafi": {"LOW": "#00CC96", "MEDIUM": "#FFA500", "HIGH": "#FF4B4B"},
}

# KPI Card styles
KPI_STYLES = {
    "success": {"bg": "#D4EDDA", "border": "#28A745", "icon": "✅"},
    "warning": {"bg": "#FFF3CD", "border": "#FFC107", "icon": "⚠️"},
    "danger": {"bg": "#F8D7DA", "border": "#DC3545", "icon": "🚨"},
    "info": {"bg": "#D1ECF1", "border": "#17A2B8", "icon": "ℹ️"},
}

# Custom CSS for the dashboard
CUSTOM_CSS = """
<style>
    /* Main container styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Metric cards */
    div[data-testid="metric-container"] {
        background-color: #1e1e2e;
        border: 1px solid #44475a;
        border-radius: 8px;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    
    /* Sidebar styling - dark theme */
    section[data-testid="stSidebar"] {
        background-color: #1a1a2e !important;
    }
    
    section[data-testid="stSidebar"] > div {
        background-color: #1a1a2e !important;
    }
    
    /* Sidebar text color */
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] span {
        color: #f8f8f2 !important;
    }
    
    /* Sidebar inputs */
    section[data-testid="stSidebar"] input {
        background-color: #2d2d44 !important;
        color: #f8f8f2 !important;
        border: 1px solid #44475a !important;
    }
    
    section[data-testid="stSidebar"] .stSelectbox > div > div {
        background-color: #2d2d44 !important;
        color: #f8f8f2 !important;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #2d2d44;
        border-radius: 4px 4px 0px 0px;
        padding: 10px 20px;
        color: #f8f8f2;
    }
    
    /* Tables */
    .dataframe {
        font-size: 14px;
    }
    
    /* Download button */
    .stDownloadButton > button {
        background-color: #28a745 !important;
        color: white !important;
    }
    
    /* Buttons in sidebar */
    section[data-testid="stSidebar"] button {
        background-color: #44475a !important;
        color: #f8f8f2 !important;
        border: 1px solid #6272a4 !important;
    }
    
    section[data-testid="stSidebar"] button:hover {
        background-color: #6272a4 !important;
    }
    
    /* Info boxes */
    .info-box {
        background-color: #1e3a5f;
        border-left: 4px solid #2196F3;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0 8px 8px 0;
        color: #f8f8f2;
    }
    
    .warning-box {
        background-color: #5f4b1e;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0 8px 8px 0;
        color: #f8f8f2;
    }
    
    .danger-box {
        background-color: #5f1e1e;
        border-left: 4px solid #dc3545;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0 8px 8px 0;
        color: #f8f8f2;
    }
    
    .success-box {
        background-color: #1e5f2d;
        border-left: 4px solid #28a745;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0 8px 8px 0;
        color: #f8f8f2;
    }
    
    /* Slider styling */
    section[data-testid="stSidebar"] .stSlider > div > div {
        background-color: #44475a !important;
    }
</style>
"""


def get_tier_color(tier: str) -> str:
    """Get color for a tier/level value."""
    return TIER_COLORS.get(tier.upper() if tier else "", DEFAULT_COLOR)


def apply_custom_css():
    """Apply custom CSS to the Streamlit app."""
    import streamlit as st
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

