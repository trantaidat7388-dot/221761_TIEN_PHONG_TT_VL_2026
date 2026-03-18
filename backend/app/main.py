"""
main.py
Điểm khởi đầu (Khởi tạo FastAPI, CORS, gán Router).
"""

from datetime import datetime
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from . import database
from . import models
from .config import CORS_ALLOW_ALL, CORS_ORIGINS, TEMP_TTL_HOURS, OUTPUT_TTL_HOURS, TEMP_FOLDER, OUTPUTS_FOLDER
from .utils.api_utils import quet_xoa_thu_muc_mo_coi
from .routers import templates, chuyen_doi, auth_routes

# Khởi tạo FastAPI app
app = FastAPI(title="Word2LaTeX API", version="1.0.0")

# Khởi tạo database
models.Base.metadata.create_all(bind=database.engine)

# Cấu hình CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if CORS_ALLOW_ALL else CORS_ORIGINS,
    allow_credentials=not CORS_ALLOW_ALL,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gắn các routers
app.include_router(templates.router)
app.include_router(chuyen_doi.router)
app.include_router(auth_routes.router)

@app.on_event("startup")
def xu_ly_don_dep_khi_khoi_dong():
    """Startup hook: in route POST và dọn rác."""
    print("Registered POST routes:")
    for route in app.routes:
        if getattr(route, "methods", None) and "POST" in route.methods:
            print(f" - {route.path}")

    # Dọn dẹp các thư mục/file mồ côi trong temp khi server khởi động
    quet_xoa_thu_muc_mo_coi(TEMP_FOLDER, TEMP_TTL_HOURS)
    quet_xoa_thu_muc_mo_coi(OUTPUTS_FOLDER, OUTPUT_TTL_HOURS)

@app.get("/")
def doc_api():
    """Endpoint gốc - hướng dẫn sử dụng API."""
    return {
        "message": "Word2LaTeX API đang hoạt động",
        "endpoints": {
            "/api/chuyen-doi": "POST - Upload file .docx/.docm và chuyển đổi",
            "/docs": "Xem Swagger documentation"
        }
    }

@app.get("/health")
def kiem_tra_suc_khoe():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Trả về 204 No Content để tắt lỗi 404 từ trình duyệt."""
    return Response(status_code=204)

if __name__ == "__main__":
    # Chạy server với uvicorn
    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload khi code thay đổi (chỉ dùng development)
        reload_dirs=["backend/app"],
        reload_excludes=["*storage*", "*temp_jobs*"]
    )
