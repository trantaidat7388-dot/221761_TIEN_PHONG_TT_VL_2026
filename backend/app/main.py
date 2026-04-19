"""
main.py
Điểm khởi đầu (Khởi tạo FastAPI, CORS, gán Router).
"""

from collections import defaultdict, deque
import logging
import os
import threading
import time
import uuid
from fastapi import FastAPI, Response
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text
from fastapi.responses import JSONResponse
import uvicorn

from . import database
from . import models
from . import auth
from .config import (
    CORS_ALLOW_ALL,
    CORS_ORIGINS,
    TEMP_TTL_HOURS,
    OUTPUT_TTL_HOURS,
    TEMP_FOLDER,
    OUTPUTS_FOLDER,
    LOG_LEVEL,
    FREE_PLAN_MAX_PAGES,
    RATE_LIMIT_AUTH_PER_MINUTE,
    RATE_LIMIT_CONVERT_PER_MINUTE,
    RATE_LIMIT_ADMIN_PER_MINUTE,
)
from .utils.api_utils import quet_xoa_thu_muc_mo_coi
from .routers import admin_routes, auth_routes, base, file_upload, payment_routes, pages_routes
from .services.landing_content import lay_noi_dung_landing
from .services.admin_system_config import lay_cau_hinh_he_thong as _lay_cau_hinh_he_thong

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)
_RATE_LIMIT_WINDOW_SECONDS = 60
_rate_limit_store: dict[str, deque[float]] = defaultdict(deque)
_rate_limit_lock = threading.Lock()

# Khởi tạo FastAPI app
app = FastAPI(title="Word2LaTeX API", version="1.0.0")

# Khởi tạo database
models.Base.metadata.create_all(bind=database.engine)

# Gắn các routers
app.include_router(base.router)
app.include_router(file_upload.router)
app.include_router(auth_routes.router)
app.include_router(admin_routes.router)
app.include_router(payment_routes.router)
app.include_router(pages_routes.router)


def _dam_bao_cot_vai_tro_nguoi_dung() -> None:
    inspector = inspect(database.engine)
    user_columns = [col["name"] for col in inspector.get_columns("users")]
    if "role" in user_columns:
        return

    with database.engine.begin() as conn:
        conn.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR DEFAULT 'user' NOT NULL"))
        conn.execute(text("UPDATE users SET role = 'user' WHERE role IS NULL OR TRIM(role) = ''"))


def _dam_bao_schema_users_premium_token_google() -> None:
    inspector = inspect(database.engine)
    user_columns = {col["name"] for col in inspector.get_columns("users")}

    alter_statements = []
    if "plan_type" not in user_columns:
        alter_statements.append("ALTER TABLE users ADD COLUMN plan_type VARCHAR DEFAULT 'free' NOT NULL")
    if "token_balance" not in user_columns:
        alter_statements.append(f"ALTER TABLE users ADD COLUMN token_balance INTEGER DEFAULT {FREE_PLAN_MAX_PAGES} NOT NULL")
    if "premium_started_at" not in user_columns:
        alter_statements.append("ALTER TABLE users ADD COLUMN premium_started_at DATETIME")
    if "premium_expires_at" not in user_columns:
        alter_statements.append("ALTER TABLE users ADD COLUMN premium_expires_at DATETIME")
    if "auth_provider" not in user_columns:
        alter_statements.append("ALTER TABLE users ADD COLUMN auth_provider VARCHAR DEFAULT 'local' NOT NULL")
    if "google_id" not in user_columns:
        alter_statements.append("ALTER TABLE users ADD COLUMN google_id VARCHAR")

    with database.engine.begin() as conn:
        for stmt in alter_statements:
            conn.execute(text(stmt))

        conn.execute(text("UPDATE users SET plan_type='free' WHERE plan_type IS NULL OR TRIM(plan_type) = ''"))
        conn.execute(text(
            f"UPDATE users SET token_balance={FREE_PLAN_MAX_PAGES} "
            f"WHERE plan_type='free' AND (token_balance IS NULL OR token_balance < 0 OR token_balance > {FREE_PLAN_MAX_PAGES})"
        ))
        conn.execute(text("UPDATE users SET token_balance=25000 WHERE plan_type='premium' AND (token_balance IS NULL OR token_balance < 0)"))
        conn.execute(text("UPDATE users SET auth_provider='local' WHERE auth_provider IS NULL OR TRIM(auth_provider) = ''"))

        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_users_plan_type ON users (plan_type)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_users_premium_expires_at ON users (premium_expires_at)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_users_google_id ON users (google_id)"))
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_users_google_id_not_null ON users (google_id) WHERE google_id IS NOT NULL"))


