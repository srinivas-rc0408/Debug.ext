from __future__ import annotations

import sys
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SHARED_DIR = os.path.join(BASE_DIR, "..", "shared")
sys.path.append(SHARED_DIR)

from datetime import datetime
from zoneinfo import ZoneInfo

from fpdf import FPDF
from fpdf.enums import XPos, YPos

from triage_prompt_engine import TriageReport

# ---- Palette, matched to your brief's "Silicon Valley SaaS Aesthetic" ----
COLOR_BG_CODE = (15, 23, 42)       # #0F172A dark terminal block
COLOR_TEXT_CODE = (56, 189, 248)   # #38BDF8 neon blue
COLOR_HEADER = (10, 10, 10)        # #0A0A0A graphite
COLOR_WHITE = (255, 255, 255)
COLOR_MUTED = (110, 110, 110)

PRIORITY_COLORS = {
    "P0": (220, 38, 38),   # red — critical
    "P1": (234, 88, 12),   # orange — high
    "P2": (202, 138, 4),   # amber — medium
    "P3": (22, 163, 74),   # green — low
}

SECTION_TITLES = [
    "1. Incident Summary & Target Context",
    "2. Probable Root Cause Analysis",
    "3. Technical Execution Breakdown",
    "4. Verified Solution & Code Patch",
    "5. QA Verification Checklist",
]


class DebugExtPDF(FPDF):
    """Overrides header()/footer() so every page auto-matches the sample layout."""

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
        self.cell(0, 8, f"[{self.priority}] {self._priority_label()} Priority Incident", ln=1)

        self.set_font("Helvetica", "", 10)
        self.set_text_color(*COLOR_HEADER)
        self.cell(0, 6, f"Category {self.category}    AI Confidence {self.confidence}%", ln=1)
        self.ln(2)
        self.set_draw_color(200, 200, 200)
        self.line(20, self.get_y(), 190, self.get_y())
        self.ln(4)

    def footer(self) -> None:
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*COLOR_MUTED)
        self.cell(0, 10, f"Page {self.page_no()} | Debug.ext Universal Triage Core", align="L")

    def _priority_label(self) -> str:
        return {"P0": "Critical", "P1": "High", "P2": "Medium", "P3": "Low"}.get(self.priority, "")

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

    def _wrap_code_line(self, line: str, max_chars: int) -> list[str]:
        if len(line) <= max_chars or max_chars <= 4:
            return [line] if line else [""]
        rows = [line[:max_chars]]
        rest = line[max_chars:]
        cont_max = max_chars - 2
        while rest:
            rows.append("  " + rest[:cont_max])
            rest = rest[cont_max:]
        return rows

    def code_block(self, filename: str, language: str, code: str) -> None:
        self.set_font("Helvetica", "I", 9)
        self.set_text_color(*COLOR_MUTED)
        self.cell(0, 6, f"// {filename} ({language})", ln=1)

        self.set_font("Courier", "", 9.5)
        line_height = 5
        text_width_mm = 166 
        char_w = self.get_string_width("M")
        max_chars = max(10, int(text_width_mm / char_w))

        display_rows: list[str] = []
        for logical_line in code.split("\n"):
            display_rows.extend(self._wrap_code_line(logical_line, max_chars))

        i = 0
        while i < len(display_rows):
            available_h = self.h - self.b_margin - self.get_y()
            max_lines_this_page = max(1, int(available_h // line_height))
            chunk = display_rows[i : i + max_lines_this_page]

            block_h = line_height * len(chunk)
            self.set_fill_color(*COLOR_BG_CODE)
            self.set_text_color(*COLOR_TEXT_CODE)
            x, y = self.get_x(), self.get_y()
            self.rect(x, y, 170, block_h, style="F")
            self.set_xy(x + 2, y + 1)
            for row in chunk:
                self.set_x(x + 2)
                self.cell(166, line_height, row, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

            i += max_lines_this_page
            self.set_xy(x, self.get_y())
            if i < len(display_rows):
                self.add_page()

        self.set_text_color(30, 30, 30)
        self.ln(4)


def generate_triage_pdf(report: TriageReport) -> bytes:
    pdf = DebugExtPDF(priority=report.priority, category=report.category, confidence=report.confidence)
    pdf.add_page()

    pdf.section_title(SECTION_TITLES[0])
    pdf.body_paragraph(report.incident_summary)

    pdf.section_title(SECTION_TITLES[1])
    pdf.body_paragraph(report.root_cause_analysis)

    pdf.section_title(SECTION_TITLES[2])
    pdf.numbered_list(report.technical_execution_breakdown)

    pdf.section_title(SECTION_TITLES[3])
    pdf.body_paragraph(report.solution_summary)
    if report.config_notes:
        pdf.body_paragraph(f"Config note: {report.config_notes}")
    pdf.code_block(report.code_patch.filename, report.code_patch.language, report.code_patch.code)

    pdf.section_title(SECTION_TITLES[4])
    pdf.checklist(report.qa_checklist)

    raw = pdf.output(dest="S")
    return bytes(raw)
