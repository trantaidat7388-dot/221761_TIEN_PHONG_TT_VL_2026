from backend.core_engine.jinja_renderer import JinjaLaTeXRenderer


def test_renderer_uses_fixed_table_float_H():
    renderer = JinjaLaTeXRenderer(".")
    body = [
        {
            "type": "table",
            "rows": 1,
            "cols": 2,
            "caption": "Sample",
            "data": [
                [
                    {"type": "cell", "text": "A", "colspan": 1, "rowspan": 1},
                    {"type": "cell", "text": "B", "colspan": 1, "rowspan": 1},
                ]
            ],
        }
    ]

    out = renderer.render_body_nodes(body)
    assert "\\begin{table}[H]" in out


def test_renderer_uses_flexible_table_float_for_springer():
    renderer = JinjaLaTeXRenderer(".")
    body = [
        {
            "type": "table",
            "rows": 1,
            "cols": 2,
            "caption": "Sample",
            "data": [
                [
                    {"type": "cell", "text": "A", "colspan": 1, "rowspan": 1},
                    {"type": "cell", "text": "B", "colspan": 1, "rowspan": 1},
                ]
            ],
        }
    ]

    out = renderer.render_body_nodes(body, doc_class="springer")
    assert "\\begin{table}[htbp]" in out


def test_renderer_uses_fixed_table_float_for_ieee():
    renderer = JinjaLaTeXRenderer(".")
    body = [
        {
            "type": "table",
            "rows": 1,
            "cols": 2,
            "caption": "Sample",
            "data": [
                [
                    {"type": "cell", "text": "A", "colspan": 1, "rowspan": 1},
                    {"type": "cell", "text": "B", "colspan": 1, "rowspan": 1},
                ]
            ],
        }
    ]

    out = renderer.render_body_nodes(body, doc_class="ieee")
    assert "\\begin{table}[H]" in out


def test_renderer_honors_table_width_ratio():
    renderer = JinjaLaTeXRenderer(".")
    body = [
        {
            "type": "table",
            "rows": 1,
            "cols": 2,
            "caption": "Sample",
            "width_ratio": 0.65,
            "data": [
                [
                    {"type": "cell", "text": "A", "colspan": 1, "rowspan": 1},
                    {"type": "cell", "text": "B", "colspan": 1, "rowspan": 1},
                ]
            ],
        }
    ]

    out = renderer.render_body_nodes(body)
    assert "\\resizebox{0.650\\columnwidth}{!}{%" in out
