import jinja2
import os
import re
from .utils import loc_ky_tu, detect_doc_class
from .author_strategies import (
    IEEEAuthorStrategy,
    SpringerAuthorStrategy,
    ElsevierAuthorStrategy,
    ACMAuthorStrategy,
    MDPIAuthorStrategy,
    OSCMAuthorStrategy,
    GenericAuthorStrategy,
)

class JinjaLaTeXRenderer:
    """
    Takes an Intermediate Representation (IR) JSON and a Jinja-compatible LaTeX template,
    and renders the final .tex file using the jinja2 engine.
    """
    def __init__(self, template_dir: str):
        # We must change Jinja2's default delimiters because LaTeX relies heavily on { }
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
            autoescape=False # LaTeX needs raw strings, we escape via custom LocKyTu during AST parse
        )

        self.env.filters['tex_escape'] = self.escape_latex

    def escape_latex(self, text: str) -> str:
        """Escape special LaTeX characters if needed. (Fallback if AST didn't do it)"""
        # LocKyTu inside AST parser handles most escapes.
        return str(text)

    def render_body_nodes(self, body_nodes: list) -> str:
        """Helper to render common semantic body nodes into standard LaTeX."""
        out = []
        table_counter = 0
        for node in body_nodes:
            t = node.get("type", "")
            if t == "section":
                lvl = node.get("level", 1)
                text = node.get("text", "")
                if lvl == 1: out.append(f"\\section{{{text}}}\n")
                elif lvl == 2: out.append(f"\\subsection{{{text}}}\n")
                else: out.append(f"\\subsubsection{{{text}}}\n")
            elif t == "paragraph":
                out.append(f"{node.get('text', '')}\n\n")
            elif t == "table":
                table_counter += 1
                cols = node.get("cols", 1)
                rows_data = node.get("data", [])
                
                # Setup proportional column width
                width_frac = 0.98 / cols if cols > 0 else 0.15
                col_def = "|" + "|".join([f"p{{{width_frac:.3f}\\linewidth}}" for _ in range(cols)]) + "|"
                
                # IEEE standard: caption ABOVE table
                table_caption = node.get("caption", "Table")
                out.append("\\begin{table}[htbp]\n\\centering\n")
                out.append(f"\\caption{{{table_caption}}}\\label{{tab{table_counter}}}\n")
                out.append("\\resizebox{\\columnwidth}{!}{%\n")
                out.append(f"\\begin{{tabular}}{{{col_def}}}\n\\hline\n")
                
                # Theo dõi các ô bị chiếm bởi rowspan từ các hàng phía trên
                occupied_cells = {} # (row_idx, col_idx) -> True
                
                for r_idx, row in enumerate(rows_data):
                    tex_cells = []
                    c_logical = 0   # Chỉ số cột thực tế trong LaTeX
                    cell_ptr = 0    # Con trỏ duyệt qua danh sách ô trong data của IR
                    
                    while c_logical < cols:
                        # Kiểm tra nếu ô này đã bị chiếm bởi rowspan từ phía trên
                        if occupied_cells.get((r_idx, c_logical)):
                            tex_cells.append("")
                            c_logical += 1
                            continue
                        
                        # Nếu còn ô trong dữ liệu của hàng này
                        if cell_ptr < len(row):
                            cell = row[cell_ptr]
                            cell_ptr += 1
                            
                            # Bỏ qua nếu đây là marker 'empty' (vốn đã được xử lý bởi occupied_cells)
                            if cell.get("type") == "empty":
                                tex_cells.append("")
                                c_logical += 1
                                continue
                                
                            colspan = cell.get("colspan", 1)
                            rowspan = cell.get("rowspan", 1)
                            text = cell.get("text") or ""
                            
                            # Đánh dấu các ô bị chiếm trong tương lai (col/row span)
                            for dr in range(rowspan):
                                for dc in range(colspan):
                                    if dr > 0 or dc > 0:
                                        occupied_cells[(r_idx + dr, c_logical + dc)] = True
                                        
                            token = text
                            if rowspan > 1:
                                token = f"\\multirow{{{rowspan}}}{{*}}{{{token}}}"
                            if colspan > 1:
                                mc_width = colspan * width_frac
                                token = f"\\multicolumn{{{colspan}}}{{p{{{mc_width:.3f}\\linewidth}}}}{{{token}}}"
                                
                            tex_cells.append(token)
                            c_logical += colspan
                        else:
                            # Hết dữ liệu ô nhưng chưa đủ số cột
                            tex_cells.append("")
                            c_logical += 1
                    
                    # Lọc để đóng gói thành dòng LaTeX (skip các ô bị multicolumn chiếm trong cùng hàng)
                    dong_filtered = []
                    skip_mc = 0
                    for cell_str in tex_cells:
                        if skip_mc > 0:
                            skip_mc -= 1
                            continue
                        dong_filtered.append(cell_str)
                        if "\\multicolumn{" in cell_str:
                            import re
                            mc_match = re.search(r'\\multicolumn\{(\d+)\}', cell_str)
                            if mc_match:
                                skip_mc = int(mc_match.group(1)) - 1
                    
                    out.append(" & ".join(dong_filtered) + " \\\\\n\\hline\n")
                    
                out.append("\\end{tabular}%\n}\n")
                out.append("\\end{table}\n\n")
        
        # Ensure everything in `out` is strings
        return "".join([str(x) for x in out])

    def render(self, template_name: str, ir_data: dict, output_path: str, **kwargs):
        """
        Renders the IR data using the specified template file.
        The template MUST use custom delimiters (<< >>, <% %>).
        """
        template = self.env.get_template(template_name)
        
        # Pre-render body nodes so templates just drop << body >>
        body_tex = self.render_body_nodes(ir_data.get('body', []))
        
        bib_file = self._generate_bib_file(ir_data.get('references', []), output_path)
        references_block = self._generate_thebibliography(ir_data.get('references', []))
        
        # Detect document class to generate format-appropriate author block
        try:
            template_path = os.path.join(self.env.loader.searchpath[0], template_name)
            with open(template_path, 'r', encoding='utf-8', errors='ignore') as f:
                template_src = f.read()
        except Exception:
            template_src = ""
        
        doc_class = detect_doc_class(template_src)
        
        # Override author_block with format-appropriate version
        metadata = dict(ir_data.get('metadata', {}))
        authors = metadata.get('authors', [])
        if authors:
            metadata['author_block'] = self._generate_author_block(authors, doc_class)
        
        tex_content = template.render(
            metadata=metadata,
            body=body_tex,
            has_bib=bool(bib_file),
            bib_file="references",
            references_block=references_block,
        )

        # Thêm magic comment để trình biên dịch trên Overleaf/TeXworks ưu tiên dùng XeLaTeX
        magic_comment = "% !TeX program = xelatex\n"

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(magic_comment + tex_content)

        # Tạo latexmkrc để ÉP Overleaf dùng XeLaTeX (Overleaf bỏ qua magic comment)
        # $pdf_mode = 5 yêu cầu latexmk >= 4.51 (TeX Live 2019+, Overleaf đều có)
        # $pdflatex override: fallback cho latexmk cũ hơn
        latexmkrc_path = os.path.join(os.path.dirname(output_path), 'latexmkrc')
        if not os.path.exists(latexmkrc_path):
            with open(latexmkrc_path, 'w', encoding='utf-8') as f:
                f.write(
                    "# Force XeLaTeX for full Unicode support (Vietnamese, CJK, etc.)\n"
                    "# Required for Overleaf: default compiler is pdfLaTeX which cannot handle Unicode\n"
                    "$pdf_mode = 5;\n"
                    "# Fallback for older latexmk versions\n"
                    "$pdflatex = 'xelatex -interaction=nonstopmode -halt-on-error -synctex=1 %O %S';\n"
                )


    def _generate_author_block(self, authors: list, doc_class: str) -> str:
        """Generate author block LaTeX code appropriate for the detected document class."""
        if not authors:
            return ""
            
        strategies = {
            "ieee": IEEEAuthorStrategy(),
            "springer": SpringerAuthorStrategy(),
            "elsevier": ElsevierAuthorStrategy(),
            "acm": ACMAuthorStrategy(),
            "mdpi": MDPIAuthorStrategy(),
            "oscm": OSCMAuthorStrategy(),
        }
        
        strategy = strategies.get(doc_class, GenericAuthorStrategy())
        return strategy.generate(authors)

    def _generate_thebibliography(self, references: list) -> str:
        """Generate \\begin{thebibliography} block with numbered \\bibitem entries."""
        if not references:
            return ""
        items = []
        for i, ref in enumerate(references):
            text = ref.get("text", "")
            if not text:
                continue
            # Strip leading numbers like "[1]" or "1. "
            text = re.sub(r'^\[?\d+\]?\s*\.?\s*', '', text).strip()
            if text:
                items.append(f"\\bibitem{{ref{i+1}}} {text}")
        if not items:
            return ""
        width_label = str(len(items))
        return "\\begin{thebibliography}{" + width_label + "}\n" + "\n".join(items) + "\n\\end{thebibliography}"

    def _generate_bib_file(self, references: list, output_path: str) -> str:
        """Generates a references.bib file alongside the TeX output if references exist."""
        if not references:
            return ""
            
        bib_path = os.path.join(os.path.dirname(os.path.abspath(output_path)), "references.bib")
        with open(bib_path, "w", encoding="utf-8") as f:
            for i, ref in enumerate(references):
                # refs are standard paragraph nodes
                text = ref.get("text", "")
                if not text:
                    continue
                # Strip leading numbers like "[1]" or "1. " from bibliography items
                text = re.sub(r'^\[?\d+\]?\s*\.?\s*', '', text).strip()
                
                # Write minimal generic @misc entry since deep parsing citations into Author/Title is out of scope 
                f.write(f"@misc{{ref{i+1},\n")
                f.write(f"  note = {{{text}}}\n")
                f.write("}\n\n")
                
        return bib_path
