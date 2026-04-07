from backend.core_engine.author_strategies import IEEEAuthorStrategy


def test_ieee_author_block_keeps_email_in_thanks_not_affiliation():
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

    # Corresponding email must be in footnote note
    assert "\\thanks{* Corresponding author: b@x.com}" in block
    # Email should not remain in affiliation block anymore
    assert "\\IEEEauthorblockA{\\textit{Inst B, City, Country} \\\\ b@x.com}" not in block
