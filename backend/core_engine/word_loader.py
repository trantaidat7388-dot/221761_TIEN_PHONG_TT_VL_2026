"""
Word input loading pipeline.

Provides a dedicated service for:
- converting macro-enabled .docm to cleaned .docx
- converting Strict Open XML documents to Transitional format
- loading the document through compatibility-aware python-docx adapter

This keeps the orchestration class focused on conversion behavior.
"""

from __future__ import annotations

import os
import shutil
import time
import zipfile
from typing import Any

from .docx_compat import mo_tai_lieu_word
from .utils import sua_docx_co_macro


def chuyen_docm_sang_docx(duong_dan_docm: str) -> str:
    """Convert .docm to .docx while removing macro artifacts."""
    duong_dan_docx = duong_dan_docm.rsplit(".", 1)[0] + "_converted.docx"
    shutil.copy2(duong_dan_docm, duong_dan_docx)
    sua_docx_co_macro(duong_dan_docx)
    return duong_dan_docx


def chuyen_strict_sang_transitional(duong_dan_strict: str) -> str:
    r"""Convert Strict Open XML to Transitional namespace mapping."""
    duong_dan_docx = duong_dan_strict.rsplit(".", 1)[0] + "_transitional.docx"

    mapping = {
        b"http://purl.oclc.org/ooxml/drawingml/main": b"http://schemas.openxmlformats.org/drawingml/2006/main",
        b"http://purl.oclc.org/ooxml/drawingml/wordprocessingDrawing": b"http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
        b"http://purl.oclc.org/ooxml/officeDocument/extendedProperties": b"http://schemas.openxmlformats.org/officeDocument/2006/extended-properties",
        b"http://purl.oclc.org/ooxml/officeDocument/math": b"http://schemas.openxmlformats.org/officeDocument/2006/math",
        b"http://purl.oclc.org/ooxml/wordprocessingml/main": b"http://schemas.openxmlformats.org/wordprocessingml/2006/main",
        b"http://purl.oclc.org/ooxml/officeDocument/customXml": b"http://schemas.openxmlformats.org/officeDocument/2006/customXml",
        b"http://purl.oclc.org/ooxml/officeDocument/docPropsVTypes": b"http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes",
        b"http://purl.oclc.org/ooxml/officeDocument/relationships/extendedProperties": b"http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties",
        b"http://purl.oclc.org/ooxml/officeDocument/relationships": b"http://schemas.openxmlformats.org/officeDocument/2006/relationships",
        b"http://purl.oclc.org/ooxml/": b"http://schemas.openxmlformats.org/",
    }

    with zipfile.ZipFile(duong_dan_strict, "r") as zin:
        with zipfile.ZipFile(duong_dan_docx, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                du_lieu = zin.read(item.filename)
                if item.filename.lower().endswith((".xml", ".rels")):
                    for old_ns, new_ns in mapping.items():
                        du_lieu = du_lieu.replace(old_ns, new_ns)
                zout.writestr(item, du_lieu)

    return duong_dan_docx


def mo_tai_lieu_word_co_fallback(duong_dan_word: str) -> tuple[Any, list[str]]:
    """Load a Word file and return loaded document plus temporary files to cleanup.

    Fallback sequence:
    1) If source is .docm, convert to cleaned .docx first.
    2) Try loading with compatibility adapter.
    3) On Strict Open XML namespace error, convert to Transitional then retry.
    """
    if not os.path.exists(duong_dan_word):
        raise FileNotFoundError(f"Không tìm thấy file: {duong_dan_word}")

    duong_dan_thuc = duong_dan_word
    temp_files: list[str] = []

    if duong_dan_word.lower().endswith(".docm"):
        duong_dan_thuc = chuyen_docm_sang_docx(duong_dan_word)
        temp_files.append(duong_dan_thuc)

    try:
        sua_docx_co_macro(duong_dan_thuc)
        time.sleep(0.1)
    except Exception:
        # Keep conversion flow alive; parser still has fallback branches.
        pass

    try:
        return mo_tai_lieu_word(duong_dan_thuc), temp_files
    except KeyError as e:
        if "officeDocument" not in str(e):
            raise RuntimeError(f"Lỗi mở file: {e}")

        transitional_path = chuyen_strict_sang_transitional(duong_dan_thuc)
        temp_files.append(transitional_path)
        try:
            return mo_tai_lieu_word(transitional_path), temp_files
        except Exception as ex:
            raise RuntimeError(f"Chuyển đổi Strict->Transitional thất bại: {ex}")
    except Exception as e:
        raise RuntimeError(f"Lỗi mở file: {e}")
