from backend.core_engine.jinja_renderer import JinjaLaTeXRenderer
from backend.core_engine.template_preprocessor import TemplatePreprocessor


def test_paragraph_newlines_are_normalized():
    nodes = [
        {
            "type": "paragraph",
            "text": "This is line one.\n\nThis is line two.\n   This is line three.",
        }
    ]

    out = JinjaLaTeXRenderer(".").render_body_nodes(nodes)

    assert "This is line one. This is line two. This is line three." in out
    assert "line one.\n\nThis" not in out


def test_hidden_unicode_spaces_are_removed_from_paragraph():
    nodes = [
        {
            "type": "paragraph",
            "text": "Alpha\u200b\u200c\ufeff\xa0Beta",
        }
    ]

    out = JinjaLaTeXRenderer(".").render_body_nodes(nodes)

    assert "Alpha Beta" in out


def test_springer_parskip_is_normalized_once():
    src = "\\documentclass{llncs}\n\\begin{document}\nX\n\\end{document}\n"
    out = TemplatePreprocessor._normalize_paragraph_spacing(src, "springer")

    assert "\\setlength{\\parskip}{0pt}" in out
    assert "\\setlength{\\parsep}{0pt}" in out
    assert "\\hyphenpenalty=1500" in out
    assert "\\exhyphenpenalty=1500" in out
    assert "\\tolerance=1800" in out
    assert "\\emergencystretch=1.0em" in out
    assert out.count("\\setlength{\\parskip}{0pt}") == 1
    assert out.count("\\hyphenpenalty=1500") == 1
