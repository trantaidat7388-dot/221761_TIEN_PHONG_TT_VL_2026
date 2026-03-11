"""
config.py
Đọc và quản lý cấu hình từ biến môi trường cho Web API.
"""

import os
from pathlib import Path

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
TEMP_TTL_HOURS = int(os.getenv('TEMP_TTL_HOURS', '6').strip() or '6')
OUTPUT_TTL_HOURS = int(os.getenv('OUTPUT_TTL_HOURS', '24').strip() or '24')
