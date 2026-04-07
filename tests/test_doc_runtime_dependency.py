import pytest

from backend.core_engine import word_loader


def test_doc_conversion_raises_clear_error_when_libreoffice_missing(monkeypatch):
    monkeypatch.setattr(word_loader, "_tim_lenh_soffice", lambda: None)

    with pytest.raises(RuntimeError) as exc:
        word_loader.chuyen_doc_sang_docx("any_input.doc")

    msg = str(exc.value)
    assert "Khong ho tro file .doc" in msg
    assert "LibreOffice" in msg
    assert "LIBREOFFICE_PATH" in msg
