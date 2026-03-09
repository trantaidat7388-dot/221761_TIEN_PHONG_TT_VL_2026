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
        tex = cls._cleanup_publisher_metadata(tex)
        tex = cls._process_title(tex)
        tex = cls._process_authors(tex)
        tex = cls._process_abstract(tex)
        tex = cls._process_keywords(tex)
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
        while True:
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

    # ── Phase 1: Essential packages ───────────────────────────────

    @classmethod
    def _ensure_essential_packages(cls, tex: str) -> str:
        r"""
        Ensure essential packages for XeLaTeX compilation.

        Strategy:
        1. \PassOptionsToPackage{table,xcdraw}{xcolor} BEFORE \documentclass
           — prevents option clash with cls files (MDPI, ACM) that load xcolor internally.
        2. Remove pdftex/pdflatex driver hints from \documentclass options
           — XeLaTeX auto-detects the correct driver; leftover hints cause errors.
        3. Replace T1/OT1 fontenc with fontspec; comment out inputenc.
        4. Inject @ifpackageloaded guards before \begin{document}.
           Package options are pre-set via \PassOptionsToPackage so the guards
           use bare \usepackage{pkg} — no option clash regardless of loading order.
        """
        # Skip if already injected
        if '\\PassOptionsToPackage{table,xcdraw}{xcolor}' in tex:
            return tex

        # ── Before \documentclass ──
        PASS_OPTIONS = "\\PassOptionsToPackage{table,xcdraw}{xcolor}\n"
        dc_match = re.search(r'^[ \t]*\\documentclass', tex, re.MULTILINE)
        if dc_match:
            tex = tex[:dc_match.start()] + PASS_OPTIONS + tex[dc_match.start():]

        # Remove pdftex/pdflatex from \documentclass options (XeLaTeX does not need driver hints)
        dc_opts = re.search(r'(\\documentclass\s*\[)([^\]]*)(\])', tex)
        if dc_opts:
            opts = dc_opts.group(2)
            opt_list = [o.strip() for o in opts.split(',')]
            opt_list = [o for o in opt_list if o.lower() not in ('pdftex', 'pdflatex')]
            new_opts = ', '.join(opt_list)
            tex = tex[:dc_opts.start(2)] + new_opts + tex[dc_opts.end(2):]

        # ── fontenc / inputenc handling ──
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
        # Options for xcolor are pre-set above via \PassOptionsToPackage,
        # so the guard here uses bare \usepackage{xcolor}.
        # hyperref: no forced options — let each template decide its own style.
        INJECT_BLOCK = (
            "\\makeatletter\n"
            "\\@ifpackageloaded{fontspec}{}{\\usepackage{fontspec}}\n"
            "\\@ifpackageloaded{amsmath}{}{\\usepackage{amsmath}}\n"
            "\\@ifpackageloaded{amssymb}{}{\\usepackage{amssymb}}\n"
            "\\@ifpackageloaded{xurl}{}{\\usepackage{xurl}}\n"
            "\\@ifpackageloaded{xcolor}{}{\\usepackage{xcolor}}\n"
            "\\@ifpackageloaded{graphicx}{}{\\usepackage{graphicx}}\n"
            "\\@ifpackageloaded{hyperref}{}{\\usepackage[hidelinks]{hyperref}}\n"
            "\\makeatother\n"
        )

        if '@ifpackageloaded{amsmath}' in tex:
            return tex

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

        return tex

    # ── Phase 3: Title ──────────────────────────────────────────

    @classmethod
    def _process_title(cls, tex: str) -> str:
        r"""
        Replace content of \title{...} or \Title{...} with << metadata.title >>.
        Case-insensitive to support MDPI's \Title{} and standard \title{}.
        Handles optional args: \title[short title]{full title}.
        """
        match_iter = re.finditer(r'(?i)\\title\s*(?:\[[^\]]*\])?\s*\{', tex)
        for match in match_iter:
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
            while True:
                pattern = cmd + r'\s*(?:\[[^\]]*\])?\s*\{'
                match = re.search(pattern, tex)
                if not match:
                    break
                start_match = match.start()
                start_open = match.end() - 1
                end_close = cls._find_matching_brace(tex, start_open)
                if end_close != -1:
                    remove_end = end_close + 1
                    while remove_end < len(tex) and tex[remove_end] in (' ', '\t'):
                        remove_end += 1
                    if remove_end < len(tex) and tex[remove_end] == '\n':
                        remove_end += 1
                    tex = tex[:start_match] + tex[remove_end:]
                else:
                    break

        # Remove commands with only optional args (no required brace): \authornotemark[1]
        tex = re.sub(r'^[ \t]*\\authornotemark\s*\[[^\]]*\].*$\n?', '', tex, flags=re.MULTILINE)

        # Inject << metadata.author_block >> after \title{...} if not already present
        if '<< metadata.author_block >>' not in tex:
            insert_pos = -1

            # Try: after \title{...}
            match_iter = re.finditer(r'(?i)\\title\s*(?:\[[^\]]*\])?\s*\{', tex)
            for match in match_iter:
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
                tex = tex[:insert_pos] + "\n<< metadata.author_block >>\n" + tex[insert_pos:]

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
            matches = list(re.finditer(p, tex))
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
            match = re.search(p, tex)
            if match:
                pos = match.start()
                if pos < body_end and pos > body_start:
                    body_end = pos

        if body_start != -1 and body_start < body_end:
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
        """
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
        # Bước 1: Thay thế \begin{thebibliography}...\end{thebibliography}
        pattern = r'\\begin\{thebibliography\}.*?\\end\{thebibliography\}'
        match = re.search(pattern, tex, re.DOTALL)
        if match:
            tex = tex[:match.start()] + '<< references_block >>' + tex[match.end():]

        # Bước 2: Nếu có \section*{References}, xóa TOÀN BỘ nội dung từ đó đến \end{document}
        # (bao gồm dummy guidance text, \color{red} warning, v.v.) và chỉ giữ references_block
        ref_match = re.search(r'\\section\*?\s*\{References\}', tex)
        end_doc_match = re.search(r'\\end\{document\}', tex)
        if ref_match and end_doc_match and ref_match.start() < end_doc_match.start():
            tex = tex[:ref_match.start()] + '\n<< references_block >>\n\n' + tex[end_doc_match.start():]

        # Bước 3: Comment out \bibliographystyle{} and \bibliography{} since we use thebibliography
        tex = re.sub(r'^(\s*)(\\bibliographystyle\{[^}]*\})', r'\1% \2', tex, flags=re.MULTILINE)
        tex = re.sub(r'^(\s*)(\\bibliography\{[^}]*\})', r'\1% \2', tex, flags=re.MULTILINE)

        return tex

if __name__ == "__main__":
    # Test quickly
    sample = r'''
    \documentclass{IEEEtran}
    \title{This is a fake title \thanks{Sponsor A}}
    \author{\IEEEauthorblockN{Alice} \and \IEEEauthorblockN{Bob}}
    \begin{document}
    \maketitle
    \begin{abstract}
    This is old abstract text that will be deleted.
    \end{abstract}
    \begin{IEEEkeywords}
    Key, Words
    \end{IEEEkeywords}
    \section{Intro}
    Blah blah
    \begin{thebibliography}{1}
    \bibitem{a} ref a
    \end{thebibliography}
    \end{document}
    '''
    
    print("BEFORE:\n", sample)
    print("\nAFTER:\n", TemplatePreprocessor.auto_tag(sample))