def _dam_bao_schema_conversion_history_token_fields() -> None:
    inspector = inspect(database.engine)
    if "conversion_history" not in inspector.get_table_names():
        return

    history_columns = {col["name"] for col in inspector.get_columns("conversion_history")}
    alter_statements = []
    if "pages_count" not in history_columns:
        alter_statements.append("ALTER TABLE conversion_history ADD COLUMN pages_count INTEGER DEFAULT 0 NOT NULL")
    if "token_cost" not in history_columns:
        alter_statements.append("ALTER TABLE conversion_history ADD COLUMN token_cost INTEGER DEFAULT 0 NOT NULL")
    if "token_refunded" not in history_columns:
        alter_statements.append("ALTER TABLE conversion_history ADD COLUMN token_refunded BOOLEAN DEFAULT 0 NOT NULL")
    if "error_type" not in history_columns:
        alter_statements.append("ALTER TABLE conversion_history ADD COLUMN error_type VARCHAR")
    if "error_message" not in history_columns:
        alter_statements.append("ALTER TABLE conversion_history ADD COLUMN error_message VARCHAR")

    with database.engine.begin() as conn:
        for stmt in alter_statements:
            conn.execute(text(stmt))

        conn.execute(text("UPDATE conversion_history SET pages_count=0 WHERE pages_count IS NULL"))
        conn.execute(text("UPDATE conversion_history SET token_cost=0 WHERE token_cost IS NULL"))
        conn.execute(text("UPDATE conversion_history SET token_refunded=0 WHERE token_refunded IS NULL"))

        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_conversion_history_user_created ON conversion_history (user_id, created_at DESC)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_conversion_history_token_refunded ON conversion_history (token_refunded)"))


def _dam_bao_schema_token_ledger_indexes() -> None:
    with database.engine.begin() as conn:
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_token_ledger_user_created ON token_ledger (user_id, created_at DESC)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_token_ledger_reason ON token_ledger (reason)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_token_ledger_job_id ON token_ledger (job_id)"))


