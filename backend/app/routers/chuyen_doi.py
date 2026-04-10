"""
chuyen_doi.py
Định nghĩa các API liên quan đến chuyển đổi Word sang LaTeX.
"""

import uuid
import time
import json
import shutil
import logging
from datetime import datetime
from pathlib import Path
import re

from fastapi import APIRouter, File, UploadFile, HTTPException, Query, BackgroundTasks, Request, Depends, Body
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from ..config import TEMP_FOLDER, OUTPUTS_FOLDER, MAX_DOC_UPLOAD_MB, SSE_CLEANUP_DELAY_SECONDS
from ..utils.api_utils import xoa_thu_muc_an_toan, don_dep_sau_15_phut, don_dep_sau_thoi_gian, _resolve_template_path
from ..database import lay_db
from .. import models
from .. import auth
from ..services import token_service

# Nhập các module lõi từ core_engine
from backend.core_engine.chuyen_doi import ChuyenDoiWordSangLatex
from backend.core_engine.ast_parser import WordASTParser
from backend.core_engine.word_ieee_renderer import IEEEWordRenderer
from backend.core_engine.word_springer_renderer import SpringerWordRenderer
from backend.core_engine.utils import (
    don_dep_file_rac, bien_dich_latex, tim_file_tex_chinh,
    giai_nen_mau_zip, dong_goi_thu_muc_dau_ra
)
from backend.core_engine.tex_log_parser import phan_tich_log_latex

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/api", tags=["Chuyển Đổi"])

DEFAULT_IEEE_WORD_TEMPLATE = (
    Path(__file__).resolve().parents[3]
    / "input_data"
    / "Template_word"
    / "conference-template-a4 (ieee).docx"
)

DEFAULT_SPRINGER_WORD_TEMPLATE = (
    Path(__file__).resolve().parents[3]
    / "input_data"
    / "Template_word"
    / "splnproc2510.docm"
)


def _la_file_word_hop_le(ten_file: str) -> bool:
    ten = (ten_file or "").lower()
    return ten.endswith('.docx') or ten.endswith('.docm')


def _ghi_lich_su_chuyen_doi(
    db: Session,
    user_id: int,
    job_id: str,
    file_name: str,
    template_name: str,
    status: str,
    file_path: str,
    pages_count: int,
    token_cost: int,
    token_refunded: bool = False,
    error_type: str | None = None,
    error_message: str | None = None,
) -> None:
    history_record = models.ConversionHistory(
        user_id=user_id,
        job_id=job_id,
        file_name=file_name,
        template_name=template_name,
        status=status,
        file_path=file_path,
        pages_count=pages_count,
        token_cost=token_cost,
        token_refunded=token_refunded,
        error_type=error_type,
        error_message=error_message,
    )
    db.add(history_record)
    db.commit()

