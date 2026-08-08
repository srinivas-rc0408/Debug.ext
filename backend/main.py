from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
import json
from datetime import datetime
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SHARED_DIR = os.path.join(BASE_DIR, "..", "shared")
sys.path.append(SHARED_DIR)

from triage_prompt_engine import run_triage

DB_PATH = os.path.join(BASE_DIR, "history.db")

app = FastAPI(title="Debug.ext Enterprise Gateway", version="3.0")

class BugReportRequest(BaseModel):
    raw_report: str
    url: str = "Universal Web Target"
    source: str = "extension"

class SeedRequest(BaseModel):
    results: list[dict]

@app.post("/api/analyze")
async def analyze_bug(req: BugReportRequest):
    try:
        # 1. High-Speed Universal Normalization & Triage
        raw_text = req.raw_report.strip()
        report = run_triage(raw_text, source_context=req.url)
        
        # Convert Pydantic TriageReport to dict for storage and return
        ai_payload = report.model_dump()
        ai_payload["bug_summary"] = ai_payload.get("incident_summary", ai_payload.get("bug_summary", "Unknown Bug"))
        ai_payload["confidence_pct"] = ai_payload.get("confidence", 0)
        ai_payload["affected_component"] = ai_payload.get("code_patch", {}).get("filename", req.url)
        ai_payload["severity"] = {"P0": "Critical", "P1": "High", "P2": "Medium", "P3": "Low"}.get(ai_payload.get("priority"), "Medium")
        category = ai_payload.get("category", "Unknown")
        severity = ai_payload.get("severity")
        priority = ai_payload.get("priority")

        # 2. SQLite Persistence Layer
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS bug_history
                     (id INTEGER PRIMARY KEY, timestamp TEXT, url TEXT, summary TEXT, 
                      category TEXT, severity TEXT, priority TEXT, full_json TEXT)''')
        
        c.execute("INSERT INTO bug_history (timestamp, url, summary, category, severity, priority, full_json) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (datetime.now().isoformat(), req.url, ai_payload["bug_summary"], category, severity, priority, json.dumps(ai_payload)))
        conn.commit()
        conn.close()

        return ai_payload

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/history")
async def get_history():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM bug_history ORDER BY id DESC")
        rows = [dict(row) for row in c.fetchall()]
        conn.close()
        return rows
    except:
        return []

@app.get("/api/results")
async def get_results():
    return await get_history()

@app.post("/api/results/seed")
async def seed_results(req: SeedRequest):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS bug_history
                     (id INTEGER PRIMARY KEY, timestamp TEXT, url TEXT, summary TEXT, 
                      category TEXT, severity TEXT, priority TEXT, full_json TEXT)''')
        
        count = 0
        for item in req.results:
            url = item.get("url", item.get("affected_component", "Unknown Module"))
            summary = item.get("bug_summary", "Unknown Error")
            category = item.get("category", "General")
            severity = item.get("severity", "Medium")
            priority = item.get("priority", "P2")
            full_json = json.dumps(item)
            
            c.execute("INSERT INTO bug_history (timestamp, url, summary, category, severity, priority, full_json) VALUES (?, ?, ?, ?, ?, ?, ?)",
                      (item.get("timestamp", datetime.now().isoformat()), url, summary, category, severity, priority, full_json))
            count += 1
            
        c.execute("SELECT COUNT(*) FROM bug_history")
        total = c.fetchone()[0]
        
        conn.commit()
        conn.close()
        return {"seeded": count, "total": total}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    return {"status": "online", "system": "Debug.ext Enterprise Gateway"}
