import os
import sys
import uuid
import shutil
import zipfile
import time
import json
import asyncio
import re
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, HTTPException, Query, BackgroundTasks, Request
from fastapi.responses import FileResponse, JSONResponse, Response, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel
from sqlalchemy.orm import Session
from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm

import database
import models
import auth

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from chuyen_doi import ChuyenDoiWordSangLatex
from utils import don_dep_file_rac, bien_dich_latex, find_main_tex, extract_zip_template, package_output_directory
from tex_log_parser import parse_latex_log
from template_preprocessor import TemplatePreprocessor

# Khởi tạo FastAPI app
app = FastAPI(title="Word2LaTeX API", version="1.0.0")

# Khởi tạo database
models.Base.metadata.create_all(bind=database.engine)

# Cấu hình CORS - cho phép frontend truy cập (hỗ trợ nhiều port)
cors_allow_all = os.getenv('CORS_ALLOW_ALL', '0').strip() == '1'
cors_origins_raw = os.getenv('CORS_ORIGINS', '').strip()
cors_origins = [o.strip() for o in cors_origins_raw.split(',') if o.strip()]
if not cors_origins:
    cors_origins = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:5173",
        "http://localhost:5174",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if cors_allow_all else cors_origins,
    allow_credentials=False if cors_allow_all else True,
    allow_methods=["*"],
    allow_headers=["*"],
)

base_dir = Path(__file__).parent.parent
template_folder = base_dir / "input_data"
custom_template_folder = base_dir / "backend" / "custom_templates"
temp_folder = base_dir / "temp_jobs"
outputs_folder = base_dir / "outputs"

custom_template_folder.mkdir(parents=True, exist_ok=True)
temp_folder.mkdir(parents=True, exist_ok=True)
outputs_folder.mkdir(parents=True, exist_ok=True)


def in_log_loi(thong_diep: str, loi: Exception = None):
    # In log lỗi ra console để developer dễ debug
    if loi is not None:
        print(f"[LOI] {thong_diep}: {loi}")
    else:
        print(f"[LOI] {thong_diep}")


def doc_noi_dung_tex_an_toan(duong_dan: Path) -> str:
    # Đọc nội dung .tex an toàn với fallback encoding
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


def xoa_thu_muc_an_toan(duong_dan: Path):
    # Xóa thư mục an toàn và không làm crash server nếu lỗi
    try:
        if duong_dan.exists():
            shutil.rmtree(duong_dan, ignore_errors=True)
    except Exception as loi:
        in_log_loi(f"Không thể xóa thư mục: {duong_dan}", loi)


async def don_dep_sau_thoi_gian(duong_dan: Path, giay: int = 3600):
    # Dọn dẹp thư mục job sau TTL (mặc định 1 giờ) để user có thời gian tải ZIP
    try:
        await asyncio.sleep(giay)
    except Exception as loi:
        in_log_loi(f"Lỗi sleep cleanup: {duong_dan}", loi)
    xoa_thu_muc_an_toan(duong_dan)


# Alias backward-compatible
async def don_dep_sau_15_phut(duong_dan: Path):
    await don_dep_sau_thoi_gian(duong_dan, 900)





def quet_xoa_thu_muc_mo_coi(thu_muc_goc: Path, so_gio_ton_tai_toi_da: int):
    # Quét và xóa các thư mục/file cũ còn tồn đọng để tránh tràn ổ đĩa
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


# ── BUILT-IN TEMPLATE RESOLVER ───────────────────────────────────────────────
# Directory-based templates live in custom_templates/<name>/.
# Legacy flat .tex templates (onecolumn, elsarticle) keep their .tex extension
# so the resolver also handles them transparently.

_BUILTIN_TEMPLATE_MAP = {
    "ieee_conference":  "IEEE-conference-template-062824",
    "twocolumn":        "IEEE-conference-template-062824",
    "springer_lncs":    "LaTeX2e_Proceedings_Templates_download__1",
    "onecolumn":        "latex_template_onecolumn.tex",
    "elsarticle":       "elsarticle-template-harv.tex",
}

def _resolve_template_path(template_type: str) -> Path | None:
    """Resolve a built-in template type → absolute path of the main .tex file."""
    tpl_name = _BUILTIN_TEMPLATE_MAP.get(template_type)
    if not tpl_name:
        return None
    if tpl_name.endswith(".tex"):
        # Legacy flat-file template
        for probe in (custom_template_folder / tpl_name, template_folder / tpl_name):
            if probe.exists():
                return probe
        return None
    # Directory-based template
    dir_path = custom_template_folder / tpl_name
    if dir_path.is_dir():
        try:
            return Path(find_main_tex(str(dir_path)))
        except FileNotFoundError:
            return next(dir_path.rglob("*.tex"), None)
    # Fallback: try flat .tex with the same stem
    for probe in (custom_template_folder / f"{tpl_name}.tex", template_folder / f"{tpl_name}.tex"):
        if probe.exists():
            return probe
    return None


@app.get("/")
def doc_api():
    # Endpoint gốc - hướng dẫn sử dụng API
    return {
        "message": "Word2LaTeX API đang hoạt động",
        "endpoints": {
        "/api/chuyen-doi": "POST - Upload file .docx/.docm và chuyển đổi",
            "/docs": "Xem Swagger documentation"
        }
    }


