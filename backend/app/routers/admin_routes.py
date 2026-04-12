"""
admin_routes.py
Định nghĩa các API quản trị cho tài khoản admin.
"""

import shutil

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from .. import auth
from .. import models
from ..config import CUSTOM_TEMPLATE_FOLDER
from ..database import lay_db
from ..services.admin_system_config import cap_nhat_cau_hinh_he_thong, lay_cau_hinh_he_thong

router = APIRouter(prefix="/api/admin", tags=["Admin"])

_RESERVED_TEMPLATE_NAMES = {
    "IEEE-conference-template-062824",
    "LaTeX2e_Proceedings_Templates_download__1",
    "LaTeX2e_Proceedings_Templates_download__1_",
    "samplepaper_springer_",
    "samplepaper_springer",
    "samplepaper",
    "latex_template_onecolumn",
    "elsarticle-template-harv",
    "elsarticle-template-num",
    "IEEEtran",
    "llncs",
}
_USERS_TEMPLATE_DIRNAME = "users"
_GLOBAL_TEMPLATE_PREFIX = "custom_global_"
_PRIVATE_TEMPLATE_PREFIX = "custom_user_"


class YeuCauCapNhatVaiTro(BaseModel):
    role: str


class YeuCauCapNhatPremium(BaseModel):
    enabled: bool
    so_ngay: int = 30


class YeuCauDieuChinhToken(BaseModel):
    amount: int
    reason: str | None = None


class YeuCauCapNhatCauHinhHeThong(BaseModel):
    token_min_cost_vnd: int | None = None
    free_plan_max_pages: int | None = None
    max_doc_upload_mb: int | None = None
    rate_limit_admin_per_minute: int | None = None


def _ghi_audit_admin(
    db: Session,
    actor_user_id: int,
    action: str,
    request: Request,
    target_user_id: int | None = None,
    target_record_id: str | None = None,
    detail: str | None = None,
) -> None:
    db.add(
        models.AdminAuditLog(
            actor_user_id=actor_user_id,
            action=action,
            target_user_id=target_user_id,
            target_record_id=target_record_id,
            detail=detail,
            request_id=getattr(request.state, "request_id", None),
            ip_address=request.client.host if request.client else None,
        )
    )


@router.get("/system-config")
def lay_cau_hinh_he_thong_admin(
    _: models.User = Depends(auth.yeu_cau_quyen_admin),
) -> dict:
    return lay_cau_hinh_he_thong()


@router.patch("/system-config")
def cap_nhat_cau_hinh_he_thong_admin(
    req: YeuCauCapNhatCauHinhHeThong,
    request: Request,
    db: Session = Depends(lay_db),
    current_admin: models.User = Depends(auth.yeu_cau_quyen_admin),
) -> dict:
    payload = req.model_dump(exclude_none=True)
    if not payload:
        raise HTTPException(status_code=400, detail="Khong co gia tri cau hinh de cap nhat")

    ranges = {
        "token_min_cost_vnd": (1, 1_000_000),
        "free_plan_max_pages": (1, 1_000_000),
        "max_doc_upload_mb": (1, 1024),
        "rate_limit_admin_per_minute": (10, 5000),
    }

    for key, value in payload.items():
        min_val, max_val = ranges[key]
        if not isinstance(value, int):
            raise HTTPException(status_code=400, detail=f"{key} phai la so nguyen")
        if value < min_val or value > max_val:
            raise HTTPException(status_code=400, detail=f"{key} phai trong khoang [{min_val}, {max_val}]")

    result = cap_nhat_cau_hinh_he_thong(payload)
    _ghi_audit_admin(
        db=db,
        actor_user_id=current_admin.id,
        action="admin.update_system_config",
        request=request,
        detail=";".join(f"{k}={v}" for k, v in payload.items()),
    )
    db.commit()
    return result


@router.get("/overview")
def lay_tong_quan(
    db: Session = Depends(lay_db),
    _: models.User = Depends(auth.yeu_cau_quyen_admin),
) -> dict:
    tong_nguoi_dung = db.query(models.User).count()
    tong_admin = db.query(models.User).filter(models.User.role == "admin").count()
    tong_premium = db.query(models.User).filter(models.User.plan_type == "premium").count()
    tong_ban_ghi = db.query(models.ConversionHistory).count()
    return {
        "tong_nguoi_dung": tong_nguoi_dung,
        "tong_admin": tong_admin,
        "tong_premium": tong_premium,
        "tong_ban_ghi_lich_su": tong_ban_ghi,
    }


