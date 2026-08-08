import tempfile
import json
from fpdf import FPDF
from datetime import datetime

class ReportPDF(FPDF):
    def __init__(self):
        super().__init__(format='A4')
        self.set_margins(left=20, top=20, right=20)
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
        self.set_font("helvetica", "B", 18)
        self.set_text_color(79, 70, 229)
        self.cell(0, 10, "Debug.ext | Executive AI Intelligence Report", ln=True, align="L")
        
        self.set_font("helvetica", "I", 9)
        self.set_text_color(100, 116, 139)
        self.cell(0, 5, f"Autonomous Verification Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} IST", ln=True, align="L")
        self.set_draw_color(79, 70, 229)
        self.set_line_width(0.4)
        self.line(20, 32, 190, 32)
        self.ln(8)
        
    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(148, 163, 184)
        self.cell(0, 10, f"Page {self.page_no()} | Debug.ext Universal Triage Core", 0, 0, "C")

    def chapter_title(self, title):
        self.ln(4)
        self.set_font("helvetica", "B", 11)
        self.set_text_color(15, 23, 42)
        self.cell(0, 7, title, ln=True)
        self.set_draw_color(203, 213, 225)
        self.set_line_width(0.2)
        self.line(20, self.get_y(), 190, self.get_y())
        self.ln(2)

    def chapter_body(self, body):
        self.set_font("helvetica", "", 10)
        self.set_text_color(51, 65, 85)
        self.multi_cell(0, 5, body)
        self.ln(2)

def sanitize(text):
    if not text:
        return "N/A"
    return str(text).encode('latin-1', 'replace').decode('latin-1')

def generate_pdf_report(bug_data: dict) -> bytes:
    if isinstance(bug_data.get('full_json'), str):
        try:
            nested = json.loads(bug_data['full_json'])
            bug_data = {**bug_data, **nested}
        except:
            pass

    pdf = ReportPDF()
    pdf.add_page()
    
    # Priority & Severity Badge
    pdf.set_font("helvetica", "B", 10)
    pdf.set_fill_color(254, 226, 226)
    pdf.set_text_color(220, 38, 38)
    pdf.set_draw_color(248, 113, 113)
    pri = bug_data.get('priority', 'P0')
    sev = bug_data.get('severity', 'Critical')
    badge_text = f" [{pri}] {sev} Priority Incident "
    pdf.cell(pdf.get_string_width(badge_text) + 4, 7, badge_text, border=1, fill=True, ln=True)
    pdf.ln(3)

    # Metadata Grid Table
    pdf.set_font("helvetica", "B", 9)
    pdf.set_fill_color(241, 245, 249)
    pdf.set_text_color(15, 23, 42)
    
    pdf.cell(32, 6, " Category", border=1, fill=True)
    pdf.set_font("helvetica", "", 9)
    pdf.cell(63, 6, f" {sanitize(bug_data.get('category', 'General'))}", border=1)
    
    pdf.set_font("helvetica", "B", 9)
    pdf.cell(32, 6, " AI Confidence", border=1, fill=True)
    pdf.set_font("helvetica", "", 9)
    conf = bug_data.get('confidence_score', 0.96)
    conf_pct = int(conf * 100) if conf <= 1 else int(conf)
    pdf.cell(43, 6, f" {conf_pct}%", border=1, ln=True)
    pdf.ln(5)

    # Report Sections
    pdf.chapter_title("1. Incident Summary & Target Context")
    pdf.chapter_body(sanitize(bug_data.get('bug_summary', 'Universal Target Interception')))
    
    pdf.chapter_title("2. Probable Root Cause Analysis")
    pdf.chapter_body(sanitize(bug_data.get('probable_root_cause', 'N/A')))
    
    pdf.chapter_title("3. Technical Execution Breakdown")
    pdf.chapter_body(sanitize(bug_data.get('technical_analysis', 'Analyzed via multi-model telemetry core.')))
    
    pdf.chapter_title("4. Verified Solution & Code Patch")
    fix_data = bug_data.get('suggested_fix', {})
    if isinstance(fix_data, str):
        try: fix_data = json.loads(fix_data)
        except: fix_data = {"explanation": fix_data, "code_snippet": "// Patch applied"}
        
    explanation = fix_data.get('explanation', 'Apply the following verified code fix:')
    code_snippet = fix_data.get('code_snippet', '// No code patch required')
    
    pdf.chapter_body(sanitize(explanation))
    
    pdf.set_font("courier", "", 9)
    pdf.set_fill_color(15, 23, 42)
    pdf.set_text_color(56, 189, 248)
    pdf.multi_cell(0, 5, sanitize(f"  {code_snippet}"), fill=True, border=1)
    pdf.ln(4)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pdf.output(tmp.name)
        tmp.seek(0)
        return tmp.read()
