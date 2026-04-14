"""Debug parser exactly on the crashing file."""
import json
from backend.core_engine.ast_parser import WordASTParser

path = r"c:\221761_TIEN_PHONG_TT_VL_2026\debug_output2\step1_ieee.docx"

# Parse without mode=latex first to see
parser = WordASTParser(path, thu_muc_anh="images_test", mode="latex")

elements = parser._extract_elements_in_order()
idx1 = None
for idx, (etype, elem) in enumerate(elements[:10]):
    if etype == "table":
        idx1 = idx
        print(f"[{idx}] table found")
        for ci, cell in enumerate(elem.rows[0].cells):
            t = "\n".join([p.text for p in cell.paragraphs])
            print(f"  cell {ci} length: {len(t)}")
            print(f"  first paragraph text: {repr(cell.paragraphs[0].text)}")

# Replace logic to see what table block does
state = "pre_title"
table_lines = []
for row in elements[idx1][1].rows:
    for cell in row.cells:
        cell_text = "\n".join([p.text.strip() for p in cell.paragraphs if p.text.strip()]).strip()
        print(f"  cell_text extracted: {repr(cell_text)}")
        if cell_text:
            lines = [line.strip() for line in cell_text.split('\n') if line.strip()]
            table_lines.extend(lines)

print(f"Table lines built: {table_lines}")

ir = parser.parse()
print(f"Result authors: {json.dumps(ir['metadata']['authors'], ensure_ascii=False)}")
