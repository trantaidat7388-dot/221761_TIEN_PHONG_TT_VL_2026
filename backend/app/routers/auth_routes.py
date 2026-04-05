"""
auth_routes.py
Định nghĩa các API liên quan đến xác thực người dùng và tra cứu lịch sử chuyển đổi.
"""

import json
import os
from datetime import datetime, timedelta
from urllib import parse, request as urlrequest

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .. import models
from .. import auth
from ..database import lay_db
from ..config import (
    FRONTEND_URL,
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URI,
)

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


def _serialize_user(user: models.User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "plan_type": user.plan_type,
        "token_balance": user.token_balance,
        "premium_started_at": user.premium_started_at.isoformat() if user.premium_started_at else None,
        "premium_expires_at": user.premium_expires_at.isoformat() if user.premium_expires_at else None,
        "auth_provider": user.auth_provider,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


def _tao_auth_payload(user: models.User) -> dict:
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


def _dong_bo_tai_khoan_google(db: Session, google_sub: str, google_email: str, google_name: str) -> models.User:
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

    return user


def _lay_google_user_info_tu_authorization_code(code: str) -> dict:
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="Thiếu GOOGLE_CLIENT_ID hoặc GOOGLE_CLIENT_SECRET")

    token_payload = parse.urlencode(
        {
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        }
    ).encode("utf-8")

    try:
        token_req = urlrequest.Request(
            "https://oauth2.googleapis.com/token",
            data=token_payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        with urlrequest.urlopen(token_req, timeout=10) as resp:
            token_data = json.loads(resp.read().decode("utf-8", errors="ignore"))
    except Exception:
        raise HTTPException(status_code=401, detail="Không thể đổi authorization code từ Google")

    access_token = (token_data.get("access_token") or "").strip()
    if not access_token:
        raise HTTPException(status_code=401, detail="Google không trả về access_token")

    try:
        userinfo_req = urlrequest.Request(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
            method="GET",
        )
        with urlrequest.urlopen(userinfo_req, timeout=10) as resp:
            info = json.loads(resp.read().decode("utf-8", errors="ignore"))
    except Exception:
        raise HTTPException(status_code=401, detail="Không thể lấy thông tin user từ Google")

    google_email = (info.get("email") or "").strip().lower()
    google_sub = (info.get("sub") or "").strip()
    email_verified = bool(info.get("email_verified"))
    google_name = (info.get("name") or "").strip()

    if not google_sub or not google_email:
        raise HTTPException(status_code=401, detail="Google userinfo thiếu thông tin định danh")
    if not email_verified:
        raise HTTPException(status_code=401, detail="Email Google chưa được xác minh")

    return {"sub": google_sub, "email": google_email, "name": google_name}

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

    user = _dong_bo_tai_khoan_google(db, google_sub, google_email, google_name)
    return _tao_auth_payload(user)


@router.get("/auth/google/login")
def dang_nhap_google_redirect() -> RedirectResponse:
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Thiếu cấu hình GOOGLE_CLIENT_ID")

    query = parse.urlencode(
        {
            "client_id": GOOGLE_CLIENT_ID,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "online",
            "prompt": "select_account",
        }
    )
    return RedirectResponse(url=f"https://accounts.google.com/o/oauth2/v2/auth?{query}")


@router.get("/auth/google/callback")
def google_callback(code: str, request: Request, db: Session = Depends(lay_db)) -> RedirectResponse:
    _ = request  # reserved for future state validation / audit logging.
    google_info = _lay_google_user_info_tu_authorization_code(code)
    user = _dong_bo_tai_khoan_google(db, google_info["sub"], google_info["email"], google_info["name"])

    payload = _tao_auth_payload(user)
    token = payload["access_token"]
    return RedirectResponse(url=f"{FRONTEND_URL.rstrip('/')}/dang-nhap?token={parse.quote(token)}")

@router.get("/auth/me")
def lay_thong_tin_ban_than(current_user: models.User = Depends(auth.lay_nguoi_dung_hien_tai)) -> dict:
    """Trả về thông tin người dùng đang đăng nhập dựa trên JWT token."""
    return _serialize_user(current_user)


@router.get("/premium/options")
def lay_goi_premium(current_user: models.User = Depends(auth.lay_nguoi_dung_hien_tai)) -> dict:
    from ..config import PREMIUM_PACKAGES
    return {
        "danh_sach_goi": PREMIUM_PACKAGES,
        "nguoi_dung": {
            "id": current_user.id,
            "plan_type": current_user.plan_type,
            "token_balance": current_user.token_balance,
            "premium_expires_at": current_user.premium_expires_at.isoformat() if current_user.premium_expires_at else None,
        },
    }


class YeuCauDangKyPremium(BaseModel):
    plan_key: str

@router.post("/premium/subscribe")
def dang_ky_goi_premium(
    req: YeuCauDangKyPremium,
    db: Session = Depends(lay_db),
    current_user: models.User = Depends(auth.lay_nguoi_dung_hien_tai),
) -> dict:
    from ..config import PREMIUM_PACKAGES
    
    plan = PREMIUM_PACKAGES.get(req.plan_key)
    if not plan:
        raise HTTPException(status_code=400, detail="Gói Premium không hợp lệ")

    now = datetime.utcnow()
    
    # Cho phép cộng dồn ngày nếu đang có Premium
    if current_user.plan_type == "premium" and current_user.premium_expires_at and current_user.premium_expires_at > now:
        base_time = current_user.premium_expires_at
    else:
        base_time = now

    token_cost = plan.get("token_cost", 0)
    so_ngay = plan.get("so_ngay", 30)

    if current_user.token_balance < token_cost:
        raise HTTPException(
            status_code=400,
            detail=f"Không đủ token để đăng ký. Cần {token_cost} token",
        )

    current_user.token_balance -= token_cost
    current_user.plan_type = "premium"
    if current_user.premium_expires_at is None or current_user.premium_expires_at < now:
        current_user.premium_started_at = now
    current_user.premium_expires_at = base_time + timedelta(days=so_ngay)

    db.add(
        models.TokenLedger(
            user_id=current_user.id,
            delta_token=-token_cost,
            balance_after=current_user.token_balance,
            reason="premium_subscribe",
            meta_json=f"plan={req.plan_key},days={so_ngay}",
        )
    )
    db.commit()
    db.refresh(current_user)

    return {
        "thanh_cong": True,
        "thong_bao": f"Đăng ký thành công {plan['name']}",
        "goi": {
            "so_ngay": so_ngay,
            "token_cost": token_cost,
        },
        "user": _serialize_user(current_user),
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

    la_tai_khoan_google = (current_user.auth_provider or "").strip().lower() == "google"

    if la_tai_khoan_google and req.new_password is not None:
        raise HTTPException(status_code=400, detail="Tài khoản Google không hỗ trợ đổi mật khẩu tại đây")

    can_xac_nhan_mat_khau = not la_tai_khoan_google

    if can_xac_nhan_mat_khau and not req.current_password:
        raise HTTPException(status_code=400, detail="Vui lòng nhập mật khẩu hiện tại để xác nhận")

    if can_xac_nhan_mat_khau and not auth.xac_minh_mat_khau(req.current_password, current_user.hashed_password):
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
        "user": _serialize_user(current_user),
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
