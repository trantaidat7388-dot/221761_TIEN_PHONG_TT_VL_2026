from backend.core_engine.author_strategies import IEEEAuthorStrategy


def test_ieee_author_block_shows_email_in_affiliation_not_footnote():
    strategy = IEEEAuthorStrategy()
    block = strategy.generate(
        [
            {
                "name": "A One",
                "affiliations": ["Inst A, City, Country"],
            },
            {
                "name": "B Two",
                "affiliations": ["Inst B, City, Country", "*", "b@x.com"],
            },
        ]
    )

    assert "\\texttt{b@x.com}" in block
    assert "\\thanks{" not in block


def test_ieee_shared_email_block_is_distributed_by_author_order():
    strategy = IEEEAuthorStrategy()
    shared = ["Shared University", "a@x.com", "b@x.com", "c@x.com"]
    block = strategy.generate(
        [
            {"name": "A One", "affiliations": shared},
            {"name": "B Two", "affiliations": shared},
            {"name": "C Three", "affiliations": shared},
        ]
    )

    assert block.count("\\texttt{a@x.com}") == 1
    assert block.count("\\texttt{b@x.com}") == 1
    assert block.count("\\texttt{c@x.com}") == 1


def test_ieee_authors_with_one_shared_affiliation_keep_word_style_columns():
    strategy = IEEEAuthorStrategy()
    block = strategy.generate(
        [
            {"name": "A One", "affiliations": ["Shared University", "a@x.com"]},
            {"name": "B Two", "affiliations": ["Shared University", "b@x.com"]},
            {"name": "C Three", "affiliations": ["Shared University", "c@x.com"]},
        ]
    )

    assert block.count("\\parbox[t]{0.31\\textwidth}") == 3
    assert block.count("\\textit{Shared University}") == 3
    assert block.count("\\hfill") == 2


def test_ieee_long_affiliation_is_split_to_preserve_author_columns():
    strategy = IEEEAuthorStrategy()
    block = strategy.generate(
        [
            {
                "name": "A One",
                "affiliations": [
                    "Faculty of IT, Example University, Main Street, City, Country",
                    "a@x.com",
                ],
            }
        ]
    )

    assert "\\textit{Faculty of IT, Example University}" in block
    assert "\\textit{Main Street, City}" in block
    assert "\\textit{Country}" in block