@router.post("/chuyen-doi")
async def chuyen_doi_file(
    background_tasks: BackgroundTasks,
    request: Request,
    file: UploadFile = File(...),
    template_type: str = Query("ieee_conference", description="ieee_conference hoặc custom_xxx"),
    template_file: UploadFile = File(None, description="Tùy chọn: file .tex hoặc .zip chứa template"),
    db: Session = Depends(lay_db)
) -> JSONResponse:
    """Endpoint chuyển đổi file Word → LaTeX (chế độ thường)."""
    
    ten_file = file.filename.lower()
    if not _la_file_word_hop_le(ten_file):
        raise HTTPException(status_code=400, detail="Chi chap nhan file .docx hoac .docm")
    
    current_user = None
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
        try:
            current_user = auth.lay_nguoi_dung_hien_tai(token=token, db=db)
        except Exception as e:
            logger.warning("Bearer token không hợp lệ cho request /chuyen-doi", exc_info=e)

    contents = await file.read()
    if len(contents) > MAX_DOC_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File quá lớn. Kích thước tối đa {MAX_DOC_UPLOAD_MB}MB")
    
    job_id = str(uuid.uuid4())
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    token_usage = {
        "pages_count": 0,
        "token_cost": 0,
        "balance_after": None,
        "deducted": False,
        "refunded": False,
    }

    if current_user is not None:
        pages_estimate = token_service.uoc_tinh_so_trang_tu_noi_dung_word(contents)
        deduction = token_service.tru_token_cho_chuyen_doi(
            db=db,
            user_id=current_user.id,
            so_trang_uoc_tinh=pages_estimate,
            job_id=job_id,
        )
        token_usage.update({
            "pages_count": deduction["pages_count"],
            "token_cost": deduction["token_cost"],
            "balance_after": deduction["balance_after"],
            "deducted": True,
        })

    request_id = getattr(request.state, "request_id", "-")
    logger.info(
        "request_id=%s job_id=%s upload_received file=%s template=%s",
        request_id,
        job_id,
        file.filename,
        template_type,
    )
    
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
                giai_nen_mau_zip(str(zip_path), str(job_folder))
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"File ZIP template không hợp lệ: {e}")
            finally:
                if zip_path.exists(): zip_path.unlink()
            try:
                template_path = Path(tim_file_tex_chinh(str(job_folder)))
            except FileNotFoundError:
                raise HTTPException(status_code=400, detail="Không tìm thấy file .tex chính trong ZIP")

            template_tex_dir = template_path.parent
            if template_tex_dir != job_folder:
                # Copy ALL files from the extracted template directory to job_folder
                try:
                    shutil.copytree(str(template_tex_dir), str(job_folder), dirs_exist_ok=True)
                except Exception as e:
                    logger.warning("copytree ZIP template thất bại", exc_info=e)
                
                # Update template_path to point to the new location in job_folder
                template_path = job_folder / template_path.name
        else:
            template_path = job_folder / "custom_uploaded_template.tex"
            with open(template_path, "wb") as f: f.write(template_contents)
    # 2. Template from system
    else:
        template_path = _resolve_template_path(
            template_type,
            current_user_id=current_user.id if current_user else None,
            current_user_role=current_user.role if current_user else None,
        ) or _resolve_template_path("ieee_conference")
        if not template_path or not template_path.exists():
            raise HTTPException(status_code=500, detail="Template không tồn tại hoặc lỗi cấu trúc thư mục.")
        
        template_dir_actual = template_path.parent
        try:
            shutil.copytree(str(template_dir_actual), str(job_folder), dirs_exist_ok=True)
        except Exception as e:
            logger.warning("copytree template thất bại, fallback rglob", exc_info=e)
            for item in template_dir_actual.rglob("*"):
                if item.is_file():
                    try:
                        target_file = job_folder / item.relative_to(template_dir_actual)
                        target_file.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(item, target_file)
                    except Exception as e:
                        logger.warning("Fallback copy file thất bại: %s", item, exc_info=e)
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
        await run_in_threadpool(bo_chuyen_doi.chuyen_doi)

        try:
            tex_raw = output_path.read_text(encoding='utf-8', errors='ignore')
            # [FAIL-SAFE] Dọn dẹp rác metadata còn sót lại để tránh lỗi "Missing \begin{document}"
            # This regex aggressively removes the metadata tag AND any subsequent { } blocks even with spaces between them.
            tex_raw = re.sub(r'<<\s*metadata\.[a-zA-Z0-9_]+\s*>>(?:\s*\{[^{}]*\}\s*)*', '', tex_raw)
            images_abs = str(images_folder).replace('\\', '/')
            job_abs = str(job_folder).replace('\\', '/')
            tex_raw = tex_raw.replace(images_abs + '/', 'images/').replace(images_abs, 'images')
            tex_raw = tex_raw.replace(job_abs + '/', '').replace(job_abs, '')
            images_abs_win = str(images_folder).replace('/', '\\')
            job_abs_win = str(job_folder).replace('/', '\\')
            tex_raw = tex_raw.replace(images_abs_win + '\\', 'images/').replace(images_abs_win, 'images')
            tex_raw = tex_raw.replace(job_abs_win + '\\', '').replace(job_abs_win, '')
            output_path.write_text(tex_raw, encoding='utf-8')
        except Exception as e:
            logger.warning("Không thể chuẩn hóa đường dẫn trong file tex đầu ra", exc_info=e)

        # SKIP PDF compilation — only convert Word → LaTeX
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
        dong_goi_thu_muc_dau_ra(str(job_folder), str(zip_path), generated_tex_name=output_filename)

        da_thanh_cong = True
        background_tasks.add_task(don_dep_sau_15_phut, job_folder)
        
        try:
            shutil.copy2(zip_path, OUTPUTS_FOLDER / zip_filename)
        except Exception as e:
            logger.warning("Không thể copy ZIP sang outputs", exc_info=e)

        if current_user is not None:
            try:
                _ghi_lich_su_chuyen_doi(
                    db=db,
                    user_id=current_user.id,
                    job_id=job_id,
                    file_name=file.filename,
                    template_name=template_type,
                    status="Thành công",
                    file_path=str(OUTPUTS_FOLDER / zip_filename),
                    pages_count=token_usage["pages_count"],
                    token_cost=token_usage["token_cost"],
                )
            except Exception as hist_err:
                logger.warning("Không thể lưu lịch sử conversion /chuyen-doi", exc_info=hist_err)

        logger.info(
            "request_id=%s job_id=%s conversion_success output_zip=%s",
            request_id,
            job_id,
            zip_filename,
        )

        return JSONResponse(status_code=200, content={
            "thanh_cong": True,
            "tex_content": tex_raw,
            "job_id": job_id,
            "ten_file_zip": zip_filename,
            "ten_file_latex": output_filename,
            "metadata": {
                "so_trang": None,
                "so_hinh_anh": so_hinh_anh,
                "so_cong_thuc": so_cong_thuc,
                "so_bang": so_bang,
                "thoi_gian_xu_ly_giay": round(thoi_gian_xu_ly_giay, 2),
                "pages_count": token_usage["pages_count"],
                "token_cost": token_usage["token_cost"],
                "token_balance_after": token_usage["balance_after"],
            },
            "token_usage": {
                "pages_count": token_usage["pages_count"],
                "token_cost": token_usage["token_cost"],
                "token_balance_after": token_usage["balance_after"],
            },
        })
    except HTTPException as loi_http:
        if current_user is not None and token_usage["deducted"] and not token_usage["refunded"]:
            try:
                token_service.hoan_token_chuyen_doi(
                    db=db,
                    user_id=current_user.id,
                    token_cost=token_usage["token_cost"],
                    job_id=job_id,
                    pages_count=token_usage["pages_count"],
                )
                token_usage["refunded"] = True
            except Exception as refund_err:
                logger.warning("Hoàn token thất bại cho request /chuyen-doi", exc_info=refund_err)

        if current_user is not None:
            try:
                _ghi_lich_su_chuyen_doi(
                    db=db,
                    user_id=current_user.id,
                    job_id=job_id,
                    file_name=file.filename,
                    template_name=template_type,
                    status="Thất bại",
                    file_path="",
                    pages_count=token_usage["pages_count"],
                    token_cost=token_usage["token_cost"],
                    token_refunded=token_usage["refunded"],
                    error_type="HTTPException",
                    error_message=str(getattr(loi_http, "detail", "")),
                )
            except Exception as hist_err:
                logger.warning("Lưu lịch sử thất bại /chuyen-doi (HTTPException)", exc_info=hist_err)
        raise
    except Exception as loi:
        if current_user is not None and token_usage["deducted"] and not token_usage["refunded"]:
            try:
                token_service.hoan_token_chuyen_doi(
                    db=db,
                    user_id=current_user.id,
                    token_cost=token_usage["token_cost"],
                    job_id=job_id,
                    pages_count=token_usage["pages_count"],
                )
                token_usage["refunded"] = True
            except Exception as refund_err:
                logger.warning("Hoàn token thất bại cho lỗi runtime /chuyen-doi", exc_info=refund_err)

        if current_user is not None:
            try:
                _ghi_lich_su_chuyen_doi(
                    db=db,
                    user_id=current_user.id,
                    job_id=job_id,
                    file_name=file.filename,
                    template_name=template_type,
                    status="Thất bại",
                    file_path="",
                    pages_count=token_usage["pages_count"],
                    token_cost=token_usage["token_cost"],
                    token_refunded=token_usage["refunded"],
                    error_type=type(loi).__name__,
                    error_message=str(loi),
                )
            except Exception as hist_err:
                logger.warning("Lưu lịch sử thất bại /chuyen-doi (runtime)", exc_info=hist_err)

        logger.exception("request_id=%s job_id=%s conversion_failed", request_id, job_id)
        return JSONResponse(status_code=400, content={"error": f"Lỗi: {str(loi) or 'không xác định'}"})
    finally:
        if not da_thanh_cong: xoa_thu_muc_an_toan(job_folder)


