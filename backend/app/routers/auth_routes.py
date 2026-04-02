"""
auth_routes.py
Định nghĩa các API liên quan đến xác thực người dùng và tra cứu lịch sử chuyển đổi.
"""

import json
import os
from urllib import parse, request as urlrequest

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .. import models
from .. import auth
from ..database import lay_db

router = APIRouter(prefix="/api", tags=["Auth & History"])

class YeuCauDangKy(BaseModel):
    username: str
    email: str
    password: str

class YeuCauDangNhap(BaseModel):
    email: str
    password: str


class YeuCauDangNhapGoogle(BaseModel):
    id_token: str


class YeuCauCapNhatTaiKhoan(BaseModel):
    username: str | None = None
    email: str | None = None
    current_password: str | None = None
    new_password: str | None = None


def _xac_thuc_google_id_token(id_token: str) -> dict:
    if not id_token:
        raise HTTPException(status_code=400, detail="Thiếu Google id_token")

    token_info_url = f"https://oauth2.googleapis.com/tokeninfo?{parse.urlencode({'id_token': id_token})}"
    try:
        with urlrequest.urlopen(token_info_url, timeout=8) as resp:
            payload = json.loads(resp.read().decode("utf-8", errors="ignore"))
    except Exception:
        raise HTTPException(status_code=401, detail="Google token không hợp lệ hoặc đã hết hạn")

    google_email = (payload.get("email") or "").strip().lower()
    google_sub = (payload.get("sub") or "").strip()
    email_verified = str(payload.get("email_verified", "false")).lower() == "true"
    aud = (payload.get("aud") or "").strip()
    required_aud = os.getenv("GOOGLE_CLIENT_ID", "").strip()

    if required_aud and aud != required_aud:
        raise HTTPException(status_code=401, detail="Google token sai client_id")
    if not google_sub or not google_email:
        raise HTTPException(status_code=401, detail="Google token thiếu thông tin định danh")
    if not email_verified:
        raise HTTPException(status_code=401, detail="Email Google chưa được xác minh")

    return {
        "sub": google_sub,
        "email": google_email,
        "name": (payload.get("name") or "").strip(),
    }


def _tao_username_tu_google(db: Session, email: str, display_name: str = "") -> str:
    base = (display_name or email.split("@")[0] or "user").strip().lower()
    base = "".join(c if c.isalnum() or c in {"_", "-"} else "_" for c in base).strip("_") or "user"
    candidate = base
    counter = 1
    while db.query(models.User).filter(models.User.username == candidate).first():
        counter += 1
        candidate = f"{base}{counter}"
    return candidate

@router.post("/auth/register")
def dang_ky(req: YeuCauDangKy, db: Session = Depends(lay_db)) -> dict:
    """Tạo tài khoản mới, trả về JWT token."""
    if db.query(models.User).filter(models.User.email == req.email).first():
        raise HTTPException(status_code=400, detail="Email này đã được đăng ký")
    if db.query(models.User).filter(models.User.username == req.username).first():
        raise HTTPException(status_code=400, detail="Tên đăng nhập đã tồn tại")
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Mật khẩu phải có ít nhất 6 ký tự")

    user = models.User(
        username=req.username,
        email=req.email,
        hashed_password=auth.bam_mat_khau(req.password),
        role="user",
        plan_type="free",
        token_balance=5000,
        auth_provider="local",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = auth.tao_access_token({"sub": str(user.id)})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "plan_type": user.plan_type,
            "token_balance": user.token_balance,
            "premium_expires_at": user.premium_expires_at.isoformat() if user.premium_expires_at else None,
            "auth_provider": user.auth_provider,
        }
    }

@router.post("/auth/login")
def dang_nhap(req: YeuCauDangNhap, db: Session = Depends(lay_db)) -> dict:
    """Đăng nhập bằng email + mật khẩu, trả về JWT token."""
    user = db.query(models.User).filter(models.User.email == req.email).first()
    if not user or not auth.xac_minh_mat_khau(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Email hoặc mật khẩu không đúng")

    token = auth.tao_access_token({"sub": str(user.id)})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "plan_type": user.plan_type,
            "token_balance": user.token_balance,
            "premium_expires_at": user.premium_expires_at.isoformat() if user.premium_expires_at else None,
            "auth_provider": user.auth_provider,
        }
    }


@router.post("/auth/google")
def dang_nhap_voi_google(req: YeuCauDangNhapGoogle, db: Session = Depends(lay_db)) -> dict:
    google_info = _xac_thuc_google_id_token(req.id_token)
    google_sub = google_info["sub"]
    google_email = google_info["email"]
    google_name = google_info["name"]

    user = db.query(models.User).filter(models.User.google_id == google_sub).first()

    if user is None:
        user_by_email = db.query(models.User).filter(models.User.email == google_email).first()
        if user_by_email:
            user_by_email.google_id = google_sub
            user_by_email.auth_provider = "google"
            user = user_by_email
        else:
            user = models.User(
                username=_tao_username_tu_google(db, google_email, google_name),
                email=google_email,
                hashed_password=auth.bam_mat_khau(os.urandom(24).hex()),
                role="user",
                plan_type="free",
                token_balance=5000,
                auth_provider="google",
                google_id=google_sub,
            )
            db.add(user)

        db.commit()
        db.refresh(user)

    token = auth.tao_access_token({"sub": str(user.id)})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "plan_type": user.plan_type,
            "token_balance": user.token_balance,
            "premium_expires_at": user.premium_expires_at.isoformat() if user.premium_expires_at else None,
            "auth_provider": user.auth_provider,
        },
    }

