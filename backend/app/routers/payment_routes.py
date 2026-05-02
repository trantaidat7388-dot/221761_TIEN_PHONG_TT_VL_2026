from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from .. import models, auth
from ..database import lay_db
from ..config import NAME_WEB, APP_ENV, TOPUP_PACKAGES, PREMIUM_PACKAGES
from ..services.sepay_sync import encode_payment_id, check_payment_status

router = APIRouter(prefix="/api/payment", tags=["Payment"])
PAYMENT_EXPIRE_MINUTES = 60

class YeuCauTaoPayment(BaseModel):
    amount_vnd: int
    plan_key: str | None = None

@router.post("/create")
def tao_payment(req: YeuCauTaoPayment, db: Session = Depends(lay_db), current_user: models.User = Depends(auth.lay_nguoi_dung_hien_tai)):
    if req.amount_vnd < 10000:
        raise HTTPException(status_code=400, detail="Số tiền nạp tối thiểu là 10,000 VNĐ")

    # Xác định số token dựa trên gói
    if req.plan_key:
        # Combo Premium: lấy token_bonus từ config
        plan = PREMIUM_PACKAGES.get(req.plan_key)
        if not plan:
            raise HTTPException(status_code=400, detail=f"Gói Premium '{req.plan_key}' không tồn tại")
        token_amount = plan.get("token_bonus", 0)
    else:
        # Nạp lẻ: chỉ chấp nhận mệnh giá trong TOPUP_PACKAGES
        token_amount = TOPUP_PACKAGES.get(req.amount_vnd)
        if token_amount is None:
            valid_amounts = ', '.join(f"{a:,}đ" for a in sorted(TOPUP_PACKAGES.keys()))
            raise HTTPException(
                status_code=400,
                detail=f"Mệnh giá {req.amount_vnd:,}đ không hợp lệ. Chỉ chấp nhận: {valid_amounts}"
            )

    payment = models.Payment(
        user_id=current_user.id,
        amount_vnd=req.amount_vnd,
        token_amount=token_amount,
        status="pending",
        plan_key=req.plan_key
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

    # Hóa đơn quá hạn sẽ chuyển failed để frontend hiển thị rõ trạng thái.
    # Dù vậy, hệ thống vẫn tiếp tục đối soát SePay để hỗ trợ "tiền về muộn".
    if payment.status == "pending":
        gioi_han = payment.created_at + timedelta(minutes=PAYMENT_EXPIRE_MINUTES)
        if datetime.utcnow() > gioi_han:
            payment.status = "failed"
            payment.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(payment)

    # Nếu chưa completed (pending/failed), gọi SePay để check
    is_paid, tx_id = check_payment_status(payment.id, payment.amount_vnd)
    if is_paid:
        # Cập nhật payment
        payment.status = "completed"
        payment.updated_at = datetime.utcnow()
        
        # Nhỏ gọn: update user token
        current_user.token_balance += payment.token_amount
        
        # [Way A] Xử lý kích hoạt Premium Combo nếu có plan_key
        thong_bao_extra = ""
        if payment.plan_key:
            from ..config import PREMIUM_PACKAGES
            plan = PREMIUM_PACKAGES.get(payment.plan_key)
            if plan:
                so_ngay = plan.get("so_ngay", 30)
                now = datetime.utcnow()
                if current_user.plan_type == "premium" and current_user.premium_expires_at and current_user.premium_expires_at > now:
                    base_time = current_user.premium_expires_at
                else:
                    base_time = now
                    current_user.premium_started_at = now
                
                current_user.plan_type = "premium"
                current_user.premium_expires_at = base_time + timedelta(days=so_ngay)
                thong_bao_extra = f" + Kích hoạt Premium {so_ngay} ngày"

        # Thêm lịch sử Ledger
        db.add(models.TokenLedger(
            user_id=current_user.id,
            delta_token=payment.token_amount,
            balance_after=current_user.token_balance,
            reason=f"nạp combo {payment.plan_key}" if payment.plan_key else "nạp token qua sepay",
            meta_json=f"sepay_tx={tx_id}"
        ))
        
        db.commit()
        db.refresh(payment)
        return {
            "thanh_cong": True, 
            "status": "completed", 
            "token_nhan": payment.token_amount,
            "thong_bao": f"Nạp thành công {payment.token_amount} token{thong_bao_extra}"
        }

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

    # [Way A] Xử lý kích hoạt Premium Combo nếu có plan_key
    thong_bao_extra = ""
    if payment.plan_key:
        from ..config import PREMIUM_PACKAGES
        plan = PREMIUM_PACKAGES.get(payment.plan_key)
        if plan:
            so_ngay = plan.get("so_ngay", 30)
            now = datetime.utcnow()
            if current_user.plan_type == "premium" and current_user.premium_expires_at and current_user.premium_expires_at > now:
                base_time = current_user.premium_expires_at
            else:
                base_time = now
                current_user.premium_started_at = now
            
            current_user.plan_type = "premium"
            current_user.premium_expires_at = base_time + timedelta(days=so_ngay)
            thong_bao_extra = f" + Kích hoạt Premium {so_ngay} ngày"

    db.add(models.TokenLedger(
        user_id=current_user.id,
        delta_token=payment.token_amount,
        balance_after=current_user.token_balance,
        reason=f"nạp combo {payment.plan_key} (dev)" if payment.plan_key else "nạp token dev manual",
        meta_json=f"payment_id={payment.id}"
    ))

    db.commit()
    return {
        "thanh_cong": True, 
        "status": "completed", 
        "token_nhan": payment.token_amount,
        "thong_bao": f"Nạp dev thành công{thong_bao_extra}"
    }


@router.post("/webhook/sepay")
async def sepay_webhook(request: Request, db: Session = Depends(lay_db)):
    """
    Webhook endpoint nhận thông báo giao dịch từ SePay.
    Tài liệu: https://docs.sepay.vn/tich-hop-webhook.html
    """
    try:
        data = await request.json()
    except Exception:
        return {"status": "error", "message": "Invalid JSON"}

    # Lấy nội dung chuyển khoản
    content = data.get("transaction_content", data.get("content", ""))
    amount_in = data.get("amount_in", 0)
    sepay_tx_id = data.get("id")

    if not content or amount_in <= 0:
        return {"status": "ignored", "message": "Missing content or amount"}

    # Tìm payment_id từ nội dung
    from ..services.sepay_sync import extract_payment_id_from_content
    payment_id = extract_payment_id_from_content(content)
    
    if not payment_id:
        return {"status": "ignored", "message": "No payment_id found in content"}

    # Tìm payment trong DB
    payment = db.query(models.Payment).filter(models.Payment.id == payment_id).first()
    if not payment:
        return {"status": "error", "message": "Payment not found"}

    if payment.status == "completed":
        return {"status": "success", "message": "Already completed"}

    if amount_in < payment.amount_vnd:
        return {"status": "error", "message": "Insufficient amount"}

    # Cập nhật trạng thái
    payment.status = "completed"
    payment.updated_at = datetime.utcnow()
    
    # Cộng token cho user
    user = db.query(models.User).filter(models.User.id == payment.user_id).first()
    if user:
        user.token_balance += payment.token_amount
        
        # Xử lý Premium Combo
        if payment.plan_key:
            from ..config import PREMIUM_PACKAGES
            plan = PREMIUM_PACKAGES.get(payment.plan_key)
            if plan:
                so_ngay = plan.get("so_ngay", 30)
                now = datetime.utcnow()
                if user.plan_type == "premium" and user.premium_expires_at and user.premium_expires_at > now:
                    base_time = user.premium_expires_at
                else:
                    base_time = now
                    user.premium_started_at = now
                
                user.plan_type = "premium"
                user.premium_expires_at = base_time + timedelta(days=so_ngay)

        # Ghi ledger
        db.add(models.TokenLedger(
            user_id=user.id,
            delta_token=payment.token_amount,
            balance_after=user.token_balance,
            reason=f"nạp combo {payment.plan_key} (webhook)" if payment.plan_key else "nạp token sepay (webhook)",
            meta_json=f"sepay_tx={sepay_tx_id}"
        ))

    db.commit()
    return {"status": "success", "message": "Payment completed via webhook"}
