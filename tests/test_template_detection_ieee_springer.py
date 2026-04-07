from backend.core_engine.utils import phat_hien_loai_tai_lieu


def test_detect_ieee_and_springer_document_classes():
    ieee_src = r"\\documentclass[conference]{IEEEtran}"
    springer_llncs = r"\\documentclass[runningheads]{llncs}"
    springer_svjour = r"\\documentclass{svjour}"

    assert phat_hien_loai_tai_lieu(ieee_src) == "ieee"
    assert phat_hien_loai_tai_lieu(springer_llncs) == "springer"
    assert phat_hien_loai_tai_lieu(springer_svjour) == "springer"
