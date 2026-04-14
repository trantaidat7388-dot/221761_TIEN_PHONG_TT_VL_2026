"""Debug: Inspect IEEE Word output for author table structure."""
from docx import Document
from docx.text.paragraph import Paragraph

doc = Document(r"c:\221761_TIEN_PHONG_TT_VL_2026\debug_output\step2_ieee.docx")

print("=== All elements (paragraphs + tables) in document order ===")
body = doc.element.body

idx = 0
for child in body:
    tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
    if tag == "p":
        p = Paragraph(child, doc) 
        style = p.style.name if p.style else "None"
        text = p.text.strip()[:120]
        print(f"  [{idx}] PARAGRAPH  style='{style}'  text='{text}'")
    elif tag == "tbl":
        from docx.table import Table
        t = Table(child, doc)
        print(f"  [{idx}] TABLE  rows={len(t.rows)} cols={len(t.columns)}")
        for ri, row in enumerate(t.rows):
            for ci, cell in enumerate(row.cells):
                ct = cell.text.strip()[:80]
                print(f"        [{ri},{ci}] '{ct}'")
    elif tag == "sectPr":
        print(f"  [{idx}] SECTION_PROPERTIES")
    else:
        print(f"  [{idx}] OTHER: {tag}")
    idx += 1
    if idx > 25:
        break