@router.get("/auth/me")
def lay_thong_tin_ban_than(current_user: models.User = Depends(auth.lay_nguoi_dung_hien_tai)) -> dict:
    """Trả về thông tin người dùng đang đăng nhập dựa trên JWT token."""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role,
        "plan_type": current_user.plan_type,
        "token_balance": current_user.token_balance,
        "premium_started_at": current_user.premium_started_at.isoformat() if current_user.premium_started_at else None,
        "premium_expires_at": current_user.premium_expires_at.isoformat() if current_user.premium_expires_at else None,
        "auth_provider": current_user.auth_provider,
        "created_at": current_user.created_at.isoformat()
    }


@router.patch("/auth/me")
def cap_nhat_thong_tin_ban_than(
    req: YeuCauCapNhatTaiKhoan,
    db: Session = Depends(lay_db),
    current_user: models.User = Depends(auth.lay_nguoi_dung_hien_tai),
) -> dict:
    co_thay_doi = any(
        [
            req.username is not None,
            req.email is not None,
            req.new_password is not None,
        ]
    )
    if not co_thay_doi:
        raise HTTPException(status_code=400, detail="Không có thông tin nào để cập nhật")

    if not req.current_password:
        raise HTTPException(status_code=400, detail="Vui lòng nhập mật khẩu hiện tại để xác nhận")

    if not auth.xac_minh_mat_khau(req.current_password, current_user.hashed_password):
        raise HTTPException(status_code=401, detail="Mật khẩu hiện tại không đúng")

    if req.username is not None:
        username_moi = req.username.strip()
        if not username_moi:
            raise HTTPException(status_code=400, detail="Tên đăng nhập không được để trống")
        trung_username = (
            db.query(models.User)
            .filter(models.User.username == username_moi, models.User.id != current_user.id)
            .first()
        )
        if trung_username:
            raise HTTPException(status_code=400, detail="Tên đăng nhập đã tồn tại")
        current_user.username = username_moi

    if req.email is not None:
        email_moi = req.email.strip().lower()
        if not email_moi:
            raise HTTPException(status_code=400, detail="Email không được để trống")
        trung_email = (
            db.query(models.User)
            .filter(models.User.email == email_moi, models.User.id != current_user.id)
            .first()
        )
        if trung_email:
            raise HTTPException(status_code=400, detail="Email này đã được đăng ký")
        current_user.email = email_moi

    if req.new_password is not None:
        if len(req.new_password) < 6:
            raise HTTPException(status_code=400, detail="Mật khẩu mới phải có ít nhất 6 ký tự")
        current_user.hashed_password = auth.bam_mat_khau(req.new_password)

    db.commit()
    db.refresh(current_user)

    return {
        "thanh_cong": True,
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "role": current_user.role,
            "plan_type": current_user.plan_type,
            "token_balance": current_user.token_balance,
            "premium_started_at": current_user.premium_started_at.isoformat() if current_user.premium_started_at else None,
            "premium_expires_at": current_user.premium_expires_at.isoformat() if current_user.premium_expires_at else None,
            "auth_provider": current_user.auth_provider,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
        },
    }


# ── HISTORY ENDPOINTS ───────────────────────────────────────────────────

@router.get("/history")
def lay_lich_su(db: Session = Depends(lay_db), current_user: models.User = Depends(auth.lay_nguoi_dung_hien_tai)) -> dict:
    """Lấy lịch sử chuyển đổi của người dùng đang đăng nhập."""
    records = (
        db.query(models.ConversionHistory)
        .filter(models.ConversionHistory.user_id == current_user.id)
        .order_by(models.ConversionHistory.created_at.desc())
        .all()
    )
    return {
        "danhSach": [
            {
                "id": r.id,
                "job_id": r.job_id,
                "tenFileGoc": r.file_name,
                "templateName": r.template_name,
                "trangThai": r.status,
                "file_path": r.file_path,
                "thoiGian": r.created_at.isoformat()
            }
            for r in records
        ]
    }

@router.delete("/history/{record_id}")
def xoa_lich_su(record_id: int, db: Session = Depends(lay_db), current_user: models.User = Depends(auth.lay_nguoi_dung_hien_tai)) -> dict:
    """Xóa một bản ghi lịch sử (chỉ của người dùng hiện tại)."""
    record = db.query(models.ConversionHistory).filter(
        models.ConversionHistory.id == record_id,
        models.ConversionHistory.user_id == current_user.id
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Không tìm thấy bản ghi")
    db.delete(record)
    db.commit()
    return {"thanhCong": True}
