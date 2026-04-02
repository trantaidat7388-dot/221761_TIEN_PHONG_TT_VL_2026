from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.main import (
    _dam_bao_cot_vai_tro_nguoi_dung,
    _dam_bao_schema_users_premium_token_google,
    _dam_bao_schema_conversion_history_token_fields,
    _dam_bao_schema_token_ledger_indexes,
    _dam_bao_schema_admin_audit_indexes,
    _tao_tai_khoan_admin_mac_dinh,
)


client = TestClient(app)


def _prepare_schema_and_admin() -> None:
    _dam_bao_cot_vai_tro_nguoi_dung()
    _dam_bao_schema_users_premium_token_google()
    _dam_bao_schema_conversion_history_token_fields()
    _dam_bao_schema_token_ledger_indexes()
    _dam_bao_schema_admin_audit_indexes()
    _tao_tai_khoan_admin_mac_dinh()


def _dang_nhap_admin_headers() -> dict[str, str]:
    login = client.post("/api/auth/login", json={"email": "admin@word2latex.local", "password": "Admin@123456"})
    assert login.status_code == 200
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _tao_user_test_if_needed() -> int:
    email = "smoke-user-token@example.com"
    reg = client.post(
        "/api/auth/register",
        json={"username": "smoke_user_token", "email": email, "password": "123456"},
    )
    if reg.status_code in (200, 400):
        pass

    headers = _dang_nhap_admin_headers()
    users = client.get("/api/admin/users", headers=headers)
    assert users.status_code == 200
    for u in users.json().get("danh_sach", []):
        if u.get("email") == email:
            return u["id"]
    raise AssertionError("Could not find smoke user")


def test_admin_token_grant_and_audit_log() -> None:
    _prepare_schema_and_admin()
    headers = _dang_nhap_admin_headers()
    user_id = _tao_user_test_if_needed()

    grant = client.post(
        f"/api/admin/users/{user_id}/token/grant",
        headers=headers,
        json={"amount": 7, "reason": "pytest grant"},
    )
    assert grant.status_code == 200

    ledger = client.get(f"/api/admin/users/{user_id}/token-ledger?limit=10", headers=headers)
    assert ledger.status_code == 200
    assert any(item.get("reason") == "admin_grant" for item in ledger.json().get("danh_sach", []))

    audit = client.get("/api/admin/audit-logs?limit=50", headers=headers)
    assert audit.status_code == 200
    assert any(item.get("action") == "admin.token_grant" for item in audit.json().get("danh_sach", []))
