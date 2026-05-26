from __future__ import annotations
import re
from datetime import date

from fpdf import FPDF

# ── palette ───────────────────────────────────────────────────────────────────
RED = (218, 41, 28)
YELLOW = (255, 205, 0)
BLACK = (30, 30, 30)
WHITE = (255, 255, 255)
LIGHT_GRAY = (245, 245, 245)
MID_GRAY = (160, 160, 160)

MARGIN = 15
CONTENT_W = 180  # 210mm A4 - 2 * 15mm


# ── PDF class ─────────────────────────────────────────────────────────────────

class _PDF(FPDF):
    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("Helvetica", "B", 7)
        self.set_text_color(*RED)
        self.cell(0, 5, "LEGO DESIGNER AI  ·  BUILD MANUAL", align="R")
        self.set_draw_color(*MID_GRAY)
        self.set_line_width(0.2)
        self.line(MARGIN, self.get_y() + 5, 210 - MARGIN, self.get_y() + 5)
        self.ln(9)

    def footer(self):
        if self.page_no() == 1:
            return
        self.set_y(-12)
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*MID_GRAY)
        self.cell(0, 5, f"Page {self.page_no() - 1}", align="C")


# ── page builders ─────────────────────────────────────────────────────────────

def _cover(pdf: _PDF, prompt: str, inventory: dict[str, int]) -> None:
    pdf.add_page()

    # Red top band
    pdf.set_fill_color(*RED)
    pdf.rect(0, 0, 210, 48, "F")

    # "LEGO" in band
    pdf.set_font("Helvetica", "B", 26)
    pdf.set_text_color(*WHITE)
    pdf.set_y(10)
    pdf.cell(0, 14, "LEGO", align="C")
    pdf.ln(13)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 6, "DESIGNER AI", align="C")

    # Yellow accent stripe
    pdf.set_fill_color(*YELLOW)
    pdf.rect(0, 48, 210, 5, "F")

    # "BUILD MANUAL" label
    pdf.set_y(66)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*MID_GRAY)
    pdf.cell(0, 5, "BUILD MANUAL", align="C")
    pdf.ln(10)

    # Title (user prompt)
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(*BLACK)
    pdf.set_x(MARGIN)
    pdf.multi_cell(CONTENT_W, 11, prompt.upper(), align="C")

    # Stats badge
    total = sum(inventory.values())
    types = len(inventory)
    pdf.ln(8)
    badge_w, badge_h = 90, 20
    badge_x = (210 - badge_w) / 2
    badge_y = pdf.get_y()
    pdf.set_fill_color(*LIGHT_GRAY)
    pdf.set_draw_color(*MID_GRAY)
    pdf.set_line_width(0.3)
    pdf.rect(badge_x, badge_y, badge_w, badge_h, "DF")
    pdf.set_y(badge_y + 3)
    pdf.set_font("Helvetica", "B", 15)
    pdf.set_text_color(*RED)
    pdf.cell(0, 7, str(total), align="C")
    pdf.ln(7)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*BLACK)
    pdf.cell(0, 5, f"pieces  ·  {types} type{'s' if types != 1 else ''}", align="C")

    # Yellow bottom band
    pdf.set_fill_color(*YELLOW)
    pdf.rect(0, 274, 210, 23, "F")
    pdf.set_y(281)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*BLACK)
    pdf.cell(0, 6, date.today().strftime("%B %Y").upper(), align="C")


