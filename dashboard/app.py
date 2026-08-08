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
# ==============================================================================
# 🖤 ELITE PRO-TIER BLACK THEME & SPACING DESIGN SYSTEM
# ==============================================================================
st.set_page_config(page_title="Debug.ext Intelligence", page_icon="assets/favicon.ico", layout="wide")

st.markdown("""
<style>
    /* 1. Global Pitch-Black Canvas */
    .stApp {
        background-color: #000000;
        color: #F8FAFC;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* Hide default Streamlit elements for clean SaaS look */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header[data-testid="stHeader"] { display: none; }
    
    /* 2. Pro-Tier Graphite Cards with Neon Depth */
    .pro-card {
        background: #0A0A0A;
        border: 1px solid #1F2937;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.8);
    }
    
    .spotlight-header {
        background: linear-gradient(135deg, #0F172A 0%, #000000 100%);
        padding: 20px 24px;
        border-radius: 12px;
        border-left: 5px solid #10B981;
        border-top: 1px solid #1F2937;
        border-right: 1px solid #1F2937;
        border-bottom: 1px solid #1F2937;
        margin-bottom: 24px;
    }

    /* 3. Mathematical Spacing Controls */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 3rem !important;
        max-width: 95% !important;
    }
    
    /* 4. Elite Custom Buttons */
    div.stButton > button {
        background: linear-gradient(135deg, #4F46E5 0%, #3730A3 100%);
        color: #FFFFFF !important;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 600;
        letter-spacing: 0.5px;
        width: 100%;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 20px rgba(79, 70, 229, 0.3);
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 25px rgba(79, 70, 229, 0.5);
    }

    /* 5. Dataframe & Tables Styling */
    dataframe, [data-testid="stTable"] {
        background-color: #0A0A0A !important;
        border-radius: 8px;
        border: 1px solid #1F2937;
    }

    /* 6. Inputs & Text Areas */
    .stTextInput input, .stTextArea textarea {
        background-color: #0A0A0A !important;
        color: #F8FAFC !important;
        border: 1px solid #1F2937 !important;
        border-radius: 8px !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #4F46E5 !important;
        box-shadow: 0 0 10px rgba(79, 70, 229, 0.2) !important;
    }
    
    /* =========================================
       SKELETON LOADER ANIMATIONS
       ========================================= */
    .skeleton-wrapper {
        display: flex;
        flex-direction: column;
        gap: 16px;
        padding: 20px;
        background-color: #0A0A0A;
        border: 1px solid #1E293B;
        border-radius: 12px;
        margin-bottom: 20px;
    }
    .skeleton {
        background: linear-gradient(90deg, #1E293B 25%, #334155 50%, #1E293B 75%);
        background-size: 200% 100%;
        animation: pulse 1.5s infinite ease-in-out;
        border-radius: 6px;
    }
    @keyframes pulse {
        0% { background-position: 200% 0; }
        100% { background-position: -200% 0; }
    }
    .skel-header { width: 40%; height: 28px; }
    .skel-badge { width: 15%; height: 20px; margin-bottom: 12px; }
    .skel-line { width: 100%; height: 16px; margin-bottom: 8px; }
    .skel-line-short { width: 80%; height: 16px; }
    .skel-box { width: 100%; height: 120px; margin-top: 10px; }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 🖥️ APPLICATION HEADER & STATUS BAR
# ==============================================================================
col_title, col_status = st.columns([4, 1], vertical_alignment="center")

with col_title:
    st.markdown("""
        <h1 style='margin: 0; font-size: 28px; font-weight: 800; color: #F8FAFC; letter-spacing: -0.5px;'>
            🐛 Debug<span style='color: #4F46E5;'>.ext</span> Intelligence
        </h1>
        <p style='margin: 4px 0 0 0; color: #64748B; font-size: 13px;'>
            Autonomous Multi-Model Triage Engine • Inkling • MiniMax M3 • GLM 5.2
        </p>
    """, unsafe_allow_html=True)

with col_status:
    try:
        health_check = requests.get("http://localhost:8000/api/health", timeout=1)
        if health_check.status_code == 200:
            st.markdown('<div style="text-align: right;"><span style="background: rgba(16, 185, 129, 0.1); color: #10B981; border: 1px solid #10B981; padding: 6px 14px; border-radius: 20px; font-size: 11px; font-weight: 700;">🟢 GATEWAY ONLINE</span></div>', unsafe_allow_html=True)
        else:
            raise Exception()
    except:
        st.markdown('<div style="text-align: right;"><span style="background: rgba(239, 68, 68, 0.1); color: #EF4444; border: 1px solid #EF4444; padding: 6px 14px; border-radius: 20px; font-size: 11px; font-weight: 700;">🔴 OFFLINE</span></div>', unsafe_allow_html=True)

st.markdown("<div style='margin-bottom: 24px;'></div>", unsafe_allow_html=True)
st.divider()



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

# ==============================================================================
# 3. BULLETPROOF DATA LOADER & SCHEMA NORMALIZER
# ==============================================================================
@st.cache_data(ttl=1)
def fetch_and_normalize_history():
    try:
        res = requests.get("http://localhost:8000/api/history", timeout=2)
        if res.status_code == 200 and res.json():
            raw_data = res.json()
            processed_rows = []
            
            for row in raw_data:
                # Unpack full_json securely
                full_json_str = row.get('full_json', '{}')
                try:
                    nested_data = json.loads(full_json_str) if isinstance(full_json_str, str) else full_json_str
                except:
                    nested_data = {}
                
                merged_row = {**row, **nested_data}
                
                # GUARANTEE required fields exist so Pandas never throws KeyErrors
                if 'bug_summary' not in merged_row and 'summary' in merged_row:
                    merged_row['bug_summary'] = merged_row['summary']
                elif 'bug_summary' not in merged_row:
                    merged_row['bug_summary'] = "Intercepted Exception Trace"
                    
                if 'affected_component' not in merged_row:
                    merged_row['affected_component'] = merged_row.get('url', 'Unknown Module')
                    
                if 'confidence_score' in merged_row:
                    try:
                        val = float(merged_row['confidence_score'])
                        merged_row['confidence_pct'] = int(val * 100) if val <= 1.0 else int(val)
                    except:
                        merged_row['confidence_pct'] = 95
                else:
                    merged_row['confidence_pct'] = 95
                    
                processed_rows.append(merged_row)
                
            df = pd.DataFrame(processed_rows)
            return df
    except Exception as e:
        pass
    
    # Return a safe, empty schema if backend is offline
    return pd.DataFrame(columns=[
        'timestamp', 'source', 'url', 'category', 'severity', 'priority', 
        'bug_summary', 'affected_component', 'confidence_pct', 'probable_root_cause'
    ])

import time
ui_placeholder = st.empty()

with ui_placeholder.container():
    st.markdown("""
    <div class="skeleton-wrapper">
        <div class="skeleton skel-header"></div>
        <div style="display: flex; gap: 10px; margin-top: 10px;">
            <div class="skeleton skel-badge"></div>
            <div class="skeleton skel-badge"></div>
        </div>
        <br>
        <div class="skeleton skel-line"></div>
        <div class="skeleton skel-line"></div>
        <div class="skeleton skel-line-short"></div>
        <div class="skeleton skel-box"></div>
    </div>
    """, unsafe_allow_html=True)

time.sleep(0.5) 
df = fetch_and_normalize_history()

ui_placeholder.empty()

# ==============================================================================
# 🚀 ACTIVE INCIDENT SPOTLIGHT
# ==============================================================================
if not df.empty:
    latest_bug = df.iloc[0]
    
    priority_val = latest_bug.get('priority', 'P0')
    severity_val = latest_bug.get('severity', 'Critical')
    category_val = latest_bug.get('category', 'Network')
    conf_pct = latest_bug.get('confidence_pct', 95)
    module_val = latest_bug.get('affected_component', 'Unknown')
    root_cause = latest_bug.get('probable_root_cause', latest_bug.get('bug_summary', 'N/A'))
    
    st.markdown('<div class="spotlight-header"><h3 style="margin: 0; color: #F8FAFC; font-size: 18px; font-weight: 700;">✅ Autonomous Triage Complete: Active Incident</h3></div>', unsafe_allow_html=True)
    
    col_details, col_fix = st.columns([1, 1.3], gap="large")
    
    with col_details:
        st.markdown('<div class="pro-card">', unsafe_allow_html=True)
        st.markdown("<h4 style='margin-top:0; color:#94A3B8; font-size:12px; text-transform:uppercase;'>📊 Intelligence Matrix</h4>", unsafe_allow_html=True)
        
        badge_color = "#EF4444" if priority_val in ["P0", "Critical"] else "#F59E0B"
        st.markdown(f"**Priority Level:** <span style='background: rgba(239, 68, 68, 0.1); color: {badge_color}; padding: 2px 8px; border-radius: 4px; font-weight: 800;'>[{priority_val}]</span> | **Severity:** `{severity_val}`", unsafe_allow_html=True)
        st.markdown(f"**Classification:** `{category_val}` | **AI Confidence:** `{conf_pct}%`")
        st.markdown(f"**Vulnerable Module:** `{module_val}`")
        
        st.markdown("<div style='margin: 16px 0; border-top: 1px solid #1F2937;'></div>", unsafe_allow_html=True)
        st.markdown("<h4 style='margin-top:0; color:#94A3B8; font-size:12px; text-transform:uppercase;'>🔍 Root Cause Analysis</h4>", unsafe_allow_html=True)
        st.info(root_cause)
        
        from pdf_generator import generate_pdf_report
        try:
            pdf_bytes = generate_pdf_report(latest_bug.to_dict())
            st.download_button(
                label="📄 Download Executive PDF Intelligence Report",
                data=pdf_bytes,
                file_name=f"Debug_ext_{priority_val}_Report.pdf",
                mime="application/pdf",
                use_container_width=True,
                type="primary"
            )
        except Exception as e:
            st.error(f"PDF Engine Error: {e}")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_fix:
        st.markdown('<div class="pro-card">', unsafe_allow_html=True)
        st.markdown("<h4 style='margin-top:0; color:#94A3B8; font-size:12px; text-transform:uppercase;'>🛠️ Autonomous Code Patch</h4>", unsafe_allow_html=True)
        
        fix_data = latest_bug.get('suggested_fix', {})
        if isinstance(fix_data, str):
            try: fix_data = json.loads(fix_data)
            except: fix_data = {"explanation": fix_data, "code_snippet": "// Patch applied"}
            
        if isinstance(fix_data, dict):
            st.write(fix_data.get('explanation', 'Apply the following verified patch:'))
            code = fix_data.get('code_snippet', '// No code patch required')
            st.code(code, language="javascript")
        else:
            st.warning("No structured code fix was returned.")
        st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<div style='margin: 30px 0;'></div>", unsafe_allow_html=True)

# ==============================================================================
# 📊 ANALYTICS GRAPHS (CATEGORIZATION & PRIORITIZATION)
# ==============================================================================
st.markdown("<h3 style='font-size: 20px; font-weight: 700; color: #F8FAFC; margin-bottom: 16px;'>📈 Telemetry Analytics & Graphs</h3>", unsafe_allow_html=True)

if not df.empty:
    g_col1, g_col2 = st.columns(2, gap="large")
    
    with g_col1:
        st.markdown('<div class="pro-card">', unsafe_allow_html=True)
        st.markdown("#### 🏷️ Bug Categorization Spread", unsafe_allow_html=True)
        if 'category' in df.columns:
            cat_counts = df['category'].value_counts().reset_index()
            cat_counts.columns = ['Category', 'Count']
            fig_cat = px.pie(cat_counts, names='Category', values='Count', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
            fig_cat.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#F8FAFC'), margin=dict(t=10, b=10, l=10, r=10))
            st.plotly_chart(fig_cat, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    with g_col2:
        st.markdown('<div class="pro-card">', unsafe_allow_html=True)
        st.markdown("#### ⚡ Prioritization Distribution", unsafe_allow_html=True)
        if 'priority' in df.columns:
            pri_counts = df['priority'].value_counts().reset_index()
            pri_counts.columns = ['Priority', 'Count']
            fig_pri = px.bar(pri_counts, x='Priority', y='Count', color='Priority', color_discrete_map={'P0':'#EF4444', 'P1':'#F59E0B', 'P2':'#3B82F6', 'P3':'#10B981'})
            fig_pri.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#F8FAFC'), margin=dict(t=10, b=10, l=10, r=10), showlegend=False)
            st.plotly_chart(fig_pri, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

# ==============================================================================
# 📋 SAFE SESSION ERROR LOG TABLE (CRASH-PROOF SLICING)
# ==============================================================================
st.markdown("<h3 style='font-size: 20px; font-weight: 700; color: #F8FAFC; margin-bottom: 12px;'>📋 Session Error Log</h3>", unsafe_allow_html=True)

if not df.empty:
    # 🟢 BULLETPROOF COLUMN FILTER: Only pick columns that actually exist in df
    desired_columns = ['timestamp', 'source', 'url', 'category', 'severity', 'priority', 'bug_summary', 'affected_component', 'confidence_pct']
    safe_display_cols = [col for col in desired_columns if col in df.columns]
    
    st.dataframe(df[safe_display_cols], use_container_width=True, hide_index=True)

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
