"""
api_utils.py
Các hàm tiện ích cho riêng Web API.
"""

import shutil
import asyncio
import time
import logging
from pathlib import Path

from ..config import CUSTOM_TEMPLATE_FOLDER, TEMPLATE_FOLDER

logger = logging.getLogger(__name__)

def in_log_loi(thong_diep: str, loi: Exception | None = None) -> None:
    """In log lỗi ra console để developer dễ debug."""
    if loi is not None:
        logger.error("%s: %s", thong_diep, loi)
    else:
        logger.error(thong_diep)

def doc_noi_dung_tex_an_toan(duong_dan: Path) -> str:
    """Đọc nội dung .tex an toàn với fallback encoding."""
    if not duong_dan.exists():
        return ''

    for enc in ['utf-8', 'utf-16', 'latin-1']:
        try:
            noi_dung = duong_dan.read_text(encoding=enc, errors='ignore')
            if noi_dung and noi_dung.strip():
                return noi_dung
        except Exception as loi:
            in_log_loi(f"Không thể đọc tex bằng encoding={enc}: {duong_dan}", loi)
    return ''

def xoa_thu_muc_an_toan(duong_dan: Path) -> None:
    """Xóa thư mục an toàn và không làm crash server nếu có lỗi."""
    try:
        if duong_dan.exists():
            shutil.rmtree(duong_dan, ignore_errors=True)
    except Exception as loi:
        in_log_loi(f"Không thể xóa thư mục: {duong_dan}", loi)

async def don_dep_sau_thoi_gian(duong_dan: Path, giay: int = 3600) -> None:
    """Dọn dẹp thư mục job sau TTL (mặc định 1 giờ) để user có thời gian tải ZIP."""
    try:
        await asyncio.sleep(giay)
    except Exception as loi:
        in_log_loi(f"Lỗi sleep cleanup: {duong_dan}", loi)
    xoa_thu_muc_an_toan(duong_dan)

async def don_dep_sau_15_phut(duong_dan: Path) -> None:
    """Alias backward-compatible cho tác vụ dọn dẹp hệ thống cũ (15 phút)."""
    await don_dep_sau_thoi_gian(duong_dan, 900)

def quet_xoa_thu_muc_mo_coi(thu_muc_goc: Path, so_gio_ton_tai_toi_da: int) -> None:
    """Quét và xóa các thư mục/file cũ còn tồn đọng để tránh tràn ổ đĩa."""
    if not thu_muc_goc.exists():
        return
    now = time.time()
    ttl_seconds = max(1, so_gio_ton_tai_toi_da) * 3600

    try:
        for item in thu_muc_goc.iterdir():
            try:
                mtime = item.stat().st_mtime
                if now - mtime < ttl_seconds:
                    continue
                if item.is_dir():
                    shutil.rmtree(item, ignore_errors=True)
                else:
                    item.unlink(missing_ok=True)
            except Exception as loi_item:
                in_log_loi(f"Không thể dọn item mồ côi: {item}", loi_item)
    except Exception as loi:
        in_log_loi(f"Không thể quét dọn thư mục: {thu_muc_goc}", loi)

_BUILTIN_TEMPLATE_MAP = {
    "ieee_conference":  "IEEE-conference-template-062824",
    "twocolumn":        "IEEE-conference-template-062824",
    "springer_lncs":    "LaTeX2e_Proceedings_Templates_download__1",
    "onecolumn":        "latex_template_onecolumn.tex",
    "elsarticle":       "elsarticle-template-harv.tex",
    "rho_article":      "Rho_Class_Extracted",
}

_GLOBAL_TEMPLATE_PREFIX = "custom_global_"
_PRIVATE_TEMPLATE_PREFIX = "custom_user_"
_USERS_TEMPLATE_DIRNAME = "users"


def _resolve_custom_template_name_and_scope(
    template_type: str,
    current_user_id: int | None,
    current_user_role: str | None,
) -> tuple[str | None, Path | None]:
    """Phân tích ID template custom và trả về (scope, đường dẫn thư mục gốc template)."""
    role = (current_user_role or "user").lower()

    # custom_user_<owner_id>_<template_name>
    if template_type.startswith(_PRIVATE_TEMPLATE_PREFIX):
        payload = template_type[len(_PRIVATE_TEMPLATE_PREFIX):]
        owner_part, sep, template_name = payload.partition("_")
        if not sep or not owner_part.isdigit() or not template_name:
            return (None, None)
        owner_id = int(owner_part)
        if current_user_id is None:
            return (None, None)
        if owner_id != current_user_id and role != "admin":
            return (None, None)
        return ("private", CUSTOM_TEMPLATE_FOLDER / _USERS_TEMPLATE_DIRNAME / f"u_{owner_id}" / template_name)

    # custom_global_<template_name>
    if template_type.startswith(_GLOBAL_TEMPLATE_PREFIX):
        name = template_type[len(_GLOBAL_TEMPLATE_PREFIX):]
        if not name:
            return (None, None)
        return ("global", CUSTOM_TEMPLATE_FOLDER / name)

    # Legacy support: custom_<template_name> => global template
    if template_type.startswith("custom_"):
        legacy_name = template_type[len("custom_"):]
        if not legacy_name:
            return (None, None)
        return ("global", CUSTOM_TEMPLATE_FOLDER / legacy_name)

    return (None, None)

def _resolve_template_path(
    template_type: str,
    current_user_id: int | None = None,
    current_user_role: str | None = None,
) -> Path | None:
    """Resolve a built-in OR custom template type → absolute path of the main .tex file."""
    # Nhập `tim_file_tex_chinh` từ core engine tại đây để tránh vòng lặp logic
    from backend.core_engine.utils import tim_file_tex_chinh

    # ── Handle custom_* template IDs ──
    custom_scope, custom_path = _resolve_custom_template_name_and_scope(
        template_type,
        current_user_id=current_user_id,
        current_user_role=current_user_role,
    )
    if custom_scope and custom_path is not None:
        # Try directory-based custom template
        dir_path = custom_path
        if dir_path.is_dir():
            try:
                return Path(tim_file_tex_chinh(str(dir_path)))
            except FileNotFoundError:
                # Fallback: first .tex found
                first_tex = next(dir_path.rglob("*.tex"), None)
                return first_tex
        # Try flat .tex file
        tex_path = dir_path.with_suffix(".tex")
        if tex_path.exists():
            return tex_path
        return None

    # ── Built-in template map ──
    tpl_name = _BUILTIN_TEMPLATE_MAP.get(template_type)
    if not tpl_name:
        return None
    if tpl_name.endswith(".tex"):
        # Legacy flat-file template
        for probe in (CUSTOM_TEMPLATE_FOLDER / tpl_name, TEMPLATE_FOLDER / tpl_name):
            if probe.exists():
                return probe
        return None
        
    # Directory-based template
    dir_path = CUSTOM_TEMPLATE_FOLDER / tpl_name
    if dir_path.is_dir():
        try:
            return Path(tim_file_tex_chinh(str(dir_path)))
        except FileNotFoundError:
            return next(dir_path.rglob("*.tex"), None)
            
    # Fallback: try flat .tex with the same stem
    for probe in (CUSTOM_TEMPLATE_FOLDER / f"{tpl_name}.tex", TEMPLATE_FOLDER / f"{tpl_name}.tex"):
        if probe.exists():
            return probe
    return None
