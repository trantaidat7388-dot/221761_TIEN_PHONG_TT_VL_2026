from backend.core_engine.template_preprocessor import TemplatePreprocessor


def test_auto_tag_trims_duplicate_document_tail():
    tex = r"""
\documentclass[conference]{IEEEtran}
	itle{Real Title}
\author{Real Author}
\begin{abstract}
Real abstract.
\end{abstract}
\begin{IEEEkeywords}
kw1, kw2
\end{IEEEkeywords}
\begin{document}
\maketitle
\section{Intro}
Body
\end{document}

\documentclass[conference]{IEEEtran}
\begin{document}
\title{Conference Paper Title*}
\maketitle
Template guidance text
\end{document}
"""

    out = TemplatePreprocessor.auto_tag(tex)

    assert out.count(r"\documentclass") == 1
    assert out.count(r"\end{document}") == 1
    assert "Conference Paper Title*" not in out
