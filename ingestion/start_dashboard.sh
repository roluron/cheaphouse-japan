#!/bin/bash
# Launch the CheapHouse pipeline dashboard
cd "$(dirname "$0")"
source venv/bin/activate
streamlit run dashboard.py --server.port 8501 --server.address localhost --browser.gatherUsageStats false
