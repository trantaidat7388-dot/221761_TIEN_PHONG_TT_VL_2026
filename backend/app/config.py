"""
config.py
Đọc và quản lý cấu hình từ biến môi trường cho Web API.
"""

import os
from pathlib import Path


def _lay_so_nguyen_tu_env(name: str, default: int, min_value: int = 0) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError:
        value = default
    return max(min_value, value)

# Thư mục gốc dự án
BASE_DIR = Path(__file__).parent.parent.parent

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

# API giới hạn upload
MAX_DOC_UPLOAD_MB = _lay_so_nguyen_tu_env('MAX_DOC_UPLOAD_MB', 10, min_value=1)
MAX_TEMPLATE_UPLOAD_MB = _lay_so_nguyen_tu_env('MAX_TEMPLATE_UPLOAD_MB', 20, min_value=1)

# Timeout/TTL ở tầng API
SSE_CLEANUP_DELAY_SECONDS = _lay_so_nguyen_tu_env('SSE_CLEANUP_DELAY_SECONDS', 3600, min_value=60)

# Token economy (pre-release)
TOKEN_WORDS_PER_PAGE = _lay_so_nguyen_tu_env('TOKEN_WORDS_PER_PAGE', 450, min_value=100)
TOKEN_WORDS_PER_UNIT = _lay_so_nguyen_tu_env('TOKEN_WORDS_PER_UNIT', 2250, min_value=100)
TOKEN_MIN_COST = _lay_so_nguyen_tu_env('TOKEN_MIN_COST', 1, min_value=1)
PREMIUM_SELF_SUBSCRIBE_DAYS = _lay_so_nguyen_tu_env('PREMIUM_SELF_SUBSCRIBE_DAYS', 30, min_value=1)
PREMIUM_SELF_SUBSCRIBE_TOKEN_COST = _lay_so_nguyen_tu_env('PREMIUM_SELF_SUBSCRIBE_TOKEN_COST', 12000, min_value=1)

# Rate limiting
RATE_LIMIT_AUTH_PER_MINUTE = _lay_so_nguyen_tu_env('RATE_LIMIT_AUTH_PER_MINUTE', 30, min_value=5)
RATE_LIMIT_CONVERT_PER_MINUTE = _lay_so_nguyen_tu_env('RATE_LIMIT_CONVERT_PER_MINUTE', 20, min_value=5)
RATE_LIMIT_ADMIN_PER_MINUTE = _lay_so_nguyen_tu_env('RATE_LIMIT_ADMIN_PER_MINUTE', 120, min_value=10)
