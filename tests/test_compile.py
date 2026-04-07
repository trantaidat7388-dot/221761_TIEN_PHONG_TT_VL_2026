from pathlib import Path
from types import SimpleNamespace
import pytest

from backend.core_engine.utils import bien_dich_latex, giai_nen_mau_zip, tim_file_tex_chinh


ROOT_DIR = Path(__file__).resolve().parents[1]


def test_tim_tex_chinh_tu_zip_template(tmp_path: Path) -> None:
    """Kiem tra co the giai nen va tim file tex chinh tu template zip."""
    input_dir = ROOT_DIR / "input_data"
    ds_zip = sorted(input_dir.glob("*.zip"))
    if not ds_zip:
        pytest.skip("Khong co file template zip trong input_data")

    duong_dan_zip = ds_zip[0]
    thu_muc_dich = tmp_path / "template"
    thu_muc_dich.mkdir(parents=True, exist_ok=True)

    giai_nen_mau_zip(str(duong_dan_zip), str(thu_muc_dich))
    tex_chinh = tim_file_tex_chinh(str(thu_muc_dich))

    assert Path(tex_chinh).exists()
    assert Path(tex_chinh).suffix.lower() == ".tex"


@pytest.mark.integration
def test_chuyen_doi_duong_ong_docx_co_the_khoi_tao(tmp_path: Path) -> None:
    """Smoke level: kiem tra tai nguyen dau vao de phuc vu test chuyen doi full stack."""
    thu_muc_word = ROOT_DIR / "input_data" / "Template_word"
    ds_docx = sorted(thu_muc_word.glob("*.docx")) + sorted(thu_muc_word.glob("*.docm"))
    if not ds_docx:
        pytest.skip("Khong co file Word mau trong input_data/Template_word")

    assert ds_docx[0].exists()


def test_bien_dich_latex_khong_copy_khi_cung_file(monkeypatch, tmp_path: Path) -> None:
    """Tranh SameFileError khi file PDF dau ra da nam dung vi tri dich."""
    tex_path = tmp_path / "job_output.tex"
    pdf_path = tmp_path / "job_output.pdf"
    tex_path.write_text("\\documentclass{article}\\begin{document}x\\end{document}", encoding="utf-8")
    pdf_path.write_bytes(b"%PDF-1.4\n% mock\n")

    def _fake_run(*args, **kwargs):
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("backend.core_engine.utils.subprocess.run", _fake_run)

    ok, err = bien_dich_latex(str(tex_path), engine="xelatex")
    assert ok is True
    assert err == ""