@app.get("/api/templates")
def lay_danh_sach_template():
    # Luôn đọc trực tiếp từ disk — KHÔNG cache trong memory
    templates = []

    # Built-in templates shown to every user (directory-based)
    BUILTIN = [
        ("ieee_conference", "IEEE Conference (2 cột)",  "IEEE-conference-template-062824"),
        ("springer_lncs",  "Springer LNCS",             "LaTeX2e_Proceedings_Templates_download__1"),
    ]

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

    for tpl_id, tpl_label, tpl_dir in BUILTIN:
        dir_path = custom_template_folder / tpl_dir
        if dir_path.is_dir():
            try:
                find_main_tex(str(dir_path))  # validate
                kich_thuoc = sum(f.stat().st_size for f in dir_path.rglob('*') if f.is_file())
                templates.append({"id": tpl_id, "ten": tpl_label, "loai": "mac_dinh", "kichThuoc": kich_thuoc})
            except Exception:
                pass

    # Custom templates uploaded by users
    for tpl_path in custom_template_folder.iterdir():
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


# Reserved directory names that must not be overwritten by user uploads
_RESERVED_UPLOAD_NAMES = {
    "IEEE-conference-template-062824",
    "LaTeX2e_Proceedings_Templates_download__1",
    "LaTeX2e_Proceedings_Templates_download__1_",
    "samplepaper_springer_", "samplepaper_springer",
    "samplepaper", "latex_template_onecolumn",
    "elsarticle-template-harv", "elsarticle-template-num",
    "IEEEtran", "llncs",
}


@app.post("/api/templates/upload")
async def tai_len_template(file: UploadFile = File(...)):
    # Upload template LaTeX tùy chỉnh (hỗ trợ .tex và .zip)
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
        while (custom_template_folder / candidate).exists() or (custom_template_folder / f"{candidate}.tex").exists():
            candidate = f"{safe_name}_custom{counter}"
            counter += 1
        safe_name = candidate
    
    if not is_zip:
        text = contents.decode('utf-8', errors='ignore')
        if '\\documentclass' not in text and '\\begin{document}' not in text:
            raise HTTPException(status_code=400, detail="File không phải template LaTeX hợp lệ")
        save_path = custom_template_folder / f"{safe_name}.tex"
        with open(save_path, 'wb') as f:
            f.write(contents)
    else:
        # Xử lý file zip
        target_dir = custom_template_folder / safe_name
        target_dir.mkdir(parents=True, exist_ok=True)
        zip_path = target_dir / "temp.zip"
        with open(zip_path, 'wb') as f:
            f.write(contents)
            
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(target_dir)
        except Exception as e:
            shutil.rmtree(target_dir, ignore_errors=True)
            raise HTTPException(status_code=400, detail="File ZIP không hợp lệ")
        finally:
            if zip_path.exists():
                zip_path.unlink()
                
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


@app.delete("/api/templates/{template_id}")
def xoa_template(template_id: str):
    # Xóa template tùy chỉnh
    if not template_id.startswith("custom_"):
        raise HTTPException(status_code=400, detail="Không thể xóa template mặc định")
    
    name = template_id.replace("custom_", "", 1)
    file_path = custom_template_folder / f"{name}.tex"
    dir_path = custom_template_folder / name
    
    if file_path.exists():
        file_path.unlink()
    elif dir_path.exists() and dir_path.is_dir():
        shutil.rmtree(dir_path, ignore_errors=True)
    else:
        raise HTTPException(status_code=404, detail="Template không tồn tại")
    
    return {"thanhCong": True, "message": f"Đã xóa template: {name}"}