def _dam_bao_schema_admin_audit_indexes() -> None:
    with database.engine.begin() as conn:
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_admin_audit_logs_actor_user_id ON admin_audit_logs (actor_user_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_admin_audit_logs_action ON admin_audit_logs (action)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_admin_audit_logs_target_user_id ON admin_audit_logs (target_user_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_admin_audit_logs_request_id ON admin_audit_logs (request_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_admin_audit_logs_created_at ON admin_audit_logs (created_at)"))


def _dam_bao_schema_login_sessions() -> None:
    """Đảm bảo bảng login_sessions tồn tại cho Cloud-Sync Polling."""
    inspector = inspect(database.engine)
    if "login_sessions" not in inspector.get_table_names():
        with database.engine.begin() as conn:
            conn.execute(text("""
                CREATE TABLE login_sessions (
                    session_id VARCHAR PRIMARY KEY,
                    token VARCHAR,
                    status VARCHAR DEFAULT 'pending' NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
                )
            """))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_login_sessions_status ON login_sessions (status)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_login_sessions_created_at ON login_sessions (created_at)"))
        logger.info("[Migration] Created login_sessions table for Cloud-Sync Polling.")


def _lay_rate_limit_cho_path(path: str) -> tuple[str, int] | None:
    if path.startswith("/api/auth"):
        return ("auth", RATE_LIMIT_AUTH_PER_MINUTE)
    if path.startswith("/api/chuyen-doi"):
        return ("convert", RATE_LIMIT_CONVERT_PER_MINUTE)
    if path.startswith("/api/admin"):
        return ("admin", RATE_LIMIT_ADMIN_PER_MINUTE)
    return None


def _bi_rate_limit(category: str, identity: str, max_requests: int, now: float) -> bool:
    key = f"{category}:{identity}"
    with _rate_limit_lock:
        q = _rate_limit_store[key]
        while q and (now - q[0]) > _RATE_LIMIT_WINDOW_SECONDS:
            q.popleft()
        if len(q) >= max_requests:
            return True
        q.append(now)
        return False


def _tao_tai_khoan_admin_mac_dinh() -> None:
    admin_username = os.getenv("ADMIN_USERNAME", "admin").strip() or "admin"
    admin_email = os.getenv("ADMIN_EMAIL", "admin@word2latex.local").strip() or "admin@word2latex.local"
    admin_password = os.getenv("ADMIN_PASSWORD", "Admin@123456")

    db = database.SessionLocal()
    try:
        existing_admin = db.query(models.User).filter(models.User.email == admin_email).first()
        if existing_admin:
            changed = False
            if (existing_admin.role or "user").lower() != "admin":
                existing_admin.role = "admin"
                changed = True
            if (existing_admin.plan_type or "free") != "premium":
                existing_admin.plan_type = "premium"
                changed = True
            if (existing_admin.auth_provider or "local") != "local":
                existing_admin.auth_provider = "local"
                changed = True
            if (existing_admin.token_balance or 0) < 25000:
                existing_admin.token_balance = 25000
                changed = True
            if changed:
                db.commit()
            return

        admin_user = models.User(
            username=admin_username,
            email=admin_email,
            hashed_password=auth.bam_mat_khau(admin_password),
            role="admin",
            plan_type="premium",
            token_balance=25000,
            auth_provider="local",
        )
        db.add(admin_user)
        db.commit()
        logger.warning(
            "Default admin account created email=%s username=%s. Please change ADMIN_PASSWORD immediately.",
            admin_email,
            admin_username,
        )
    finally:
        db.close()


@app.middleware("http")
async def gan_request_id(request: Request, call_next) -> Response:
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id

    rate_limit_config = _lay_rate_limit_cho_path(request.url.path)
    if rate_limit_config:
        category, max_requests = rate_limit_config
        client_ip = request.client.host if request.client else "unknown"
        if _bi_rate_limit(category, client_ip, max_requests, time.monotonic()):
            return JSONResponse(
                status_code=429,
                content={
                    "detail": f"Vượt quá giới hạn request cho nhóm {category}. Vui lòng thử lại sau.",
                    "request_id": request_id,
                },
                headers={"X-Request-ID": request_id, "Retry-After": "60"},
            )

    started = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - started) * 1000
    response.headers["X-Request-ID"] = request_id
    response.headers["ngrok-skip-browser-warning"] = "true"
    response.headers["Bypass-Tunnel-Reminder"] = "true"
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
    _dam_bao_cot_vai_tro_nguoi_dung()
    _dam_bao_schema_users_premium_token_google()
    _dam_bao_schema_conversion_history_token_fields()
    _dam_bao_schema_token_ledger_indexes()
    _dam_bao_schema_admin_audit_indexes()
    _dam_bao_schema_login_sessions()
    _tao_tai_khoan_admin_mac_dinh()

    logger.info("Registered POST routes:")
    for route in app.routes:
        if getattr(route, "methods", None) and "POST" in route.methods:
            logger.info(" - %s", route.path)

    # Dọn dẹp các thư mục/file mồ côi trong temp khi server khởi động
    quet_xoa_thu_muc_mo_coi(TEMP_FOLDER, TEMP_TTL_HOURS)
    quet_xoa_thu_muc_mo_coi(OUTPUTS_FOLDER, OUTPUT_TTL_HOURS)

# ── PUBLIC ENDPOINTS (no auth required) ──────────────────────────────────────

@app.get("/api/landing-content", tags=["Public"])
def lay_noi_dung_landing_public() -> dict:
    """Public endpoint: Trả về nội dung landing page để hiển thị."""
    return {"content": lay_noi_dung_landing()}


@app.get("/api/active-theme", tags=["Public"])
def lay_theme_hien_tai() -> dict:
    """Public endpoint: Trả về theme đang active cho toàn website."""
    config = _lay_cau_hinh_he_thong()
    return {"theme": config.get("settings", {}).get("active_theme", "dark-indigo")}


@app.get("/favicon.ico", include_in_schema=False)
async def favicon() -> Response:
    """Trả về 204 No Content để tắt lỗi 404 từ trình duyệt."""
    return Response(status_code=204)

# ── CORS MIDDLEWARE (Outermost) ──────────────────────────────────────────────
# Đặt ở cuối để nó được thực thi đầu tiên (Outer-most) trong stack middleware
if CORS_ALLOW_ALL:
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex="https?://.*",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

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