@router.post("/chuyen-doi-word-ieee")
async def chuyen_doi_springer_word_sang_ieee_word(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    template_file: UploadFile | None = File(None),
) -> JSONResponse:
    """Convert Springer Word content into IEEE Word using uploaded or default template."""

    ten_file = (file.filename or "").lower()
    if not _la_file_word_hop_le(ten_file):
        raise HTTPException(status_code=400, detail="Chi chap nhan file .docx hoac .docm")

    contents = await file.read()
    if len(contents) > MAX_DOC_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File quá lớn. Kích thước tối đa {MAX_DOC_UPLOAD_MB}MB")

    template_contents = None
    template_filename = None
    template_ext = ".docx"
    if template_file is not None:
        ten_template = (template_file.filename or "").lower()
        if not _la_file_word_hop_le(ten_template):
            raise HTTPException(status_code=400, detail="Template IEEE phai la file .docx hoac .docm")
        template_contents = await template_file.read()
        if len(template_contents) > MAX_DOC_UPLOAD_MB * 1024 * 1024:
            raise HTTPException(status_code=400, detail=f"Template quá lớn. Kích thước tối đa {MAX_DOC_UPLOAD_MB}MB")
        template_filename = template_file.filename
        template_ext = Path(template_filename or "template.docx").suffix.lower() or ".docx"
    elif not DEFAULT_IEEE_WORD_TEMPLATE.exists():
        raise HTTPException(status_code=500, detail="Không tìm thấy template IEEE mặc định trên server")

    job_id = str(uuid.uuid4())
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    original_name = Path(file.filename or "document").stem
    safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in original_name).lstrip(" -_") or "document"

    job_folder = TEMP_FOLDER / f"job_{job_id}"
    job_folder.mkdir(parents=True, exist_ok=True)

    file_ext = Path(file.filename or "document.docx").suffix.lower() or ".docx"
    input_path = job_folder / f"{safe_name}_{timestamp}{file_ext}"
    images_folder = job_folder / "images"
    images_folder.mkdir(parents=True, exist_ok=True)
    template_path = job_folder / f"ieee_template_{timestamp}{template_ext}"
    output_docx_name = f"{safe_name}_{timestamp}_ieee.docx"
    output_docx_path = job_folder / output_docx_name

    with open(input_path, "wb") as f:
        f.write(contents)

    if template_contents is not None:
        with open(template_path, "wb") as f:
            f.write(template_contents)
    else:
        shutil.copy2(DEFAULT_IEEE_WORD_TEMPLATE, template_path)

    da_thanh_cong = False
    try:
        parser = WordASTParser(str(input_path), thu_muc_anh=str(images_folder))
        ir = await run_in_threadpool(parser.parse)

        renderer = IEEEWordRenderer()
        await run_in_threadpool(renderer.render, ir, str(output_docx_path), str(job_folder), str(template_path))

        if not output_docx_path.exists():
            raise Exception("Không tạo được file Word IEEE đầu ra")

        try:
            shutil.copy2(output_docx_path, OUTPUTS_FOLDER / output_docx_name)
        except Exception as e:
            logger.warning("Không thể copy DOCX IEEE sang outputs", exc_info=e)

        da_thanh_cong = True
        background_tasks.add_task(don_dep_sau_15_phut, job_folder)

        body_nodes = ir.get("body", []) if isinstance(ir, dict) else []
        quality_report = getattr(renderer, "last_render_metrics", {}) if renderer is not None else {}
        return JSONResponse(
            status_code=200,
            content={
                "thanh_cong": True,
                "job_id": job_id,
                "ten_file_word": output_docx_name,
                "word_url": f"/api/tai-ve-word/{job_id}",
                "metadata": {
                    "so_section": len([n for n in body_nodes if n.get("type") == "section"]),
                    "so_paragraph": len([n for n in body_nodes if n.get("type") == "paragraph"]),
                    "so_bang": len([n for n in body_nodes if n.get("type") == "table"]),
                    "so_tai_lieu_tham_khao": len(ir.get("references", []) if isinstance(ir, dict) else []),
                    "bao_cao_dinh_dang_ieee": quality_report,
                },
            },
        )
    except Exception as loi:
        logger.exception("Springer Word -> IEEE Word failed")
        return JSONResponse(status_code=400, content={"error": f"Lỗi: {str(loi) or 'không xác định'}"})
    finally:
        if not da_thanh_cong:
            xoa_thu_muc_an_toan(job_folder)


