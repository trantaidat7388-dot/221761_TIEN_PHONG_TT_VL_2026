from backend.core_engine.author_strategies import IEEEAuthorStrategy


def test_ieee_author_escapes_hash_symbol():
    strategy = IEEEAuthorStrategy()
    block = strategy.generate(
        [
            {
                "name": "First Author#1",
                "affiliations": ["Company #1", "mail#tag@example.com"],
            }
        ]
    )

    assert "First Author\\#1" in block
    assert "Company \\#1" in block