@app.post("/api/chuyen-doi")
async def chuyen_doi_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    template_type: str = Query("ieee_conference", description="ieee_conference hoặc custom_xxx"),
    template_file: UploadFile = File(None, description="Tùy chọn: file .tex hoặc .zip chứa template")
):
    # Endpoint chuyển đổi file Word → LaTeX
    
    # Kiểm tra file extension — chấp nhận .docx và .docm
    ten_file = file.filename.lower()
    if not (ten_file.endswith('.docx') or ten_file.endswith('.docm')):
        raise HTTPException(
            status_code=400, 
            detail="Chỉ chấp nhận file .docx hoặc .docm"
        )
    
    # Kiểm tra kích thước file (max 10MB)
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:  # 10MB
        raise HTTPException(
            status_code=400,
            detail="File quá lớn. Kích thước tối đa 10MB"
        )
    
    job_id = str(uuid.uuid4())
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    print(f"[JOB {job_id}] Nhận yêu cầu chuyển đổi: {file.filename} template={template_type}")
    
    # Tạo tên file an toàn
    original_name = Path(file.filename).stem  # Tên không có extension
    safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in original_name)
    safe_name = safe_name.lstrip(" -_")
    if not safe_name:
        safe_name = "document"
    
    job_folder = temp_folder / f"job_{job_id}"
    job_folder.mkdir(parents=True, exist_ok=True)
    # Giữ đuôi file gốc (.docx hoặc .docm)
    file_ext = Path(file.filename).suffix.lower() or '.docx'
    input_filename = f"{safe_name}_{timestamp}{file_ext}"
    input_path = job_folder / input_filename
    output_filename = f"{safe_name}_{timestamp}.tex"
    output_path = job_folder / output_filename
    images_folder = job_folder / "images"
    images_folder.mkdir(parents=True, exist_ok=True)

    with open(input_path, "wb") as f:
        f.write(contents)
    
    template_path = None
    
    # 1. Ưu tiên sử dụng file template được upload trực tiếp
    if template_file:
        is_zip = template_file.filename.lower().endswith('.zip')
        template_contents = await template_file.read()
        
        if is_zip:
            zip_path = job_folder / "uploaded_template.zip"
            with open(zip_path, "wb") as f:
                f.write(template_contents)
            try:
                extract_zip_template(str(zip_path), str(job_folder))
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"File ZIP template không hợp lệ: {e}")
            finally:
                if zip_path.exists():
                    zip_path.unlink()

            # Tìm file .tex chính bằng hàm tiện ích (đệ quy + blacklist + ưu tiên main.tex)
            try:
                template_path = Path(find_main_tex(str(job_folder)))
            except FileNotFoundError:
                raise HTTPException(status_code=400, detail="Không tìm thấy file .tex chính (có chứa \\documentclass) trong ZIP")

            # Nếu file .tex chính nằm ở thư mục con, copy các file dependency (.cls, .sty, .bst, hình ảnh)
            # lên job_folder để trình biên dịch xelatex nhìn thấy chúng.
            template_tex_dir = template_path.parent
            if template_tex_dir != job_folder:
                print(f"[INFO] File .tex chính nằm trong thư mục con: {template_tex_dir.relative_to(job_folder)}")
                dep_extensions = {'.cls', '.sty', '.bst', '.png', '.jpg', '.jpeg', '.pdf', '.eps', '.bib'}
                for item in template_tex_dir.rglob("*"):
                    if item.is_file() and item.suffix.lower() in dep_extensions:
                        target_file = job_folder / item.relative_to(template_tex_dir)
                        target_file.parent.mkdir(parents=True, exist_ok=True)
                        if not target_file.exists():
                            shutil.copy2(item, target_file)
                # Copy file .tex chính ra job_folder để compiler cwd đúng
                main_tex_dest = job_folder / template_path.name
                if not main_tex_dest.exists():
                    shutil.copy2(template_path, main_tex_dest)
                template_path = main_tex_dest
        else:
            # Upload file .tex đơn
            template_path = job_folder / "custom_uploaded_template.tex"
            with open(template_path, "wb") as f:
                f.write(template_contents)
                
    # 2. Xử lý template theo template_type (nếu không upload file)
    else:
        if template_type.startswith("custom_"):
            custom_name = template_type.replace("custom_", "", 1)
            temp_file = custom_template_folder / f"{custom_name}.tex"
            temp_dir = custom_template_folder / custom_name

            if temp_file.exists():
                template_path = temp_file
            elif temp_dir.exists() and temp_dir.is_dir():
                try:
                    template_path = Path(find_main_tex(str(temp_dir)))
                except FileNotFoundError:
                    template_path = next(temp_dir.rglob("*.tex"), None)
            else:
                raise HTTPException(status_code=500, detail="Template tùy chỉnh không tồn tại")
        else:
            template_path = _resolve_template_path(template_type) or _resolve_template_path("ieee_conference")
        
        if not template_path or not template_path.exists():
            raise HTTPException(
                status_code=500,
                detail=f"Template không tồn tại hoặc lỗi cấu trúc thư mục."
            )
        
        # Copy các file dependencies (.cls, .sty, .bst, fonts, images, etc.) sang thư mục job_folder
        _DEP_EXTENSIONS = {
            '.cls', '.sty', '.bst', '.bib', '.bbx', '.cbx', '.lbx', '.dbx',
            '.fd', '.cfg', '.def',
            '.png', '.jpg', '.jpeg', '.pdf', '.eps', '.gif', '.svg',
            '.ttf', '.otf', '.pfb', '.tfm',
        }
        template_dir_actual = template_path.parent
        for item in template_dir_actual.rglob("*"):
            if item.is_file() and item.suffix.lower() in _DEP_EXTENSIONS:
                try:
                    target_file = job_folder / item.relative_to(template_dir_actual)
                    target_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, target_file)
                except Exception as e:
                    print(f"[WARN] Lỗi khi copy dependency {item.name}: {e}")
        
        # Copy template .tex sang job_folder để chuyen_doi sinh .j2 trong job folder (không ô nhiễm custom_templates/)
        template_dest = job_folder / template_path.name
        if not template_dest.exists():
            shutil.copy2(template_path, template_dest)
        template_path = template_dest

    zip_filename = output_filename.replace('.tex', '.zip')
    zip_path = job_folder / zip_filename

    da_thanh_cong = False

    try:
        thoi_gian_bat_dau = time.time()
        print(f"[JOB {job_id}] Bắt đầu chuyển đổi Word → LaTeX")
        bo_chuyen_doi = ChuyenDoiWordSangLatex(
            duong_dan_word=str(input_path),
            duong_dan_template=str(template_path),
            duong_dan_dau_ra=str(output_path),
            thu_muc_anh=str(images_folder),
            mode='demo'
        )
        bo_chuyen_doi.chuyen_doi()

        print(f"[JOB {job_id}] Đã tạo file .tex, bắt đầu biên dịch PDF")

        # POST-PROCESSING: Thay đường dẫn ảnh tuyệt đối bằng đường dẫn tương đối
        # Overleaf không thể đọc đường dẫn tuyệt đối (d:/, c:/, /tmp/...)
        try:
            tex_raw = output_path.read_text(encoding='utf-8', errors='ignore')
            images_abs = str(images_folder).replace('\\', '/')
            job_abs = str(job_folder).replace('\\', '/')
            # Thay thế đường dẫn tuyệt đối thư mục images bằng "images"
            tex_raw = tex_raw.replace(images_abs + '/', 'images/')
            tex_raw = tex_raw.replace(images_abs, 'images')
            # Thay thế đường dẫn tuyệt đối thư mục job bằng ""
            tex_raw = tex_raw.replace(job_abs + '/', '')
            tex_raw = tex_raw.replace(job_abs, '')
            # Cũng xử lý backslash paths trên Windows
            images_abs_win = str(images_folder).replace('/', '\\')
            job_abs_win = str(job_folder).replace('/', '\\')
            tex_raw = tex_raw.replace(images_abs_win + '\\', 'images/')
            tex_raw = tex_raw.replace(images_abs_win, 'images')
            tex_raw = tex_raw.replace(job_abs_win + '\\', '')
            tex_raw = tex_raw.replace(job_abs_win, '')
            output_path.write_text(tex_raw, encoding='utf-8')
            print(f"[JOB {job_id}] POST-PROCESS: Đã thay thế đường dẫn tuyệt đối → tương đối")
        except Exception as e:
            print(f"[WARN] Không thể post-process đường dẫn ảnh: {e}")

        thanh_cong, thong_bao_loi = bien_dich_latex(str(output_path))
        
        if not thanh_cong:
            print(f"[JOB {job_id}] CẢNH BÁO: Biên dịch Xelatex thất bại.")
            # Tìm kiếm lỗi thiếu file LaTeX (.cls, .sty)
            missing_file_match = re.search(r"! LaTeX Error: File `(.*?)' not found.", thong_bao_loi)
            if missing_file_match:
                ten_file_thieu = missing_file_match.group(1)
                raise Exception(f"Thiếu thư viện cấu trúc LaTeX: '{ten_file_thieu}'. Vui lòng tải {ten_file_thieu} vào thư mục chứa template này.")
                
            # Dùng NLP/Regex bóc xuất nguyên nhân Visual Debugger
            chi_tiet_loi = parse_latex_log(thong_bao_loi)
            # Serialize thành JSON string để HTTP exception có thể chuyên chở được data cấu trúc phức tạp
            raise HTTPException(
                status_code=422,
                detail=json.dumps(chi_tiet_loi, ensure_ascii=False)
            )

        print(f"[JOB {job_id}] Đã chạy xelatex, đọc log/metadata")

        so_trang = None
        try:
            log_path = output_path.with_suffix('.log')
            if log_path.exists():
                log_text = log_path.read_text(encoding='utf-8', errors='ignore')
                match = re.search(r'Output written on .*?\((\d+) pages?[,\)]', log_text, re.DOTALL)
                if match:
                    so_trang = int(match.group(1))
        except Exception as loi:
            print(f"[WARN] Không thể lấy số trang từ log job_id={job_id}: {loi}")

        # Tránh trả về 0 trang nếu PDF đã tồn tại nhưng không parse được log
        pdf_path = output_path.with_suffix('.pdf')
        if so_trang is None and pdf_path.exists():
            so_trang = 1  # Fallback tối thiểu
            # Thử đọc trực tiếp binary PDF để đếm thẻ /Type/Page
            try:
                import re as regex_pdf
                with open(pdf_path, 'rb') as f:
                    pdf_data = f.read()
                    pages_found = len(regex_pdf.findall(b'/Type\\s*/Page\\b', pdf_data))
                    if pages_found > 0:
                        so_trang = pages_found
            except:
                pass

        don_dep_file_rac(str(output_path))

        print(f"[JOB {job_id}] Đã dọn file rác, chuẩn bị zip")

        if not output_path.exists():
            raise Exception("Không tạo được file .tex đầu ra")

        tex_raw = output_path.read_text(encoding='utf-8', errors='ignore')
        if not tex_raw.strip():
            raise Exception("Nội dung LaTeX rỗng hoặc không đọc được")

        so_hinh_anh = 0
        so_cong_thuc = 0
        so_bang = 0
        try:
            so_hinh_anh = len(re.findall(r'\\includegraphics', tex_raw))
            so_bang = len(re.findall(r'\\begin\{table', tex_raw))

            # Ưu tiên dùng total_formulas từ AST IR (chính xác hơn regex)
            ir = getattr(bo_chuyen_doi, 'ir', None)
            if ir and ir.get("metadata", {}).get("total_formulas", 0) > 0:
                so_cong_thuc = ir["metadata"]["total_formulas"]
            else:
                so_equation_env = len(re.findall(r'\\begin\{(equation\*?|align\*?|eqnarray\*?)\}', tex_raw))
                so_bracket_math = len(re.findall(r'\\\[', tex_raw))
                so_inline_math = len(re.findall(r'\\\(', tex_raw))
                so_dollar_blocks = len(re.findall(r'\$\$', tex_raw)) // 2
                so_cong_thuc = so_equation_env + so_bracket_math + so_inline_math + so_dollar_blocks
        except Exception as loi:
            print(f"[WARN] Không thể đếm metadata job_id={job_id}: {loi}")

        thoi_gian_xu_ly_giay = max(0.0, time.time() - thoi_gian_bat_dau)

        # Đóng gói TOÀN BỘ thư mục job thành ZIP (Overleaf-ready)
        # Bao gồm: .tex render, .pdf, images, .cls, .sty, .bst, .bib, v.v.
        # Loại trừ: file rác LaTeX (.aux, .log), file Word gốc (.docx, .docm)
        package_output_directory(str(job_folder), str(zip_path), generated_tex_name=output_filename)

        print(f"[JOB {job_id}] Hoàn tất zip: {zip_path.name}")

        tex_content = tex_raw

        da_thanh_cong = True
        background_tasks.add_task(don_dep_sau_15_phut, job_folder)

        # Lưu copy vào thư mục outputs để người dùng dễ theo dõi
        try:
            shutil.copy2(zip_path, outputs_folder / zip_filename)
        except Exception as e:
            print(f"[WARN] Không thể copy kết quả vào outputs job_id={job_id}: {e}")

        return JSONResponse(status_code=200, content={
            "thanh_cong": True,
            "tex_content": tex_content,
            "job_id": job_id,
            "ten_file_zip": zip_filename,
            "ten_file_latex": output_filename,
            "metadata": {
                "so_trang": so_trang,
                "so_hinh_anh": so_hinh_anh,
                "so_cong_thuc": so_cong_thuc,
                "so_bang": so_bang,
                "thoi_gian_xu_ly_giay": round(thoi_gian_xu_ly_giay, 2)
            }
        })
    except HTTPException:
        raise
    except Exception as loi:
        print(f"[ERROR] Lỗi chuyển đổi job_id={job_id}: {loi}")
        thong_diep_loi = str(loi).strip() if str(loi) else "File Word không hợp lệ hoặc không thể xử lý"
        return JSONResponse(status_code=400, content={"error": f"Lỗi khi chuyển đổi: {thong_diep_loi}"})
    finally:
        if not da_thanh_cong:
             xoa_thu_muc_an_toan(job_folder)

