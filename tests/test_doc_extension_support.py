from backend.app.routers.chuyen_doi import _la_file_word_hop_le


def test_word_extension_validator_accepts_doc_family():
    assert _la_file_word_hop_le("paper.doc")
    assert _la_file_word_hop_le("paper.docx")
    assert _la_file_word_hop_le("paper.docm")


def test_word_extension_validator_rejects_non_word():
    assert not _la_file_word_hop_le("paper.pdf")
    assert not _la_file_word_hop_le("paper.txt")
