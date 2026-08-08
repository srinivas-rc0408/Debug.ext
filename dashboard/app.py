import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import json
import os
from streamlit_autorefresh import st_autorefresh
from utils import format_github_issue, format_jira_issue
from pdf_generator import generate_pdf_report

if "triage_result" not in st.session_state:
    st.session_state.triage_result = None
if "pdf_bytes" not in st.session_state:
    st.session_state.pdf_bytes = None
# ==========================================
# 1. PAGE CONFIGURATION & STYLING
# ==========================================
st.set_page_config(
    page_title="Debug.ext Analytics",
    page_icon="assets/favicon.ico",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');
    /* Absolute Black Background */
    .stApp { background-color: #000000; color: #F8FAFC; font-family: 'Inter', sans-serif; }
    
    /* Elegant Spacing for Uploader and Text Areas */
    .stFileUploader, .stTextArea {
        margin-bottom: 24px !important;
        padding-top: 8px !important;
    }
    
    /* Pro-Tier Button Styling */
    div.stButton > button {
        background: linear-gradient(135deg, #4F46E5 0%, #3730A3 100%);
        color: white !important;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 600;
        letter-spacing: 0.5px;
        transition: all 0.3s ease;
        margin-top: 10px;
        box-shadow: 0 4px 15px rgba(79, 70, 229, 0.2);
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(79, 70, 229, 0.4);
    }
    
    /* Cleaner Expander Borders */
    div[data-testid="stExpander"] {
        background-color: #0A0A0A;
        border: 1px solid #1E293B;
        border-radius: 8px;
        margin-bottom: 16px;
    }
    
    /* Graphite Metric Cards with Neon Borders */
    .metric-card {
        background-color: #0A0A0A;
        padding: 16px;
        border-radius: 10px;
        border: 1px solid #333333;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0,0,0,0.5);
    }
    .metric-value { font-size: 26px; font-weight: bold; color: #6366F1; }
    .metric-label { font-size: 11px; color: #94A3B8; text-transform: uppercase; letter-spacing: 1px; }
    
    /* Status Pill */
    .status-pill {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        background: rgba(16, 185, 129, 0.1);
        color: #10B981;
        border: 1px solid #10B981;
    }
    
    /* Sleek Expanders and Inputs */
    div[data-testid="stExpander"] {
        background-color: #0A0A0A;
        border: 1px solid #222222;
        border-radius: 8px;
        margin-bottom: 10px;
    }
    div[data-testid="stExpander"] summary {
        font-weight: 600;
        color: #f8fafc;
    }
    div[data-testid="stExpander"] summary:hover {
        color: #6366f1;
    }
    
    /* Upload Button Gradient */
    div[data-testid="stSidebar"] button, div.stButton > button {
        background: linear-gradient(135deg, #4F46E5 0%, #3730A3 100%);
        color: white !important;
        border: none;
        border-radius: 6px;
        transition: 0.3s;
    }
    div.stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 0 15px rgba(79, 70, 229, 0.4);
    }
    
    .code-container { background: #0D1117; border: 1px solid rgba(148, 163, 184, 0.12); border-radius: 10px; padding: 16px; font-family: 'JetBrains Mono', monospace; font-size: 12px; overflow-x: auto; }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header[data-testid="stHeader"] { display: none; }
</style>
""", unsafe_allow_html=True)


# ==========================================
# 2. SIDEBAR & LIVE REFRESH
# ==========================================
with st.sidebar:
    st.markdown("### ⚙️ Workspace Controls")
    if st.button("🔄 Reset Live Session", width="stretch"):
        # Clears the temporary memory for a fresh demo
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    st.divider()

    st.markdown("### ⚙️ Dashboard Settings")
    live_mode = st.toggle("🔴 Live Mode (Auto-Refresh)", value=False, help="Enable to auto-refresh during live demos. New errors appear automatically.")
    refresh_interval = st.select_slider("Refresh Interval", options=[3, 5, 10, 15, 30], value=5, format_func=lambda x: f"{x}s", disabled=not live_mode)
    st.divider()
    st.markdown("### 🔗 Quick Links")
    st.markdown("- [Backend API Docs](http://localhost:8000/docs)")
    st.markdown("- [Health Check](http://localhost:8000/api/health)")

if live_mode:
    st_autorefresh(interval=refresh_interval * 1000, limit=1000, key="debug_ext_live_refresh")
    st.markdown(f"""
        <div style="position: fixed; top: 12px; right: 16px; z-index: 9999;
                    background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.3);
                    border-radius: 999px; padding: 4px 14px; font-size: 11px;
                    font-weight: 600; color: #EF4444; font-family: Inter, sans-serif;
                    backdrop-filter: blur(8px); animation: pulse-live 2s ease-in-out infinite;">
            🔴 LIVE — refreshing every {refresh_interval}s
        </div>
        <style>@keyframes pulse-live {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.6; }} }}</style>
        """, unsafe_allow_html=True)
    st.cache_data.clear()

# ==========================================
# 3. DATA FETCHING
# ==========================================
@st.cache_data(ttl=2)
def load_history():
    try:
        res = requests.get("http://localhost:8000/api/history", timeout=3)
        if res.status_code == 200:
            df = pd.DataFrame(res.json())
            if not df.empty:
                df['confidence_pct'] = df['confidence'].apply(lambda x: int(x * 100) if x <= 1.0 else int(x))
                return df
    except requests.exceptions.ConnectionError:
        # Fails gracefully without a red crash screen
        st.sidebar.error("⚠️ AI Gateway Offline. Check backend server.")
    except Exception:
        pass
    
    # CRITICAL FIX: Return a structured empty dataframe so Pandas NEVER crashes
    return pd.DataFrame(columns=[
        'summary', 'category', 'severity', 'priority', 
        'confidence', 'confidence_pct', 'component', 
        'probable_root_cause', 'suggested_fix', 'missing_information',
        'source', 'url', 'timestamp'
    ])

df = load_history()

# ==========================================
# 🚀 1. THE AUTONOMOUS TRIAGE SPOTLIGHT
# ==========================================
if not df.empty:
    latest_bug = df.iloc[0] # The most recent error
    
    st.markdown("""
    <div style="background: linear-gradient(90deg, #1E293B 0%, #0F172A 100%); 
                padding: 16px 24px; border-radius: 12px; border-left: 5px solid #EF4444; margin-bottom: 20px;">
        <h3 style="margin: 0; color: #F8FAFC; font-size: 20px;">🚨 Active Incident: Action Required</h3>
    </div>
    """, unsafe_allow_html=True)
    
    col_details, col_fix = st.columns([1, 1.2], gap="large")
    
    with col_details:
        st.markdown("#### 📊 Triage Analytics")
        st.markdown(f"**Priority:** `<span style='color:#EF4444; font-weight:bold;'>[{latest_bug.get('priority', 'P0')}]</span>` | **Severity:** `{latest_bug.get('severity', 'Critical')}`", unsafe_allow_html=True)
        st.markdown(f"**Category:** `{latest_bug.get('category', 'Unknown')}`")
        st.markdown(f"**Vulnerable Module:** `{latest_bug.get('affected_component', 'Unknown')}`")
        
        st.markdown("#### 🔍 Root Cause Detection")
        st.info(latest_bug.get('probable_root_cause', 'N/A'))
        
        # Generates the downloadable PDF instantly
        from pdf_generator import generate_pdf_report
        try:
            pdf_bytes = generate_pdf_report(latest_bug.to_dict())
            st.download_button(
                label="📄 Download Full PDF Report",
                data=pdf_bytes,
                file_name=f"Debug_ext_{latest_bug.get('priority', 'P0')}_Report.pdf",
                mime="application/pdf",
                width="stretch",
                type="primary"
            )
        except:
            st.error("PDF Engine Offline")

    with col_fix:
        st.markdown("#### 🛠️ Autonomous Code Remediation")
        fix_data = latest_bug.get('suggested_fix', {})
        
        if isinstance(fix_data, dict):
            st.write(fix_data.get('explanation', 'Apply the following fix:'))
            code = fix_data.get('code_snippet', '// No code provided')
            st.code(code, language="javascript")
        else:
            st.warning("No structured code fix was returned by the AI gateway.")

    st.divider()

    # ==========================================
    # 📋 2. THE ERROR LOG TABLE
    # ==========================================
    st.markdown("### 📋 Session Error Log")
    st.caption("Complete history of intercepted exceptions, categorized and prioritized.")
    
    # Render a beautiful, interactive SaaS data table
    st.dataframe(
        df[['priority', 'severity', 'category', 'bug_summary', 'affected_component']],
        column_config={
            "priority": st.column_config.TextColumn("Priority", width="small"),
            "severity": st.column_config.TextColumn("Severity", width="small"),
            "category": st.column_config.TextColumn("Category", width="medium"),
            "bug_summary": st.column_config.TextColumn("Exception Trace", width="large"),
            "affected_component": st.column_config.TextColumn("Module", width="medium")
        },
        use_container_width=True,
        hide_index=True
    )
    st.markdown("<br><br>", unsafe_allow_html=True)

# ==========================================
# HEADER
# ==========================================
_logo_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'logo.png')

col_title, col_status = st.columns([3, 1])
with col_title:
    if os.path.exists(_logo_path):
        _hdr_logo, _hdr_text = st.columns([0.08, 0.92])
        with _hdr_logo: st.image(_logo_path, width=52)
        with _hdr_text:
            st.title("Debug.ext Analytics")
            st.caption("Multi-Model AI Bug Triage Engine · Inkling · MiniMax M3 · GLM 5.2")
    else:
        st.title("Debug.ext Analytics")
        st.caption("Multi-Model AI Bug Triage Engine · Inkling · MiniMax M3 · GLM 5.2")

with col_status:
    st.markdown("<br>", unsafe_allow_html=True)
    try:
        health_check = requests.get("http://localhost:8000/api/health", timeout=1)
        if health_check.status_code == 200:
            st.markdown('<div class="status-pill">🟢 Gateway API Online</div>', unsafe_allow_html=True)
    except:
        st.markdown('<div class="status-pill" style="color: #EF4444; border-color: #EF4444; background: rgba(239, 68, 68, 0.1);">🔴 Gateway Offline</div>', unsafe_allow_html=True)

# ==========================================
# TABS
# ==========================================
tab1, tab2 = st.tabs(["🚀 Live Triage & Upload", "🗄️ Bug History"])

# ─── TAB 1: LIVE TRIAGE & UPLOAD ─────────────────────────────────────────────
with tab1:
    st.subheader("📥 Omni-Format QA Ingestion Engine")
    st.caption("Upload unstructured error dumps, customer tickets, or tabular QA logs.")
    st.markdown("<br>", unsafe_allow_html=True) # Adds breathing room
    
    # 1. UNLOCK ALL FILE TYPES
    allowed_types = ['txt', 'log', 'json', 'csv', 'md', 'xml']
    uploaded_file = st.file_uploader(
        f"Drop {', '.join(allowed_types).upper()} files here:", 
        type=allowed_types
    )
    
    st.markdown("<br>", unsafe_allow_html=True) # Separates uploader from text area
    raw_text = st.text_area("Or paste raw text/stack trace directly:", height=150)
    
    st.markdown("<br>", unsafe_allow_html=True) # Separates text area from button
    
    if st.button("🚀 Run Autonomous AI Triage", width="stretch"):
        payload_text = ""
        
        # 2. BULLETPROOF PARSING
        if uploaded_file is not None:
            # errors="ignore" guarantees the dashboard won't crash on corrupted CSV/Log bytes
            payload_text = uploaded_file.getvalue().decode("utf-8", errors="ignore")
            
            # Pro UI Touch: Show the judges that the file was instantly read
            st.toast(f"Successfully ingested {uploaded_file.name} ({round(uploaded_file.size / 1024, 2)} KB)", icon="📂")
            
        elif raw_text.strip():
            payload_text = raw_text.strip()
            
        if payload_text:
            with st.spinner("Processing massive payload through AI architecture..."):
                try:
                    res = requests.post("http://localhost:8000/api/analyze", json={
                        "raw_report": payload_text, 
                        "url": f"File Upload: {uploaded_file.name if uploaded_file else 'Manual Paste'}", 
                        "source": "dashboard_upload"
                    })
                    
                    if res.status_code == 200:
                        bug_data = res.json()
                        from pdf_generator import generate_pdf_report
                        
                        # 3. SAVE TO SESSION STATE
                        st.session_state.triage_result = bug_data
                        st.session_state.pdf_bytes = generate_pdf_report(bug_data)
                        st.toast('Analysis Complete! PDF Ready.', icon='✅')
                except Exception as e:
                    st.error(f"Gateway connection error: {e}")
        else:
            st.warning("⚠️ Please upload a document or paste a log trace first.")

    # 4. PERSISTENT DISPLAY
    if st.session_state.get('triage_result'):
        data = st.session_state.triage_result
        
        # Clean UI Layout for Results
        res_col1, res_col2 = st.columns([2, 1])
        with res_col1:
            st.markdown(f"### 📌 [{data.get('priority')}] {data.get('category')} Error")
            st.info(f"**Root Cause Identified:** {data.get('probable_root_cause')}")
        with res_col2:
            st.markdown("<br>", unsafe_allow_html=True)
            st.download_button(
                label="📄 Download PDF Intelligence Report",
                data=st.session_state.pdf_bytes,
                file_name=f"Debug_ext_Report_{data.get('priority')}.pdf",
                mime="application/pdf",
                width="stretch",
                type="primary"
            )

# ─── TAB 2: BUG HISTORY ──────────────────────────────────────────────────────
with tab2:
    if not df.empty:
        # Metrics
        m1, m2, m3, m4 = st.columns(4)
        total_bugs = len(df)
        critical_ratio = (len(df[df['severity'] == 'Critical']) / total_bugs * 100) if total_bugs > 0 else 0.0
        avg_health = max(0.0, 100 - (critical_ratio * 1.5))
        
        with m1:
            st.metric("Total Bugs Analyzed", str(total_bugs), delta=f"+{max(1, total_bugs // 5)}", delta_color="normal")
        with m2:
            st.metric("Critical Ratio", f"{critical_ratio:.1f}%", delta="-2.1%", delta_color="inverse")
        with m3:
            st.metric("Auto-Intercepted", str(len(df[df["source"]=="extension"])), delta="+3", delta_color="normal")
        with m4:
            st.metric("System Health", f"{avg_health:.1f}", delta="+1.4", delta_color="normal")
        
        st.divider()
        
        st.subheader("🗄️ Historical Ledger")
        
        # Real-Time Workspace Search & Filter Bar
        s_col1, s_col2 = st.columns([2, 1])
        with s_col1:
            search_query = st.text_input("🔎 Search by Keyword, Component, or Summary:", placeholder="e.g., PaymentForm, 500, Token...")
        with s_col2:
            selected_sev = st.multiselect("Filter Severity:", options=['Critical', 'High', 'Medium', 'Low'], default=['Critical', 'High', 'Medium', 'Low'])

        filtered_df = df[df['severity'].isin(selected_sev)]
        if search_query:
            filtered_df = filtered_df[
                filtered_df['summary'].str.contains(search_query, case=False, na=False) |
                filtered_df.apply(lambda x: search_query.lower() in str(x.get('full_analysis', {}).get('affected_component', '')).lower(), axis=1)
            ]
        
        st.caption(f"Showing {len(filtered_df)} of {len(df)} entries")
        
        st.dataframe(
            filtered_df[['timestamp', 'source', 'url', 'category', 'severity', 'priority', 'summary', 'confidence_pct']],
            column_config={
                "timestamp": st.column_config.DatetimeColumn("Timestamp", format="D MMM YYYY, h:mm a"),
                "confidence_pct": st.column_config.ProgressColumn("Confidence", format="%d%%", min_value=0, max_value=100)
            },
            width="stretch", hide_index=True
        )
        
        # Add Visual Analytics Chart
        st.markdown("##### Most Vulnerable Modules")
        # Check if df is not empty AND the column actually exists
        if not df.empty and 'component' in df.columns:
            valid_mods = df[~df['component'].isin(['Unknown', 'unknown', 'N/A', '', None])]
            
            if not valid_mods.empty:
                mod_counts = valid_mods['component'].value_counts().reset_index()
                mod_counts.columns = ['Component', 'Failures']
                
                fig_bar = px.bar(
                    mod_counts, y='Component', x='Failures', orientation='h',
                    color_discrete_sequence=['#6366F1']
                )
                # Make chart background transparent to match the black theme
                fig_bar.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#F8FAFC'),
                    xaxis=dict(title="Failure Count", dtick=1, gridcolor="#333333"),
                    yaxis=dict(title=""),
                    margin=dict(l=20, r=20, t=20, b=40)
                )
                st.plotly_chart(fig_bar, width="stretch")
            else:
                st.info("No module data available yet.")
        else:
            st.info("Awaiting initial bug telemetry...")
        
        st.markdown("#### 📋 History Details")
        for idx, row in filtered_df.iterrows():
            full = row.get('full_analysis', {})
            with st.expander(f"📌 [{row['priority']}] {row['summary'][:80]} — ({row['category']})"):
                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"**Source URL:** `{row['url']}`")
                    st.write("**Probable Root Cause:**")
                    st.info(full.get('probable_root_cause', row.get('probable_root_cause', 'N/A')))
                    st.write("**Technical Breakdown:**")
                    st.write(full.get('technical_analysis', 'N/A'))
                with c2:
                    st.write("**Suggested Code Fix:**")
                    fix = full.get('suggested_fix', {})
                    if isinstance(fix, dict):
                        if fix.get('explanation'):
                            st.markdown(fix['explanation'])
                        if fix.get('code_snippet'):
                            st.code(fix['code_snippet'], language="typescript")
                
                exp_col1, exp_col2 = st.columns(2)
                with exp_col1:
                    st.download_button(
                        "📄 Download GitHub Markdown Issue",
                        data=format_github_issue(full),
                        file_name=f"issue_{row['priority']}_{idx}.md",
                        mime="text/markdown",
                        key=f"gh_{idx}"
                    )
                with exp_col2:
                    st.download_button(
                        "📌 Download Jira Issue Format",
                        data=format_jira_issue(full),
                        file_name=f"jira_{row['priority']}_{idx}.txt",
                        mime="text/plain",
                        key=f"jira_{idx}"
                    )
        
        st.divider()
        
        # Export functionality
        st.subheader("📤 Export & Share")
        export_cols = st.columns(3)
        with export_cols[0]:
            if st.button("Download JSON (GitHub/Jira)", width="stretch"):
                export_data = []
                for _, row in df.iterrows():
                    issue = {
                        "title": f"[{row['severity']}][{row['priority']}] {row['summary']}",
                        "body": (
                            f"## Bug Analysis Report\n\n"
                            f"**Category:** {row['category']}\n"
                            f"**Severity:** {row['severity']}\n"
                            f"**Priority:** {row['priority']}\n"
                            f"**Component:** {row.get('affected_component', 'Unknown')}\n"
                            f"**Confidence:** {row['confidence_pct']}%\n\n"
                            f"### Root Cause\n{row.get('full_analysis', {}).get('probable_root_cause', 'N/A')}\n\n"
                            f"### Technical Analysis\n{row.get('full_analysis', {}).get('technical_analysis', 'N/A')}\n\n"
                        ),
                        "labels": [row["category"], row["severity"], row["priority"]],
                    }
                    export_data.append(issue)
                json_str = json.dumps(export_data, indent=2)
                st.download_button(
                    label="⬇ Download JSON", data=json_str,
                    file_name="debug_ext_issues.json", mime="application/json",
                    width="stretch"
                )
        with export_cols[1]:
            csv_cols = ['summary', 'category', 'severity', 'priority', 'confidence_pct', 'url', 'source']
            csv = df[csv_cols].to_csv(index=False)
            st.download_button(
                label="📊 Download CSV", data=csv,
                file_name="debug_ext_bugs.csv", mime="text/csv",
                width="stretch"
            )
        with export_cols[2]:
            if st.button("🔄 Refresh Data", width="stretch"):
                st.cache_data.clear()
                st.rerun()
    else:
        st.info("The history ledger is currently empty. Upload a bug or start debugging to record autonomous analysis.")

st.markdown('<div style="text-align: center; padding: 32px 0 16px; color: #64748B; font-size: 11px;">Debug.ext Autonomous Dashboard · Powered by Inkling · MiniMax M3 · GLM 5.2</div>', unsafe_allow_html=True)
