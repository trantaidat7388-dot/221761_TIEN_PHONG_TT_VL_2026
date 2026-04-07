from backend.core_engine.ast_parser import WordASTParser


def test_table_with_images_is_listed_as_figures_without_subfigure_analysis(monkeypatch):
    parser = WordASTParser("dummy.docx", thu_muc_anh="images")

    monkeypatch.setattr(parser, "_detect_equation_table", lambda _tbl: None)
    monkeypatch.setattr(parser, "_trich_xuat_anh_tu_bang", lambda _tbl: ["a.png", "b.png"])
    monkeypatch.setattr(parser, "_bat_caption_hinh", lambda _elements, _idx, _used: "Main caption")

    elements = [("table", object())]
    parser._build_semantic_tree(elements)

    body = parser.ir["body"]
    assert len(body) == 2
    assert all(node.get("type") == "paragraph" for node in body)
    assert all("\\begin{figure}" in node.get("text", "") for node in body)
    assert all("\\begin{subfigure}" not in node.get("text", "") for node in body)
    assert "\\caption{Main caption}" in body[0]["text"]
