# Aadhaar Alert Analytics Dashboard

## Quick Start

### 1. Start the FastAPI Backend
```bash
cd /home/voyager4/projects/uidai
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Run the Streamlit Dashboard
```bash
cd /home/voyager4/projects/uidai/frontend
pip install -r requirements.txt
export BACKEND_URL="http://127.0.0.1:8000"
streamlit run app.py
```

The dashboard will open at `http://localhost:8501`

## Features
- 6 analytics pages: Overview, Migration, Infrastructure, Biometric, Lost Generation, ML Forecast
- Interactive Plotly charts with filtering
- CSV download for all data tables
- Responsive sidebar with global filters

