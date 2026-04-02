"""
main.py
Điểm khởi đầu (Khởi tạo FastAPI, CORS, gán Router).
"""

from datetime import datetime
import logging
import time
import uuid
from fastapi import FastAPI, Response
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from . import database
from . import models
from .config import (
    CORS_ALLOW_ALL,
    CORS_ORIGINS,
    TEMP_TTL_HOURS,
    OUTPUT_TTL_HOURS,
    TEMP_FOLDER,
    OUTPUTS_FOLDER,
    LOG_LEVEL,
)
from .utils.api_utils import quet_xoa_thu_muc_mo_coi
from .routers import templates, chuyen_doi, auth_routes

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)

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


@app.middleware("http")
async def gan_request_id(request: Request, call_next) -> Response:
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id
    started = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - started) * 1000
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "request_id=%s method=%s path=%s status=%s duration_ms=%.2f",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
    )
    return response

@app.on_event("startup")
def xu_ly_don_dep_khi_khoi_dong() -> None:
    """Startup hook: in route POST và dọn rác."""
    logger.info("Registered POST routes:")
    for route in app.routes:
        if getattr(route, "methods", None) and "POST" in route.methods:
            logger.info(" - %s", route.path)

    # Dọn dẹp các thư mục/file mồ côi trong temp khi server khởi động
    quet_xoa_thu_muc_mo_coi(TEMP_FOLDER, TEMP_TTL_HOURS)
    quet_xoa_thu_muc_mo_coi(OUTPUTS_FOLDER, OUTPUT_TTL_HOURS)

@app.get("/")
def doc_api() -> dict:
    """Endpoint gốc - hướng dẫn sử dụng API."""
    return {
        "message": "Word2LaTeX API đang hoạt động",
        "endpoints": {
            "/api/chuyen-doi": "POST - Upload file .docx/.docm và chuyển đổi",
            "/docs": "Xem Swagger documentation"
        }
    }

@app.get("/health")
def kiem_tra_suc_khoe() -> dict:
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/favicon.ico", include_in_schema=False)
async def favicon() -> Response:
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
