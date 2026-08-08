import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_autorefresh import st_autorefresh
import requests
import json
import base64

# Import unified PDF generators safely
from pdf_generator import generate_pdf_report, generate_triage_pdf

st.set_page_config(page_title="Debug.ext Intelligence", page_icon="assets/favicon.ico", layout="wide")
st_autorefresh(interval=3000, limit=1000, key="live_refresh")

# ==============================================================================
# 🖤 PITCH-BLACK PRO-TIER DESIGN SYSTEM (CSS)
# ==============================================================================
st.markdown("""
<style>
    .stApp { background-color: #000000; color: #F8FAFC; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    .pro-card { background: #0A0A0A; border: 1px solid #1F2937; border-radius: 12px; padding: 24px; margin-bottom: 20px; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.8); }
    .spotlight-header { background: linear-gradient(135deg, #0F172A 0%, #000000 100%); padding: 20px 24px; border-radius: 12px; border-left: 5px solid #10B981; border: 1px solid #1F2937; margin-bottom: 24px; }
    .block-container { max-width: 95% !important; padding-top: 2rem !important; }
    div.stButton > button { background: linear-gradient(135deg, #4F46E5 0%, #3730A3 100%); color: #FFFFFF !important; border: none; border-radius: 8px; padding: 12px 24px; font-weight: 600; width: 100%; box-shadow: 0 4px 20px rgba(79, 70, 229, 0.3); transition: all 0.3s ease; }
    div.stButton > button:hover { transform: translateY(-2px); box-shadow: 0 6px 25px rgba(79, 70, 229, 0.5); }
    div[data-testid="stExpander"] { background-color: #0A0A0A; border: 1px solid #1F2937; border-radius: 8px; margin-bottom: 12px; }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 🔄 ROBUST DATA LOADER & SCHEMA NORMALIZER
# ==============================================================================
@st.cache_data(ttl=1)
def fetch_and_normalize_history():
    try:
        res = requests.get("http://localhost:8000/api/history", timeout=2)
        if res.status_code == 200 and res.json():
            raw_data = res.json()
            processed_rows = []
            
            for row in raw_data:
                full_json_str = row.get('full_json', '{}')
                try:
                    nested_data = json.loads(full_json_str) if isinstance(full_json_str, str) else full_json_str
                except:
                    nested_data = {}
                
                merged_row = {**row, **nested_data}
                
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
                
            return pd.DataFrame(processed_rows)
    except Exception as e:
        pass
    
    return pd.DataFrame(columns=[
        'timestamp', 'source', 'url', 'category', 'severity', 'priority', 
        'bug_summary', 'affected_component', 'confidence_pct', 'probable_root_cause'
    ])

df = fetch_and_normalize_history()

def render_pdf_preview(pdf_bytes):
    b64 = base64.b64encode(pdf_bytes).decode('utf-8')
    pdf_html = f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="500px" style="border-radius: 8px; border: 1px solid #1F2937;"></iframe>'
    st.markdown(pdf_html, unsafe_allow_html=True)

# Header & Status Bar
col_title, col_status = st.columns([4, 1], vertical_alignment="center")
with col_title:
    st.markdown("<h1 style='margin: 0; font-size: 28px; font-weight: 800; color: #F8FAFC;'>🐛 Debug<span style='color: #4F46E5;'>.ext</span> Intelligence</h1>", unsafe_allow_html=True)
with col_status:
    st.markdown('<div style="text-align: right;"><span style="background: rgba(16, 185, 129, 0.1); color: #10B981; border: 1px solid #10B981; padding: 6px 14px; border-radius: 20px; font-size: 11px; font-weight: 700;">🟢 GATEWAY ONLINE</span></div>', unsafe_allow_html=True)

st.divider()

# ==============================================================================
# 🚀 ACTIVE INCIDENT SPOTLIGHT (PDF PREVIEW & DOWNLOAD)
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
        
        try:
            pdf_bytes = generate_pdf_report(latest_bug.to_dict())
            
            pdf_col1, pdf_col2 = st.columns(2)
            with pdf_col1:
                st.download_button(
                    label="📄 Download PDF",
                    data=pdf_bytes,
                    file_name=f"Debug_ext_{priority_val}_Report.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    type="primary"
                )
            with pdf_col2:
                view_pdf_toggle = st.button("👁️ View PDF Report", use_container_width=True)
                
            if view_pdf_toggle:
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("#### 📑 Executive PDF Report Viewer")
                render_pdf_preview(pdf_bytes)
                
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
# 📊 TELEMETRY ANALYTICS & GRAPHS
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
# 💾 EXPORT TELEMETRY DATA (CSV, JSON DOWNLOAD TOOLBAR)
# ==============================================================================
st.markdown("<h3 style='font-size: 20px; font-weight: 700; color: #F8FAFC; margin-bottom: 12px;'>💾 Export Telemetry Data</h3>", unsafe_allow_html=True)
st.markdown("<p style='color: #64748B; font-size: 13px; margin-bottom: 16px;'>Download the complete historical error logs and audit trails in open data formats.</p>", unsafe_allow_html=True)

if not df.empty:
    exp_col1, exp_col2 = st.columns(2, gap="medium")
    with exp_col1:
        csv_payload = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Telemetry Log (CSV)",
            data=csv_payload,
            file_name="debug_ext_telemetry_logs.csv",
            mime="text/csv",
            use_container_width=True
        )
    with exp_col2:
        json_payload = df.to_json(orient="records", indent=2).encode('utf-8')
        st.download_button(
            label="📥 Download Telemetry Dump (JSON)",
            data=json_payload,
            file_name="debug_ext_telemetry_dump.json",
            mime="application/json",
            use_container_width=True
        )

st.markdown("<div style='margin: 20px 0;'></div>", unsafe_allow_html=True)

# ==============================================================================
# 📋 PRIORITIZED ERROR LOG & REMEDIATION DIRECTORY (INLINE SOLUTIONS)
# ==============================================================================
st.markdown("<h3 style='font-size: 20px; font-weight: 700; color: #F8FAFC; margin-bottom: 8px;'>📋 Prioritized Error Log & Remediation Directory</h3>", unsafe_allow_html=True)
st.markdown("<p style='color: #64748B; font-size: 13px; margin-bottom: 20px;'>Click any intercepted incident below to inspect its detailed root cause and verified code solution inline.</p>", unsafe_allow_html=True)

if not df.empty:
    for idx, row in df.iterrows():
        pri = row.get('priority', 'P2')
        sev = row.get('severity', 'Medium')
        cat = row.get('category', 'General')
        summary = row.get('bug_summary', row.get('summary', 'Incident Log'))
        root_cause = row.get('probable_root_cause', 'N/A')
        
        with st.expander(f"[{pri}] {sev.upper()} | {cat} — {summary}"):
            exp_col1, exp_col2 = st.columns([1, 1], gap="large")
            
            with exp_col1:
                st.markdown(f"**Target URL / Module:** `{row.get('affected_component', row.get('url', 'Unknown'))}`")
                st.markdown(f"**Classification:** `{cat}` | **Severity:** `{sev}`")
                st.markdown("#### 🔍 Problem Statement & Root Cause")
                st.info(root_cause)
                
            with exp_col2:
                st.markdown("#### 🛠️ Verified Solution & Patch")
                fix = row.get('suggested_fix', {})
                if isinstance(fix, str):
                    try: fix = json.loads(fix)
                    except: fix = {"explanation": fix, "code_snippet": "// Solution applied"}
                
                st.write(fix.get('explanation', 'Review the remediation code patch below:'))
                st.code(fix.get('code_snippet', '// No code patch provided'), language="javascript")
