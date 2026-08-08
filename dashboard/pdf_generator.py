import tempfile
from fpdf import FPDF
from datetime import datetime

class ReportPDF(FPDF):
    def header(self):
        # Enterprise Header
        self.set_font("helvetica", "B", 18)
        self.set_text_color(99, 102, 241)  # Indigo
        self.cell(0, 10, "Debug.ext - AI Triage Intelligence Report", ln=True, align="C")
        
        self.set_font("helvetica", "I", 10)
        self.set_text_color(148, 163, 184) # Slate
        self.cell(0, 8, f"Generated automatically on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align="C")
        self.ln(10)
        
    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(148, 163, 184)
        self.cell(0, 10, f"Page {self.page_no()} | Debug.ext Multi-Model Architecture", 0, 0, "C")

    def chapter_title(self, title):
        self.set_font("helvetica", "B", 12)
        self.set_fill_color(241, 245, 249) # Light slate background
        self.set_text_color(15, 23, 42)    # Dark slate text
        self.cell(0, 10, f"  {title}", ln=True, fill=True)
        self.ln(4)

    def chapter_body(self, body):
        self.set_font("helvetica", "", 11)
        self.set_text_color(51, 65, 85)
        self.multi_cell(0, 6, body)
        self.ln(8)

def sanitize(text):
    """Minute detail: Prevents PDF generation from crashing on weird log characters"""
    if not text:
        return "N/A"
    return str(text).encode('latin-1', 'replace').decode('latin-1')

def generate_pdf_report(bug_data: dict) -> bytes:
    pdf = ReportPDF()
    pdf.add_page()
    
    # 1. Severity & Priority Badges
    pdf.set_font("helvetica", "B", 14)
    if bug_data.get('severity') in ['Critical', 'High']:
        pdf.set_text_color(220, 38, 38) # Red for critical
    else:
        pdf.set_text_color(217, 119, 6) # Amber for warnings
        
    pdf.cell(0, 10, f"[{bug_data.get('priority', 'P2')}] {bug_data.get('severity', 'Medium')} Severity", ln=True)
    pdf.ln(2)
    
    # 2. Executive Summary
    pdf.chapter_title("1. Bug Summary")
    pdf.chapter_body(sanitize(bug_data.get('bug_summary')))
    
    # 3. System Context
    pdf.chapter_title("2. System Context & Metrics")
    context = (
        f"Category: {bug_data.get('category', 'Unknown')}\n"
        f"Affected Component: {bug_data.get('affected_component', 'Unknown')}\n"
        f"AI Confidence Score: {int(bug_data.get('confidence_score', 0.0) * 100)}%"
    )
    pdf.chapter_body(sanitize(context))
    
    # 4. Root Cause
    pdf.chapter_title("3. Probable Root Cause")
    pdf.chapter_body(sanitize(bug_data.get('probable_root_cause')))
    
    # 5. Technical Breakdown
    pdf.chapter_title("4. Technical Analysis")
    pdf.chapter_body(sanitize(bug_data.get('technical_analysis')))
    
    # 6. Code Fix
    pdf.chapter_title("5. Suggested Remediation & Code Patch")
    fix_data = bug_data.get('suggested_fix', {})
    fix_text = fix_data.get('explanation', '') + "\n\n" + fix_data.get('code_snippet', '')
    
    pdf.set_font("courier", "", 10)
    pdf.set_text_color(15, 23, 42)
    pdf.multi_cell(0, 5, sanitize(fix_text))
    pdf.ln(8)
    
    # 7. QA Missing Info
    pdf.chapter_title("6. Missing Information Required from QA")
    pdf.set_font("helvetica", "", 11)
    for item in bug_data.get('missing_information', []):
        pdf.cell(0, 6, f"- {sanitize(item)}", ln=True)

    # Save to buffer and return bytes
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pdf.output(tmp.name)
        tmp.seek(0)
        return tmp.read()
