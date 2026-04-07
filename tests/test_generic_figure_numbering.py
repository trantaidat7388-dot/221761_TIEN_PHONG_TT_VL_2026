from backend.core_engine.template_preprocessor import TemplatePreprocessor


def test_generic_template_numbers_figure_and_table_by_section():
    src = "\\documentclass{article}\n\\begin{document}\n\\section{Methods}\nX\n\\end{document}\n"
    out = TemplatePreprocessor._normalize_float_numbering(src, "generic")

    assert "\\@addtoreset{figure}{section}" in out
    assert "\\renewcommand{\\thefigure}{\\thesection.\\arabic{figure}}" in out
    assert "\\@addtoreset{table}{section}" in out
    assert "\\renewcommand{\\thetable}{\\thesection.\\arabic{table}}" in out


def test_non_generic_template_does_not_inject_section_float_numbering():
    src = "\\documentclass[conference]{IEEEtran}\n\\begin{document}\nX\n\\end{document}\n"
    out = TemplatePreprocessor._normalize_float_numbering(src, "ieee")

    assert "\\renewcommand{\\thefigure}{\\thesection.\\arabic{figure}}" not in out


def test_springer_template_numbers_figure_and_table_by_section():
    src = "\\documentclass[runningheads]{llncs}\n\\begin{document}\n\\section{Methods}\nX\n\\end{document}\n"
    out = TemplatePreprocessor._normalize_float_numbering(src, "springer")

    assert "\\@addtoreset{figure}{section}" in out
    assert "\\renewcommand{\\thefigure}{\\thesection.\\arabic{figure}}" in out
