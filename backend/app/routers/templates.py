"""
templates.py
Định nghĩa các API liên quan đến quản lý, tải lên mẫu LaTeX (Templates).
"""

import shutil
import zipfile
from io import BytesIO
from pathlib import Path
from fastapi import APIRouter, File, UploadFile, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi import Depends
from sqlalchemy.orm import Session

from ..config import CUSTOM_TEMPLATE_FOLDER, MAX_TEMPLATE_UPLOAD_MB
from ..utils.api_utils import doc_noi_dung_tex_an_toan, in_log_loi
from .. import auth, models
from ..database import lay_db

router = APIRouter(prefix="/api/templates", tags=["Templates"])

# Names/stems to hide from the custom list (defaults + support/class files)
HIDDEN = {
    "IEEE-conference-template-062824",
    "LaTeX2e_Proceedings_Templates_download__1",
    "LaTeX2e_Proceedings_Templates_download__1_",
    "samplepaper_springer_", "samplepaper_springer",
    "samplepaper",
    "latex_template_onecolumn",
    "elsarticle-template-harv", "elsarticle-template-num",
    "IEEEtran", "llncs",
}

# Reserved directory names that must not be overwritten by user uploads
_RESERVED_UPLOAD_NAMES = HIDDEN.copy()

_ALLOWED_TEMPLATE_EXTENSIONS = {
    ".tex", ".cls", ".sty", ".bst", ".bib", ".csl", ".txt",
    ".png", ".jpg", ".jpeg", ".pdf", ".eps", ".png",
    ".otf", ".ttf", ".woff", ".woff2",
}
_MAX_ZIP_EXTRACT_SIZE = 80 * 1024 * 1024  # 80MB uncompressed
_MAX_SINGLE_ZIP_ENTRY_SIZE = 20 * 1024 * 1024  # 20MB
_USERS_TEMPLATE_DIRNAME = "users"
_GLOBAL_TEMPLATE_PREFIX = "custom_global_"
_PRIVATE_TEMPLATE_PREFIX = "custom_user_"


def _sanitize_template_name(raw_name: str) -> str:
    return ("".join(c if c.isalnum() or c in ('-', '_') else '_' for c in raw_name).strip('_') or "template")


def _global_template_paths(name: str) -> tuple[Path, Path]:
    return (CUSTOM_TEMPLATE_FOLDER / f"{name}.tex", CUSTOM_TEMPLATE_FOLDER / name)


def _user_template_base(user_id: int) -> Path:
    return CUSTOM_TEMPLATE_FOLDER / _USERS_TEMPLATE_DIRNAME / f"u_{user_id}"


def _user_template_paths(user_id: int, name: str) -> tuple[Path, Path]:
    base = _user_template_base(user_id)
    return (base / f"{name}.tex", base / name)


def _ensure_unique_name_for_scope(base_name: str, tex_path: Path, dir_path: Path) -> str:
    if not tex_path.exists() and not dir_path.exists():
        return base_name
    counter = 2
    while True:
        candidate = f"{base_name}_{counter}"
        candidate_tex = tex_path.with_name(f"{candidate}.tex")
        candidate_dir = dir_path.with_name(candidate)
        if not candidate_tex.exists() and not candidate_dir.exists():
            return candidate
        counter += 1


def _template_metadata(
    template_id: str,
    ten: str,
    kich_thuoc: int,
    pham_vi: str,
    owner_user_id: int | None = None,
    co_the_xoa: bool = True,
) -> dict:
    return {
        "id": template_id,
        "ten": ten,
        "loai": "tuy_chinh",
        "phamVi": pham_vi,
        "ownerUserId": owner_user_id,
        "coTheXoa": co_the_xoa,
        "kichThuoc": kich_thuoc,
    }


def _resolve_current_user_from_bearer(request: Request, db: Session) -> models.User | None:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ", 1)[1]
    try:
        return auth.lay_nguoi_dung_hien_tai(token=token, db=db)
    except Exception:
        return None


