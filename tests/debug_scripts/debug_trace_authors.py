"""Debug: Patch _build_semantic_tree to trace authors_buf."""
import json
from pathlib import Path

from backend.core_engine.ast_parser import WordASTParser
from backend.core_engine.word_ieee_renderer import IEEEWordRenderer

INPUT_FILE = r"c:\221761_TIEN_PHONG_TT_VL_2026\input_data\Template_word\-TUAN_Magazine_01-12- Customer Churn Prediction in Vietnam's Enterprise Market Using Machine Learning Methods in a Streaming Data (1).docx"
IEEE_TEMPLATE = r"c:\221761_TIEN_PHONG_TT_VL_2026\input_data\Template_word\conference-template-a4 (ieee).docx"

OUTPUT_DIR = Path(r"c:\221761_TIEN_PHONG_TT_VL_2026\debug_output4")
OUTPUT_DIR.mkdir(exist_ok=True)
(OUTPUT_DIR / "images1").mkdir(exist_ok=True)
(OUTPUT_DIR / "images2").mkdir(exist_ok=True)

# Step 1: Create IEEE Word 
print("=== Step 1: Create IEEE Word ===")
parser1 = WordASTParser(INPUT_FILE, thu_muc_anh=str(OUTPUT_DIR / "images1"), mode="latex")
ir1 = parser1.parse()

ieee_output = str(OUTPUT_DIR / "ieee_output.docx")
renderer = IEEEWordRenderer()
renderer.render(ir_data=ir1, output_path=ieee_output, image_root_dir=str(OUTPUT_DIR), ieee_template_path=IEEE_TEMPLATE)
print(f"Created: {ieee_output}")

# Step 2: Parse IEEE Word and trace authors_buf
print("\n=== Step 2: Parse IEEE Word ===")

import re
import os
from typing import List, Dict, Any
from docx.text.paragraph import Paragraph
from docx.table import Table
from backend.core_engine.config import A_NAMESPACE

# Manually replicate the table parsing from _build_semantic_tree
parser2 = WordASTParser(ieee_output, thu_muc_anh=str(OUTPUT_DIR / "images2"), mode="latex")
parser2.doc, parser2._temp_word_files = __import__('backend.core_engine.word_loader', fromlist=['mo_tai_lieu_word_co_fallback']).mo_tai_lieu_word_co_fallback(ieee_output)

elements = parser2._extract_elements_in_order()
print(f"Total elements: {len(elements)}")

# Check first few elements
for i, (etype, elem) in enumerate(elements[:10]):
    if etype == "paragraph":
        style = elem.style.name if elem.style else "None"
        text = elem.text.strip()[:80]
        print(f"  [{i}] {etype}: style='{style}' text='{text}'")
    elif etype == "table":
        print(f"  [{i}] table: rows={len(elem.rows)}")
        for ri, row in enumerate(elem.rows):
            seen = set()
            for cell in row.cells:
                cid = id(cell._tc)
                if cid in seen:
                    continue
                seen.add(cid)
                ct = cell.text.strip()[:60]
                print(f"    cell: '{ct}'")

# Now check: what does _build_semantic_tree produce via the table parsing path?
# Replicate table parsing code from line 762-783
for idx, (etype, element) in enumerate(elements):
    if etype == "table":
        print(f"\n  Table at idx={idx}")
        table_lines = []
        seen_cells = set()
        for row in element.rows:
            for cell in row.cells:
                cell_id = id(cell._tc)
                if cell_id in seen_cells:
                    continue
                seen_cells.add(cell_id)
                cell_text = "\n".join([p.text.strip() for p in cell.paragraphs if p.text.strip()]).strip()
                print(f"    cell_text repr: {repr(cell_text[:100])}")
                if cell_text:
                    table_lines.extend([line.strip() for line in cell_text.split('\n') if line.strip()])
        
        table_text = "\n".join(table_lines)
        print(f"  table_text length: {len(table_text)}")
        print(f"  table_lines: {table_lines}")
        break  # Only check first table

# Now do full parse
print("\n=== Full Parse ===")
parser3 = WordASTParser(ieee_output, thu_muc_anh=str(OUTPUT_DIR / "images2b"), mode="latex")
ir3 = parser3.parse()
print(f"Title: '{ir3['metadata']['title'][:200]}'")
print(f"Authors: {json.dumps(ir3['metadata']['authors'], indent=2, ensure_ascii=False)[:500]}")