# ========================= SSE REAL-TIME CONVERSION =========================

@app.post("/api/chuyen-doi-stream")
async def chuyen_doi_file_stream(
    background_tasks: BackgroundTasks,
    request: Request,
    file: UploadFile = File(...),
    template_type: str = Query("ieee_conference"),
    template_file: UploadFile = File(None),
    db: Session = Depends(database.get_db)
):
    """SSE endpoint: trả về Server-Sent Events cho tiến trình chuyển đổi real-time."""

    # --- Resolve user tùy chọn từ Bearer token ---
    current_user = None
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
        try:
            current_user = auth.get_current_user(token=token, db=db)
        except Exception:
            pass   # gọp lỗi token thì bỏ qua, không chặn yêu cầu

    ten_file = file.filename.lower()
    if not (ten_file.endswith('.docx') or ten_file.endswith('.docm')):
        raise HTTPException(status_code=400, detail="Chỉ chấp nhận file .docx hoặc .docm")

    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File quá lớn. Kích thước tối đa 10MB")

    template_contents = None
    template_filename = None
    if template_file:
        template_contents = await template_file.read()
        template_filename = template_file.filename

    async def event_generator():
        job_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        da_thanh_cong = False

        original_name = Path(file.filename).stem
        safe_name = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in original_name)
        safe_name = safe_name.strip('_') or "document"

        job_folder = temp_folder / f"job_{job_id}"
        job_folder.mkdir(parents=True, exist_ok=True)
        file_ext = Path(file.filename).suffix.lower() or '.docx'
        input_filename = f"{safe_name}_{timestamp}{file_ext}"
        input_path = job_folder / input_filename
        output_filename = f"{safe_name}_{timestamp}.tex"
        output_path = job_folder / output_filename
        images_folder = job_folder / "images"
        images_folder.mkdir(parents=True, exist_ok=True)

        def sse_event(step, msg, **extra):
            payload = {"step": step, "msg": msg, **extra}
            return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

        try:
            yield sse_event(1, "Đang tải file lên server...")

            with open(input_path, "wb") as f:
                f.write(contents)

            # --- Template resolution (giống endpoint gốc) ---
            template_path = None
            if template_contents:
                is_zip = template_filename and template_filename.lower().endswith('.zip')
                if is_zip:
                    zip_path = job_folder / "uploaded_template.zip"
                    with open(zip_path, "wb") as f:
                        f.write(template_contents)
                    try:
                        extract_zip_template(str(zip_path), str(job_folder))
                    except ValueError as e:
                        yield sse_event(-1, f"File ZIP template không hợp lệ: {e}", error=True)
                        return
                    finally:
                        if zip_path.exists():
                            zip_path.unlink()
                    try:
                        template_path = Path(find_main_tex(str(job_folder)))
                    except FileNotFoundError:
                        yield sse_event(-1, "Không tìm thấy file .tex chính trong ZIP", error=True)
                        return
                    template_tex_dir = template_path.parent
                    if template_tex_dir != job_folder:
                        dep_extensions = {'.cls', '.sty', '.bst', '.png', '.jpg', '.jpeg', '.pdf', '.eps', '.bib'}
                        for item in template_tex_dir.rglob("*"):
                            if item.is_file() and item.suffix.lower() in dep_extensions:
                                target_file = job_folder / item.relative_to(template_tex_dir)
                                target_file.parent.mkdir(parents=True, exist_ok=True)
                                if not target_file.exists():
                                    shutil.copy2(item, target_file)
                        main_tex_dest = job_folder / template_path.name
                        if not main_tex_dest.exists():
                            shutil.copy2(template_path, main_tex_dest)
                        template_path = main_tex_dest
                else:
                    template_path = job_folder / "custom_uploaded_template.tex"
                    with open(template_path, "wb") as f:
                        f.write(template_contents)
            else:
                if template_type.startswith("custom_"):
                    custom_name = template_type.replace("custom_", "", 1)
                    temp_file = custom_template_folder / f"{custom_name}.tex"
                    temp_dir = custom_template_folder / custom_name
                    if temp_file.exists(): template_path = temp_file
                    elif temp_dir.exists() and temp_dir.is_dir():
                        try: template_path = Path(find_main_tex(str(temp_dir)))
                        except FileNotFoundError: template_path = next(temp_dir.rglob("*.tex"), None)
                    else:
                        yield sse_event(-1, "Template tùy chỉnh không tồn tại", error=True)
                        return
                else:
                    template_path = _resolve_template_path(template_type) or _resolve_template_path("ieee_conference")

                if not template_path or not template_path.exists():
                    yield sse_event(-1, "Template không tồn tại", error=True)
                    return

                template_dir_actual = template_path.parent
                _DEP_EXTENSIONS = {
                    '.cls', '.sty', '.bst', '.bib', '.bbx', '.cbx', '.lbx', '.dbx',
                    '.fd', '.cfg', '.def',
                    '.png', '.jpg', '.jpeg', '.pdf', '.eps', '.gif', '.svg',
                    '.ttf', '.otf', '.pfb', '.tfm',
                }
                for item in template_dir_actual.rglob("*"):
                    if item.is_file() and item.suffix.lower() in _DEP_EXTENSIONS:
                        try:
                            target_file = job_folder / item.relative_to(template_dir_actual)
                            target_file.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(item, target_file)
                        except Exception:
                            pass
                template_dest = job_folder / template_path.name
                if not template_dest.exists():
                    shutil.copy2(template_path, template_dest)
                template_path = template_dest

            yield sse_event(2, "Đang xây dựng cây AST & Phân tích ngữ nghĩa...")

            thoi_gian_bat_dau = time.time()
            bo_chuyen_doi = ChuyenDoiWordSangLatex(
                duong_dan_word=str(input_path),
                duong_dan_template=str(template_path),
                duong_dan_dau_ra=str(output_path),
                thu_muc_anh=str(images_folder),
                mode='demo'
            )

            yield sse_event(3, "Đang nạp dữ liệu vào template Jinja2...")
            bo_chuyen_doi.chuyen_doi()

            # Post-process: đường dẫn tuyệt đối → tương đối
            try:
                tex_raw = output_path.read_text(encoding='utf-8', errors='ignore')
                images_abs = str(images_folder).replace('\\', '/')
                job_abs = str(job_folder).replace('\\', '/')
                tex_raw = tex_raw.replace(images_abs + '/', 'images/')
                tex_raw = tex_raw.replace(images_abs, 'images')
                tex_raw = tex_raw.replace(job_abs + '/', '')
                tex_raw = tex_raw.replace(job_abs, '')
                images_abs_win = str(images_folder).replace('/', '\\')
                job_abs_win = str(job_folder).replace('/', '\\')
                tex_raw = tex_raw.replace(images_abs_win + '\\', 'images/')
                tex_raw = tex_raw.replace(images_abs_win, 'images')
                tex_raw = tex_raw.replace(job_abs_win + '\\', '')
                tex_raw = tex_raw.replace(job_abs_win, '')
                output_path.write_text(tex_raw, encoding='utf-8')
            except Exception:
                pass

            yield sse_event(4, "Đang biên dịch XeLaTeX (Sẽ mất vài giây)...")

            thanh_cong, thong_bao_loi = bien_dich_latex(str(output_path))

            if not thanh_cong:
                # Structured error with Visual Debugger info
                missing_file_match = re.search(r"! LaTeX Error: File `(.*?)' not found.", thong_bao_loi)
                if missing_file_match:
                    yield sse_event(-1, f"Thiếu thư viện: '{missing_file_match.group(1)}'",
                                    error=True, error_type="MISSING_FILE")
                    return

                chi_tiet_loi = parse_latex_log(thong_bao_loi)
                yield sse_event(-1, chi_tiet_loi.get("thong_diep", "Biên dịch thất bại"),
                                error=True,
                                error_type="LATEX_COMPILATION_FAILED",
                                details=chi_tiet_loi)
                return

            yield sse_event(5, "Đang đóng gói kết quả...")

            # Metadata
            so_trang = None
            try:
                log_path = output_path.with_suffix('.log')
                if log_path.exists():
                    log_text = log_path.read_text(encoding='utf-8', errors='ignore')
                    match = re.search(r'Output written on .*?\((\d+) pages?[,\)]', log_text, re.DOTALL)
                    if match:
                        so_trang = int(match.group(1))
            except Exception:
                pass

            pdf_path = output_path.with_suffix('.pdf')
            if so_trang is None and pdf_path.exists():
                so_trang = 1
                try:
                    with open(pdf_path, 'rb') as f:
                        pdf_data = f.read()
                        pages_found = len(re.findall(b'/Type\\s*/Page\\b', pdf_data))
                        if pages_found > 0:
                            so_trang = pages_found
                except Exception:
                    pass

            don_dep_file_rac(str(output_path))

            tex_raw = output_path.read_text(encoding='utf-8', errors='ignore')
            so_hinh_anh = len(re.findall(r'\\includegraphics', tex_raw))
            so_bang = len(re.findall(r'\\begin\{table', tex_raw))

            # Ưu tiên dùng total_formulas từ AST IR (chính xác hơn regex)
            ir = getattr(bo_chuyen_doi, 'ir', None)
            if ir and ir.get("metadata", {}).get("total_formulas", 0) > 0:
                so_cong_thuc = ir["metadata"]["total_formulas"]
            else:
                so_equation_env = len(re.findall(r'\\begin\{(equation\*?|align\*?|eqnarray\*?)\}', tex_raw))
                so_bracket_math = len(re.findall(r'\\\[', tex_raw))
                so_inline_math = len(re.findall(r'\\\(', tex_raw))
                so_dollar_blocks = len(re.findall(r'\$\$', tex_raw)) // 2
                so_cong_thuc = so_equation_env + so_bracket_math + so_inline_math + so_dollar_blocks
            thoi_gian_xu_ly_giay = max(0.0, time.time() - thoi_gian_bat_dau)

            zip_filename = output_filename.replace('.tex', '.zip')
            zip_path = job_folder / zip_filename
            package_output_directory(str(job_folder), str(zip_path), generated_tex_name=output_filename)

            da_thanh_cong = True
            # TTL 1 giờ (3600s) cho temp directories
            background_tasks.add_task(don_dep_sau_thoi_gian, job_folder, 3600)

            # Lưu output ZIP vào outputs/
            output_zip_path = outputs_folder / zip_filename
            try:
                shutil.copy2(zip_path, output_zip_path)
            except Exception:
                output_zip_path = zip_path   # fallback

            # Lưu lịch sử vào SQLite nếu người dùng đã đăng nhập
            if current_user is not None:
                try:
                    history_record = models.ConversionHistory(
                        user_id=current_user.id,
                        job_id=job_id,
                        file_name=file.filename,
                        template_name=template_type,
                        status="Thành công",
                        file_path=str(output_zip_path)
                    )
                    db.add(history_record)
                    db.commit()
                except Exception as hist_err:
                    print(f"[WARN] Không thể lưu lịch sử: {hist_err}")

            yield sse_event(6, "Hoàn tất!",
                            done=True,
                            job_id=job_id,
                            ten_file_zip=zip_filename,
                            ten_file_latex=output_filename,
                            tex_content=tex_raw,
                            metadata={
                                "so_trang": so_trang,
                                "so_hinh_anh": so_hinh_anh,
                                "so_cong_thuc": so_cong_thuc,
                                "so_bang": so_bang,
                                "thoi_gian_xu_ly_giay": round(thoi_gian_xu_ly_giay, 2)
                            })

        except Exception as loi:
            print(f"[ERROR] SSE lỗi job_id={job_id}: {loi}")
            yield sse_event(-1, str(loi) or "Lỗi không xác định", error=True)
        finally:
            if not da_thanh_cong:
                xoa_thu_muc_an_toan(job_folder)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@app.get("/api/tai-ve-zip/{job_id}")
