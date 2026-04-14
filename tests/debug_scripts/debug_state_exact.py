"""Debug state exactly."""
from backend.core_engine.ast_parser import WordASTParser

path = r"c:\221761_TIEN_PHONG_TT_VL_2026\debug_output2\step1_ieee.docx"
parser = WordASTParser(path, thu_muc_anh="images_test", mode="latex")

_old_build = WordASTParser._build_semantic_tree
def build_patch(self, elements):
    self._state_tracker = "pre_title"
    for idx, (etype, elem) in enumerate(elements[:5]):
        if etype == "paragraph":
            print(f"[{idx}] param: {repr(elem.text[:50])} (state={self._state_tracker})")
        else:
            print(f"[{idx}] table (rows={len(elem.rows)}) (state={self._state_tracker})")
            
        # Manually run exactly what state changes
        if etype == "paragraph":
            plain = self._normalize_text(elem.text.strip())
            from backend.core_engine.semantic_parser import du_doan_loai_node
            is_title = du_doan_loai_node(elem, "title") or self._du_doan_la_title(plain, elem.runs[0] if elem.runs else None)
            if is_title:
                if self._state_tracker == "pre_title":
                    self._state_tracker = "title"
                print(f"   -> Mark as title!")
    _old_build(self, elements)

WordASTParser._build_semantic_tree = build_patch
parser.parse()