def _parse_custom_template_id(template_id: str) -> tuple[str, int | None, str]:
    if template_id.startswith(_PRIVATE_TEMPLATE_PREFIX):
        payload = template_id[len(_PRIVATE_TEMPLATE_PREFIX):]
        owner_part, sep, name = payload.partition("_")
        if sep and owner_part.isdigit() and name:
            return ("private", int(owner_part), name)
        raise HTTPException(status_code=400, detail="ID template private không hợp lệ")

    if template_id.startswith(_GLOBAL_TEMPLATE_PREFIX):
        name = template_id[len(_GLOBAL_TEMPLATE_PREFIX):]
        if name:
            return ("global", None, name)
        raise HTTPException(status_code=400, detail="ID template global không hợp lệ")

    # Backward compatibility: custom_<name> => global
    if template_id.startswith("custom_"):
        name = template_id.replace("custom_", "", 1)
        if name:
            return ("global", None, name)

    raise HTTPException(status_code=400, detail="ID template không hợp lệ")


def _safe_extract_template_zip(zip_bytes: bytes, target_dir: Path) -> None:
    """Extract template ZIP safely with path traversal and extension checks."""
    total_size = 0
    try:
        with zipfile.ZipFile(BytesIO(zip_bytes), "r") as zip_ref:
            for member in zip_ref.infolist():
                raw_name = member.filename.replace("\\", "/")
                normalized = Path(raw_name)

                if normalized.is_absolute() or ".." in normalized.parts or ":" in raw_name:
                    raise HTTPException(status_code=400, detail=f"Đường dẫn không an toàn trong ZIP: {member.filename}")

                if member.is_dir():
                    continue

                ext = Path(member.filename).suffix.lower()
                if ext not in _ALLOWED_TEMPLATE_EXTENSIONS:
                    raise HTTPException(status_code=400, detail=f"File trong ZIP không được phép: {member.filename}")

                if member.file_size > _MAX_SINGLE_ZIP_ENTRY_SIZE:
                    raise HTTPException(status_code=400, detail=f"File quá lớn trong ZIP: {member.filename}")

                total_size += member.file_size
                if total_size > _MAX_ZIP_EXTRACT_SIZE:
                    raise HTTPException(status_code=400, detail="Tổng dung lượng giải nén vượt giới hạn 80MB")

                dest_path = (target_dir / normalized).resolve()
                base_path = target_dir.resolve()
                if not str(dest_path).startswith(str(base_path)):
                    raise HTTPException(status_code=400, detail=f"Đường dẫn không hợp lệ trong ZIP: {member.filename}")

                dest_path.parent.mkdir(parents=True, exist_ok=True)
                with zip_ref.open(member, "r") as src, open(dest_path, "wb") as dst:
                    shutil.copyfileobj(src, dst)
    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="File ZIP không hợp lệ")