def tai_ve_zip_theo_job(job_id: str):
    # Tải file ZIP theo job_id trong thư mục temp
    job_folder = temp_folder / f"job_{job_id}"
    if not job_folder.exists() or not job_folder.is_dir():
        raise HTTPException(status_code=404, detail="Job không tồn tại hoặc đã bị dọn")

    danh_sach_zip = sorted(job_folder.glob('*.zip'), key=lambda p: p.stat().st_mtime, reverse=True)
    if not danh_sach_zip:
        raise HTTPException(status_code=404, detail="Không tìm thấy file .zip trong job")

    zip_path = danh_sach_zip[0]
    return FileResponse(
        path=str(zip_path),
        filename=zip_path.name,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename={zip_path.name}",
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
    )


@app.on_event("startup")
def xu_ly_don_dep_khi_khoi_dong():
    print("Registered POST routes:")
    for route in app.routes:
        if getattr(route, "methods", None) and "POST" in route.methods:
            print(f" - {route.path}")

    # Dọn dẹp các thư mục/file mồ côi trong temp khi server khởi động
    try:
        so_gio_ttl = int(os.getenv('TEMP_TTL_HOURS', '6').strip() or '6')
    except Exception as loi:
        print(f'[WARN] Giá trị TEMP_TTL_HOURS không hợp lệ, dùng mặc định 6 giờ: {loi}')
        so_gio_ttl = 6
    quet_xoa_thu_muc_mo_coi(temp_folder, so_gio_ttl)

    try:
        so_gio_ttl_output = int(os.getenv('OUTPUT_TTL_HOURS', '24').strip() or '24')
    except Exception as loi:
        print(f'[WARN] Giá trị OUTPUT_TTL_HOURS không hợp lệ, dùng mặc định 24 giờ: {loi}')
        so_gio_ttl_output = 24
    quet_xoa_thu_muc_mo_coi(outputs_folder, so_gio_ttl_output)


