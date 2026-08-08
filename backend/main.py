"""
Debug.ext — FastAPI Application Entry Point
Multi-model AI-powered bug analysis gateway.
"""

from __future__ import annotations

import logging
import os

from dotenv import load_dotenv

# Load environment before anything else
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.analyze import router as analyze_router

# ─── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(name)-24s │ %(levelname)-7s │ %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("debug_ext")

# ─── FastAPI App ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="Debug.ext API",
    description=(
        "Multi-model AI gateway for structured bug analysis. "
        "Routes browser-captured error data through Inkling (sanitization & routing), "
        "MiniMax M3 (structural analysis), and GLM 5.2 (deep reasoning)."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow all origins for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(analyze_router)


from services import database

@app.on_event("startup")
async def _startup():
    # Initialize SQLite database
    database.init_db()
    logger.info("═" * 60)
    logger.info("  Debug.ext Backend — Starting Up")
    logger.info("═" * 60)
    logger.info("  NVIDIA Base URL : %s", os.getenv("NVIDIA_BASE_URL", "not set"))
    logger.info("  GLM Key         : %s", "✓ loaded" if os.getenv("NVIDIA_API_KEY_GLM") else "✗ missing")
    logger.info("  MiniMax Key     : %s", "✓ loaded" if os.getenv("NVIDIA_API_KEY_MINIMAX") else "✗ missing")
    logger.info("  Inkling Key     : %s", "✓ loaded" if os.getenv("NVIDIA_API_KEY_INKLING") else "✗ missing")
    logger.info("═" * 60)


# ─── Direct Run ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
