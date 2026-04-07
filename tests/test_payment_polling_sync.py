from __future__ import annotations

from datetime import datetime, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient

import backend.app.routers.payment_routes as router_payment
from backend.app import models
from backend.app.database import SessionLocal
from backend.app.main import app


client = TestClient(app)


def _dang_ky_dang_nhap_nguoi_dung() -> tuple[int, dict[str, str]]:
    suffix = uuid4().hex[:10]
    email = f"pay-{suffix}@example.com"
    username = f"pay_{suffix}"

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

    data = login.json()
    token = data["access_token"]
    user_id = int(data["user"]["id"])
    return user_id, {"Authorization": f"Bearer {token}"}


def _lay_so_du_token(headers: dict[str, str]) -> int:
    me = client.get("/api/auth/me", headers=headers)
    assert me.status_code == 200
    return int(me.json().get("token_balance", 0))


def _lay_payment(payment_id: int) -> models.Payment | None:
    db = SessionLocal()
    try:
        return db.query(models.Payment).filter(models.Payment.id == payment_id).first()
    finally:
        db.close()


def _lay_ledger_moi_nhat(user_id: int) -> models.TokenLedger | None:
    db = SessionLocal()
    try:
        return (
            db.query(models.TokenLedger)
            .filter(models.TokenLedger.user_id == user_id)
            .order_by(models.TokenLedger.id.desc())
            .first()
        )
    finally:
        db.close()


def test_payment_polling_flow_pending_then_completed(monkeypatch) -> None:
    user_id, headers = _dang_ky_dang_nhap_nguoi_dung()
    so_du_ban_dau = _lay_so_du_token(headers)

    tao = client.post(
        "/api/payment/create",
        json={"amount_vnd": 15000},
        headers=headers,
    )
    assert tao.status_code == 200
    payment_id = int(tao.json()["payment_id"])

    monkeypatch.setattr(router_payment, "check_payment_status", lambda *_args, **_kwargs: (False, ""))
    pending = client.get(f"/api/payment/status/{payment_id}", headers=headers)
    assert pending.status_code == 200
    assert pending.json().get("status") == "pending"

    monkeypatch.setattr(router_payment, "check_payment_status", lambda *_args, **_kwargs: (True, "TX_OK_001"))
    completed = client.get(f"/api/payment/status/{payment_id}", headers=headers)
    assert completed.status_code == 200
    assert completed.json().get("status") == "completed"
    assert int(completed.json().get("token_nhan", 0)) == 15000

    so_du_sau = _lay_so_du_token(headers)
    assert so_du_sau == so_du_ban_dau + 15000

    payment = _lay_payment(payment_id)
    assert payment is not None
    assert payment.status == "completed"

    ledger = _lay_ledger_moi_nhat(user_id)
    assert ledger is not None
    assert ledger.reason == "nạp token qua sepay"
    assert "sepay_tx=TX_OK_001" in str(ledger.meta_json)


def test_payment_failed_can_still_complete_when_money_arrives_late(monkeypatch) -> None:
    user_id, headers = _dang_ky_dang_nhap_nguoi_dung()

    tao = client.post(
        "/api/payment/create",
        json={"amount_vnd": 12000},
        headers=headers,
    )
    assert tao.status_code == 200
    payment_id = int(tao.json()["payment_id"])

    db = SessionLocal()
    try:
        payment = db.query(models.Payment).filter(models.Payment.id == payment_id).first()
        assert payment is not None
        payment.status = "pending"
        payment.created_at = datetime.utcnow() - timedelta(minutes=61)
        db.commit()
    finally:
        db.close()

    monkeypatch.setattr(router_payment, "check_payment_status", lambda *_args, **_kwargs: (True, "TX_LATE_999"))

    status_resp = client.get(f"/api/payment/status/{payment_id}", headers=headers)
    assert status_resp.status_code == 200
    assert status_resp.json().get("status") == "completed"
    assert int(status_resp.json().get("token_nhan", 0)) == 12000

    payment_after = _lay_payment(payment_id)
    assert payment_after is not None
    assert payment_after.status == "completed"

    ledger = _lay_ledger_moi_nhat(user_id)
    assert ledger is not None
    assert ledger.reason == "nạp token qua sepay"
    assert "TX_LATE_999" in str(ledger.meta_json)
