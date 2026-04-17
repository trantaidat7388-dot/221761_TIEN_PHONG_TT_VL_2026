"""
config.py
Đọc và quản lý cấu hình từ biến môi trường cho Web API.
"""

import os
from pathlib import Path


def _nap_env_tu_file(file_path: Path) -> None:
    if not file_path.exists():
        return

    for raw_line in file_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _lay_so_nguyen_tu_env(name: str, default: int, min_value: int = 0) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError:
        value = default
    return max(min_value, value)


def _lay_chuoi_tu_env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()

# Thư mục gốc dự án
BASE_DIR = Path(__file__).parent.parent.parent

# Nạp biến môi trường local từ backend/.env (không ghi đè biến đã set trong hệ thống).
_nap_env_tu_file(BASE_DIR / "backend" / ".env")

# Các thư mục dữ liệu
TEMPLATE_FOLDER = BASE_DIR / "input_data"
CUSTOM_TEMPLATE_FOLDER = BASE_DIR / "backend" / "storage" / "custom_templates"
TEMP_FOLDER = BASE_DIR / "backend" / "storage" / "temp_jobs"
OUTPUTS_FOLDER = BASE_DIR / "outputs"

# Đảm bảo các thư mục tồn tại
CUSTOM_TEMPLATE_FOLDER.mkdir(parents=True, exist_ok=True)
TEMP_FOLDER.mkdir(parents=True, exist_ok=True)
OUTPUTS_FOLDER.mkdir(parents=True, exist_ok=True)

# Tùy chọn CORS
CORS_ALLOW_ALL = os.getenv('CORS_ALLOW_ALL', '0').strip() == '1'
CORS_ORIGINS_RAW = os.getenv('CORS_ORIGINS', '').strip()
CORS_ORIGINS = [o.strip() for o in CORS_ORIGINS_RAW.split(',') if o.strip()]

if not CORS_ORIGINS:
    CORS_ORIGINS = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:5173",
        "http://localhost:5174",
    ]

# Cấu hình TTL (Time To Live) cho thư mục rác
TEMP_TTL_HOURS = _lay_so_nguyen_tu_env('TEMP_TTL_HOURS', 6, min_value=1)
OUTPUT_TTL_HOURS = _lay_so_nguyen_tu_env('OUTPUT_TTL_HOURS', 24, min_value=1)

# Logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').strip().upper() or 'INFO'
APP_ENV = _lay_chuoi_tu_env('APP_ENV', 'development').lower() or 'development'

# Frontend / OAuth URLs
FRONTEND_URL = _lay_chuoi_tu_env('FRONTEND_URL', 'http://localhost:5173')

# API giới hạn upload
MAX_DOC_UPLOAD_MB = _lay_so_nguyen_tu_env('MAX_DOC_UPLOAD_MB', 10, min_value=1)
MAX_TEMPLATE_UPLOAD_MB = _lay_so_nguyen_tu_env('MAX_TEMPLATE_UPLOAD_MB', 20, min_value=1)

# Timeout/TTL ở tầng API
SSE_CLEANUP_DELAY_SECONDS = _lay_so_nguyen_tu_env('SSE_CLEANUP_DELAY_SECONDS', 3600, min_value=60)

# Token economy (pre-release)
TOKEN_WORDS_PER_PAGE = _lay_so_nguyen_tu_env('TOKEN_WORDS_PER_PAGE', 1000, min_value=100)
TOKEN_WORDS_PER_UNIT = _lay_so_nguyen_tu_env('TOKEN_WORDS_PER_UNIT', 2250, min_value=100)
TOKEN_MIN_COST = _lay_so_nguyen_tu_env('TOKEN_MIN_COST', 1, min_value=1)
FREE_PLAN_MAX_PAGES = _lay_so_nguyen_tu_env('FREE_PLAN_MAX_PAGES', 60, min_value=1)

# Cấu hình Gói Premium
PREMIUM_PACKAGES = {
    "premium_7d": {"name": "Gói Tuần", "so_ngay": 7, "token_cost": 200, "phu_hop": "Dùng thử ngắn hạn", "tiet_kiem": False},
    "premium_30d": {"name": "Gói Tháng", "so_ngay": 30, "token_cost": 500, "phu_hop": "Phổ biến nhất", "tiet_kiem": False},
    "premium_365d": {"name": "Gói Năm", "so_ngay": 365, "token_cost": 5000, "phu_hop": "Tiết kiệm dài hạn", "tiet_kiem": True}
}

# Cấu hình nạp tiền (SePay)
SEPAY_API_KEY = _lay_chuoi_tu_env('SEPAY_API_KEY', '')
NAME_WEB = _lay_chuoi_tu_env('NAME_WEB', 'W2L')
SECRET_XOR_KEY = _lay_so_nguyen_tu_env('SECRET_XOR_KEY', 0x5EAFB)

# Google OAuth redirect flow
GOOGLE_CLIENT_ID = _lay_chuoi_tu_env('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = _lay_chuoi_tu_env('GOOGLE_CLIENT_SECRET')
GOOGLE_REDIRECT_URI = _lay_chuoi_tu_env('GOOGLE_REDIRECT_URI', 'http://localhost:8000/api/auth/google/callback')
GOOGLE_REDIRECT_URI_FLUTTER = _lay_chuoi_tu_env(
    'GOOGLE_REDIRECT_URI_FLUTTER',
    GOOGLE_REDIRECT_URI.replace('/callback', '/callback/flutter') if GOOGLE_REDIRECT_URI else ''
)

# Rate limiting
RATE_LIMIT_AUTH_PER_MINUTE = _lay_so_nguyen_tu_env('RATE_LIMIT_AUTH_PER_MINUTE', 30, min_value=5)
RATE_LIMIT_CONVERT_PER_MINUTE = _lay_so_nguyen_tu_env('RATE_LIMIT_CONVERT_PER_MINUTE', 20, min_value=5)
RATE_LIMIT_ADMIN_PER_MINUTE = _lay_so_nguyen_tu_env('RATE_LIMIT_ADMIN_PER_MINUTE', 120, min_value=10)
