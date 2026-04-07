from backend.core_engine.author_strategies import IEEEAuthorStrategy


def test_ieee_author_strategy_splits_comma_affiliation_lines():
    strategy = IEEEAuthorStrategy()
    block = strategy.generate(
        [
            {
                "name": "NGUYEN-HOANG Anh-Tuan",
                "affiliations": ["Nam Can Tho University, Can Tho, Vietnam"],
            },
            {
                "name": "TRAN Binh-An",
                "affiliations": ["Adhightech Ltd., Can Tho, Viet Nam"],
            },
            {
                "name": "NGUYEN Anh-Duy",
                "affiliations": ["Adhightech Ltd., Can Tho, Viet Nam", "*", "nguyenanhduy@adhightech.com"],
            },
        ]
    )

    assert "\\textit{Nam Can Tho University, Can Tho, Vietnam}" in block
    assert "\\textit{Adhightech Ltd., Can Tho, Viet Nam}" in block
    assert "nguyenanhduy@adhightech.com" in block
    assert "NGUYEN Anh-Duy\\textsuperscript{*}" in block
    assert "\\textit{*}" not in block
    assert "\\texttt{nguyenanhduy@adhightech.com}" in block
    assert "\\thanks{" not in block