def _inventory_page(pdf: _PDF, inventory: dict[str, int]) -> None:
    _section_header(pdf, "Parts List")
    pdf.ln(2)

    col_name, col_qty = 148, 32
    row_h = 8

    # Header row
    pdf.set_fill_color(*RED)
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_x(MARGIN)
    pdf.cell(col_name, row_h, "  PIECE", fill=True)
    pdf.cell(col_qty, row_h, "QTY", align="C", fill=True)
    pdf.ln()

    pdf.set_font("Helvetica", "", 9)
    for i, (name, count) in enumerate(sorted(inventory.items())):
        bg = LIGHT_GRAY if i % 2 == 0 else WHITE
        pdf.set_fill_color(*bg)
        pdf.set_text_color(*BLACK)
        pdf.set_x(MARGIN)
        pdf.cell(col_name, row_h, f"  {name}", fill=True)
        pdf.cell(col_qty, row_h, str(count), align="C", fill=True)
        pdf.ln()

    # Total row
    pdf.set_fill_color(*YELLOW)
    pdf.set_text_color(*BLACK)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_x(MARGIN)
    pdf.cell(col_name, row_h, "  TOTAL", fill=True)
    pdf.cell(col_qty, row_h, str(sum(inventory.values())), align="C", fill=True)
    pdf.ln()


def _section_header(pdf: _PDF, text: str) -> None:
    pdf.set_fill_color(*RED)
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_x(MARGIN)
    pdf.cell(CONTENT_W, 9, f"  {text.upper()}", fill=True)
    pdf.ln(13)


def _step_block(pdf: _PDF, number: str, title: str) -> None:
    x = MARGIN
    y = pdf.get_y()
    badge = 9

    pdf.set_fill_color(*RED)
    pdf.rect(x, y, badge, badge, "F")

    pdf.set_font("Helvetica", "B", 7)
    pdf.set_text_color(*WHITE)
    pdf.set_xy(x, y + (badge - 5) / 2)
    pdf.cell(badge, 5, number, align="C")

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*BLACK)
    pdf.set_xy(x + badge + 3, y + (badge - 6) / 2)
    pdf.cell(CONTENT_W - badge - 3, 6, title)

    pdf.set_y(y + badge + 3)


def _body_text(pdf: _PDF, text: str) -> None:
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*BLACK)
    pdf.set_x(MARGIN)
    pdf.multi_cell(CONTENT_W, 5, text)
    pdf.ln(2)


# ── parser ────────────────────────────────────────────────────────────────────

def _parse(text: str) -> list[tuple]:
    elements: list[tuple] = []
    body_lines: list[str] = []

    def flush():
        if body_lines:
            block = "\n".join(body_lines).strip()
            if block:
                elements.append(("body", block))
            body_lines.clear()

    for raw in text.splitlines():
        line = raw.strip()

        if not line:
            flush()
            continue

        # Numbered step: "3. Title" or "3. **Title**"
        m = re.match(r'^(\d+)\.\s+\*?\*?(.*?)\*?\*?\s*$', line)
        if m:
            flush()
            title = m.group(2).strip() or f"Step {m.group(1)}"
            elements.append(("step", m.group(1), title))
            continue

        # Standalone bold header: **Title**
        m = re.match(r'^\*\*(.*?)\*\*\s*$', line)
        if m:
            flush()
            elements.append(("header", m.group(1).strip()))
            continue

        # Markdown header: ## Title
        m = re.match(r'^#{1,3}\s+(.*)', line)
        if m:
            flush()
            elements.append(("header", m.group(1).strip()))
            continue

        # Body text — strip inline bold markers, normalise bullets
        clean = re.sub(r'\*\*(.*?)\*\*', r'\1', line)
        clean = re.sub(r'^[-*]\s+', '- ', clean)
        body_lines.append(clean)

    flush()
    return elements


# ── public API ────────────────────────────────────────────────────────────────

def generate_pdf(plan_text: str, prompt: str, inventory: dict[str, int]) -> bytes:
    pdf = _PDF(orientation="P", unit="mm", format="A4")
    pdf.set_margins(MARGIN, MARGIN, MARGIN)
    pdf.set_auto_page_break(auto=True, margin=20)

    _cover(pdf, prompt, inventory)

    if inventory:
        pdf.add_page()
        _inventory_page(pdf, inventory)

    pdf.add_page()
    _section_header(pdf, "Build Plan")

    for el in _parse(plan_text):
        if el[0] == "header":
            pdf.ln(2)
            _section_header(pdf, el[1])
        elif el[0] == "step":
            _step_block(pdf, el[1], el[2])
        elif el[0] == "body":
            _body_text(pdf, el[1])

    return bytes(pdf.output())
