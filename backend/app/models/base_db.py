"""Export thành phần database theo cấu trúc dự án thống nhất.

Module này cung cấp điểm import ổn định cho Base/Session/engine,
đồng thời tái sử dụng triển khai hiện có trong backend.app.database.
"""

from ..database import Base, SessionLocal, engine, lay_db

__all__ = ["Base", "SessionLocal", "engine", "lay_db"]
