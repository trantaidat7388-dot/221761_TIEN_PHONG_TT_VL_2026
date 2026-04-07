from backend.core_engine.jinja_renderer import JinjaLaTeXRenderer


def test_ieee_section_headings_are_uppercased():
    renderer = JinjaLaTeXRenderer(".")
    nodes = [
        {"type": "section", "level": 1, "text": "Introduction"},
        {"type": "section", "level": 2, "text": "Related work"},
    ]

    out = renderer.render_body_nodes(nodes, doc_class="ieee")

    assert "\\section{INTRODUCTION}" in out
    assert "\\subsection{RELATED WORK}" in out
