"""
landing_content.py
Quản lý nội dung Landing Page — đọc/ghi từ file JSON.
Admin có thể chỉnh sửa nội dung landing page từ dashboard.
"""

from __future__ import annotations

import json
from threading import Lock

from ..config import BASE_DIR

_CONTENT_FILE = BASE_DIR / "backend" / "storage" / "landing_content.json"
_LOCK = Lock()

# ── NỘI DUNG MẶC ĐỊNH (giống hardcoded trong TrangLanding.jsx) ──────────────

_NOI_DUNG_MAC_DINH: dict = {
    "hero": {
        "badge": "Nền tảng chuyển đổi tự động",
        "title": "Biến file Word thành",
        "title_highlight": "LaTeX chuẩn xuất bản",
        "description": "Upload file .docx, chọn template nhà xuất bản, nhận kết quả LaTeX chuẩn — tự động, nhanh chóng, chính xác.",
        "cta_primary": "Bắt đầu miễn phí",
        "cta_secondary": "Tải App Android",
        "stats": [
            {"val": "6+", "sub": "Template"},
            {"val": "3", "sub": "Tầng toán học"},
            {"val": "Live", "sub": "Realtime"},
            {"val": "24/7", "sub": "Hoạt động"},
        ],
    },
    "tinh_nang": [
        {"icon": "FileText", "title": "Chuyển đổi thông minh", "desc": "Tự động nhận dạng bố cục tài liệu, tiêu đề, tác giả, công thức và bảng biểu từ file Word."},
        {"icon": "BrainCircuit", "title": "Công thức toán học", "desc": "Giữ công thức rõ ràng, dễ biên dịch và đúng ngữ cảnh trong tài liệu LaTeX."},
        {"icon": "Layers", "title": "6+ mẫu nhà xuất bản", "desc": "IEEE, Springer LNCS, ACM, Elsevier, MDPI, Rho Class — sẵn sàng nộp bài ngay."},
        {"icon": "Zap", "title": "Xử lý thời gian thực", "desc": "Theo dõi tiến trình trực tiếp trong khi hệ thống chuyển đổi tài liệu."},
        {"icon": "Lock", "title": "Bảo mật tài khoản", "desc": "Đăng nhập an toàn, phân quyền rõ ràng và bảo vệ dữ liệu người dùng."},
        {"icon": "CreditCard", "title": "Thanh toán tiện lợi", "desc": "Nạp token nhanh bằng chuyển khoản và nhận cập nhật trạng thái gần như tức thời."},
    ],
    "buoc_su_dung": [
        {"step": 1, "icon": "Upload", "title": "Tải lên file Word", "desc": "Chọn file .docx từ máy tính của bạn."},
        {"step": 2, "icon": "Settings", "title": "Chọn mẫu LaTeX", "desc": "Chọn nhà xuất bản hoặc upload template riêng."},
        {"step": 3, "icon": "Download", "title": "Tải về kết quả", "desc": "Nhận .zip gồm .tex, .pdf, hình ảnh và phụ thuộc."},
    ],
    "mau_template": [
        {"name": "IEEE Conference", "cls": "IEEEtran.cls"},
        {"name": "Springer LNCS", "cls": "llncs.cls"},
        {"name": "ACM SIG", "cls": "acmart.cls"},
        {"name": "MDPI Open Access", "cls": "mdpi.cls"},
        {"name": "Elsevier", "cls": "elsarticle.cls"},
        {"name": "Rho Class", "cls": "rho.cls"},
    ],
    "goi_premium": [
        {"name": "Gói Tuần", "days": 7, "price": "20.000", "badge": None},
        {"name": "Gói Tháng", "days": 30, "price": "50.000", "badge": "Phổ biến"},
        {"name": "Gói Năm", "days": 365, "price": "500.000", "badge": "Tiết kiệm"},
    ],
    "faq": [
        {
            "q": "Kết quả xuất ra gồm những gì?",
            "a": "Hệ thống xuất file .zip sẵn sàng sử dụng: .tex, hình ảnh, tài nguyên template và file PDF nếu môi trường có LaTeX.",
        },
        {
            "q": "Thanh toán có an toàn không?",
            "a": "Hệ thống hỗ trợ các kênh thanh toán phổ biến và lưu vết giao dịch rõ ràng trong tài khoản.",
        },
        {
            "q": "Sau khi thanh toán thì kích hoạt khi nào?",
            "a": "Tài khoản được kích hoạt nhanh chóng ngay sau khi giao dịch được xác nhận.",
        },
    ],
    "so_sanh": {
        "truoc": {
            "title": "Thủ công, rời rạc, dễ sai",
            "items": [
                "Copy/paste công thức và format nhiều lần",
                "Dễ lệch chuẩn template nhà xuất bản",
                "Mất thời gian sửa lỗi biên dịch",
            ],
        },
        "sau": {
            "title": "Tự động, nhất quán, sẵn nộp",
            "items": [
                "Chuẩn hóa heading, tác giả, hình, bảng",
                "Mapping công thức đa tầng OMML/OLE sang LaTeX",
                "Xuất gói .zip sẵn upload Overleaf",
            ],
        },
    },
    "cta_bottom": {
        "title": "Sẵn sàng chuyển đổi?",
        "description": "Đăng ký miễn phí và bắt đầu chuyển đổi bài báo của bạn ngay hôm nay.",
    },
    "section_order": [
        "hero",
        "tinh_nang",
        "buoc_su_dung",
        "mau_template",
        "goi_premium",
        "thanh_toan",
        "so_sanh",
        "faq",
        "cta_bottom",
    ],
}


def _doc_file_json() -> dict:
    if not _CONTENT_FILE.exists():
        return {}
    try:
        return json.loads(_CONTENT_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def lay_noi_dung_landing() -> dict:
    """Trả về nội dung landing page. Merge với default để đảm bảo đầy đủ."""
    with _LOCK:
        saved = _doc_file_json()

    if not saved:
        return dict(_NOI_DUNG_MAC_DINH)

    # Merge: saved overrides defaults
    result = dict(_NOI_DUNG_MAC_DINH)
    for key in result:
        if key in saved:
            result[key] = saved[key]
    # Allow custom keys from saved
    for key in saved:
        if key not in result:
            result[key] = saved[key]
    return result


def cap_nhat_noi_dung_landing(data: dict) -> dict:
    """Cập nhật nội dung landing page. Ghi toàn bộ data vào file."""
    with _LOCK:
        _CONTENT_FILE.parent.mkdir(parents=True, exist_ok=True)
        tmp_file = _CONTENT_FILE.with_suffix(".tmp")
        tmp_file.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        tmp_file.replace(_CONTENT_FILE)

    return lay_noi_dung_landing()


def reset_noi_dung_landing() -> dict:
    """Reset về nội dung mặc định."""
    with _LOCK:
        if _CONTENT_FILE.exists():
            _CONTENT_FILE.unlink()
    return dict(_NOI_DUNG_MAC_DINH)
