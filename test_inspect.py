import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from backend.core_engine.word_loader import mo_tai_lieu_word_co_fallback
doc, temps = mo_tai_lieu_word_co_fallback(r"c:\221761_TIEN_PHONG_TT_VL_2026\input_data\Template_word\Vietnamese Text-to-Speech System Using Artificial Intelligence (AI).docm")
import json
out = []
for p in doc.paragraphs[:50]:
    out.append({"style": p.style.name if p.style else None, "text": p.text})
with open("inspect_out.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