@router.get("/users")
def lay_danh_sach_nguoi_dung(
    db: Session = Depends(lay_db),
    _: models.User = Depends(auth.yeu_cau_quyen_admin),
) -> dict:
    users = db.query(models.User).order_by(models.User.created_at.desc()).all()
    return {
        "danh_sach": [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "role": u.role,
                "plan_type": u.plan_type,
                "token_balance": u.token_balance,
                "premium_started_at": u.premium_started_at.isoformat() if u.premium_started_at else None,
                "premium_expires_at": u.premium_expires_at.isoformat() if u.premium_expires_at else None,
                "auth_provider": u.auth_provider,
                "created_at": u.created_at.isoformat() if u.created_at else None,
                "so_lan_chuyen_doi": db.query(models.ConversionHistory)
                .filter(models.ConversionHistory.user_id == u.id)
                .count(),
            }
            for u in users
        ]
    }


@router.patch("/users/{user_id}/role")
def cap_nhat_vai_tro_nguoi_dung(
    user_id: int,
    req: YeuCauCapNhatVaiTro,
    request: Request,
    db: Session = Depends(lay_db),
    current_admin: models.User = Depends(auth.yeu_cau_quyen_admin),
) -> dict:
    role_moi = (req.role or "").strip().lower()
    if role_moi not in {"admin", "user"}:
        raise HTTPException(status_code=400, detail="Role chỉ chấp nhận 'admin' hoặc 'user'")

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")

    if user.id == current_admin.id and role_moi != "admin":
        raise HTTPException(status_code=400, detail="Không thể tự hạ quyền admin của chính mình")

    role_cu = user.role
    user.role = role_moi
    _ghi_audit_admin(
        db=db,
        actor_user_id=current_admin.id,
        action="admin.update_role",
        request=request,
        target_user_id=user.id,
        detail=f"from={role_cu};to={role_moi}",
    )
    db.commit()
    db.refresh(user)
    return {
        "thanh_cong": True,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
        },
    }


@router.patch("/users/{user_id}/premium")
def cap_nhat_premium_nguoi_dung(
    user_id: int,
    req: YeuCauCapNhatPremium,
    request: Request,
    db: Session = Depends(lay_db),
    current_admin: models.User = Depends(auth.yeu_cau_quyen_admin),
) -> dict:
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")

    if req.enabled:
        so_ngay = max(1, req.so_ngay)
        now = datetime.utcnow()
        user.plan_type = "premium"
        user.premium_started_at = now
        user.premium_expires_at = now + timedelta(days=so_ngay)
        if user.token_balance < 25000:
            user.token_balance = 25000
    else:
        user.plan_type = "free"
        user.premium_expires_at = None

    _ghi_audit_admin(
        db=db,
        actor_user_id=current_admin.id,
        action="admin.update_premium",
        request=request,
        target_user_id=user.id,
        detail=f"enabled={req.enabled};days={req.so_ngay}",
    )

    db.commit()
    db.refresh(user)
    return {
        "thanh_cong": True,
        "user": {
            "id": user.id,
            "plan_type": user.plan_type,
            "token_balance": user.token_balance,
            "premium_started_at": user.premium_started_at.isoformat() if user.premium_started_at else None,
            "premium_expires_at": user.premium_expires_at.isoformat() if user.premium_expires_at else None,
        },
    }


@router.post("/users/{user_id}/token/grant")
def cong_token_nguoi_dung(
    user_id: int,
    req: YeuCauDieuChinhToken,
    request: Request,
    db: Session = Depends(lay_db),
    current_admin: models.User = Depends(auth.yeu_cau_quyen_admin),
) -> dict:
    amount = max(0, req.amount)
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Số token cộng phải lớn hơn 0")

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")

    user.token_balance += amount
    db.add(
        models.TokenLedger(
            user_id=user.id,
            delta_token=amount,
            balance_after=user.token_balance,
            reason="admin_grant",
            meta_json=req.reason or "",
        )
    )
    _ghi_audit_admin(
        db=db,
        actor_user_id=current_admin.id,
        action="admin.token_grant",
        request=request,
        target_user_id=user.id,
        detail=f"amount={amount};reason={req.reason or ''}",
    )
    db.commit()
    db.refresh(user)
    return {"thanh_cong": True, "token_balance": user.token_balance}


