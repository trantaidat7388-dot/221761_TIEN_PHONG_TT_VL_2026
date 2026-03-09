import re

class TemplatePreprocessor:
    """
    Tự động xử lý một file mẫu LaTeX (.tex) tải từ internet (IEEE, ACM, Springer, v.v...)
    bằng cách tiêm các biến Jinja2 (ví dụ: {{ metadata.title }}, {{ body }})
    để tương thích với JinjaLaTeXRenderer.
    """

    @classmethod
    def auto_tag(cls, tex_content: str) -> str:
        tex = cls._ensure_essential_packages(tex_content)
        tex = cls._process_title(tex)
        tex = cls._process_authors(tex)
        tex = cls._process_abstract(tex)
        tex = cls._process_keywords(tex)
        tex = cls._process_references(tex)
        tex = cls._process_body(tex)
        return tex

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
    def _ensure_essential_packages(cls, tex: str) -> str:
        r"""
        FORCE FIX: Chèn block @ifpackageloaded ngay trước \begin{document}.
        Không dùng regex dò tìm. Để LaTeX tự quyết định nạp package hay không.
        Cách này chuẩn xác 100%, không bao giờ gây xung đột.

        Universal compatibility:
        - fontspec: required for XeLaTeX Unicode support (Vietnamese, CJK, etc.)
        - amsmath/amssymb: math packages
        - xurl: URL line-breaking
        - Removes inputenc (pdfLaTeX-only, conflicts with XeLaTeX)
        - Replaces T1/OT1 fontenc with fontspec
        """
        INJECT_BLOCK = (
            "\\makeatletter\n"
            "\\@ifpackageloaded{fontspec}{}{\\usepackage{fontspec}}\n"
            "\\@ifpackageloaded{amsmath}{}{\\usepackage{amsmath}}\n"
            "\\@ifpackageloaded{amssymb}{}{\\usepackage{amssymb}}\n"
            "\\@ifpackageloaded{xurl}{}{\\usepackage{xurl}}\n"
            "\\makeatother\n"
        )

        # XeLaTeX Unicode fix: T1/OT1 fontenc is pdfLaTeX-only; replace with fontspec
        # so Vietnamese (and other Unicode) characters render correctly under XeLaTeX.
        for old_enc in (
            '\\usepackage[T1]{fontenc}',
            '\\usepackage[OT1]{fontenc}',
        ):
            if old_enc in tex:
                tex = tex.replace(
                    old_enc,
                    '\\usepackage{fontspec}  % XeLaTeX: Unicode font support (tiếng Việt)'
                )
                break  # only one encoding package is expected

        # Remove inputenc variants — pdfLaTeX-only, not needed (and sometimes harmful) under XeLaTeX
        tex = re.sub(
            r'^[ \t]*\\usepackage\[[^\]]*\]\{inputenc\}.*$',
            r'% \g<0>  % Removed: XeLaTeX handles UTF-8 natively',
            tex,
            flags=re.MULTILINE,
        )

        # Skip if already injected
        if '@ifpackageloaded{amsmath}' in tex:
            return tex

        target = '\\begin{document}'
        if target not in tex:
            return tex

        return tex.replace(target, INJECT_BLOCK + target, 1)

    @classmethod
    def _process_title(cls, tex: str) -> str:
        """
        Tìm lệnh \title{...} và gán << metadata.title >> vào trong.
        Hỗ trợ nhận dạng \title kể cả khi nó trải qua nhiều dòng.
        """
        match_iter = re.finditer(r'\\title\s*\{', tex)
        for match in match_iter:
            start_open = match.end() - 1
            end_close = cls._find_matching_brace(tex, start_open)
            if end_close != -1:
                # Trích xuất nội dung cần giữ lại như \thanks{} nếu có
                old_content = tex[start_open + 1:end_close]
                thanks_match = re.search(r'\\thanks\s*\{', old_content)
                
                thanks_block = ""
                if thanks_match:
                    thanks_start = thanks_match.start()
                    thanks_open = thanks_start + thanks_match.group().find('{')
                    thanks_close = cls._find_matching_brace(old_content, thanks_open)
                    if thanks_close != -1:
                        thanks_block = old_content[thanks_start:thanks_close + 1]

                # Jinja2 in this system uses custom delimiters: << >> to avoid { } conflict
                # Không giữ \thanks{} từ template vì nó luôn chứa dummy text mẫu
                new_title = r"<< metadata.title >>"

                # Thay thế
                tex = tex[:start_open + 1] + new_title + tex[end_close:]
                break # Chỉ xử lý title đầu tiên
        return tex

    @classmethod
    def _process_authors(cls, tex: str) -> str:
        r"""
        Xóa toàn bộ các khối lệnh tác giả hỗn tạp (\author, \affil, \address, \email, \institute, \IEEEauthorblockN)
        Và chèn 1 dòng << metadata.author_block >> thay thế (chứa mã nguồn LaTeX hoàn chỉnh cho phần tác giả).
        """
        # Định nghĩa các regex blocks cần gỡ bỏ hoàn toàn
        commands_to_remove = [r'\\authorrunning', r'\\titlerunning', r'\\author', r'\\affil', r'\\address', r'\\email', r'\\institute']
        
        for cmd in commands_to_remove:
            while True:
                # Tìm lệnh, có thể theo sau là [options] rồi {
                pattern = cmd + r'(?:\s*\[[^\]]*\])?\s*\{'
                match = re.search(pattern, tex)
                if not match:
                    break
                
                start_match = match.start()
                start_open = match.end() - 1
                end_close = cls._find_matching_brace(tex, start_open)
                
                if end_close != -1:
                    # Gỡ phần lệnh và nội dung đã tìm được
                    tex = tex[:start_match] + tex[end_close + 1:]
                else:
                    break
        
        # Chèn marker author_block vào vị trí hợp lý (thường là sau \title hoặc trước \maketitle)
        # Chỉ chèn nếu chưa có marker
        if '<< metadata.author_block >>' not in tex:
            title_end_pos = -1
            match_iter = re.finditer(r'\\title\s*\{', tex)
            for match in match_iter:
                start_open = match.end() - 1
                end_close = cls._find_matching_brace(tex, start_open)
                if end_close != -1:
                    title_end_pos = end_close + 1
                    break
            
            if title_end_pos != -1:
                tex = tex[:title_end_pos] + "\n<< metadata.author_block >>\n" + tex[title_end_pos:]
        
        return tex

    @classmethod
    def _process_abstract(cls, tex: str) -> str:
        r"""
        Tìm \begin{abstract}...\end{abstract} và thay ruột bằng << metadata.abstract >>.
        Nếu bên trong có chứa \keywords (như template Springer), ta bảo tồn lệnh này.
        """
        # Kiểm tra xem có \keywords bên trong abstract không
        match = re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}', tex, re.DOTALL)
        has_keywords_inside = False
        if match:
            inner_text = match.group(1)
            if r'\keywords' in inner_text:
                has_keywords_inside = True

        pattern = r'(\\begin\{abstract\}).*?(\\end\{abstract\})'
        
        repl = r'\g<1>\n<< metadata.abstract >>\n'
        if has_keywords_inside:
            repl += r'\\keywords{<< metadata.keywords_str >>}\n'
        repl += r'\g<2>'
        
        tex = re.sub(
            pattern,
            repl,
            tex,
            flags=re.DOTALL,
        )
        return cls._process_ieee_keywords(tex)

    @classmethod
    def _process_ieee_keywords(cls, tex: str) -> str:
        """Inject << metadata.keywords_str >> into IEEEkeywords environment."""
        pattern = r'(\\begin\{IEEEkeywords\}).*?(\\end\{IEEEkeywords\})'
        repl = r'\g<1>\n<< metadata.keywords_str >>\n\g<2>'
        return re.sub(pattern, repl, tex, flags=re.DOTALL)

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
        # dùng \begin{document} làm điểm bắt đầu
        if body_start == -1:
            doc_match = re.search(r'\\begin\{document\}', tex)
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

    @classmethod
    def _process_keywords(cls, tex: str) -> str:
        r"""Inject << metadata.keywords_str >> into \keywords{} command (Springer format)."""
        match = re.search(r'\\keywords\s*\{', tex)
        if match:
            start_open = match.end() - 1
            end_close = cls._find_matching_brace(tex, start_open)
            if end_close != -1:
                tex = tex[:start_open + 1] + '<< metadata.keywords_str >>' + tex[end_close:]
        return tex

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
