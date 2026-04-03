"""
run_api.py
Script khởi động nhanh API server bằng Uvicorn.

Cách sử dụng:
    python run_api.py
    python run_api.py --host 0.0.0.0 --port 8000 --reload
"""

import argparse
import uvicorn


def main() -> None:
    """Phân tích tham số dòng lệnh và khởi chạy Uvicorn server."""
    parser = argparse.ArgumentParser(
        description="Khởi động Word2LaTeX API server.",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Địa chỉ host lắng nghe (mặc định: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Cổng lắng nghe (mặc định: 8000)",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        default=True,
        help="Tự động reload khi code thay đổi (mặc định: bật)",
    )
    parser.add_argument(
        "--no-reload",
        action="store_true",
        help="Tắt auto-reload (dùng cho production)",
    )
    args = parser.parse_args()

    reload_enabled = args.reload and not args.no_reload

    uvicorn.run(
        "backend.app.main:app",
        host=args.host,
        port=args.port,
        reload=reload_enabled,
        reload_dirs=["backend/app", "backend/core_engine"] if reload_enabled else None,
        reload_excludes=["*storage*", "*temp_jobs*"] if reload_enabled else None,
    )


if __name__ == "__main__":
    main()
