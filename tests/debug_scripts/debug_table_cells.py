"""Debug: Directly inspect step2 authors - see what authors_buf looks like."""
import json, sys, os
from pathlib import Path

# Patch _build_semantic_tree to capture authors_buf
from backend.core_engine.ast_parser import WordASTParser

_orig_build = WordASTParser._build_semantic_tree

def _patched_build(self, elements):
    _orig_build(self, elements)
    # The title and authors are already assigned. Let's trace the problem differently.

# Instead, let's directly check IEEEWordRenderer output for the table structure

from backend.core_engine.word_ieee_renderer import IEEEWordRenderer
from backend.core_engine.word_springer_renderer import SpringerWordRenderer

INPUT_FILE = r"c:\221761_TIEN_PHONG_TT_VL_2026\input_data\Template_word\-TUAN_Magazine_01-12- Customer Churn Prediction in Vietnam's Enterprise Market Using Machine Learning Methods in a Streaming Data (1).docx"
IEEE_TEMPLATE = r"c:\221761_TIEN_PHONG_TT_VL_2026\input_data\Template_word\conference-template-a4 (ieee).docx"

OUTPUT_DIR = Path(r"c:\221761_TIEN_PHONG_TT_VL_2026\debug_output3")
OUTPUT_DIR.mkdir(exist_ok=True)
(OUTPUT_DIR / "images1").mkdir(exist_ok=True)

# Step 1: Parse original and create IEEE Word
parser1 = WordASTParser(INPUT_FILE, thu_muc_anh=str(OUTPUT_DIR / "images1"), mode="latex")
ir1 = parser1.parse()
print(f"Step 1 Title: '{ir1['metadata']['title'][:80]}'")
print(f"Step 1 Authors: {json.dumps(ir1['metadata']['authors'], indent=2, ensure_ascii=False)[:400]}")

ieee_output = str(OUTPUT_DIR / "step1_ieee.docx")
renderer = IEEEWordRenderer()
renderer.render(ir_data=ir1, output_path=ieee_output, image_root_dir=str(OUTPUT_DIR), ieee_template_path=IEEE_TEMPLATE)

# Step 2: Parse the IEEE Word output 
print("\n--- Inspecting IEEE Word output ---")
from docx import Document
from docx.text.paragraph import Paragraph
from docx.table import Table

doc = Document(ieee_output)
body = doc.element.body
print("Elements:")
for child in body:
    tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
    if tag == "p":
        p = Paragraph(child, doc)
        style = p.style.name if p.style else "None"
        text = p.text.strip()[:100]
        print(f"  P: style='{style}' text='{text}'")
    elif tag == "tbl":
        t = Table(child, doc)
        print(f"  TABLE: {len(t.rows)} rows x {len(t.columns)} cols")
        for ri, row in enumerate(t.rows):
            for ci, cell in enumerate(row.cells):
                cell_paragraphs = list(cell.paragraphs)
                print(f"    [{ri},{ci}] paragraphs={len(cell_paragraphs)}")
                for pi, para in enumerate(cell_paragraphs):
                    print(f"      p[{pi}]: style='{para.style.name}' text='{para.text.strip()[:60]}'")
        break  # Only inspect first table

# Now do the ACTUAL parse with WordASTParser 
print("\n--- WordASTParser parse (mode=latex) ---")
(OUTPUT_DIR / "images2").mkdir(exist_ok=True)
parser2 = WordASTParser(ieee_output, thu_muc_anh=str(OUTPUT_DIR / "images2"), mode="latex")
ir2 = parser2.parse()
print(f"Title: '{ir2['metadata']['title'][:200]}'")
print(f"Authors: {json.dumps(ir2['metadata']['authors'], indent=2, ensure_ascii=False)[:600]}")
