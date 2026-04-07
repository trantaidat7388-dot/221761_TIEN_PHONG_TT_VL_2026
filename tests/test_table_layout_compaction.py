from backend.core_engine.jinja_renderer import JinjaLaTeXRenderer


def test_three_column_feature_type_description_uses_wider_description_column():
    renderer = JinjaLaTeXRenderer(".")
    body = [
        {
            "type": "table",
            "rows": 2,
            "cols": 3,
            "caption": "Sample",
            "data": [
                [
                    {"type": "cell", "text": "Feature", "colspan": 1, "rowspan": 1},
                    {"type": "cell", "text": "Type", "colspan": 1, "rowspan": 1},
                    {"type": "cell", "text": "Description", "colspan": 1, "rowspan": 1},
                ],
                [
                    {"type": "cell", "text": "A", "colspan": 1, "rowspan": 1},
                    {"type": "cell", "text": "B", "colspan": 1, "rowspan": 1},
                    {"type": "cell", "text": "Long content", "colspan": 1, "rowspan": 1},
                ],
            ],
        }
    ]

    out = renderer.render_body_nodes(body)
    assert "p{0.220\\linewidth}|p{0.200\\linewidth}|p{0.540\\linewidth}" in out
    assert "\\setlength{\\tabcolsep}{3pt}" in out
    assert "\\renewcommand{\\arraystretch}{0.95}" in out