@app.get("/health")
def kiem_tra_suc_khoe():
    # Health check endpoint
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    # Trả về 204 No Content để tắt lỗi 404 từ trình duyệt
    return Response(status_code=204)


# ── AUTH ENDPOINTS ────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str


@app.post("/api/auth/register")
def dang_ky(req: RegisterRequest, db: Session = Depends(database.get_db)):
    """Tạo tài khoản mới, trả về JWT token."""
    if db.query(models.User).filter(models.User.email == req.email).first():
        raise HTTPException(status_code=400, detail="Email này đã được đăng ký")
    if db.query(models.User).filter(models.User.username == req.username).first():
        raise HTTPException(status_code=400, detail="Tên đăng nhập đã tồn tại")
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Mật khẩu phải có ít nhất 6 ký tự")

    user = models.User(
        username=req.username,
        email=req.email,
        hashed_password=auth.hash_password(req.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = auth.create_access_token({"sub": str(user.id)})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }
    }


@app.post("/api/auth/login")
def dang_nhap(req: LoginRequest, db: Session = Depends(database.get_db)):
    """Đăng nhập bằng email + mật khẩu, trả về JWT token."""
    user = db.query(models.User).filter(models.User.email == req.email).first()
    if not user or not auth.verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Email hoặc mật khẩu không đúng")

    token = auth.create_access_token({"sub": str(user.id)})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }
    }


