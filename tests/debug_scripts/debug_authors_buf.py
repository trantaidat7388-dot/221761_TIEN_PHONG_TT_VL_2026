"""Debug: Show exact authors_buf when parsing IEEE Word."""
import json
from pathlib import Path

from backend.core_engine.ast_parser import WordASTParser

ieee_file = r"c:\221761_TIEN_PHONG_TT_VL_2026\debug_output2\step1_ieee.docx"

# Monkey-patch to intercept authors_buf
original_build = WordASTParser._build_semantic_tree

def patched_build(self, elements):
    original_build(self, elements)
    # Access authors_buf doesn't exist outside... let's intercept differently.
    
WordASTParser._build_semantic_tree = patched_build

# Actually, let's just parse and inspect the table cells directly
from docx import Document
from docx.text.paragraph import Paragraph
from docx.table import Table

doc = Document(ieee_file)
body = doc.element.body

print("=== Parsing IEEE Word author table ===")
for child in body:
    tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
    if tag == "tbl":
        t = Table(child, doc)
        if len(t.rows) == 1 and len(t.columns) == 3:
            print("Found author table!")
            seen_cells = set()
            table_lines = []
            for row in t.rows:
                for cell in row.cells:
                    cell_id = id(cell._tc)
                    if cell_id in seen_cells:
                        continue
                    seen_cells.add(cell_id)
                    # This is the exact code from ast_parser.py line 774
                    cell_text = "\n".join([p.text.strip() for p in cell.paragraphs if p.text.strip()]).strip()
                    print(f"  cell_text: '{cell_text}'")
                    if cell_text:
                        lines = [line.strip() for line in cell_text.split('\n') if line.strip()]
                        print(f"  split lines: {lines}")
                        table_lines.extend(lines)
            
            print(f"\nFinal table_lines (authors_buf):")
            for i, line in enumerate(table_lines):
                print(f"  [{i}] '{line}'")
            
            # Now test _parse_authors with this
            parser = WordASTParser(ieee_file, thu_muc_anh="images")
            parser.doc = doc
            result = parser._parse_authors(table_lines)
            print(f"\nParsed authors:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            break

# Also check: what does the actual parser produce?
print("\n\n=== Full AST Parse (mode=latex) ===")
parser2 = WordASTParser(ieee_file, thu_muc_anh="debug_output2/images_test", mode="latex")
ir = parser2.parse()
print(f"Title: '{ir['metadata']['title'][:200]}'")
print(f"Authors: {json.dumps(ir['metadata']['authors'], indent=2, ensure_ascii=False)[:600]}")
