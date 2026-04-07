from pathlib import Path

from backend.core_engine.ast_parser import WordASTParser


def test_ieee_template_extracts_non_empty_title_and_authors():
    docx_path = Path("input_data/Template_word/conference-template-a4 (ieee).docx")
    parser = WordASTParser(str(docx_path))
    ir = parser.parse()

    assert (ir.get("metadata", {}).get("title") or "").strip()
    assert len(ir.get("metadata", {}).get("authors") or []) > 0
