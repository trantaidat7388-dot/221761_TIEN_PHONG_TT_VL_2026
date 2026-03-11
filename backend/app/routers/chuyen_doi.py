"""
chuyen_doi.py
Định nghĩa các API liên quan đến chuyển đổi Word sang LaTeX.
"""

import uuid
import time
import json
import shutil
from datetime import datetime
from pathlib import Path
import re

from fastapi import APIRouter, File, UploadFile, HTTPException, Query, BackgroundTasks, Request, Depends
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from sqlalchemy.orm import Session

from ..config import TEMP_FOLDER, OUTPUTS_FOLDER
from ..utils.api_utils import xoa_thu_muc_an_toan, don_dep_sau_15_phut, don_dep_sau_thoi_gian, _resolve_template_path
from ..database import get_db
from .. import models
from .. import auth

# Nhập các module lõi từ core_engine
from backend.core_engine.chuyen_doi import ChuyenDoiWordSangLatex
from backend.core_engine.utils import (
    don_dep_file_rac, bien_dich_latex, find_main_tex,
    extract_zip_template, package_output_directory
)
from backend.core_engine.tex_log_parser import parse_latex_log


router = APIRouter(prefix="/api", tags=["Chuyển Đổi"])

@router.post("/chuyen-doi")
async def chuyen_doi_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    template_type: str = Query("ieee_conference", description="ieee_conference hoặc custom_xxx"),
    template_file: UploadFile = File(None, description="Tùy chọn: file .tex hoặc .zip chứa template")
):
    """Endpoint chuyển đổi file Word → LaTeX (chế độ thường)."""
    
    ten_file = file.filename.lower()
    if not (ten_file.endswith('.docx') or ten_file.endswith('.docm')):
        raise HTTPException(status_code=400, detail="Chỉ chấp nhận file .docx hoặc .docm")
    
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File quá lớn. Kích thước tối đa 10MB")
    
    job_id = str(uuid.uuid4())
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"[JOB {job_id}] Nhận yêu cầu: {file.filename} temp={template_type}")
    
    original_name = Path(file.filename).stem
    safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in original_name).lstrip(" -_") or "document"
    
    job_folder = TEMP_FOLDER / f"job_{job_id}"
    job_folder.mkdir(parents=True, exist_ok=True)
    
    file_ext = Path(file.filename).suffix.lower() or '.docx'
    input_path = job_folder / f"{safe_name}_{timestamp}{file_ext}"
    output_filename = f"{safe_name}_{timestamp}.tex"
    output_path = job_folder / output_filename
    images_folder = job_folder / "images"
    images_folder.mkdir(parents=True, exist_ok=True)

    with open(input_path, "wb") as f:
        f.write(contents)
    
    template_path = None
    
    # 1. Template uploaded
    if template_file:
        is_zip = template_file.filename.lower().endswith('.zip')
        template_contents = await template_file.read()
        
        if is_zip:
            zip_path = job_folder / "uploaded_template.zip"
            with open(zip_path, "wb") as f: f.write(template_contents)
            try:
                extract_zip_template(str(zip_path), str(job_folder))
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"File ZIP template không hợp lệ: {e}")
            finally:
                if zip_path.exists(): zip_path.unlink()
            try:
                template_path = Path(find_main_tex(str(job_folder)))
            except FileNotFoundError:
                raise HTTPException(status_code=400, detail="Không tìm thấy file .tex chính trong ZIP")

            template_tex_dir = template_path.parent
            if template_tex_dir != job_folder:
                dep_extensions = {'.cls', '.sty', '.bst', '.tex', '.png', '.jpg', '.jpeg', '.pdf', '.eps', '.bib'}
                for item in template_tex_dir.rglob("*"):
                    if item.is_file() and item.suffix.lower() in dep_extensions:
                        target_file = job_folder / item.relative_to(template_tex_dir)
                        target_file.parent.mkdir(parents=True, exist_ok=True)
                        if not target_file.exists(): shutil.copy2(item, target_file)
                main_tex_dest = job_folder / template_path.name
                if not main_tex_dest.exists(): shutil.copy2(template_path, main_tex_dest)
                template_path = main_tex_dest
        else:
            template_path = job_folder / "custom_uploaded_template.tex"
            with open(template_path, "wb") as f: f.write(template_contents)
    # 2. Template from system
    else:
        template_path = _resolve_template_path(template_type) or _resolve_template_path("ieee_conference")
        if not template_path or not template_path.exists():
            raise HTTPException(status_code=500, detail="Template không tồn tại hoặc lỗi cấu trúc thư mục.")
        
        template_dir_actual = template_path.parent
        try:
            shutil.copytree(str(template_dir_actual), str(job_folder), dirs_exist_ok=True)
        except Exception as e:
            print(f"[WARN] copytree thất bại, fallback rglob: {e}")
            for item in template_dir_actual.rglob("*"):
                if item.is_file():
                    try:
                        target_file = job_folder / item.relative_to(template_dir_actual)
                        target_file.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(item, target_file)
                    except Exception: pass
        template_path = job_folder / template_path.name

    zip_filename = output_filename.replace('.tex', '.zip')
    zip_path = job_folder / zip_filename
    da_thanh_cong = False

    try:
        t0 = time.time()
        bo_chuyen_doi = ChuyenDoiWordSangLatex(
            duong_dan_word=str(input_path),
            duong_dan_template=str(template_path),
            duong_dan_dau_ra=str(output_path),
            thu_muc_anh=str(images_folder),
            mode='demo'
        )
        bo_chuyen_doi.chuyen_doi()

        try:
            tex_raw = output_path.read_text(encoding='utf-8', errors='ignore')
            images_abs = str(images_folder).replace('\\', '/')
            job_abs = str(job_folder).replace('\\', '/')
            tex_raw = tex_raw.replace(images_abs + '/', 'images/').replace(images_abs, 'images')
            tex_raw = tex_raw.replace(job_abs + '/', '').replace(job_abs, '')
            images_abs_win = str(images_folder).replace('/', '\\')
            job_abs_win = str(job_folder).replace('/', '\\')
            tex_raw = tex_raw.replace(images_abs_win + '\\', 'images/').replace(images_abs_win, 'images')
            tex_raw = tex_raw.replace(job_abs_win + '\\', '').replace(job_abs_win, '')
            output_path.write_text(tex_raw, encoding='utf-8')
        except Exception: pass

        thanh_cong, thong_bao_loi = bien_dich_latex(str(output_path))
        if not thanh_cong:
            missing_file_match = re.search(r"! LaTeX Error: File `(.*?)' not found.", thong_bao_loi)
            if missing_file_match:
                raise Exception(f"Thiếu thư viện cấu trúc LaTeX: '{missing_file_match.group(1)}'.")
            chi_tiet_loi = parse_latex_log(thong_bao_loi)
            raise HTTPException(status_code=422, detail=json.dumps(chi_tiet_loi, ensure_ascii=False))

        so_trang = None
        try:
            log_path = output_path.with_suffix('.log')
            if log_path.exists():
                log_text = log_path.read_text(encoding='utf-8', errors='ignore')
                match = re.search(r'Output written on .*?\((\d+) pages?[,\)]', log_text, re.DOTALL)
                if match: so_trang = int(match.group(1))
        except Exception: pass

        pdf_path = output_path.with_suffix('.pdf')
        if so_trang is None and pdf_path.exists():
            so_trang = 1
            try:
                import re as regex_pdf
                with open(pdf_path, 'rb') as f:
                    pages_found = len(regex_pdf.findall(b'/Type\\s*/Page\\b', f.read()))
                    if pages_found > 0: so_trang = pages_found
            except: pass

        don_dep_file_rac(str(output_path))
        if not output_path.exists(): raise Exception("Không tạo được file .tex đầu ra")

        tex_raw = output_path.read_text(encoding='utf-8', errors='ignore')
        so_hinh_anh = len(re.findall(r'\\includegraphics', tex_raw))
        so_bang = len(re.findall(r'\\begin\{table', tex_raw))
        ir = getattr(bo_chuyen_doi, 'ir', None)
        if ir and ir.get("metadata", {}).get("total_formulas", 0) > 0:
            so_cong_thuc = ir["metadata"]["total_formulas"]
        else:
            so_cong_thuc = len(re.findall(r'\\begin\{(equation\*?|align\*?|eqnarray\*?)\}', tex_raw)) + \
                           len(re.findall(r'\\\[', tex_raw)) + len(re.findall(r'\\\(', tex_raw)) + \
                           len(re.findall(r'\$\$', tex_raw)) // 2
        
        thoi_gian_xu_ly_giay = max(0.0, time.time() - t0)
        package_output_directory(str(job_folder), str(zip_path), generated_tex_name=output_filename)

        da_thanh_cong = True
        background_tasks.add_task(don_dep_sau_15_phut, job_folder)
        
        try: shutil.copy2(zip_path, OUTPUTS_FOLDER / zip_filename)
        except Exception: pass

        return JSONResponse(status_code=200, content={
            "thanh_cong": True,
            "tex_content": tex_raw,
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
    except HTTPException: raise
    except Exception as loi:
        return JSONResponse(status_code=400, content={"error": f"Lỗi: {str(loi) or 'không xác định'}"})
    finally:
        if not da_thanh_cong: xoa_thu_muc_an_toan(job_folder)


@router.post("/chuyen-doi-stream")
async def chuyen_doi_file_stream(
    background_tasks: BackgroundTasks,
    request: Request,
    file: UploadFile = File(...),
    template_type: str = Query("ieee_conference"),
    template_file: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    """SSE endpoint: trả về Server-Sent Events cho tiến trình chuyển đổi real-time."""
    current_user = None
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
        try:
            current_user = auth.get_current_user(token=token, db=db)
        except Exception: pass

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
        safe_name = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in original_name).strip('_') or "document"

        job_folder = TEMP_FOLDER / f"job_{job_id}"
        job_folder.mkdir(parents=True, exist_ok=True)
        file_ext = Path(file.filename).suffix.lower() or '.docx'
        input_path = job_folder / f"{safe_name}_{timestamp}{file_ext}"
        output_filename = f"{safe_name}_{timestamp}.tex"
        output_path = job_folder / output_filename
        images_folder = job_folder / "images"
        images_folder.mkdir(parents=True, exist_ok=True)

        def sse_event(step, msg, **extra):
            payload = {"step": step, "msg": msg, **extra}
            return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

        try:
            yield sse_event(1, "Đang tải file lên server...")
            with open(input_path, "wb") as f: f.write(contents)

            template_path = None
            if template_contents:
                is_zip = template_filename and template_filename.lower().endswith('.zip')
                if is_zip:
                    zip_path = job_folder / "uploaded_template.zip"
                    with open(zip_path, "wb") as f: f.write(template_contents)
                    try: extract_zip_template(str(zip_path), str(job_folder))
                    except ValueError as e:
                        yield sse_event(-1, f"File ZIP template không hợp lệ: {e}", error=True); return
                    finally:
                        if zip_path.exists(): zip_path.unlink()
                    try: template_path = Path(find_main_tex(str(job_folder)))
                    except FileNotFoundError:
                        yield sse_event(-1, "Không tìm thấy file .tex chính trong ZIP", error=True); return
                    template_tex_dir = template_path.parent
                    if template_tex_dir != job_folder:
                        for item in template_tex_dir.rglob("*"):
                            if item.is_file() and item.suffix.lower() in {'.cls', '.sty', '.bst', '.tex', '.png', '.jpg', '.pdf', '.bib'}:
                                target_file = job_folder / item.relative_to(template_tex_dir)
                                target_file.parent.mkdir(parents=True, exist_ok=True)
                                if not target_file.exists(): shutil.copy2(item, target_file)
                        main_tex_dest = job_folder / template_path.name
                        if not main_tex_dest.exists(): shutil.copy2(template_path, main_tex_dest)
                        template_path = main_tex_dest
                else:
                    template_path = job_folder / "custom_uploaded_template.tex"
                    with open(template_path, "wb") as f: f.write(template_contents)
            else:
                template_path = _resolve_template_path(template_type) or _resolve_template_path("ieee_conference")
                if not template_path or not template_path.exists():
                    yield sse_event(-1, "Template không tồn tại", error=True); return
                template_dir_actual = template_path.parent
                try: shutil.copytree(str(template_dir_actual), str(job_folder), dirs_exist_ok=True)
                except Exception:
                    for item in template_dir_actual.rglob("*"):
                        if item.is_file():
                            try:
                                target_file = job_folder / item.relative_to(template_dir_actual)
                                target_file.parent.mkdir(parents=True, exist_ok=True)
                                shutil.copy2(item, target_file)
                            except Exception: pass
                template_path = job_folder / template_path.name

            yield sse_event(2, "Đang xây dựng cây AST & Phân tích ngữ nghĩa...")
            t0 = time.time()
            bo_chuyen_doi = ChuyenDoiWordSangLatex(
                duong_dan_word=str(input_path),
                duong_dan_template=str(template_path),
                duong_dan_dau_ra=str(output_path),
                thu_muc_anh=str(images_folder),
                mode='demo'
            )

            yield sse_event(3, "Đang nạp dữ liệu vào template Jinja2...")
            bo_chuyen_doi.chuyen_doi()

            try:
                tex_raw = output_path.read_text(encoding='utf-8', errors='ignore')
                images_abs = str(images_folder).replace('\\', '/')
                job_abs = str(job_folder).replace('\\', '/')
                tex_raw = tex_raw.replace(images_abs + '/', 'images/').replace(images_abs, 'images')
                tex_raw = tex_raw.replace(job_abs + '/', '').replace(job_abs, '')
                images_abs_win = str(images_folder).replace('/', '\\')
                job_abs_win = str(job_folder).replace('/', '\\')
                tex_raw = tex_raw.replace(images_abs_win + '\\', 'images/').replace(images_abs_win, 'images')
                tex_raw = tex_raw.replace(job_abs_win + '\\', '').replace(job_abs_win, '')
                output_path.write_text(tex_raw, encoding='utf-8')
            except Exception: pass

            yield sse_event(4, "Đang biên dịch XeLaTeX (Sẽ mất vài giây)...")
            thanh_cong, thong_bao_loi = bien_dich_latex(str(output_path))
            if not thanh_cong:
                missing_file_match = re.search(r"! LaTeX Error: File `(.*?)' not found.", thong_bao_loi)
                if missing_file_match:
                    yield sse_event(-1, f"Thiếu thư viện: '{missing_file_match.group(1)}'", error=True); return
                chi_tiet_loi = parse_latex_log(thong_bao_loi)
                yield sse_event(-1, chi_tiet_loi.get("thong_diep", "Biên dịch thất bại"), error=True, details=chi_tiet_loi); return

            yield sse_event(5, "Đang đóng gói kết quả...")
            so_trang = None
            try:
                log_path = output_path.with_suffix('.log')
                if log_path.exists():
                    match = re.search(r'Output written on .*?\((\d+) pages?[,\)]', log_path.read_text('utf-8', 'ignore'), re.DOTALL)
                    if match: so_trang = int(match.group(1))
            except Exception: pass

            pdf_path = output_path.with_suffix('.pdf')
            if so_trang is None and pdf_path.exists():
                so_trang = 1
                try:
                    with open(pdf_path, 'rb') as f:
                        pages_found = len(re.findall(b'/Type\\s*/Page\\b', f.read()))
                        if pages_found > 0: so_trang = pages_found
                except Exception: pass

            don_dep_file_rac(str(output_path))
            tex_raw = output_path.read_text(encoding='utf-8', errors='ignore')
            so_hinh_anh = len(re.findall(r'^[^%\n]*\\includegraphics', tex_raw, re.MULTILINE))
            so_bang = len(re.findall(r'^[^%\n]*\\begin\{table', tex_raw, re.MULTILINE))
            
            ir = getattr(bo_chuyen_doi, 'ir', None)
            if ir and ir.get("metadata", {}).get("total_formulas", 0) > 0:
                so_cong_thuc = ir["metadata"]["total_formulas"]
            else:
                so_cong_thuc = len(re.findall(r'\\begin\{(equation\*?|align\*?|eqnarray\*?)\}', tex_raw)) + \
                               len(re.findall(r'\\\[', tex_raw)) + len(re.findall(r'\\\(', tex_raw)) + \
                               len(re.findall(r'\$\$', tex_raw)) // 2
            
            thoi_gian_xu_ly_giay = max(0.0, time.time() - t0)
            zip_filename = output_filename.replace('.tex', '.zip')
            zip_path = job_folder / zip_filename
            package_output_directory(str(job_folder), str(zip_path), generated_tex_name=output_filename)

            da_thanh_cong = True
            background_tasks.add_task(don_dep_sau_thoi_gian, job_folder, 3600)
            
            output_zip_path = OUTPUTS_FOLDER / zip_filename
            try: shutil.copy2(zip_path, output_zip_path)
            except Exception: output_zip_path = zip_path

            if current_user is not None:
                try:
                    history_record = models.ConversionHistory(
                        user_id=current_user.id, job_id=job_id, file_name=file.filename,
                        template_name=template_type, status="Thành công", file_path=str(output_zip_path)
                    )
                    db.add(history_record)
                    db.commit()
                except Exception as hist_err: print(f"[WARN] Không thể lưu lịch sử: {hist_err}")

            yield sse_event(6, "Hoàn tất!", done=True, job_id=job_id, ten_file_zip=zip_filename,
                            ten_file_latex=output_filename, tex_content=tex_raw,
                            metadata={"so_trang": so_trang, "so_hinh_anh": so_hinh_anh, "so_cong_thuc": so_cong_thuc,
                                      "so_bang": so_bang, "thoi_gian_xu_ly_giay": round(thoi_gian_xu_ly_giay, 2)})
        except Exception as loi:
            yield sse_event(-1, str(loi) or "Lỗi không xác định", error=True)
        finally:
            if not da_thanh_cong: xoa_thu_muc_an_toan(job_folder)

    return StreamingResponse(event_generator(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"})


@router.get("/tai-ve-zip/{job_id}")
def tai_ve_zip_theo_job(job_id: str):
    job_folder = TEMP_FOLDER / f"job_{job_id}"
    if not job_folder.exists() or not job_folder.is_dir():
        raise HTTPException(status_code=404, detail="Job không tồn tại hoặc đã bị dọn")

    danh_sach_zip = sorted(job_folder.glob('*.zip'), key=lambda p: p.stat().st_mtime, reverse=True)
    if not danh_sach_zip:
        raise HTTPException(status_code=404, detail="Không tìm thấy file .zip trong job")

    zip_path = danh_sach_zip[0]
    return FileResponse(
        path=str(zip_path), filename=zip_path.name, media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={zip_path.name}", "Access-Control-Expose-Headers": "Content-Disposition"}
    )


@router.get("/download/{job_id}")
def tai_ve_theo_job(job_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Tải file ZIP từ đường dẫn được lưu trong DB (yêu cầu auth)."""
    record = db.query(models.ConversionHistory).filter(models.ConversionHistory.job_id == job_id, models.ConversionHistory.user_id == current_user.id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Không tìm thấy bản ghi")

    zip_path = Path(record.file_path) if record.file_path else None
    if not zip_path or not zip_path.exists():
        job_folder = TEMP_FOLDER / f"job_{job_id}"
        if job_folder.exists():
            zips = sorted(job_folder.glob("*.zip"), key=lambda p: p.stat().st_mtime, reverse=True)
            if zips: zip_path = zips[0]

    if not zip_path or not zip_path.exists():
        raise HTTPException(status_code=404, detail="File ZIP không còn tồn tại trên server")

    return FileResponse(
        path=str(zip_path), filename=zip_path.name, media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={zip_path.name}", "Access-Control-Expose-Headers": "Content-Disposition"}
    )
