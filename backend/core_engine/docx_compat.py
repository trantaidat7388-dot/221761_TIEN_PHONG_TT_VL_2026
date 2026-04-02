"""
Compatibility helpers for python-docx integration.

This module isolates monkey-patch behavior so patches are applied in one place,
with explicit invocation and idempotent guards.
"""

from __future__ import annotations

from typing import Any

import docx
import docx.api
from docx.opc.constants import CONTENT_TYPE as CT
from docx.opc.part import PartFactory
from docx.package import Package
from docx.parts.document import DocumentPart
from docx.text.paragraph import Paragraph
from docx.text.run import Run

DOCM_CONTENT_TYPE = "application/vnd.ms-word.document.macroEnabled.main+xml"

_PATCH_APPLIED = False


def mo_tai_lieu_word(docx_path: str | None = None) -> Any:
    """Load a Word document supporting both docx and docm MIME types."""
    from docx.api import _default_docx_path

    candidate_path = _default_docx_path() if docx_path is None else docx_path
    document_part = Package.open(candidate_path).main_document_part

    allowed_word_mime_types = [
        CT.WML_DOCUMENT_MAIN,
        DOCM_CONTENT_TYPE,
    ]

    if document_part.content_type not in allowed_word_mime_types:
        tmpl = "file '%s' is not a Word file, content type is '%s'"
        raise ValueError(tmpl % (candidate_path, document_part.content_type))
    return document_part.document


def _lay_toan_bo_van_ban(self) -> str:
    return "".join(node.text for node in self._element.xpath(".//w:t") if node.text)


def _lay_toan_bo_run(self) -> list[Run]:
    return [Run(r, self) for r in self._element.xpath(".//w:r")]


def ap_dung_ban_va_tuong_thich_docx() -> None:
    """Apply all python-docx compatibility patches exactly once."""
    global _PATCH_APPLIED
    if _PATCH_APPLIED:
        return

    PartFactory.part_type_for[DOCM_CONTENT_TYPE] = DocumentPart

    # Patch constructors used by upstream docx API.
    docx.Document = mo_tai_lieu_word
    docx.api.Document = mo_tai_lieu_word

    # Patch paragraph accessors so inline content-control text is preserved.
    Paragraph.text = property(_lay_toan_bo_van_ban)
    Paragraph.runs = property(_lay_toan_bo_run)

    _PATCH_APPLIED = True
