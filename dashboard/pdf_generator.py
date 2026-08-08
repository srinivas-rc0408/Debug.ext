import tempfile
from fpdf import FPDF
from datetime import datetime

class ReportPDF(FPDF):
    def header(self):
        # Premium Enterprise Header
        self.set_font("helvetica", "B", 20)
        self.set_text_color(79, 70, 229)  # Indigo
        self.cell(0, 10, "Debug.ext | AI Triage Intelligence Report", ln=True, align="L")
        
        self.set_font("helvetica", "I", 10)
        self.set_text_color(148, 163, 184) # Slate Gray
        self.cell(0, 6, f"Generated autonomously on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} IST", ln=True, align="L")
        self.set_draw_color(79, 70, 229)
        self.line(10, 28, 200, 28)
        self.ln(10)
        
    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(148, 163, 184)
        self.cell(0, 10, f"Page {self.page_no()} | Debug.ext Multi-Model Triage Architecture", 0, 0, "C")

    def chapter_title(self, title):
        self.ln(4)
        self.set_font("helvetica", "B", 12)
        self.set_fill_color(30, 41, 59)    # Dark Slate Background
        self.set_text_color(248, 250, 252) # White Text
        self.cell(0, 8, f"  {title}", ln=True, fill=True)
        self.ln(2)

    def chapter_body(self, body):
        self.set_font("helvetica", "", 10)
        self.set_text_color(51, 65, 85)
        self.multi_cell(0, 5, body)
        self.ln(4)
        
    def draw_metadata_table(self, bug_data):
        """Renders a clean, 2-column metrics table"""
        self.set_font("helvetica", "B", 10)
        self.set_fill_color(241, 245, 249)
        self.set_text_color(15, 23, 42)
        
        # Row 1
        self.cell(45, 8, " Priority & Severity:", border=1, fill=True)
        self.set_font("helvetica", "", 10)
        self.cell(50, 8, f" [{bug_data.get('priority', 'N/A')}] {bug_data.get('severity', 'N/A')}", border=1)
        
        self.set_font("helvetica", "B", 10)
        self.cell(45, 8, " AI Confidence:", border=1, fill=True)
        self.set_font("helvetica", "", 10)
        conf = bug_data.get('confidence_score', 0)
        self.cell(50, 8, f" {int(conf * 100)}%", border=1, ln=True)

        # Row 2
        self.set_font("helvetica", "B", 10)
        self.cell(45, 8, " Bug Category:", border=1, fill=True)
        self.set_font("helvetica", "", 10)
        self.cell(50, 8, f" {bug_data.get('category', 'Unknown')}", border=1)
        
        self.set_font("helvetica", "B", 10)
        self.cell(45, 8, " Affected Module:", border=1, fill=True)
        self.set_font("helvetica", "", 10)
        self.cell(50, 8, f" {bug_data.get('affected_component', 'Unknown')}", border=1, ln=True)
        self.ln(5)

    def render_code_block(self, code_text):
        """Renders a dark-mode IDE style code block"""
        self.set_font("courier", "", 9)
        self.set_fill_color(15, 23, 42)    # Very dark blue/black
        self.set_text_color(56, 189, 248)  # Light neon blue for code
        self.multi_cell(0, 5, code_text, fill=True, border=1)
        self.ln(4)

def sanitize(text):
    """Prevents UnicodeEncodeError on special log characters"""
    if not text:
        return "N/A"
    return str(text).encode('latin-1', 'replace').decode('latin-1')

def generate_pdf_report(bug_data: dict) -> bytes:
    pdf = ReportPDF()
    pdf.add_page()
    
    # 1. Executive Summary
    pdf.set_font("helvetica", "B", 14)
    pdf.set_text_color(15, 23, 42)
    pdf.multi_cell(0, 6, sanitize(bug_data.get('bug_summary', 'Bug Triage Report')))
    pdf.ln(2)
    
    # 2. Metadata Table
    pdf.draw_metadata_table(bug_data)
    
    # 3. Root Cause Analysis
    pdf.chapter_title("1. Probable Root Cause")
    pdf.chapter_body(sanitize(bug_data.get('probable_root_cause')))
    
    # 4. Technical Breakdown
    pdf.chapter_title("2. Technical Execution Analysis")
    pdf.chapter_body(sanitize(bug_data.get('technical_analysis')))
    
    # 5. Remediation & Suggested Fix (The Pro Feature)
    pdf.chapter_title("3. Suggested Fix & Code Patch")
    fix_data = bug_data.get('suggested_fix', {})
    
    # Explanation
    explanation = fix_data.get('explanation', 'Apply the following code patch to resolve the issue.')
    pdf.chapter_body(sanitize(explanation))
    
    # Dark Mode Code Block
    code_snippet = fix_data.get('code_snippet', '// No code patch required')
    pdf.render_code_block(sanitize(code_snippet))
    
    # 6. Missing Information Checklist
    pdf.chapter_title("4. Missing Information Required from QA")
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(51, 65, 85)
    missing_info = bug_data.get('missing_information', [])
    if not missing_info:
        pdf.cell(0, 6, "All necessary diagnostic information was provided.", ln=True)
    else:
        for item in missing_info:
            pdf.cell(0, 6, f" [ ] {sanitize(item)}", ln=True)

    # 7. Metrics & Impact
    metrics = bug_data.get('metrics', {})
    if metrics:
        pdf.chapter_title("5. Effort & Impact Estimation")
        est_time = metrics.get('estimated_fix_time_hours', 'N/A')
        impact = metrics.get('business_impact_score', 'N/A')
        pdf.chapter_body(f"Estimated Engineering Fix Time: {est_time} hours\nCalculated Business Impact Score (1-10): {impact}")

    # Output to bytes
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pdf.output(tmp.name)
        tmp.seek(0)
        return tmp.read()
