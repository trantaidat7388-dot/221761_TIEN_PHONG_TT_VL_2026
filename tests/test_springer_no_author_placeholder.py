from backend.core_engine.jinja_renderer import JinjaLaTeXRenderer


def test_generate_author_block_springer_empty_authors_uses_explicit_empty_block():
    renderer = JinjaLaTeXRenderer(".")

    block = renderer._generate_author_block([], "springer")

    assert block == "\\author{}\n\\institute{}"


def test_generate_author_block_ieee_empty_authors_stays_empty():
    renderer = JinjaLaTeXRenderer(".")

    block = renderer._generate_author_block([], "ieee")

    assert block == ""
