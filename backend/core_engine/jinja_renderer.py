import jinja2
import os
import re
from .utils import loc_ky_tu

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
                
                for r_idx, row_cells in enumerate(rows_data):
                    tex_cells = []
                    c_idx = 0
                    
                    while c_idx < len(row_cells):
                        cell = row_cells[c_idx]
                        c_type = cell.get("type", "empty")
                        
                        if c_type == "empty":
                            tex_cells.append("")
                            c_idx += 1
                            continue
                            
                        # It's a real cell
                        text = cell.get("text") or ""
                        # AST parser already handled escaping and LaTeX macros
                        
                        colspan = cell.get("colspan", 1)
                        rowspan = cell.get("rowspan", 1)
                        
                        token = text
                        if rowspan > 1:
                            token = f"\\multirow{{{rowspan}}}{{*}}{{{token}}}"
                        if colspan > 1:
                            mc_width = colspan * width_frac
                            token = f"\\multicolumn{{{colspan}}}{{p{{{mc_width:.3f}\\linewidth}}}}{{{token}}}"
                            
                        tex_cells.append(token)
                        
                        # Pad empty spots if colspan > 1 so zip/join aligns correctly
                        for _ in range(colspan - 1):
                            tex_cells.append("")
                            c_idx += 1
                            
                        c_idx += 1
                    
                    # Filter out empty cells that are masked by previous multicolumns
                    dong_filtered = []
                    skip = 0
                    for cell_str in tex_cells:
                        if skip > 0:
                            skip -= 1
                            continue
                        dong_filtered.append(cell_str)
                        if "\\multicolumn{" in cell_str:
                            import re
                            mc_match = re.search(r'\\multicolumn\{(\d+)\}', cell_str)
                            if mc_match:
                                skip = int(mc_match.group(1)) - 1
                                
                    # Pad missing columns just in case
                    while len(dong_filtered) < cols:
                        dong_filtered.append("")
                        
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
        
        doc_class = self._detect_doc_class(template_src)
        
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
                    "$pdflatex = 'xelatex -interaction=nonstopmode -synctex=1 %O %S';\n"
                )

    @staticmethod
    def _detect_doc_class(template_src: str) -> str:
        """Detect document class from template source. Returns normalized class name."""
        m = re.search(r'\\documentclass(?:\[.*?\])?\{([^}]+)\}', template_src)
        if not m:
            return "generic"
        # Extract basename from path-based class names (e.g. "Definitions/mdpi" -> "mdpi")
        cls = m.group(1).rsplit('/', 1)[-1].lower()
        if cls in ('ieeetran',):
            return "ieee"
        elif cls in ('llncs', 'svjour3', 'svmono', 'svmult'):
            return "springer"
        elif cls in ('elsarticle', 'cas-sc', 'cas-dc'):
            return "elsevier"
        elif cls in ('acmart',):
            return "acm"
        elif cls in ('mdpi',):
            return "mdpi"
        else:
            # Generic fallback — works for article, report, book, memoir,
            # revtex4, amsart, thesis, or any unknown class
            return "generic"

    def _generate_author_block(self, authors: list, doc_class: str) -> str:
        """Generate author block LaTeX code appropriate for the detected document class."""
        if not authors:
            return ""
        if doc_class == "ieee":
            return self._generate_ieee_author_block(authors)
        elif doc_class == "springer":
            return self._generate_springer_author_block(authors)
        elif doc_class == "elsevier":
            return self._generate_elsevier_author_block(authors)
        elif doc_class == "acm":
            return self._generate_acm_author_block(authors)
        elif doc_class == "mdpi":
            return self._generate_mdpi_author_block(authors)
        else:
            return self._generate_generic_author_block(authors)

    @staticmethod
    def _generate_ieee_author_block(authors: list) -> str:
        """Generate author block in IEEEtran format."""
        block = "\\author{\n"
        parts = []
        for author in authors:
            auth_str = f"\\IEEEauthorblockN{{{author['name']}}}"
            if author.get('affiliations'):
                affil_lines = []
                for aff in author['affiliations']:
                    sub_lines = [s.strip() for s in aff.split('\n') if s.strip()]
                    for sl in sub_lines:
                        if '@' in sl:
                            affil_lines.append(sl)
                        else:
                            affil_lines.append(f"\\textit{{{sl}}}")
                affil_text = " \\\\ ".join(affil_lines)
                auth_str += f"\n\\IEEEauthorblockA{{{affil_text}}}"
            parts.append(auth_str)
        block += " \\and\n".join(parts)
        block += "\n}"
        return block

    @staticmethod
    def _generate_springer_author_block(authors: list) -> str:
        """Generate author block in Springer LNCS format (\\author + \\institute)."""
        # Collect unique affiliations across all authors
        affil_map = {}  # affiliation text -> institute number
        for author in authors:
            for aff in author.get('affiliations', []):
                clean = aff.strip()
                if clean and clean not in affil_map:
                    affil_map[clean] = len(affil_map) + 1

        # Build \author{...} block
        author_parts = []
        for author in authors:
            name = author['name']
            insts = []
            for aff in author.get('affiliations', []):
                clean = aff.strip()
                if clean in affil_map:
                    insts.append(str(affil_map[clean]))
            if insts:
                name += f"\\inst{{{','.join(insts)}}}"
            author_parts.append(name)

        author_block = "\\author{" + " \\and ".join(author_parts) + "}"

        # Build \institute{...} block
        if affil_map:
            inst_parts = []
            for aff_text in affil_map:
                # Separate email from affiliation text
                lines = [s.strip() for s in aff_text.split('\n') if s.strip()]
                main_parts = []
                email_parts = []
                for line in lines:
                    if '@' in line:
                        email_parts.append(line)
                    else:
                        main_parts.append(line)
                entry = ", ".join(main_parts) if main_parts else aff_text
                if email_parts:
                    entry += f"\\\\\n\\email{{{', '.join(email_parts)}}}"
                inst_parts.append(entry)
            author_block += "\n\\institute{" + " \\and ".join(inst_parts) + "}"
        else:
            # FIX 5: Graceful fallback when no affiliations were parsed (avoids "No Institute Given")
            author_block += "\n\\institute{Institution not specified}"

        return author_block

    @staticmethod
    def _generate_elsevier_author_block(authors: list) -> str:
        """Generate author block in Elsevier format (\\author + \\affiliation).

        Uses the key-value affiliation syntax required by elsarticle.cls:
        ``\\affiliation{organization={...}, city={...}, country={...}}``.
        """
        parts = []
        for author in authors:
            parts.append(f"\\author{{{author['name']}}}")
            for aff in author.get('affiliations', []):
                aff_clean = aff.strip()
                lines = [s.strip() for s in aff_clean.split('\n') if s.strip()]
                email_line = None
                plain_lines = []
                for line in lines:
                    if '@' in line:
                        email_line = line
                    else:
                        plain_lines.append(line)
                org = plain_lines[0] if plain_lines else aff_clean
                city = plain_lines[1] if len(plain_lines) > 1 else ''
                country = plain_lines[2] if len(plain_lines) > 2 else ''
                kv_parts = [f"organization={{{org}}}"]
                if city:
                    kv_parts.append(f"city={{{city}}}")
                if country:
                    kv_parts.append(f"country={{{country}}}")
                parts.append("\\affiliation{" + ",\n            ".join(kv_parts) + "}")
                if email_line:
                    parts.append(f"\\ead{{{email_line}}}")
        return "\n".join(parts)

    @staticmethod
    def _generate_acm_author_block(authors: list) -> str:
        """Generate author block in ACM format.

        ACM strictly requires \\institution{}, \\city{}, and \\country{} inside
        each \\affiliation{} block.
        """
        parts = []
        for author in authors:
            parts.append(f"\\author{{{author['name']}}}")
            affs = author.get('affiliations', [])
            if affs:
                for aff in affs:
                    aff_clean = aff.strip()
                    # Separate email from affiliation text
                    lines = [s.strip() for s in aff_clean.split('\n') if s.strip()]
                    email_line = None
                    plain_lines = []
                    for line in lines:
                        if '@' in line:
                            email_line = line
                        else:
                            plain_lines.append(line)

                    # Respect explicit ACM fields if they already exist in input.
                    institution_match = re.search(r'\\institution\{([^}]*)\}', aff_clean)
                    city_match = re.search(r'\\city\{([^}]*)\}', aff_clean)
                    country_match = re.search(r'\\country\{([^}]*)\}', aff_clean)

                    institution = (
                        institution_match.group(1).strip()
                        if institution_match and institution_match.group(1).strip()
                        else (plain_lines[0] if plain_lines else 'University')
                    )
                    city = (
                        city_match.group(1).strip()
                        if city_match and city_match.group(1).strip()
                        else (plain_lines[1] if len(plain_lines) > 1 else 'Your City')
                    )
                    country = (
                        country_match.group(1).strip()
                        if country_match and country_match.group(1).strip()
                        else 'Vietnam'
                    )

                    aff_block = (
                        "\\affiliation{%\n"
                        f"  \\institution{{{institution}}}\n"
                        f"  \\city{{{city}}}\n"
                        f"  \\country{{{country}}}\n"
                        "}"
                    )
                    parts.append(aff_block)
                    if email_line:
                        parts.append(f"\\email{{{email_line}}}")
            else:
                parts.append(
                    "\\affiliation{%\n"
                    "  \\institution{University}\n"
                    "  \\city{Your City}\n"
                    "  \\country{Vietnam}\n"
                    "}"
                )
        return "\n".join(parts)

    @staticmethod
    def _generate_mdpi_author_block(authors: list) -> str:
        r"""Generate author block in MDPI format (\Author + \address).

        MDPI strictly requires:
          \Author{Name1 $^{1}$, Name2 $^{2}$}
          \address{$^{1}$ \quad Affil 1; email1 \\
          $^{2}$ \quad Affil 2; email2}
        """
        # Collect unique affiliations and per-affiliation emails
        affil_map = {}    # affiliation text (no email) -> number
        affil_emails = {}  # affiliation text (no email) -> email string
        for author in authors:
            for aff in author.get('affiliations', []):
                lines = [s.strip() for s in aff.strip().split('\n') if s.strip()]
                email_parts = []
                inst_parts = []
                for line in lines:
                    if '@' in line:
                        email_parts.append(line)
                    else:
                        inst_parts.append(line)
                key = ', '.join(inst_parts) if inst_parts else aff.strip()
                if key and key not in affil_map:
                    affil_map[key] = len(affil_map) + 1
                    if email_parts:
                        affil_emails[key] = '; '.join(email_parts)

        # Build \Author{...}
        author_parts = []
        for author in authors:
            name = author['name']
            insts = []
            for aff in author.get('affiliations', []):
                lines = [s.strip() for s in aff.strip().split('\n') if s.strip()]
                inst_parts = [l for l in lines if '@' not in l]
                key = ', '.join(inst_parts) if inst_parts else aff.strip()
                if key in affil_map:
                    insts.append(str(affil_map[key]))
            if insts:
                name += " $^{" + ",".join(insts) + "}$"
            author_parts.append(name)
        block = "\\Author{" + ", ".join(author_parts) + "}"

        # Build \AuthorNames{...} (plain names without affiliations)
        plain_names = [a['name'] for a in authors]
        block += "\n\\AuthorNames{" + ", ".join(plain_names) + "}"

        # Build \address{...} with emails appended per affiliation
        # MDPI cls ALWAYS reads \@address at \begin{document}; must emit \address{} to avoid undefined
        if affil_map:
            addr_parts = []
            for aff_text, num in affil_map.items():
                entry = f"$^{{{num}}}$ \\quad {aff_text}"
                email = affil_emails.get(aff_text)
                if email:
                    entry += f"; {email}"
                addr_parts.append(entry)
            block += "\n\\address{" + " \\\\\n".join(addr_parts) + "}"
        else:
            block += "\n\\address{~}"

        return block

    @staticmethod
    def _generate_generic_author_block(authors: list) -> str:
        """Generate a generic \\author{} block with simple ,  separation.
        Uses only standard LaTeX commands (\\author, , , \\thanks) that work
        with article, report, book, memoir, and virtually any document class."""
        # Collect unique affiliations for \thanks footnotes
        affils = []
        for a in authors:
            for aff in a.get('affiliations', []):
                if aff.strip() and aff.strip() not in affils:
                    affils.append(aff.strip())
        affil_note = ""
        if affils:
            affil_note = "\\thanks{" + "; ".join(affils) + "}"
        # Build \author{Name1 ,  Name2 \thanks{...}}
        names = [a['name'] for a in authors]
        block = "\\author{" + ", ".join(names)
        if affil_note:
            block += " " + affil_note
        block += "}"
        return block

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
