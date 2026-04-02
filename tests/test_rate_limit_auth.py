from __future__ import annotations

from fastapi.testclient import TestClient

import backend.app.main as main_module
from backend.app.main import app


def test_rate_limit_auth_group() -> None:
    client = TestClient(app)

    old_limit = main_module.RATE_LIMIT_AUTH_PER_MINUTE
    old_store = main_module._rate_limit_store

    try:
        main_module.RATE_LIMIT_AUTH_PER_MINUTE = 2
        main_module._rate_limit_store.clear()

        payload = {"email": "nope@example.com", "password": "wrongpass"}

        r1 = client.post("/api/auth/login", json=payload)
        r2 = client.post("/api/auth/login", json=payload)
        r3 = client.post("/api/auth/login", json=payload)

        assert r1.status_code in (401, 400)
        assert r2.status_code in (401, 400)
        assert r3.status_code == 429
    finally:
        main_module.RATE_LIMIT_AUTH_PER_MINUTE = old_limit
        main_module._rate_limit_store = old_store
        main_module._rate_limit_store.clear()
