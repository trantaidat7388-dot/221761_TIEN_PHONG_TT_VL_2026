from backend.core_engine.jinja_renderer import JinjaLaTeXRenderer


def test_magic_engine_defaults_to_pdflatex_when_no_unicode_engine_package():
    renderer = JinjaLaTeXRenderer(".")
    tex = "\\documentclass{article}\\n\\usepackage{graphicx}\\n"
    assert renderer._choose_magic_engine(tex) == "pdflatex"


def test_magic_engine_switches_to_xelatex_for_fontspec():
    renderer = JinjaLaTeXRenderer(".")
    tex = "\\documentclass{article}\\n\\usepackage{fontspec}\\n"
    assert renderer._choose_magic_engine(tex) == "xelatex"
