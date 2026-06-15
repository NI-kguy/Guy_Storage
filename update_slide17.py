from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from lxml import etree
import copy

pptx_path = r'd:\dev\Guy_Storage\Digilent Test Strategy.pptx'
prs = Presentation(pptx_path)

slide = prs.slides[16]  # Slide 17 (0-indexed)

# ── Remove existing content shapes (keep title only) ────────────────────────
shapes_to_remove = []
for shape in slide.shapes:
    if shape.name != "Title 1":
        shapes_to_remove.append(shape)

for shape in shapes_to_remove:
    sp = shape._element
    sp.getparent().remove(sp)

# ── Table data ───────────────────────────────────────────────────────────────
headers = ["Priority", "Issue", "Scope", "Est. Cost", "Timeline"]

rows_data = [
    ("High",   "Obsolete Test Kits – No Spare",                    "12 products",  "TBD",       "Immediate"),
    ("Medium", "Obsolete Test Station (PXIe-8135 & old Chassis)",  "8 stations",   "USD 28k",   "Q3 2026"),
    ("Medium", "Legacy OS – Windows 7 → Windows 10 LTSC",          "6 images",     "TBD",       "Q4 2026"),
    ("Low",    "Obsolete Test Kits – Has Spare",                   "28 products",  "TBD",       "Planned"),
    ("Low",    "Missing Source Code (bits/dll files)",             "44 products",  "TBD",       "Planned"),
    ("Low",    "Convert Test Solution to NI Standard (BlueNITE / TestStand)", "114 products", "TBD", "Ongoing"),
]

# Colour mapping for priority
priority_colors = {
    "High":   RGBColor(0xFF, 0x00, 0x00),   # Red
    "Medium": RGBColor(0xFF, 0xC0, 0x00),   # Amber
    "Low":    RGBColor(0x70, 0xAD, 0x47),   # Green
}

priority_bg = {
    "High":   RGBColor(0xFF, 0xE0, 0xE0),
    "Medium": RGBColor(0xFF, 0xF2, 0xCC),
    "Low":    RGBColor(0xE2, 0xEF, 0xDA),
}

header_bg   = RGBColor(0x1F, 0x49, 0x7D)   # Dark blue
header_fg   = RGBColor(0xFF, 0xFF, 0xFF)   # White
row_alt_bg  = RGBColor(0xF2, 0xF2, 0xF2)  # Light grey (alt row)
text_dark   = RGBColor(0x00, 0x00, 0x00)

# ── Add table ────────────────────────────────────────────────────────────────
left   = Inches(0.35)
top    = Inches(1.3)
width  = Inches(13.0)
height = Inches(5.4)

num_rows = len(rows_data) + 1  # +1 for header
num_cols = len(headers)

table_shape = slide.shapes.add_table(num_rows, num_cols, left, top, width, height)
table = table_shape.table

# Column widths (total = 13 inches)
col_widths = [Inches(1.2), Inches(4.8), Inches(1.8), Inches(1.5), Inches(1.7)]
for i, w in enumerate(col_widths):
    table.columns[i].width = w

def set_cell(cell, text, font_size=13, bold=False,
             fg=text_dark, bg=None, align=PP_ALIGN.LEFT):
    tf = cell.text_frame
    tf.word_wrap = True
    para = tf.paragraphs[0]
    para.alignment = align
    run = para.add_run()
    run.text = text
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.color.rgb = fg
    if bg:
        fill = cell.fill
        fill.solid()
        fill.fore_color.rgb = bg

# Header row
for col_idx, header_text in enumerate(headers):
    cell = table.cell(0, col_idx)
    set_cell(cell, header_text, font_size=13, bold=True,
             fg=header_fg, bg=header_bg, align=PP_ALIGN.CENTER)

# Data rows
for row_idx, (priority, issue, scope, cost, timeline) in enumerate(rows_data):
    row_num = row_idx + 1
    bg = priority_bg[priority]

    set_cell(table.cell(row_num, 0), priority,  font_size=12, bold=True,
             fg=priority_colors[priority], bg=bg, align=PP_ALIGN.CENTER)
    set_cell(table.cell(row_num, 1), issue,     font_size=11, bg=bg)
    set_cell(table.cell(row_num, 2), scope,     font_size=11, bg=bg, align=PP_ALIGN.CENTER)
    set_cell(table.cell(row_num, 3), cost,      font_size=11, bg=bg, align=PP_ALIGN.CENTER)
    set_cell(table.cell(row_num, 4), timeline,  font_size=11, bg=bg, align=PP_ALIGN.CENTER)

prs.save(pptx_path)
print("Slide 17 updated successfully.")
