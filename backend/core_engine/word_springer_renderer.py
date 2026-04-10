"""Springer Word Renderer built on top of IEEE renderer infrastructure.

This renderer keeps the robust IR handling/equation/table logic from IEEEWordRenderer,
but switches layout and styles toward Springer-like Word output.
"""

import re
from typing import Any, Dict, List

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt, Inches

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
        rendered_path = super().render(
            ir_data=ir_data,
            output_path=output_path,
            image_root_dir=image_root_dir,
            ieee_template_path=springer_template_path,
        )

        # Template headers often keep placeholder short title unless replaced explicitly.
        try:
            doc = Document(rendered_path)
            self._sync_template_header_title(doc, (ir_data.get("metadata") or {}).get("title") or "")
            doc.save(rendered_path)
        except Exception:
            pass

        return rendered_path

    def _sync_template_header_title(self, doc: Document, title: str) -> None:
        short_title = self._latex_to_plain(title or "").strip()
        if not short_title:
            return
        if len(short_title) > 72:
            short_title = short_title[:69].rstrip() + "..."

        placeholder_rx = re.compile(r"contribution\s+title(?:\s*\(shortened\s+if\s+too\s+long\))?", re.IGNORECASE)

        for sec in doc.sections:
            headers = [sec.header]
            for attr in ("first_page_header", "even_page_header"):
                try:
                    headers.append(getattr(sec, attr))
                except Exception:
                    continue

            for header in headers:
                for p in header.paragraphs:
                    if not p.text:
                        continue
                    if not placeholder_rx.search(p.text):
                        continue

                    changed = False
                    for run in p.runs:
                        new_text = placeholder_rx.sub(short_title, run.text or "")
                        if new_text != (run.text or ""):
                            run.text = new_text
                            changed = True

                    if not changed and p.runs:
                        p.runs[0].text = placeholder_rx.sub(short_title, p.runs[0].text or "")

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
        title_style = self._pick_style_name(["papertitle", "paper title", "Title"])
        if title_style:
            try:
                p.style = title_style
            except Exception:
                pass
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(self._latex_to_plain(title))
        if not self._using_uploaded_template:
            run.bold = True
            run.font.name = "Times New Roman"
            run.font.size = Pt(16)
        p.paragraph_format.space_after = Pt(8)

    def _add_authors_table(self, doc: Document, authors: List[Dict[str, Any]]) -> None:
        if not authors:
            return
        author_style = self._pick_style_name(["author", "Author"])
        address_style = self._pick_style_name(["address", "Address", "institute"])

        names: list[str] = []
        extra_affiliation_candidates: list[str] = []
        for a in authors:
            raw_name = str(a.get("name") or "").strip()
            if not raw_name:
                continue
            cleaned = self._clean_author_name(raw_name)
            if cleaned and self._looks_like_person_name(cleaned):
                names.append(cleaned)
            elif cleaned:
                extra_affiliation_candidates.append(cleaned)
        names = list(dict.fromkeys(names))
        if names:
            p_name = doc.add_paragraph(", ".join(names))
            if author_style:
                try:
                    p_name.style = author_style
                except Exception:
                    pass
            p_name.alignment = WD_ALIGN_PARAGRAPH.CENTER
            if not self._using_uploaded_template:
                for run in p_name.runs:
                    run.font.name = "Times New Roman"
                    run.font.size = Pt(11)

        affiliation_lines: list[str] = []
        seen: set[str] = set()
        for author in authors:
            affs = [
                self._latex_to_plain(str(x)).strip()
                for x in (author.get("affiliations") or [])
                if str(x).strip() and not self._looks_like_pure_author_name(str(x))
            ]
            email = self._latex_to_plain(str(author.get("email") or "")).strip()
            if email and not self._looks_like_email(email):
                email = ""

            if affs:
                aff_line = "; ".join(affs)
                if email and email.lower() not in aff_line.lower():
                    aff_line = f"{aff_line}; {email}"
            else:
                aff_line = email

            key = aff_line.lower().strip()
            if aff_line and key and key not in seen:
                seen.add(key)
                affiliation_lines.append(aff_line)

        for c in extra_affiliation_candidates:
            key = c.lower().strip()
            if key and key not in seen and not self._looks_like_email(c):
                seen.add(key)
                affiliation_lines.append(c)

        for line in affiliation_lines:
            p_aff = doc.add_paragraph(line)
            if address_style:
                try:
                    p_aff.style = address_style
                except Exception:
                    pass
            p_aff.alignment = WD_ALIGN_PARAGRAPH.CENTER
            if not self._using_uploaded_template:
                for run in p_aff.runs:
                    run.font.name = "Times New Roman"
                    run.font.size = Pt(9)
                    run.italic = True

        doc.add_paragraph("")

    def _add_abstract_and_keywords(self, doc: Document, metadata: Dict[str, Any]) -> None:
        abstract = self._latex_to_plain(metadata.get("abstract") or "")
        abstract = re.sub(r"^\s*abstract\s*[:.\-–—]*\s*", "", abstract, flags=re.IGNORECASE)
        abstract = re.sub(r"^\s*[-–—]{2,}\s*", "", abstract).strip()
        if abstract:
            p = doc.add_paragraph()
            abs_style = self._pick_style_name(["abstract", "Abstract"])
            if abs_style:
                try:
                    p.style = abs_style
                except Exception:
                    pass
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            run_label = p.add_run("Abstract. ")
            if not self._using_uploaded_template:
                run_label.bold = True
                run_label.font.name = "Times New Roman"
                run_label.font.size = Pt(10)
            run_body = p.add_run(abstract)
            if not self._using_uploaded_template:
                run_body.font.name = "Times New Roman"
                run_body.font.size = Pt(10)

        keywords = self._sanitize_keywords(metadata.get("keywords") or [])
        if keywords:
            kw = ", ".join(self._latex_to_plain(str(k)) for k in keywords if str(k).strip())
            kw = re.sub(r"^\s*keywords?\s*[:\-–—]*\s*", "", kw, flags=re.IGNORECASE)
            p = doc.add_paragraph()
            kw_style = self._pick_style_name(["keywords", "Keywords"])
            if kw_style:
                try:
                    p.style = kw_style
                except Exception:
                    pass
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            run_label = p.add_run("Keywords: ")
            if not self._using_uploaded_template:
                run_label.bold = True
                run_label.font.name = "Times New Roman"
                run_label.font.size = Pt(10)
            run_body = p.add_run(kw)
            if not self._using_uploaded_template:
                run_body.font.name = "Times New Roman"
                run_body.font.size = Pt(10)

    def _add_body(self, doc: Document, body_nodes: List[Dict[str, Any]]) -> None:
        for idx, node in enumerate(body_nodes):
            node_type = node.get("type", "")

            if node_type == "section":
                level = int(node.get("level", 1) or 1)
                level = max(1, min(3, level))
                text = self._latex_to_plain(node.get("text") or "")
                if text:
                    self._add_ieee_heading(doc, text, level)
                continue

            if node_type == "table":
                self._add_table_node(doc, node, force_full_width=False)
                continue

            if node_type == "list":
                self._add_list_node(doc, node)
                continue

            if node_type != "paragraph":
                continue

            raw_text = str(node.get("text") or "")
            plain = self._latex_to_plain(raw_text).strip()
            if not plain:
                continue

            if self._is_duplicate_table_title_paragraph(plain, body_nodes, idx):
                continue

            # Drop orphan IEEE caption labels that should be merged into table captions.
            if re.match(r"^\s*(?:TABLE|BANG|BẢNG)\s+[IVXLCDM\d]+\s*[:.\-]?\s*$", plain, re.IGNORECASE):
                continue

            if self._is_equation_like_paragraph(raw_text):
                self._add_equation_node(doc, raw_text)
                continue

            if "\\begin{figure" in raw_text or "\\includegraphics" in raw_text:
                self._add_figure_node(doc, raw_text)
                continue

            # Some IEEE extractions produce plain caption paragraph instead of figure node.
            if re.match(r"^Fig\.?\s*\d+\.?", plain, re.IGNORECASE):
                cap_clean = self._normalize_springer_caption(plain, "figure")
                fig_idx_match = re.match(r"^Fig\.?\s*(\d+)\.?", plain, re.IGNORECASE)
                fig_idx = int(fig_idx_match.group(1)) if fig_idx_match else max(1, self._figure_index + 1)
                self._figure_index = max(self._figure_index, fig_idx)
                p_cap = doc.add_paragraph(f"Fig. {fig_idx}. {cap_clean}" if cap_clean else f"Fig. {fig_idx}.")
                fig_style = self._pick_style_name(["figurecaption", "Figure Caption", "Caption"])
                if fig_style:
                    try:
                        p_cap.style = fig_style
                    except Exception:
                        pass
                p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
                continue

            p = doc.add_paragraph()
            body_style = self._pick_style_name(["p1a", "Normal"])
            if body_style:
                try:
                    p.style = body_style
                except Exception:
                    pass
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p.add_run(plain)

    def _is_duplicate_table_title_paragraph(self, plain: str, body_nodes: List[Dict[str, Any]], idx: int) -> bool:
        next_node = body_nodes[idx + 1] if idx + 1 < len(body_nodes) else None
        if not next_node or next_node.get("type") != "table":
            return False

        caption = self._normalize_springer_caption(str(next_node.get("caption") or ""), "table")
        if not caption:
            return False

        p_norm = re.sub(r"[^a-z0-9]+", " ", plain.lower()).strip()
        c_norm = re.sub(r"[^a-z0-9]+", " ", caption.lower()).strip()
        if len(p_norm) < 12:
            return False

        return p_norm == c_norm or p_norm in c_norm or c_norm in p_norm

    def _add_ieee_heading(self, doc: Document, text: str, level: int) -> None:
        """Springer-like heading numbering (arabic)."""
        clean = self._latex_to_plain(text)
        if not clean:
            return
        clean = self._strip_existing_heading_number(clean)

        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT

        heading_style = self._pick_style_name(
            [
                "heading1" if level == 1 else "heading2" if level == 2 else "Heading 3",
                f"Heading {min(level, 4)}",
            ]
        )
        if heading_style:
            try:
                p.style = heading_style
            except Exception:
                pass

        if level == 1:
            self._section_index += 1
            self._subsection_counters[self._section_index] = 0
            numbered = f"{self._section_index} {clean}"
            run = p.add_run(numbered)
            if not self._using_uploaded_template:
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
            if not self._using_uploaded_template:
                run.bold = True
                run.font.name = "Times New Roman"
                run.font.size = Pt(11)
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(3)
        else:
            run = p.add_run(clean)
            if not self._using_uploaded_template:
                run.bold = True
                run.italic = True
                run.font.name = "Times New Roman"
                run.font.size = Pt(10)
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(2)

    def _add_table_caption(self, doc: Document, label: str, caption: str) -> None:
        """Springer-style table caption as a single line."""
        index = getattr(self, "_table_index", 1)
        caption = self._normalize_springer_caption(caption, "table")
        text = f"Table {index}. {caption}" if caption else f"Table {index}."
        p = doc.add_paragraph()
        cap_style = self._pick_style_name(["tablecaption", "Table Caption", "Caption"])
        if cap_style:
            try:
                p.style = cap_style
            except Exception:
                pass
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        run = p.add_run(text)
        if not self._using_uploaded_template:
            run.bold = True
            run.font.name = "Times New Roman"
            run.font.size = Pt(9)
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(2)

    def _add_references(self, doc: Document, references: List[Dict[str, Any]]) -> None:
        if not references:
            return
        p = doc.add_paragraph("References")
        heading_style = self._pick_style_name(["heading1", "Heading 1", "headings"])
        if heading_style:
            try:
                p.style = heading_style
            except Exception:
                pass
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        if not self._using_uploaded_template:
            for run in p.runs:
                run.bold = True
                run.font.name = "Times New Roman"
                run.font.size = Pt(12)

        ref_style = self._pick_style_name(["referenceitem", "referencelist", "ReferenceLine", "Normal"])

        for idx, ref in enumerate(references, start=1):
            if isinstance(ref, dict):
                text = self._latex_to_plain(ref.get("text") or "")
            else:
                text = self._latex_to_plain(str(ref))
            if not text:
                continue
            text = self._clean_reference_text(text)
            while True:
                updated = re.sub(r"^\s*\[?\d+\]?\s*[\.)]?\s*", "", text)
                if updated == text:
                    break
                text = updated
            text = re.sub(r"(?<!\s)(https?://)", r" \1", text)
            text = re.sub(r"\s+", " ", text).strip()
            text = f"{idx}. {text}"
            rp = doc.add_paragraph(text)
            if ref_style:
                try:
                    rp.style = ref_style
                except Exception:
                    pass
            rp.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            rp.paragraph_format.space_after = Pt(2)
            if not self._using_uploaded_template:
                for run in rp.runs:
                    run.font.name = "Times New Roman"
                    run.font.size = Pt(9)

    def _select_table_layout_mode(self, doc: Document, node: Dict[str, Any]) -> str:
        """Springer/LNCS is single-column, keep tables in-column to match template."""
        return "column"

    def _current_table_target_width_inch(self, doc: Document, force_full_width: bool) -> float:
        if not doc.sections:
            return 6.0
        sec = doc.sections[-1]
        try:
            content_width = (sec.page_width - sec.left_margin - sec.right_margin).inches
            return max(4.8, content_width)
        except Exception:
            return 6.0

    def _add_equation_node(self, doc: Document, raw_text: str) -> None:
        """Render equation using Springer equation paragraph style when available."""
        omml_match = re.search(r"«OMML:([A-Za-z0-9+/=]+)»", raw_text)
        tag_match = re.search(r"\\tag\{([^}]*)\}", raw_text)
        if tag_match:
            tag_text = re.sub(r"\s+", "", tag_match.group(1) or "")
            eq_num = f"({tag_text})" if tag_text else ""
        else:
            trailing_num = re.search(r"\((\d{1,3}[A-Za-z]?)\)\s*$", str(raw_text or ""))
            if trailing_num and "=" in str(raw_text or ""):
                eq_num = f"({trailing_num.group(1)})"
                raw_text = str(raw_text or "")[: trailing_num.start()].rstrip()
            else:
                eq_num = ""

        clean = raw_text
        clean = re.sub(r"«OMML:([A-Za-z0-9+/=]+)»", "", clean)
        clean = re.sub(r"\\begin\{equation\*?\}", "", clean)
        clean = re.sub(r"\\end\{equation\*?\}", "", clean)
        clean = re.sub(r"\\tag\{([^}]*)\}", "", clean)
        clean = re.sub(r"\\\[", "", clean)
        clean = re.sub(r"\\\]", "", clean)
        clean = self._latex_math_to_readable(clean).strip()

        p = doc.add_paragraph()
        eq_style = self._pick_style_name(["equation", "Equation"])
        if eq_style:
            try:
                p.style = eq_style
            except Exception:
                pass
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER

        if omml_match:
            try:
                self._insert_omml_to_paragraph(p, omml_match.group(1))
            except Exception:
                if clean:
                    p.add_run(clean)
        elif clean:
            p.add_run(clean)

        if eq_num:
            p.add_run(f"  {eq_num}")

    def _is_equation_like_paragraph(self, raw_text: str) -> bool:
        if super()._is_equation_like_paragraph(raw_text):
            return True

        plain = self._latex_to_plain(str(raw_text or "")).strip()
        if not plain or len(plain) > 180:
            return False
        if re.search(r"https?://", plain, re.IGNORECASE):
            return False

        has_trailing_number = bool(re.search(r"\(\d{1,3}[A-Za-z]?\)\s*$", plain))
        has_math_relation = "=" in plain or any(sym in plain for sym in ["≤", "≥", "∑", "∫", "∞"])
        has_math_token = bool(re.search(r"\b(BA|F1|AUC|ROC|RMSE|MSE|Precision|Recall|Specificity|Sensitivity)\b", plain, re.IGNORECASE))

        if has_math_relation and (has_trailing_number or has_math_token):
            return True

        return False

    def _add_figure_node(self, doc: Document, latex_figure_text: str) -> None:
        """Render Springer figure with centered image and `figurecaption` style below."""
        self._figure_index += 1

        path_match = re.search(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", latex_figure_text)
        cap_match = re.search(r"\\caption\{([^}]*)\}", latex_figure_text)
        image_path = self._latex_to_plain(path_match.group(1)) if path_match else ""
        caption = self._normalize_springer_caption(
            self._latex_to_plain(cap_match.group(1)) if cap_match else "",
            "figure",
        )

        resolved = self._resolve_image_path(image_path)
        if resolved and resolved.exists():
            try:
                pic_para = doc.add_paragraph()
                pic_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                width = max(3.2, min(5.6, self._current_table_target_width_inch(doc, False)))
                pic_para.add_run().add_picture(str(resolved), width=Inches(width))
            except Exception:
                pass

        cap_text = f"Fig. {self._figure_index}. {caption}" if caption else f"Fig. {self._figure_index}."
        p = doc.add_paragraph(cap_text)
        fig_style = self._pick_style_name(["figurecaption", "Figure Caption", "Caption"])
        if fig_style:
            try:
                p.style = fig_style
            except Exception:
                pass
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    def _sanitize_keywords(self, keywords: List[Any]) -> List[str]:
        cleaned: list[str] = []
        for item in keywords:
            raw = self._latex_to_plain(str(item or "")).strip()
            if not raw:
                continue
            # Guard against parser over-capturing whole body into keywords.
            candidates = [x.strip(" .;:-") for x in raw.split(",") if x.strip()]
            for c in candidates:
                c = re.sub(r"^keywords?\s*[-–—:]*\s*", "", c, flags=re.IGNORECASE).strip()
                if not c:
                    continue
                if len(c) > 60:
                    continue
                if len(c.split()) > 5:
                    continue
                if "." in c:
                    continue
                if c.lower() in {"however", "therefore", "thus", "and", "or", "are", "is"}:
                    continue
                if len(c.split()) <= 2 and c.lower() == c:
                    continue
                if re.search(r"\b(section|introduction|references|table|figure)\b", c, re.IGNORECASE):
                    continue
                cleaned.append(c)
        return list(dict.fromkeys(cleaned))

    def _normalize_springer_caption(self, caption: str, kind: str) -> str:
        text = (caption or "").replace("\n", " ").strip()
        if not text:
            return ""

        if kind == "table":
            text = re.sub(r"^\s*table\s*(?:[ivxlcdm]{1,8}|\d+)\b\s*[:.\-]?\s*", "", text, flags=re.IGNORECASE)
            text = re.sub(r"^\s*TABLE\s*(?:[IVXLCDM]{1,8}|\d+)\b\s*[:.\-]?\s*", "", text)
        else:
            text = re.sub(r"^\s*fig(?:ure)?\.?\s*\d+\s*[:.\-]?\s*", "", text, flags=re.IGNORECASE)

        text = re.sub(r"\s+", " ", text).strip(" .")
        return text

    def _strip_existing_heading_number(self, text: str) -> str:
        clean = (text or "").strip()
        # Remove duplicated numbering patterns like "3 3 TITLE" or "3.2 3.2 TITLE".
        clean = re.sub(r"^\s*(\d+(?:\.\d+)?)\s+\1\s+", "", clean)
        # Remove one leading numbering token that likely comes from source style.
        clean = re.sub(r"^\s*(?:\d+(?:\.\d+)?|[IVXLCDM]+|[A-Z])\s*[.)]?\s+", "", clean)
        return clean.strip()

    def _looks_like_affiliation_text(self, text: str) -> bool:
        value = (text or "").lower()
        if self._looks_like_email(value):
            return True
        hints = [
            "university", "institute", "department", "faculty", "school",
            "city", "country", "street", "road", "heidelberg", "princeton",
            "vietnam", "việt", "college", "laboratory", "lab",
        ]
        return any(h in value for h in hints) or bool(re.search(r"\d", value))

    def _looks_like_person_name(self, text: str) -> bool:
        value = (text or "").strip()
        if not value:
            return False
        if self._looks_like_email(value):
            return False

        normalized = re.sub(r"\[[^\]]+\]", "", value)
        normalized = re.sub(r"\d+", "", normalized).strip()
        words = [w for w in re.split(r"\s+", normalized) if w]
        if len(words) < 2 or len(words) > 6:
            return False

        lower = normalized.lower()
        bad_tokens = {
            "university", "institute", "department", "faculty", "school",
            "springer", "street", "road", "city", "country",
            "usa", "germany", "vietnam", "heidelberg", "princeton", "tiergartenstr", "nj",
        }
        if any(tok in lower for tok in bad_tokens):
            return False
        if re.search(r"\b\d{4,}\b", value):
            return False
        return True

    def _looks_like_pure_author_name(self, text: str) -> bool:
        value = self._clean_author_name(text)
        if not value:
            return False
        words = [w for w in re.split(r"\s+", value) if w]
        return 1 <= len(words) <= 6 and all(not re.search(r"\d", w) for w in words)

    def _clean_author_name(self, raw_name: str) -> str:
        text = super()._clean_author_name(raw_name)
        text = re.sub(r"\[[^\]]+\]", "", text)
        text = re.sub(r"\s+", " ", text).strip(" ,;")
        return text
