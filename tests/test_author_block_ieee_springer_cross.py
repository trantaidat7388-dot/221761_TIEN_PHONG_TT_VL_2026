from backend.core_engine.jinja_renderer import JinjaLaTeXRenderer


def test_cross_template_author_block_generation_ieee_and_springer():
    renderer = JinjaLaTeXRenderer(".")
    authors = [
        {"name": "A One", "affiliations": ["Inst A, City, Country"]},
        {"name": "B Two", "affiliations": ["Inst B, City, Country", "*", "b@x.com"]},
    ]

    ieee_block = renderer._generate_author_block(authors, "ieee")
    springer_block = renderer._generate_author_block(authors, "springer")

    assert "\\IEEEauthorblockN{" in ieee_block
    assert "\\IEEEauthorblockA{" in ieee_block
    assert "B Two\\textsuperscript{*}" in ieee_block
    assert "\\texttt{b@x.com}" in ieee_block
    assert "\\thanks{" not in ieee_block

    assert "\\author{" in springer_block
    assert "\\institute{" in springer_block
    assert "B Two\\inst{2}*" in springer_block
    assert "\\email{b@x.com}" in springer_block
