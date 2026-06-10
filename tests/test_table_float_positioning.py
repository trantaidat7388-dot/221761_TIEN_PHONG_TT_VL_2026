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


def test_renderer_keeps_regular_ieee_table_at_source_position():
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


def test_short_four_column_ieee_table_stays_in_one_column():
    renderer = JinjaLaTeXRenderer(".")
    body = [
        {
            "type": "table",
            "rows": 2,
            "cols": 4,
            "caption": "Compact metrics",
            "width_ratio": 0.83,
            "data": [
                [
                    {"type": "cell", "text": "Algorithm", "colspan": 1, "rowspan": 1},
                    {"type": "cell", "text": "Average", "colspan": 1, "rowspan": 1},
                    {"type": "cell", "text": "Last Batch", "colspan": 1, "rowspan": 1},
                    {"type": "cell", "text": "Std. Dev.", "colspan": 1, "rowspan": 1},
                ],
                [
                    {"type": "cell", "text": "EKI-Bagging", "colspan": 1, "rowspan": 1},
                    {"type": "cell", "text": "99.05", "colspan": 1, "rowspan": 1},
                    {"type": "cell", "text": "98.82", "colspan": 1, "rowspan": 1},
                    {"type": "cell", "text": "0.93", "colspan": 1, "rowspan": 1},
                ],
            ],
        }
    ]

    out = renderer.render_body_nodes(body, doc_class="ieee")

    assert "\\begin{table}[H]" in out
    assert "\\begin{table*}" not in out
    assert "\\begin{adjustbox}{max width=\\columnwidth}" in out


def test_ieee_wide_table_uses_inline_two_column_strip():
    renderer = JinjaLaTeXRenderer(".")
    row = [
        {"type": "cell", "text": f"Column {i}", "colspan": 1, "rowspan": 1}
        for i in range(5)
    ]
    body = [
        {
            "type": "table",
            "rows": 13,
            "cols": 5,
            "caption": "Wide results",
            "data": [row for _ in range(13)],
        }
    ]

    out = renderer.render_body_nodes(body, doc_class="ieee")

    assert "\\begin{strip}" in out
    assert "\\FloatBarrier\n\\begin{strip}" in out
    assert "\\captionof{table}{Wide results}" in out
    assert "\\begin{adjustbox}{max width=\\textwidth}" in out
    assert "\\begin{longtable}" not in out
    assert "\\onecolumn" not in out


def test_ieee_table_uses_full_grid_like_word_output():
    renderer = JinjaLaTeXRenderer(".")
    body = [
        {
            "type": "table",
            "rows": 1,
            "cols": 2,
            "caption": "Sample",
            "data": [[
                {"type": "cell", "text": "A", "colspan": 1, "rowspan": 1},
                {"type": "cell", "text": "B", "colspan": 1, "rowspan": 1},
            ]],
        }
    ]

    out = renderer.render_body_nodes(body, doc_class="ieee")

    assert "\\begin{tabular}{|c|c|}" in out


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
    assert "\\begin{adjustbox}{max width=0.650\\columnwidth}" in out


def test_plain_word_equation_labels_render_upright():
    renderer = JinjaLaTeXRenderer(".")
    body = [
        {
            "type": "paragraph",
            "text": (
                "\\begin{equation}\n"
                "Balanced Accuracy (BA) = \\frac{1}{2} "
                "(Specificity + Sensitivity)\n"
                "\\tag{1}\n"
                "\\end{equation}"
            ),
        }
    ]

    out = renderer.render_body_nodes(body, doc_class="ieee")

    assert "\\text{Balanced Accuracy (BA)}" in out
    assert "\\mathrm{Specificity}" in out
    assert "\\mathrm{Sensitivity}" in out
    assert "\\tag{1}" in out
    assert "\\tag{1}}$" not in out


def test_omml_math_artifacts_are_repaired():
    renderer = JinjaLaTeXRenderer(".")
    out = renderer._normalize_math_text_artifacts(
        "\\begin{equation}"
        "{L}_{LSCE} = - \\sumi-1C y_i log(y_i)"
        "\\end{equation}"
        " $ŷ = B a c k b o n e (X), \\parallelF\\parallel, "
        "\\sumi=1{N}_{c}, {\\text{\\Sigma}}_{i=1}, ϵ$ "
        "with ε smoothing; F\u0302 normalized"
    )

    assert "\\sum_{i=1}^{C}" in out
    assert "\\sum_{i=1}^{N_c}" in out
    assert "\\parallel F\\parallel" in out
    assert "\\epsilon" in out
    assert "\\log(" in out
    assert "\\hat{y}" in out
    assert "Backbone" in out
    assert "\\ensuremath{\\hat{F}}" in out
