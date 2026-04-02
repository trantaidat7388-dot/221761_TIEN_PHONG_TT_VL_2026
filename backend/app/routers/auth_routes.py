"""
auth_routes.py
Định nghĩa các API liên quan đến xác thực người dùng và tra cứu lịch sử chuyển đổi.
"""

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

@router.post("/auth/register")
def dang_ky(req: YeuCauDangKy, db: Session = Depends(lay_db)):
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
        hashed_password=auth.bam_mat_khau(req.password)
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
            "email": user.email
        }
    }

@router.post("/auth/login")
def dang_nhap(req: YeuCauDangNhap, db: Session = Depends(lay_db)):
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
            "email": user.email
        }
    }

@router.get("/auth/me")
def lay_thong_tin_ban_than(current_user: models.User = Depends(auth.lay_nguoi_dung_hien_tai)):
    """Trả về thông tin người dùng đang đăng nhập dựa trên JWT token."""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "created_at": current_user.created_at.isoformat()
    }


# ── HISTORY ENDPOINTS ───────────────────────────────────────────────────

@router.get("/history")
def lay_lich_su(db: Session = Depends(lay_db), current_user: models.User = Depends(auth.lay_nguoi_dung_hien_tai)):
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
def xoa_lich_su(record_id: int, db: Session = Depends(lay_db), current_user: models.User = Depends(auth.lay_nguoi_dung_hien_tai)):
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