@router.post("/chuyen-doi-word-springer")
async def chuyen_doi_ieee_word_sang_springer_word(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    template_file: UploadFile | None = File(None),
) -> JSONResponse:
    """Convert IEEE Word content into Springer Word using uploaded or default template."""

    ten_file = (file.filename or "").lower()
    if not _la_file_word_hop_le(ten_file):
        raise HTTPException(status_code=400, detail="Chi chap nhan file .docx hoac .docm")

    contents = await file.read()
    if len(contents) > MAX_DOC_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File quá lớn. Kích thước tối đa {MAX_DOC_UPLOAD_MB}MB")

    template_contents = None
    template_ext = ".docx"
    if template_file is not None:
        ten_template = (template_file.filename or "").lower()
        if not _la_file_word_hop_le(ten_template):
            raise HTTPException(status_code=400, detail="Template Springer phai la file .docx hoac .docm")
        template_contents = await template_file.read()
        if len(template_contents) > MAX_DOC_UPLOAD_MB * 1024 * 1024:
            raise HTTPException(status_code=400, detail=f"Template quá lớn. Kích thước tối đa {MAX_DOC_UPLOAD_MB}MB")
        template_ext = Path(template_file.filename or "template.docx").suffix.lower() or ".docx"
    elif not DEFAULT_SPRINGER_WORD_TEMPLATE.exists():
        raise HTTPException(status_code=500, detail="Không tìm thấy template Springer mặc định trên server")

    job_id = str(uuid.uuid4())
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    original_name = Path(file.filename or "document").stem
    safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in original_name).lstrip(" -_") or "document"

    job_folder = TEMP_FOLDER / f"job_{job_id}"
    job_folder.mkdir(parents=True, exist_ok=True)

    file_ext = Path(file.filename or "document.docx").suffix.lower() or ".docx"
    input_path = job_folder / f"{safe_name}_{timestamp}{file_ext}"
    images_folder = job_folder / "images"
    images_folder.mkdir(parents=True, exist_ok=True)
    template_path = job_folder / f"springer_template_{timestamp}{template_ext}"
    output_docx_name = f"{safe_name}_{timestamp}_springer.docx"
    output_docx_path = job_folder / output_docx_name

    with open(input_path, "wb") as f:
        f.write(contents)

    if template_contents is not None:
        with open(template_path, "wb") as f:
            f.write(template_contents)
    else:
        shutil.copy2(DEFAULT_SPRINGER_WORD_TEMPLATE, template_path)

    da_thanh_cong = False
    try:
        parser = WordASTParser(str(input_path), thu_muc_anh=str(images_folder))
        ir = await run_in_threadpool(parser.parse)

        renderer = SpringerWordRenderer()
        await run_in_threadpool(renderer.render, ir, str(output_docx_path), str(job_folder), str(template_path))

        if not output_docx_path.exists():
            raise Exception("Không tạo được file Word Springer đầu ra")

        try:
            shutil.copy2(output_docx_path, OUTPUTS_FOLDER / output_docx_name)
        except Exception as e:
            logger.warning("Không thể copy DOCX Springer sang outputs", exc_info=e)

        da_thanh_cong = True
        background_tasks.add_task(don_dep_sau_15_phut, job_folder)

        body_nodes = ir.get("body", []) if isinstance(ir, dict) else []
        return JSONResponse(
            status_code=200,
            content={
                "thanh_cong": True,
                "job_id": job_id,
                "ten_file_word": output_docx_name,
                "word_url": f"/api/tai-ve-word/{job_id}",
                "metadata": {
                    "so_section": len([n for n in body_nodes if n.get("type") == "section"]),
                    "so_paragraph": len([n for n in body_nodes if n.get("type") == "paragraph"]),
                    "so_bang": len([n for n in body_nodes if n.get("type") == "table"]),
                    "so_tai_lieu_tham_khao": len(ir.get("references", []) if isinstance(ir, dict) else []),
                },
            },
        )
    except Exception as loi:
        logger.exception("IEEE Word -> Springer Word failed")
        return JSONResponse(status_code=400, content={"error": f"Lỗi: {str(loi) or 'không xác định'}"})
    finally:
        if not da_thanh_cong:
            xoa_thu_muc_an_toan(job_folder)


