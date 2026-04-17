"""
admin_system_config.py
Luu/nap cau hinh he thong phuc vu tab Admin Cau hinh.
"""

from __future__ import annotations

import json
from threading import Lock

from ..config import (
    BASE_DIR,
    FREE_PLAN_MAX_PAGES,
    MAX_DOC_UPLOAD_MB,
    RATE_LIMIT_ADMIN_PER_MINUTE,
    SEPAY_API_KEY,
    TOKEN_MIN_COST,
)

_CONFIG_FILE = BASE_DIR / "backend" / "storage" / "admin_system_config.json"
_LOCK = Lock()

_VALID_THEMES = {"dark-indigo", "midnight-cyan", "warm-slate", "light-pro"}

_DEFAULTS = {
    "token_min_cost_vnd": int(TOKEN_MIN_COST),
    "free_plan_max_pages": int(FREE_PLAN_MAX_PAGES),
    "max_doc_upload_mb": int(MAX_DOC_UPLOAD_MB),
    "rate_limit_admin_per_minute": int(RATE_LIMIT_ADMIN_PER_MINUTE),
    "active_theme": "dark-indigo",
}


def _doc_file_json() -> dict:
    if not _CONFIG_FILE.exists():
        return {}
    try:
        return json.loads(_CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception:
        # Neu file hu/format sai thi bo qua de tranh crash API admin.
        return {}


def _xay_dung_ket_qua_tu_saved(saved: dict) -> dict:
    raw_theme = saved.get("active_theme", _DEFAULTS["active_theme"])
    settings = {
        "token_min_cost_vnd": int(saved.get("token_min_cost_vnd", _DEFAULTS["token_min_cost_vnd"])),
        "free_plan_max_pages": int(saved.get("free_plan_max_pages", _DEFAULTS["free_plan_max_pages"])),
        "max_doc_upload_mb": int(saved.get("max_doc_upload_mb", _DEFAULTS["max_doc_upload_mb"])),
        "rate_limit_admin_per_minute": int(saved.get("rate_limit_admin_per_minute", _DEFAULTS["rate_limit_admin_per_minute"])),
        "active_theme": raw_theme if raw_theme in _VALID_THEMES else _DEFAULTS["active_theme"],
    }
    return {
        "settings": settings,
        "meta": {
            "sepay_api_key_configured": bool(SEPAY_API_KEY),
            "file_path": str(_CONFIG_FILE),
            "restart_required": True,
            "note": "Gia tri duoc luu o backend/storage/admin_system_config.json. Cac service chinh se doc lai sau khi restart backend.",
        },
    }


def lay_cau_hinh_he_thong() -> dict:
    with _LOCK:
        saved = _doc_file_json()
    return _xay_dung_ket_qua_tu_saved(saved)


def cap_nhat_cau_hinh_he_thong(partial: dict) -> dict:
    payload = {}
    for k, v in partial.items():
        if v is not None:
            if k == "active_theme":
                payload[k] = str(v)
            else:
                payload[k] = int(v)

    with _LOCK:
        saved = _doc_file_json()
        current = _xay_dung_ket_qua_tu_saved(saved)["settings"]
        merged = {**current, **payload}

        _CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        tmp_file = _CONFIG_FILE.with_suffix(".tmp")
        tmp_file.write_text(json.dumps(merged, ensure_ascii=True, indent=2), encoding="utf-8")
        tmp_file.replace(_CONFIG_FILE)

    with _LOCK:
        return _xay_dung_ket_qua_tu_saved(_doc_file_json())
