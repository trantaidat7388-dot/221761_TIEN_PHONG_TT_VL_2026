from backend.core_engine.ast_parser import WordASTParser


def test_parse_authors_names_then_affiliations_block():
    parser = WordASTParser("dummy.docx")
    authors_raw = [
        "NGUYEN-HOANG Anh-Tuan",
        "TRAN Binh-An",
        "NGUYEN Anh-Duy",
        "Nam Can Tho University, Can Tho, Vietnam",
        "Adhightech Ltd., Can Tho, Viet Nam",
        "nguyenanhduy@adhightech.com",
    ]

    authors = parser._parse_authors(authors_raw)

    assert len(authors) == 3
    assert authors[0]["name"] == "NGUYEN-HOANG Anh-Tuan"
    assert authors[1]["name"] == "TRAN Binh-An"
    assert authors[2]["name"] == "NGUYEN Anh-Duy"

    assert any("Nam Can Tho University" in a for a in authors[0]["affiliations"])
    assert any("Adhightech Ltd." in a for a in authors[1]["affiliations"])
    assert any("@" in a for a in authors[2]["affiliations"])