@router.get("")
def lay_danh_sach_template(
    request: Request,
    db: Session = Depends(lay_db),
) -> JSONResponse:
    """Lấy danh sách template LaTeX mặc định và tùy chỉnh (không cache)."""
    
    # Import tim_file_tex_chinh local để tránh import cycles
    from backend.core_engine.utils import tim_file_tex_chinh
    
    templates = []

    # Built-in templates shown to every user (directory-based)
    BUILTIN = [
        ("ieee_conference", "IEEE Conference (2 cột)",  "IEEE-conference-template-062824"),
        ("springer_lncs",  "Springer LNCS",             "LaTeX2e_Proceedings_Templates_download__1"),
    ]

    for tpl_id, tpl_label, tpl_dir in BUILTIN:
        dir_path = CUSTOM_TEMPLATE_FOLDER / tpl_dir
        if dir_path.is_dir():
            try:
                tim_file_tex_chinh(str(dir_path))  # validate
                kich_thuoc = sum(f.stat().st_size for f in dir_path.rglob('*') if f.is_file())
                templates.append({"id": tpl_id, "ten": tpl_label, "loai": "mac_dinh", "kichThuoc": kich_thuoc})
            except Exception:
                pass

    current_user = _resolve_current_user_from_bearer(request, db)

    # Global custom templates (uploaded by admin)
    for tpl_path in CUSTOM_TEMPLATE_FOLDER.iterdir():
        if tpl_path.name == _USERS_TEMPLATE_DIRNAME:
            continue
        # Skip non-template files
        if tpl_path.is_file() and tpl_path.suffix in ('.j2', '.cls', '.bst'):
            continue
        # Skip anything matching a default/support name
        if tpl_path.stem in HIDDEN or tpl_path.name in HIDDEN:
            continue

        if tpl_path.is_file() and tpl_path.suffix == '.tex':
            templates.append(
                _template_metadata(
                    template_id=f"{_GLOBAL_TEMPLATE_PREFIX}{tpl_path.stem}",
                    ten=tpl_path.stem,
                    kich_thuoc=tpl_path.stat().st_size,
                    pham_vi="global",
                    co_the_xoa=current_user is not None and (current_user.role or "user").lower() == "admin",
                )
            )
        elif tpl_path.is_dir():
            # Xac thuc: phai co it nhat 1 file .tex (uu tien tim_file_tex_chinh,
            # fallback ve bat ky .tex de thu muc loi van hien thi tren UI)
            has_tex = False
            try:
                tim_file_tex_chinh(str(tpl_path))
                has_tex = True
            except Exception:
                has_tex = any(tpl_path.rglob("*.tex"))
                if not has_tex:
                    in_log_loi(f"Template thư mục không hợp lệ (không có .tex): {tpl_path.name}")
            if has_tex:
                kich_thuoc = sum(f.stat().st_size for f in tpl_path.rglob('*') if f.is_file())
                templates.append(
                    _template_metadata(
                        template_id=f"{_GLOBAL_TEMPLATE_PREFIX}{tpl_path.name}",
                        ten=tpl_path.name,
                        kich_thuoc=kich_thuoc,
                        pham_vi="global",
                        co_the_xoa=current_user is not None and (current_user.role or "user").lower() == "admin",
                    )
                )

    # Private templates for current user only
    if current_user is not None:
        user_dir = _user_template_base(current_user.id)
        if user_dir.exists() and user_dir.is_dir():
            for tpl_path in user_dir.iterdir():
                if tpl_path.is_file() and tpl_path.suffix == '.tex':
                    templates.append(
                        _template_metadata(
                            template_id=f"{_PRIVATE_TEMPLATE_PREFIX}{current_user.id}_{tpl_path.stem}",
                            ten=f"{tpl_path.stem} (cá nhân)",
                            kich_thuoc=tpl_path.stat().st_size,
                            pham_vi="private",
                            owner_user_id=current_user.id,
                        )
                    )
                elif tpl_path.is_dir():
                    kich_thuoc = sum(f.stat().st_size for f in tpl_path.rglob('*') if f.is_file())
                    templates.append(
                        _template_metadata(
                            template_id=f"{_PRIVATE_TEMPLATE_PREFIX}{current_user.id}_{tpl_path.name}",
                            ten=f"{tpl_path.name} (cá nhân)",
                            kich_thuoc=kich_thuoc,
                            pham_vi="private",
                            owner_user_id=current_user.id,
                        )
                    )

    return JSONResponse(
        content={"templates": templates},
        headers={"Cache-Control": "no-store"}
    )


