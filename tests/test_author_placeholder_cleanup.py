from backend.core_engine.template_preprocessor import TemplatePreprocessor


def test_replace_existing_author_removes_springer_sample_placeholders():
    tex = r"""
\title{Sample}
\author{First Author\inst{1} \and Second Author\inst{2,3}\orcidID{1111-2222-3333-4444}}
\institute{Inst A \and Inst B}
\begin{document}
\maketitle
\end{document}
"""

    out = TemplatePreprocessor._replace_existing_author(tex)

    assert "<< metadata.author_block >>" in out
    assert "Second Author" not in out
    assert "\\author{" not in out
