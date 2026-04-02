"""Base/system routes such as health checks."""

from datetime import datetime

from fastapi import APIRouter

router = APIRouter(tags=["Base"])


@router.get("/")
def doc_api() -> dict:
    """Return root API metadata and quick navigation links."""
    return {
        "message": "Word2LaTeX API đang hoạt động",
        "endpoints": {
            "/api/chuyen-doi": "POST - Upload file .docx/.docm và chuyển đổi",
            "/docs": "Xem Swagger documentation",
        },
    }


@router.get("/health")
def kiem_tra_suc_khoe() -> dict:
    """Return service health probe payload."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
    }
