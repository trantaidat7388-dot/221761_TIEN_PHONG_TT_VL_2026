import os
import re
import hashlib
from typing import Dict, Any, List

import docx
from docx.table import Table
from docx.text.paragraph import Paragraph
from docx.text.run import Run

from .config import MAP_STYLE, HEADING_PATTERNS, A_NAMESPACE, REL_NAMESPACE
from docx.oxml.ns import qn
from .utils import loc_ky_tu
from .xu_ly_toan import BoXuLyToan
from .xu_ly_ole_equation import ole_equation_to_latex
from .semantic_parser import du_doan_loai_node

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
        from .utils import sua_docx_co_macro
        
        try:
            sua_docx_co_macro(self.doc_path)
            # Reload to make sure docx is fresh
            import time
            time.sleep(0.1)
        except Exception as e:
            print(f"[WARN] Lỗi khi làm sạch file Word trước khi parse: {e}")
            
        self.doc = docx.Document(self.doc_path)
        
        elements = self._extract_elements_in_order()
        self._build_semantic_tree(elements)
        self._post_process_citations()
        
        return self.ir
        
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
        for kw in ["REFERENCES", "TÀI LIỆU THAM KHẢO", "TAI LIEU THAM KHAO", "BIBLIOGRAPHY"]:
            if norm.startswith(kw):
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
                                img_blob = rel.target_part.blob
                                img_ext = rel.target_part.content_type.split('/')[-1]
                                if img_ext == 'jpeg': img_ext = 'jpg'
                                elif img_ext == 'x-emf': img_ext = 'emf'

                                self.dem_anh += 1
                                img_hash = hashlib.md5(img_blob).hexdigest()[:8]
                                img_name = f"img_{img_hash}.{img_ext}"

                                if self.thu_muc_anh:
                                    os.makedirs(self.thu_muc_anh, exist_ok=True)
                                    img_path = os.path.join(self.thu_muc_anh, img_name)
                                else:
                                    img_path = img_name

                                if not os.path.exists(img_path):
                                    with open(img_path, "wb") as f:
                                        f.write(img_blob)
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
                caption_text = loc_ky_tu(text)
                # FIX 1: Support decimal chapter numbers like "Table 3.1"
                caption_text = re.sub(
                    r'^(Bảng|Table|TABLE|Bang|BANG)\.?\s*\d+(\.\d+)*\s*[:\.\-–—]?\s*',
                    '', caption_text, flags=re.IGNORECASE
                ).strip()
                return caption_text
        except Exception as e:
            print(f"[Cảnh báo] _bat_caption_bang: {e}")
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
                # FIX 1: Support decimal chapter numbers like "Figure 3.1"
                if re.match(r'^(HÌNH|HINH|ẢNH|ANH|FIGURE|FIG\.?)\b', text, re.IGNORECASE):
                    used_nodes.add(idx_sau)
                    caption_text = loc_ky_tu(text)
                    caption_text = re.sub(
                        r'^(Hình|Figure|Fig\.?)\s*\d+(\.\d+)*\s*[:\.\-–—]?\s*',
                        '', caption_text, flags=re.IGNORECASE
                    ).strip()
                    return caption_text
                # Dừng nếu gặp section heading mới
                if hasattr(phan_tu, 'style') and phan_tu.style and phan_tu.style.name and 'Heading' in phan_tu.style.name:
                    break
        except Exception as e:
            print(f"[Cảnh báo] _bat_caption_hinh: {e}")
        return None

    def _is_title_paragraph(self, p: Paragraph, idx: int) -> bool:
        """Heuristic for title: usually bold, large, or specific style 'Title'."""
        text = p.text.strip()
        if not text or len(text) < 3: return False
        if "Short Title" in text or "ACM Reference Format" in text: return False
        
        style_name = p.style.name if p.style else ""
        if "Title" in style_name or "Header" in style_name:
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
                # Check if this paragraph has images (look for drawings/blips)
                has_img = bool(element._p.findall(f'.//{{{A_NAMESPACE}}}blip'))
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
                        if re.match(r'^(HÌNH|HINH|ẢNH|ANH|FIGURE|FIG\.?)\b', a_text, re.IGNORECASE):
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
                if not text and state == "pre_title": continue # Skip empty leading lines
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
                    elif self._is_authors_label(text) or style_cmd == r"\author" or prediction == "AUTHOR" or style_name == "Authors":
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
                        authors_buf.append(text)
                elif state == "abstract":
                    # FIX 3: Smart split — paragraph may contain BOTH "Abstract." and "Keywords:"
                    combined_match = re.search(
                        r'(?:abstract\.?\s*)(.+?)\s*(?:keywords?\s*[:\-–]\s*)(.+)',
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
                elif state == "body":
                    node = self._parse_paragraph(element)
                    node_text = node.get('text', '')
                    # Post-process: nếu paragraph chứa standalone figure, tìm caption phía dưới
                    if '\\includegraphics' in node_text and '\\begin{figure' in node_text:
                        caption = self._bat_caption_hinh(elements, idx, used_nodes)
                        if caption:
                            node['text'] = node_text.replace('\\caption{}', f'\\caption{{{caption}}}')
                    self.ir["body"].append(node)
                elif state == "references":
                    # Skip the header label itself (e.g., "Tài Liệu Tham Khảo", "References")
                    if not self._is_references_label(text):
                        self.ir["references"].append(self._parse_paragraph(element))
                
            elif etype == "table":
                # Tables always force body
                state = "body"
                eq_node = self._detect_equation_table(element)
                if eq_node:
                    self.ir["body"].append(eq_node)
                elif self._la_bang_chua_anh(element):
                    # Table is actually a figure layout — extract images, not a table
                    danh_sach_anh = self._trich_xuat_anh_tu_bang(element)
                    if danh_sach_anh:
                        caption_con = self._tim_caption_con_trong_bang(element)
                        caption_chinh = self._bat_caption_hinh(elements, idx, used_nodes)
                        ten_thu_muc = os.path.basename(self.thu_muc_anh)
                        if len(danh_sach_anh) > 1 and caption_con:
                            # Subfigure layout
                            so_anh = len(danh_sach_anh)
                            do_rong = f"{0.9 / so_anh:.2f}" if so_anh > 1 else "0.48"
                            fig_tex = "\\begin{figure}[!ht]\n\\centering\n"
                            for i, ten_anh in enumerate(danh_sach_anh):
                                mo_ta = ""
                                if i < len(caption_con):
                                    mo_ta = re.sub(r'^\([a-z]\)\s*', '', caption_con[i]).strip()
                                nhan = chr(ord('a') + i)
                                fig_tex += f"  \\begin{{subfigure}}[b]{{{do_rong}\\linewidth}}\n"
                                fig_tex += "    \\centering\n"
                                fig_tex += f"    \\includegraphics[width=\\linewidth]{{{ten_thu_muc}/{ten_anh}}}\n"
                                fig_tex += f"    \\caption{{{mo_ta}}}\n"
                                fig_tex += f"    \\label{{fig:img_{i}_{nhan}}}\n"
                                fig_tex += "  \\end{subfigure}\n"
                                if i < so_anh - 1:
                                    fig_tex += "  \\hfill\n"
                            cap_final = caption_chinh or ""
                            fig_tex += f"  \\caption{{{cap_final}}}\n"
                            fig_tex += f"  \\label{{fig:group_{idx}}}\n"
                            fig_tex += "\\end{figure}\n\n"
                            self.ir["body"].append({"type": "paragraph", "text": fig_tex})
                        else:
                            for ten_anh in danh_sach_anh:
                                cap = caption_chinh or ""
                                fig_tex = "\\begin{figure}[!ht]\n\\centering\n"
                                fig_tex += f"  \\includegraphics[width=0.8\\linewidth]{{{ten_thu_muc}/{ten_anh}}}\n"
                                fig_tex += f"  \\caption{{{cap}}}\n"
                                fig_tex += f"  \\label{{fig:img_{self.dem_anh}}}\n"
                                fig_tex += "\\end{figure}\n\n"
                                self.ir["body"].append({"type": "paragraph", "text": fig_tex})
                else:
                    # Regular data table — with caption from look-behind
                    caption = self._bat_caption_bang(elements, idx, used_nodes)
                    table_node = self._parse_table(element)
                    if caption:
                        table_node["caption"] = caption
                    self.ir["body"].append(table_node)

        # Final metadata assignment
        self.ir["metadata"]["title"] = " ".join(title_buf).strip()
        self.ir["metadata"]["authors"] = self._parse_authors(authors_buf)
        self.ir["metadata"]["abstract"] = "\n\n".join(abstract_buf).strip()
        self.ir["metadata"]["keywords"] = keywords_buf
        self.ir["metadata"]["keywords_str"] = ", ".join(keywords_buf)
                
        # Finalize Metadata
        self.ir["metadata"]["title"] = " ".join(title_buf).strip()
        
        # Fallback: Nếu Parser heuristic không tìm thấy Title, bốc ngay Paragraph đầu tiên trong body làm Title
        if not self.ir["metadata"]["title"] and len(self.ir["body"]) > 0:
            for i, p_node in enumerate(self.ir["body"]):
                if p_node.get("type") == "paragraph" and p_node.get("text").strip():
                    self.ir["metadata"]["title"] = p_node.get("text").strip()
                    self.ir["body"].pop(i)
                    break
        
        if not authors_buf and len(self.ir["body"]) > 0:
            author_candidates = []
            while len(self.ir["body"]) > 0:
                nxt = self.ir["body"][0]
                if nxt.get("type") == "paragraph" and len(nxt.get("text", "").split()) < 15:
                     author_candidates.append(nxt.get("text"))
                     self.ir["body"].pop(0)
                else:
                     break
            authors_buf.extend(author_candidates)
                     
        # Final metadata assignment
        self.ir["metadata"]["title"] = " ".join(title_buf).strip()
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
            
            # Check if last cell is equation number like (1), (2), etc.
            last_text = cells[-1].text.strip()
            if not re.match(r'^\(\d+\)$', last_text):
                return None
            
            # The formula is in the first cell(s)
            formula_text = cells[0].text.strip()
            
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
            omath = tbl_xml.find(f".//{{{ns_m}}}oMath")
            
            if omath is not None:
                latex_math = self.bo_toan.omml_element_to_latex(omath)
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
            is_affil = any(kw in clean for kw in ['@', 'University', 'Institute', 'Dept', 'Faculty', 'Ltd',
                                                    'Department', 'School', 'Lab', 'Center', 'Vietnam',
                                                    'Viet Nam', 'Việt Nam'])
            if (',' in clean or ' and ' in clean) and not is_affil:
                # Tách bằng ' and ' trước, rồi ','
                parts = re.split(r'\s+and\s+', clean)
                all_parts = []
                for p in parts:
                    all_parts.extend([x.strip() for x in p.split(',') if x.strip()])
                # Nếu tất cả các phần đều ngắn (tên người), tách thành nhiều tác giả
                if len(all_parts) > 1 and all(len(p) < 60 for p in all_parts):
                    expanded.extend(all_parts)
                    continue
            expanded.append(clean)

        for info in expanded:
            clean = info.strip()
            if not clean:
                continue
            is_affil = any(kw in clean for kw in ['@', 'University', 'Institute', 'Dept', 'Faculty', 'Ltd',
                                                    'Department', 'School', 'Lab', 'Center', 'Vietnam',
                                                    'Viet Nam', 'Việt Nam'])
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
        
        def traverse_node(node):
            nonlocal text, has_math
            if not hasattr(node, "tag") or not isinstance(node.tag, str):
                return
            
            if node.tag == f"{{{ns_m}}}oMath":
                has_math = True
                self.total_formulas += 1
                latex_math = self.bo_toan.omml_element_to_latex(node)
                text += f" ${latex_math}$ "
                # Don't traverse inside oMath, the math parser handles it
                return
            elif node.tag == f"{{{ns_w}}}r":
                # Convert run to text
                run_obj = Run(node, p)
                text += loc_ky_tu(run_obj.text)
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
                            img_blob = rel.target_part.blob
                            img_ext = rel.target_part.content_type.split('/')[-1]
                            if img_ext == 'jpeg': img_ext = 'jpg'
                            elif img_ext == 'x-emf': img_ext = 'emf'
                            
                            img_hash = hashlib.md5(img_blob).hexdigest()[:8]
                            img_name = f"img_{img_hash}.{img_ext}"
                            
                            if self.thu_muc_anh:
                                os.makedirs(self.thu_muc_anh, exist_ok=True)
                                img_path = os.path.join(self.thu_muc_anh, img_name)
                            else:
                                img_path = img_name
                                
                            if not os.path.exists(img_path):
                                with open(img_path, "wb") as f:
                                    f.write(img_blob)
                            
                            ten_thu_muc = os.path.basename(self.thu_muc_anh)
                            latex_path = f"{ten_thu_muc}/{img_name}"
                            
                            if in_table:
                                latex_img = f"\n\\begin{{center}}\n\\includegraphics[width=\\linewidth]{{{latex_path}}}\n\\end{{center}}\n"
                            else:
                                self.dem_anh += 1
                                latex_img = f"\n\\begin{{figure}}[!ht]\n\\centering\n\\includegraphics[width=0.9\\columnwidth]{{{latex_path}}}\n\\caption{{}}\n\\label{{fig:img_{self.dem_anh}}}\n\\end{{figure}}\n"
                            text += latex_img
                        except Exception:
                            pass
                return
            elif node.tag == f"{{{ns_w}}}drawing":
                ns_a = "http://schemas.openxmlformats.org/drawingml/2006/main"
                blip = node.find(f".//{{{ns_a}}}blip")
                if blip is not None:
                    r_id = blip.get(f"{{{ns_r}}}embed")
                    if r_id:
                        try:
                            rel = p.part.rels[r_id]
                            img_blob = rel.target_part.blob
                            img_ext = rel.target_part.content_type.split('/')[-1]
                            
                            if img_ext == 'jpeg': img_ext = 'jpg'
                            elif img_ext == 'x-emf': img_ext = 'emf'
                            
                            img_hash = hashlib.md5(img_blob).hexdigest()[:8]
                            img_name = f"img_{img_hash}.{img_ext}"
                            
                            if self.thu_muc_anh:
                                os.makedirs(self.thu_muc_anh, exist_ok=True)
                                img_path = os.path.join(self.thu_muc_anh, img_name)
                            else:
                                img_path = img_name
                                
                            if not os.path.exists(img_path):
                                with open(img_path, "wb") as f:
                                    f.write(img_blob)
                            
                            ten_thu_muc = os.path.basename(self.thu_muc_anh)
                            latex_path = f"{ten_thu_muc}/{img_name}"
                            if in_table:
                                latex_img = f"\n\\begin{{center}}\n\\includegraphics[width=\\linewidth]{{{latex_path}}}\n\\end{{center}}\n"
                            else:
                                self.dem_anh += 1
                                latex_img = f"\n\\begin{{figure}}[!ht]\n\\centering\n\\includegraphics[width=0.9\\columnwidth]{{{latex_path}}}\n\\caption{{}}\n\\label{{fig:img_{self.dem_anh}}}\n\\end{{figure}}\n"
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

    def _parse_table(self, t: Table) -> Dict:
        """Parse table including rowspan (vMerge) and colspan (gridSpan)."""
        tbl = t._tbl
        tr_list = list(tbl.tr_lst)

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
                }

                for k in range(colspan):
                    if c + k < so_cot:
                        luoi[r][c + k] = cell_id
                        if (r, c + k) not in meta:
                            meta[(r, c + k)] = meta[(r, c)]

                c += colspan

        # Compute rowspan
        rowspan_map = {}
        for (r, c), info in list(meta.items()):
            if not info.get('start'): continue
            if meta.get((r, c)) != info: continue

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
            
        return {
            "type": "table",
            "rows": len(tr_list), 
            "cols": so_cot,
            "has_header": is_header,
            "data": parsed_rows
        }
