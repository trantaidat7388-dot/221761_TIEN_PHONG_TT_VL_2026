import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.core_engine.ast_parser import WordASTParser
from backend.core_engine.word_ieee_renderer import IEEEWordRenderer

input_docx = r"c:\221761_TIEN_PHONG_TT_VL_2026\input_data\Template_word\Vietnamese Text-to-Speech System Using Artificial Intelligence (AI).docm"
template_docx = r"c:\221761_TIEN_PHONG_TT_VL_2026\input_data\Template_word\conference-template-a4 (ieee).docx"
output_docx = r"c:\221761_TIEN_PHONG_TT_VL_2026\outputs\FINAL_IEEE_OUTPUT.docx"
workspace = r"c:\221761_TIEN_PHONG_TT_VL_2026\outputs\tmp_workspace"

os.makedirs(workspace, exist_ok=True)

print("Parsing Word Document to IR...")
parser = WordASTParser(input_docx, workspace)
parser.parse()
ir_data = parser.ir

print(f"Num references: {len(ir_data['references'])}")
print(f"Num body: {len(ir_data['body'])}")

import json
with open(os.path.join(workspace, "ast_debug.json"), "w", encoding="utf-8") as f:
    json.dump(ir_data, f, indent=2, ensure_ascii=False)

print("Rendering IEEE Document...")
renderer = IEEEWordRenderer()
renderer.render(ir_data, output_docx, workspace, ieee_template_path=template_docx)

print(f"Success! Output saved to: {output_docx}")
