import re

class TemplatePreprocessor:
    """
    Universal LaTeX template preprocessor for Jinja2 tagging.
    Supports: IEEE, ACM, Springer (LLNCS), Elsevier, MDPI, and generic templates.
    Injects Jinja2 variables (e.g. << metadata.title >>, << body >>)
    using custom delimiters << >> to avoid { } conflict.
    """

    @classmethod
    def auto_tag(cls, tex_content: str) -> str:
        tex = cls._ensure_essential_packages(tex_content)
        
        # ── Hỗ trợ Tiếng Việt (fontspec cho XeLaTeX - chỉ fallback nếu chưa có font) ──
        if r'\setmainfont' not in tex and r'\usepackage{fontspec}' not in tex:
            # Ta dùng fontspec nhưng không ép cứng font nếu không cần thiết để tránh crash do thiếu font hệ thống
            font_patch = r"\usepackage{fontspec}" + "\n" + r"% \setmainfont{Times New Roman} % Bỏ comment nếu muốn ép dùng font này" + "\n"
            # Chèn sau documentclass
            tex = re.sub(r'(\\documentclass\b.*?\]?\{.*?\})', r'\1' + '\n' + font_patch.replace('\\', '\\\\'), tex)

        # ── Vá lỗi apacite: \onemaskedcitationmsg + \maskedcitationsmsg undefined ──
        if r'\onemaskedcitationmsg' not in tex:
            patch = r"\providecommand{\onemaskedcitationmsg}[1]{}" + "\n" + r"\providecommand{\maskedcitationsmsg}[1]{}" + "\n"
            tex = re.sub(r'(\\begin\{document\})', patch.replace('\\', '\\\\') + r'\1', tex)
        
        # BẮT BUỘC dùng TexSoup cho các node metadata chính để tránh lỗi rớt ngoặc
        try:
            from TexSoup import TexSoup
            soup = TexSoup(tex)
            
            # 1. Xử lý Title
            titles = list(soup.find_all('title')) + list(soup.find_all('Title'))
            for t in titles:
                if t.args:
                    for arg in reversed(t.args):
                        if hasattr(arg, 'contents'):
                            arg.contents = ['<< metadata.title >>']
                            break
            
            # 2. Xử lý Author & Affiliations (Robust Deletion + Arity Padding for jov/acmart/generic)
            # Tìm vị trí author đầu tiên để chèn tag lên trước
            author_nodes = list(soup.find_all('author')) + list(soup.find_all('Author'))
            if author_nodes:
                print(f"[*] TexSoup found {len(author_nodes)} author nodes. Revamping injection...")
                first_author = author_nodes[0]
                
                # --- ARITY DETECTION (Fix Argument Gobbling) ---
                extra_braces_count = 0
                parent = first_author.parent
                if parent:
                    try:
                        contents = list(parent.contents)
                        # Tìm vị trí node author đầu tiên trong danh sách contents của parent
                        idx = -1
                        for i, item in enumerate(contents):
                            if item == first_author:
                                idx = i
                                break
                        
                        if idx != -1:
                            to_delete_extra = []
                            # Duyệt các sibling đứng sau để tìm các BraceGroup rời rạc (ví dụ: \author{N}{Aff}{URL}{Email})
                            for i in range(idx + 1, len(contents)):
                                sibling = contents[i]
                                s_sibling = str(sibling).strip()
                                if not s_sibling: continue # Bỏ qua khoảng trắng/xuống dòng
                                
                                # Nếu sibling bắt đầu bằng { và kết thúc bằng } và KHÔNG phải là lệnh (không bắt đầu bằng \)
                                if s_sibling.startswith('{') and s_sibling.endswith('}') and not s_sibling.startswith('\\'):
                                    print(f"[*] Detected trailing argument (gobbling risk): {s_sibling}")
                                    extra_braces_count += 1
                                    to_delete_extra.append(sibling)
                                else:
                                    # Gặp lệnh khác hoặc text thường thì dừng lại
                                    break
                            
                            # Xóa các tham số thừa để dọn đường cho tag mới
                            for item in to_delete_extra:
                                try: item.delete()
                                except: pass
                    except Exception as e:
                        print(f"[!] Warning: Arity detection failed: {e}")

                # Bù đắp số ngoặc nhọn để thỏa mãn signature của macro (ví dụ jov.cls yêu cầu 4 tham số)
                padding = "{}" * extra_braces_count
                first_author.insert_before(f'<< metadata.author_block >>{padding}\n')
                print(f"[*] TexSoup inserted author_block tag with padding: {padding}")

            # Xóa sạch toàn bộ các node metadata cũ
            related_cmds = ['author', 'Author', 'affil', 'affiliation', 'address', 'email', 'institute', 
                            'authornote', 'orcid', 'corres', 'firstnote', 'AuthorNames', 
                            'authorrunning', 'titlerunning']
            for cmd in related_cmds:
                nodes = soup.find_all(cmd)
                for node in nodes:
                    try: node.delete()
                    except: pass
            print("[*] TexSoup deleted all legacy author/affiliation nodes.")

            # 3. Xử lý Abstract
            abstracts = list(soup.find_all('abstract')) + list(soup.find_all('Abstract'))
            for ab in abstracts:
                # Nếu là command \abstract{...}
                if ab.args:
                    for arg in reversed(ab.args):
                        if hasattr(arg, 'contents'):
                            arg.contents = ['<< metadata.abstract >>']
                            print("[*] TexSoup tagged abstract command.")
                            break
                else:
                    # Nếu là environment \begin{abstract}...\end{abstract}
                    # Ta thay thế toàn bộ nội dung trong begin/end
                    ab.replace_with('\\begin{abstract}\n<< metadata.abstract >>\n\\end{abstract}')
                    print("[*] TexSoup tagged abstract environment.")

            # 4. Xử lý Keywords
            for cmd in ['keywords', 'keyword', 'IEEEkeywords', 'IndexTerms']:
                for kw in soup.find_all(cmd):
                    if kw.args:
                        for arg in reversed(kw.args):
                            if hasattr(arg, 'contents'):
                                arg.contents = ['<< metadata.keywords_str >>']
                                print(f"[*] TexSoup tagged {cmd} command.")
                                break
                    else:
                        kw.replace_with(f'\\begin{{{cmd}}}\n<< metadata.keywords_str >>\n\\end{{{cmd}}}')
                        print(f"[*] TexSoup tagged {cmd} environment.")

            tex = str(soup)
            print("[*] TexSoup tagging hoàn tất cho metadata.")
            
        except Exception as e:
            print(f"[WARN] TexSoup thất bại ({e}), đang dùng Regex fallback an toàn...")
            tex = cls._cleanup_publisher_metadata(tex)
            tex = cls._process_title(tex)
            tex = cls._process_authors(tex)
            tex = cls._process_abstract(tex)
            tex = cls._process_keywords(tex)

        # MỤC 4: Logic Body và References vẫn dùng Regex (ổn định hơn cho việc "quét sạch" dummy text)
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
        # xcolor & hyperref options are already handled via \PassOptionsToPackage before
        # \documentclass, so we only need bare \usepackage guards here.
        # hyperref is NOT force-loaded: many publisher classes (MDPI, ACM, Springer)
        # load it themselves with specific options; forcing it causes option clashes.
        # fontspec is NOT injected here: classes that use fontenc (MDPI, etc.) conflict
        # with fontspec's TU encoding. The fontenc→fontspec replacement in the preamble
        # (above) already handles templates that explicitly load fontenc in their body.
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
            # Preamble was already processed before; still guarantee xcolor is ensured.
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

        # Match only non-commented \begin{document} (avoid % comment matches)
        doc_match = re.search(r'^[ \t]*\\begin\{document\}', tex, re.MULTILINE)
        if not doc_match:
            return tex

        pos = doc_match.start()
        return tex[:pos] + INJECT_BLOCK + tex[pos:]

    # ── Phase 2: Publisher metadata cleanup ───────────────────────

    @classmethod
    def _cleanup_publisher_metadata(cls, tex: str) -> str:
        """Remove publisher-specific metadata that won't be populated from Word input."""
        # ── ACM ──
        # CCSXML block
        tex = re.sub(
            r'\\begin\{CCSXML\}.*?\\end\{CCSXML\}\s*\n?',
            '', tex, flags=re.DOTALL,
        )
        # \ccsdesc[...]{...}
        tex = cls._remove_command(tex, r'\\ccsdesc')
        # Publisher metadata commands (multi-arg: \acmConference[...]{...}{...}{...})
        for cmd in ('acmConference', 'acmBooktitle', 'acmDOI', 'acmYear',
                     'acmISBN', 'acmPrice', 'acmSubmissionID',
                     'setcopyright', 'copyrightyear'):
            tex = cls._remove_command(tex, r'\\' + cmd, multi_brace=True)
        # \begin{teaserfigure}...\end{teaserfigure}
        tex = re.sub(
            r'\\begin\{teaserfigure\}.*?\\end\{teaserfigure\}\s*\n?',
            '', tex, flags=re.DOTALL,
        )
        # \renewcommand{\shortauthors}{...}
        tex = re.sub(
            r'^[ \t]*\\renewcommand\s*\{\\shortauthors\}\s*\{[^}]*\}.*$\n?',
            '', tex, flags=re.MULTILINE,
        )

        # ── MDPI ──
        # \AuthorNames{...} (redundant with \Author)
        tex = cls._remove_command(tex, r'\\AuthorNames')
        # Correspondence, review metadata (corres/firstnote handled in _process_authors)
        for cmd in ('secondnote', 'thirdnote',
                     'fourthnote', 'fifthnote', 'sixthnote', 'seventhnote', 'eighthnote',
                     'institutionalreview', 'dataavailability',
                     'conflictsofinterest', 'sampleavailability',
                     'authorcontributions', 'funding',
                     'abbreviations', 'appendixtitles'):
            tex = cls._remove_command(tex, r'\\' + cmd)

        # ── Elsevier (elsarticle) ──
        # The authoryear option enables natbib author-year mode, which requires
        # \bibitem[Author(Year)]{key} format.  Our renderer generates plain
        # \bibitem{key} (numeric), so switch to numbered citations.
        if re.search(r'\\documentclass\b[^}]*\{elsarticle\}', tex):
            # Only touch the first uncommented \documentclass line
            tex = re.sub(
                r'^([^%\n]*\\documentclass\s*\[)([^\]]*)\]',
                lambda m: m.group(1) + m.group(2).replace('authoryear', 'number') + ']',
                tex, count=1, flags=re.MULTILINE,
            )
            # Also switch harv bibliography style to numeric
            tex = re.sub(
                r'(\\bibliographystyle\{)elsarticle-harv(\})',
                r'\1elsarticle-num\2',
                tex,
            )
            # Remove \journal{...} — not populated from Word
            tex = cls._remove_command(tex, r'\\journal')
            # Remove Elsevier-specific frontmatter elements not populated from Word
            for cmd in ('tnotetext', 'fntext', 'cortext', 'ead'):
                tex = cls._remove_command(tex, r'\\' + cmd)
            # Remove graphicalabstract and highlights environments
            tex = re.sub(
                r'[ \t]*\\begin\{graphicalabstract\}.*?\\end\{graphicalabstract\}\s*',
                '', tex, flags=re.DOTALL,
            )
            tex = re.sub(
                r'[ \t]*\\begin\{highlights\}.*?\\end\{highlights\}\s*',
                '', tex, flags=re.DOTALL,
            )

        # ── MDPI first‑page left‑column overlap fix ──
        # In submit mode the class places dates + copyright as a marginnote on
        # page 1.  With long body text the note overlaps content.
        # Fix: redefine \contentleftcolumn to empty so the marginnote is blank.
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
        r"""
        Replace content of \title{...} or \Title{...} with << metadata.title >>.
        Case-insensitive to support MDPI's \Title{} and standard \title{}.
        Handles optional args: \title[short title]{full title}.
        Skips commented-out occurrences.
        """
        match_iter = re.finditer(r'(?i)\\title\s*(?:\[\[^\]]*\])?\s*\{', tex)
        for match in match_iter:
            if cls._is_commented(tex, match.start()):
                continue
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
        Remove all author-related commands and inject << metadata.author_block >>.
        Supports IEEE, ACM, Springer, MDPI, Elsevier formats.

        Case-insensitive for \author / \Author (MDPI) and \address / \Address.
        """
        commands_to_remove = [
            r'\\authorrunning', r'\\titlerunning',
            r'(?i)\\author(?!Names|note|mark|contributions)',  # \author/\Author but not \AuthorNames etc.
            r'(?i)\\affil(?:iation)?',   # \affil (Springer), \affiliation (ACM)
            r'(?i)\\address',
            r'\\email',
            r'\\institute',
            r'\\authornote',             # ACM
            r'\\orcid',                  # ACM
            r'\\corres',                 # MDPI
            r'\\firstnote',              # MDPI
        ]

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
                    remove_end = end_close + 1
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
            match_iter = re.finditer(r'(?i)\\title\s*(?:\[\[^\]]*\])?\s*\{', tex)
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
                # Inject with 5 empty braces for universal arity support (Regex Fallback)
                author_tag = "\n<< metadata.author_block >>{ }{ }{ }{ }{ }\n"
                tex = tex[:insert_pos] + author_tag + tex[insert_pos:]

        return tex

    # ── Phase 5: Abstract ────────────────────────────────────────

    @classmethod
    def _process_abstract(cls, tex: str) -> str:
        r"""
        Replace abstract content with << metadata.abstract >>.

        Supports:
        - \begin{abstract}...\end{abstract} (IEEE, ACM, Springer, Elsevier)
        - \abstract{...} (MDPI command form)
        - Fallback: inject abstract block if neither is found.
        """
        # Pattern 1: Environment form \begin{abstract}...\end{abstract}
        env_match = re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}', tex, re.DOTALL)
        if env_match:
            inner_text = env_match.group(1)
            has_keywords_inside = r'\keywords' in inner_text

            repl = r'\g<1>\n<< metadata.abstract >>\n'
            if has_keywords_inside:
                repl += r'\\keywords{<< metadata.keywords_str >>}\n'
            repl += r'\g<2>'

            tex = re.sub(
                r'(\\begin\{abstract\}).*?(\\end\{abstract\})',
                repl, tex, flags=re.DOTALL,
            )
            return cls._process_ieee_keywords(tex)

        # Pattern 2: Command form \abstract{...} (MDPI) — case-insensitive
        cmd_match = re.search(r'(?i)\\abstract\s*\{', tex)
        if cmd_match:
            start_open = cmd_match.end() - 1
            end_close = cls._find_matching_brace(tex, start_open)
            if end_close != -1:
                tex = tex[:start_open + 1] + '<< metadata.abstract >>' + tex[end_close:]
                return cls._process_ieee_keywords(tex)

        # Fallback: inject abstract block after author_block or after \begin{document}
        if '<< metadata.abstract >>' not in tex:
            ab_pos = tex.find('<< metadata.author_block >>')
            if ab_pos != -1:
                # Insert after the author_block line
                nl = tex.find('\n', ab_pos + len('<< metadata.author_block >>'))
                insert_pos = nl if nl != -1 else ab_pos + len('<< metadata.author_block >>')
                tex = (tex[:insert_pos] +
                       "\n\\begin{abstract}\n<< metadata.abstract >>\n\\end{abstract}\n" +
                       tex[insert_pos:])
            else:
                doc_match = re.search(r'^[ \t]*\\begin\{document\}', tex, re.MULTILINE)
                if doc_match:
                    insert_pos = doc_match.end()
                    tex = (tex[:insert_pos] +
                           "\n\\begin{abstract}\n<< metadata.abstract >>\n\\end{abstract}\n" +
                           tex[insert_pos:])

        return cls._process_ieee_keywords(tex)

    @classmethod
    def _process_ieee_keywords(cls, tex: str) -> str:
        """Inject << metadata.keywords_str >> into IEEEkeywords environment."""
        pattern = r'(\\begin\{IEEEkeywords\}).*?(\\end\{IEEEkeywords\})'
        repl = r'\g<1>\n<< metadata.keywords_str >>\n\g<2>'
        return re.sub(pattern, repl, tex, flags=re.DOTALL)

    # ── Phase 7: Body ────────────────────────────────────────────

    @staticmethod
    def _verbatim_ranges(tex: str) -> list:
        """Return list of (start, end) char ranges that are inside verbatim contexts.

        Covers \\verb|...|  (any delimiter) and \\begin{verbatim}...\\end{verbatim}.
        """
        ranges = []
        # \verb<delim>...<delim>
        for m in re.finditer(r'\\verb(.)(.*?)\1', tex, re.DOTALL):
            ranges.append((m.start(), m.end()))
        # \begin{verbatim}...\end{verbatim}
        for m in re.finditer(r'\\begin\{verbatim\}.*?\\end\{verbatim\}', tex, re.DOTALL):
            ranges.append((m.start(), m.end()))
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
    def _process_keywords(cls, tex: str) -> str:
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
                bib_style = bib_styles[-1] if bib_styles else None
                bib_cmd = bib_cmds[-1] if bib_cmds else None
                start = bib_style.start() if bib_style else (bib_cmd.start() if bib_cmd else None)
                if start is not None:
                    tex = tex[:start] + '\n<< references_block >>\n\n' + tex[end_doc.start():]
        else:
            # references_block already exists — just comment out the commands
            tex = re.sub(r'^(\s*)(\\bibliographystyle\{[^}]*\})', r'\1% \2', tex, flags=re.MULTILINE)
            tex = re.sub(r'^(\s*)(\\bibliography\{[^}]*\})', r'\1% \2', tex, flags=re.MULTILINE)

        return tex
