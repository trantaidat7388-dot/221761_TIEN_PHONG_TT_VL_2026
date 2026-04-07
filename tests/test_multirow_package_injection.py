from backend.core_engine.template_preprocessor import TemplatePreprocessor


def test_auto_tag_injects_multirow_guard():
    src = r"""
\documentclass[runningheads]{llncs}
\begin{document}
\begin{table}
\begin{tabular}{|c|c|}
\multirow{2}{*}{A} & B \\
\end{tabular}
\end{table}
\end{document}
"""

    out = TemplatePreprocessor._ensure_essential_packages(src)

    assert r"\@ifpackageloaded{multirow}{}{\usepackage{multirow}}" in out
