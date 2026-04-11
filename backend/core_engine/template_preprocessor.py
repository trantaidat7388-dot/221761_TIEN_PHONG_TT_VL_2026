import re
import json
import os
from .utils import phat_hien_loai_tai_lieu

MANIFEST_PATH = os.path.join(os.path.dirname(__file__), 'publishers_manifest.json')
try:
    with open(MANIFEST_PATH, 'r', encoding='utf-8') as f:
        PUBLISHERS_MANIFEST = json.load(f)
except Exception:
    PUBLISHERS_MANIFEST = {}

class TemplatePreprocessor:
    """
    Universal LaTeX template preprocessor for Jinja2 tagging.
    Supports: IEEE, ACM, Springer (LLNCS), Elsevier, MDPI, and generic templates.
    Injects Jinja2 variables (e.g. << metadata.title >>, << body >>)
    using custom delimiters << >> to avoid { } conflict.
    """

    @classmethod
    def auto_tag(cls, tex_content: str, config: dict = None) -> str:
        # 1. Detect publisher logic
        tex_content = cls._trim_after_first_end_document(tex_content)
        doc_class = phat_hien_loai_tai_lieu(tex_content)
        pub_config = PUBLISHERS_MANIFEST.get(doc_class, {})
        
        # Merge provided config with manifest-based defaults
        config = {**pub_config, **(config or {})}
        
        tex = cls._ensure_essential_packages(tex_content)
        tex = cls._normalize_paragraph_spacing(tex, doc_class)
        tex = cls._normalize_float_numbering(tex, doc_class)
        
        # ── Hỗ trợ Tiếng Việt (fontspec cho XeLaTeX - chỉ fallback nếu chưa có font) ──
        if doc_class != 'ieee' and r'\setmainfont' not in tex and r'\usepackage{fontspec}' not in tex:
            # Strict regex: skip commented-out \documentclass lines (starting with %)
            active_dc_pattern = re.compile(r'^(?!\s*%).*?\\documentclass(\[.*?\])?\{.*?\}', re.MULTILINE)
            lines = tex.split('\n')
            injected = False
            for i, line in enumerate(lines):
                if not injected and active_dc_pattern.match(line):
                    lines.insert(i + 1, r"\usepackage{iftex}")
                    lines.insert(i + 2, r"\ifXeTeX")
                    lines.insert(i + 3, r"  \usepackage{fontspec}")
                    lines.insert(i + 4, r"  % \setmainfont{Times New Roman} % Bỏ comment nếu muốn ép dùng font này")
                    lines.insert(i + 5, r"\fi")
                    injected = True
                    break
            if injected:
                tex = '\n'.join(lines)

        # ── Vá lỗi apacite / jovcite: provide missing commands ──
        # jovcite.sty (2008) dựa trên apacite cũ, thiếu nhiều lệnh mà
        # english.apc v6.03 (TeX Live 2026) gọi \renewcommand.
        # Dùng \providecommand để tránh crash nếu chưa tồn tại,
        # nhưng vô hại nếu đã có.
        _apacite_patch_lines = [
            r"\providecommand{\onemaskedcitationmsg}[1]{}",
            r"\providecommand{\maskedcitationsmsg}[1]{}",
            r"\providecommand{\BRetrievedFrom}{Retrieved from\ }",
            r"\providecommand{\PrintOrdinal}[1]{#1}",
            r"\providecommand{\CardinalNumeric}[1]{\number#1}",
            r"\providecommand{\APACmonth}[1]{\ifcase #1\or January\or February\or March\or April\or May\or June\or July\or August\or September\or October\or November\or December\else {#1}\fi}",
            r"\providecommand{\APACrefYearMonthDay}[3]{{(#1)}}",
        ]
        # Boolean flag that english.apc checks via \if@APAC@natbib@apa
        _apacite_flag_line = r"\makeatletter\@ifundefined{if@APAC@natbib@apa}{\newif\if@APAC@natbib@apa}{}\makeatother"

        if r'\onemaskedcitationmsg' not in tex:
            active_bd_pattern = re.compile(r'^(?!\s*%).*?\\begin\{document\}', re.MULTILINE)
            lines = tex.split('\n')
            patched = False
            for i, line in enumerate(lines):
                if not patched and active_bd_pattern.match(line):
                    # Inject BEFORE \begin{document}
                    all_patches = [_apacite_flag_line] + _apacite_patch_lines
                    for p_line in reversed(all_patches):
                        lines.insert(i, p_line)
                    patched = True
                    break
            if patched:
                tex = '\n'.join(lines)

        # 1. Clean up known publisher metadata (Always run)
        tex = cls._cleanup_publisher_metadata(tex, config)
        
        # 2. BẮT BUỘC dùng pylatexenc cho các node metadata chính để tránh lỗi rớt ngoặc
        try:
            from pylatexenc.latexwalker import LatexWalker, LatexMacroNode, LatexEnvironmentNode, LatexGroupNode
            walker = LatexWalker(tex)
            nodelist, _, _ = walker.get_latex_nodes()

            replace_ops = [] # list of (start, end, replacement_text)

            def traverse(nodes, in_def=False):
                if not nodes: return []
                found = []
                for n in nodes:
                    is_def = in_def
                    if isinstance(n, LatexMacroNode) and n.macroname in ('newcommand', 'renewcommand', 'providecommand', 'def', 'let'):
                        is_def = True
                    n._is_definition = in_def
                    found.append(n)
                    if getattr(n, 'nodelist', None):
                        found.extend(traverse(n.nodelist, is_def))
                    if getattr(n, 'nodeargd', None) and getattr(n.nodeargd, 'argnlist', None):
                        for arg in n.nodeargd.argnlist:
                            if arg:
                                arg._is_definition = is_def
                                found.append(arg)
                                if getattr(arg, 'nodelist', None):
                                    found.extend(traverse(arg.nodelist, is_def))
                return found

            all_nodes = traverse(nodelist)

            # 1. Processing Title
            title_cmd_raw = config.get("title_command", "title").replace("\\", "")
            titles = [n for n in all_nodes if isinstance(n, LatexMacroNode) and n.macroname.lower() == title_cmd_raw.lower() and not getattr(n, '_is_definition', False)]
            for t in titles:
                if getattr(t, 'nodeargd', None) and getattr(t.nodeargd, 'argnlist', None):
                    for arg in reversed(t.nodeargd.argnlist):
                        if arg and isinstance(arg, LatexGroupNode):
                            title_tag = '<< metadata.title >>'
                            title_tag = re.sub(r'\s+', ' ', title_tag).strip()
                            replace_ops.append((arg.pos + 1, arg.pos + arg.len - 1, title_tag))
                            break

            # 2. Author & Affiliations - Universal approach
            author_cmd_raw = config.get("author_command", "author").replace("\\", "")
            # Base related commands
            related_cmds = {author_cmd_raw, 'author', 'Author', 'affil', 'affiliation', 'address', 'email', 'institute'}
            # Add publisher-specific ones from manifest
            related_cmds.update(config.get("author_related_cmds", [
                'authornote', 'authornotemark', 'orcid', 'corres', 'firstnote', 'AuthorNames', 
                'authorrunning', 'titlerunning', 'address', 'institute'
            ]))
            
            author_nodes = [n for n in all_nodes if isinstance(n, LatexMacroNode) and n.macroname in related_cmds and not getattr(n, '_is_definition', False)]
            if author_nodes:
                print(f"[*] pylatexenc found {len(author_nodes)} author nodes. Revamping injection...")
                first_author = author_nodes[0]
                insert_pos = first_author.pos
                author_tag = '<< metadata.author_block >>'
                author_tag = re.sub(r'\s+', ' ', author_tag).strip()
                replace_ops.append((insert_pos, insert_pos, author_tag))
                
                for node in author_nodes:
                    end_pos = node.pos + node.len
                    # pylatexenc quirk: for \author[a,1]{Name}, it often
                    # absorbs the '[' into the node span but leaves
                    # 'a,1]{Name}' as rest. Detect this by checking if the
                    # node span ends with '['.
                    if end_pos > 0 and tex[end_pos - 1] == '[':
                        # Find the matching ']' first
                        closing_bracket = tex.find(']', end_pos)
                        if closing_bracket != -1:
                            end_pos = closing_bracket + 1
                    
                    while end_pos < len(tex):
                        rest = tex[end_pos:]
                        match = re.match(r'^(\s|%.*?\n)*', rest)
                        skip_len = match.end() if match else 0
                        
                        if end_pos + skip_len < len(tex):
                            next_char = tex[end_pos + skip_len]
                            
                            if next_char == '{':
                                next_end = cls._find_matching_brace(tex, end_pos + skip_len)
                                if next_end != -1:
                                    end_pos = next_end + 1
                                    continue
                            elif next_char == '[':
                                closing_bracket = tex.find(']', end_pos + skip_len)
                                if closing_bracket != -1:
                                    end_pos = closing_bracket + 1
                                    continue
                            elif next_char in ('*', ']'):
                                # '*' = star variant; ']' = orphaned closing bracket
                                end_pos = end_pos + skip_len + 1
                                continue
                                
                        break
                    replace_ops.append((node.pos, end_pos, ''))

            # 3. Processing Abstract
            abstract_env_raw = config.get("abstract_env", "abstract").replace("\\", "")
            abstracts_env = [n for n in all_nodes if isinstance(n, LatexEnvironmentNode) and n.environmentname.lower() == abstract_env_raw.lower() and not getattr(n, '_is_definition', False)]
            if abstracts_env:
                ab = abstracts_env[0]
                replace_ops.append((ab.pos, ab.pos + ab.len, f'\\begin{{{ab.environmentname}}}\n<< metadata.abstract >>\n\\end{{{ab.environmentname}}}'))
            else:
                abstracts_cmd = [n for n in all_nodes if isinstance(n, LatexMacroNode) and n.macroname.lower() == abstract_env_raw.lower() and not getattr(n, '_is_definition', False)]
                if abstracts_cmd:
                    ab = abstracts_cmd[0]
                    if getattr(ab, 'nodeargd', None) and getattr(ab.nodeargd, 'argnlist', None):
                        for arg in reversed(ab.nodeargd.argnlist):
                            if arg and isinstance(arg, LatexGroupNode):
                                replace_ops.append((arg.pos + 1, arg.pos + arg.len - 1, '<< metadata.abstract >>'))
                                break

            # 4. Processing Keywords
            kw_envs = [n for n in all_nodes if isinstance(n, LatexEnvironmentNode) and n.environmentname in ['keywords', 'keyword', 'IEEEkeywords', 'IndexTerms'] and not getattr(n, '_is_definition', False)]
            if kw_envs:
                kw = kw_envs[0]
                replace_ops.append((kw.pos, kw.pos + kw.len, f'\\begin{{{kw.environmentname}}}\n<< metadata.keywords_str >>\n\\end{{{kw.environmentname}}}'))
            else:
                kw_cmds = [n for n in all_nodes if isinstance(n, LatexMacroNode) and n.macroname in ['keywords', 'keyword', 'IEEEkeywords', 'IndexTerms'] and not getattr(n, '_is_definition', False)]
                if kw_cmds:
                    kw = kw_cmds[0]
                    if getattr(kw, 'nodeargd', None) and getattr(kw.nodeargd, 'argnlist', None):
                        for arg in reversed(kw.nodeargd.argnlist):
                            if arg and isinstance(arg, LatexGroupNode):
                                replace_ops.append((arg.pos + 1, arg.pos + arg.len - 1, '<< metadata.keywords_str >>'))
                                break

            # Apply replacements from back to front
            # Sort by start descending. For same start, sort by end descending (largest span first).
            replace_ops.sort(key=lambda x: (x[0], x[1]), reverse=True)
            filtered_ops = []
            last_start = float('inf')
            for start, end, text in replace_ops:
                # Same-start operations are allowed if they are non-overlapping with NEXT items (smaller start)
                # But here we just need to ensure we don't skip an insertion at the same start as a deletion.
                # If end <= last_start, it doesn't overlap with previously added (which are later in the file).
                if end <= last_start:
                    filtered_ops.append((start, end, text))
                    last_start = start
                elif start == last_start and end > last_start:
                    # Special case: Deletion starting at same point as a previously added insertion/deletion.
                    # Since we sort by end descending, the LARGER span came first.
                    # So we should skip the smaller ones that are 'inside' it.
                    continue

            res_tex = tex
            for start, end, text in filtered_ops:
                res_tex = res_tex[:start] + text + res_tex[end:]
                
            tex = res_tex

            # Kích hoạt fallback lưu động nếu pylatexenc bỏ sót metadata do macro không chuẩn (vd \Title của MDPI)
            if '<< metadata.title >>' not in tex:
                tex = cls._process_title(tex, config)
            if '<< metadata.author_block >>' not in tex:
                tex = cls._process_authors(tex, config)
            if '<< metadata.abstract >>' not in tex:
                tex = cls._process_abstract(tex, config)
            if '<< metadata.keywords_str >>' not in tex:
                tex = cls._process_keywords(tex, config)

            print("[*] pylatexenc tagging done for metadata.")
        except Exception as e:
            print(f"[WARN] pylatexenc failed ({e}), using safe regex fallback...")
            # Note: _cleanup_publisher_metadata already ran before the try block.
            tex = cls._process_title(tex, config)
            tex = cls._process_authors(tex, config)
            tex = cls._process_abstract(tex, config)
            tex = cls._process_keywords(tex, config)

        # MỤC 4: Logic Body và References vẫn dùng Regex (ổn định hơn cho việc "quét sạch" dummy text)
        tex = cls._process_references(tex)
        tex = cls._process_body(tex)
        
        # MỤC 5: Xóa tùy chọn pdftex gây crash driver xcolor khi dùng xelatex
        def remove_pdftex_option(match):
            opts_str = match.group(1)
            opts = [o.strip() for o in opts_str.split(',')]
            opts = [o for o in opts if o.lower() != 'pdftex']
            return r'\documentclass[' + ','.join(opts) + ']' if opts else r'\documentclass'

        tex = re.sub(r'\\documentclass\s*\[([^\]]*)\]', remove_pdftex_option, tex)

        return tex

    @classmethod
    def _trim_after_first_end_document(cls, tex: str) -> str:
        """Keep a single LaTeX document by dropping accidental trailing content.

        Some uploaded templates are malformed and contain a second full document
        appended after the first ``\\end{document}``. We keep everything through the
        first active ``\\end{document}`` and discard anything that follows.
        """
        end_match = re.search(r'^[ \t]*\\end\{document\}', tex, re.MULTILINE)
        if not end_match:
            return tex
        return tex[:end_match.end()] + "\n"

    @classmethod
    def _normalize_paragraph_spacing(cls, tex: str, doc_class: str) -> str:
        """Keep paragraph spacing compact and line breaks smoother for Springer-like templates."""
        if doc_class != 'springer':
            return tex

        if '\\setlength{\\parskip}' in tex and '\\hyphenpenalty=' in tex:
            return tex

        doc_match = re.search(r'^[ \t]*\\begin\{document\}', tex, re.MULTILINE)
        if not doc_match:
            return tex

        lines = []
        if '\\setlength{\\parskip}' not in tex:
            lines.extend([
                "\\setlength{\\parskip}{0pt}",
                "\\setlength{\\parsep}{0pt}",
            ])
        if '\\hyphenpenalty=' not in tex:
            lines.extend([
                "\\hyphenpenalty=1500",
                "\\exhyphenpenalty=1500",
                "\\tolerance=1800",
                "\\emergencystretch=1.0em",
            ])

        if not lines:
            return tex

        block = "\n".join(lines) + "\n"
        pos = doc_match.start()
        return tex[:pos] + block + tex[pos:]

    # ── Utilities ──────────────────────────────────────────────────

    @classmethod
    def _find_matching_brace(cls, text: str, start_index: int) -> int:
        """Tìm vị trí đóng ngoặc nhọn } khớp với { tại start_index."""
        if start_index >= len(text) or text[start_index] != '{':
            return -1
        count = 0
        for i in range(start_index, len(text)):
            if text[i] == '{' and (i == 0 or text[i-1] != '\\'):
                count += 1
            elif text[i] == '}' and (i == 0 or text[i-1] != '\\'):
                count -= 1
                if count == 0:
                    return i
        return -1

    @classmethod
    def _remove_command(cls, tex: str, cmd_regex: str, *, multi_brace: bool = False) -> str:
        """Remove all occurrences of a LaTeX command with its balanced brace arguments.

        cmd_regex: regex matching the command (e.g. r'\\\\author').
        multi_brace: if True, consume additional {...} groups after the first.
        """
        pattern = cmd_regex + r'\s*(?:\[[^\]]*\])?\s*\{'
        _failsafe = 0
        while True:
            _failsafe += 1
            if _failsafe > 200:
                break
            match = re.search(pattern, tex)
            if not match:
                break
            start = match.start()
            brace_start = match.end() - 1
            brace_end = cls._find_matching_brace(tex, brace_start)
            if brace_end == -1:
                break
            end = brace_end
            if multi_brace:
                while end + 1 < len(tex):
                    rest = tex[end + 1:]
                    match = re.match(r'^(\s|%.*?\n)*', rest)
                    skip_len = match.end() if match else 0
                    if end + 1 + skip_len < len(tex) and tex[end + 1 + skip_len] == '{':
                        next_brace = end + 1 + skip_len
                        next_end = cls._find_matching_brace(tex, next_brace)
                        if next_end == -1:
                            break
                        end = next_end
                    else:
                        break
            # Remove including trailing whitespace + newline
            remove_end = end + 1
            while remove_end < len(tex) and tex[remove_end] in (' ', '\t'):
                remove_end += 1
            if remove_end < len(tex) and tex[remove_end] == '\n':
                remove_end += 1
            tex = tex[:start] + tex[remove_end:]
        return tex

    @classmethod
    def _normalize_float_numbering(cls, tex: str, doc_class: str) -> str:
        """For generic templates, number figures/tables by section (e.g., 3.1)."""
        if doc_class not in ('generic', 'springer'):
            return tex

        already_configured = (
            re.search(r'\\(counterwithin|numberwithin)\s*\{figure\}\s*\{section\}', tex) is not None
            or re.search(r'\\renewcommand\s*\{\\thefigure\}', tex) is not None
            or re.search(r'@addtoreset\s*\{figure\}\s*\{section\}', tex) is not None
        )
        if already_configured:
            return tex

        block = (
            "\\makeatletter\n"
            "\\@addtoreset{figure}{section}\n"
            "\\renewcommand{\\thefigure}{\\thesection.\\arabic{figure}}\n"
            "\\@addtoreset{table}{section}\n"
            "\\renewcommand{\\thetable}{\\thesection.\\arabic{table}}\n"
            "\\makeatother\n"
        )

        doc_match = re.search(r'^[ \t]*\\begin\{document\}', tex, re.MULTILINE)
        if not doc_match:
            return tex

        pos = doc_match.start()
        return tex[:pos] + block + tex[pos:]

    @staticmethod
    def _is_commented(tex: str, pos: int) -> bool:
        """Return True if *pos* falls on a line whose first non-space character is %."""
        line_start = tex.rfind('\n', 0, pos) + 1   # 0 if no newline found
        before = tex[line_start:pos]
        return '%' in before

    # ── Phase 1: Essential packages ───────────────────────────────

    @classmethod
    def _ensure_essential_packages(cls, tex: str) -> str:
        r"""
        Ensure essential packages for LaTeX compilation.

        Strategy:
        1. \PassOptionsToPackage{table,xcdraw}{xcolor} BEFORE \documentclass
           — prevents option clash with cls files (MDPI, ACM) that load xcolor internally.
        2. Detect engine: nếu template dùng pdftex + tikz/pgf → giữ nguyên cho pdflatex.
           Ngược lại → chuẩn bị cho XeLaTeX (xóa pdftex, thay fontenc→fontspec).
        3. Inject @ifpackageloaded guards before \begin{document}.
        """
        # ── Detect if template needs pdflatex (pdftex option + tikz/pgf) ──
        dc_opts_match = re.search(r'\\documentclass\s*\[([^\]]*)\]', tex)
        dc_opts_str = dc_opts_match.group(1) if dc_opts_match else ''
        has_pdftex = any(o.strip().lower() in ('pdftex', 'pdflatex') for o in dc_opts_str.split(','))
        # Detect tikz/pgf in template body or cls path (MDPI etc.)
        has_pgf = bool(re.search(r'tikz|pgf|mdpi', tex[:3000], re.IGNORECASE))
        use_pdflatex = has_pdftex and has_pgf

        if use_pdflatex:
            # Keep pdfLaTeX but avoid OT1 encoding because characters like
            # \DJ/\dj are unavailable there.
            tex = tex.replace(
                '\\usepackage[OT1]{fontenc}',
                '\\usepackage[T1]{fontenc}',
            )

        # ── Before \documentclass ──
        PASS_XCOLOR = "\\PassOptionsToPackage{table,xcdraw}{xcolor}\n"
        PASS_HYPERREF = "\\PassOptionsToPackage{hidelinks}{hyperref}\n"
        dc_match = re.search(r'^[ \t]*\\documentclass', tex, re.MULTILINE)
        if dc_match:
            inject_before_dc = ""
            if PASS_XCOLOR.strip() not in tex:
                inject_before_dc += PASS_XCOLOR
            if PASS_HYPERREF.strip() not in tex:
                inject_before_dc += PASS_HYPERREF
            if inject_before_dc:
                tex = tex[:dc_match.start()] + inject_before_dc + tex[dc_match.start():]

        if not use_pdflatex:
            # ── XeLaTeX mode: remove pdftex, replace fontenc ──
            dc_opts = re.search(r'(\\documentclass\s*\[)([^\]]*)(\])', tex)
            if dc_opts:
                opts = dc_opts.group(2)
                opt_list = [o.strip() for o in opts.split(',')]
                opt_list = [o for o in opt_list if o.lower() not in ('pdftex', 'pdflatex')]
                new_opts = ', '.join(opt_list)
                tex = tex[:dc_opts.start(2)] + new_opts + tex[dc_opts.end(2):]

            for old_enc in (
                '\\usepackage[T1]{fontenc}',
                '\\usepackage[OT1]{fontenc}',
            ):
                if old_enc in tex:
                    tex = tex.replace(
                        old_enc,
                        '\\usepackage{iftex}\n\\ifXeTeX\n  \\usepackage{fontspec}\n\\else\n  ' + old_enc + '\n\\fi'
                    )
                    break

            tex = re.sub(
                r'^([ \t]*)(\\usepackage\[[^\]]*\]\{inputenc\})',
                r'\1\\ifXeTeX\n\1  % \2\n\1\\else\n\1  \2\n\1\\fi',
                tex,
                flags=re.MULTILINE,
            )

        # ── Package injection before \begin{document} ──
        # xcolor & hyperref options are already handled via \PassOptionsToPackage before
        # \documentclass, so we only need bare \usepackage guards here.
        # hyperref is NOT force-loaded: many publisher classes (MDPI, ACM, Springer)
        # load it themselves with specific options; forcing it causes option clashes.
        # fontspec is NOT injected here: classes that use fontenc (MDPI, etc.) conflict
        # with fontspec's TU encoding. The fontenc→fontspec replacement in the preamble
        # (above) already handles templates that explicitly load fontenc in their body.
        INJECT_BLOCK = (
            "\\makeatletter\n"
            "\\@ifpackageloaded{iftex}{}{\\usepackage{iftex}}\n"
            "\\ifPDFTeX\\@ifpackageloaded{fontenc}{}{\\usepackage[T1]{fontenc}}\\fi\n"
            "\\@ifpackageloaded{amsmath}{}{\\usepackage{amsmath}}\n"
            "\\@ifundefined{Bbbk}{}{\\let\\Bbbk\\relax}\n"
            "\\@ifpackageloaded{amssymb}{}{\\usepackage{amssymb}}\n"
            "\\@ifpackageloaded{xurl}{}{\\usepackage{xurl}}\n"
            "\\@ifpackageloaded{xcolor}{}{\\usepackage{xcolor}}\n"
            "\\@ifpackageloaded{graphicx}{}{\\usepackage{graphicx}}\n"
            "\\@ifpackageloaded{float}{}{\\usepackage{float}}\n"
            "\\@ifpackageloaded{wrapfig}{}{\\usepackage{wrapfig}}\n"
            "\\@ifpackageloaded{placeins}{}{\\usepackage{placeins}}\n"
            "\\makeatother\n"
        )

        if '@ifpackageloaded{amsmath}' in tex:
            # Preamble was already processed before; still guarantee required guards.
            has_xcolor_guard = '@ifpackageloaded{xcolor}' in tex
            has_xcolor_pkg = re.search(r'\\usepackage(?:\[[^\]]*\])?\{xcolor\}', tex) is not None
            has_fontenc_t1 = re.search(r'\\usepackage\[T1\]\{fontenc\}', tex) is not None
            has_fontenc_guard = '\\ifPDFTeX\\@ifpackageloaded{fontenc}{}{\\usepackage[T1]{fontenc}}\\fi' in tex
            has_iftex_pkg = re.search(r'\\usepackage(?:\[[^\]]*\])?\{iftex\}', tex) is not None

            if (has_xcolor_guard or has_xcolor_pkg) and (has_fontenc_t1 or has_fontenc_guard):
                return tex
            doc_match = re.search(r'^[ \t]*\\begin\{document\}', tex, re.MULTILINE)
            if not doc_match:
                return tex
            repair_lines = ["\\makeatletter"]
            if not has_iftex_pkg:
                repair_lines.append("\\@ifpackageloaded{iftex}{}{\\usepackage{iftex}}")
            if not (has_fontenc_t1 or has_fontenc_guard):
                repair_lines.append("\\ifPDFTeX\\@ifpackageloaded{fontenc}{}{\\usepackage[T1]{fontenc}}\\fi")
            if not (has_xcolor_guard or has_xcolor_pkg):
                repair_lines.append("\\@ifpackageloaded{xcolor}{}{\\usepackage{xcolor}}")
            repair_lines.append("\\makeatother")
            repair_block = "\n".join(repair_lines) + "\n"

            pos = doc_match.start()
            if repair_block == "\\makeatletter\n\\makeatother\n":
                return tex
            return tex[:pos] + repair_block + tex[pos:]

        # Match only non-commented \begin{document} (avoid % comment matches)
        doc_match = re.search(r'^[ \t]*\\begin\{document\}', tex, re.MULTILINE)
        if not doc_match:
            return tex

        pos = doc_match.start()
        return tex[:pos] + INJECT_BLOCK + tex[pos:]

    # ── Phase 2: Publisher metadata cleanup ───────────────────────

    @classmethod
    def _cleanup_publisher_metadata(cls, tex: str, config: dict = None) -> str:
        """Remove publisher-specific metadata using rules from manifest."""
        config = config or {}
        
        # 1. Strip commands from manifest
        for cmd in config.get("strip_commands", []):
            tex = cls._remove_command(tex, r'\\' + cmd)
            
        # 2. Strip multi-brace commands from manifest
        for cmd in config.get("multi_brace_commands", []):
            tex = cls._remove_command(tex, r'\\' + cmd, multi_brace=True)
            
        # 3. Strip environments from manifest
        for env in config.get("strip_environments", []):
            tex = re.sub(
                rf'[ \t]*\\begin\{{{env}\}}.*?\\end\{{{env}\}}\s*',
                '', tex, flags=re.DOTALL,
            )

        # 4. Elsevier (elsarticle) specialized fixes
        if 'elsarticle' in tex:
            # Switch to numbered citations
            tex = re.sub(
                r'^([^%\n]*\\documentclass\s*\[)([^\]]*)\]',
                lambda m: m.group(1) + m.group(2).replace('authoryear', 'number') + ']',
                tex, count=1, flags=re.MULTILINE,
            )
            tex = re.sub(
                r'(\\bibliographystyle\{)elsarticle-harv(\})',
                r'\1elsarticle-num\2',
                tex,
            )

        # 5. MDPI first‑page left‑column overlap fix
        if 'mdpi' in tex or 'Definitions/mdpi' in tex:
            doc_match = re.search(r'^[ \t]*\\begin\{document\}', tex, re.MULTILINE)
            if doc_match:
                override = "\\makeatletter\\renewcommand{\\contentleftcolumn}{}\\makeatother\n"
                if override.strip() not in tex:
                    tex = tex[:doc_match.start()] + override + tex[doc_match.start():]

        return tex

    # ── Phase 3: Title ──────────────────────────────────────────

    @classmethod
    def _process_title(cls, tex: str, config: dict = None) -> str:
        config = config or {}
        r"""
        Replace content of \title{...} or \Title{...} with << metadata.title >>.
        Case-insensitive to support MDPI's \Title{} and standard \title{}.
        Handles optional args: \title[short title]{full title}.
        Skips commented-out occurrences.
        """
        title_cmd = config.get("title_command", r"\title")
        title_cmd_regex = r"\\" + title_cmd[1:] if title_cmd.startswith("\\") else r"\\" + title_cmd
        match_iter = re.finditer(rf'(?i){title_cmd_regex}\s*(?:\[\[^\]]*\])?\s*\{{', tex)
        for match in match_iter:
            if cls._is_commented(tex, match.start()):
                continue
            start_open = match.end() - 1
            end_close = cls._find_matching_brace(tex, start_open)
            if end_close != -1:
                title_tag = '<< metadata.title >>'
                title_tag = re.sub(r'\s+', ' ', title_tag).strip()
                tex = tex[:start_open + 1] + title_tag + tex[end_close:]
                break
        return tex

    # ── Phase 4: Authors ─────────────────────────────────────────

    @classmethod
    def _replace_existing_author(cls, tex: str) -> str:
        """Replace author macros with a single placeholder.
        The first non‑commented \author (or \Author) macro is replaced by the
        ``<< metadata.author_block >>`` placeholder. Any additional author macros
        are removed entirely to avoid duplicate definitions.
        """
        # Use brace matching to support deeply nested author bodies, e.g.:
        # \author{A\inst{1} \and B\inst{2,3}\orcidID{...}}
        pattern = r'(?i)\\author(?!running|note|notemark|names|contributions)\*?\s*(?:\[[^\]]*\])?\s*\{'
        spans = []
        search_start = 0
        while True:
            m = re.search(pattern, tex[search_start:])
            if not m:
                break

            abs_start = search_start + m.start()
            if cls._is_commented(tex, abs_start):
                search_start = search_start + m.end()
                continue

            open_brace = search_start + m.end() - 1
            close_brace = cls._find_matching_brace(tex, open_brace)
            if close_brace == -1:
                search_start = search_start + m.end()
                continue

            spans.append((abs_start, close_brace + 1))
            search_start = close_brace + 1

        if not spans:
            return tex

        first_start, first_end = spans[0]
        tex = tex[:first_start] + "<< metadata.author_block >>" + tex[first_end:]

        # Remove additional author macros from right to left on the updated text.
        # Re-scan to get current offsets after the first replacement.
        extra_spans = []
        search_start = 0
        while True:
            m = re.search(pattern, tex[search_start:])
            if not m:
                break
            abs_start = search_start + m.start()
            if cls._is_commented(tex, abs_start):
                search_start = search_start + m.end()
                continue
            open_brace = search_start + m.end() - 1
            close_brace = cls._find_matching_brace(tex, open_brace)
            if close_brace == -1:
                search_start = search_start + m.end()
                continue
            extra_spans.append((abs_start, close_brace + 1))
            search_start = close_brace + 1

        for s, e in reversed(extra_spans):
            tex = tex[:s] + tex[e:]

        return tex
    def _process_authors(cls, tex: str, config: dict = None) -> str:
        config = config or {}
        r"""
        Remove all author-related commands and inject << metadata.author_block >>.
        Supports IEEE, ACM, Springer, MDPI, Elsevier formats.

        Case-insensitive for \author / \Author (MDPI) and \address / \Address.
        """
        # First, replace any existing \author definition with placeholder to avoid duplicate definitions
        tex = cls._replace_existing_author(tex)
        commands_to_remove = [
            r'\\authorrunning', r'\\titlerunning',
            r'(?i)\\author(?!Names|note|mark|contributions)',  # \author/\Author but not \AuthorNames etc.
            r'(?i)\\affil(?:iation)?',   # \affil (Springer), \affiliation (ACM)
            r'(?i)\\address',
            r'(?i)\\email',
            r'(?i)\\institute',
            r'\\authornote',             # ACM
            r'\\authornotemark',         # ACM
            r'\\orcid',                  # ACM
            r'\\corres',                 # MDPI
            r'\\firstnote',              # MDPI
            r'\\ead',                    # Elsevier
        ]
        author_cmd = config.get("author_command")
        if author_cmd:
            commands_to_remove.append(r"\\" + author_cmd[1:] if author_cmd.startswith("\\") else r"\\" + author_cmd)

        for cmd in commands_to_remove:
            _failsafe = 0
            search_start = 0
            while True:
                _failsafe += 1
                if _failsafe > 50:
                    break
                pattern = cmd + r'\s*(?:\[[^\]]*\])?\s*\{'
                match = re.search(pattern, tex[search_start:])
                if not match:
                    break
                abs_start = search_start + match.start()
                # Skip matches inside comment lines
                if cls._is_commented(tex, abs_start):
                    search_start = search_start + match.end()
                    continue
                start_match = abs_start
                start_open = search_start + match.end() - 1
                end_close = cls._find_matching_brace(tex, start_open)
                if end_close != -1:
                    end_pos = end_close + 1
                    while end_pos < len(tex):
                        rest = tex[end_pos:]
                        match = re.match(r'^(\s|%.*?\n)*', rest)
                        skip_len = match.end() if match else 0
                        if end_pos + skip_len < len(tex) and tex[end_pos + skip_len] == '{':
                            next_brace = end_pos + skip_len
                            next_end = cls._find_matching_brace(tex, next_brace)
                            if next_end != -1:
                                end_pos = next_end + 1
                                continue
                        break
                    
                    remove_end = end_pos
                    while remove_end < len(tex) and tex[remove_end] in (' ', '\t'):
                        remove_end += 1
                    if remove_end < len(tex) and tex[remove_end] == '\n':
                        remove_end += 1
                    tex = tex[:start_match] + tex[remove_end:]
                    search_start = 0  # reset — tex was modified
                else:
                    break

        # Remove commands with only optional args (no required brace): \authornotemark[1]
        tex = re.sub(r'^[ \t]*\\authornotemark\s*\[[^\]]*\].*$\n?', '', tex, flags=re.MULTILINE)

        # Inject << metadata.author_block >> after \title{...} if not already present
        if '<< metadata.author_block >>' not in tex:
            insert_pos = -1

            # Try: after \title{...} (skip commented lines)
            title_cmd = config.get("title_command", r"\title")
            title_cmd_regex = r"\\" + title_cmd[1:] if title_cmd.startswith("\\") else r"\\" + title_cmd
            match_iter = re.finditer(rf'(?i){title_cmd_regex}\s*(?:\[\[^\]]*\])?\s*\{{', tex)
            for match in match_iter:
                if cls._is_commented(tex, match.start()):
                    continue
                start_open = match.end() - 1
                end_close = cls._find_matching_brace(tex, start_open)
                if end_close != -1:
                    insert_pos = end_close + 1
                    break

            # Fallback: after \begin{document} (non-commented only)
            if insert_pos == -1:
                doc_match = re.search(r'^[ \t]*\\begin\{document\}', tex, re.MULTILINE)
                if doc_match:
                    insert_pos = doc_match.end()

            if insert_pos != -1:
                author_tag = '<< metadata.author_block >>'
                author_tag = re.sub(r'\s+', ' ', author_tag).strip()
                tex = tex[:insert_pos] + author_tag + tex[insert_pos:]

        return tex

    # ── Phase 5: Abstract ────────────────────────────────────────

    @classmethod
    def _process_abstract(cls, tex: str, config: dict = None) -> str:
        config = config or {}
        r"""
        Replace abstract content with << metadata.abstract >>.

        Supports:
        - \begin{abstract}...\end{abstract} (IEEE, ACM, Springer, Elsevier)
        - \abstract{...} (MDPI command form)
        - Fallback: inject abstract block if neither is found.
        """
        abstract_env = config.get("abstract_env", "abstract")
        abstract_cmd_regex = r"\\" + abstract_env[1:] if abstract_env.startswith("\\") else r"\\" + abstract_env
        
        # Pattern 1: Environment form \begin{abstract}...\end{abstract}
        env_match = re.search(rf'\\begin\{{{abstract_env}\}}(.*?)\\end\{{{abstract_env}\}}', tex, re.DOTALL)
        if env_match:
            inner_text = env_match.group(1)
            has_keywords_inside = r'\keywords' in inner_text

            repl = r'\g<1>\n<< metadata.abstract >>\n'
            if has_keywords_inside:
                repl += r'\\keywords{<< metadata.keywords_str >>}\n'
            repl += r'\g<2>'

            # Sử dụng count=1 để tránh thay thế examples trong documentation (e.g. \inlinecode)
            tex = re.sub(
                rf'(\\begin\{{{abstract_env}\}}).*?(\\end\{{{abstract_env}\}})',
                repl, tex, count=1, flags=re.DOTALL,
            )
            return cls._process_ieee_keywords(tex)

        # Pattern 2: Command form \abstract{...} (MDPI) — case-insensitive
        cmd_match = re.search(rf'(?i){abstract_cmd_regex}\s*\{{', tex)
        if cmd_match:
            start_open = cmd_match.end() - 1
            end_close = cls._find_matching_brace(tex, start_open)
            if end_close != -1:
                tex = tex[:start_open + 1] + '<< metadata.abstract >>' + tex[end_close:]
                return cls._process_ieee_keywords(tex)

        # Fallback: inject abstract block after \maketitle or \begin{document}
        if '<< metadata.abstract >>' not in tex:
            maketitle_match = re.search(r'^[ \t]*\\maketitle', tex, re.MULTILINE)
            if maketitle_match:
                insert_pos = maketitle_match.end()
                tex = (tex[:insert_pos] +
                       "\n\n\\begin{abstract}\n<< metadata.abstract >>\n\\end{abstract}\n\n" +
                       tex[insert_pos:])
            else:
                doc_match = re.search(r'^[ \t]*\\begin\{document\}', tex, re.MULTILINE)
                if doc_match:
                    insert_pos = doc_match.end()
                    tex = (tex[:insert_pos] +
                           "\n\n\\begin{abstract}\n<< metadata.abstract >>\n\\end{abstract}\n\n" +
                           tex[insert_pos:])

        return cls._process_ieee_keywords(tex)

    @classmethod
    def _process_ieee_keywords(cls, tex: str) -> str:
        """Inject << metadata.keywords_str >> into IEEEkeywords environment."""
        pattern = r'(\\begin\{IEEEkeywords\}).*?(\\end\{IEEEkeywords\})'
        repl = r'\g<1>\n<< metadata.keywords_str >>\n\g<2>'
        return re.sub(pattern, repl, tex, flags=re.DOTALL)

    # ── Phase 7: Body ────────────────────────────────────────────

    @classmethod
    def _verbatim_ranges(cls, tex: str) -> list:
        """Return list of (start, end) char ranges that are inside verbatim contexts.

        Covers:
        - \\verb|...|  (any delimiter)
        - \\begin{verbatim}...\\end{verbatim}
        - \\inlinecode{...}
        """
        ranges = []
        # \verb<delim>...<delim>
        for m in re.finditer(r'\\verb(.)(.*?)\1', tex, re.DOTALL):
            ranges.append((m.start(), m.end()))
        # \begin{verbatim}...\end{verbatim}
        for m in re.finditer(r'\\begin\{verbatim\}.*?\\end\{verbatim\}', tex, re.DOTALL):
            ranges.append((m.start(), m.end()))
        # \inlinecode{...} (Hỗ trợ Rho-class documentation)
        for m in re.finditer(r'\\inlinecode\s*\{', tex):
            brace_start = m.end() - 1
            brace_end = cls._find_matching_brace(tex, brace_start)
            if brace_end != -1:
                ranges.append((m.start(), brace_end + 1))
        return ranges

    @classmethod
    def _process_body(cls, tex: str) -> str:
        """
        Xác định điểm bắt đầu phần thân (sau frontmatter) và kết thúc.
        XÓA SẠCH tất cả dummy text mẫu giữa 2 điểm đó rồi chèn << body >>.

        Universal: works with any template structure:
        - IEEE (maketitle + IEEEkeywords)
        - Springer (maketitle + abstract)
        - Elsevier (end frontmatter)
        - Generic (falls back to begin document if no other marker found)
        """
        verb_ranges = cls._verbatim_ranges(tex)

        def _in_verbatim(pos):
            return any(s <= pos < e for s, e in verb_ranges)

        # Tìm điểm BẮT ĐẦU: lấy vị trí xa nhất (cuối cùng) trong các mốc
        start_search_patterns = [
            r'\\maketitle',
            r'\\end\{abstract\}',
            r'\\end\{IEEEkeywords\}',
            r'\\end\{keyword\}',        # Elsevier
            r'\\end\{frontmatter\}',     # Elsevier
        ]
        
        body_start = -1
        for p in start_search_patterns:
            matches = [m for m in re.finditer(p, tex) if not _in_verbatim(m.start())]
            if matches:
                pos = matches[-1].end()
                if pos > body_start:
                    body_start = pos

        # FALLBACK: Nếu không tìm thấy marker nào (template đơn giản),
        # dùng \begin{document} làm điểm bắt đầu (non-commented only)
        if body_start == -1:
            doc_match = re.search(r'^[ \t]*\\begin\{document\}', tex, re.MULTILINE)
            if doc_match:
                body_start = doc_match.end()

        # Tìm điểm KẾT THÚC: ưu tiên References/bibliography, fallback \end{document}
        end_search_patterns = [
            r'\\section\*?\{References\}',
            r'\\begin\{thebibliography\}',
            r'\\bibliographystyle\{',
            r'\\bibliography\{',
            r'\\printbibliography',
            r'<< references_block >>',
            r'\\end\{document\}'
        ]

        body_end = len(tex)
        for p in end_search_patterns:
            for m in re.finditer(p, tex):
                if _in_verbatim(m.start()):
                    continue
                pos = m.start()
                if pos < body_end and pos > body_start:
                    body_end = pos
                    break  # first non-verbatim match for this pattern

        if body_start != -1 and body_start < body_end:
            # MDPI wraps bibliography in \begin{adjustwidth} — preserve it.
            # Find the LAST \begin{adjustwidth} before body_end.
            region = tex[body_start:body_end]
            adj_matches = list(re.finditer(
                r'(?:^[ \t]*%[^\n]*\n)*^[ \t]*\\begin\{adjustwidth\}[^\n]*\n',
                region, re.MULTILINE
            ))
            if adj_matches:
                body_end = body_start + adj_matches[-1].start()
            # XÓA SẠCH toàn bộ dummy text mẫu giữa 2 điểm, chèn << body >>
            tex = tex[:body_start] + "\n\n<< body >>\n\n" + tex[body_end:]
        elif body_start != -1:
            # Không tìm thấy end marker, cắt từ body_start đến hết
            match_end_doc = re.search(r'\\end\{document\}', tex[body_start:])
            if match_end_doc:
                end_pos = body_start + match_end_doc.start()
                tex = tex[:body_start] + "\n\n<< body >>\n\n" + tex[end_pos:]
            else:
                tex = tex[:body_start] + "\n\n<< body >>\n\n"

        return tex

    # ── Phase 6: Keywords ────────────────────────────────────────

    @classmethod
    def _process_keywords(cls, tex: str, config: dict = None) -> str:
        config = config or {}
        r"""
        Inject << metadata.keywords_str >> into keywords command.

        Supports:
        - \keywords{...} (Springer, ACM)
        - \keyword{...}  (MDPI, singular — negative lookahead for \keywords)
        - \begin{keyword}...\end{keyword} (Elsevier environment form)
        """
        # \begin{keyword}...\end{keyword} (Elsevier environment)
        env_match = re.search(r'\\begin\{keyword\}(.*?)\\end\{keyword\}', tex, re.DOTALL)
        if env_match:
            tex = (tex[:env_match.start()]
                   + r'\begin{keyword}' + '\n'
                   + '<< metadata.keywords_str >>'  + '\n'
                   + r'\end{keyword}'
                   + tex[env_match.end():])
            return tex

        # \keywords{...} (with 's') — case-insensitive
        match = re.search(r'(?i)\\keywords\s*\{', tex)
        if match:
            start_open = match.end() - 1
            end_close = cls._find_matching_brace(tex, start_open)
            if end_close != -1:
                tex = tex[:start_open + 1] + '<< metadata.keywords_str >>' + tex[end_close:]
                return tex

        # \keyword{...} (MDPI, without 's') — case-insensitive
        match = re.search(r'(?i)\\keyword(?!s)\s*\{', tex)
        if match:
            start_open = match.end() - 1
            end_close = cls._find_matching_brace(tex, start_open)
            if end_close != -1:
                tex = tex[:start_open + 1] + '<< metadata.keywords_str >>' + tex[end_close:]

        return tex

    # ── Phase 8: References ──────────────────────────────────────

    @classmethod
    def _process_references(cls, tex: str) -> str:
        r"""Replace toàn bộ phần references (thebibliography hoặc \section*{References}) và
        xóa sạch dummy text mẫu còn sót, chỉ giữ << references_block >>."""
        # Bước 1: Thay thế tất cả \begin{thebibliography}...\end{thebibliography}
        # Giữ lại block đầu tiên (thay bằng << references_block >>), xóa các block còn lại
        pattern = r'\\begin\{thebibliography\}.*?\\end\{thebibliography\}'
        first_replaced = False
        while True:
            match = re.search(pattern, tex, re.DOTALL)
            if not match:
                break
            if not first_replaced:
                tex = tex[:match.start()] + '<< references_block >>' + tex[match.end():]
                first_replaced = True
            else:
                # Remove subsequent bibliography blocks (template samples)
                tex = tex[:match.start()] + tex[match.end():]

        # Bước 1b: MDPI templates wrap bibliography in conditional macros
        # (\isAPAandChicago, \isChicagoStyle, \isAPAStyle).
        # These macros read the bibliography as a TeX parameter which breaks
        # with large reference lists. Strip the wrapping and keep << references_block >> bare.
        for mdpi_cmd in (r'\\isAPAandChicago', r'\\isChicagoStyle', r'\\isAPAStyle'):
            # Pattern: \macro{...}{...} — two brace groups
            cmd_pattern = mdpi_cmd + r'\s*'
            while True:
                m = re.search(cmd_pattern + r'\{', tex)
                if not m:
                    break
                brace1_start = m.end() - 1
                brace1_end = cls._find_matching_brace(tex, brace1_start)
                if brace1_end == -1:
                    break
                # Look for optional second brace group
                rest = tex[brace1_end + 1:]
                rest_stripped = rest.lstrip()
                if rest_stripped and rest_stripped[0] == '{':
                    offset = brace1_end + 1 + (len(rest) - len(rest_stripped))
                    brace2_end = cls._find_matching_brace(tex, offset)
                    if brace2_end == -1:
                        brace2_end = brace1_end  # no second group
                    end_pos = brace2_end + 1
                else:
                    end_pos = brace1_end + 1
                # Extract inner content of the group that has << references_block >>
                inner1 = tex[brace1_start + 1:brace1_end]
                if '<< references_block >>' in inner1:
                    # Keep the references block, remove everything else of this macro
                    tex = tex[:m.start()] + '<< references_block >>' + tex[end_pos:]
                elif rest_stripped and rest_stripped[0] == '{':
                    inner2 = tex[offset + 1:brace2_end] if brace2_end > offset else ''
                    if '<< references_block >>' in inner2:
                        tex = tex[:m.start()] + '<< references_block >>' + tex[end_pos:]
                    else:
                        # Neither group has references — remove entire macro call
                        tex = tex[:m.start()] + tex[end_pos:]
                else:
                    tex = tex[:m.start()] + tex[end_pos:]

        # Bước 2: Nếu có \section*{References}, xóa TOÀN BỘ nội dung từ đó đến \end{document}
        # (bao gồm dummy guidance text, \color{red} warning, v.v.) và chỉ giữ references_block
        ref_match = re.search(r'\\section\*?\s*\{References\}', tex)
        end_doc_match = re.search(r'\\end\{document\}', tex)
        if ref_match and end_doc_match and ref_match.start() < end_doc_match.start():
            tex = tex[:ref_match.start()] + '\n<< references_block >>\n\n' + tex[end_doc_match.start():]

        # Bước 3: Handle \bibliographystyle{} and \bibliography{} (BibTeX-based templates like ACM)
        # If no << references_block >> was created by steps 1-2, replace everything from
        # the LAST \bibliographystyle (or \bibliography) through \end{document} to ensure
        # references_block exists and leftover template content (e.g. appendix) is removed.
        # Use LAST matches to skip documentation text / verbatim examples.
        if '<< references_block >>' not in tex:
            end_docs = list(re.finditer(r'\\end\{document\}', tex))
            end_doc = end_docs[-1] if end_docs else None
            if end_doc:
                bib_styles = [m for m in re.finditer(r'^[ \t]*\\bibliographystyle\{', tex, re.MULTILINE)
                              if m.start() < end_doc.start()]
                bib_cmds = [m for m in re.finditer(r'^[ \t]*\\bibliography\{', tex, re.MULTILINE)
                            if m.start() < end_doc.start()]
                print_bibs = [m for m in re.finditer(r'^[ \t]*\\printbibliography\b', tex, re.MULTILINE)
                              if m.start() < end_doc.start()]
                
                valid_starts = []
                if bib_styles: valid_starts.append(bib_styles[-1].start())
                if bib_cmds: valid_starts.append(bib_cmds[-1].start())
                if print_bibs: valid_starts.append(print_bibs[-1].start())
                
                if valid_starts:
                    start = max(valid_starts)
                    tex = tex[:start] + '\n<< references_block >>\n\n' + tex[end_doc.start():]
                else:
                    tex = tex[:end_doc.start()] + '\n<< references_block >>\n\n' + tex[end_doc.start():]
        else:
            # references_block already exists — just comment out the commands
            tex = re.sub(r'^(\s*)(\\bibliographystyle\{[^}]*\})', r'\1% \2', tex, flags=re.MULTILINE)
            tex = re.sub(r'^(\s*)(\\bibliography\{[^}]*\})', r'\1% \2', tex, flags=re.MULTILINE)
            tex = re.sub(r'^(\s*)(\\printbibliography\b.*)', r'\1% \2', tex, flags=re.MULTILINE)

        return tex
