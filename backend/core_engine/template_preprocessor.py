import re
import os

class TemplatePreprocessor:
    """
    Universal LaTeX template preprocessor for Jinja2 tagging.
    Supports: IEEE, ACM, Springer (LLNCS), Elsevier, MDPI, and generic templates.
    Injects Jinja2 variables (e.g. << metadata.title >>, << body >>)
    using custom delimiters << >> to avoid { } conflict.
    """

    @classmethod
    def auto_tag(cls, tex_content: str) -> str:
        """
        Main entry point for tagging a LaTeX template with Jinja2 variables.
        Strategy: Patches -> Zone cleanup -> Structured processing -> Final tagging.
        """
        # ── Phase 1: Basic Patches & Essential Packages ──
        tex = cls._ensure_essential_packages(tex_content)
        
        # Hỗ trợ Tiếng Việt (fontspec + Times New Roman cho XeLaTeX)
        if r'\setmainfont' not in tex and r'\usepackage{fontspec}' not in tex:
            font_patch = r"\usepackage{fontspec}" + "\n" + r"\setmainfont{Times New Roman}" + "\n"
            # Chèn sau documentclass
            tex = re.sub(r'(\\documentclass\b.*?\]?\{.*?\})', r'\1' + '\n' + font_patch, tex)

        # Vá lỗi apacite: \onemaskedcitationmsg undefined
        if r'\onemaskedcitationmsg' not in tex:
            patch = r"\providecommand{\onemaskedcitationmsg}[1]{}" + "\n"
            tex = re.sub(r'(\\begin\{document\})', patch + r'\1', tex)

        # ── Phase 2: Zone-Based Author Cleanup (Regex) ──
        # Xóa sạch vùng từ \author đến lệnh quan trọng tiếp theo để tránh dangling arguments (như ở jov.cls)
        # Thay thế bằng Jinja tag kèm Universal Brace Padding (5 cặp ngoặc rỗng)
        author_insertion = r'<< metadata.author_block >>{ }{ }{ }{ }{ }\n'
        pattern_author_zone = r'\\author\b.*?(\\abstract|\\begin\{abstract\}|\\keywords|\\makedirs|\\maketitle|\\section)'
        if re.search(pattern_author_zone, tex, re.DOTALL | re.IGNORECASE):
            print("[*] Unified Regex: Replacing Author zone with padding...")
            tex = re.sub(pattern_author_zone, author_insertion + r'\1', tex, count=1, flags=re.DOTALL | re.IGNORECASE)

        # ── Phase 3: Structured Metadata Processing ──
        tex = cls._cleanup_publisher_metadata(tex)
        tex = cls._process_title(tex)
        tex = cls._process_authors(tex)  # Also ensures author_block exists
        tex = cls._process_abstract(tex)
        tex = cls._process_keywords(tex)
        
        # ── Phase 4: Body & References ──
        tex = cls._process_references(tex)
        tex = cls._process_body(tex)
        
        return tex

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
                    rest = tex[end + 1:].lstrip()
                    if rest and rest[0] == '{':
                        next_brace = tex.index('{', end + 1)
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
        """
        # ── Detect if template needs pdflatex (pdftex option + tikz/pgf) ──
        dc_opts_match = re.search(r'\\documentclass\s*\[([^\]]*)\]', tex)
        dc_opts_str = dc_opts_match.group(1) if dc_opts_match else ''
        has_pdftex = any(o.strip().lower() in ('pdftex', 'pdflatex') for o in dc_opts_str.split(','))
        has_pgf = bool(re.search(r'tikz|pgf|mdpi', tex[:3000], re.IGNORECASE))
        use_pdflatex = has_pdftex and has_pgf

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
                        '\\usepackage{fontspec}  % XeLaTeX: Unicode font support',
                    )
                    break

            tex = re.sub(
                r'^([ \t]*)(\\usepackage\[[^\]]*\]\{inputenc\})',
                r'\1% \2  % Removed: XeLaTeX handles UTF-8 natively',
                tex,
                flags=re.MULTILINE,
            )

        # ── Package injection before \begin{document} ──
        INJECT_BLOCK = (
            "\\makeatletter\n"
            "\\@ifpackageloaded{amsmath}{}{\\usepackage{amsmath}}\n"
            "\\@ifpackageloaded{amssymb}{}{\\usepackage{amssymb}}\n"
            "\\@ifpackageloaded{xurl}{}{\\usepackage{xurl}}\n"
            "\\@ifpackageloaded{xcolor}{}{\\usepackage{xcolor}}\n"
            "\\@ifpackageloaded{graphicx}{}{\\usepackage{graphicx}}\n"
            "\\makeatother\n"
        )

        if '@ifpackageloaded{amsmath}' in tex:
            has_xcolor_guard = '@ifpackageloaded{xcolor}' in tex
            has_xcolor_pkg = re.search(r'\\usepackage(?:\[[^\]]*\])?\{xcolor\}', tex) is not None
            if has_xcolor_guard or has_xcolor_pkg:
                return tex
            doc_match = re.search(r'^[ \t]*\\begin\{document\}', tex, re.MULTILINE)
            if not doc_match:
                return tex
            xcolor_block = (
                "\\makeatletter\n"
                "\\@ifpackageloaded{xcolor}{}{\\usepackage{xcolor}}\n"
                "\\makeatother\n"
            )
            pos = doc_match.start()
            return tex[:pos] + xcolor_block + tex[pos:]

        doc_match = re.search(r'^[ \t]*\\begin\{document\}', tex, re.MULTILINE)
        if not doc_match:
            return tex

        pos = doc_match.start()
        return tex[:pos] + INJECT_BLOCK + tex[pos:]

    # ── Phase 2: Publisher metadata cleanup ───────────────────────

    @classmethod
    def _cleanup_publisher_metadata(cls, tex: str) -> str:
        """Remove publisher-specific metadata that won't be populated."""
        tex = re.sub(r'\\begin\{CCSXML\}.*?\\end\{CCSXML\}\s*\n?', '', tex, flags=re.DOTALL)
        tex = cls._remove_command(tex, r'\\ccsdesc')
        for cmd in ('acmConference', 'acmBooktitle', 'acmDOI', 'acmYear',
                     'acmISBN', 'acmPrice', 'acmSubmissionID',
                     'setcopyright', 'copyrightyear'):
            tex = cls._remove_command(tex, r'\\' + cmd, multi_brace=True)
        tex = re.sub(r'\\begin\{teaserfigure\}.*?\\end\{teaserfigure\}\s*\n?', '', tex, flags=re.DOTALL)
        tex = re.sub(r'^[ \t]*\\renewcommand\s*\{\\shortauthors\}\s*\{[^}]*\}.*$\n?', '', tex, flags=re.MULTILINE)
        tex = cls._remove_command(tex, r'\\AuthorNames')
        for cmd in ('secondnote', 'thirdnote', 'fourthnote', 'fifthnote', 'sixthnote', 'seventhnote', 'eighthnote',
                     'institutionalreview', 'dataavailability', 'conflictsofinterest', 'sampleavailability',
                     'authorcontributions', 'funding', 'abbreviations', 'appendixtitles'):
            tex = cls._remove_command(tex, r'\\' + cmd)

        if re.search(r'\\documentclass\b[^}]*\{elsarticle\}', tex):
            tex = re.sub(r'^([^%\n]*\\documentclass\s*\[)([^\]]*)\]',
                lambda m: m.group(1) + m.group(2).replace('authoryear', 'number') + ']',
                tex, count=1, flags=re.MULTILINE)
            tex = re.sub(r'(\\bibliographystyle\{)elsarticle-harv(\})', r'\1elsarticle-num\2', tex)
            tex = cls._remove_command(tex, r'\\journal')
            for cmd in ('tnotetext', 'fntext', 'cortext', 'ead'):
                tex = cls._remove_command(tex, r'\\' + cmd)
            tex = re.sub(r'[ \t]*\\begin\{graphicalabstract\}.*?\\end\{graphicalabstract\}\s*', '', tex, flags=re.DOTALL)
            tex = re.sub(r'[ \t]*\\begin\{highlights\}.*?\\end\{highlights\}\s*', '', tex, flags=re.DOTALL)

        if re.search(r'\\documentclass[^}]*\{Definitions/mdpi\}', tex):
            doc_match = re.search(r'^[ \t]*\\begin\{document\}', tex, re.MULTILINE)
            if doc_match:
                override = "\\makeatletter\\renewcommand{\\contentleftcolumn}{}\\makeatother\n"
                if override.strip() not in tex:
                    tex = tex[:doc_match.start()] + override + tex[doc_match.start():]
        return tex

    # ── Phase 3: Title ──────────────────────────────────────────

    @classmethod
    def _process_title(cls, tex: str) -> str:
        match_iter = re.finditer(r'(?i)\\title\s*(?:\[\[^\]]*\])?\s*\{', tex)
        for match in match_iter:
            if cls._is_commented(tex, match.start()): continue
            start_open = match.end() - 1
            end_close = cls._find_matching_brace(tex, start_open)
            if end_close != -1:
                tex = tex[:start_open + 1] + '<< metadata.title >>' + tex[end_close:]
                break
        return tex

    # ── Phase 4: Authors ─────────────────────────────────────────

    @classmethod
    def _process_authors(cls, tex: str) -> str:
        r"""
        Remove author commands and inject << metadata.author_block >>.
        Universal Brace Padding is added to the injection if not already processed by auto_tag.
        """
        commands_to_remove = [
            r'\\authorrunning', r'\\titlerunning',
            r'(?i)\\author(?!Names|note|mark|contributions)',
            r'(?i)\\affil(?:iation)?', r'(?i)\\address', r'\\email', r'\\institute',
            r'\\authornote', r'\\orcid', r'\\corres', r'\\firstnote',
        ]

        for cmd in commands_to_remove:
            _failsafe = 0
            search_start = 0
            while True:
                _failsafe += 1
                if _failsafe > 50: break
                pattern = cmd + r'\s*(?:\[[^\]]*\])?\s*\{'
                match = re.search(pattern, tex[search_start:])
                if not match: break
                abs_start = search_start + match.start()
                if cls._is_commented(tex, abs_start):
                    search_start = search_start + match.end()
                    continue
                start_match = abs_start
                start_open = search_start + match.end() - 1
                end_close = cls._find_matching_brace(tex, start_open)
                if end_close != -1:
                    remove_end = end_close + 1
                    while remove_end < len(tex) and tex[remove_end] in (' ', '\t'): remove_end += 1
                    if remove_end < len(tex) and tex[remove_end] == '\n': remove_end += 1
                    tex = tex[:start_match] + tex[remove_end:]
                    search_start = 0
                else: break

        tex = re.sub(r'^[ \t]*\\authornotemark\s*\[[^\]]*\].*$\n?', '', tex, flags=re.MULTILINE)

        if 'metadata.author_block' not in tex:
            # Inject with 5 empty braces for universal arity support
            author_tag = "\n<< metadata.author_block >>{ }{ }{ }{ }{ }\n"
            insert_pos = -1
            match_iter = re.finditer(r'(?i)\\title\s*(?:\[\[^\]]*\])?\s*\{', tex)
            for match in match_iter:
                if cls._is_commented(tex, match.start()): continue
                start_open = match.end() - 1
                end_close = cls._find_matching_brace(tex, start_open)
                if end_close != -1:
                    insert_pos = end_close + 1
                    break
            if insert_pos == -1:
                doc_match = re.search(r'^[ \t]*\\begin\{document\}', tex, re.MULTILINE)
                if doc_match: insert_pos = doc_match.end()

            if insert_pos != -1:
                tex = tex[:insert_pos] + author_tag + tex[insert_pos:]
        return tex

    # ── Phase 5: Abstract ────────────────────────────────────────

    @classmethod
    def _process_abstract(cls, tex: str) -> str:
        env_match = re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}', tex, re.DOTALL)
        if env_match:
            inner_text = env_match.group(1)
            repl = r'\g<1>\n<< metadata.abstract >>\n'
            if r'\keywords' in inner_text: repl += r'\\keywords{<< metadata.keywords_str >>}\n'
            repl += r'\g<2>'
            tex = re.sub(r'(\\begin\{abstract\}).*?(\\end\{abstract\})', repl, tex, flags=re.DOTALL)
            return cls._process_ieee_keywords(tex)

        cmd_match = re.search(r'(?i)\\abstract\s*\{', tex)
        if cmd_match:
            start_open = cmd_match.end() - 1
            end_close = cls._find_matching_brace(tex, start_open)
            if end_close != -1:
                tex = tex[:start_open + 1] + '<< metadata.abstract >>' + tex[end_close:]
                return cls._process_ieee_keywords(tex)

        if '<< metadata.abstract >>' not in tex:
            ab_pos = tex.find('<< metadata.author_block >>')
            if ab_pos != -1:
                nl = tex.find('\n', ab_pos + len('<< metadata.author_block >>'))
                # Phải lùi sau các ngoặc rỗng padding { }{ }{ }{ }{ }
                padding_end = tex.find('}', ab_pos)
                last_brace = tex.find('}', padding_end + 1)
                # Đơn giản nhất là tìm dòng mới tiếp theo sau tag
                insert_pos = nl if nl != -1 else ab_pos + 100
                tex = tex[:insert_pos] + "\n\\begin{abstract}\n<< metadata.abstract >>\n\\end{abstract}\n" + tex[insert_pos:]
        return cls._process_ieee_keywords(tex)

    @classmethod
    def _process_ieee_keywords(cls, tex: str) -> str:
        pattern = r'(\\begin\{IEEEkeywords\}).*?(\\end\{IEEEkeywords\})'
        repl = r'\g<1>\n<< metadata.keywords_str >>\n\g<2>'
        return re.sub(pattern, repl, tex, flags=re.DOTALL)

    # ── Phase 7: Body ────────────────────────────────────────────

    @staticmethod
    def _verbatim_ranges(tex: str) -> list:
        ranges = []
        for m in re.finditer(r'\\verb(.)(.*?)\1', tex, re.DOTALL): ranges.append((m.start(), m.end()))
        for m in re.finditer(r'\\begin\{verbatim\}.*?\\end\{verbatim\}', tex, re.DOTALL): ranges.append((m.start(), m.end()))
        return ranges

    @classmethod
    def _process_body(cls, tex: str) -> str:
        verb_ranges = cls._verbatim_ranges(tex)
        _in_verbatim = lambda pos: any(s <= pos < e for s, e in verb_ranges)
        start_search_patterns = [r'\\maketitle', r'\\end\{abstract\}', r'\\end\{IEEEkeywords\}', r'\\end\{keyword\}', r'\\end\{frontmatter\}']
        body_start = -1
        for p in start_search_patterns:
            matches = [m for m in re.finditer(p, tex) if not _in_verbatim(m.start())]
            if matches:
                pos = matches[-1].end()
                if pos > body_start: body_start = pos
        if body_start == -1:
            doc_match = re.search(r'^[ \t]*\\begin\{document\}', tex, re.MULTILINE)
            if doc_match: body_start = doc_match.end()

        end_search_patterns = [r'\\section\*?\{References\}', r'\\begin\{thebibliography\}', r'\\bibliographystyle\{', r'\\bibliography\{', r'<< references_block >>', r'\\end\{document\}']
        body_end = len(tex)
        for p in end_search_patterns:
            for m in re.finditer(p, tex):
                if _in_verbatim(m.start()): continue
                pos = m.start()
                if pos < body_end and pos > body_start:
                    body_end = pos
                    break
        if body_start != -1 and body_start < body_end:
            region = tex[body_start:body_end]
            adj_matches = list(re.finditer(r'(?:^[ \t]*%[^\n]*\n)*^[ \t]*\\begin\{adjustwidth\}[^\n]*\n', region, re.MULTILINE))
            if adj_matches: body_end = body_start + adj_matches[-1].start()
            tex = tex[:body_start] + "\n\n<< body >>\n\n" + tex[body_end:]
        return tex

    # ── Phase 6: Keywords ────────────────────────────────────────

    @classmethod
    def _process_keywords(cls, tex: str) -> str:
        env_match = re.search(r'\\begin\{keyword\}(.*?)\\end\{keyword\}', tex, re.DOTALL)
        if env_match:
            return tex[:env_match.start()] + r'\begin{keyword}' + '\n<< metadata.keywords_str >>\n' + r'\end{keyword}' + tex[env_match.end():]
        match = re.search(r'(?i)\\keywords\s*\{', tex)
        if match:
            start_open = match.end() - 1
            end_close = cls._find_matching_brace(tex, start_open)
            if end_close != -1: return tex[:start_open + 1] + '<< metadata.keywords_str >>' + tex[end_close:]
        match = re.search(r'(?i)\\keyword(?!s)\s*\{', tex)
        if match:
            start_open = match.end() - 1
            end_close = cls._find_matching_brace(tex, start_open)
            if end_close != -1: return tex[:start_open + 1] + '<< metadata.keywords_str >>' + tex[end_close:]
        return tex

    # ── Phase 8: References ──────────────────────────────────────

    @classmethod
    def _process_references(cls, tex: str) -> str:
        pattern = r'\\begin\{thebibliography\}.*?\\end\{thebibliography\}'
        first_replaced = False
        while True:
            match = re.search(pattern, tex, re.DOTALL)
            if not match: break
            if not first_replaced:
                tex = tex[:match.start()] + '<< references_block >>' + tex[match.end():]
                first_replaced = True
            else: tex = tex[:match.start()] + tex[match.end():]

        for mdpi_cmd in (r'\\isAPAandChicago', r'\\isChicagoStyle', r'\\isAPAStyle'):
            while True:
                m = re.search(mdpi_cmd + r'\s*\{', tex)
                if not m: break
                b1s = m.end() - 1
                b1e = cls._find_matching_brace(tex, b1s)
                if b1e == -1: break
                rest = tex[b1e+1:].lstrip()
                end_pos = b1e + 1
                if rest and rest[0] == '{':
                    offset = b1e + 1 + (tex[b1e+1:].find('{'))
                    b2e = cls._find_matching_brace(tex, offset)
                    if b2e != -1: end_pos = b2e + 1
                if '<< references_block >>' in tex[m.start():end_pos]:
                    tex = tex[:m.start()] + '<< references_block >>' + tex[end_pos:]
                else: tex = tex[:m.start()] + tex[end_pos:]

        ref_match = re.search(r'\\section\*?\s*\{References\}', tex)
        end_doc_match = re.search(r'\\end\{document\}', tex)
        if ref_match and end_doc_match and ref_match.start() < end_doc_match.start():
            tex = tex[:ref_match.start()] + '\n<< references_block >>\n\n' + tex[end_doc_match.start():]

        if '<< references_block >>' not in tex:
            end_docs = list(re.finditer(r'\\end\{document\}', tex))
            end_doc = end_docs[-1] if end_docs else None
            if end_doc:
                bib_styles = [m for m in re.finditer(r'^[ \t]*\\bibliographystyle\{', tex, re.MULTILINE) if m.start() < end_doc.start()]
                bib_cmds = [m for m in re.finditer(r'^[ \t]*\\bibliography\{', tex, re.MULTILINE) if m.start() < end_doc.start()]
                start = (bib_styles[-1].start() if bib_styles else (bib_cmds[-1].start() if bib_cmds else None))
                if start is not None: tex = tex[:start] + '\n<< references_block >>\n\n' + tex[end_doc.start():]
        else:
            tex = re.sub(r'^(\s*)(\\bibliographystyle\{[^}]*\})', r'\1% \2', tex, flags=re.MULTILINE)
            tex = re.sub(r'^(\s*)(\\bibliography\{[^}]*\})', r'\1% \2', tex, flags=re.MULTILINE)
        return tex
