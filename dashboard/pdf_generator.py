import tempfile
from fpdf import FPDF
from datetime import datetime

class ReportPDF(FPDF):
    def __init__(self):
        super().__init__(format='A4')
        # Pro Spacing: 20mm margins give the document breathing room
        self.set_margins(left=20, top=20, right=20)
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
        self.set_font("helvetica", "B", 22)
        self.set_text_color(79, 70, 229)  # Indigo
        self.cell(0, 10, "Debug.ext | AI Triage Intelligence", ln=True, align="L")
        
        self.set_font("helvetica", "I", 10)
        self.set_text_color(100, 116, 139) # Slate Gray
        self.cell(0, 6, f"Generated autonomously on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} IST", ln=True, align="L")
        
        # Thicker, styled underline for the header
        self.set_draw_color(79, 70, 229)
        self.set_line_width(0.5)
        self.line(20, 38, 190, 38)
        self.ln(12) # Padding below header
        
    def footer(self):
        self.set_y(-20)
        self.set_font("helvetica", "I", 9)
        self.set_text_color(148, 163, 184)
        self.cell(0, 10, f"Page {self.page_no()} | Debug.ext Multi-Model Triage Architecture", 0, 0, "C")

    def chapter_title(self, title):
        self.ln(6) # Padding above section
        self.set_font("helvetica", "B", 13)
        self.set_text_color(15, 23, 42)
        self.cell(0, 8, title, ln=True)
        # Subtle section underline
        self.set_draw_color(203, 213, 225)
        self.set_line_width(0.2)
        self.line(20, self.get_y(), 190, self.get_y())
        self.ln(4) # Padding below section title

    def chapter_body(self, body):
        self.set_font("helvetica", "", 11)
        self.set_text_color(51, 65, 85)
        # 6mm line height for readability
        self.multi_cell(0, 6, body)
        self.ln(2)
        
    def draw_metadata_table(self, bug_data):
        self.ln(4)
        self.set_font("helvetica", "B", 10)
        self.set_fill_color(241, 245, 249)
        self.set_draw_color(203, 213, 225)
        self.set_text_color(15, 23, 42)
        
        # Row 1
        self.cell(42, 10, " Bug Category", border=1, fill=True)
        self.set_font("helvetica", "", 10)
        self.cell(43, 10, f" {bug_data.get('category', 'Unknown')}", border=1)
        
        self.set_font("helvetica", "B", 10)
        self.cell(42, 10, " AI Confidence", border=1, fill=True)
        self.set_font("helvetica", "", 10)
        conf = bug_data.get('confidence_score', 0)
        self.cell(43, 10, f" {int(conf * 100)}%", border=1, ln=True)

        # Row 2
        self.set_font("helvetica", "B", 10)
        self.cell(42, 10, " Affected Module", border=1, fill=True)
        self.set_font("helvetica", "", 10)
        self.cell(43, 10, f" {bug_data.get('affected_component', 'Unknown')}", border=1)
        
        self.set_font("helvetica", "B", 10)
        self.cell(42, 10, " Impact Score", border=1, fill=True)
        self.set_font("helvetica", "", 10)
        self.cell(43, 10, " 9.0 / 10", border=1, ln=True)
        self.ln(6)

    def render_code_block(self, code_text):
        self.ln(2)
        self.set_font("courier", "", 10)
        self.set_fill_color(15, 23, 42)    # Dark IDE Background
        self.set_text_color(56, 189, 248)  # Neon Blue Text
        # Add internal padding to the code block
        self.cell(0, 4, "", fill=True, ln=True) 
        self.multi_cell(0, 5, f"  {code_text}", fill=True)
        self.cell(0, 4, "", fill=True, ln=True)
        self.ln(6)

def sanitize(text):
    if not text:
        return "N/A"
    return str(text).encode('latin-1', 'replace').decode('latin-1')

def generate_pdf_report(bug_data: dict) -> bytes:
    pdf = ReportPDF()
    pdf.add_page()
    
    # 1. Severity Badge Display
    pdf.set_font("helvetica", "B", 12)
    pdf.set_fill_color(254, 226, 226) # Light Red Background
    pdf.set_text_color(220, 38, 38)   # Dark Red Text
    pdf.set_draw_color(248, 113, 113) # Red Border
    badge_text = f" [{bug_data.get('priority', 'P0')}] {bug_data.get('severity', 'Critical')} Severity "
    pdf.cell(pdf.get_string_width(badge_text) + 4, 10, badge_text, border=1, fill=True, ln=True)
    
    # 2. Metadata Grid
    pdf.draw_metadata_table(bug_data)
    
    # 3. Content Sections
    pdf.chapter_title("1. Bug Summary & Executive Overview")
    pdf.chapter_body(sanitize(bug_data.get('bug_summary')))
    
    pdf.chapter_title("2. Probable Root Cause")
    pdf.chapter_body(sanitize(bug_data.get('probable_root_cause')))
    
    pdf.chapter_title("3. Suggested Fix & Code Patch")
    fix_data = bug_data.get('suggested_fix', {})
    pdf.chapter_body(sanitize(fix_data.get('explanation', 'Apply the following code patch:')))
    pdf.render_code_block(sanitize(fix_data.get('code_snippet', '// No patch required')))
    
    pdf.chapter_title("4. Missing Information Required from QA")
    pdf.set_font("helvetica", "", 11)
    pdf.set_text_color(51, 65, 85)
    missing = bug_data.get('missing_information', [])
    if not missing:
        pdf.cell(0, 6, "All necessary diagnostic information was provided.", ln=True)
    else:
        for item in missing:
            pdf.cell(0, 6, f"[ ] {sanitize(item)}", ln=True)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pdf.output(tmp.name)
        tmp.seek(0)
        return tmp.read()
