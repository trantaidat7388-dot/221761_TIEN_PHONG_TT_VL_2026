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
