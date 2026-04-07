from backend.core_engine.ast_parser import WordASTParser


def test_parse_authors_filters_springer_placeholder_and_splits_email():
    parser = WordASTParser("dummy.docx")
    authors_raw = [
        "TRẦN Tấn-Đạt",
        "Second Author",
        "Faculty of Information Technology, Nam Can Tho University, Can Tho City, Viet Nam",
        "Springer Heidelberg, Tiergartenstr. 17, 69121 Heidelberg, Germanydat221761@student.nctu.edu.vn",
    ]

    authors = parser._parse_authors(authors_raw)

    assert len(authors) == 1
    assert authors[0]["name"] == "TRẦN Tấn-Đạt"
    assert any("Nam Can Tho University" in a for a in authors[0]["affiliations"])
    assert all("Springer Heidelberg" not in a for a in authors[0]["affiliations"])
    assert any("@" in a for a in authors[0]["affiliations"])
