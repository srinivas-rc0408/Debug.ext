with open('dashboard/app.py', 'r') as f:
    text = f.read()

new_css = """# ==============================================================================
# 🖤 ELITE PRO-TIER BLACK THEME & SPACING DESIGN SYSTEM
# ==============================================================================
st.set_page_config(page_title="Debug.ext Intelligence", page_icon="assets/favicon.ico", layout="wide")

st.markdown(\"\"\"
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
\"\"\", unsafe_allow_html=True)

# ==============================================================================
# 🖥️ APPLICATION HEADER & STATUS BAR
# ==============================================================================
col_title, col_status = st.columns([4, 1], vertical_alignment="center")

with col_title:
    st.markdown(\"\"\"
        <h1 style='margin: 0; font-size: 28px; font-weight: 800; color: #F8FAFC; letter-spacing: -0.5px;'>
            🐛 Debug<span style='color: #4F46E5;'>.ext</span> Intelligence
        </h1>
        <p style='margin: 4px 0 0 0; color: #64748B; font-size: 13px;'>
            Autonomous Multi-Model Triage Engine • Inkling • MiniMax M3 • GLM 5.2
        </p>
    \"\"\", unsafe_allow_html=True)

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
"""

new_fetch = """# ==============================================================================
# 3. DATA FETCHING & SKELETON
# ==============================================================================
@st.cache_data(ttl=1)
def fetch_history():
    try:
        res = requests.get("http://localhost:8000/api/history", timeout=2)
        if res.status_code == 200 and res.json():
            return pd.DataFrame(res.json())
    except:
        pass
    return pd.DataFrame()

import time
ui_placeholder = st.empty()

with ui_placeholder.container():
    st.markdown(\"\"\"
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
    \"\"\", unsafe_allow_html=True)

time.sleep(0.5) 
df = fetch_history()

ui_placeholder.empty()

# ==============================================================================
# 🚀 PRO SPOTLIGHT: ACTIVE INCIDENT REMEDIATION
# ==============================================================================
if not df.empty:
    latest_bug = df.iloc[0]
    
    summary_text = latest_bug.get('bug_summary', latest_bug.get('summary', 'Active Incident'))
    component_text = latest_bug.get('affected_component', latest_bug.get('url', 'Unknown Module'))
    priority_val = latest_bug.get('priority', 'P0')
    severity_val = latest_bug.get('severity', 'Critical')
    category_val = latest_bug.get('category', 'Network')
    
    st.markdown(\"\"\"
        <div class="spotlight-header">
            <h3 style="margin: 0; color: #F8FAFC; font-size: 18px; font-weight: 700;">✅ Autonomous Triage Complete: Active Incident</h3>
        </div>
    \"\"\", unsafe_allow_html=True)
    
    col_details, col_fix = st.columns([1, 1.3], gap="large")
    
    with col_details:
        st.markdown('<div class="pro-card">', unsafe_allow_html=True)
        st.markdown("<h4 style='margin-top:0; color:#94A3B8; font-size:12px; text-transform:uppercase; letter-spacing:1px;'>📊 Intelligence Matrix</h4>", unsafe_allow_html=True)
        
        # Priority Badge Color Coding
        badge_color = "#EF4444" if priority_val in ["P0", "Critical"] else "#F59E0B"
        st.markdown(f"**Priority Level:** <span style='background: rgba(239, 68, 68, 0.1); color: {badge_color}; padding: 2px 8px; border-radius: 4px; font-weight: 800;'>[{priority_val}]</span> | **Severity:** `{severity_val}`", unsafe_allow_html=True)
        st.markdown(f"**Classification:** `{category_val}`")
        st.markdown(f"**Vulnerable Module:** `{component_text}`")
        
        st.markdown("<div style='margin: 16px 0; border-top: 1px solid #1F2937;'></div>", unsafe_allow_html=True)
        st.markdown("<h4 style='margin-top:0; color:#94A3B8; font-size:12px; text-transform:uppercase; letter-spacing:1px;'>🔍 Root Cause Analysis</h4>", unsafe_allow_html=True)
        st.info(latest_bug.get('probable_root_cause', summary_text))
        
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
        st.markdown("<h4 style='margin-top:0; color:#94A3B8; font-size:12px; text-transform:uppercase; letter-spacing:1px;'>🛠️ Autonomous Code Patch</h4>", unsafe_allow_html=True)
        
        fix_data = latest_bug.get('suggested_fix', {})
        if isinstance(fix_data, dict):
            st.write(fix_data.get('explanation', 'Apply the following verified patch:'))
            code = fix_data.get('code_snippet', '// No code patch required')
            st.code(code, language="javascript")
        else:
            st.warning("No structured code fix was returned by the AI gateway.")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<div style='margin: 30px 0;'></div>", unsafe_allow_html=True)

    # ==============================================================================
    # 📋 SESSION ERROR LOG TABLE (PRO DARK THEME)
    # ==============================================================================
    st.markdown(\"\"\"
        <h3 style='font-size: 20px; font-weight: 700; color: #F8FAFC; margin-bottom: 4px;'>📋 Session Error Log</h3>
        <p style='color: #64748B; font-size: 13px; margin-bottom: 16px;'>Complete telemetry history of intercepted exceptions, prioritized by autonomous scoring.</p>
    \"\"\", unsafe_allow_html=True)
    
    available_cols = df.columns.tolist()
    target_cols = ['priority', 'severity', 'category', 'bug_summary', 'summary', 'affected_component', 'url']
    valid_display_cols = [col for col in target_cols if col in available_cols]
    
    if valid_display_cols:
        st.dataframe(df[valid_display_cols], use_container_width=True, hide_index=True)
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)

"""

idx1 = text.find("# ==========================================\n# 1. PAGE CONFIGURATION & STYLING")
idx2 = text.find("</style>\n\"\"\", unsafe_allow_html=True)") + len("</style>\n\"\"\", unsafe_allow_html=True)")

if idx1 != -1 and idx2 != -1:
    text = text[:idx1] + new_css + text[idx2:]

idx3 = text.find("# ==========================================\n# 3. DATA FETCHING")
idx4 = text.find("# ==========================================\n# HEADER")

if idx3 != -1 and idx4 != -1:
    text = text[:idx3] + new_fetch + text[idx4:]

idx5 = text.find("# ==========================================\n# HEADER")
idx6 = text.find("# ==========================================\n# TABS")

if idx5 != -1 and idx6 != -1:
    text = text[:idx5] + text[idx6:]

with open('dashboard/app.py', 'w') as f:
    f.write(text)

print("SUCCESS")