@router.post("/users/{user_id}/token/deduct")
def tru_token_nguoi_dung(
    user_id: int,
    req: YeuCauDieuChinhToken,
    request: Request,
    db: Session = Depends(lay_db),
    current_admin: models.User = Depends(auth.yeu_cau_quyen_admin),
) -> dict:
    amount = max(0, req.amount)
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Số token trừ phải lớn hơn 0")

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")
    if user.token_balance < amount:
        raise HTTPException(status_code=400, detail="Số dư token không đủ để trừ")

    user.token_balance -= amount
    db.add(
        models.TokenLedger(
            user_id=user.id,
            delta_token=-amount,
            balance_after=user.token_balance,
            reason="admin_deduct",
            meta_json=req.reason or "",
        )
    )
    _ghi_audit_admin(
        db=db,
        actor_user_id=current_admin.id,
        action="admin.token_deduct",
        request=request,
        target_user_id=user.id,
        detail=f"amount={amount};reason={req.reason or ''}",
    )
    db.commit()
    db.refresh(user)
    return {"thanh_cong": True, "token_balance": user.token_balance}


@router.get("/users/{user_id}/history")
def lay_lich_su_theo_nguoi_dung(
    user_id: int,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(lay_db),
    _: models.User = Depends(auth.yeu_cau_quyen_admin),
) -> dict:
    records = (
        db.query(models.ConversionHistory)
        .filter(models.ConversionHistory.user_id == user_id)
        .order_by(models.ConversionHistory.created_at.desc())
        .limit(limit)
        .all()
    )
    return {
        "danh_sach": [
            {
                "id": r.id,
                "job_id": r.job_id,
                "file_name": r.file_name,
                "status": r.status,
                "pages_count": r.pages_count,
                "token_cost": r.token_cost,
                "token_refunded": r.token_refunded,
                "error_type": r.error_type,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in records
        ]
    }


@router.get("/users/{user_id}/token-ledger")
def lay_token_ledger_theo_nguoi_dung(
    user_id: int,
    limit: int = Query(200, ge=1, le=1000),
    db: Session = Depends(lay_db),
    _: models.User = Depends(auth.yeu_cau_quyen_admin),
) -> dict:
    records = (
        db.query(models.TokenLedger)
        .filter(models.TokenLedger.user_id == user_id)
        .order_by(models.TokenLedger.created_at.desc())
        .limit(limit)
        .all()
    )
    return {
        "danh_sach": [
            {
                "id": r.id,
                "delta_token": r.delta_token,
                "balance_after": r.balance_after,
                "reason": r.reason,
                "job_id": r.job_id,
                "meta_json": r.meta_json,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in records
        ]
    }


@router.get("/audit-logs")
def lay_audit_logs_admin(
    limit: int = Query(200, ge=1, le=1000),
    db: Session = Depends(lay_db),
    _: models.User = Depends(auth.yeu_cau_quyen_admin),
) -> dict:
    rows = (
        db.query(models.AdminAuditLog)
        .order_by(models.AdminAuditLog.created_at.desc())
        .limit(limit)
        .all()
    )
    return {
        "danh_sach": [
            {
                "id": r.id,
                "actor_user_id": r.actor_user_id,
                "action": r.action,
                "target_user_id": r.target_user_id,
                "target_record_id": r.target_record_id,
                "detail": r.detail,
                "request_id": r.request_id,
                "ip_address": r.ip_address,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]
    }


@router.delete("/users/{user_id}")
def xoa_nguoi_dung(
    user_id: int,
    request: Request,
    db: Session = Depends(lay_db),
    current_admin: models.User = Depends(auth.yeu_cau_quyen_admin),
) -> dict:
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")

    if user.id == current_admin.id:
        raise HTTPException(status_code=400, detail="Không thể tự xóa tài khoản admin hiện tại")

    db.query(models.ConversionHistory).filter(models.ConversionHistory.user_id == user.id).delete()
    db.query(models.TokenLedger).filter(models.TokenLedger.user_id == user.id).delete()
    _ghi_audit_admin(
        db=db,
        actor_user_id=current_admin.id,
        action="admin.delete_user",
        request=request,
        target_user_id=user.id,
        detail=f"email={user.email}",
    )
    db.delete(user)
    db.commit()
    return {"thanh_cong": True}


@router.get("/history")
def lay_lich_su_toan_he_thong(
    limit: int = Query(200, ge=1, le=1000),
    db: Session = Depends(lay_db),
    _: models.User = Depends(auth.yeu_cau_quyen_admin),
) -> dict:
    records = (
        db.query(models.ConversionHistory)
        .order_by(models.ConversionHistory.created_at.desc())
        .limit(limit)
        .all()
    )

    users = {
        u.id: u
        for u in db.query(models.User).filter(models.User.id.in_([r.user_id for r in records])).all()
    }

    return {
        "danh_sach": [
            {
                "id": r.id,
                "user_id": r.user_id,
                "username": users.get(r.user_id).username if users.get(r.user_id) else None,
                "email": users.get(r.user_id).email if users.get(r.user_id) else None,
                "job_id": r.job_id,
                "file_name": r.file_name,
                "template_name": r.template_name,
                "status": r.status,
                "file_path": r.file_path,
                "pages_count": r.pages_count,
                "token_cost": r.token_cost,
                "token_refunded": r.token_refunded,
                "error_type": r.error_type,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in records
        ]
    }


@router.delete("/history/{record_id}")
def xoa_ban_ghi_lich_su(
    record_id: int,
    request: Request,
    db: Session = Depends(lay_db),
    current_admin: models.User = Depends(auth.yeu_cau_quyen_admin),
) -> dict:
    record = db.query(models.ConversionHistory).filter(models.ConversionHistory.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Không tìm thấy bản ghi")

    _ghi_audit_admin(
        db=db,
        actor_user_id=current_admin.id,
        action="admin.delete_history",
        request=request,
        target_user_id=record.user_id,
        target_record_id=str(record.id),
        detail=f"job_id={record.job_id}",
    )
    db.delete(record)
    db.commit()
    return {"thanh_cong": True}


@router.get("/templates")
def lay_danh_sach_template_admin(
    db: Session = Depends(lay_db),
    _: models.User = Depends(auth.yeu_cau_quyen_admin),
) -> dict:
    danh_sach = []
    users_map = {
        u.id: u
        for u in db.query(models.User).all()
    }

    users_root = CUSTOM_TEMPLATE_FOLDER / _USERS_TEMPLATE_DIRNAME
    for item in CUSTOM_TEMPLATE_FOLDER.iterdir():
        if item.name == _USERS_TEMPLATE_DIRNAME:
            continue
        if item.name in _RESERVED_TEMPLATE_NAMES or item.stem in _RESERVED_TEMPLATE_NAMES:
            continue
        if item.name.startswith('.'):
            continue
        if item.is_file() and item.suffix.lower() == '.tex':
            danh_sach.append(
                {
                    "id": f"{_GLOBAL_TEMPLATE_PREFIX}{item.stem}",
                    "scope": "global",
                    "ten": item.stem,
                    "duong_dan": str(item),
                    "loai": "file",
                    "kich_thuoc": item.stat().st_size,
                }
            )
        elif item.is_dir():
            kich_thuoc = sum(f.stat().st_size for f in item.rglob('*') if f.is_file())
            danh_sach.append(
                {
                    "id": f"{_GLOBAL_TEMPLATE_PREFIX}{item.name}",
                    "scope": "global",
                    "ten": item.name,
                    "duong_dan": str(item),
                    "loai": "folder",
                    "kich_thuoc": kich_thuoc,
                }
            )

    if users_root.exists() and users_root.is_dir():
        for user_dir in users_root.iterdir():
            if not user_dir.is_dir() or not user_dir.name.startswith("u_"):
                continue
            user_id_raw = user_dir.name.replace("u_", "", 1)
            if not user_id_raw.isdigit():
                continue
            owner_user_id = int(user_id_raw)
            owner = users_map.get(owner_user_id)
            owner_label = owner.email if owner else f"user#{owner_user_id}"

            for item in user_dir.iterdir():
                if item.is_file() and item.suffix.lower() == '.tex':
                    danh_sach.append(
                        {
                            "id": f"{_PRIVATE_TEMPLATE_PREFIX}{owner_user_id}_{item.stem}",
                            "scope": "private",
                            "owner_user_id": owner_user_id,
                            "owner_label": owner_label,
                            "ten": item.stem,
                            "duong_dan": str(item),
                            "loai": "file",
                            "kich_thuoc": item.stat().st_size,
                        }
                    )
                elif item.is_dir():
                    kich_thuoc = sum(f.stat().st_size for f in item.rglob('*') if f.is_file())
                    danh_sach.append(
                        {
                            "id": f"{_PRIVATE_TEMPLATE_PREFIX}{owner_user_id}_{item.name}",
                            "scope": "private",
                            "owner_user_id": owner_user_id,
                            "owner_label": owner_label,
                            "ten": item.name,
                            "duong_dan": str(item),
                            "loai": "folder",
                            "kich_thuoc": kich_thuoc,
                        }
                    )

    danh_sach.sort(key=lambda x: x["ten"].lower())
    return {"danh_sach": danh_sach}


@router.delete("/templates/{template_id}")
def xoa_template_admin(
    template_id: str,
    request: Request,
    db: Session = Depends(lay_db),
    current_admin: models.User = Depends(auth.yeu_cau_quyen_admin),
) -> dict:
    if template_id.startswith(_PRIVATE_TEMPLATE_PREFIX):
        payload = template_id[len(_PRIVATE_TEMPLATE_PREFIX):]
        owner_part, sep, name = payload.partition("_")
        if not sep or not owner_part.isdigit() or not name:
            raise HTTPException(status_code=400, detail="Template private không hợp lệ")
        owner_user_id = int(owner_part)
        user_root = CUSTOM_TEMPLATE_FOLDER / _USERS_TEMPLATE_DIRNAME / f"u_{owner_user_id}"
        file_path = user_root / f"{name}.tex"
        dir_path = user_root / name
    else:
        if template_id.startswith(_GLOBAL_TEMPLATE_PREFIX):
            name = template_id[len(_GLOBAL_TEMPLATE_PREFIX):]
        elif template_id.startswith("custom_"):
            # backward-compat id
            name = template_id.replace("custom_", "", 1)
        else:
            raise HTTPException(status_code=400, detail="Không thể xóa template mặc định")

        if name in _RESERVED_TEMPLATE_NAMES:
            raise HTTPException(status_code=400, detail="Không thể xóa template mặc định")

        file_path = CUSTOM_TEMPLATE_FOLDER / f"{name}.tex"
        dir_path = CUSTOM_TEMPLATE_FOLDER / name

    if file_path.exists():
        file_path.unlink()
    elif dir_path.exists() and dir_path.is_dir():
        shutil.rmtree(dir_path, ignore_errors=True)
    else:
        raise HTTPException(status_code=404, detail="Template không tồn tại")

    _ghi_audit_admin(
        db=db,
        actor_user_id=current_admin.id,
        action="admin.delete_template",
        request=request,
        target_record_id=template_id,
        detail=f"name={name}",
    )
    db.commit()

    return {"thanh_cong": True}


# ── ADMIN PAYMENT MANAGEMENT ──────────────────────────────────────────────────


@router.get("/payments")
def lay_danh_sach_payments_admin(
    limit: int = Query(200, ge=1, le=1000),
    db: Session = Depends(lay_db),
    _: models.User = Depends(auth.yeu_cau_quyen_admin),
) -> dict:
    """Liệt kê tất cả payments trong hệ thống (admin only)."""
    records = (
        db.query(models.Payment)
        .order_by(models.Payment.created_at.desc())
        .limit(limit)
        .all()
    )

    users = {
        u.id: u
        for u in db.query(models.User)
        .filter(models.User.id.in_([r.user_id for r in records]))
        .all()
    }

    return {
        "danh_sach": [
            {
                "id": r.id,
                "user_id": r.user_id,
                "username": users.get(r.user_id).username if users.get(r.user_id) else None,
                "email": users.get(r.user_id).email if users.get(r.user_id) else None,
                "amount_vnd": r.amount_vnd,
                "token_amount": r.token_amount,
                "status": r.status,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "updated_at": r.updated_at.isoformat() if r.updated_at else None,
            }
            for r in records
        ]
    }


@router.patch("/payments/{payment_id}/complete")
def xac_nhan_payment_thu_cong_admin(
    payment_id: int,
    request: Request,
    db: Session = Depends(lay_db),
    current_admin: models.User = Depends(auth.yeu_cau_quyen_admin),
) -> dict:
    """Admin xác nhận payment thủ công (khi khách chuyển sai nội dung / SePay không match)."""
    payment = db.query(models.Payment).filter(models.Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Không tìm thấy hóa đơn")

    if payment.status == "completed":
        return {"thanh_cong": True, "status": "completed", "thong_bao": "Hóa đơn đã hoàn thành trước đó"}

    # Cập nhật payment → completed
    payment.status = "completed"
    payment.updated_at = datetime.utcnow()

    # Cộng token cho user
    user = db.query(models.User).filter(models.User.id == payment.user_id).first()
    if user:
        user.token_balance += payment.token_amount
        db.add(
            models.TokenLedger(
                user_id=user.id,
                delta_token=payment.token_amount,
                balance_after=user.token_balance,
                reason="admin_confirm_payment",
                meta_json=f"payment_id={payment.id}",
            )
        )

    _ghi_audit_admin(
        db=db,
        actor_user_id=current_admin.id,
        action="admin.confirm_payment",
        request=request,
        target_user_id=payment.user_id,
        target_record_id=str(payment.id),
        detail=f"amount_vnd={payment.amount_vnd};token={payment.token_amount}",
    )
    db.commit()
    return {
        "thanh_cong": True,
        "status": "completed",
        "token_nhan": payment.token_amount,
    }