@router.post("/upload")
async def tai_len_template(
    file: UploadFile = File(...),
    current_user: models.User = Depends(auth.lay_nguoi_dung_hien_tai),
) -> dict:
    """Upload template LaTeX tùy chỉnh (hỗ trợ .tex và .zip)"""
    is_zip = file.filename.lower().endswith('.zip')
    if not (file.filename.lower().endswith('.tex') or is_zip):
        raise HTTPException(status_code=400, detail="Chỉ chấp nhận file .tex hoặc .zip")
    
    contents = await file.read()
    if len(contents) > MAX_TEMPLATE_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File template quá lớn (tối đa {MAX_TEMPLATE_UPLOAD_MB}MB)")
    
    role = (current_user.role or "user").lower()
    la_admin = role == "admin"
    safe_name = _sanitize_template_name(Path(file.filename).stem)

    if la_admin:
        if safe_name in _RESERVED_UPLOAD_NAMES:
            safe_name = f"{safe_name}_custom"
        global_tex, global_dir = _global_template_paths(safe_name)
        safe_name = _ensure_unique_name_for_scope(safe_name, global_tex, global_dir)
        save_tex_path, save_dir_path = _global_template_paths(safe_name)
        template_id = f"{_GLOBAL_TEMPLATE_PREFIX}{safe_name}"
        pham_vi = "global"
    else:
        user_tex, user_dir = _user_template_paths(current_user.id, safe_name)
        safe_name = _ensure_unique_name_for_scope(safe_name, user_tex, user_dir)
        save_tex_path, save_dir_path = _user_template_paths(current_user.id, safe_name)
        save_tex_path.parent.mkdir(parents=True, exist_ok=True)
        template_id = f"{_PRIVATE_TEMPLATE_PREFIX}{current_user.id}_{safe_name}"
        pham_vi = "private"
    
    if not is_zip:
        text = contents.decode('utf-8', errors='ignore')
        if '\\documentclass' not in text and '\\begin{document}' not in text:
            raise HTTPException(status_code=400, detail="File không phải template LaTeX hợp lệ")
        with open(save_tex_path, 'wb') as f:
            f.write(contents)
    else:
        # Xử lý file zip
        target_dir = save_dir_path
        target_dir.mkdir(parents=True, exist_ok=True)

        try:
            _safe_extract_template_zip(contents, target_dir)
        except HTTPException:
            shutil.rmtree(target_dir, ignore_errors=True)
            raise
        except Exception:
            shutil.rmtree(target_dir, ignore_errors=True)
            raise HTTPException(status_code=400, detail="File ZIP không hợp lệ")
                
        # Nếu zip chỉ chứa 1 thư mục duy nhất thì dời các file ra ngoài
        extracted_items = list(target_dir.iterdir())
        if len(extracted_items) == 1 and extracted_items[0].is_dir():
            inner_dir = extracted_items[0]
            for item in inner_dir.iterdir():
                shutil.move(str(item), str(target_dir / item.name))
            inner_dir.rmdir()
                
        # Kiểm tra file .tex chính
        has_main_tex = False
        for f in target_dir.rglob("*.tex"):
            text = doc_noi_dung_tex_an_toan(f)
            if '\\documentclass' in text and '\\begin{document}' in text:
                has_main_tex = True
                break
        if not has_main_tex:
            shutil.rmtree(target_dir, ignore_errors=True)
            raise HTTPException(status_code=400, detail="Không tìm thấy file .tex chính (có chứa documentclass) trong thư mục ZIP")

    return {
        "thanhCong": True,
        "template": {
            "id": template_id,
            "ten": safe_name if pham_vi == "global" else f"{safe_name} (cá nhân)",
            "loai": "tuy_chinh",
            "phamVi": pham_vi,
            "ownerUserId": current_user.id if pham_vi == "private" else None,
            "coTheXoa": True,
            "kichThuoc": len(contents)
        },
        "message": f"Đã tải lên template: {safe_name}"
    }


@router.delete("/{template_id}")
def xoa_template(
    template_id: str,
    current_user: models.User = Depends(auth.lay_nguoi_dung_hien_tai),
) -> dict:
    """Xóa một template tùy chỉnh"""
    scope, owner_user_id, name = _parse_custom_template_id(template_id)

    role = (current_user.role or "user").lower()
    la_admin = role == "admin"
    if scope == "global" and not la_admin:
        raise HTTPException(status_code=403, detail="Bạn không có quyền xóa template global")
    if scope == "private" and owner_user_id != current_user.id and not la_admin:
        raise HTTPException(status_code=403, detail="Bạn không có quyền xóa template của người dùng khác")

    if scope == "global":
        file_path, dir_path = _global_template_paths(name)
    else:
        if owner_user_id is None:
            raise HTTPException(status_code=400, detail="Template private không hợp lệ")
        file_path, dir_path = _user_template_paths(owner_user_id, name)
    
    if file_path.exists():
        file_path.unlink()
    elif dir_path.exists() and dir_path.is_dir():
        shutil.rmtree(dir_path, ignore_errors=True)
    else:
        raise HTTPException(status_code=404, detail="Template không tồn tại")

    # Nếu xóa private template làm thư mục user rỗng, dọn nhẹ.
    if scope == "private" and owner_user_id is not None:
        user_dir = _user_template_base(owner_user_id)
        try:
            if user_dir.exists() and user_dir.is_dir() and not any(user_dir.iterdir()):
                user_dir.rmdir()
        except Exception:
            pass
    
    return {"thanhCong": True, "message": f"Đã xóa template: {name}"}
