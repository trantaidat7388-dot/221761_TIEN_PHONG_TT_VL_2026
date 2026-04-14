"""Debug sleep test."""
import json
import time
from pathlib import Path

from backend.core_engine.ast_parser import WordASTParser
from backend.core_engine.word_ieee_renderer import IEEEWordRenderer
from backend.core_engine.word_springer_renderer import SpringerWordRenderer

INPUT_FILE = r"c:\221761_TIEN_PHONG_TT_VL_2026\input_data\Template_word\-TUAN_Magazine_01-12- Customer Churn Prediction in Vietnam's Enterprise Market Using Machine Learning Methods in a Streaming Data (1).docx"
IEEE_TEMPLATE = r"c:\221761_TIEN_PHONG_TT_VL_2026\input_data\Template_word\conference-template-a4 (ieee).docx"

OUTPUT_DIR = Path(r"c:\221761_TIEN_PHONG_TT_VL_2026\debug_output7")
OUTPUT_DIR.mkdir(exist_ok=True)
(OUTPUT_DIR / "images").mkdir(exist_ok=True)

print("Step 1")
parser1 = WordASTParser(INPUT_FILE, thu_muc_anh=str(OUTPUT_DIR / "images"), mode="latex")
ir1 = parser1.parse()

ieee_output = str(OUTPUT_DIR / "step1_ieee.docx")
renderer_ieee = IEEEWordRenderer()
renderer_ieee.render(ir_data=ir1, output_path=ieee_output, image_root_dir=str(OUTPUT_DIR), ieee_template_path=IEEE_TEMPLATE)
print("Step 1 done")

# SLEEP HERE !!
print("Sleeping 2 seconds...")
time.sleep(2)

print("Step 2")
(OUTPUT_DIR / "images2").mkdir(exist_ok=True)
parser2 = WordASTParser(ieee_output, thu_muc_anh=str(OUTPUT_DIR / "images2"), mode="latex")
ir2 = parser2.parse()
print(f"Authors: {json.dumps(ir2['metadata']['authors'][:3], indent=2, ensure_ascii=False)[:500]}")
