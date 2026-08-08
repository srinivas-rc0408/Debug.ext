import tempfile
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from fpdf import FPDF
from fpdf.enums import XPos, YPos

COLOR_BG_CODE = (15, 23, 42)
COLOR_TEXT_CODE = (56, 189, 248)
COLOR_HEADER = (10, 10, 10)
COLOR_MUTED = (110, 110, 110)

PRIORITY_COLORS = {
    "P0": (220, 38, 38),
    "P1": (234, 88, 12),
    "P2": (202, 138, 4),
    "P3": (22, 163, 74),
}

class DebugExtPDF(FPDF):
    def __init__(self, priority: str, category: str, confidence: int):
        super().__init__(format="A4")
        self.priority = priority
        self.category = category
        self.confidence = confidence
        self.set_auto_page_break(auto=True, margin=20)
        self.set_margins(20, 20, 20)

    def header(self) -> None:
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(*COLOR_HEADER)
        self.cell(0, 8, "Debug.ext | Executive AI Intelligence Report", ln=1)

        timestamp = datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M:%S IST")
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*COLOR_MUTED)
        self.cell(0, 6, f"Autonomous Verification Timestamp: {timestamp}", ln=1)

        badge_color = PRIORITY_COLORS.get(self.priority, (100, 100, 100))
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*badge_color)
        self.cell(0, 8, f"[{self.priority}] Priority Incident", ln=1)

        self.set_font("Helvetica", "", 10)
        self.set_text_color(*COLOR_HEADER)
        self.cell(0, 6, f"Category: {self.category}    AI Confidence: {self.confidence}%", ln=1)
        self.ln(2)
        self.set_draw_color(200, 200, 200)
        self.line(20, self.get_y(), 190, self.get_y())
        self.ln(4)

    def footer(self) -> None:
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*COLOR_MUTED)
        self.cell(0, 10, f"Page {self.page_no()} | Debug.ext Universal Triage Core", align="L")

    def section_title(self, title: str) -> None:
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(*COLOR_HEADER)
        self.cell(0, 8, title, ln=1)
        self.ln(1)

    def body_paragraph(self, text: str) -> None:
        self.set_font("Helvetica", "", 10.5)
        self.set_text_color(30, 30, 30)
        self.multi_cell(0, 6, text, align="L", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(3)

    def numbered_list(self, items: list[str]) -> None:
        self.set_text_color(30, 30, 30)
        for i, item in enumerate(items, start=1):
            self.set_font("Helvetica", "B", 10.5)
            prefix = f"{i}) "
            prefix_w = self.get_string_width(prefix) + 1
            self.cell(prefix_w, 6, prefix, new_x=XPos.RIGHT, new_y=YPos.TOP)
            self.set_font("Helvetica", "", 10.5)
            self.multi_cell(0, 6, item, align="L", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(3)

    def checklist(self, items: list[str]) -> None:
        self.set_font("Helvetica", "", 10.5)
        self.set_text_color(30, 30, 30)
        for item in items:
            self.multi_cell(0, 6, f"[ ]  {item}", align="L", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(3)

    def code_block(self, filename: str, language: str, code: str) -> None:
        self.set_font("Helvetica", "I", 9)
        self.set_text_color(*COLOR_MUTED)
        self.cell(0, 6, f"// {filename} ({language})", ln=1)

        self.set_font("Courier", "", 9.5)
        line_height = 5
        text_width_mm = 166
        char_w = self.get_string_width("M")
        max_chars = max(10, int(text_width_mm / char_w))

        display_rows = []
        for line in code.split("\n"):
            if len(line) <= max_chars:
                display_rows.append(line if line else "")
            else:
                while line:
                    display_rows.append(line[:max_chars])
                    line = line[max_chars:]

        i = 0
        while i < len(display_rows):
            available_h = self.h - self.b_margin - self.get_y()
            max_lines = max(1, int(available_h // line_height))
            chunk = display_rows[i : i + max_lines]
            block_h = line_height * len(chunk)
            
            self.set_fill_color(*COLOR_BG_CODE)
            self.set_text_color(*COLOR_TEXT_CODE)
            x, y = self.get_x(), self.get_y()
            self.rect(x, y, 170, block_h, style="F")
            self.set_xy(x + 2, y + 1)
            
            for row in chunk:
                self.set_x(x + 2)
                self.cell(166, line_height, row, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

            i += max_lines
            self.set_xy(x, self.get_y())
            if i < len(display_rows):
                self.add_page()

        self.set_text_color(30, 30, 30)
        self.ln(4)

def generate_pdf_report(bug_data) -> bytes:
    if hasattr(bug_data, "model_dump"):
        bug_data = bug_data.model_dump()
    elif isinstance(bug_data.get('full_json'), str):
        try:
            nested = json.loads(bug_data['full_json'])
            bug_data = {**bug_data, **nested}
        except:
            pass

    priority = bug_data.get('priority', 'P0')
    category = bug_data.get('category', 'Network')
    conf = bug_data.get('confidence_score', bug_data.get('confidence', 95))
    confidence = int(conf * 100) if conf <= 1 else int(conf)

    pdf = DebugExtPDF(priority=priority, category=category, confidence=confidence)
    pdf.add_page()

    pdf.section_title("1. Incident Summary & Target Context")
    pdf.body_paragraph(bug_data.get('incident_summary', bug_data.get('bug_summary', 'Universal Target Interception')))

    pdf.section_title("2. Probable Root Cause Analysis")
    pdf.body_paragraph(bug_data.get('probable_root_cause', bug_data.get('root_cause_analysis', 'N/A')))

    pdf.section_title("3. Technical Execution Breakdown")
    breakdown = bug_data.get('technical_execution_breakdown', [bug_data.get('technical_analysis', 'Multi-model analysis complete.')])
    if isinstance(breakdown, str):
        breakdown = [breakdown]
    pdf.numbered_list(breakdown)

    pdf.section_title("4. Verified Solution & Code Patch")
    fix_data = bug_data.get('suggested_fix', bug_data.get('code_patch', {}))
    if isinstance(fix_data, str):
        try: fix_data = json.loads(fix_data)
        except: fix_data = {"explanation": fix_data, "code_snippet": "// Patch applied"}

    explanation = fix_data.get('explanation', bug_data.get('solution_summary', 'Apply verified code patch:'))
    code_snippet = fix_data.get('code_snippet', fix_data.get('code', '// No code patch required'))
    filename = fix_data.get('filename', 'patch.tsx')
    language = fix_data.get('language', 'javascript')

    pdf.body_paragraph(explanation)
    pdf.code_block(filename, language, code_snippet)

    pdf.section_title("5. QA Verification Checklist")
    checklist_items = bug_data.get('qa_checklist', ['Verify network recovery', 'Confirm error boundary catches state'])
    pdf.checklist(checklist_items)

    return bytes(pdf.output(dest="S"))

# 🟢 EXPOSE BOTH FUNCTION NAMES TO PREVENT IMPORT ERRORS
def generate_triage_pdf(bug_data) -> bytes:
    return generate_pdf_report(bug_data)
