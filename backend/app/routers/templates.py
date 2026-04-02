"""
templates.py
Định nghĩa các API liên quan đến quản lý, tải lên mẫu LaTeX (Templates).
"""

import shutil
import zipfile
from io import BytesIO
from pathlib import Path
from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse

from ..config import CUSTOM_TEMPLATE_FOLDER
from ..utils.api_utils import doc_noi_dung_tex_an_toan, in_log_loi

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


def _safe_extract_template_zip(zip_bytes: bytes, target_dir: Path):
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
def lay_danh_sach_template():
    """Lấy danh sách template LaTeX mặc định và tùy chỉnh (không cache)."""
    
    # Import find_main_tex local để tránh import cycles
    from backend.core_engine.utils import find_main_tex
    
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
                find_main_tex(str(dir_path))  # validate
                kich_thuoc = sum(f.stat().st_size for f in dir_path.rglob('*') if f.is_file())
                templates.append({"id": tpl_id, "ten": tpl_label, "loai": "mac_dinh", "kichThuoc": kich_thuoc})
            except Exception:
                pass

    # Custom templates uploaded by users
    for tpl_path in CUSTOM_TEMPLATE_FOLDER.iterdir():
        # Skip non-template files
        if tpl_path.is_file() and tpl_path.suffix in ('.j2', '.cls', '.bst'):
            continue
        # Skip anything matching a default/support name
        if tpl_path.stem in HIDDEN or tpl_path.name in HIDDEN:
            continue

        if tpl_path.is_file() and tpl_path.suffix == '.tex':
            templates.append({
                "id": f"custom_{tpl_path.stem}",
                "ten": tpl_path.stem,
                "loai": "tuy_chinh",
                "kichThuoc": tpl_path.stat().st_size
            })
        elif tpl_path.is_dir():
            # Validate: must have at least one .tex file (find_main_tex preferred,
            # fallback to any .tex so silently-broken dirs still surface in UI)
            has_tex = False
            try:
                find_main_tex(str(tpl_path))
                has_tex = True
            except Exception:
                has_tex = any(tpl_path.rglob("*.tex"))
                if not has_tex:
                    in_log_loi(f"Template thư mục không hợp lệ (không có .tex): {tpl_path.name}")
            if has_tex:
                kich_thuoc = sum(f.stat().st_size for f in tpl_path.rglob('*') if f.is_file())
                templates.append({
                    "id": f"custom_{tpl_path.name}",
                    "ten": tpl_path.name,
                    "loai": "tuy_chinh",
                    "kichThuoc": kich_thuoc
                })

    return JSONResponse(
        content={"templates": templates},
        headers={"Cache-Control": "no-store"}
    )


@router.post("/upload")
async def tai_len_template(file: UploadFile = File(...)):
    """Upload template LaTeX tùy chỉnh (hỗ trợ .tex và .zip)"""
    is_zip = file.filename.lower().endswith('.zip')
    if not (file.filename.lower().endswith('.tex') or is_zip):
        raise HTTPException(status_code=400, detail="Chỉ chấp nhận file .tex hoặc .zip")
    
    contents = await file.read()
    if len(contents) > 20 * 1024 * 1024:  # 20MB
        raise HTTPException(status_code=400, detail="File template quá lớn (tối đa 20MB)")
    
    safe_name = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in Path(file.filename).stem)
    safe_name = safe_name.strip('_') or "template"

    # Prevent collisions with reserved/builtin names — append suffix until unique
    if safe_name in _RESERVED_UPLOAD_NAMES:
        counter = 2
        candidate = f"{safe_name}_custom"
        while (CUSTOM_TEMPLATE_FOLDER / candidate).exists() or (CUSTOM_TEMPLATE_FOLDER / f"{candidate}.tex").exists():
            candidate = f"{safe_name}_custom{counter}"
            counter += 1
        safe_name = candidate
    
    if not is_zip:
        text = contents.decode('utf-8', errors='ignore')
        if '\\documentclass' not in text and '\\begin{document}' not in text:
            raise HTTPException(status_code=400, detail="File không phải template LaTeX hợp lệ")
        save_path = CUSTOM_TEMPLATE_FOLDER / f"{safe_name}.tex"
        with open(save_path, 'wb') as f:
            f.write(contents)
    else:
        # Xử lý file zip
        target_dir = CUSTOM_TEMPLATE_FOLDER / safe_name
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
            "id": f"custom_{safe_name}",
            "ten": safe_name,
            "loai": "tuy_chinh",
            "kichThuoc": len(contents)
        },
        "message": f"Đã tải lên template: {safe_name}"
    }


@router.delete("/{template_id}")
def xoa_template(template_id: str):
    """Xóa một template tùy chỉnh"""
    if not template_id.startswith("custom_"):
        raise HTTPException(status_code=400, detail="Không thể xóa template mặc định")
    
    name = template_id.replace("custom_", "", 1)
    file_path = CUSTOM_TEMPLATE_FOLDER / f"{name}.tex"
    dir_path = CUSTOM_TEMPLATE_FOLDER / name
    
    if file_path.exists():
        file_path.unlink()
    elif dir_path.exists() and dir_path.is_dir():
        shutil.rmtree(dir_path, ignore_errors=True)
    else:
        raise HTTPException(status_code=404, detail="Template không tồn tại")
    
    return {"thanhCong": True, "message": f"Đã xóa template: {name}"}
