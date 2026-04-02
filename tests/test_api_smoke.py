from __future__ import annotations

from pathlib import Path
import zipfile
import pytest

pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from backend.app.main import app
import backend.app.routers.chuyen_doi as router_chuyen_doi
import backend.app.routers.templates as router_templates


client = TestClient(app)


class GiaLapBoChuyenDoi:
    def __init__(self, duong_dan_word: str, duong_dan_template: str, duong_dan_dau_ra: str, thu_muc_anh: str, mode: str):
        self.duong_dan_dau_ra = duong_dan_dau_ra
        self.thu_muc_anh = thu_muc_anh
        self.ir = {"metadata": {"total_formulas": 0}}

    def chuyen_doi(self) -> None:
        Path(self.thu_muc_anh).mkdir(parents=True, exist_ok=True)
        Path(self.duong_dan_dau_ra).write_text(
            "\\documentclass{article}\\begin{document}Noi dung test\\end{document}",
            encoding="utf-8",
        )


def _gia_lap_dong_goi_thu_muc_dau_ra(work_dir: str, output_zip_path: str, exclude_suffixes=None, generated_tex_name: str | None = None) -> str:
    with zipfile.ZipFile(output_zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        if generated_tex_name:
            duong_dan_tex = Path(work_dir) / generated_tex_name
            if duong_dan_tex.exists():
                zf.write(duong_dan_tex, "main.tex")
    return output_zip_path


def test_smoke_upload_template_tex(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(router_templates, "CUSTOM_TEMPLATE_FOLDER", tmp_path)
    tep_tex = b"\\documentclass{article}\\begin{document}A\\end{document}"

    response = client.post(
        "/api/templates/upload",
        files={"file": ("mau.tex", tep_tex, "application/x-tex")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["thanhCong"] is True


def test_smoke_chuyen_doi_stream(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(router_chuyen_doi, "ChuyenDoiWordSangLatex", GiaLapBoChuyenDoi)
    monkeypatch.setattr(router_chuyen_doi, "dong_goi_thu_muc_dau_ra", _gia_lap_dong_goi_thu_muc_dau_ra)

    tep_word = b"gia lap noi dung word"
    tep_template = b"\\documentclass{article}\\begin{document}<<content>><< /content >>\\end{document}"

    response = client.post(
        "/api/chuyen-doi-stream",
        params={"template_type": "ieee_conference"},
        files={
            "file": ("mau.docx", tep_word, "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
            "template_file": ("mau.tex", tep_template, "application/x-tex"),
        },
    )

    assert response.status_code == 200
    noi_dung = response.text
    assert "\"done\": true" in noi_dung
    assert "Ho\u00e0n t\u1ea5t" in noi_dung or "Hoàn tất" in noi_dung
