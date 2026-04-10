import jinja2
import os
import re
from bisect import bisect_right
from .utils import phat_hien_loai_tai_lieu
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

    def render_body_nodes(self, body_nodes: list, doc_class: str = "generic") -> str:
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
                para_text = str(node.get('text', '') or '')
                para_text = para_text.replace("\\n\\label{", " \\label{")
                # Normalize accidental literal "\\n" tokens before core LaTeX commands.
                para_text = re.sub(
                    r'\\n(\\(?:label|caption|includegraphics|refstepcounter|begin|end)\b)',
                    r'\n\1',
                    para_text,
                )
                # Normalize hard line breaks from DOC/PDF-converted sources to avoid
                # unintended visual line-spacing artifacts in LaTeX output.
                para_text = re.sub(r'[\u200b\u200c\u200d\ufeff\xa0]+', ' ', para_text)
                para_text = re.sub(r'\s*\n+\s*', ' ', para_text)
                para_text = re.sub(r'[ \t]{2,}', ' ', para_text).strip()
                if doc_class == "springer":
                    promoted_eq = self._promote_inline_equation_paragraph(para_text)
                    if promoted_eq:
                        out.append(promoted_eq)
                        continue
                if para_text:
                    out.append(f"{para_text}\n\n")
            elif t == "table":
                table_counter += 1
                cols = node.get("cols", 1)
                rows_data = node.get("data", [])

                # Setup column widths. For common 3-column metadata tables
                # (Feature/Type/Description), make the description column wider
                # to avoid excessive line wrapping and tall rows.
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

                col_def = "|" + "|".join([f"p{{{w:.3f}\\linewidth}}" for w in col_widths]) + "|"
                
                # IEEE standard: caption ABOVE table
                table_caption = node.get("caption", "Table")
                table_width_ratio = node.get("width_ratio")
                if isinstance(table_width_ratio, (int, float)) and table_width_ratio > 0:
                    table_width_expr = f"{min(0.95, max(0.2, float(table_width_ratio))):.3f}\\columnwidth"
                else:
                    table_width_expr = "\\columnwidth"
                is_floating_word_table = bool(node.get("is_floating_word_table"))
                # Keep IEEE tables anchored to preserve Word-like ordering.
                if doc_class == "springer":
                    table_pos = "[htbp]"
                elif is_floating_word_table:
                    # Strongly prefer current insertion point for Word floating tables.
                    table_pos = "[!h]"
                else:
                    table_pos = "[H]"
                out.append(f"\\begin{{table}}{table_pos}\n\\centering\n")
                out.append(f"\\caption{{{table_caption}}}\\label{{tab{table_counter}}}\n")
                out.append("\\begingroup\\small\\setlength{\\tabcolsep}{3pt}\\renewcommand{\\arraystretch}{0.95}\n")
                out.append(f"\\resizebox{{{table_width_expr}}}{{!}}{{%\n")
                out.append(f"\\begin{{tabular}}{{{col_def}}}\n\\hline\n")
                
                # Track active multirow spans: col_index -> remaining rows
                active_multirows = {}  # col_index -> rows_remaining

                for r_idx, row in enumerate(rows_data):
                    tex_cells = []
                    c_logical = 0   # Logical column index in final tabular grid
                    is_header_row = bool(node.get("has_header")) and r_idx == 0
                    row_multirow_starts = {}  # col -> rowspan (new multirows starting this row)

                    # Table parser already resolves merge structure. Rendering should
                    # respect those logical cells directly to avoid double-merge drift.
                    for cell in row:
                        if c_logical >= cols:
                            break

                        if cell.get("type") == "empty":
                            tex_cells.append("")
                            c_logical += 1
                            continue

                        colspan = max(1, int(cell.get("colspan", 1) or 1))
                        rowspan = max(1, int(cell.get("rowspan", 1) or 1))
                        text = cell.get("text") or ""
                        if is_header_row and text.strip() and "\\textbf{" not in text:
                            text = f"\\textbf{{{text}}}"

                        token = text
                        if rowspan > 1:
                            token = f"\\multirow{{{rowspan}}}{{*}}{{{token}}}"
                            # Record multirow starts for this row
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
                    
                    # Lọc để đóng gói thành dòng LaTeX (skip các ô bị multicolumn chiếm trong cùng hàng)
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
                    
                    # Update active multirow tracking
                    # First, decrement existing active multirows
                    new_active = {}
                    for col_idx, remaining in active_multirows.items():
                        if remaining > 1:
                            new_active[col_idx] = remaining - 1
                    # Then add new multirow starts from this row
                    for col_idx, rspan in row_multirow_starts.items():
                        new_active[col_idx] = rspan
                    active_multirows = new_active

                    # Determine horizontal rule: use \cline if any multirow is spanning
                    # into the next row, otherwise use \hline
                    spanning_cols = set()
                    for col_idx, remaining in active_multirows.items():
                        if remaining > 1:  # Still spanning into the next row
                            spanning_cols.add(col_idx)
                    
                    if spanning_cols and r_idx < len(rows_data) - 1:
                        # Build \cline commands for non-spanning column ranges
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
                    
                out.append("\\end{tabular}%\n}\n")
                out.append("\\endgroup\n")
                out.append("\\end{table}\n\n")
        
        # Ensure everything in `out` is strings
        return "".join([str(x) for x in out])

    def render(self, template_name: str, ir_data: dict, output_path: str, **kwargs):
        """
        Renders the IR data using the specified template file.
        The template MUST use custom delimiters (<< >>, <% %>).
        """
        template = self.env.get_template(template_name)
        
        # Detect document class to generate format-appropriate output behavior
        try:
            template_path = os.path.join(self.env.loader.searchpath[0], template_name)
            with open(template_path, 'r', encoding='utf-8', errors='ignore') as f:
                template_src = f.read()
        except Exception:
            template_src = ""
        
        doc_class = phat_hien_loai_tai_lieu(template_src)

        # Pre-render body nodes so templates just drop << body >>
        body_tex = self.render_body_nodes(ir_data.get('body', []), doc_class=doc_class)
        if doc_class == "ieee":
            body_tex = self._normalize_ieee_figure_placement(body_tex)
            body_tex = self._remove_float_barriers(body_tex)
        elif doc_class == "springer":
            body_tex = self._normalize_springer_float_placement(body_tex)

        bib_file = self._generate_bib_file(ir_data.get('references', []), output_path)
        references_block = self._generate_thebibliography(ir_data.get('references', []), doc_class)
        
        # Override author_block with format-appropriate version
        metadata = dict(ir_data.get('metadata', {}))
        authors = metadata.get('authors', [])
        metadata['author_block'] = self._generate_author_block(authors, doc_class)
        
        tex_content = template.render(
            metadata=metadata,
            body=body_tex,
            has_bib=bool(bib_file),
            bib_file="references",
            references_block=references_block,
        )
        tex_content = self._normalize_tex_preamble(tex_content)

        # Prefer pdfLaTeX by default, but switch to XeLaTeX when the rendered
        # content includes packages that require a Unicode engine.
        magic_comment = f"% !TeX program = {self._choose_magic_engine(tex_content)}\n"

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(magic_comment + tex_content)

        # Remove stale latexmkrc that may force XeLaTeX from older output runs.
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
        body_tex = re.sub(r"\\begin\{figure\}\[[^\]]*\]", r"\\begin{figure}[htbp]", body_tex)
        figure_pattern = re.compile(r"\\begin\{figure\}\[htbp\].*?\\end\{figure\}", re.DOTALL)
        section_pattern = re.compile(r"\\section\{")

        chunks = []
        cursor = 0
        for match in figure_pattern.finditer(body_tex):
            start, end = match.span()
            fig_block = match.group(0)

            # Captionless figure blocks are usually formula snapshots or decorative
            # blocks from Word. Keep them inline to avoid float drift.
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
        # Some DOCX conversions carry a literal "\\n" token before \label.
        # Normalize it first so regex extraction stays stable.
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
            + (f"\\n{label_cmd}" if label_cmd else "")
            + "\n\\par\n"
            "\\endgroup\n"
        )

    def _normalize_springer_float_placement(self, body_tex: str) -> str:
        """Normalize Springer float hints and add local barriers near headings.

        Use ``[!ht]`` to avoid float-only pages caused by the ``p`` placement mode,
        then add ``\\FloatBarrier`` only when a section starts shortly after a float.
        """
        body_tex = re.sub(r"\\begin\{figure\}\[[^\]]*\]", r"\\begin{figure}[!ht]", body_tex)
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
        return f"\\begin{{equation}}\n{expr}\n\\tag{{{num}}}\n\\end{{equation}}\n\n"

    def _remove_float_barriers(self, body_tex: str) -> str:
        """Remove legacy FloatBarrier markers that can force awkward page breaks."""
        return re.sub(r"^[ \t]*\\FloatBarrier[ \t]*\n?", "", body_tex, flags=re.MULTILINE)

    def _choose_magic_engine(self, tex_content: str) -> str:
        """Choose a safe TeX engine hint for editors/Overleaf based on content."""
        if re.search(r"\\usepackage\{fontspec\}", tex_content):
            return "xelatex"
        if re.search(r"\\usepackage\{unicode-math\}", tex_content):
            return "xelatex"
        if re.search(r"\\usepackage\{polyglossia\}", tex_content):
            return "xelatex"

        # Respect templates that explicitly pin pdfTeX in documentclass options.
        docclass_opts = re.search(r"\\documentclass\s*\[([^\]]*)\]", tex_content)
        if docclass_opts is not None:
            options = [o.strip().lower() for o in docclass_opts.group(1).split(",")]
            if any(o in ("pdftex", "pdflatex") for o in options):
                return "pdflatex"

        # Fallback for multilingual content: non-ASCII often compiles more safely
        # with XeLaTeX than pdfLaTeX.
        if re.search(r"[^\x00-\x7f]", tex_content):
            return "xelatex"
        return "pdflatex"

    def _normalize_tex_preamble(self, tex_content: str) -> str:
        """Normalize preamble so pdfLaTeX avoids OT1 pitfalls (e.g., \DJ unavailable)."""
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
            inject_lines.append("\\ifPDFTeX")
            inject_lines.append("\\usepackage[T5]{fontenc}")
            inject_lines.append("\\usepackage[utf8]{inputenc}")
            inject_lines.append("\\fi")
        if not has_multirow:
            inject_lines.append("\\usepackage{multirow}")
        if not inject_lines:
            return tex_content
        inject_block = "\n".join(inject_lines) + "\n"

        pos = doc_match.start()
        return tex_content[:pos] + inject_block + tex_content[pos:]


    def _generate_author_block(self, authors: list, doc_class: str) -> str:
        """Generate author block LaTeX code appropriate for the detected document class."""
        if not authors:
            if doc_class == "springer":
                # Prevent LLNCS class defaults: "No Author Given" / "No Institute Given".
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

    def _generate_thebibliography(self, references: list, doc_class: str = "generic") -> str:
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
                if doc_class == "jov":
                    # jovcite/apacite requires \bibitem to have an optional argument
                    items.append(f"\\bibitem[{{\\relax }}]{{ref{i+1}}} {text}")
                else:
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
