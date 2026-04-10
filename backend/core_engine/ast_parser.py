import os
import re
import hashlib
import base64
from typing import Dict, Any, List, Optional
from lxml import etree

from docx.table import Table
from docx.text.paragraph import Paragraph
from docx.text.run import Run

from .config import MAP_STYLE, HEADING_PATTERNS, A_NAMESPACE, REL_NAMESPACE, W_NAMESPACE
from docx.oxml.ns import qn
from .utils import loc_ky_tu
from .xu_ly_toan import BoXuLyToan
from .xu_ly_ole_equation import ole_equation_to_latex
from .semantic_parser import du_doan_loai_node
from .word_loader import mo_tai_lieu_word_co_fallback

class WordASTParser:
    """
    Parser converts a Word document (.docx) into an Intermediate Representation (IR).
    The IR is a JSON-serializable dictionary capturing the semantic meaning of the document
    (Metadata + Body Nodes) independently of LaTeX layout.
    """
    def __init__(self, doc_path: str, thu_muc_anh: str = "images"):
        self.doc_path = doc_path
        self.thu_muc_anh = thu_muc_anh
        self.doc = None
        self._temp_word_files: List[str] = []
        self.bo_toan = BoXuLyToan()
        self.dem_anh = 0
        self.total_formulas = 0
        
        # Intermediate Representation
        self.ir: Dict[str, Any] = {
            "metadata": {
                "title": "",
                "authors": [],
                "abstract": "",
                "keywords": [],
                "total_formulas": 0
            },
            "body": [],
            "references": []
        }
        
    def parse(self) -> Dict[str, Any]:
        """Main entry point to parse the document."""
        try:
            self.doc, self._temp_word_files = mo_tai_lieu_word_co_fallback(self.doc_path)

            elements = self._extract_elements_in_order()
            self._build_semantic_tree(elements)
            self._post_process_citations()

            return self.ir
        finally:
            for temp_path in self._temp_word_files:
                try:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                except Exception:
                    pass
        
    def _extract_elements_in_order(self) -> List[tuple]:
        """Flatten the document body including elements inside content controls."""
        elements = []
        body = self.doc.element.body
        
        def traverse(node):
            if not hasattr(node, "tag") or not isinstance(node.tag, str):
                return
            tag = node.tag.split("}")[-1]
            if tag == "p":
                elements.append(("paragraph", Paragraph(node, self.doc)))
                # Capture nested blocks only from explicit containers where paragraph
                # text is semantically embedded (e.g., text boxes / content controls),
                # avoiding broad recursion that can duplicate paragraphs.
                seen_container_ids = set()
                for descendant in node.iter():
                    dtag = descendant.tag.split("}")[-1] if hasattr(descendant, "tag") and isinstance(descendant.tag, str) else ""
                    if dtag in ("txbxContent", "sdtContent"):
                        did = id(descendant)
                        if did in seen_container_ids:
                            continue
                        seen_container_ids.add(did)
                        for nested in descendant:
                            traverse(nested)
            elif tag == "tbl":
                elements.append(("table", Table(node, self.doc)))
            else:
                for child in node:
                    traverse(child)
                    
        for node in body:
            traverse(node)
            
        return elements
        
    def _is_abstract_label(self, text: str) -> bool:
        norm = re.sub(r"^[\d\.]+\s*", "", text.strip().upper())
        return norm.startswith("ABSTRACT") or norm.startswith("TÓM TẮT") or norm.startswith("TOM TAT")
        
    def _is_keywords_label(self, text: str) -> bool:
        norm = text.strip().upper()
        # ACM style often uses "Additional Keywords and Phrases:"
        for kw in ["KEYWORDS", "TỪ KHÓA", "TU KHOA", "INDEX TERMS"]:
            if kw in norm:
                return True
        return False

    def _image_ext_from_content_type(self, content_type: str) -> str:
        ct = (content_type or '').lower()
        if 'jpeg' in ct:
            return 'jpg'
        if 'x-emf' in ct or ct.endswith('/emf'):
            return 'emf'
        if 'x-wmf' in ct or ct.endswith('/wmf'):
            return 'wmf'
        if '/' in ct:
            return ct.split('/')[-1]
        return 'png'

    def _save_image_from_relationship(self, rel) -> Optional[str]:
        """Persist image blob and return LaTeX path; convert EMF/WMF to PNG when possible."""
        try:
            img_blob = rel.target_part.blob
            img_ext = self._image_ext_from_content_type(getattr(rel.target_part, 'content_type', ''))

            img_hash = hashlib.md5(img_blob).hexdigest()[:8]
            if self.thu_muc_anh:
                os.makedirs(self.thu_muc_anh, exist_ok=True)
                out_dir = self.thu_muc_anh
            else:
                out_dir = ''

            if img_ext in ('emf', 'wmf'):
                source_name = f"img_{img_hash}.{img_ext}"
                source_path = os.path.join(out_dir, source_name) if out_dir else source_name
                if not os.path.exists(source_path):
                    with open(source_path, "wb") as f:
                        f.write(img_blob)
                try:
                    from PIL import Image
                    with Image.open(source_path) as img:
                        png_name = f"img_{img_hash}.png"
                        png_path = os.path.join(out_dir, png_name) if out_dir else png_name
                        img.convert("RGBA").save(png_path, format="PNG")
                    try:
                        if os.path.exists(source_path):
                            os.remove(source_path)
                    except Exception:
                        pass
                    final_name = png_name
                except Exception:
                    print(f"[WARN] Skip unsupported vector image format: {source_name}")
                    return None
            else:
                final_name = f"img_{img_hash}.{img_ext}"
                final_path = os.path.join(out_dir, final_name) if out_dir else final_name
                if not os.path.exists(final_path):
                    with open(final_path, "wb") as f:
                        f.write(img_blob)

            ten_thu_muc = os.path.basename(self.thu_muc_anh) if self.thu_muc_anh else ''
            return f"{ten_thu_muc}/{final_name}" if ten_thu_muc else final_name
        except Exception:
            return None

    def _includegraphics_options(self, width_expr: str) -> str:
        """Use bounded image sizing to preserve layout when source vector crop info is lossy."""
        return f"width={width_expr},height=0.35\\textheight,keepaspectratio"
        
    def _is_body_label(self, text: str) -> bool:
        norm = re.sub(r"^[\d\.]+\s*", "", text.strip().upper())
        for kw in ["INTRODUCTION", "GIỚI THIỆU", "GIOI THIEU", "MỞ ĐẦU", "CHAPTER 1", "BACKGROUND"]:
            if norm.startswith(kw):
                return True
        if re.match(r"^[IV]+\.\s+", text.strip()):
            return True
        return False

    def _is_authors_label(self, text: str) -> bool:
        norm = text.strip().upper()
        for kw in ["AUTHORS", "TÁC GIẢ", "TAC GIA"]:
            if kw in norm and len(text) < 15:
                return True
        return False

    def _is_references_label(self, text: str) -> bool:
        norm = re.sub(r"^[\d\.]+\s*", "", text.strip().upper())
        # Avoid false positives like "References and Footnotes" in publisher templates.
        if re.match(r"^REFERENCES\s*[:\.]?$", norm):
            return True
        if re.match(r"^BIBLIOGRAPHY\s*[:\.]?$", norm):
            return True
        if norm.startswith("TÀI LIỆU THAM KHẢO") or norm.startswith("TAI LIEU THAM KHAO"):
            return True
        return False

    def _looks_like_reference_entry(self, text: str) -> bool:
        t = (text or '').strip()
        if not t or len(t) < 12:
            return False
        tl = t.lower()

        # Skip common guide/template lines.
        if re.match(r'^(examples?:|footnotes?|references?\s+and\s+footnotes|books?|periodicals?|reports?|patents?|electronic\s+sources|standards?)\b', tl):
            return False
        if tl.startswith("reference numbers are set"):
            return False
        if tl.startswith("other than books"):
            return False
        if tl.startswith("for papers published"):
            return False
        if "first check if you have an existing account" in tl:
            return False
        if "ieee.org/publications_standards/publications/" in tl:
            return False

        # Typical bibliography signals.
        if re.search(r'\b(19|20)\d{2}\b', t):
            return True
        if re.search(r'\b(doi|arxiv|vol\.|pp\.|patent|thesis|dissertation|tech\.\s*rep\.|[Oo]nline\.|available:)\b', t):
            return True
        if re.search(r'https?://|www\.', t):
            return True

        # Author-like leading pattern: initials/names followed by comma.
        if re.match(r'^([A-Z]\.\s*){1,4}[A-Za-z\-\']+\s*,', t):
            return True

        return False

    # ====== HEURISTIC: Table/Image detection (ported from legacy xu_ly_bang.py) ======

    def _la_bang_chua_anh(self, table: Table) -> bool:
        """Phát hiện bảng chứa chủ yếu ảnh (figure layout).
        Ported from BoXuLyBang.la_bang_chua_anh()."""
        try:
            so_cell_co_anh = 0
            so_cell_co_text_dai = 0
            tong_cell = 0
            cells_da_kiem = set()

            for hang in table.rows:
                for cell in hang.cells:
                    cell_id = id(cell._tc)
                    if cell_id in cells_da_kiem:
                        continue
                    cells_da_kiem.add(cell_id)
                    tong_cell += 1
                    cell_text = cell.text.strip()
                    co_anh = False

                    for para in cell.paragraphs:
                        for run in para.runs:
                            blips = run._element.findall(f'.//{{{A_NAMESPACE}}}blip')
                            if blips:
                                co_anh = True
                                break
                        drawings = para._element.findall(f'.//{{{A_NAMESPACE}}}blip')
                        if drawings:
                            co_anh = True

                    if co_anh:
                        so_cell_co_anh += 1

                    if re.match(r'^[\(\[]*[a-zA-Z0-9][\)\]]*\.?$', cell_text):
                        pass
                    elif re.match(r'^(Hình|Figure|Fig\.?|Bảng|Table)\s*\d+(\.\d+)*', cell_text, re.IGNORECASE):
                        pass
                    elif len(cell_text) > 20:
                        so_cell_co_text_dai += 1

            if tong_cell == 0:
                return False
            if so_cell_co_anh >= 1:
                if so_cell_co_text_dai <= 1:
                    return True
                if so_cell_co_anh / tong_cell >= 0.3:
                    return True
        except Exception as e:
            print(f'[Cảnh báo] la_bang_chua_anh (AST): {e}')
        return False

    def _trich_xuat_anh_tu_bang(self, table: Table) -> List[str]:
        """Trích xuất ảnh từ bảng figure-layout, lưu vào thu_muc_anh.
        Ported from BoXuLyBang.trich_xuat_anh_tu_bang()."""
        danh_sach_anh = []
        seen_names = set()
        for hang in table.rows:
            for cell in hang.cells:
                for para in cell.paragraphs:
                    for run in para.runs:
                        blips = run._element.findall(f'.//{{{A_NAMESPACE}}}blip')
                        for blip in blips:
                            embed = blip.get(f'{{{REL_NAMESPACE}}}embed')
                            if not embed:
                                continue
                            try:
                                rel = para.part.rels.get(embed)
                                if not rel:
                                    continue
                                latex_path = self._save_image_from_relationship(rel)
                                if not latex_path:
                                    continue
                                img_name = os.path.basename(latex_path)
                                if img_name not in seen_names:
                                    seen_names.add(img_name)
                                    danh_sach_anh.append(img_name)
                            except Exception:
                                pass
        return danh_sach_anh

    def _tim_caption_con_trong_bang(self, table: Table) -> List[str]:
        """Tìm caption con (a), (b)... trong các cell của bảng."""
        danh_sach = []
        try:
            for hang in table.rows:
                for cell in hang.cells:
                    text = cell.text.strip()
                    match = re.match(r'^\(([a-z])\)(.*)$', text)
                    if match:
                        nhan = match.group(1)
                        mo_ta = match.group(2).strip()
                        caption = f"({nhan})"
                        if mo_ta:
                            caption += f" {mo_ta}"
                        danh_sach.append(loc_ky_tu(caption))
        except Exception:
            pass
        return danh_sach

    def _bat_caption_bang(self, elements: List[tuple], idx: int, used_nodes: set) -> str:
        """Bắt caption thật của bảng từ paragraph ngay phía TRÊN (idx - 1).
        Ported from ChuyenDoiWordSangLatex.bat_caption_bang()."""
        try:
            idx_truoc = idx - 1
            if idx_truoc < 0 or idx_truoc >= len(elements):
                return None
            loai, phan_tu = elements[idx_truoc]
            if loai != 'paragraph':
                return None
            text = phan_tu.text.strip()
            if not text:
                return None
            if re.match(r'^(BẢNG|BANG|TABLE)\b', text, re.IGNORECASE):
                used_nodes.add(idx_truoc)
                caption_text = self._chuan_hoa_ten_caption(text, kind='table')
                return caption_text
        except Exception as e:
            print(f"[Cảnh báo] _bat_caption_bang: {e}")
        return None

    def _bat_caption_hinh_theo_style(self, elements: List[tuple], idx: int, used_nodes: set) -> str:
        """Fallback caption extraction for templates using dedicated caption styles.

        Supports patterns like "Example of a figure caption. (figure caption)"
        even when they do not start with "Figure/Fig".
        """
        def _extract_text(raw: str) -> str:
            txt = loc_ky_tu((raw or '').strip())
            if not txt:
                return ""
            txt = re.sub(r'\(\s*figure\s+caption\s*\)', '', txt, flags=re.IGNORECASE).strip()
            txt = re.sub(r'^(example\s+of\s+a\s+)?figure\s+caption\s*[:\-–]\s*', '', txt, flags=re.IGNORECASE).strip()
            txt = re.sub(r'\s{2,}', ' ', txt)
            return txt

        # Prefer nearby look-ahead first.
        for buoc in range(1, 16):
            j = idx + buoc
            if j >= len(elements):
                break
            loai, phan_tu = elements[j]
            if loai != 'paragraph':
                continue
            text = (phan_tu.text or '').strip()
            if not text:
                continue
            style_name = (phan_tu.style.name if phan_tu.style else '').lower()
            if 'heading 1' in style_name:
                break
            is_caption_style = ('figure caption' in style_name) or ('caption' == style_name)
            is_caption_marker = 'figure caption' in text.lower()
            if is_caption_style or is_caption_marker:
                used_nodes.add(j)
                cleaned = _extract_text(text)
                if cleaned:
                    return cleaned

        # Then short look-behind.
        for buoc in range(1, 8):
            j = idx - buoc
            if j < 0:
                break
            loai, phan_tu = elements[j]
            if loai != 'paragraph':
                continue
            text = (phan_tu.text or '').strip()
            if not text:
                continue
            style_name = (phan_tu.style.name if phan_tu.style else '').lower()
            is_caption_style = ('figure caption' in style_name) or ('caption' == style_name)
            is_caption_marker = 'figure caption' in text.lower()
            if is_caption_style or is_caption_marker:
                used_nodes.add(j)
                cleaned = _extract_text(text)
                if cleaned:
                    return cleaned

        return None

    def _bat_caption_hinh(self, elements: List[tuple], idx: int, used_nodes: set) -> str:
        """Bắt caption thật của hình từ paragraph phía DƯỚI (tìm tối đa 5 đoạn).
        Ported from ChuyenDoiWordSangLatex.bat_caption_hinh()."""
        try:
            for buoc in range(1, 6):
                idx_sau = idx + buoc
                if idx_sau >= len(elements):
                    break
                loai, phan_tu = elements[idx_sau]
                if loai == 'table':
                    break
                if loai != 'paragraph':
                    continue
                text = phan_tu.text.strip()
                if not text:
                    continue
                # FIX 1: Support decimal chapter numbers like "Figure 3.1" and IEEE "Fig. 1."
                if re.match(r'^(HÌNH|HINH|ẢNH|ANH|FIGURE|FIG)(?:\.|\b)', text, re.IGNORECASE):
                    used_nodes.add(idx_sau)
                    caption_text = self._chuan_hoa_ten_caption(text, kind='figure')
                    return caption_text
                # Dừng nếu gặp section heading mới
                if hasattr(phan_tu, 'style') and phan_tu.style and phan_tu.style.name and 'Heading' in phan_tu.style.name:
                    break
        except Exception as e:
            print(f"[Cảnh báo] _bat_caption_hinh: {e}")
        return None

    def _chuan_hoa_ten_caption(self, text: str, kind: str) -> str:
        """Return pure caption content without leading label/number.

        This ensures display style (Table/Fig naming) is delegated to the
        LaTeX template/class instead of duplicating labels from Word input.
        """
        caption_text = loc_ky_tu((text or '').strip())
        if not caption_text:
            return caption_text

        if kind == 'table':
            # Examples stripped: "Table 1:", "TABLE 3.1 -", "BANG 2.", "TABLE I" (IEEE)
            pattern = r'^(Bảng|BANG|Bang|Table|TABLE)\.?\s*[\dIIVX]+(\.\d+)*\s*[:\.\-–—]?\s*'
        else:
            # Examples stripped: "Figure 2:", "Fig. 3.1", "HINH 1 -", "ẢNH 5"
            pattern = r'^(Hình|HINH|Hình|Ảnh|ANH|ẢNH|Figure|FIGURE|Fig\.?)\s*\d+(\.\d+)*\s*[:\.\-–—]?\s*'

        caption_text = re.sub(pattern, '', caption_text, flags=re.IGNORECASE).strip()
        return caption_text

    def _is_title_paragraph(self, p: Paragraph, idx: int) -> bool:
        """Heuristic for title: usually bold, large, or specific style 'Title'."""
        text = p.text.strip()
        if not text or len(text) < 3: return False
        if "Short Title" in text or "ACM Reference Format" in text: return False
        
        style_name = p.style.name if p.style else ""
        style_lc = style_name.lower()
        if "title" in style_lc or "header" in style_lc:
            return True
        
        # Heuristics: Center aligned + Bold or Large font + Bold
        aligned_center = False
        try:
            if p.paragraph_format.alignment == 1: aligned_center = True
        except: pass
        
        runs = p.runs
        all_bold = all(r.bold for r in runs if r.text.strip()) if runs else False
        large_font = any(r.font.size and r.font.size.pt >= 14 for r in runs) if runs else False
        
        if (aligned_center and all_bold) or (large_font and all_bold):
            return True
            
        return False

    def _build_semantic_tree(self, elements: List[tuple]):
        """State machine to classify elements into Metadata vs Body nodes."""
        print(f"[*] _build_semantic_tree: Processing {len(elements)} elements")
        state = "pre_title"
        
        # Temp buffers for metadata
        title_buf = []
        authors_buf = []
        abstract_buf = []
        keywords_buf = []
        seen_figure_paths = set()
        
        # Set of element indices already used as captions (skip in body)
        used_nodes = set()
        
        # Pre-scan: mark caption paragraphs (Table captions above, Figure captions below)
        for idx, (etype, element) in enumerate(elements):
            if etype == 'table':
                # Table caption: look 1 paragraph ABOVE
                if idx > 0:
                    prev_type, prev_el = elements[idx - 1]
                    if prev_type == 'paragraph':
                        text = prev_el.text.strip()
                        if text and re.match(r'^(BẢNG|BANG|TABLE)\b', text, re.IGNORECASE):
                            used_nodes.add(idx - 1)
            if etype == 'paragraph':
                # Check if this paragraph has images (look for drawings/blips or vml/imagedata)
                has_img = bool(element._p.findall(f'.//{{{A_NAMESPACE}}}blip')) or bool(element._p.findall(r'.//{urn:schemas-microsoft-com:vml}imagedata'))
                if has_img:
                    # Figure caption: look 1-5 paragraphs BELOW
                    # FIX 1: Match decimal figure numbers like "Figure 3.1"
                    for step in range(1, 6):
                        idx_after = idx + step
                        if idx_after >= len(elements):
                            break
                        a_type, a_el = elements[idx_after]
                        if a_type == 'table':
                            break
                        if a_type != 'paragraph':
                            continue
                        a_text = a_el.text.strip()
                        if not a_text:
                            continue
                        if re.match(r'^(HÌNH|HINH|ẢNH|ANH|FIGURE|FIG)(?:\.|\b)', a_text, re.IGNORECASE):
                            used_nodes.add(idx_after)
                            break
                        if hasattr(a_el, 'style') and a_el.style and a_el.style.name and 'Heading' in a_el.style.name:
                            break
        
        for idx, (etype, element) in enumerate(elements):
            # Skip paragraphs already consumed as captions
            if idx in used_nodes:
                continue
                
            text = ""
            is_bold = False
            prediction = "PARAGRAPH"
            style_name = ""
            style_cmd = ""
            
            if etype == "paragraph":
                text = element.text.strip()
                has_img_para = bool(element._p.findall(f'.//{{{A_NAMESPACE}}}blip')) or bool(element._p.findall(r'.//{urn:schemas-microsoft-com:vml}imagedata'))
                if not text and state == "pre_title" and (not has_img_para):
                    continue # Skip empty leading lines (but keep image-only paragraphs)
                if text == "Short Title": continue
                
                style_name = element.style.name if element.style else ""
                style_cmd = MAP_STYLE.get(style_name, "")
                
                # Font features
                for r in element.runs:
                    if r.text.strip() and r.bold:
                        is_bold = True
                        break
                prediction = du_doan_loai_node(text, idx, is_bold)

                # State Transitions
                if state == "pre_title":
                    if style_cmd == r"\title" or self._is_title_paragraph(element, idx):
                        state = "title"
                    elif self._is_abstract_label(text) or prediction == "ABSTRACT" or style_name == "Abstract":
                        state = "abstract"
                    elif (
                        self._is_authors_label(text)
                        or style_cmd == r"\author"
                        or prediction == "AUTHOR"
                        or style_name in ("Authors", "Author", "AuthorsBlock")
                        or style_name.lower() in ("authors", "author", "authorsblock")
                    ):
                        state = "authors"
                    elif self._is_body_label(text) or prediction == "HEADING" or style_name.startswith("Heading"):
                        state = "body"
                
                # State-specific transition checks (to exit current state)
                if state == "title":
                    if style_name == "Subtitle" or style_name == "subtitle":
                        state = "title"
                    elif self._is_abstract_label(text) or prediction == "ABSTRACT" or style_name == "Abstract":
                        state = "abstract"
                    elif self._is_body_label(text) or prediction == "HEADING" or style_name.startswith("Heading"):
                        state = "body"
                    elif (len(text) > 250 or prediction == "AUTHOR" or style_name in ("Authors", "AuthorsBlock", "Author") or self._is_authors_label(text)):
                        state = "authors"
                        
                elif state == "authors":
                    if (self._is_abstract_label(text) or prediction == "ABSTRACT" or style_name == "Abstract" or
                        self._is_keywords_label(text) or prediction == "KEYWORDS" or style_name in ("KeyWords", "Keywords", "CCSCONCEPTS") or
                        self._is_body_label(text) or prediction == "HEADING" or style_name.startswith("Heading") or
                        (style_name in ("BodyText", "Body Text", "Normal") and len(text) > 100)):
                        
                        if self._is_abstract_label(text) or prediction == "ABSTRACT" or style_name == "Abstract":
                            state = "abstract"
                        elif self._is_keywords_label(text) or prediction == "KEYWORDS" or style_name in ("KeyWords", "Keywords", "CCSCONCEPTS"):
                            state = "keywords"
                        else:
                            state = "body"

                elif state == "abstract":
                    if (self._is_keywords_label(text) or prediction == "KEYWORDS" or style_name in ("KeyWords", "Keywords", "CCSCONCEPTS") or
                        self._is_body_label(text) or prediction == "HEADING" or style_name.startswith("Heading")):
                        
                        if self._is_keywords_label(text) or prediction == "KEYWORDS" or style_name in ("KeyWords", "Keywords", "CCSCONCEPTS"):
                            state = "keywords"
                        else:
                            state = "body"

                elif state == "keywords":
                    if (self._is_body_label(text) or prediction == "HEADING" or style_name.startswith("Heading")):
                        state = "body"

                # From body (or any state): detect references section
                if state == "body":
                    if (self._is_references_label(text) or
                        style_name.lower() in ("referenceitem", "references", "bibliography")):
                        state = "references"

                # Action: Add to buffer or ir
                if state == "title":
                    title_buf.append(loc_ky_tu(text))
                elif state == "authors":
                    # Strip boilerplate
                    if not any(x in text for x in ("Submission Template", "Reference Format", "Short Title")):
                        if "\n" in text:
                            for line in text.splitlines():
                                line_clean = line.strip()
                                if not line_clean:
                                    continue
                                # IEEE Word template often stores author blocks as:
                                # "line 1: ...", "line 2: ..."; strip this wrapper.
                                line_clean = re.sub(r'^line\s*\d+\s*:\s*', '', line_clean, flags=re.IGNORECASE)
                                if line_clean:
                                    authors_buf.append(line_clean)
                        else:
                            cleaned = re.sub(r'^line\s*\d+\s*:\s*', '', text, flags=re.IGNORECASE).strip()
                            if cleaned:
                                authors_buf.append(cleaned)
                elif state == "abstract":
                    # FIX 3: Smart split — paragraph may contain BOTH "Abstract." and "Keywords:"
                    combined_match = re.search(
                        r'(?:abstract\.?\s*)(.+?)\s*(?:keywords?|index\s+terms?)[^\w]*(.+)',
                        text, re.IGNORECASE | re.DOTALL
                    )
                    if combined_match:
                        abs_text = combined_match.group(1).strip()
                        kw_text  = combined_match.group(2).strip()
                        if abs_text:
                            abstract_buf.append(loc_ky_tu(abs_text))
                        if kw_text:
                            keywords_buf.append(loc_ky_tu(kw_text))
                        # Jump state forward so subsequent parsing picks up body correctly
                        state = "keywords"
                    else:
                        clean_text = re.sub(r"^(abstract\.?)[:\s]*", "", text, flags=re.IGNORECASE).strip()
                        if clean_text:
                            abstract_buf.append(loc_ky_tu(clean_text))
                elif state == "keywords":
                    # Remove label
                    clean_text = re.sub(r"^(Additional Keywords and Phrases:|Keywords?\s*[:\-–]|Index Terms:|Từ khóa:)\s*", "", text, flags=re.IGNORECASE).strip()
                    if clean_text:
                        keywords_buf.append(loc_ky_tu(clean_text))
                elif state == "body" or (has_img_para and state != "references"):
                    node = self._parse_paragraph(element)
                    node_text = node.get('text', '')
                    # Post-process: nếu paragraph chứa standalone figure, tìm caption phía dưới
                    if '\\includegraphics' in node_text and '\\begin{figure' in node_text:
                        img_match = re.search(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}', node_text)
                        img_path = img_match.group(1).strip() if img_match else ""
                        if img_path and img_path in seen_figure_paths:
                            continue
                        caption = self._bat_caption_hinh(elements, idx, used_nodes)
                        if not caption:
                            caption = self._bat_caption_hinh_theo_style(elements, idx, used_nodes)
                        if caption:
                            node['text'] = node_text.replace('\\caption{}', f'\\caption{{{caption}}}')
                        if img_path:
                            seen_figure_paths.add(img_path)
                    self.ir["body"].append(node)
                elif state == "references":
                    # Skip the header label itself (e.g., "Tài Liệu Tham Khảo", "References")
                    if (not self._is_references_label(text)) and self._looks_like_reference_entry(text):
                        node = self._parse_paragraph(element)
                        node_text = node.get("text", "")
                        if node_text.startswith("\\url{") and len(self.ir["references"]) > 0:
                            self.ir["references"][-1]["text"] += " " + node_text
                        else:
                            self.ir["references"].append(node)
                
            elif etype == "table":
                # Bypass: Nếu bảng đứng trước abstract, có thể đây là Author Table đặc thù của IEEE
                if state in ("pre_title", "title", "authors") and not abstract_buf:
                    try:
                        table_lines = []
                        table_lines = []
                        seen_cells = set()
                        for row in element.rows:
                            for cell in row.cells:
                                cell_id = id(cell._tc)
                                if cell_id in seen_cells:
                                    continue
                                seen_cells.add(cell_id)
                                cell_text = "\n".join([p.text.strip() for p in cell.paragraphs if p.text.strip()]).strip()
                                if cell_text:
                                    table_lines.extend([line.strip() for line in cell_text.split('\n') if line.strip()])
                                        
                        table_text = "\n".join(table_lines)
                        if len(table_text) < 1500 and not self._la_bang_chua_anh(element):
                            state = "authors"
                            authors_buf.extend(table_lines)
                            # Đánh dấu bảng này đã được dùng cho authors để tránh tự xuất hiện lại trong body (nếu được xử lý tiếp)
                            used_nodes.add(idx)
                            continue
                    except Exception as e:
                        print(f"[WARN] Error parsing potential IEEE author table: {e}")
                        
                # Tables always force body
                state = "body"
                eq_node = self._detect_equation_table(element)
                if eq_node:
                    self.ir["body"].append(eq_node)
                else:
                    danh_sach_anh = self._trich_xuat_anh_tu_bang(element)
                    if danh_sach_anh:
                        # Simple and robust mode: emit every extracted image as a figure.
                        caption_chinh = self._bat_caption_hinh(elements, idx, used_nodes)
                        ten_thu_muc = os.path.basename(self.thu_muc_anh)
                        for i, ten_anh in enumerate(danh_sach_anh):
                            self.dem_anh += 1
                            img_path = f"{ten_thu_muc}/{ten_anh}"
                            if img_path in seen_figure_paths:
                                continue
                            cap = caption_chinh if i == 0 else ""
                            fig_tex = "\\begin{figure}[htbp]\n\\centering\n"
                            fig_tex += f"  \\includegraphics[width=0.9\\columnwidth]{{{img_path}}}\n"
                            fig_tex += f"  \\caption{{{cap}}}\n"
                            fig_tex += f"  \\label{{fig:img_{self.dem_anh}}}\n"
                            fig_tex += "\\end{figure}\n\n"
                            seen_figure_paths.add(img_path)
                            self.ir["body"].append({"type": "paragraph", "text": fig_tex})
                    else:
                        # Regular data table — with caption from look-behind
                        caption = self._bat_caption_bang(elements, idx, used_nodes)
                        table_node = self._parse_table(element)
                        if caption:
                            table_node["caption"] = caption
                        self.ir["body"].append(table_node)

        extracted_title = " ".join(title_buf).strip()
        
        # Fallback: Nếu Parser heuristic không tìm thấy Title, bốc ngay Paragraph đầu tiên trong body làm Title
        if not extracted_title and len(self.ir["body"]) > 0:
            for i, p_node in enumerate(self.ir["body"]):
                p_text = p_node.get("text", "")
                is_figure_para = "\\begin{figure" in p_text or "\\includegraphics" in p_text
                if p_node.get("type") == "paragraph" and p_text.strip() and (not is_figure_para):
                    extracted_title = p_node.get("text").strip()
                    self.ir["body"].pop(i)
                    break
        
        if not authors_buf and len(self.ir["body"]) > 0:
            author_candidates = []
            while len(self.ir["body"]) > 0:
                nxt = self.ir["body"][0]
                nxt_text = nxt.get("text", "")
                is_figure_para = "\\begin{figure" in nxt_text or "\\includegraphics" in nxt_text
                if nxt.get("type") == "paragraph" and (not is_figure_para) and len(nxt_text.split()) < 15:
                    author_candidates.append(nxt.get("text"))
                    self.ir["body"].pop(0)
                else:
                    break
            authors_buf.extend(author_candidates)
                     
        # Final metadata assignment
        self.ir["metadata"]["title"] = extracted_title
        parsed_authors = self._parse_authors(authors_raw=authors_buf)
        self.ir["metadata"]["authors"] = parsed_authors
        self.ir["metadata"]["author_block"] = ""  # Will be generated by renderer based on template class
        self.ir["metadata"]["abstract"] = "\n\n".join(abstract_buf).strip()
        kw_list = [k.strip() for k in " ".join(keywords_buf).replace(";", ",").split(",") if k.strip()]
        self.ir["metadata"]["keywords"] = kw_list
        self.ir["metadata"]["keywords_str"] = ", ".join(kw_list)
        self.ir["metadata"]["total_formulas"] = self.total_formulas

    def _extract_author_with_superscripts(self, p) -> str:
        """Extract author text preserving superscript markers as \\textsuperscript{}."""
        result = ""
        for run in p.runs:
            txt = run.text
            if not txt:
                continue
            if run.font.superscript:
                result += f"\\textsuperscript{{{loc_ky_tu(txt)}}}"
            else:
                result += loc_ky_tu(txt)
        return result.strip() if result.strip() else loc_ky_tu(p.text).strip()

    def _detect_equation_table(self, t) -> dict:
        """Detect if a Word table is actually a layout table for an equation.
        Pattern: 1 row, 2-3 columns, last column contains equation number like (1).
        """
        try:
            rows = t.rows
            if len(rows) != 1:
                return None
            cells = rows[0].cells
            if len(cells) < 2 or len(cells) > 3:
                return None
            
            # Check if last cell is equation number like (1), (2), (1a), (A1), etc.
            last_text = cells[-1].text.strip()
            if not re.match(r'^\(([A-Za-z0-9\.\-\*]+)\)$', last_text):
                return None
            
            # The formula usually occupies all cells except the rightmost equation number.
            formula_parts = [c.text.strip() for c in cells[:-1] if c.text.strip()]
            formula_text = " ".join(formula_parts)
            
            # Check if first cell(s) contain math-like content (=, ½, fractions, symbols)
            math_indicators = ['=', '½', '∑', '∏', '∫', '+', '−', '×', '÷', 'frac', '\\', 
                             'Accuracy', 'Precision', 'Recall', 'Sensitivity', 'Specificity']
            has_math = any(ind in formula_text for ind in math_indicators)
            if not has_math:
                return None
            
            # It's an equation table! Convert to equation node
            # Try to extract OMML math if present
            ns_m = "http://schemas.openxmlformats.org/officeDocument/2006/math"
            tbl_xml = t._tbl
            omml_math = tbl_xml.find(f".//{{{ns_m}}}oMathPara")
            if omml_math is None:
                omml_math = tbl_xml.find(f".//{{{ns_m}}}oMath")
            
            if omml_math is not None:
                latex_math = self.bo_toan.omml_element_to_latex(omml_math)
                # Capture raw OMML XML
                try:
                    omml_str = etree.tostring(omml_math, encoding='unicode')
                    omml_b64 = base64.b64encode(omml_str.encode('utf-8')).decode('utf-8')
                    eq_text = f"\\begin{{equation}}\n«OMML:{omml_b64}»\n\\tag{{{last_text.strip('()')}}}\n\\end{{equation}}"
                except Exception:
                    eq_text = f"\\begin{{equation}}\n{latex_math}\n\\tag{{{last_text.strip('()')}}}\n\\end{{equation}}"
            else:
                # No OMML, use the plain text and try to make it look like an equation
                # Replace ½ with \\frac{1}{2}, etc.
                formula_text = formula_text.replace('½', '\\frac{1}{2}')
                formula_text = formula_text.replace('×', '\\times')
                formula_text = formula_text.replace('−', '-')
                eq_text = f"\\begin{{equation}}\n{formula_text}\n\\tag{{{last_text.strip('()')}}}\n\\end{{equation}}"
            
            self.total_formulas += 1
            return {"type": "paragraph", "text": eq_text, "has_math": True}
        except Exception:
            return None

    def _post_process_citations(self):
        """Scans all body paragraphs and replaces bracket citations like [1] or [1, 2] with \\cite{ref1}."""
        citation_pattern = re.compile(r'\[([0-9\s,\-]+)\]')
        
        def replace_cite(match):
            inner = match.group(1).replace(" ", "")
            parts = inner.split(",")
            ref_keys = []
            for part in parts:
                if "-" in part:
                    bounds = part.split("-")
                    if len(bounds) == 2 and bounds[0].isdigit() and bounds[1].isdigit():
                        start, end = int(bounds[0]), int(bounds[1])
                        for i in range(start, end + 1):
                            ref_keys.append(f"ref{i}")
                    else:
                        ref_keys.append(f"ref{part}")
                elif part.isdigit():
                    ref_keys.append(f"ref{part}")
                else:
                    return match.group(0) # Not a valid citation format
            
            if ref_keys:
                return f"\\cite{{{','.join(ref_keys)}}}"
            return match.group(0)

        for node in self.ir["body"]:
            if node["type"] in ("paragraph", "section"):
                node["text"] = citation_pattern.sub(replace_cite, node["text"])
            elif node["type"] == "table":
                if "data" in node:
                    for row in node["data"]:
                        for cell in row:
                            if "text" in cell:
                                cell["text"] = citation_pattern.sub(replace_cite, cell["text"])

    def _parse_authors(self, authors_raw: List[str]) -> List[Dict]:
        """Convert a flat list of author strings into structured dicts.
        Hỗ trợ: tác giả trên nhiều dòng, hoặc nhiều tác giả trên 1 dòng (phân tách bằng dấu phẩy / and).
        Handles superscript number mapping between author names and affiliations.
        """
        def _looks_like_affiliation(text: str) -> bool:
            t = (text or '').lower()
            affil_keywords = [
                '@', 'university', 'institute', 'dept', 'faculty', 'ltd',
                'department', 'school', 'lab', 'center', 'organization',
                'city', 'country', 'affiliation', 'vietnam', 'viet nam', 'việt nam'
            ]
            return any(kw in t for kw in affil_keywords)

        def _looks_like_ieee_membership_suffix(text: str) -> bool:
            t = (text or '').lower()
            membership_keywords = [
                'member',
                'senior member',
                'fellow',
                'life fellow',
                'student member',
                'ieee',
            ]
            return any(kw in t for kw in membership_keywords)

        authors = []
        current = None

        # Tiền xử lý: tách các dòng chứa nhiều tên tác giả (phân tách bằng ',' hoặc ' and ')
        expanded = []
        for info in authors_raw:
            clean = info.strip()
            if not clean:
                continue
            # Kiểm tra: dòng này có chứa nhiều tác giả không?
            # Điều kiện: có dấu phẩy hoặc ' and ' NHƯNG không phải affiliation
            is_affil = _looks_like_affiliation(clean)
            if (',' in clean or ' and ' in clean) and not is_affil:
                # Tách bằng ' and ' trước, rồi ','
                parts = re.split(r'\s+and\s+', clean)
                all_parts = []
                for p in parts:
                    if ',' in p and _looks_like_ieee_membership_suffix(p):
                        all_parts.append(p.strip())
                    else:
                        all_parts.extend([x.strip() for x in p.split(',') if x.strip()])
                # Nếu tất cả các phần đều ngắn (tên người), tách thành nhiều tác giả
                if len(all_parts) > 1 and all(len(p) < 60 for p in all_parts):
                    expanded.extend(all_parts)
                    continue
            expanded.append(clean)

        # Fast-path for common publisher layout: all author names first, then affiliations.
        # Without this branch, sequential parsing can incorrectly attach all affiliations to
        # the last author only.
        if expanded:
            first_affil_idx = None
            has_name_after_affil = False
            for idx, item in enumerate(expanded):
                is_affil = _looks_like_affiliation(item)
                if is_affil and first_affil_idx is None:
                    first_affil_idx = idx
                elif first_affil_idx is not None and (not is_affil) and len(item) < 60:
                    has_name_after_affil = True
                    break

            if first_affil_idx is not None and first_affil_idx >= 2 and not has_name_after_affil:
                names = expanded[:first_affil_idx]
                affils = expanded[first_affil_idx:]
                authors = [{"name": n, "affiliations": []} for n in names]

                if len(affils) >= len(authors):
                    # 1-1 by index; any extra lines (often email/address continuation)
                    # are appended to the last author.
                    for i, af in enumerate(affils):
                        target_idx = i if i < len(authors) else len(authors) - 1
                        authors[target_idx]["affiliations"].append(af)
                elif affils:
                    # Fewer affiliations than names: map by index then reuse the last one.
                    for i, a in enumerate(authors):
                        mapped = affils[i] if i < len(affils) else affils[-1]
                        a["affiliations"].append(mapped)

                current = None

        if not authors:
            for info in expanded:
                clean = info.strip()
                if not clean:
                    continue
                is_affil = _looks_like_affiliation(clean)
                if not current:
                    current = {"name": clean, "affiliations": []}
                elif is_affil or (len(clean) >= 40 and '@' in clean):
                    current["affiliations"].append(clean)
                elif len(clean) < 50 and not is_affil:
                    authors.append(current)
                    current = {"name": clean, "affiliations": []}
                else:
                    current["affiliations"].append(clean)
            if current:
                authors.append(current)

        # Post-process: map superscript numbers/symbols in names to numbered affiliations
        affil_map = {}  # marker -> affiliation text
        unmapped_affils = []
        all_affils = []
        for a in authors:
            for af in a.get("affiliations", []):
                all_affils.append(af)
                m_num = re.match(r'^(\d+)\s+(.*)', af)
                if m_num:
                    affil_map[m_num.group(1)] = m_num.group(2).strip()
                else:
                    m_sym = re.search(r'([*†‡]+)', af)
                    if m_sym:
                        affil_map[m_sym.group(1)] = af.strip()
                    else:
                        unmapped_affils.append(af.strip())

        # FIX 2: Collect unmapped standalone emails
        email_pattern = re.compile(r'[\w\.\-\+]+@[\w\.\-]+')
        extracted_emails = []
        for af in unmapped_affils:
            extracted_emails.extend(email_pattern.findall(af))

        if affil_map:
            # FIX 2: Map by superscript numbers/symbols (*, †, ‡ included)
            for a in authors:
                name = a["name"]
                # Match trailing superscript markers: digits, *, †, ‡, commas
                num_match = re.search(r'([\d\*†‡,\s]+)$', name)
                if num_match:
                    raw_markers = num_match.group(1)
                    markers = re.findall(r'\d+|[*†‡]', raw_markers)
                    a["name"] = name[:num_match.start()].strip()
                    a["affiliations"] = []
                    for mk in markers:
                        if mk in affil_map:
                            a["affiliations"].append(affil_map[mk])
                    # If * present and no mapped affil found, fall back to all
                    if not a["affiliations"] and '*' in raw_markers and '*' not in affil_map:
                        a["affiliations"] = list(affil_map.values())
                else:
                    # No markers => give all numbered affiliations as fallback
                    a["affiliations"] = [v for k, v in affil_map.items() if str(k).isdigit()]
        elif len(authors) > 1:
            # Fallback: if some have no affil, share all
            any_empty = any(not a.get("affiliations") for a in authors)
            any_multi = any(len(a.get("affiliations", [])) > 1 for a in authors)
            if any_empty and any_multi:
                for a in authors:
                    a["affiliations"] = all_affils[:]

        # FIX 2: Attach remaining extracted emails to authors who have no email yet
        if extracted_emails:
            email_idx = 0
            for a in authors:
                has_email = any('@' in aff for aff in a.get('affiliations', []))
                if not has_email and email_idx < len(extracted_emails):
                    a.setdefault('affiliations', []).append(extracted_emails[email_idx])
                    email_idx += 1

        # Normalize affiliations: split fused email text and remove placeholder metadata
        email_pattern = re.compile(r'[\w\.\-\+]+@[\w\.\-]+')
        for a in authors:
            normalized_affils = []
            for aff in a.get('affiliations', []):
                raw = (aff or '').strip()
                if not raw:
                    continue
                emails = email_pattern.findall(raw)
                non_email = email_pattern.sub('', raw)
                non_email = re.sub(r'\s{2,}', ' ', non_email).strip(' ,;')
                if non_email:
                    normalized_affils.append(non_email)
                for em in emails:
                    normalized_affils.append(em)

            # Deduplicate while preserving order
            seen = set()
            deduped = []
            for item in normalized_affils:
                key = item.lower()
                if key in seen:
                    continue
                seen.add(key)
                deduped.append(item)
            a['affiliations'] = deduped

        # Remove common template placeholders accidentally captured from sample templates
        placeholder_name = re.compile(
            r'^(first|second|third|fourth|fifth|sixth)\s+(?:[a-z]\.?\s+)?author(?:,\s*(?:jr\.?|sr\.?))?$',
            re.IGNORECASE,
        )
        membership_only = re.compile(r'^(fellow|member|senior\s+member|student\s+member|life\s+fellow|ieee)$', re.IGNORECASE)
        placeholder_affil = re.compile(r'(springer\s+heidelberg|tiergartenstr|69121\s+heidelberg)', re.IGNORECASE)
        ieee_template_affil = re.compile(
            r'(dept\.?\s*name\s*of\s*organization|\(of\s*affiliation\)|city,\s*country|email\s*address\s*or\s*orcid)',
            re.IGNORECASE,
        )
        cleaned_authors = []
        for a in authors:
            name = (a.get('name') or '').strip()
            affs = a.get('affiliations', [])
            if not name:
                continue
            if placeholder_name.match(name):
                # Skip placeholder rows from default publisher templates.
                continue
            if membership_only.match(name):
                continue

            # Remove placeholder affiliation lines but keep valid emails/other lines.
            filtered_affs = [x for x in affs if (not placeholder_affil.search(x)) and (not ieee_template_affil.search(x))]
            a['affiliations'] = filtered_affs
            cleaned_authors.append(a)

        authors = cleaned_authors

        return authors

    def _parse_paragraph(self, p: Paragraph, in_table: bool = False) -> Dict:
        """Parse paragraph into an IR node. Basic implementation, focuses on text."""
        text = ""
        has_math = False
        

        
        style_name = p.style.name if p.style else ""
        from .config import MAP_STYLE
        style_cmd = MAP_STYLE.get(style_name, "")
        
        # Level detection for sections
        level = None
        if style_cmd == r"\section": level = 1
        elif style_cmd == r"\subsection": level = 2
        elif style_cmd == r"\subsubsection": level = 3
        elif style_name.lower().startswith("heading"):
            try:
                level = int(re.sub(r'[^\d]', '', style_name))
            except:
                level = 1
        
        # We must process the text at the Run-level, to insert math between text nodes
        if p.runs:
            for run in p.runs:
                # Check for math inside this run's vicinity (actually math is sibling to run usually)
                pass
                
        # Better approach: Iterate the XML elements of the paragraph in exact order via recursive descent
        ns_w = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
        ns_m = "http://schemas.openxmlformats.org/officeDocument/2006/math"
        ns_o = "urn:schemas-microsoft-com:office:office"
        ns_r = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
        ns_v = "urn:schemas-microsoft-com:vml"
        ns_a = "http://schemas.openxmlformats.org/drawingml/2006/main"

        def _ty_le_rong_hinh_tu_drawing(drawing_node):
            """Estimate image width ratio from Word drawing extent (EMU)."""
            try:
                ns_wp = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
                extent = drawing_node.find(f".//{{{ns_wp}}}extent")
                if extent is None:
                    return None
                cx = extent.get("cx")
                if not cx:
                    return None
                cx_emu = float(cx)
                if not self.doc.sections:
                    return None
                sec = self.doc.sections[0]
                usable_emu = float(sec.page_width - sec.left_margin - sec.right_margin)
                if usable_emu <= 0:
                    return None
                ratio = cx_emu / usable_emu
                return max(0.2, min(0.95, ratio))
            except Exception:
                return None
        
        def traverse_node(node):
            nonlocal text, has_math
            if not hasattr(node, "tag") or not isinstance(node.tag, str):
                return

            if node.tag == f"{{{ns_m}}}oMathPara":
                has_math = True
                self.total_formulas += 1
                latex_math = self.bo_toan.omml_element_to_latex(node)
                try:
                    omml_str = etree.tostring(node, encoding='unicode')
                    omml_b64 = base64.b64encode(omml_str.encode('utf-8')).decode('utf-8')
                    text += f" «OMML:{omml_b64}» "
                except Exception:
                    text += f" ${latex_math}$ "
                return
            
            if node.tag == f"{{{ns_m}}}oMath":
                has_math = True
                self.total_formulas += 1
                latex_math = self.bo_toan.omml_element_to_latex(node)
                # Capture raw OMML XML for high-fidelity rendering
                try:
                    omml_str = etree.tostring(node, encoding='unicode')
                    omml_b64 = base64.b64encode(omml_str.encode('utf-8')).decode('utf-8')
                    text += f" «OMML:{omml_b64}» "
                except Exception:
                    text += f" ${latex_math}$ "
                return
            elif node.tag == f"{{{ns_w}}}r":
                # Convert run to text
                run_obj = Run(node, p)
                run_text = loc_ky_tu(run_obj.text)
                if run_text.strip() and level is None:
                    is_bold = bool(run_obj.bold)
                    is_italic = bool(run_obj.italic)
                    if is_bold and is_italic:
                        run_text = f"\\textbf{{\\textit{{{run_text}}}}}"
                    elif is_bold:
                        run_text = f"\\textbf{{{run_text}}}"
                    elif is_italic:
                        run_text = f"\\textit{{{run_text}}}"
                text += run_text
                # Keep traversing to find inline w:drawing or w:object inside the run
            elif node.tag == f"{{{ns_w}}}object":
                ole_obj = node.find(f".//{{{ns_o}}}OLEObject")
                if ole_obj is not None:
                    prog_id = ole_obj.get("ProgID", "")
                    if "Equation" in prog_id:
                        r_id = ole_obj.get(f"{{{ns_r}}}id")
                        if r_id:
                            try:
                                rel = p.part.rels[r_id]
                                ole_bin = rel.target_part.blob
                                latex = ole_equation_to_latex(ole_bin)
                                if latex:
                                    has_math = True
                                    self.total_formulas += 1
                                    text += f" ${latex}$ "
                            except Exception:
                                pass
                return
            elif node.tag == f"{{{ns_w}}}pict":
                imagedata = node.find(f".//{{{ns_v}}}imagedata")
                if imagedata is not None:
                    r_id = imagedata.get(f"{{{ns_r}}}id")
                    if r_id:
                        try:
                            rel = p.part.rels[r_id]
                            latex_path = self._save_image_from_relationship(rel)
                            if not latex_path:
                                return
                            
                            if in_table:
                                img_opts = self._includegraphics_options("\\linewidth")
                                latex_img = f"\n\\begin{{center}}\n\\includegraphics[{img_opts}]{{{latex_path}}}\n\\end{{center}}\n"
                            else:
                                self.dem_anh += 1
                                img_opts = self._includegraphics_options("0.9\\columnwidth")
                                latex_img = f"\n\\begin{{figure}}[htbp]\n\\centering\n\\includegraphics[{img_opts}]{{{latex_path}}}\n\\caption{{}}\n\\label{{fig:img_{self.dem_anh}}}\n\\end{{figure}}\n"
                            text += latex_img
                        except Exception:
                            pass
                return
            elif node.tag == f"{{{ns_w}}}drawing":
                blip = node.find(f".//{{{ns_a}}}blip")
                if blip is not None:
                    r_id = blip.get(f"{{{ns_r}}}embed")
                    if r_id:
                        try:
                            rel = p.part.rels[r_id]
                            latex_path = self._save_image_from_relationship(rel)
                            if not latex_path:
                                return
                            if in_table:
                                img_opts = self._includegraphics_options("\\linewidth")
                                latex_img = f"\n\\begin{{center}}\n\\includegraphics[{img_opts}]{{{latex_path}}}\n\\end{{center}}\n"
                            else:
                                self.dem_anh += 1
                                width_ratio = _ty_le_rong_hinh_tu_drawing(node)
                                if width_ratio:
                                    width_expr = f"{width_ratio:.3f}\\columnwidth"
                                else:
                                    width_expr = "0.9\\columnwidth"
                                img_opts = self._includegraphics_options(width_expr)
                                latex_img = f"\n\\begin{{figure}}[htbp]\n\\centering\n\\includegraphics[{img_opts}]{{{latex_path}}}\n\\caption{{}}\n\\label{{fig:img_{self.dem_anh}}}\n\\end{{figure}}\n"
                            text += latex_img
                        except Exception:
                            pass
                return
            elif node.tag == f"{{{ns_a}}}blip":
                r_id = node.get(f"{{{ns_r}}}embed")
                if r_id:
                    try:
                        rel = p.part.rels[r_id]
                        latex_path = self._save_image_from_relationship(rel)
                        if not latex_path:
                            return
                        if in_table:
                            img_opts = self._includegraphics_options("\\linewidth")
                            latex_img = f"\n\\begin{{center}}\n\\includegraphics[{img_opts}]{{{latex_path}}}\n\\end{{center}}\n"
                        else:
                            self.dem_anh += 1
                            img_opts = self._includegraphics_options("0.9\\columnwidth")
                            latex_img = f"\n\\begin{{figure}}[htbp]\n\\centering\n\\includegraphics[{img_opts}]{{{latex_path}}}\n\\caption{{}}\n\\label{{fig:img_{self.dem_anh}}}\n\\end{{figure}}\n"
                        text += latex_img
                    except Exception:
                        pass
                return
                
            for child in node:
                traverse_node(child)
                
        traverse_node(p._p)
        text = text.strip()

        # Heuristics for headings
        if not level:
            for pattern, latex_cmd in HEADING_PATTERNS:
                if re.match(pattern, text, re.IGNORECASE):
                    if latex_cmd == r"\section": level = 1
                    elif latex_cmd == r"\subsection": level = 2
                    elif latex_cmd == r"\subsubsection": level = 3
                    break
                    
        if level:
            # We strip numbering (e.g., "1. Introduction" -> "Introduction")
            clean_text = re.sub(r'^[A-Z0-9IVX]+\.\s+', '', text)
            return {"type": "section", "level": level, "text": clean_text}
            
        # Standard paragraph
        # Ideally, we would preserve bold/italics here. For now, just raw text.
        return {"type": "paragraph", "text": text, "has_math": has_math}

    def _lay_gridspan(self, tc) -> int:
        try:
            tcPr = tc.tcPr
            if tcPr is None: return 1
            gridSpan = tcPr.gridSpan
            if gridSpan is None: return 1
            val = gridSpan.get(qn('w:val'))
            return max(1, int(val)) if val else 1
        except:
            return 1

    def _lay_vmerge(self, tc):
        try:
            tcPr = tc.tcPr
            if tcPr is None: return None
            vMerge = tcPr.vMerge
            if vMerge is None: return None
            val = vMerge.get(qn('w:val'))
            return str(val) if val else 'continue'
        except:
            return None

    def _lay_ty_le_rong_bang(self, t: Table):
        """Read table preferred width from Word XML and map to page ratio (0..1]."""
        try:
            tbl_pr = getattr(t._tbl, "tblPr", None)
            if tbl_pr is None:
                return None

            tblw = tbl_pr.find(qn('w:tblW'))
            if tblw is None:
                return None

            w_type = (tblw.get(qn('w:type')) or "").lower()
            w_val = tblw.get(qn('w:w'))
            if not w_val:
                return None

            if w_type == 'pct':
                # In WordprocessingML, pct is stored in fiftieths of a percent.
                ratio = float(w_val) / 5000.0
                return max(0.2, min(0.95, ratio))

            if w_type == 'dxa':
                twips = float(w_val)
                if not self.doc.sections:
                    return None
                sec = self.doc.sections[0]
                usable_twips = (
                    sec.page_width.twips
                    - sec.left_margin.twips
                    - sec.right_margin.twips
                )
                if usable_twips <= 0:
                    return None
                ratio = twips / float(usable_twips)
                return max(0.2, min(0.95, ratio))
        except Exception:
            return None

        return None

    def _parse_table(self, t: Table) -> Dict:
        """Parse table including rowspan (vMerge) and colspan (gridSpan)."""
        tbl = t._tbl
        tr_list = list(tbl.tr_lst)
        width_ratio = self._lay_ty_le_rong_bang(t)

        so_cot = 0
        try:
            grid_cols = tbl.tblGrid.gridCol_lst
            so_cot = len(grid_cols)
        except: pass

        if so_cot <= 0:
            for tr in tr_list:
                so_cot = max(so_cot, len(list(tr.tc_lst)))

        luoi = [[None for _ in range(so_cot)] for _ in range(len(tr_list))]
        meta = {}

        for r, tr in enumerate(tr_list):
            c = 0
            for tc in list(tr.tc_lst):
                while c < so_cot and luoi[r][c] is not None:
                    c += 1
                if c >= so_cot:
                    break

                colspan = self._lay_gridspan(tc)
                vmerge = self._lay_vmerge(tc)

                cell_id = id(tc)
                if vmerge in ('continue', 'cont') and r > 0 and luoi[r - 1][c] is not None:
                    cell_id = meta.get((r - 1, c), {}).get('id', cell_id)

                meta[(r, c)] = {
                    'id': cell_id,
                    'tc': tc,
                    'colspan': colspan,
                    'vmerge': vmerge,
                    'start': not (vmerge in ('continue', 'cont')),
                    'col_start': c,
                }

                for k in range(colspan):
                    if c + k < so_cot:
                        luoi[r][c + k] = cell_id
                        if k > 0:
                            # Horizontal merge continuation cells must not be treated
                            # as independent starts, otherwise content is duplicated.
                            meta[(r, c + k)] = {
                                'id': cell_id,
                                'tc': tc,
                                'colspan': 1,
                                'vmerge': vmerge,
                                'start': False,
                                'col_start': c,
                            }

                c += colspan

        # Compute rowspan
        rowspan_map = {}
        for (r, c), info in list(meta.items()):
            if not info.get('start'):
                continue
            if info.get('col_start', c) != c:
                continue

            cell_id = info['id']
            rowspan = 1
            rr = r + 1
            while rr < len(tr_list):
                info_down = meta.get((rr, c))
                if not info_down or info_down.get('id') != cell_id or info_down.get('start'):
                    break
                rowspan += 1
                rr += 1
            rowspan_map[cell_id] = max(rowspan_map.get(cell_id, 1), rowspan)
            
        # Build logical grid data for IR
        parsed_rows = []
        for r in range(len(tr_list)):
            row_data = []
            c = 0
            while c < so_cot:
                info = meta.get((r, c))
                if not info or not info.get('start') or meta.get((r, c)) != info:
                    # It's a merged cell or empty
                    row_data.append({"type": "empty", "colspan": 1, "rowspan": 1, "text": ""})
                    c += 1
                    continue
                    
                colspan = int(info.get('colspan') or 1)
                cell_id = info['id']
                rowspan = int(rowspan_map.get(cell_id, 1))
                
                # Retrieve pure text for now
                cell_obj = None
                try:
                    cell_obj = t.rows[r].cells[0]
                    for candidate in t.rows[r].cells:
                        if id(candidate._tc) == id(info['tc']):
                            cell_obj = candidate
                            break
                except: pass
                
                text_content = ""
                if cell_obj:
                    cell_texts = []
                    for p in cell_obj.paragraphs:
                        p_data = self._parse_paragraph(p, in_table=True)
                        cell_texts.append(p_data.get("text", ""))
                    text_content = "\n".join(cell_texts).strip()
                    if not text_content:
                        text_content = loc_ky_tu(cell_obj.text.strip())
                    
                row_data.append({
                    "type": "cell",
                    "text": text_content,
                    "colspan": colspan,
                    "rowspan": rowspan,
                    "is_merged": colspan > 1 or rowspan > 1
                })
                
                c += colspan
                
            parsed_rows.append(row_data)

        # Trích xuất Header (Heuristic đơn giản: lấy row 0 làm header nếu có text)
        is_header = False
        if len(parsed_rows) > 0 and len(tr_list) > 1:
            is_header = any(cell["text"] != "" for cell in parsed_rows[0])
            
        is_floating_word_table = t._tbl.find(f".//{{{W_NAMESPACE}}}tblpPr") is not None

        return {
            "type": "table",
            "rows": len(tr_list), 
            "cols": so_cot,
            "has_header": is_header,
            "data": parsed_rows,
            "width_ratio": width_ratio,
            "is_floating_word_table": bool(is_floating_word_table),
        }
