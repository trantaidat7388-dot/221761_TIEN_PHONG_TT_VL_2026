"""Debug: Trace state machine through elements."""
import json
from pathlib import Path
from backend.core_engine import ast_parser as ap
_original_build = ap.WordASTParser._build_semantic_tree

def _debug_build(self, elements):
    print("\n--- TRACING STATE MACHINE ---")
    state = "pre_title"
    title_buf = []
    authors_buf = []
    abstract_buf = []
    
    for idx, (etype, element) in enumerate(elements):
        text = element.text.strip() if etype == "paragraph" else ""
        print(f"[{idx:2d}] {etype} | len={len(text):3d} | current_state={self._state_tracker if hasattr(self, '_state_tracker') else '?'}")
        
        # We need to see what `self.ir["metadata"]["authors"]` etc become
    
    # Actually just patch it properly
    # The actual state machine modifies a local variable `state`. 
    pass

ap.WordASTParser._build_semantic_tree = _debug_build

from backend.core_engine.word_ieee_renderer import IEEEWordRenderer

INPUT_FILE = r"c:\221761_TIEN_PHONG_TT_VL_2026\input_data\Template_word\-TUAN_Magazine_01-12- Customer Churn Prediction in Vietnam's Enterprise Market Using Machine Learning Methods in a Streaming Data (1).docx"
IEEE_TEMPLATE = r"c:\221761_TIEN_PHONG_TT_VL_2026\input_data\Template_word\conference-template-a4 (ieee).docx"
OUTPUT_DIR = Path(r"c:\221761_TIEN_PHONG_TT_VL_2026\debug_state")
OUTPUT_DIR.mkdir(exist_ok=True)

# Just parse IEEE word and print exact author buffer
(OUTPUT_DIR / "img1").mkdir(exist_ok=True)
parser1 = ap.WordASTParser(INPUT_FILE, thu_muc_anh=str(OUTPUT_DIR / "img1"), mode="latex")
ir1 = parser1.parse()

ieee_file = str(OUTPUT_DIR / "ieee.docx")
renderer1 = IEEEWordRenderer()
renderer1.render(ir_data=ir1, output_path=ieee_file, image_root_dir=str(OUTPUT_DIR), ieee_template_path=IEEE_TEMPLATE)

def intercept_parse_authors(self, authors_raw):
    print(f"\n[INTERCEPT] authors_raw length: {len(authors_raw)}")
    for i, a in enumerate(authors_raw):
        print(f"  raw[{i}]: {repr(a)}")
    return []

ap.WordASTParser._parse_authors = intercept_parse_authors

print("\n=== PARSE IEEE ===")
parser2 = ap.WordASTParser(ieee_file, thu_muc_anh=str(OUTPUT_DIR / "img2"), mode="latex")
_ = parser2.parse()
