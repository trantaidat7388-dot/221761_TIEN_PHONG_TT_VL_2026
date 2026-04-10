"""Springer Word Renderer built on top of IEEE renderer infrastructure.

This renderer keeps the robust IR handling/equation/table logic from IEEEWordRenderer,
but switches layout and styles toward Springer-like Word output.
"""

from typing import Any, Dict, List

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt

from .word_ieee_renderer import IEEEWordRenderer


class SpringerWordRenderer(IEEEWordRenderer):
    """Render IR output into a Springer-like Word document."""

    def render(
        self,
        ir_data: Dict[str, Any],
        output_path: str,
        image_root_dir: str | None = None,
        springer_template_path: str | None = None,
    ) -> str:
        return super().render(
            ir_data=ir_data,
            output_path=output_path,
            image_root_dir=image_root_dir,
            ieee_template_path=springer_template_path,
        )

    def _configure_ieee_document(self, doc: Document) -> None:
        """Configure a Springer-like one-column document."""
        section = doc.sections[0]
        section.page_width = Cm(21.0)
        section.page_height = Cm(29.7)
        section.top_margin = Cm(2.2)
        section.bottom_margin = Cm(2.2)
        section.left_margin = Cm(2.3)
        section.right_margin = Cm(2.3)
        self._set_section_columns(section, 1)

        normal_style = doc.styles["Normal"]
        normal_style.font.name = "Times New Roman"
        normal_style.font.size = Pt(10)
        normal_style.paragraph_format.space_before = Pt(0)
        normal_style.paragraph_format.space_after = Pt(4)
        normal_style.paragraph_format.line_spacing = 1.15

    def _start_two_column_body(self, doc: Document) -> None:
        """Springer body stays one-column (no IEEE two-column switch)."""
        if not doc.sections:
            return
        for sec in doc.sections:
            self._set_section_columns(sec, 1)

    def _add_title_section(self, doc: Document, metadata: Dict[str, Any]) -> None:
        title = (metadata.get("title") or "").strip()
        if not title:
            return
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(self._latex_to_plain(title))
        run.bold = True
        run.font.name = "Times New Roman"
        run.font.size = Pt(16)
        p.paragraph_format.space_after = Pt(8)

    def _add_authors_table(self, doc: Document, authors: List[Dict[str, Any]]) -> None:
        if not authors:
            return
        names = [self._clean_author_name(str(a.get("name") or "")) for a in authors if str(a.get("name") or "").strip()]
        if names:
            p_name = doc.add_paragraph(", ".join(names))
            p_name.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in p_name.runs:
                run.font.name = "Times New Roman"
                run.font.size = Pt(11)

        for author in authors:
            affs = [self._latex_to_plain(str(x)).strip() for x in (author.get("affiliations") or []) if str(x).strip()]
            if affs:
                p_aff = doc.add_paragraph("; ".join(affs))
                p_aff.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for run in p_aff.runs:
                    run.font.name = "Times New Roman"
                    run.font.size = Pt(9)
                    run.italic = True

        doc.add_paragraph("")

    def _add_abstract_and_keywords(self, doc: Document, metadata: Dict[str, Any]) -> None:
        abstract = self._latex_to_plain(metadata.get("abstract") or "")
        if abstract:
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            run_label = p.add_run("Abstract. ")
            run_label.bold = True
            run_label.font.name = "Times New Roman"
            run_label.font.size = Pt(10)
            run_body = p.add_run(abstract)
            run_body.font.name = "Times New Roman"
            run_body.font.size = Pt(10)

        keywords = metadata.get("keywords") or []
        if keywords:
            kw = ", ".join(self._latex_to_plain(str(k)) for k in keywords if str(k).strip())
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            run_label = p.add_run("Keywords: ")
            run_label.bold = True
            run_label.font.name = "Times New Roman"
            run_label.font.size = Pt(10)
            run_body = p.add_run(kw)
            run_body.font.name = "Times New Roman"
            run_body.font.size = Pt(10)

    def _add_ieee_heading(self, doc: Document, text: str, level: int) -> None:
        """Springer-like heading numbering (arabic)."""
        clean = self._latex_to_plain(text)
        if not clean:
            return
        clean = clean.strip()

        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT

        if level == 1:
            self._section_index += 1
            self._subsection_counters[self._section_index] = 0
            numbered = f"{self._section_index} {clean}"
            run = p.add_run(numbered)
            run.bold = True
            run.font.name = "Times New Roman"
            run.font.size = Pt(12)
            p.paragraph_format.space_before = Pt(10)
            p.paragraph_format.space_after = Pt(4)
            return

        if self._section_index not in self._subsection_counters:
            self._subsection_counters[self._section_index] = 0
        self._subsection_counters[self._section_index] += 1
        sub_idx = self._subsection_counters[self._section_index]

        if level == 2:
            numbered = f"{self._section_index}.{sub_idx} {clean}"
            run = p.add_run(numbered)
            run.bold = True
            run.font.name = "Times New Roman"
            run.font.size = Pt(11)
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(3)
        else:
            run = p.add_run(clean)
            run.bold = True
            run.italic = True
            run.font.name = "Times New Roman"
            run.font.size = Pt(10)
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(2)

    def _add_table_caption(self, doc: Document, label: str, caption: str) -> None:
        """Springer-style table caption as a single line."""
        index = getattr(self, "_table_index", 1)
        text = f"Table {index}. {caption}" if caption else f"Table {index}."
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        run = p.add_run(text)
        run.bold = True
        run.font.name = "Times New Roman"
        run.font.size = Pt(9)
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(2)

    def _add_references(self, doc: Document, references: List[Dict[str, Any]]) -> None:
        if not references:
            return
        p = doc.add_paragraph("References")
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        for run in p.runs:
            run.bold = True
            run.font.name = "Times New Roman"
            run.font.size = Pt(12)

        for idx, ref in enumerate(references, start=1):
            if isinstance(ref, dict):
                text = self._latex_to_plain(ref.get("text") or "")
            else:
                text = self._latex_to_plain(str(ref))
            if not text:
                continue
            text = self._clean_reference_text(text)
            rp = doc.add_paragraph(f"[{idx}] {text}")
            rp.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            rp.paragraph_format.space_after = Pt(2)
            for run in rp.runs:
                run.font.name = "Times New Roman"
                run.font.size = Pt(9)
