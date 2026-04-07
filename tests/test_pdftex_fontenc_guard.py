from backend.core_engine.template_preprocessor import TemplatePreprocessor


def test_ensure_essential_packages_injects_pdftex_fontenc_guard():
    src = "\\documentclass[conference]{IEEEtran}\n\\begin{document}\nX\n\\end{document}\n"
    out = TemplatePreprocessor._ensure_essential_packages(src)

    assert "\\usepackage{iftex}" in out
    assert "\\ifPDFTeX\\@ifpackageloaded{fontenc}{}{\\usepackage[T1]{fontenc}}\\fi" in out


def test_ensure_essential_packages_rewrites_ot1_to_t1_for_pdftex_templates():
    src = (
        "\\documentclass[pdftex,conference]{IEEEtran}\n"
        "\\usepackage[OT1]{fontenc}\n"
        "\\usepackage{tikz}\n"
        "\\begin{document}\nX\n\\end{document}\n"
    )
    out = TemplatePreprocessor._ensure_essential_packages(src)

    assert "\\usepackage[OT1]{fontenc}" not in out
    assert "\\usepackage[T1]{fontenc}" in out


def test_ensure_essential_packages_repairs_existing_guarded_preamble_with_fontenc():
    src = (
        "\\documentclass[conference]{IEEEtran}\n"
        "\\makeatletter\n"
        "\\@ifpackageloaded{amsmath}{}{\\usepackage{amsmath}}\n"
        "\\@ifpackageloaded{xcolor}{}{\\usepackage{xcolor}}\n"
        "\\makeatother\n"
        "\\begin{document}\nX\n\\end{document}\n"
    )
    out = TemplatePreprocessor._ensure_essential_packages(src)

    assert "\\ifPDFTeX\\@ifpackageloaded{fontenc}{}{\\usepackage[T1]{fontenc}}\\fi" in out
