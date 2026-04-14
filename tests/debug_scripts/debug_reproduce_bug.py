"""Debug: Reproduce exact user flow - IEEE Word -> Springer Word -> LaTeX IEEE.
This simulates what happens in the web API."""
import json
from pathlib import Path

from backend.core_engine.ast_parser import WordASTParser
from backend.core_engine.word_ieee_renderer import IEEEWordRenderer
from backend.core_engine.word_springer_renderer import SpringerWordRenderer
from backend.core_engine.chuyen_doi import ChuyenDoiWordSangLatex

INPUT_FILE = r"c:\221761_TIEN_PHONG_TT_VL_2026\input_data\Template_word\-TUAN_Magazine_01-12- Customer Churn Prediction in Vietnam's Enterprise Market Using Machine Learning Methods in a Streaming Data (1).docx"
IEEE_TEMPLATE = r"c:\221761_TIEN_PHONG_TT_VL_2026\input_data\Template_word\conference-template-a4 (ieee).docx"
SPRINGER_TEMPLATE = r"c:\221761_TIEN_PHONG_TT_VL_2026\input_data\Template_word\splnproc2510.docm"
OUTPUT_DIR = Path(r"c:\221761_TIEN_PHONG_TT_VL_2026\debug_output2")
OUTPUT_DIR.mkdir(exist_ok=True)
(OUTPUT_DIR / "images").mkdir(exist_ok=True)

# === Step 1: Original -> IEEE Word (using API-like mode: default 'latex') ===
print("=" * 60)
print("STEP 1: Original -> IEEE Word (mode=latex, like API)")
print("=" * 60)

parser1 = WordASTParser(INPUT_FILE, thu_muc_anh=str(OUTPUT_DIR / "images"), mode="latex")
ir1 = parser1.parse()
print(f"Title: '{ir1['metadata']['title'][:100]}'")

ieee_output = str(OUTPUT_DIR / "step1_ieee.docx")
renderer_ieee = IEEEWordRenderer()
renderer_ieee.render(ir_data=ir1, output_path=ieee_output, image_root_dir=str(OUTPUT_DIR), ieee_template_path=IEEE_TEMPLATE)
print(f"IEEE Word created: {ieee_output}")

# === Step 2: IEEE Word -> Springer Word (mode=latex, like API) ===
print("\n" + "=" * 60)
print("STEP 2: IEEE Word -> Springer Word (mode=latex, like API)")
print("=" * 60)

(OUTPUT_DIR / "images2").mkdir(exist_ok=True)
parser2 = WordASTParser(ieee_output, thu_muc_anh=str(OUTPUT_DIR / "images2"), mode="latex")
ir2 = parser2.parse()
print(f"Title: '{ir2['metadata']['title'][:200]}'")
print(f"Authors: {json.dumps(ir2['metadata']['authors'][:3], indent=2, ensure_ascii=False)[:500]}")

springer_output = str(OUTPUT_DIR / "step2_springer.docx")
renderer_springer = SpringerWordRenderer()
renderer_springer.render(ir_data=ir2, output_path=springer_output, image_root_dir=str(OUTPUT_DIR), springer_template_path=SPRINGER_TEMPLATE)
print(f"Springer Word created: {springer_output}")

# === Step 3: Springer Word -> LaTeX IEEE (mode=latex, like API) ===
print("\n" + "=" * 60)
print("STEP 3: Springer Word -> LaTeX IEEE (mode=latex, like API)")
print("=" * 60)

(OUTPUT_DIR / "images3").mkdir(exist_ok=True)
parser3 = WordASTParser(springer_output, thu_muc_anh=str(OUTPUT_DIR / "images3"), mode="latex")
ir3 = parser3.parse()
print(f"\n*** CRITICAL: Title from IR3 ***")
print(f"Title: '{ir3['metadata']['title'][:500]}'")
print(f"\n*** Authors from IR3 ***")
print(f"Authors: {json.dumps(ir3['metadata']['authors'][:5], indent=2, ensure_ascii=False)[:800]}")
print(f"\nAbstract: '{ir3['metadata']['abstract'][:100]}'")

# Check if title contains author info (the bug!)
title = ir3['metadata']['title']
if 'NGUYEN' in title or 'University' in title or 'Anh-Tuan' in title:
    print("\n*** BUG CONFIRMED: Title contains author information! ***")
else:
    print("\n*** Title looks correct (no author info mixed in) ***")

# Inspect Springer Word doc structure
from docx import Document
doc = Document(springer_output)
print("\n--- Springer Word first 10 paragraphs ---")
for i, p in enumerate(doc.paragraphs[:10]):
    style = p.style.name if p.style else "None"
    text = p.text.strip()[:200]
    print(f"  P{i:3d}: style='{style}' => '{text}'")

print("\nDONE!")
