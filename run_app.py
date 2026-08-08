import subprocess
import time
import sys
import os

def run_debug_ext():
    print("=" * 60)
    print("🚀 BOOTSTRAPPING DEBUG.EXT MULTI-MODEL SYSTEM")
    print("=" * 60)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Intelligently locate the virtual environment to ensure flawless execution
    venv_uvicorn = os.path.join(base_dir, "backend", ".venv", "bin", "uvicorn")
    venv_streamlit = os.path.join(base_dir, "backend", ".venv", "bin", "streamlit")

    # 1. Start FastAPI Backend
    print("[1/2] Starting FastAPI Gateway on http://localhost:8000...")
    backend_cmd = [venv_uvicorn if os.path.exists(venv_uvicorn) else sys.executable, "-m", "uvicorn", "main:app", "--reload", "--port", "8000"]
    if os.path.exists(venv_uvicorn):
        backend_cmd = [venv_uvicorn, "main:app", "--reload", "--port", "8000"]
    
    backend = subprocess.Popen(backend_cmd, cwd=os.path.join(base_dir, "backend"))
    
    time.sleep(2) # Allow backend to initialize

    # 2. Start Streamlit Dashboard
    print("[2/2] Starting Streamlit Analytics Dashboard on http://localhost:8501...")
    dashboard_cmd = [venv_streamlit if os.path.exists(venv_streamlit) else sys.executable, "-m", "streamlit", "run", "app.py", "--server.port", "8501"]
    if os.path.exists(venv_streamlit):
        dashboard_cmd = [venv_streamlit, "run", "app.py", "--server.port", "8501"]
        
    dashboard = subprocess.Popen(dashboard_cmd, cwd=os.path.join(base_dir, "dashboard"))

    print("\n✅ DEBUG.EXT IS LIVE!")
    print("👉 Dashboard: http://localhost:8501")
    print("👉 API Docs:   http://localhost:8000/docs")
    print("Press Ctrl+C to terminate all services.\n")

    try:
        backend.wait()
        dashboard.wait()
    except KeyboardInterrupt:
        print("\n Shutting down Debug.ext services cleanly...")
        backend.terminate()
        dashboard.terminate()

if __name__ == "__main__":
    run_debug_ext()
