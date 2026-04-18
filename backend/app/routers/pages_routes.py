from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel

from .. import models, auth
from ..database import lay_db
from .admin_routes import _ghi_audit_admin

router = APIRouter()

# Schema
class CustomPageCreate(BaseModel):
    slug: str
    title: str
    content_html: str = ""
    css_variables: str = "{}"
    is_published: bool = False

class CustomPageUpdate(BaseModel):
    title: str | None = None
    content_html: str | None = None
    css_variables: str | None = None
    is_published: bool | None = None

# PUBLIC endpoints
@router.get("/api/pages/{slug}", tags=["Pages"])
def lay_noi_dung_trang(slug: str, db: Session = Depends(lay_db)):
    page = db.query(models.CustomPage).filter(models.CustomPage.slug == slug).first()
    if not page or not page.is_published:
        raise HTTPException(status_code=404, detail="Không tìm thấy trang hoặc trang chưa được công khai")
    return {
        "slug": page.slug,
        "title": page.title,
        "content_html": page.content_html,
        "css_variables": page.css_variables,
        "created_at": page.created_at.isoformat(),
        "updated_at": page.updated_at.isoformat()
    }

# ADMIN endpoints
@router.get("/api/admin/pages", tags=["Admin Pages"])
def lay_danh_sach_trang_admin(
    db: Session = Depends(lay_db),
    current_admin: models.User = Depends(auth.yeu_cau_quyen_admin)
):
    pages = db.query(models.CustomPage).order_by(models.CustomPage.created_at.desc()).all()
    return {
        "danh_sach": [
            {
                "id": p.id,
                "slug": p.slug,
                "title": p.title,
                "is_published": p.is_published,
                "created_at": p.created_at.isoformat(),
                "updated_at": p.updated_at.isoformat()
            } for p in pages
        ]
    }

@router.get("/api/admin/pages/{slug}", tags=["Admin Pages"])
def lay_chi_tiet_trang_admin(
    slug: str,
    db: Session = Depends(lay_db),
    current_admin: models.User = Depends(auth.yeu_cau_quyen_admin)
):
    page = db.query(models.CustomPage).filter(models.CustomPage.slug == slug).first()
    if not page:
        raise HTTPException(status_code=404, detail="Không tìm thấy trang")
    return {
        "id": page.id,
        "slug": page.slug,
        "title": page.title,
        "content_html": page.content_html,
        "css_variables": page.css_variables,
        "is_published": page.is_published,
        "created_at": page.created_at.isoformat(),
        "updated_at": page.updated_at.isoformat()
    }

@router.post("/api/admin/pages", tags=["Admin Pages"])
def tao_trang_moi_admin(
    req: CustomPageCreate,
    request: Request,
    db: Session = Depends(lay_db),
    current_admin: models.User = Depends(auth.yeu_cau_quyen_admin)
):
    existing = db.query(models.CustomPage).filter(models.CustomPage.slug == req.slug).first()
    if existing:
        raise HTTPException(status_code=400, detail="Slug đã tồn tại. Vui lòng chọn đường dẫn khác.")
    
    new_page = models.CustomPage(
        slug=req.slug,
        title=req.title,
        content_html=req.content_html,
        css_variables=req.css_variables,
        is_published=req.is_published
    )
    db.add(new_page)
    _ghi_audit_admin(
        db=db,
        actor_user_id=current_admin.id,
        action="admin.create_page",
        request=request,
        detail=f"slug={req.slug}",
    )
    db.commit()
    db.refresh(new_page)
    return {"thanh_cong": True, "id": new_page.id, "slug": new_page.slug}

@router.patch("/api/admin/pages/{slug}", tags=["Admin Pages"])
def cap_nhat_trang_admin(
    slug: str,
    req: CustomPageUpdate,
    request: Request,
    db: Session = Depends(lay_db),
    current_admin: models.User = Depends(auth.yeu_cau_quyen_admin)
):
    page = db.query(models.CustomPage).filter(models.CustomPage.slug == slug).first()
    if not page:
        raise HTTPException(status_code=404, detail="Không tìm thấy trang")
    
    if req.title is not None:
        page.title = req.title
    if req.content_html is not None:
        page.content_html = req.content_html
    if req.css_variables is not None:
        page.css_variables = req.css_variables
    if req.is_published is not None:
        page.is_published = req.is_published

    _ghi_audit_admin(
        db=db,
        actor_user_id=current_admin.id,
        action="admin.update_page",
        request=request,
        target_record_id=str(page.id),
        detail=f"slug={slug}",
    )
    db.commit()
    db.refresh(page)
    return {"thanh_cong": True, "slug": page.slug}

@router.delete("/api/admin/pages/{slug}", tags=["Admin Pages"])
def xoa_trang_admin(
    slug: str,
    request: Request,
    db: Session = Depends(lay_db),
    current_admin: models.User = Depends(auth.yeu_cau_quyen_admin)
):
    page = db.query(models.CustomPage).filter(models.CustomPage.slug == slug).first()
    if not page:
        raise HTTPException(status_code=404, detail="Không tìm thấy trang")
    
    _ghi_audit_admin(
        db=db,
        actor_user_id=current_admin.id,
        action="admin.delete_page",
        request=request,
        target_record_id=str(page.id),
        detail=f"slug={slug}",
    )
    db.delete(page)
    db.commit()
    return {"thanh_cong": True}
