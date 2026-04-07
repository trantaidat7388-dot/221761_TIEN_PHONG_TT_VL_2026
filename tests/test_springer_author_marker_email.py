from backend.core_engine.author_strategies import SpringerAuthorStrategy


def test_springer_author_ignores_marker_and_email_for_inst_indexing():
    strategy = SpringerAuthorStrategy()
    block = strategy.generate(
        [
            {
                "name": "NGUYEN-HOANG Anh-Tuan",
                "affiliations": ["Nam Can Tho University, Can Tho, Vietnam"],
            },
            {
                "name": "TRAN Binh-An",
                "affiliations": ["Adhightech Ltd.,Can Tho, Viet Nam"],
            },
            {
                "name": "NGUYEN Anh-Duy",
                "affiliations": ["Adhightech Ltd.,Can Tho, Viet Nam", "*", "nguyenanhduy@adhigtechn.com"],
            },
        ]
    )

    # Marker/email must not create new institute indexes.
    assert "NGUYEN Anh-Duy\\inst{2}*" in block
    assert "\\inst{2,3" not in block
    assert "\\inst{4" not in block

    # Exactly two institute entries from two unique affiliations.
    assert "Nam Can Tho University, Can Tho, Vietnam" in block
    assert "Adhightech Ltd.,Can Tho, Viet Nam" in block
    assert "\\email{nguyenanhduy@adhigtechn.com}" in block
