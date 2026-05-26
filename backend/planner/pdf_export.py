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

# Step card dimensions
_BAR_H   = 9    # red title bar
_ILLUS_H = 48   # illustration box height
_ILLUS_W = 110  # illustration box width
_GAP     = 3    # gap between illustration and sidebar
_SIDE_W  = CONTENT_W - _ILLUS_W - _GAP  # sidebar width
_CARD_H  = _BAR_H + _ILLUS_H


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


def _step_card(
    pdf: _PDF,
    number: str,
    title: str,
    body: str,
    inventory: dict[str, int],
) -> None:
    """Full-width step card: red header bar, illustration placeholder, piece sidebar."""
    # Page-break guard — add a new page if the card won't fit
    if pdf.get_y() + _CARD_H + 5 > pdf.h - pdf.b_margin:
        pdf.add_page()

    x0 = MARGIN
    y0 = pdf.get_y()

    # ── red title bar ──────────────────────────────────────────────────────────
    pdf.set_fill_color(*RED)
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_xy(x0, y0)
    label = f"  STEP {number}  -  {title.upper()}"
    pdf.cell(CONTENT_W, _BAR_H, label[:72], fill=True)  # cap to avoid overflow

    iy = y0 + _BAR_H  # top of illustration row

    # ── illustration placeholder ───────────────────────────────────────────────
    pdf.set_fill_color(*LIGHT_GRAY)
    pdf.set_draw_color(*MID_GRAY)
    pdf.set_line_width(0.3)
    pdf.rect(x0, iy, _ILLUS_W, _ILLUS_H, "DF")

    # Corner tick marks
    pdf.set_draw_color(*MID_GRAY)
    pdf.set_line_width(0.6)
    t = 5
    for cx, cy, sx, sy in [
        (x0 + 3,           iy + 3,            1,  1),
        (x0 + _ILLUS_W - 3, iy + 3,           -1,  1),
        (x0 + 3,           iy + _ILLUS_H - 3,  1, -1),
        (x0 + _ILLUS_W - 3, iy + _ILLUS_H - 3, -1, -1),
    ]:
        pdf.line(cx, cy, cx + sx * t, cy)
        pdf.line(cx, cy, cx, cy + sy * t)

    # Stud grid
    pdf.set_draw_color(215, 215, 215)
    pdf.set_line_width(0.15)
    sp = 7.5
    grid_x0, grid_y0 = x0 + 11, iy + 9
    cols = int((_ILLUS_W - 22) / sp)
    rows = int((_ILLUS_H - 18) / sp)
    r = 1.4
    for row in range(rows):
        for col in range(cols):
            sx2 = grid_x0 + col * sp
            sy2 = grid_y0 + row * sp
            pdf.ellipse(sx2 - r, sy2 - r, r * 2, r * 2)

    # Large step number watermark
    pdf.set_font("Helvetica", "B", 32)
    pdf.set_text_color(210, 210, 210)
    pdf.set_xy(x0, iy + (_ILLUS_H - 18) / 2)
    pdf.cell(_ILLUS_W, 18, number, align="C")

    # ── piece sidebar ──────────────────────────────────────────────────────────
    sx0 = x0 + _ILLUS_W + _GAP
    pdf.set_fill_color(250, 250, 250)
    pdf.set_draw_color(*MID_GRAY)
    pdf.set_line_width(0.3)
    pdf.rect(sx0, iy, _SIDE_W, _ILLUS_H, "DF")

    # Yellow "PIECES" header
    pdf.set_fill_color(*YELLOW)
    pdf.set_xy(sx0, iy)
    pdf.set_font("Helvetica", "B", 7)
    pdf.set_text_color(*BLACK)
    pdf.cell(_SIDE_W, 6, "  PIECES", fill=True)

    # Detect inventory pieces mentioned in this step (case-insensitive)
    step_lower = (title + " " + body).lower()
    used = [(name, qty) for name, qty in inventory.items() if name.lower() in step_lower]

    entry_y = iy + 8
    pdf.set_font("Helvetica", "", 7)
    pdf.set_text_color(*BLACK)
    if used:
        for name, qty in used[:7]:
            if entry_y + 5 > iy + _ILLUS_H - 1:
                break
            short = (name[:20] + "..") if len(name) > 22 else name
            pdf.set_xy(sx0 + 2, entry_y)
            pdf.cell(_SIDE_W - 4, 5, f"x{qty}  {short}")
            entry_y += 5
    else:
        pdf.set_text_color(*MID_GRAY)
        pdf.set_xy(sx0 + 2, entry_y)
        pdf.multi_cell(_SIDE_W - 4, 5, "See plan\nfor pieces")

    pdf.set_y(y0 + _CARD_H + 2)

    if body:
        _body_text(pdf, body)
    pdf.ln(1)


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

    elements = _parse(plan_text)
    i = 0
    while i < len(elements):
        el = elements[i]
        if el[0] == "step":
            # Consume the immediately following body block into the card
            body = ""
            if i + 1 < len(elements) and elements[i + 1][0] == "body":
                i += 1
                body = elements[i][1]
            _step_card(pdf, el[1], el[2], body, inventory)
        elif el[0] == "header":
            pdf.ln(2)
            _section_header(pdf, el[1])
        elif el[0] == "body":
            _body_text(pdf, el[1])
        i += 1

    return bytes(pdf.output())
