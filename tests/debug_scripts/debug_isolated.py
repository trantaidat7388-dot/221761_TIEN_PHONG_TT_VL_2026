"""Test parser2 straight away."""
import json
from pathlib import Path
from backend.core_engine.ast_parser import WordASTParser

OUTPUT_DIR = Path(r"c:\221761_TIEN_PHONG_TT_VL_2026\debug_output2")
ieee_output = str(OUTPUT_DIR / "step1_ieee.docx")

parser2 = WordASTParser(ieee_output, thu_muc_anh=str(OUTPUT_DIR / "images_test_2"), mode="latex")
ir2 = parser2.parse()

print(f"Authors: {json.dumps(ir2['metadata']['authors'][:3], indent=2, ensure_ascii=False)}")