@router.post("/chuyen-doi-stream")
async def chuyen_doi_file_stream(
    background_tasks: BackgroundTasks,
    request: Request,
    file: UploadFile = File(...),
    template_type: str = Query("ieee_conference"),
    template_file: UploadFile = File(None),
    db: Session = Depends(lay_db)
) -> StreamingResponse:
    """SSE endpoint: trả về Server-Sent Events cho tiến trình chuyển đổi real-time."""
    current_user = None
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
        try:
            current_user = auth.lay_nguoi_dung_hien_tai(token=token, db=db)
        except Exception as e:
            logger.warning("Bearer token không hợp lệ cho SSE request", exc_info=e)

    ten_file = file.filename.lower()
    if not _la_file_word_hop_le(ten_file):
        raise HTTPException(status_code=400, detail="Chi chap nhan file .docx hoac .docm")

    contents = await file.read()
    if len(contents) > MAX_DOC_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File quá lớn. Kích thước tối đa {MAX_DOC_UPLOAD_MB}MB")

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
        token_usage = {
            "pages_count": 0,
            "token_cost": 0,
            "balance_after": None,
            "deducted": False,
            "refunded": False,
        }

        def sse_event(step, msg, **extra):
            payload = {"step": step, "msg": msg, **extra}
            return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

        try:
            if current_user is not None:
                pages_estimate = token_service.uoc_tinh_so_trang_tu_noi_dung_word(contents)
                deduction = token_service.tru_token_cho_chuyen_doi(
                    db=db,
                    user_id=current_user.id,
                    so_trang_uoc_tinh=pages_estimate,
                    job_id=job_id,
                )
                token_usage.update({
                    "pages_count": deduction["pages_count"],
                    "token_cost": deduction["token_cost"],
                    "balance_after": deduction["balance_after"],
                    "deducted": True,
                })

            yield sse_event(1, "Đang tải file lên server...")
            with open(input_path, "wb") as f: f.write(contents)

            template_path = None
            if template_contents:
                is_zip = template_filename and template_filename.lower().endswith('.zip')
                if is_zip:
                    zip_path = job_folder / "uploaded_template.zip"
                    with open(zip_path, "wb") as f: f.write(template_contents)
                    try: giai_nen_mau_zip(str(zip_path), str(job_folder))
                    except ValueError as e:
                        yield sse_event(-1, f"File ZIP template không hợp lệ: {e}", error=True); return
                    finally:
                        if zip_path.exists(): zip_path.unlink()
                    try: template_path = Path(tim_file_tex_chinh(str(job_folder)))
                    except FileNotFoundError:
                        yield sse_event(-1, "Không tìm thấy file .tex chính trong ZIP", error=True); return
                    template_tex_dir = template_path.parent
                    if template_tex_dir != job_folder:
                        try:
                            shutil.copytree(str(template_tex_dir), str(job_folder), dirs_exist_ok=True)
                        except Exception as e:
                            logger.warning("copytree SSE ZIP template thất bại", exc_info=e)
                        template_path = job_folder / template_path.name
                else:
                    template_path = job_folder / "custom_uploaded_template.tex"
                    with open(template_path, "wb") as f: f.write(template_contents)
            else:
                template_path = _resolve_template_path(
                    template_type,
                    current_user_id=current_user.id if current_user else None,
                    current_user_role=current_user.role if current_user else None,
                ) or _resolve_template_path("ieee_conference")
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
                            except Exception as e:
                                logger.warning("Fallback copy SSE file thất bại: %s", item, exc_info=e)
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
            await run_in_threadpool(bo_chuyen_doi.chuyen_doi)

            try:
                tex_raw = output_path.read_text(encoding='utf-8', errors='ignore')
                # This regex aggressively removes the metadata tag AND any subsequent { } blocks even with spaces between them.
                tex_raw = re.sub(r'<<\s*metadata\.[a-zA-Z0-9_]+\s*>>(?:\s*\{[^{}]*\}\s*)*', '', tex_raw, flags=re.MULTILINE)
                images_abs = str(images_folder).replace('\\', '/')
                job_abs = str(job_folder).replace('\\', '/')
                tex_raw = tex_raw.replace(images_abs + '/', 'images/').replace(images_abs, 'images')
                tex_raw = tex_raw.replace(job_abs + '/', '').replace(job_abs, '')
                images_abs_win = str(images_folder).replace('/', '\\')
                job_abs_win = str(job_folder).replace('/', '\\')
                tex_raw = tex_raw.replace(images_abs_win + '\\', 'images/').replace(images_abs_win, 'images')
                tex_raw = tex_raw.replace(job_abs_win + '\\', '').replace(job_abs_win, '')
                output_path.write_text(tex_raw, encoding='utf-8')
            except Exception as e:
                logger.warning("Không thể chuẩn hóa đường dẫn trong file tex SSE", exc_info=e)

            # SKIP PDF compilation — only convert Word → LaTeX
            if not output_path.exists():
                yield sse_event(-1, "Không tạo được file .tex đầu ra", error=True); return

            yield sse_event(4, "Đang đóng gói kết quả...")
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
            dong_goi_thu_muc_dau_ra(str(job_folder), str(zip_path), generated_tex_name=output_filename)

            da_thanh_cong = True
            background_tasks.add_task(don_dep_sau_thoi_gian, job_folder, SSE_CLEANUP_DELAY_SECONDS)
            
            output_zip_path = OUTPUTS_FOLDER / zip_filename
            try: shutil.copy2(zip_path, output_zip_path)
            except Exception: output_zip_path = zip_path

            if current_user is not None:
                try:
                    _ghi_lich_su_chuyen_doi(
                        db=db,
                        user_id=current_user.id,
                        job_id=job_id,
                        file_name=file.filename,
                        template_name=template_type,
                        status="Thành công",
                        file_path=str(output_zip_path),
                        pages_count=token_usage["pages_count"],
                        token_cost=token_usage["token_cost"],
                    )
                except Exception as hist_err:
                    logger.warning("Không thể lưu lịch sử conversion", exc_info=hist_err)

            yield sse_event(5, "Hoàn tất!", done=True, job_id=job_id, ten_file_zip=zip_filename,
                            ten_file_latex=output_filename, tex_content=tex_raw,
                            metadata={"so_trang": None, "so_hinh_anh": so_hinh_anh, "so_cong_thuc": so_cong_thuc,
                                      "so_bang": so_bang, "thoi_gian_xu_ly_giay": round(thoi_gian_xu_ly_giay, 2),
                                      "pages_count": token_usage["pages_count"],
                                      "token_cost": token_usage["token_cost"],
                                      "token_balance_after": token_usage["balance_after"]},
                            token_usage={"pages_count": token_usage["pages_count"],
                                         "token_cost": token_usage["token_cost"],
                                         "token_balance_after": token_usage["balance_after"]})
        except Exception as loi:
            req_id = getattr(request.state, "request_id", "-")
            if current_user is not None and token_usage["deducted"] and not token_usage["refunded"]:
                try:
                    token_service.hoan_token_chuyen_doi(
                        db=db,
                        user_id=current_user.id,
                        token_cost=token_usage["token_cost"],
                        job_id=job_id,
                        pages_count=token_usage["pages_count"],
                    )
                    token_usage["refunded"] = True
                except Exception as refund_err:
                    logger.warning("Hoàn token thất bại cho SSE conversion", exc_info=refund_err)

            if current_user is not None:
                try:
                    _ghi_lich_su_chuyen_doi(
                        db=db,
                        user_id=current_user.id,
                        job_id=job_id,
                        file_name=file.filename,
                        template_name=template_type,
                        status="Thất bại",
                        file_path="",
                        pages_count=token_usage["pages_count"],
                        token_cost=token_usage["token_cost"],
                        token_refunded=token_usage["refunded"],
                        error_type=type(loi).__name__,
                        error_message=str(loi),
                    )
                except Exception as hist_err:
                    logger.warning("Không thể lưu lịch sử thất bại SSE", exc_info=hist_err)

            logger.exception("request_id=%s job_id=%s sse_conversion_failed", req_id, job_id)
            yield sse_event(-1, str(loi) or "Lỗi không xác định", error=True)
        finally:
            if not da_thanh_cong: xoa_thu_muc_an_toan(job_folder)

    return StreamingResponse(event_generator(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"})


@router.api_route("/tai-ve-zip/{job_id}", methods=["GET", "HEAD"])
def tai_ve_zip_theo_job(job_id: str) -> FileResponse:
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


@router.api_route("/tai-ve-word/{job_id}", methods=["GET", "HEAD"])
def tai_ve_word_theo_job(job_id: str) -> FileResponse:
    job_folder = TEMP_FOLDER / f"job_{job_id}"
    if not job_folder.exists() or not job_folder.is_dir():
        raise HTTPException(status_code=404, detail="Job không tồn tại hoặc đã bị dọn")

    ds_docx = sorted(job_folder.glob("*_ieee.docx"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not ds_docx:
        ds_docx = sorted(job_folder.glob("*.docx"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not ds_docx:
        raise HTTPException(status_code=404, detail="Không tìm thấy file .docx trong job")

    docx_path = ds_docx[0]
    return FileResponse(
        path=str(docx_path),
        filename=docx_path.name,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename={docx_path.name}", "Access-Control-Expose-Headers": "Content-Disposition"},
    )


@router.api_route("/download/{job_id}", methods=["GET", "HEAD"])
def tai_ve_theo_job(job_id: str, db: Session = Depends(lay_db), current_user: models.User = Depends(auth.lay_nguoi_dung_hien_tai)) -> FileResponse:
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


@router.post("/compile-pdf/{job_id}")
async def bien_dich_pdf_theo_job(job_id: str, request: Request, payload: dict = Body(None)) -> JSONResponse:
    """Biên dịch PDF từ file .tex đã tạo (step 2 — tách riêng khỏi conversion)."""
    request_id = getattr(request.state, "request_id", "-")
    logger.info("request_id=%s job_id=%s Triggering PDF compilation", request_id, job_id)
    job_folder = TEMP_FOLDER / f"job_{job_id}"
    if not job_folder.exists() or not job_folder.is_dir():
        raise HTTPException(status_code=404, detail="Job không tồn tại hoặc đã bị dọn")

    danh_sach_tex = sorted(job_folder.glob('*.tex'), key=lambda p: p.stat().st_mtime, reverse=True)
    if not danh_sach_tex:
        raise HTTPException(status_code=404, detail="Không tìm thấy file .tex trong job")
    
    # 🛡️ Thay rename bằng copy2 để tránh WinError 2 khi gọi đúp
    original_tex = danh_sach_tex[0]
    original_tex_name = original_tex.name
    tex_path = job_folder / "job_output.tex"
    if original_tex_name != "job_output.tex":
        try:
            if tex_path.exists(): tex_path.unlink()
            import shutil
            shutil.copy2(original_tex, tex_path)
        except Exception as e:
            logger.warning("request_id=%s job_id=%s Failed to copy to safe filename", request_id, job_id, exc_info=e)
            tex_path = original_tex # Fallback to original if copy fails
            original_tex_name = tex_path.name

    try:
        thanh_cong, thong_bao_loi = await run_in_threadpool(bien_dich_latex, str(tex_path))
        if not thanh_cong:
            missing_file_match = re.search(r"! LaTeX Error: File `(.*?)' not found.", thong_bao_loi)
            if missing_file_match:
                return JSONResponse(status_code=422, content={
                    "thanh_cong": False,
                    "loi": f"Thiếu thư viện: '{missing_file_match.group(1)}'",
                })
            chi_tiet_loi = phan_tich_log_latex(thong_bao_loi)
            return JSONResponse(status_code=422, content={
                "thanh_cong": False,
                "loi": chi_tiet_loi.get("thong_diep", "Biên dịch thất bại"),
                "chi_tiet": chi_tiet_loi,
            })

        # Trích xuất số trang từ log
        so_trang = None
        try:
            log_path = tex_path.with_suffix('.log')
            if log_path.exists():
                match = re.search(
                    r'Output written on .*?\((\d+) pages?[,\)]',
                    log_path.read_text('utf-8', 'ignore'), re.DOTALL
                )
                if match:
                    so_trang = int(match.group(1))
        except Exception:
            pass
        # Đường dẫn PDF kết quả (sử dụng base name mới)
        pdf_name = tex_path.with_suffix('.pdf').name
        pdf_path = job_folder / pdf_name
        
        if not pdf_path.exists():
            return JSONResponse(status_code=500, content={
                "thanh_cong": False,
                "loi": "Biên dịch không tạo được file PDF",
            })

        # Dọn file rác biên dịch
        don_dep_file_rac(str(tex_path))

        # Tên PDF đẹp (dựa vào tên file gốc)
        ten_pdf_dep = original_tex_name.replace('.tex', '.pdf')

        return JSONResponse(status_code=200, content={
            "thanh_cong": True,
            "so_trang": so_trang,
            "ten_file_pdf": ten_pdf_dep,
            "pdf_url": f"/api/tai-ve-pdf/{job_id}",
        })
    except Exception as loi:
        import traceback
        logger.exception("request_id=%s job_id=%s bien_dich_pdf_theo_job CRASH", request_id, job_id)
        traceback.print_exc()
        return JSONResponse(status_code=500, content={
            "thanh_cong": False,
            "loi": f"Lỗi hệ thống khi biên dịch: {str(loi)}",
        })


@router.api_route("/tai-ve-pdf/{job_id}", methods=["GET", "HEAD"])
def tai_ve_pdf_theo_job(job_id: str) -> FileResponse:
    """Tải file PDF đã biên dịch từ job folder."""
    job_folder = TEMP_FOLDER / f"job_{job_id}"
    if not job_folder.exists() or not job_folder.is_dir():
        raise HTTPException(status_code=404, detail="Job không tồn tại hoặc đã bị dọn")

    danh_sach_pdf = sorted(job_folder.glob('*.pdf'), key=lambda p: p.stat().st_mtime, reverse=True)
    if not danh_sach_pdf:
        raise HTTPException(status_code=404, detail="Không tìm thấy file PDF — hãy biên dịch trước")

    pdf_path = danh_sach_pdf[0]
    
    # Tìm tên file gốc từ file .zip (là file có tên đẹp nhất)
    ten_hien_thi = pdf_path.name
    # Lấy zip mới nhất
    danh_sach_zip = sorted(job_folder.glob('*.zip'), key=lambda p: p.stat().st_mtime, reverse=True)
    if danh_sach_zip:
        ten_hien_thi = danh_sach_zip[0].name.replace('.zip', '.pdf')
    elif pdf_path.name == "job_output.pdf":
        ten_hien_thi = "document.pdf"

    return FileResponse(
        path=str(pdf_path), filename=ten_hien_thi, media_type="application/pdf",
        headers={
            "Content-Disposition": f"inline; filename=\"{ten_hien_thi}\"", 
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
    )
