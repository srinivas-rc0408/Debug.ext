#!/usr/bin/env python3
"""
Debug.ext — Demo Runner
Seeds the backend with pre-analyzed bug reports and verifies system health.
Run this after starting the backend to populate the dashboard immediately.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import requests

# ─── Configuration ─────────────────────────────────────────────────────────────

BACKEND_URL = "http://localhost:8000"
DEMO_FILE = Path(__file__).parent / "demo_bug_reports.json"

# ─── ANSI Colors ───────────────────────────────────────────────────────────────

USE_COLOR = sys.stdout.isatty()

class C:
    BOLD = "\033[1m" if USE_COLOR else ""
    DIM = "\033[2m" if USE_COLOR else ""
    RED = "\033[91m" if USE_COLOR else ""
    GREEN = "\033[92m" if USE_COLOR else ""
    YELLOW = "\033[93m" if USE_COLOR else ""
    BLUE = "\033[94m" if USE_COLOR else ""
    MAGENTA = "\033[95m" if USE_COLOR else ""
    CYAN = "\033[96m" if USE_COLOR else ""
    RESET = "\033[0m" if USE_COLOR else ""


def log(icon: str, msg: str, color: str = ""):
    timestamp = time.strftime("%H:%M:%S")
    print(f"  {C.DIM}{timestamp}{C.RESET}  {icon}  {color}{msg}{C.RESET}")


def header(text: str):
    width = 60
    print()
    print(f"  {C.MAGENTA}{C.BOLD}{'═' * width}{C.RESET}")
    print(f"  {C.MAGENTA}{C.BOLD}  {text}{C.RESET}")
    print(f"  {C.MAGENTA}{C.BOLD}{'═' * width}{C.RESET}")
    print()


def section(text: str):
    print(f"\n  {C.CYAN}{C.BOLD}── {text} ──{C.RESET}\n")


# ─── Health Check ──────────────────────────────────────────────────────────────

def check_health() -> bool:
    """Verify backend is running and healthy."""
    section("Backend Health Check")
    try:
        start = time.time()
        resp = requests.get(f"{BACKEND_URL}/api/health", timeout=5)
        latency = (time.time() - start) * 1000

        if resp.status_code == 200:
            data = resp.json()
            log("✅", f"Backend is {C.GREEN}HEALTHY{C.RESET}")
            log("📊", f"Results in store: {data.get('results_count', 0)}")
            log("⏱️ ", f"Health check latency: {latency:.0f}ms", C.DIM)
            return True
        else:
            log("❌", f"Health check returned HTTP {resp.status_code}", C.RED)
            return False
    except requests.ConnectionError:
        log("❌", "Cannot connect to backend — is it running?", C.RED)
        log("💡", f"Start with: {C.CYAN}cd backend && python main.py{C.RESET}", C.YELLOW)
        return False
    except Exception as e:
        log("❌", f"Health check failed: {e}", C.RED)
        return False


# ─── Seed Demo Data ───────────────────────────────────────────────────────────

def seed_demo_data() -> bool:
    """Load demo bug reports and seed them into the backend."""
    section("Seeding Demo Data")

    if not DEMO_FILE.exists():
        log("❌", f"Demo file not found: {DEMO_FILE}", C.RED)
        return False

    with open(DEMO_FILE) as f:
        demo = json.load(f)

    analyzed = demo.get("analyzed_results", [])
    if not analyzed:
        log("⚠️ ", "No analyzed results found in demo file", C.YELLOW)
        return False

    log("📦", f"Loaded {len(analyzed)} pre-analyzed bug reports")

    # Seed via the bulk endpoint
    try:
        start = time.time()
        resp = requests.post(
            f"{BACKEND_URL}/api/results/seed",
            json={"results": analyzed},
            timeout=10,
        )
        latency = (time.time() - start) * 1000

        if resp.status_code == 200:
            data = resp.json()
            log("✅", f"Seeded {data.get('seeded', 0)} results successfully", C.GREEN)
            log("📊", f"Total results in store: {data.get('total', 0)}")
            log("⏱️ ", f"Seed latency: {latency:.0f}ms", C.DIM)
            return True
        else:
            log("❌", f"Seed request returned HTTP {resp.status_code}: {resp.text}", C.RED)
            return False
    except Exception as e:
        log("❌", f"Seed failed: {e}", C.RED)
        return False


# ─── Verify Seeded Data ───────────────────────────────────────────────────────

def verify_results() -> bool:
    """Verify that seeded data is retrievable."""
    section("Verifying Seeded Results")

    try:
        start = time.time()
        resp = requests.get(f"{BACKEND_URL}/api/results", timeout=5)
        latency = (time.time() - start) * 1000

        if resp.status_code == 200:
            results = resp.json()
            log("✅", f"Retrieved {len(results)} results from API", C.GREEN)
            log("⏱️ ", f"Fetch latency: {latency:.0f}ms", C.DIM)

            # Print summary table
            print()
            print(f"  {'─' * 90}")
            print(
                f"  {C.BOLD}{'#':<4} {'Severity':<10} {'Priority':<10} "
                f"{'Category':<18} {'Confidence':<12} {'Summary':<40}{C.RESET}"
            )
            print(f"  {'─' * 90}")

            for i, r in enumerate(results, 1):
                sev = r.get("severity", "?")
                pri = r.get("priority", "?")
                cat = r.get("category", "?")
                conf = r.get("confidence_score", 0)
                summary = r.get("bug_summary", "")[:38]

                sev_color = {
                    "Critical": C.RED,
                    "High": C.YELLOW,
                    "Medium": C.BLUE,
                    "Low": C.GREEN,
                }.get(sev, "")

                print(
                    f"  {i:<4} {sev_color}{sev:<10}{C.RESET} {pri:<10} "
                    f"{cat:<18} {conf:<12.0%} {summary}"
                )

            print(f"  {'─' * 90}")
            print()
            return True
        else:
            log("❌", f"Results fetch returned HTTP {resp.status_code}", C.RED)
            return False
    except Exception as e:
        log("❌", f"Verification failed: {e}", C.RED)
        return False


# ─── Model Route Test ──────────────────────────────────────────────────────────

def test_model_routes():
    """Test that the analysis endpoint is reachable (without calling actual models)."""
    section("Model Route Availability")

    models = [
        ("Inkling", "Sanitization & Intent Routing"),
        ("MiniMax M3", "Structural Analysis & Code Patches"),
        ("GLM 5.2", "Deep Reasoning & Root Cause Analysis"),
    ]

    for name, desc in models:
        log("🤖", f"{C.BOLD}{name}{C.RESET} — {C.DIM}{desc}{C.RESET}")

    log("💡", "Full model integration test requires sending a real bug report.", C.DIM)
    log("💡", f"Try: {C.CYAN}curl -X POST http://localhost:8000/api/analyze -H 'Content-Type: application/json' -d '{{\"url\":\"https://example.com\",\"raw_error\":\"Test error\"}}'", C.DIM)


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    header("Debug.ext — Demo Runner")

    log("🐛", f"Debug.ext Demo & Verification Suite", C.BOLD)
    log("🔗", f"Backend URL: {C.CYAN}{BACKEND_URL}{C.RESET}")
    log("📁", f"Demo file: {C.CYAN}{DEMO_FILE}{C.RESET}")

    # Step 1: Health check
    if not check_health():
        log("💀", "Backend is not available. Aborting.", C.RED)
        sys.exit(1)

    # Step 2: Seed demo data
    if not seed_demo_data():
        log("⚠️ ", "Seeding failed, but continuing with verification...", C.YELLOW)

    # Step 3: Verify
    verify_results()

    # Step 4: Model routes
    test_model_routes()

    # Summary
    section("Summary")
    log("✅", f"{C.GREEN}{C.BOLD}Demo setup complete!{C.RESET}")
    log("🌐", f"Backend API:  {C.CYAN}http://localhost:8000/docs{C.RESET}")
    log("📊", f"Dashboard:    {C.CYAN}http://localhost:8501{C.RESET}")
    log("🔌", f"Extension:    {C.CYAN}chrome://extensions → Load Unpacked → extension/{C.RESET}")
    print()


if __name__ == "__main__":
    main()
