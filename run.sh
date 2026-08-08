#!/bin/bash
echo "Starting Debug.ext Enterprise Architecture..."
# Start FastAPI backend in the background
cd backend && uvicorn main:app --host 0.0.0.0 --port 8000 &
# Start Streamlit dashboard
cd ../dashboard && streamlit run app.py --server.port 8501
