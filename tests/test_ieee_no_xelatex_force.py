from backend.core_engine.jinja_renderer import JinjaLaTeXRenderer


def test_ieee_render_does_not_force_xelatex(tmp_path):
    template_dir = tmp_path / "tpl"
    template_dir.mkdir()
    template_file = template_dir / "main.tex"
    template_file.write_text(
        "\\documentclass[conference]{IEEEtran}\n"
        "\\begin{document}\n"
        "\\title{<< metadata.title >>}\n"
        "\\author{<< metadata.author_block >>}\n"
        "\\maketitle\n"
        "<< body >>\n"
        "\\end{document}\n",
        encoding="utf-8",
    )

    out_file = tmp_path / "out.tex"
    renderer = JinjaLaTeXRenderer(str(template_dir))
    renderer.render(
        "main.tex",
        {
            "metadata": {"title": "Demo"},
            "body": [{"type": "paragraph", "text": "Hello"}],
            "references": [],
        },
        str(out_file),
    )

    rendered = out_file.read_text(encoding="utf-8")
    assert not rendered.startswith("% !TeX program = xelatex")
    assert "\\documentclass[conference]{IEEEtran}" in rendered
    assert not (tmp_path / "latexmkrc").exists()
