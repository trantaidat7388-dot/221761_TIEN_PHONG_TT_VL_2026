import pytest

from backend.core_engine.chuyen_doi import ChuyenDoiWordSangLatex


def test_ieee_mode_rejects_llncs_template_class():
    conv = ChuyenDoiWordSangLatex(
        duong_dan_word="dummy.docx",
        duong_dan_template="dummy.tex",
        duong_dan_dau_ra="out.tex",
        expected_doc_class="ieee",
    )

    with pytest.raises(ValueError, match="IEEEtran"):
        conv._validate_expected_template_class(r"\documentclass[runningheads]{llncs}")


def test_ieee_mode_accepts_ieeetran_template_class():
    conv = ChuyenDoiWordSangLatex(
        duong_dan_word="dummy.docx",
        duong_dan_template="dummy.tex",
        duong_dan_dau_ra="out.tex",
        expected_doc_class="ieee",
    )

    conv._validate_expected_template_class(r"\documentclass[conference]{IEEEtran}")
