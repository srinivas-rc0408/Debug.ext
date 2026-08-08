import sqlite3
import json
import os
from datetime import datetime, timedelta

def seed_database():
    # Make sure we're writing to the backend's db directory
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend", "history.db")
    
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS bug_history
                 (id INTEGER PRIMARY KEY, timestamp TEXT, url TEXT, summary TEXT, 
                  category TEXT, severity TEXT, priority TEXT, full_json TEXT)''')

    # Generate 5 diverse bugs for beautiful charts
    mock_bugs = [
        {"sum": "Stripe SDK fails to load on checkout", "cat": "Payment", "sev": "Critical", "pri": "P0"},
        {"sum": "Infinite redirect loop on OAuth callback", "cat": "Authentication", "sev": "High", "pri": "P1"},
        {"sum": "504 Gateway Timeout on user table scan", "cat": "Performance", "sev": "High", "pri": "P1"},
        {"sum": "Missing alt-text on profile image", "cat": "UI/UX", "sev": "Low", "pri": "P3"},
        {"sum": "JWT Token validation bypassing expiry check", "cat": "Security", "sev": "Critical", "pri": "P0"}
    ]

    for i, bug in enumerate(mock_bugs):
        ts = (datetime.now() - timedelta(hours=i*2)).isoformat()
        full_json = json.dumps({
            "bug_summary": bug["sum"], "category": bug["cat"], 
            "severity": bug["sev"], "priority": bug["pri"],
            "confidence_score": 0.95 - (i * 0.05), "affected_component": "MockComponent.tsx",
            "probable_root_cause": "Seeded root cause for demo purposes.",
            "technical_analysis": "Simulated stack trace analysis.",
            "suggested_fix": {"explanation": "Apply hotfix.", "code_snippet": "// fix"},
            "missing_information": []
        })
        # Handle the updated SQLite schema: table structure might include 'source'
        # Check table columns first
        c.execute("PRAGMA table_info(bug_history)")
        columns = [col[1] for col in c.fetchall()]
        
        if "source" in columns:
            c.execute("INSERT INTO bug_history (timestamp, url, source, summary, category, severity, priority, full_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                      (ts, "http://localhost:3000", "demo_seeder", bug["sum"], bug["cat"], bug["sev"], bug["pri"], full_json))
        else:
            c.execute("INSERT INTO bug_history (timestamp, url, summary, category, severity, priority, full_json) VALUES (?, ?, ?, ?, ?, ?, ?)",
                      (ts, "http://localhost:3000", bug["sum"], bug["cat"], bug["sev"], bug["pri"], full_json))
    
    conn.commit()
    conn.close()
    print("✅ Database perfectly seeded for Hackathon Demo!")

if __name__ == "__main__":
    seed_database()
