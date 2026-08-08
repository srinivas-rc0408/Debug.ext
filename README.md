# 🐛 Debug.ext | AI-Powered Bug Triage Engine

**Debug.ext** is a zero-latency, multi-model AI triage ecosystem. It consists of a Manifest V3 Chrome Extension that autonomously intercepts silent runtime errors on `localhost`, and a FastAPI/Streamlit analytics dashboard that transforms unstructured logs into structured, prioritized engineering intelligence.

## 🚀 Architecture
- **Browser Interceptor (JS):** Main-world DOM injection captures Network 500s, unhandled promises, and React render crashes automatically.
- **Multi-LLM Gateway (Python/FastAPI):** Asynchronous routing via Inkling (sanitization), MiniMax M3 (structural parsing), and GLM 5.2 (deep reasoning).
- **Analytics Dashboard (Streamlit):** Real-time SQLite-backed visual analytics, multi-format QA log ingestion, and automated PDF Intelligence Report generation.

## 🛠️ Quick Start
1. Clone the repository.
2. Install dependencies: `pip install fastapi uvicorn streamlit pandas plotly fpdf2 python-dotenv`
3. Add your API keys to a `.env` file.
4. Launch the ecosystem: `python run_app.py`
5. Load the `/extension` directory into Chrome (`chrome://extensions` -> Load Unpacked).
