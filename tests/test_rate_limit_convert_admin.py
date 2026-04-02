from __future__ import annotations

from fastapi.testclient import TestClient

import backend.app.main as main_module
from backend.app.main import app, _tao_tai_khoan_admin_mac_dinh


client = TestClient(app)


def _login_admin_headers() -> dict[str, str]:
    _tao_tai_khoan_admin_mac_dinh()
    res = client.post(
        "/api/auth/login",
        json={"email": "admin@word2latex.local", "password": "Admin@123456"},
    )
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_rate_limit_convert_group() -> None:
    old_limit = main_module.RATE_LIMIT_CONVERT_PER_MINUTE
    try:
        main_module.RATE_LIMIT_CONVERT_PER_MINUTE = 2
        main_module._rate_limit_store.clear()

        # Invalid payload is fine here; we only test middleware throttling.
        r1 = client.post("/api/chuyen-doi")
        r2 = client.post("/api/chuyen-doi")
        r3 = client.post("/api/chuyen-doi")

        assert r1.status_code in (400, 401, 402, 422)
        assert r2.status_code in (400, 401, 402, 422)
        assert r3.status_code == 429
    finally:
        main_module.RATE_LIMIT_CONVERT_PER_MINUTE = old_limit
        main_module._rate_limit_store.clear()


def test_rate_limit_admin_group() -> None:
    old_limit = main_module.RATE_LIMIT_ADMIN_PER_MINUTE
    headers = _login_admin_headers()
    try:
        main_module.RATE_LIMIT_ADMIN_PER_MINUTE = 2
        main_module._rate_limit_store.clear()

        r1 = client.get("/api/admin/users", headers=headers)
        r2 = client.get("/api/admin/users", headers=headers)
        r3 = client.get("/api/admin/users", headers=headers)

        assert r1.status_code == 200
        assert r2.status_code == 200
        assert r3.status_code == 429
    finally:
        main_module.RATE_LIMIT_ADMIN_PER_MINUTE = old_limit
        main_module._rate_limit_store.clear()
