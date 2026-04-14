"""Debug full reproduce with proper sleep."""
import json
import time
from pathlib import Path

from backend.core_engine.ast_parser import WordASTParser
from backend.core_engine.word_ieee_renderer import IEEEWordRenderer
from backend.core_engine.word_springer_renderer import SpringerWordRenderer

INPUT_FILE = r"c:\221761_TIEN_PHONG_TT_VL_2026\input_data\Template_word\-TUAN_Magazine_01-12- Customer Churn Prediction in Vietnam's Enterprise Market Using Machine Learning Methods in a Streaming Data (1).docx"
IEEE_TEMPLATE = r"c:\221761_TIEN_PHONG_TT_VL_2026\input_data\Template_word\conference-template-a4 (ieee).docx"
SPRINGER_TEMPLATE = r"c:\221761_TIEN_PHONG_TT_VL_2026\input_data\Template_word\splnproc2510.docm"
OUTPUT_DIR = Path(r"c:\221761_TIEN_PHONG_TT_VL_2026\debug_output8")
OUTPUT_DIR.mkdir(exist_ok=True)
(OUTPUT_DIR / "images").mkdir(exist_ok=True)

# Step 1
print("STEP 1: Original -> IEEE")
parser1 = WordASTParser(INPUT_FILE, thu_muc_anh=str(OUTPUT_DIR / "images"), mode="latex")
ir1 = parser1.parse()
ieee_output = str(OUTPUT_DIR / "step1_ieee.docx")
IEEEWordRenderer().render(ir_data=ir1, output_path=ieee_output, image_root_dir=str(OUTPUT_DIR), ieee_template_path=IEEE_TEMPLATE)
time.sleep(2)

# Step 2
print("\nSTEP 2: IEEE -> Springer")
(OUTPUT_DIR / "images2").mkdir(exist_ok=True)
parser2 = WordASTParser(ieee_output, thu_muc_anh=str(OUTPUT_DIR / "images2"), mode="latex")
ir2 = parser2.parse()
print(f"IR2 Authors: {json.dumps(ir2['metadata']['authors'][:2], indent=2, ensure_ascii=False)}")
springer_output = str(OUTPUT_DIR / "step2_springer.docx")
SpringerWordRenderer().render(ir_data=ir2, output_path=springer_output, image_root_dir=str(OUTPUT_DIR), springer_template_path=SPRINGER_TEMPLATE)
time.sleep(2)

# Step 3
print("\nSTEP 3: Springer -> LaTeX")
(OUTPUT_DIR / "images3").mkdir(exist_ok=True)
parser3 = WordASTParser(springer_output, thu_muc_anh=str(OUTPUT_DIR / "images3"), mode="latex")
ir3 = parser3.parse()
print(f"IR3 Title: '{ir3['metadata']['title'][:100]}'")
print(f"IR3 Authors: {json.dumps(ir3['metadata']['authors'][:2], indent=2, ensure_ascii=False)}")