@app.get("/api/auth/me")
def lay_thong_tin_ban_than(
    current_user: models.User = Depends(auth.get_current_user)
):
    """Trả về thông tin người dùng đang đăng nhập dựa trên JWT token."""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "created_at": current_user.created_at.isoformat()
    }


# ── HISTORY ENDPOINTS (token-based) ─────────────────────────────────────────

@app.get("/api/history")
def lay_lich_su(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Lấy lịch sử chuyển đổi của người dùng đang đăng nhập."""
    records = (
        db.query(models.ConversionHistory)
        .filter(models.ConversionHistory.user_id == current_user.id)
        .order_by(models.ConversionHistory.created_at.desc())
        .all()
    )
    return {
        "danhSach": [
            {
                "id": r.id,
                "job_id": r.job_id,
                "tenFileGoc": r.file_name,
                "templateName": r.template_name,
                "trangThai": r.status,
                "file_path": r.file_path,
                "thoiGian": r.created_at.isoformat()
            }
            for r in records
        ]
    }


@app.delete("/api/history/{record_id}")
def xoa_lich_su(
    record_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Xóa một bản ghi lịch sử (chỉ của người dùng hiện tại)."""
    record = db.query(models.ConversionHistory).filter(
        models.ConversionHistory.id == record_id,
        models.ConversionHistory.user_id == current_user.id
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Không tìm thấy bản ghi")
    db.delete(record)
    db.commit()
    return {"thanhCong": True}


@app.get("/api/download/{job_id}")
def tai_ve_theo_job(
    job_id: str,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Tải file ZIP từ đường dẫn được lưu trong DB."""
    record = db.query(models.ConversionHistory).filter(
        models.ConversionHistory.job_id == job_id,
        models.ConversionHistory.user_id == current_user.id
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Không tìm thấy bản ghi")

    zip_path = Path(record.file_path) if record.file_path else None

    # Fallback: tìm trong temp_jobs
    if not zip_path or not zip_path.exists():
        job_folder = temp_folder / f"job_{job_id}"
        if job_folder.exists():
            zips = sorted(job_folder.glob("*.zip"), key=lambda p: p.stat().st_mtime, reverse=True)
            if zips:
                zip_path = zips[0]

    if not zip_path or not zip_path.exists():
        raise HTTPException(status_code=404, detail="File ZIP không còn tồn tại trên server")

    return FileResponse(
        path=str(zip_path),
        filename=zip_path.name,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename={zip_path.name}",
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
    )


if __name__ == "__main__":
    # Chạy server với uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # Auto-reload khi code thay đổi (chỉ dùng development)
    )
