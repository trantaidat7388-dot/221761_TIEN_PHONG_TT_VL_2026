from __future__ import annotations

from pathlib import Path
import zipfile

from fastapi.testclient import TestClient

from backend.app.main import app, _tao_tai_khoan_admin_mac_dinh
import backend.app.routers.chuyen_doi as router_chuyen_doi


client = TestClient(app)


class _GiaLapBoChuyenDoiOK:
    def __init__(self, duong_dan_word: str, duong_dan_template: str, duong_dan_dau_ra: str, thu_muc_anh: str, mode: str):
        self.duong_dan_dau_ra = duong_dan_dau_ra
        self.thu_muc_anh = thu_muc_anh
        self.ir = {"metadata": {"total_formulas": 0}}

    def chuyen_doi(self) -> None:
        Path(self.thu_muc_anh).mkdir(parents=True, exist_ok=True)
        Path(self.duong_dan_dau_ra).write_text(
            "\\documentclass{article}\\begin{document}Token test\\end{document}",
            encoding="utf-8",
        )


class _GiaLapBoChuyenDoiFail(_GiaLapBoChuyenDoiOK):
    def chuyen_doi(self) -> None:
        raise RuntimeError("Gia lap loi convert")


async def _don_dep_nhanh(_duong_dan) -> None:
    return None


def _gia_lap_dong_goi(work_dir: str, output_zip_path: str, exclude_suffixes=None, generated_tex_name: str | None = None) -> str:
    with zipfile.ZipFile(output_zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        if generated_tex_name:
            path_tex = Path(work_dir) / generated_tex_name
            if path_tex.exists():
                zf.write(path_tex, "main.tex")
    return output_zip_path


def _register_and_login(email: str, username: str) -> tuple[int, dict[str, str]]:
    reg = client.post(
        "/api/auth/register",
        json={"username": username, "email": email, "password": "123456"},
    )
    assert reg.status_code in (200, 400)

    login = client.post(
        "/api/auth/login",
        json={"email": email, "password": "123456"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    uid = login.json()["user"]["id"]
    return uid, {"Authorization": f"Bearer {token}"}


def _admin_headers() -> dict[str, str]:
    _tao_tai_khoan_admin_mac_dinh()
    login = client.post(
        "/api/auth/login",
        json={"email": "admin@word2latex.local", "password": "Admin@123456"},
    )
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def _token_balance(headers: dict[str, str]) -> int:
    me = client.get("/api/auth/me", headers=headers)
    assert me.status_code == 200
    return int(me.json().get("token_balance", 0))


def test_token_deduct_success_flow(monkeypatch) -> None:
    monkeypatch.setattr(router_chuyen_doi, "ChuyenDoiWordSangLatex", _GiaLapBoChuyenDoiOK)
    monkeypatch.setattr(router_chuyen_doi, "dong_goi_thu_muc_dau_ra", _gia_lap_dong_goi)
    monkeypatch.setattr(router_chuyen_doi, "don_dep_sau_15_phut", _don_dep_nhanh)

    uid, headers = _register_and_login("token-ok@example.com", "token_ok_user")
    before_balance = _token_balance(headers)

    response = client.post(
        "/api/chuyen-doi",
        params={"template_type": "ieee_conference"},
        headers=headers,
        files={
            "file": ("mau.docx", b"fake-word-content", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
            "template_file": ("mau.tex", b"\\documentclass{article}\\begin{document}A\\end{document}", "application/x-tex"),
        },
    )
    assert response.status_code == 200

    body = response.json()
    token_cost = int(body.get("token_usage", {}).get("token_cost", 0))
    assert token_cost >= 1

    after_balance = _token_balance(headers)
    assert after_balance == before_balance - token_cost

    admin_headers = _admin_headers()
    hist = client.get(f"/api/admin/users/{uid}/history?limit=10", headers=admin_headers)
    assert hist.status_code == 200
    assert any((x.get("token_cost") or 0) >= 1 and x.get("status") == "Thành công" for x in hist.json().get("danh_sach", []))


def test_token_refund_on_failure(monkeypatch) -> None:
    monkeypatch.setattr(router_chuyen_doi, "ChuyenDoiWordSangLatex", _GiaLapBoChuyenDoiFail)
    monkeypatch.setattr(router_chuyen_doi, "dong_goi_thu_muc_dau_ra", _gia_lap_dong_goi)
    monkeypatch.setattr(router_chuyen_doi, "don_dep_sau_15_phut", _don_dep_nhanh)

    uid, headers = _register_and_login("token-fail@example.com", "token_fail_user")
    before_balance = _token_balance(headers)

    response = client.post(
        "/api/chuyen-doi",
        params={"template_type": "ieee_conference"},
        headers=headers,
        files={
            "file": ("mau.docx", b"fake-word-content", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
            "template_file": ("mau.tex", b"\\documentclass{article}\\begin{document}A\\end{document}", "application/x-tex"),
        },
    )
    assert response.status_code == 400

    after_balance = _token_balance(headers)
    assert after_balance == before_balance

    admin_headers = _admin_headers()
    hist = client.get(f"/api/admin/users/{uid}/history?limit=10", headers=admin_headers)
    assert hist.status_code == 200
    assert any(x.get("status") == "Thất bại" and bool(x.get("token_refunded")) for x in hist.json().get("danh_sach", []))

    ledger = client.get(f"/api/admin/users/{uid}/token-ledger?limit=20", headers=admin_headers)
    assert ledger.status_code == 200
    reasons = [x.get("reason") for x in ledger.json().get("danh_sach", [])]
    assert "convert_deduct" in reasons
    assert "refund" in reasons
