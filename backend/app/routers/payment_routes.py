from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime

from .. import models, auth
from ..database import lay_db
from ..config import NAME_WEB, APP_ENV
from ..services.sepay_sync import encode_payment_id, check_payment_status

router = APIRouter(prefix="/api/payment", tags=["Payment"])

class YeuCauTaoPayment(BaseModel):
    amount_vnd: int

@router.post("/create")
def tao_payment(req: YeuCauTaoPayment, db: Session = Depends(lay_db), current_user: models.User = Depends(auth.lay_nguoi_dung_hien_tai)):
    if req.amount_vnd < 10000:
        raise HTTPException(status_code=400, detail="Số tiền nạp tối thiểu là 10,000 VNĐ")

    # Tỷ lệ: 1 VND = 1 Token
    token_amount = req.amount_vnd

    payment = models.Payment(
        user_id=current_user.id,
        amount_vnd=req.amount_vnd,
        token_amount=token_amount,
        status="pending"
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    hex_id = encode_payment_id(payment.id)
    noidung_ck = f"{NAME_WEB}NAPTOKEN{hex_id}"

    return {
        "thanh_cong": True,
        "payment_id": payment.id,
        "hex_id": hex_id,
        "noidung_ck": noidung_ck,
        "amount_vnd": payment.amount_vnd,
        "token_amount": payment.token_amount
    }

@router.get("/status/{payment_id}")
def kiem_tra_trang_thai_payment(payment_id: int, db: Session = Depends(lay_db), current_user: models.User = Depends(auth.lay_nguoi_dung_hien_tai)):
    payment = db.query(models.Payment).filter(
        models.Payment.id == payment_id,
        models.Payment.user_id == current_user.id
    ).first()

    if not payment:
        raise HTTPException(status_code=404, detail="Không tìm thấy hóa đơn")

    if payment.status == "completed":
        return {"thanh_cong": True, "status": "completed"}

    # Nếu đang pending, gọi SePay để check
    is_paid, tx_id = check_payment_status(payment.id, payment.amount_vnd)
    if is_paid:
        # Cập nhật payment
        payment.status = "completed"
        payment.updated_at = datetime.utcnow()
        
        # Nhỏ gọn: update user token
        current_user.token_balance += payment.token_amount
        
        # Thêm lịch sử Ledger
        db.add(models.TokenLedger(
            user_id=current_user.id,
            delta_token=payment.token_amount,
            balance_after=current_user.token_balance,
            reason="nạp token qua sepay",
            meta_json=f"sepay_tx={tx_id}"
        ))
        
        db.commit()
        db.refresh(payment)
        return {"thanh_cong": True, "status": "completed", "token_nhan": payment.token_amount}

    return {"thanh_cong": True, "status": payment.status}


@router.post("/dev/complete/{payment_id}")
def xac_nhan_thanh_toan_thu_cong_dev(
    payment_id: int,
    db: Session = Depends(lay_db),
    current_user: models.User = Depends(auth.lay_nguoi_dung_hien_tai),
):
    """Dev-only fallback: manually complete a payment when SePay/bank is unavailable."""
    if APP_ENV in {"production", "prod"}:
        raise HTTPException(status_code=403, detail="Endpoint này chỉ dùng ở môi trường development")

    payment = db.query(models.Payment).filter(
        models.Payment.id == payment_id,
        models.Payment.user_id == current_user.id
    ).first()

    if not payment:
        raise HTTPException(status_code=404, detail="Không tìm thấy hóa đơn")

    if payment.status == "completed":
        return {"thanh_cong": True, "status": "completed", "token_nhan": payment.token_amount}

    payment.status = "completed"
    payment.updated_at = datetime.utcnow()
    current_user.token_balance += payment.token_amount

    db.add(models.TokenLedger(
        user_id=current_user.id,
        delta_token=payment.token_amount,
        balance_after=current_user.token_balance,
        reason="nạp token dev manual",
        meta_json=f"payment_id={payment.id}"
    ))

    db.commit()
    return {"thanh_cong": True, "status": "completed", "token_nhan": payment.token_amount}
