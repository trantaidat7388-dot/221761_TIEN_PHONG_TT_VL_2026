"""Minimal reproduction: Only 2 steps, add logging into parser."""
import json, sys, os
from pathlib import Path

# Patch _build_semantic_tree to trace table processing
from backend.core_engine import ast_parser as ap
_original_build = ap.WordASTParser._build_semantic_tree

def _debug_build(self, elements):
    """Patched version with author table debugging."""
    import re
    from backend.core_engine.config import A_NAMESPACE
    from docx.table import Table
    from docx.text.paragraph import Paragraph
    
    state = "pre_title"
    title_buf = []
    authors_buf = []
    abstract_buf = []
    
    for idx, (etype, element) in enumerate(elements):
        if etype == "table" and state in ("pre_title", "title", "authors") and not abstract_buf:
            print(f"  [TRACE] Table at idx={idx}, state={state}")
            table_lines = []
            seen_cells = set()
            for row in element.rows:
                for cell in row.cells:
                    cell_id = id(cell._tc)
                    if cell_id in seen_cells:
                        continue
                    seen_cells.add(cell_id)
                    cell_text = "\n".join([p.text.strip() for p in cell.paragraphs if p.text.strip()]).strip()
                    print(f"    cell_text repr: {repr(cell_text[:80])}")
                    if cell_text:
                        lines = [line.strip() for line in cell_text.split('\n') if line.strip()]
                        print(f"    split lines: {lines}")
                        table_lines.extend(lines)
            print(f"  [TRACE] Final table_lines: {table_lines}")
    
    # Run original
    _original_build(self, elements)

ap.WordASTParser._build_semantic_tree = _debug_build

from backend.core_engine.word_ieee_renderer import IEEEWordRenderer
from backend.core_engine.word_springer_renderer import SpringerWordRenderer

INPUT_FILE = r"c:\221761_TIEN_PHONG_TT_VL_2026\input_data\Template_word\-TUAN_Magazine_01-12- Customer Churn Prediction in Vietnam's Enterprise Market Using Machine Learning Methods in a Streaming Data (1).docx"
IEEE_TEMPLATE = r"c:\221761_TIEN_PHONG_TT_VL_2026\input_data\Template_word\conference-template-a4 (ieee).docx"
SPRINGER_TEMPLATE = r"c:\221761_TIEN_PHONG_TT_VL_2026\input_data\Template_word\splnproc2510.docm"
OUTPUT_DIR = Path(r"c:\221761_TIEN_PHONG_TT_VL_2026\debug_output6")
OUTPUT_DIR.mkdir(exist_ok=True)

# Step 1
print("=== STEP 1: Parse original ===")
(OUTPUT_DIR / "img1").mkdir(exist_ok=True)
parser1 = ap.WordASTParser(INPUT_FILE, thu_muc_anh=str(OUTPUT_DIR / "img1"), mode="latex")
ir1 = parser1.parse()
print(f"Authors: {json.dumps(ir1['metadata']['authors'][:1], indent=2, ensure_ascii=False)[:200]}...")

ieee_file = str(OUTPUT_DIR / "ieee.docx")
renderer1 = IEEEWordRenderer()
renderer1.render(ir_data=ir1, output_path=ieee_file, image_root_dir=str(OUTPUT_DIR), ieee_template_path=IEEE_TEMPLATE)

# Step 2
print("\n=== STEP 2: Parse IEEE Word ===")
(OUTPUT_DIR / "img2").mkdir(exist_ok=True)
parser2 = ap.WordASTParser(ieee_file, thu_muc_anh=str(OUTPUT_DIR / "img2"), mode="latex")
ir2 = parser2.parse()
print(f"\nTitle: '{ir2['metadata']['title'][:200]}'")
print(f"Authors: {json.dumps(ir2['metadata']['authors'][:3], indent=2, ensure_ascii=False)[:400]}")
