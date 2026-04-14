"""Debug script to inspect the title/author structure in a Word document."""
import sys
from pathlib import Path
from docx import Document

def inspect_word_doc(doc_path: str):
    doc = Document(doc_path)
    print(f"=== Inspecting: {Path(doc_path).name} ===\n")
    
    # Show all paragraph styles and text (first 30 paragraphs)
    print("--- First 30 paragraphs (style | alignment | text[:120]) ---")
    for i, p in enumerate(doc.paragraphs[:30]):
        style = p.style.name if p.style else "None"
        align = str(p.paragraph_format.alignment) if p.paragraph_format.alignment is not None else "None"
        text = p.text.strip()
        runs_info = []
        for r in p.runs[:5]:
            runs_info.append(f"[bold={r.bold}, size={r.font.size}, super={r.font.superscript}, text='{r.text[:50]}']")
        runs_str = " | ".join(runs_info) if runs_info else "(no runs)"
        print(f"  P{i:3d}: style='{style}' align={align}")
        print(f"        text='{text[:150]}'")
        print(f"        runs={runs_str}")
        print()

if __name__ == "__main__":
    doc_path = sys.argv[1] if len(sys.argv) > 1 else r"c:\221761_TIEN_PHONG_TT_VL_2026\input_data\Template_word\-TUAN_Magazine_01-12- Customer Churn Prediction in Vietnam's Enterprise Market Using Machine Learning Methods in a Streaming Data (1).docx"
    inspect_word_doc(doc_path)
