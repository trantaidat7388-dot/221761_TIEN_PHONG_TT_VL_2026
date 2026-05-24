import jinja2
import os
import re
import base64
from lxml import etree  # type: ignore
from bisect import bisect_right
from .utils import phat_hien_loai_tai_lieu
from .xu_ly_toan import BoXuLyToan
from .author_strategies import (
    IEEEAuthorStrategy,
    SpringerAuthorStrategy,
    ElsevierAuthorStrategy,
    ACMAuthorStrategy,
    MDPIAuthorStrategy,
    OSCMAuthorStrategy,
    JOVAuthorStrategy,
    GenericAuthorStrategy,
)

class JinjaLaTeXRenderer:
    """
    Nhận JSON IR và template LaTeX tương thích Jinja,
    rồi kết xuất file .tex cuối cùng bằng engine jinja2.
    """
    def __init__(self, template_dir: str):
        # Cần đổi dấu phân tách mặc định của Jinja2 vì LaTeX phụ thuộc rất nhiều vào { }
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_dir),
            block_start_string='<%',
            block_end_string='%>',
            variable_start_string='<<',
            variable_end_string='>>',
            comment_start_string='<#',
            comment_end_string='#>',
            trim_blocks=True,
            lstrip_blocks=True,
            autoescape=False # LaTeX cần chuỗi thô, việc escape được xử lý bằng LocKyTu trong bước parse AST
        )

        self.bo_toan = BoXuLyToan()
        self.env.filters['tex_escape'] = self.escape_latex

    def escape_latex(self, text: str) -> str:
        """Escape ký tự LaTeX đặc biệt nếu AST chưa xử lý."""
        # LocKyTu trong AST parser xử lý phần lớn việc escape.
        return str(text)

    def render_body_nodes(self, body_nodes: list, doc_class: str = "generic") -> str:
        """Kết xuất danh sách node ngữ nghĩa (body) sang chuỗi LaTeX."""
        # Tiền xử lý để nhóm các paragraph có "is_list" liên tiếp thành "list_block"
        grouped_nodes = []
        i = 0
        while i < len(body_nodes):
            node = body_nodes[i]
            if node.get("type") == "paragraph" and node.get("is_list"):
                list_items = []
                while i < len(body_nodes) and body_nodes[i].get("type") == "paragraph" and body_nodes[i].get("is_list"):
                    list_items.append(body_nodes[i])
                    i += 1
                grouped_nodes.append({
                    "type": "list_block",
                    "items": list_items
                })
            else:
                grouped_nodes.append(node)
                i += 1

        out = []
        table_counter = 0
        section_counter = 0
        for node in grouped_nodes:
            t = node.get("type", "")
            if t == "section":
                lvl = node.get("level", 1)
                text = node.get("text", "")
                
                if doc_class == "springer" and text.isupper() and len(text) > 3:
                    text = text.title()
                    
                # Tạo nhãn Section duy nhất động cho liên kết chéo
                sec_label = re.sub(r'[^a-zA-Z0-9]', '_', text.lower()).strip('_')
                sec_label = re.sub(r'_{2,}', '_', sec_label)
                
                if lvl == 1:
                    section_counter += 1
                    label_str = f"\\label{{sec:{sec_label}}}\\label{{sec_{section_counter}}}" if sec_label else f"\\label{{sec_{section_counter}}}"
                else:
                    label_str = f"\\label{{sec:{sec_label}}}" if sec_label else ""
                
                if lvl == 1:
                    out.append(f"\\section{{{text}}}{label_str}\n")
                elif lvl == 2:
                    out.append(f"\\subsection{{{text}}}{label_str}\n")
                else:
                    out.append(f"\\subsubsection{{{text}}}{label_str}\n")
            elif t == "list_block":
                out.append(self._render_list_block(node))
            elif t == "paragraph":
                para_text = str(node.get('text', '') or '')
                para_text = para_text.replace("\\n\\label{", " \\label{")
                # Chuẩn hóa token "\\n" vô tình xuất hiện trước các lệnh LaTeX chính.
                para_text = re.sub(
                    r'\\n(\\(?:label|caption|includegraphics|refstepcounter|begin|end)\b)',
                    r'\n\1',
                    para_text,
                )
                # Chuẩn hóa các ngắt dòng cứng từ nguồn DOC/PDF để tránh
                # tạo khoảng cách dòng không mong muốn trong đầu ra LaTeX.
                para_text = re.sub(r'[\u200b\u200c\u200d\ufeff\xa0]+', ' ', para_text)
                para_text = re.sub(r'\s*\n+\s*', ' ', para_text)
                para_text = re.sub(r'[ \t]{2,}', ' ', para_text).strip()
                
                # Áp dụng tự động hóa liên kết chéo cho Figure, Table, Equation, Section
                para_text = self._apply_cross_referencing(para_text)
                
                if doc_class in ("springer", "ieee"):
                    promoted_eq = self._promote_inline_equation_paragraph(para_text)
                    if promoted_eq:
                        out.append(promoted_eq)
                        continue
                if para_text:
                    # Strip leading/trailing newlines to prevent redundant blank lines
                    para_text = para_text.strip()
                    is_block = (
                        para_text.startswith(r"\begin{equation}") or 
                        para_text.startswith(r"\begin{figure}") or
                        node.get("is_equation")
                    )
                    if is_block:
                        # Don't add double newline before/after blocks that already handle their own spacing
                        out.append(f"{para_text}\n")
                    else:
                        out.append(f"{para_text}\n\n")
            elif t == "algorithm":
                out.append(self._render_algorithm(node))
            elif t == "table":
                table_counter += 1
                cols = node.get("cols", 1)
                rows_data = node.get("data", [])

                # Phân tích độ dài văn bản trong bảng biểu để thiết lập chế độ co giãn thông minh (Autofit)
                total_chars = 0
                cell_count = 0
                max_cell_len = 0
                for row in rows_data:
                    for cell in row:
                        cell_text = (cell.get("text") or "").strip()
                        cell_len = len(cell_text)
                        total_chars += cell_len
                        cell_count += 1
                        if cell_len > max_cell_len:
                            max_cell_len = cell_len
                avg_cell_len = total_chars / cell_count if cell_count > 0 else 0
                
                is_small_table = cols <= 3 and max_cell_len <= 20 and avg_cell_len <= 10
                used_resizebox = not is_small_table

                # Thiết lập độ rộng cột. Với bảng metadata 3 cột phổ biến
                col_widths = None
                if cols == 3 and rows_data:
                    first_row = rows_data[0]
                    headers = []
                    for c in first_row[:3]:
                        headers.append((c.get("text") or "").strip().lower())
                    joined = " | ".join(headers)
                    if (
                        ("feature" in joined or "đặc trưng" in joined)
                        and ("type" in joined or "kiểu" in joined)
                        and ("description" in joined or "mô tả" in joined)
                    ):
                        col_widths = [0.22, 0.20, 0.54]

                if not col_widths:
                    width_frac = 0.98 / cols if cols > 0 else 0.15
                    col_widths = [width_frac] * cols

                if is_small_table:
                    # Bảng nhỏ hiển thị tự nhiên với căn giữa đẹp mắt
                    col_def = "|" + "|".join(["c"] * cols) + "|"
                else:
                    col_def = "|" + "|".join([f"p{{{w:.3f}\\linewidth}}" for w in col_widths]) + "|"
                
                # Phát hiện bảng có nên là dạng rộng (trải qua hai cột) hay không
                is_wide = cols > 4 or node.get("is_wide", False)
                env_name = "table*" if (is_wide and doc_class == "acm") else "table"
                scale_width = "\\textwidth" if env_name == "table*" else "\\columnwidth"

                # Bảng siêu dài (>12 hàng): dùng longtable
                NGUONG_SIEU_DAI = 12
                is_springer_long = (
                    doc_class == "springer"
                    and len(rows_data) > NGUONG_SIEU_DAI
                )
                if is_springer_long:
                    out.append(self._render_springer_longtable(node, cols, col_widths, col_def))
                    continue

                is_ieee_long = (
                    doc_class in ("acm", "generic")
                    and len(rows_data) > NGUONG_SIEU_DAI
                )
                if is_ieee_long:
                    out.append(self._render_ieee_longtable(node, cols, col_widths))
                    continue

                # Theo chuẩn IEEE: caption nằm TRÊN bảng
                table_caption = node.get("caption", "Table")
                table_caption = table_caption.replace(r"\url{", r"\protect\url{")
                if env_name == "table*":
                    table_pos = "[t]"
                elif doc_class == "springer":
                    table_pos = "[htbp]"
                else:
                    table_pos = "[htbp]"
                
                out.append(f"\\begin{{{env_name}}}{table_pos}\n\\centering\n")
                out.append(f"\\caption{{{table_caption}}}\\label{{tab{table_counter}}}\n")
                if used_resizebox:
                    out.append(f"\\resizebox{{{scale_width}}}{{!}}{{%.\n")
                    out.append("\\begingroup\\small\\setlength{\\tabcolsep}{3pt}\\setlength{\\arrayrulewidth}{0.4pt}\\renewcommand{\\arraystretch}{0.95}\n")
                else:
                    out.append("\\begingroup\\setlength{\\tabcolsep}{10pt}\\setlength{\\arrayrulewidth}{0.4pt}\\renewcommand{\\arraystretch}{1.1}\n")
                out.append(f"\\begin{{tabular}}{{{col_def}}}\n\\hline\n")
                
                # Theo dõi các multirow đang hoạt động: col_index -> số hàng còn lại
                active_multirows = {}  # col_index -> rows_remaining

                for r_idx, row in enumerate(rows_data):
                    tex_cells = []
                    c_logical = 0   # Logical column index in final tabular grid
                    is_header_row = bool(node.get("has_header")) and r_idx == 0
                    row_multirow_starts = {}  # col -> rowspan (new multirows starting this row)

                    # Parser của bảng đã xử lý cấu trúc merge. Khi render phải
                    # tôn trọng trực tiếp các ô logic đó để tránh lệch do merge hai lần.
                    for cell in row:
                        if c_logical >= cols:
                            break

                        if cell.get("type") == "empty":
                            tex_cells.append("")
                            c_logical += 1
                            continue

                        colspan = max(1, int(cell.get("colspan", 1) or 1))
                        rowspan = max(1, int(cell.get("rowspan", 1) or 1))
                        text = self._normalize_table_cell_linebreaks(cell.get("text") or "")
                        text = self._sanitize_table_cell_math(text)
                        if is_header_row and text.strip() and "\\textbf{" not in text:
                            text = f"\\textbf{{{text}}}"

                        token = text
                        if rowspan > 1:
                            token = f"\\multirow{{{rowspan}}}{{*}}{{{token}}}"
                            # Ghi nhận các multirow bắt đầu ở hàng này
                            for dc in range(colspan):
                                row_multirow_starts[c_logical + dc] = rowspan
                        if colspan > 1:
                            width_slice = col_widths[c_logical:c_logical + colspan]
                            if width_slice:
                                mc_width = sum(width_slice)
                            else:
                                mc_width = (0.98 / cols) * colspan if cols > 0 else 0.15 * colspan
                            
                            if c_logical == 0:
                                mc_format = f"|p{{{mc_width:.3f}\\linewidth}}|"
                            else:
                                mc_format = f"p{{{mc_width:.3f}\\linewidth}}|"
                                
                            token = f"\\multicolumn{{{colspan}}}{{{mc_format}}}{{{token}}}"

                        tex_cells.append(token)
                        c_logical += colspan

                    while c_logical < cols:
                        tex_cells.append("")
                        c_logical += 1
                    
                    # Lọc để ghép thành một dòng LaTeX (bỏ qua các ô đã bị multicolumn chiếm trong cùng hàng)
                    dong_filtered = []
                    skip_mc = 0
                    for cell_str in tex_cells:
                        if skip_mc > 0:
                            skip_mc -= 1
                            continue
                        dong_filtered.append(cell_str)
                        if "\\multicolumn{" in cell_str:
                            mc_match = re.search(r'\\multicolumn\{(\d+)\}', cell_str)
                            if mc_match:
                                skip_mc = int(mc_match.group(1)) - 1
                    
                    # Cập nhật theo dõi multirow đang hoạt động
                    # Trước hết, giảm số hàng còn lại của các multirow hiện có
                    new_active = {}
                    for col_idx, remaining in active_multirows.items():
                        if remaining > 1:
                            new_active[col_idx] = remaining - 1
                    # Sau đó thêm các multirow mới bắt đầu từ hàng này
                    for col_idx, rspan in row_multirow_starts.items():
                        new_active[col_idx] = rspan
                    active_multirows = new_active

                    # Xác định đường kẻ ngang: dùng \cline nếu có multirow còn kéo
                    # sang hàng kế tiếp, ngược lại dùng \hline
                    spanning_cols = set()
                    for col_idx, remaining in active_multirows.items():
                        if remaining > 1:  # Vẫn còn kéo sang hàng kế tiếp
                            spanning_cols.add(col_idx)
                    
                    if spanning_cols and r_idx < len(rows_data) - 1:
                        # Tạo lệnh \cline cho các đoạn cột không bị multirow chiếm
                        cline_parts = []
                        range_start = None
                        for ci in range(cols):
                            if ci not in spanning_cols:
                                if range_start is None:
                                    range_start = ci
                            else:
                                if range_start is not None:
                                    cline_parts.append(f"\\cline{{{range_start + 1}-{ci}}}")
                                    range_start = None
                        if range_start is not None:
                            cline_parts.append(f"\\cline{{{range_start + 1}-{cols}}}")
                        
                        hline_str = "".join(cline_parts) if cline_parts else "\\hline"
                    else:
                        hline_str = "\\hline"

                    out.append(" & ".join(dong_filtered) + " \\\\\n" + hline_str + "\n")
                    
                out.append("\\end{tabular}\n")
                out.append("\\endgroup\n")
                if used_resizebox:
                    out.append("}\n") # End of \resizebox
                out.append(f"\\end{{{env_name}}}\n\n")
        
        # Đảm bảo mọi phần tử trong `out` đều là chuỗi
        result = "".join([str(x) for x in out])

        # Hậu xử lý: bỏ các wrapper chế độ text (\textit, \textbf) bên trong môi trường
        # equation vì chúng có thể gây lỗi "Missing $ inserted" trong LaTeX.
        def _clean_equation_block(m):
            block = m.group(0)
            block = re.sub(r'\\textit\{([^{}]*)\}', r'\1', block)
            block = re.sub(r'\\textbf\{([^{}]*)\}', r'\1', block)
            return block

        result = re.sub(
            r'\\begin\{equation\}.*?\\end\{equation\}',
            _clean_equation_block,
            result,
            flags=re.DOTALL,
        )

        return result

    def _render_springer_longtable(
        self,
        node: dict,
        cols: int,
        col_widths: list,
        col_def: str,
    ) -> str:
        """Render bảng siêu dài (>12 hàng) cho Springer LLNCS bằng longtable.

        Springer LLNCS là định dạng 1 cột nên longtable hoạt động trực tiếp.
        Không cần \\onecolumn / \\twocolumn như IEEE twocolumn.
        Dùng \\linewidth thay vì \\textwidth để đúng với kích thước text block.
        """
        rows_data = node.get("data", [])
        table_caption = node.get("caption", "Table").replace(r"\url{", r"\protect\url{")
        has_header = bool(node.get("has_header"))

        # Dùng linewidth (đúng cho Springer 1-cột)
        lw_col_widths = [w for w in col_widths]
        lt_col_def = (
            "|"
            + "|".join([f"p{{{w:.3f}\\linewidth}}" for w in lw_col_widths])
            + "|"
        )

        out = []
        out.append(f"\\setlength{{\\arrayrulewidth}}{{0.4pt}}")
        out.append(f"\\begin{{longtable}}{{{lt_col_def}}}")
        # Caption TRÊN nội dung (chuẩn IEEE + Springer cho bảng)
        out.append(f"\\caption{{{table_caption}}}\\\\")
        out.append("\\hline")

        active_multirows: dict = {}

        for r_idx, row in enumerate(rows_data):
            tex_cells = []
            c_logical = 0
            is_header_row = has_header and r_idx == 0
            row_multirow_starts: dict = {}

            for cell in row:
                if c_logical >= cols:
                    break
                if cell.get("type") == "empty":
                    tex_cells.append("")
                    c_logical += 1
                    continue

                colspan = max(1, int(cell.get("colspan", 1) or 1))
                rowspan = max(1, int(cell.get("rowspan", 1) or 1))
                text = self._normalize_table_cell_linebreaks(cell.get("text") or "")
                text = self._sanitize_table_cell_math(text)
                if is_header_row and text.strip() and "\\textbf{" not in text:
                    text = f"\\textbf{{{text}}}"

                token = text
                if rowspan > 1:
                    token = f"\\multirow{{{rowspan}}}{{*}}{{{token}}}"
                    for dc in range(colspan):
                        row_multirow_starts[c_logical + dc] = rowspan
                if colspan > 1:
                    width_slice = lw_col_widths[c_logical:c_logical + colspan]
                    mc_width = sum(width_slice) if width_slice else (0.98 / cols) * colspan
                    mc_fmt = (
                        f"|p{{{mc_width:.3f}\\linewidth}}|"
                        if c_logical == 0 else
                        f"p{{{mc_width:.3f}\\linewidth}}|"
                    )
                    token = f"\\multicolumn{{{colspan}}}{{{mc_fmt}}}{{{token}}}"

                tex_cells.append(token)
                c_logical += colspan

            while c_logical < cols:
                tex_cells.append("")
                c_logical += 1

            dong_filtered = []
            skip_mc = 0
            for cell_str in tex_cells:
                if skip_mc > 0:
                    skip_mc -= 1
                    continue
                dong_filtered.append(cell_str)
                if "\\multicolumn{" in cell_str:
                    mc_m = re.search(r'\\multicolumn\{(\d+)\}', cell_str)
                    if mc_m:
                        skip_mc = int(mc_m.group(1)) - 1

            # Cập nhật multirow tracking
            new_active: dict = {}
            for col_idx, remaining in active_multirows.items():
                if remaining > 1:
                    new_active[col_idx] = remaining - 1
            for col_idx, rspan in row_multirow_starts.items():
                new_active[col_idx] = rspan
            active_multirows = new_active

            spanning_cols = {
                col_idx for col_idx, remaining in active_multirows.items()
                if remaining > 1
            }

            out.append(" & ".join(dong_filtered) + " \\\\")

            if spanning_cols and r_idx < len(rows_data) - 1:
                cline_parts = []
                range_start = None
                for ci in range(cols):
                    if ci not in spanning_cols:
                        if range_start is None:
                            range_start = ci
                    else:
                        if range_start is not None:
                            cline_parts.append(f"\\cline{{{range_start + 1}-{ci}}}")
                            range_start = None
                if range_start is not None:
                    cline_parts.append(f"\\cline{{{range_start + 1}-{cols}}}")
                out.append("".join(cline_parts) if cline_parts else "\\hline")
            else:
                out.append("\\hline")

        out.append("\\end{longtable}")
        out.append("")
        return "\n".join(out) + "\n"

    def _render_ieee_longtable(
        self,
        node: dict,
        cols: int,
        col_widths: list,
    ) -> str:
        """Render bảng siêu dài (>12 hàng) cho IEEE/ACM twocolumn bằng longtable.

        IEEE/ACM dùng twocolumn nên longtable KHÔNG hoạt động trực tiếp.
        Phải bọc bằng ``\\onecolumn`` ... ``\\twocolumn`` để tạm thoát 2 cột.
        Dùng ``\\textwidth`` (toàn trang) thay vì ``\\linewidth`` (nửa cột).
        """
        rows_data = node.get("data", [])
        table_caption = node.get("caption", "Table").replace(r"\url{", r"\protect\url{")
        has_header = bool(node.get("has_header"))

        # Dùng textwidth (toàn trang sau khi thoát 2 cột)
        tw_col_widths = [w for w in col_widths]
        lt_col_def = (
            "|"
            + "|".join([f"p{{{w:.3f}\\textwidth}}" for w in tw_col_widths])
            + "|"
        )

        out = []
        # Thoát khỏi chế độ 2 cột
        out.append("\\onecolumn")
        out.append("")
        out.append(f"\\setlength{{\\arrayrulewidth}}{{0.4pt}}")
        out.append(f"\\begin{{longtable}}{{{lt_col_def}}}")
        # Caption TRÊN nội dung (chuẩn IEEE)
        out.append(f"\\caption{{{table_caption}}}\\\\")
        out.append("\\hline")

        active_multirows: dict = {}

        for r_idx, row in enumerate(rows_data):
            tex_cells = []
            c_logical = 0
            is_header_row = has_header and r_idx == 0
            row_multirow_starts: dict = {}

            for cell in row:
                if c_logical >= cols:
                    break
                if cell.get("type") == "empty":
                    tex_cells.append("")
                    c_logical += 1
                    continue

                colspan = max(1, int(cell.get("colspan", 1) or 1))
                rowspan = max(1, int(cell.get("rowspan", 1) or 1))
                text = self._normalize_table_cell_linebreaks(cell.get("text") or "")
                text = self._sanitize_table_cell_math(text)
                if is_header_row and text.strip() and "\\textbf{" not in text:
                    text = f"\\textbf{{{text}}}"

                token = text
                if rowspan > 1:
                    token = f"\\multirow{{{rowspan}}}{{*}}{{{token}}}"
                    for dc in range(colspan):
                        row_multirow_starts[c_logical + dc] = rowspan
                if colspan > 1:
                    width_slice = tw_col_widths[c_logical:c_logical + colspan]
                    mc_width = sum(width_slice) if width_slice else (0.98 / cols) * colspan
                    mc_fmt = (
                        f"|p{{{mc_width:.3f}\\textwidth}}|"
                        if c_logical == 0 else
                        f"p{{{mc_width:.3f}\\textwidth}}|"
                    )
                    token = f"\\multicolumn{{{colspan}}}{{{mc_fmt}}}{{{token}}}"

                tex_cells.append(token)
                c_logical += colspan

            while c_logical < cols:
                tex_cells.append("")
                c_logical += 1

            dong_filtered = []
            skip_mc = 0
            for cell_str in tex_cells:
                if skip_mc > 0:
                    skip_mc -= 1
                    continue
                dong_filtered.append(cell_str)
                if "\\multicolumn{" in cell_str:
                    mc_m = re.search(r'\\multicolumn\{(\d+)\}', cell_str)
                    if mc_m:
                        skip_mc = int(mc_m.group(1)) - 1

            # Cập nhật multirow tracking
            new_active: dict = {}
            for col_idx, remaining in active_multirows.items():
                if remaining > 1:
                    new_active[col_idx] = remaining - 1
            for col_idx, rspan in row_multirow_starts.items():
                new_active[col_idx] = rspan
            active_multirows = new_active

            spanning_cols = {
                col_idx for col_idx, remaining in active_multirows.items()
                if remaining > 1
            }

            out.append(" & ".join(dong_filtered) + " \\\\")

            if spanning_cols and r_idx < len(rows_data) - 1:
                cline_parts = []
                range_start = None
                for ci in range(cols):
                    if ci not in spanning_cols:
                        if range_start is None:
                            range_start = ci
                    else:
                        if range_start is not None:
                            cline_parts.append(f"\\cline{{{range_start + 1}-{ci}}}")
                            range_start = None
                if range_start is not None:
                    cline_parts.append(f"\\cline{{{range_start + 1}-{cols}}}")
                out.append("".join(cline_parts) if cline_parts else "\\hline")
            else:
                out.append("\\hline")

        out.append("\\end{longtable}")
        out.append("")
        # Quay lại chế độ 2 cột
        out.append("\\twocolumn")
        out.append("")
        return "\n".join(out) + "\n"

    def _normalize_table_cell_linebreaks(self, text: str) -> str:

        """Chuẩn hóa xuống dòng trong ô bảng để LaTeX hiểu đúng."""
        if not text:
            return ""
        cleaned = text.replace("\r\n", "\n").replace("\r", "\n")
        return cleaned.replace("\n", r"\\ ")

    def _sanitize_table_cell_math(self, text: str) -> str:
        """Normalize math in table cells to avoid equation blocks or bad escapes."""
        if not text:
            return ""

        def _flatten_equation(match):
            inner = (match.group(1) or "").strip()
            if not inner:
                return ""
            inner = re.sub(r"\\tag\{[^}]+\}", "", inner)
            inner = re.sub(r"\s+", " ", inner).strip()
            return f"${inner}$"

        text = re.sub(
            r"\\begin\{equation\*?\}\s*(.*?)\s*\\end\{equation\*?\}",
            _flatten_equation,
            text,
            flags=re.DOTALL,
        )

        # Fix doubled backslashes inside inline math: $\\approx$ -> $\approx$.
        text = re.sub(r"\$\\\\([A-Za-z]+)", r"$\\\1", text)
        text = re.sub(r"\\\\([A-Za-z]+)\$", r"\\\1$", text)
        return text

    def _process_omml_math(self, text_with_omml: str) -> str:
        r"""Thay placeholder «OMML:base64» bằng LaTeX thật.

        Nếu nằm trong môi trường equation thì không bọc $...$; ngược lại sẽ bọc.
        """
        if "«OMML:" not in text_with_omml:
            return text_with_omml

        def replace_inline(match):
            b64_str = match.group(1)
            try:
                xml_str = base64.b64decode(b64_str).decode('utf-8')
                omml_elem = etree.fromstring(xml_str.encode('utf-8'))
                latex_math = self.bo_toan.omml_element_to_latex(omml_elem)
                # Bỏ dấu $ sẵn có để tránh bọc hai lớp.
                latex_math = latex_math.strip().strip('$').strip()
                if not latex_math:
                    latex_math = self.bo_toan.omml_to_text(omml_elem)
                return f"${latex_math}$"
            except Exception as e:
                print(f"[Cảnh báo] Lỗi parse OMML sang LaTeX inline: {e}")
                return " [Math Error] "

        def replace_block(match):
            b64_str = match.group(1)
            try:
                xml_str = base64.b64decode(b64_str).decode('utf-8')
                omml_elem = etree.fromstring(xml_str.encode('utf-8'))
                latex_math = self.bo_toan.omml_element_to_latex(omml_elem)
                latex_math = latex_math.strip().strip('$').strip()
                if not latex_math:
                    latex_math = self.bo_toan.omml_to_text(omml_elem)
                return latex_math
            except Exception as e:
                print(f"[Cảnh báo] Lỗi parse OMML sang LaTeX block: {e}")
                return " "

        def process_equation_env(match):
            eq_block = match.group(0)
            return re.sub(r"«OMML:([A-Za-z0-9+/=]+)»", replace_block, eq_block)
            
        # 1. Xử lý OMML bên trong môi trường equation (toán khối)
        text_with_omml = re.sub(r"\\begin\{equation\*?\}.*?\\end\{equation\*?\}", process_equation_env, text_with_omml, flags=re.DOTALL)
        
        # 2. Xử lý các khối OMML còn lại (toán inline)
        text_with_omml = re.sub(r"«OMML:([A-Za-z0-9+/=]+)»", replace_inline, text_with_omml)
        
        return text_with_omml

    def _normalize_inline_math_escapes(self, text: str) -> str:
        """Fix doubled backslashes inside inline math tokens like $\\nabla$ -> $\nabla$."""
        if not text:
            return text
        text = re.sub(r"\$\\\\([A-Za-z]+)", r"$\\\1", text)
        text = re.sub(r"\\\\([A-Za-z]+)\$", r"\\\1$", text)
        return text

    def _soften_long_equations(self, text: str) -> str:
        """Insert soft breaks into long equation blocks to reduce overflow."""
        if not text:
            return text

        def _soften_block(match):
            env = match.group(1) or "equation"
            inner = match.group(2) or ""

            # Collapse letter-spaced tokens (e.g., "W e b C r y p t o" -> "WebCrypto").
            def _collapse_spaced_letters(text_value: str) -> str:
                def _join_letters(m):
                    return re.sub(r"\s+", "", m.group(0))

                return re.sub(r"(?:\b[A-Za-z]\b\s+){2,}\b[A-Za-z]\b", _join_letters, text_value)

            inner = _collapse_spaced_letters(inner)

            # Lowered threshold for IEEE columns (approx 70 chars)
            # Narrow columns often overflow around 65-75 characters.
            if len(inner) >= 70:
                scaled = re.sub(r"\s+", " ", inner).strip()
                return (
                    f"\\begin{{{env}}}\n"
                    f"\\resizebox{{\\columnwidth}}{{!}}{{${{\\displaystyle {scaled}}}$}}\n"
                    f"\\end{{{env}}}"
                )

            # For medium equations, try to insert allowbreak at common points (dots, commas)
            # Note: Standard equation env doesn't break, but this helps if user changes to dmath/multline
            softened = inner
            softened = re.sub(r"\.(?=[A-Za-z])", r".\\allowbreak ", softened)
            softened = re.sub(r",\s*", r",\\allowbreak ", softened)
            softened = re.sub(r"\(\s*", r"(\\allowbreak ", softened)
            softened = re.sub(r"\s+", " ", softened).strip()
            
            return f"\\begin{{{env}}}\n{softened}\n\\end{{{env}}}"

        return re.sub(
            r"\\begin\{(equation\*?)\}\s*(.*?)\s*\\end\{\1\}",
            _soften_block,
            text,
            flags=re.DOTALL,
        )

    def render(self, template_name: str, ir_data: dict, output_path: str, **kwargs):
        """
        Kết xuất dữ liệu IR bằng file template đã chỉ định.
        Template BẮT BUỘC phải dùng dấu phân tách tùy chỉnh (<< >>, <% %>).
        """
        template = self.env.get_template(template_name)
        
        # Phát hiện loại tài liệu để tạo đầu ra phù hợp với định dạng
        try:
            from jinja2 import FileSystemLoader
            loader = self.env.loader
            if isinstance(loader, FileSystemLoader):
                template_path = os.path.join(loader.searchpath[0], template_name)
            else:
                template_path = template_name
            with open(template_path, 'r', encoding='utf-8', errors='ignore') as f:
                template_src = f.read()
        except Exception:
            template_src = ""
        
        doc_class = phat_hien_loai_tai_lieu(template_src)

        # Kết xuất sẵn body nodes để template chỉ cần chèn << body >>
        body_tex = self.render_body_nodes(ir_data.get('body', []), doc_class=doc_class)
        body_tex = self._process_omml_math(body_tex)
        body_tex = self._normalize_inline_math_escapes(body_tex)
        body_tex = self._soften_long_equations(body_tex)
        
        if doc_class == "ieee":
            body_tex = self._normalize_ieee_figure_placement(body_tex)
            body_tex = self._remove_float_barriers(body_tex)
        elif doc_class == "springer":
            body_tex = self._normalize_springer_float_placement(body_tex)

        bib_file = self._generate_bib_file(ir_data.get('references', []), output_path)
        lvl1_count = sum(1 for node in ir_data.get('body', []) if node.get("type") == "section" and node.get("level", 1) == 1)
        references_block = self._generate_thebibliography(ir_data.get('references', []), doc_class, last_sec_num=lvl1_count)
        
        # Ghi đè author_block bằng phiên bản phù hợp với định dạng tài liệu
        metadata = dict(ir_data.get('metadata', {}))
        for key, value in metadata.items():
            if isinstance(value, str):
                metadata[key] = self._process_omml_math(value)
                
        authors = metadata.get('authors', [])
        metadata['author_block'] = self._generate_author_block(authors, doc_class)
        
        tex_content = template.render(
            metadata=metadata,
            body=body_tex,
            has_bib=bool(bib_file),
            bib_file="references",
            references_block=references_block,
        )
        tex_content = self._normalize_tex_preamble(tex_content, doc_class)

        # Fix specific LaTeX compilation errors caused by double-escaped arrows inside algorithms or math
        tex_content = tex_content.replace(r"\\\\leftarrow", r"\leftarrow")
        tex_content = tex_content.replace(r"\\leftarrow", r"\leftarrow")

        # Ưu tiên pdfLaTeX theo mặc định, nhưng chuyển sang XeLaTeX khi nội dung
        # đã render có package cần engine Unicode.
        magic_comment = f"% !TeX program = {self._choose_magic_engine(tex_content)}\n"

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(magic_comment + tex_content)

        # Xóa latexmkrc cũ có thể ép XeLaTeX từ các lần xuất trước.
        latexmkrc_path = os.path.join(os.path.dirname(output_path), 'latexmkrc')
        if os.path.exists(latexmkrc_path):
            try:
                os.remove(latexmkrc_path)
            except OSError:
                pass

    def _normalize_ieee_figure_placement(self, body_tex: str) -> str:
        """Normalize IEEE figure hints with a context-aware rule near section breaks.

        Default figure floats stay flexible as ``[htbp]``. For figures that are very
        close to the next section heading, convert them into inline non-float blocks
        so they remain anchored to the local narrative flow.
        """
        body_tex = re.sub(r"\\begin\{figure\}\[[^\]]*\]", r"\\begin{figure}[H]", body_tex)
        figure_pattern = re.compile(r"\\begin\{figure\}\[H\].*?\\end\{figure\}", re.DOTALL)
        section_pattern = re.compile(r"\\section\{")

        chunks = []
        cursor = 0
        for match in figure_pattern.finditer(body_tex):
            start, end = match.span()
            fig_block = match.group(0)

            # Các block figure không có caption thường là ảnh chụp công thức hoặc
            # block trang trí từ Word. Giữ chúng ở dạng inline để tránh lệch float.
            if self._has_empty_caption(fig_block):
                fig_block = self._convert_figure_float_to_inline(fig_block, with_counter=False)
                chunks.append(body_tex[cursor:start])
                chunks.append(fig_block)
                cursor = end
                continue

            next_section = section_pattern.search(body_tex, end)
            if next_section is not None:
                tail_text = body_tex[end:next_section.start()]
                if len(tail_text.strip()) <= 120:
                    fig_block = self._convert_figure_float_to_inline(fig_block, with_counter=True)

            chunks.append(body_tex[cursor:start])
            chunks.append(fig_block)
            cursor = end

        chunks.append(body_tex[cursor:])
        return "".join(chunks)

    def _has_empty_caption(self, fig_block: str) -> bool:
        cap_match = re.search(r"\\caption\{(.*?)\}", fig_block, re.DOTALL)
        if cap_match is None:
            return True
        return not cap_match.group(1).strip()

    def _convert_figure_float_to_inline(self, fig_block: str, with_counter: bool = True) -> str:
        """Convert a figure float block into an inline figure-like block.

        This avoids LaTeX float queue behavior in tight IEEE two-column layouts.
        """
        # Một số chuyển đổi DOCX mang token "\\n" trước \label.
        # Chuẩn hóa nó trước để việc trích xuất bằng regex ổn định.
        fig_block = fig_block.replace("\\n\\label", "\n\\label")

        include_match = re.search(r"\\includegraphics(?:\[[^\]]*\])?\{[^}]+\}", fig_block, re.DOTALL)
        if include_match is None:
            return fig_block

        include_cmd = include_match.group(0)
        include_cmd = include_cmd.replace("\\n\\label", " \\label")
        cap_match = re.search(r"\\caption\{(.*?)\}", fig_block, re.DOTALL)
        label_match = re.search(r"\\label\{([^}]+)\}", fig_block)

        caption_text = (cap_match.group(1).strip() if cap_match else "")
        label_name = (label_match.group(1).strip() if label_match else "")
        label_cmd = f"\\label{{{label_name}}}" if label_name else ""

        if caption_text and with_counter:
            return (
                "\\begingroup\n"
                "\\centering\n"
                "\\refstepcounter{figure}\n"
                f"{include_cmd}\n"
                f"\\small Fig. \\thefigure. {caption_text}"
                + (f" {label_cmd}" if label_cmd else "")
                + "\n\\par\n"
                "\\endgroup\n"
            )

        if caption_text and not with_counter:
            return (
                "\\begingroup\n"
                "\\centering\n"
                f"{include_cmd}\n"
                f"\\small {caption_text}"
                + (f" {label_cmd}" if label_cmd else "")
                + "\n\\par\n"
                "\\endgroup\n"
            )

        return (
            "\\begingroup\n"
            "\\centering\n"
            f"{include_cmd}"
            + (f"\n{label_cmd}" if label_cmd else "")
            + "\n\\par\n"
            "\\endgroup\n"
        )

    def _normalize_springer_float_placement(self, body_tex: str) -> str:
        """Normalize Springer float hints and add local barriers near headings.

        Use ``[!ht]`` to avoid float-only pages caused by the ``p`` placement mode,
        then add ``\\FloatBarrier`` only when a section starts shortly after a float.
        """
        body_tex = re.sub(r"\\begin\{figure\}\[[^\]]*\]", r"\\begin{figure}[H]", body_tex)
        body_tex = re.sub(r"\\begin\{table\}\[[^\]]*\]", r"\\begin{table}[H]", body_tex)

        float_end_pattern = re.compile(r"\\end\{(?:figure|table)\}")
        section_pattern = re.compile(r"\\(?:section|subsection|subsubsection)\{")

        float_ends = [m.end() for m in float_end_pattern.finditer(body_tex)]
        if not float_ends:
            return body_tex

        chunks = []
        cursor = 0
        for sec in section_pattern.finditer(body_tex):
            sec_start = sec.start()
            should_insert = False

            nearest_float_idx = bisect_right(float_ends, sec_start) - 1
            if nearest_float_idx >= 0:
                nearest_float_end = float_ends[nearest_float_idx]
                between = body_tex[nearest_float_end:sec_start]
                if len(between.strip()) <= 420 and "\\FloatBarrier" not in between:
                    should_insert = True

            chunks.append(body_tex[cursor:sec_start])
            if should_insert:
                chunks.append("\n\\FloatBarrier\n")
            chunks.append(sec.group(0))
            cursor = sec.end()

        chunks.append(body_tex[cursor:])
        return "".join(chunks)

    def _promote_inline_equation_paragraph(self, para_text: str) -> str | None:
        """Convert short inline equation paragraphs ending with (n) into equation blocks."""
        text = (para_text or "").strip()
        if not text or "\\begin{equation}" in text:
            return None

        m = re.match(r"^(?P<expr>.+?)\s*\((?P<num>\d+)\)\s*$", text)
        if m is None:
            return None

        expr = (m.group("expr") or "").strip()
        if not expr:
            return None
        if len(expr) > 180:
            return None
        if "=" not in expr:
            return None
        if re.search(r"\\(?:cite|ref|section|subsection)\b", expr):
            return None
        if not re.search(r"\\[A-Za-z]+|[+\-*/=^_]", expr):
            return None

        # Word text formatting wrappers are not needed inside display math.
        expr = re.sub(r"\\textit\{([^{}]+)\}", r"\1", expr)
        expr = re.sub(r"\\textbf\{([^{}]+)\}", r"\1", expr)
        expr = re.sub(r"\s+", " ", expr).strip()
        if not expr:
            return None

        num = m.group("num")
        return f"\\begin{{equation}}\n{expr}\n\\tag{{{num}}}\\label{{eq:eq_{num}}}\n\\end{{equation}}\n\n"

    def _remove_float_barriers(self, body_tex: str) -> str:
        """Remove legacy FloatBarrier markers that can force awkward page breaks."""
        return re.sub(r"^[ \t]*\\FloatBarrier[ \t]*\n?", "", body_tex, flags=re.MULTILINE)

    def _choose_magic_engine(self, tex_content: str) -> str:
        """Choose a safe TeX engine hint for editors/Overleaf based on content.
        
        Priority:
        1. Packages or content requiring XeLaTeX (fontspec, unicode-math, polyglossia, Vietnamese chars)
        2. Explicit pdfTeX in documentclass options
        3. Default to pdflatex (fallback to xelatex happens during compilation if needed)
        """
        if re.search(r"\\usepackage\{fontspec\}", tex_content) or \
           re.search(r"\\usepackage\{unicode-math\}", tex_content) or \
           re.search(r"\\usepackage\{polyglossia\}", tex_content) or \
           re.search(r'[à-ỹÀ-ỸđĐ\u1E00-\u1EFF]', tex_content):
            return "xelatex"

        # Tôn trọng template đã ghim pdfTeX trực tiếp trong options của documentclass.
        docclass_opts = re.search(r"\\documentclass\s*\[([^\]]*)\]", tex_content)
        if docclass_opts is not None:
            options = [o.strip().lower() for o in docclass_opts.group(1).split(",")]
            if any(o in ("pdftex", "pdflatex") for o in options):
                return "pdflatex"

        # Mặc định dùng pdflatex. Nếu lỗi do encoding/Unicode,
        # quá trình biên dịch sẽ tự thử lại bằng xelatex.
        return "pdflatex"

    def _normalize_tex_preamble(self, tex_content: str, doc_class: str = "generic") -> str:
        r"""Normalize preamble so pdfLaTeX avoids OT1 pitfalls (e.g., \DJ unavailable)."""
        tex_content = self._normalize_literal_newline_tokens(tex_content)
        tex_content = tex_content.replace(
            "\\usepackage[OT1]{fontenc}",
            "\\usepackage[T1]{fontenc}",
        )

        has_fontenc = re.search(r"\\usepackage(?:\[[^\]]*\])?\{fontenc\}", tex_content) is not None
        has_iftex = re.search(r"\\usepackage(?:\[[^\]]*\])?\{iftex\}", tex_content) is not None
        has_multirow = re.search(r"\\usepackage(?:\[[^\]]*\])?\{multirow\}", tex_content) is not None
        doc_match = re.search(r"^[ \t]*\\begin\{document\}", tex_content, re.MULTILINE)
        if doc_match is None:
            return tex_content

        inject_lines = []
        if not has_iftex:
            inject_lines.append("\\usepackage{iftex}")
        if not has_fontenc:
            inject_lines.append("\\ifXeTeX\\else")
            inject_lines.append("\\usepackage[T5,T1]{fontenc}")
            inject_lines.append("\\usepackage[utf8]{inputenc}")
            inject_lines.append("\\fi")
        if not has_multirow:
            inject_lines.append("\\usepackage{multirow}")
        
        if "graphicx" not in tex_content:
            inject_lines.append("\\usepackage{graphicx}")

        if "\\begin{algorithm}" in tex_content:
            if "\\usepackage{algorithm}" not in tex_content:
                inject_lines.append("\\usepackage{algorithm}")
                # Thêm khung cho thuật toán (Boxed style)
                inject_lines.append("\\floatstyle{boxed}")
                inject_lines.append("\\restylefloat{algorithm}")
            if "\\usepackage{algorithmic}" not in tex_content:
                inject_lines.append("\\usepackage{algorithmic}")
            if "\\usepackage{float}" not in tex_content:
                inject_lines.append("\\usepackage{float}")
        
        # Đảm bảo mathtools được nạp để dùng các ký hiệu như \coloneqq
        if "\\usepackage{mathtools}" not in tex_content:
            inject_lines.append("\\usepackage{mathtools}")
            
        if "IEEEtran" in tex_content:
            inject_lines.append("\\raggedbottom")
            inject_lines.append("\\setlength{\\textfloatsep}{6pt plus 2pt minus 2pt}")
            inject_lines.append("\\setlength{\\intextsep}{6pt plus 2pt minus 2pt}")
        elif doc_class == "springer":
            # Springer (LLNCS) needs very tight spacing to maintain page count
            inject_lines.append("\\setlength{\\textfloatsep}{4pt plus 1pt minus 1pt}")
            inject_lines.append("\\setlength{\\intextsep}{4pt plus 1pt minus 1pt}")
            inject_lines.append("\\setlength{\\floatsep}{4pt plus 1pt minus 1pt}")
            inject_lines.append("\\setlength{\\abovedisplayskip}{3pt plus 1pt minus 1pt}")
            inject_lines.append("\\setlength{\\belowdisplayskip}{3pt plus 1pt minus 1pt}")
            inject_lines.append("\\setlength{\\abovedisplayshortskip}{1pt}")
            inject_lines.append("\\setlength{\\belowdisplayshortskip}{1pt}")
        else:
            # ACM, generic: Tighten spacing around figures and equations
            inject_lines.append("\\setlength{\\textfloatsep}{8pt plus 2pt minus 2pt}")
            inject_lines.append("\\setlength{\\intextsep}{8pt plus 2pt minus 2pt}")
            inject_lines.append("\\setlength{\\floatsep}{8pt plus 2pt minus 2pt}")
        
        # Global equation spacing adjustment
        inject_lines.append("\\setlength{\\abovedisplayskip}{4pt}")
        inject_lines.append("\\setlength{\\belowdisplayskip}{4pt}")
        inject_lines.append("\\setlength{\\abovedisplayshortskip}{2pt}")
        inject_lines.append("\\setlength{\\belowdisplayshortskip}{2pt}")

        # Kiểm tra chính xác package longtable đã được load chưa.
        # Lưu ý: KHÔNG dùng `"longtable" not in tex_content` vì body
        # có thể chứa `\begin{longtable}` khiến check bị false negative.
        _has_longtable_pkg = bool(re.search(
            r'\\(?:usepackage|RequirePackage)\s*(?:\[[^\]]*\])?\s*\{[^}]*longtable[^}]*\}',
            tex_content,
        ))
        if not _has_longtable_pkg:
            inject_lines.append("\\usepackage{longtable}")
            
        # Ensure enumitem is loaded for professional list support
        if "enumitem" not in tex_content:
            inject_lines.append("\\usepackage{enumitem}")

        if not inject_lines:
            return tex_content
        inject_block = "\n".join(inject_lines) + "\n"

        pos = doc_match.start()
        return tex_content[:pos] + inject_block + tex_content[pos:]

    def _normalize_literal_newline_tokens(self, tex_content: str) -> str:
        """Convert accidental literal "\\n" tokens into actual newlines.

        Some sources inject "\\n" as plain text (especially around abstract/keywords),
        which LaTeX interprets as an undefined command "\\n".
        """
        # High-confidence fixes for common IEEE blocks.
        tex_content = tex_content.replace("\\begin{abstract}\\n", "\\begin{abstract}\n")
        tex_content = tex_content.replace("\\n\\end{abstract}", "\n\\end{abstract}")
        tex_content = tex_content.replace("\\begin{IEEEkeywords}\\n", "\\begin{IEEEkeywords}\n")
        tex_content = tex_content.replace("\\n\\end{IEEEkeywords}", "\n\\end{IEEEkeywords}")

        # Generic cleanup: treat standalone "\\n" tokens near sentence/command boundaries as line breaks.
        tex_content = re.sub(
            r'(?:(?<=^)|(?<=[\s\}\]\)\.,;:]))\\n(?=[A-Z\\])',
            '\n',
            tex_content,
        )
        tex_content = re.sub(r'\\n(?=\\end\{)', '\n', tex_content)
        return tex_content


    def _generate_author_block(self, authors: list, doc_class: str) -> str:
        """Generate author block LaTeX code appropriate for the detected document class."""
        if not authors:
            if doc_class == "springer":
                # Ngăn default của class LLNCS: "No Author Given" / "No Institute Given".
                return "\\author{}\n\\institute{}"
            return ""
            
        strategies = {
            "ieee": IEEEAuthorStrategy(),
            "springer": SpringerAuthorStrategy(),
            "elsevier": ElsevierAuthorStrategy(),
            "acm": ACMAuthorStrategy(),
            "mdpi": MDPIAuthorStrategy(),
            "oscm": OSCMAuthorStrategy(),
            "jov": JOVAuthorStrategy(),
        }
        
        strategy = strategies.get(doc_class, GenericAuthorStrategy())
        return strategy.generate(authors)

    def _generate_thebibliography(self, references: list, doc_class: str = "generic", last_sec_num: int = 5) -> str:
        """Generate \\begin{thebibliography} block with numbered \\bibitem entries."""
        if not references:
            return ""
        items = []
        for i, ref in enumerate(references):
            text = ref.get("text", "")
            if not text:
                continue
            # Xóa số đầu dòng kiểu "[1]" hoặc "1. "
            text = re.sub(r'^\[?\d+\]?\s*\.?\s*', '', text).strip()
            if text:
                if doc_class == "jov":
                    # jovcite/apacite yêu cầu \bibitem có đối số tùy chọn
                    items.append(f"\\bibitem[{{\\relax }}]{{ref{i+1}}} {text}")
                else:
                    items.append(f"\\bibitem{{ref{i+1}}} {text}")
        if not items:
            return ""
        width_label = str(len(items))
        label_str = f"\\label{{sec_{last_sec_num + 1}}}"
        return label_str + "\n\\begin{thebibliography}{" + width_label + "}\n" + "\n".join(items) + "\n\\end{thebibliography}"

    def _generate_bib_file(self, references: list, output_path: str) -> str:
        """Generates a semantic references.bib file alongside the TeX output if references exist."""
        if not references:
            return ""
            
        bib_path = os.path.join(os.path.dirname(os.path.abspath(output_path)), "references.bib")
        with open(bib_path, "w", encoding="utf-8") as f:
            for i, ref in enumerate(references):
                # refs là các paragraph node thông thường
                text = ref.get("text", "")
                if not text:
                    continue
                # Xóa số đầu dòng kiểu "[1]" hoặc "1. " khỏi mục tài liệu tham khảo
                text = re.sub(r'^\[?\d+\]?\s*\.?\s*', '', text).strip()
                
                # Parse deep BibTeX metadata
                entry = self._parse_deep_bib_entry(text, i + 1)
                
                # Write entry to the BibTeX file
                f.write(self._serialize_bib_entry(entry) + "\n")
                
        return bib_path

    def _render_algorithm(self, node: dict) -> str:
        """Render algorithm node to LaTeX algorithm/algorithmic environment."""
        caption = node.get("caption", "Algorithm")
        # Clean up "Algorithm 1:" or "\textbf{Algorithm 1:}" from caption iteratively
        old_caption = None
        while caption != old_caption:
            old_caption = caption
            caption = re.sub(r'^(?:\\textbf\{|\\textit\{)?\s*(?:Algorithm|Thuật toán)[\s:]*\d*[\s:.\-]*\}?\s*', '', caption, flags=re.IGNORECASE).strip()
        
        steps = node.get("steps", [])
        
        out = []
        out.append("\\begin{algorithm}")
        out.append(f"\\caption{{{caption}}}")
        out.append("\\begin{algorithmic}[1]")
        
        raw_steps = [s.get("text", "").strip() for s in steps if s.get("text", "").strip()]
        
        # Merge split lines (common in Word parsing)
        merged_txt_steps = []
        for txt in raw_steps:
            # If line starts with assignment arrow or is very short and follows a variable name
            if (txt.startswith("<-") or txt.startswith("leftarrow") or txt.startswith("=")) and merged_txt_steps:
                merged_txt_steps[-1] += " " + txt
            else:
                merged_txt_steps.append(txt)

        open_blocks = []

        for line_text in merged_txt_steps:
            # Remove leading line numbers if present
            line_text = re.sub(r'^\d+[:.]\s*', '', line_text)
            
            # Map common symbols to LaTeX math safely
            line_text = line_text.replace("\\\\leftxarrow", "leftxarrow") # protect from double mapping if any
            line_text = line_text.replace("\\\\leftarrow", "leftxarrow")
            line_text = line_text.replace("\\leftarrow", "leftxarrow")
            line_text = line_text.replace("<-", "leftxarrow")
            line_text = line_text.replace("leftxarrow", r"\ensuremath{\leftarrow}")
            line_text = line_text.replace('$ $', ' ').replace('  ', ' ')
            line_text = line_text.replace('$$', '$')
            
            # Match leading indentation formatting like \quad, \qquad, spaces, tildes
            leading_indent_match = re.match(r'^((?:\\quad|\\qquad|\s|~|\\ )*)(.*)$', line_text, re.IGNORECASE)
            if leading_indent_match:
                indent, clean_line = leading_indent_match.groups()
            else:
                indent, clean_line = "", line_text
                
            clean_line = clean_line.strip()
            l_text = clean_line.lower()
            
            if not clean_line:
                continue
                
            # Check if it is a raw algorithmic LaTeX command
            latex_cmd_match = re.match(
                r'^\\(STATE|IF|ELSIF|ELSE|ENDIF|FOR|ENDFOR|WHILE|ENDWHILE|REQUIRE|ENSURE|RETURN|PRINT)\b',
                clean_line,
                re.IGNORECASE
            )
            
            if latex_cmd_match:
                cmd = latex_cmd_match.group(1).upper()
                if cmd == "IF":
                    open_blocks.append("IF")
                elif cmd == "FOR":
                    open_blocks.append("FOR")
                elif cmd == "WHILE":
                    open_blocks.append("WHILE")
                elif cmd == "ENDIF" and open_blocks and open_blocks[-1] == "IF":
                    open_blocks.pop()
                elif cmd == "ENDFOR" and open_blocks and open_blocks[-1] == "FOR":
                    open_blocks.pop()
                elif cmd == "ENDWHILE" and open_blocks and open_blocks[-1] == "WHILE":
                    open_blocks.pop()
                
                # Output raw LaTeX command directly
                out.append(f"  {clean_line}")
                continue
                
            # Map keywords to algorithmic commands
            if l_text.startswith("if "):
                cond = clean_line[3:].strip()
                if cond.lower().endswith(" then"):
                    cond = cond[:-5].strip()
                out.append(f"  \\IF{{{cond}}}")
                open_blocks.append("IF")
            elif l_text.startswith("else if "):
                cond = clean_line[8:].strip()
                if cond.lower().endswith(" then"):
                    cond = cond[:-5].strip()
                out.append(f"  \\ELSIF{{{cond}}}")
            elif l_text == "else":
                out.append("  \\ELSE")
            elif l_text in ("end if", "endif", "end_if"):
                if open_blocks and open_blocks[-1] == "IF":
                    open_blocks.pop()
                out.append("  \\ENDIF")
            elif l_text.startswith("for "):
                cond = clean_line[4:].strip()
                if cond.lower().endswith(" do"):
                    cond = cond[:-3].strip()
                out.append(f"  \\FOR{{{cond}}}")
                open_blocks.append("FOR")
            elif l_text in ("end for", "endfor", "end_for"):
                if open_blocks and open_blocks[-1] == "FOR":
                    open_blocks.pop()
                out.append("  \\ENDFOR")
            elif l_text.startswith("while "):
                cond = clean_line[6:].strip()
                if cond.lower().endswith(" do"):
                    cond = cond[:-3].strip()
                out.append(f"  \\WHILE{{{cond}}}")
                open_blocks.append("WHILE")
            elif l_text in ("end while", "endwhile", "end_while"):
                if open_blocks and open_blocks[-1] == "WHILE":
                    open_blocks.pop()
                out.append("  \\ENDWHILE")
            elif l_text.startswith("return "):
                out.append(f"  \\RETURN {clean_line[7:].strip()}")
            elif re.match(r'^end\b\.?', l_text):
                # Generic "end" closes the most recent block
                if open_blocks:
                    last_block = open_blocks.pop()
                    if last_block == "IF":
                        out.append("  \\ENDIF")
                    elif last_block == "FOR":
                        out.append("  \\ENDFOR")
                    elif last_block == "WHILE":
                        out.append("  \\ENDWHILE")
                    else:
                        out.append(f"  \\STATE {indent}{clean_line}")
                else:
                    out.append(f"  \\STATE {indent}{clean_line}")
            else:
                out.append(f"  \\STATE {indent}{clean_line}")
                
        # Automatically close any remaining open blocks to guarantee successful TeX compilation
        while open_blocks:
            last_block = open_blocks.pop()
            if last_block == "IF":
                out.append("  \\ENDIF")
            elif last_block == "FOR":
                out.append("  \\ENDFOR")
            elif last_block == "WHILE":
                out.append("  \\ENDWHILE")
                
        out.append("\\end{algorithmic}")
        out.append("\\end{algorithm}")
        return "\n".join(out)

    def _render_list_block(self, node: dict) -> str:
        """Render a list block containing nested lists of enumerate and itemize."""
        items = node.get("items", [])
        if not items:
            return ""
            
        out = []
        stack = []  # Stack stores tuples of (list_type, list_level)
        
        for item in items:
            text = item.get("text", "").strip()
            if not text:
                continue
                
            level = item.get("list_level", 0)
            l_type = item.get("list_type", "itemize")
            
            # 1. Close deeper lists if we are returning to a shallower level
            while stack and stack[-1][1] > level:
                closed_type, _ = stack.pop()
                out.append(f"\\end{{{closed_type}}}")
                
            # 2. Open nested list if we are going to a deeper level (or starting the list)
            if not stack or stack[-1][1] < level:
                stack.append((l_type, level))
                out.append(f"\\begin{{{l_type}}}")
            # 3. If levels are same but list types changed
            elif stack and stack[-1][1] == level and stack[-1][0] != l_type:
                closed_type, _ = stack.pop()
                out.append(f"\\end{{{closed_type}}}")
                stack.append((l_type, level))
                out.append(f"\\begin{{{l_type}}}")
                
            # Render item text and apply cross-referencing inside lists too!
            text = self._apply_cross_referencing(text)
            out.append(f"  \\item {text}")
            
        # Close all remaining open lists
        while stack:
            closed_type, _ = stack.pop()
            out.append(f"\\end{{{closed_type}}}")
            
        return "\n".join(out) + "\n\n"

    def _apply_cross_referencing(self, text: str) -> str:
        """Automatically convert static Figure, Table, Equation, Section text into LaTeX references."""
        # 1. Figure references: e.g. "Figure 1", "Fig. 2", "Hình 3" -> Figure~\ref{fig:img_X}
        text = re.sub(r'\b(?:Figure|Fig\.|Hình)\s+(\d+)\b', r'Figure~\\ref{fig:img_\1}', text, flags=re.IGNORECASE)
        
        # 2. Table references: e.g. "Table I", "Table 1", "Bảng 2" -> Table~\ref{tabX}
        def table_repl(match):
            val = match.group(1)
            roman_map = {"i": "1", "ii": "2", "iii": "3", "iv": "4", "v": "5", "vi": "6", "vii": "7", "viii": "8", "ix": "9", "x": "10"}
            val_clean = roman_map.get(val.lower(), val)
            return f"Table~\\ref{{tab{val_clean}}}"
            
        text = re.sub(r'\b(?:Table|Bảng)\s+([0-9a-zA-Z]+)\b', table_repl, text, flags=re.IGNORECASE)
        
        # 3. Equation references: e.g. "Equation (3)", "Eq. (4)", "Công thức (5)" -> Equation~\eqref{eq:eq_X}
        text = re.sub(r'\b(?:Equation|Eq\.|Công thức)\s*\((\d+)\)\b', r'Equation~\\eqref{eq:eq_\1}', text, flags=re.IGNORECASE)
        
        # 4. Section references: e.g. "Section III", "Section 4", "Mục V"
        def section_repl(match):
            val = match.group(1)
            roman_map = {"i": "1", "ii": "2", "iii": "3", "iv": "4", "v": "5", "vi": "6", "vii": "7", "viii": "8", "ix": "9", "x": "10"}
            val_clean = roman_map.get(val.lower(), val)
            return f"Section~\\ref{{sec_{val_clean}}}"
            
        text = re.sub(r'\b(?:Section|Mục)\s+([IVXivx\d]+)\b', section_repl, text, flags=re.IGNORECASE)
        
        return text

    def _parse_deep_bib_entry(self, text: str, index: int) -> dict:
        """Extract semantic bibtex fields from a raw reference string using context-aware regexes."""
        entry = {
            "key": f"ref{index}",
            "type": "misc",
            "author": "",
            "title": "",
            "year": "",
            "journal": "",
            "booktitle": "",
            "volume": "",
            "number": "",
            "pages": "",
            "doi": "",
            "url": "",
            "publisher": "",
            "school": "",
            "institution": "",
            "note": text
        }
        
        # 1. Clean the text
        text_clean = text.strip()
        
        # 2. Extract DOI and URL
        doi_match = re.search(r'(?:https?://doi\.org/|doi:)\s*([^\s,;}]+)', text_clean, re.IGNORECASE)
        if doi_match:
            entry["doi"] = doi_match.group(1).strip(",. ")
            
        url_match = re.search(r'\\url\{([^}]+)\}|(https?://[^\s,;}]+)', text_clean)
        if url_match:
            url_val = url_match.group(1) or url_match.group(2)
            entry["url"] = url_val.strip(",. ")
            
        # 3. Extract Year
        year_match = re.search(r'\b(19\d{2}|20\d{2})\b', text_clean)
        if year_match:
            entry["year"] = year_match.group(1)
            
        # 4. Try to parse into standard components (Authors. Year. Title. Journal/Booktitle...)
        parts = [p.strip() for p in re.split(r'\.\s+', text_clean) if p.strip()]
        
        if len(parts) >= 3:
            # First part is highly likely to be Authors
            entry["author"] = parts[0]
            
            # Second part might contain Year or be the Title
            second_part = parts[1]
            if re.search(r'\b(19\d{2}|20\d{2})\b', second_part):
                # If year is in second part (like "2004"), then third part is Title
                entry["title"] = parts[2].strip('"\'` ')
                remaining = ". ".join(parts[3:])
            else:
                # Otherwise, second part is Title
                entry["title"] = second_part.strip('"\'` ')
                remaining = ". ".join(parts[2:])
                
            # Classify based on remaining keywords
            if remaining:
                remaining_clean = re.sub(r'\\url\{[^}]+\}|https?://[^\s]+|doi:[^\s]+', '', remaining).strip()
                remaining_clean = re.sub(r'\b(19\d{2}|20\d{2})\b', '', remaining_clean).strip(" ,.()")
                
                # Check for PhD thesis or Technical report
                if "PhD Thesis" in remaining_clean or "PhD Dissertation" in remaining_clean or "Thesis" in remaining_clean:
                    entry["type"] = "phdthesis"
                    entry["school"] = remaining_clean
                elif "Technical Report" in remaining_clean or "Tech. Rep." in remaining_clean:
                    entry["type"] = "techreport"
                    entry["institution"] = remaining_clean
                elif "Proceedings of" in remaining_clean or "Conference" in remaining_clean or "Workshop" in remaining_clean:
                    entry["type"] = "inproceedings"
                    entry["booktitle"] = remaining_clean
                elif any(kw in remaining_clean.lower() for kw in ("commun. acm", "journal", "trans.", "tcs", "j. acm", "ieee access", "sensors")):
                    entry["type"] = "article"
                    entry["journal"] = remaining_clean
                elif "book" in remaining_clean.lower() or "press" in remaining_clean.lower() or "publisher" in remaining_clean.lower() or "verlag" in remaining_clean.lower():
                    entry["type"] = "book"
                    entry["publisher"] = remaining_clean
                else:
                    entry["journal"] = remaining_clean
                    
        return entry

    def _serialize_bib_entry(self, entry: dict) -> str:
        """Serialize entry dict to BibTeX format."""
        out = []
        out.append("@" + entry['type'] + "{" + entry['key'] + ",")
        
        # Write fields if present
        for field in ("author", "title", "year", "journal", "booktitle", "volume", "number", "pages", "doi", "url", "publisher", "school", "institution"):
            if entry.get(field):
                val = entry[field].replace("{", "").replace("}", "") # clean braces
                out.append("  " + field + " = {" + val + "},")
                
        # Always write note with raw text for safety
        note_clean = entry['note'].replace("{", "").replace("}", "")
        out.append("  note = {" + note_clean + "}")
        out.append("}\n")
        return "\n".join(out)
