# utils.py - Tiện ích: escape ký tự, biên dịch LaTeX, dọn file rác

import os
import re
import subprocess
import time
import zipfile
import shutil
import tempfile


def _lay_so_nguyen_tu_env(name: str, default: int, min_value: int = 1) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError:
        value = default
    return max(min_value, value)


LATEX_COMPILE_TIMEOUT_SECONDS = _lay_so_nguyen_tu_env("LATEX_COMPILE_TIMEOUT_SECONDS", 30, min_value=5)

def sua_docx_co_macro(doc_path: str):
    """
    Tẩy rửa file Word có chứa Macro (.docm hoặc .docx dính macro):
    - Mở file dưới dạng ZIP, sửa [Content_Types].xml (content type macro → chuẩn).
    - Sửa các file .rels để loại bỏ các Relationship tới macro.
    - Xóa file cũ và đổi tên file ZIP mới thành doc_path để python-docx mở được.
    """
    if not os.path.isfile(doc_path):
        return
    try:
        dir_path = os.path.dirname(os.path.abspath(doc_path))
        base_name = os.path.basename(doc_path)
        new_zip_path = os.path.join(dir_path, base_name + ".tmp_cleaned.docx")

        with zipfile.ZipFile(doc_path, 'r') as zin:
            with zipfile.ZipFile(new_zip_path, 'w', zipfile.ZIP_DEFLATED) as zout:
                for item in zin.infolist():
                    fn_lower = item.filename.lower()
                    # Bỏ qua file VBA macro
                    if 'vbaproject.bin' in fn_lower or 'vbadata.xml' in fn_lower:
                        continue

                    content = zin.read(item.filename)
                    
                    # Sửa [Content_Types].xml (MIME types)
                    if item.filename == '[Content_Types].xml':
                        content_str = content.decode('utf-8', errors='ignore')
                        content_str = content_str.replace(
                            'application/vnd.ms-word.document.macroEnabled.main+xml',
                            'application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml'
                        )
                        # Loại bỏ Override cho vbaProject / vbaData
                        content_str = re.sub(
                            r'<Override[^>]*(?:vbaProject|vbaData)[^>]*/>', '', content_str
                        )
                        content = content_str.encode('utf-8')
                        
                    # Sửa các file quan hệ (.rels) để xóa liên kết tới macro
                    elif fn_lower.endswith('.rels'):
                        content_str = content.decode('utf-8', errors='ignore')
                        # Regex xóa tag Relationship nếu Target chứa vbaProject hoặc vbaData
                        content_str = re.sub(
                            r'<Relationship[^>]*Target="[^"]*(?:vbaProject|vbaData)[^"]*"[^>]*/>', 
                            '', content_str
                        )
                        # Cũng xóa Relationship dựa trên Type nếu Target không bắt được
                        content_str = re.sub(
                            r'<Relationship[^>]*Type="[^"]*vbaProject"[^>]*/>',
                            '', content_str
                        )
                        content = content_str.encode('utf-8')

                    zout.writestr(item, content)

        os.remove(doc_path)
        os.rename(new_zip_path, doc_path)
        print(f"[INFO] Tẩy rửa macro thành công cho {doc_path}")
    except Exception as e:
        print(f"[WARN] Lỗi khi tẩy rửa macro cho {doc_path}: {e}")

def loc_ky_tu(text: str) -> str:
    # Escape các ký tự đặc biệt LaTeX (\, %, $, _, &, #, {, }, ~, ^)
    if not text:
        return ""
    
    # BƯỚC 1: Thay Unicode bằng PLACEHOLDER trước khi escape ký tự đặc biệt
    # Placeholder dùng ASCII thuần túy, không chứa ký tự LaTeX đặc biệt
    unicode_placeholders = [
        ('\u00BD', 'UNIPHxFRAC12x', r'\ensuremath{\frac{1}{2}}'),
        ('\u00BC', 'UNIPHxFRAC14x', r'\ensuremath{\frac{1}{4}}'),
        ('\u00BE', 'UNIPHxFRAC34x', r'\ensuremath{\frac{3}{4}}'),
        ('\u00D7', 'UNIPHxTIMESx', r'\ensuremath{\times}'),
        ('\u00F7', 'UNIPHxDIVx', r'\ensuremath{\div}'),
        ('\u00B0', 'UNIPHxDEGx', r'\ensuremath{^{\circ}}'),
        ('\u00B1', 'UNIPHxPMx', r'\ensuremath{\pm}'),
        ('\u2265', 'UNIPHxGEQx', r'\ensuremath{\geq}'),
        ('\u2264', 'UNIPHxLEQx', r'\ensuremath{\leq}'),
        ('\u2260', 'UNIPHxNEQx', r'\ensuremath{\neq}'),
        ('\u2248', 'UNIPHxAPPROXx', r'\ensuremath{\approx}'),
        ('\u2192', 'UNIPHxRARRx', r'\ensuremath{\rightarrow}'),
        ('\u2190', 'UNIPHxLARRx', r'\ensuremath{\leftarrow}'),
        ('\u2022', 'UNIPHxBULLETx', r'\ensuremath{\bullet}'),
    ]
    # Ký tự Unicode thay thẳng (không cần placeholder)
    simple_unicode = [
        ('\u2014', '---'),   # em dash
        ('\u2013', '--'),    # en dash
        ('\u2018', "'"),     # Left single quote
        ('\u2019', "'"),     # Right single quote
        ('\u201C', "``"),    # Left double quote
        ('\u201D', "''"),    # Right double quote
        ('\u2026', '...'),   # ellipsis
    ]
    
    ket_qua = text
    
    # Thay Unicode đơn giản trước
    for ky_tu_u, thay_the_u in simple_unicode:
        ket_qua = ket_qua.replace(ky_tu_u, thay_the_u)
    
    # Thay Unicode phức tạp bằng placeholder ASCII
    for ky_tu_u, placeholder, _ in unicode_placeholders:
        ket_qua = ket_qua.replace(ky_tu_u, placeholder)
    
    # BƯỚC 2: Escape ký tự đặc biệt LaTeX (Dùng Regex an toàn, tránh double-escape)
    import re
    
    def replacer(match):
        char = match.group(0)
        mapping = {
            '\\': r'\textbackslash{}',
            '%': r'\%',
            '$': r'\$',
            '_': r'\_',
            '&': r'\&',
            '#': r'\#',
            '{': r'\{',
            '}': r'\}',
            '~': r'\textasciitilde{}',
            '^': r'\textasciicircum{}',
        }
        return mapping.get(char, char)

    # Dùng Negative Lookbehind (?<!\\) để bỏ qua các ký tự đã được escape bằng dấu \
    # Pattern bao quát cả 10 ký tự đặc biệt: \ % $ _ & # { } ~ ^
    pattern = r'(?<!\\)[\\%$_&#{}~^]'
    ket_qua = re.sub(pattern, replacer, ket_qua)
    
    # BƯỚC 3: Thay placeholder lại thành LaTeX command thật
    for _, placeholder, latex_cmd in unicode_placeholders:
        ket_qua = ket_qua.replace(placeholder, latex_cmd)
        
    # Tự động bọc URL vào thẻ \url{} để tránh lỗi tràn lề (overflow) trong PDF
    # Bỏ qua nếu URL đã nằm trong \url{...} hoặc \href{...}
    import re
    # Pattern tìm URL không nằm trong cấu trúc LaTeX URL
    url_pattern = r'(?<!\\url\{)(?<!\\href\{)(https?://[^\s<>"]+)'
    
    # Hàm con hỗ trợ việc thay thế với điều kiện an toàn
    def thay_the_url(match):
        url = match.group(1)
        # Loại bỏ các dấu câu thừa phần cuối URL nếu có
        url_sach = url.rstrip('.,;:\')]}')
        duoi_bi_cat = url[len(url_sach):]
        # Phục hồi các ký tự escape LaTeX đặc biệt trong URL để \url{} xử lý đúng
        url_nguyen_thuy = url_sach.replace(r'\_', '_').replace(r'\&', '&').replace(r'\%', '%').replace(r'\#', '#')
        return rf'\url{{{url_nguyen_thuy}}}' + duoi_bi_cat

    ket_qua = re.sub(url_pattern, thay_the_url, ket_qua)
    
    return ket_qua

def don_dep_file_rac(duong_dan_dau_ra: str):
    # Xóa các file phụ sinh ra từ quá trình biên dịch LaTeX
    base_name = os.path.splitext(duong_dan_dau_ra)[0]
    cac_duoi_rac = [
        '.aux', '.log', '.out', '.toc',
        '.fdb_latexmk', '.fls', '.synctex.gz',
    ]
    for duoi in cac_duoi_rac:
        file_rac = base_name + duoi

        if not os.path.exists(file_rac):
            continue

        da_xoa = xoa_file_an_toan(file_rac)
        if da_xoa:
            print(f"Đã xóa: {file_rac}")


def xoa_file_an_toan(duong_dan_file: str, so_lan_thu: int = 3, thoi_gian_cho_ms: int = 100) -> bool:
    # Xóa file an toàn có retry để tránh lỗi file đang bị hệ thống khóa
    for lan in range(max(1, so_lan_thu)):
        try:
            if os.path.exists(duong_dan_file):
                os.remove(duong_dan_file)
            return True
        except PermissionError as e:
            print(f"Không thể xóa (đang bị khóa): {duong_dan_file} ({e})")
            time.sleep(max(0, thoi_gian_cho_ms) / 1000.0)
        except Exception as e:
            print(f"Không thể xóa file: {duong_dan_file} ({e})")
            return False
    return False

def phat_hien_engine(duong_dan_tex: str) -> str:
    """Phát hiện LaTeX engine phù hợp dựa trên nội dung file .tex."""
    try:
        with open(duong_dan_tex, 'r', encoding='utf-8', errors='ignore') as f:
            first_line = f.readline().strip()
            # 🛡️ Ưu tiên 1: Đọc dòng đầu tiên xem có Magic Comment không
            match = re.search(r'^%\s*!TeX\s+program\s*=\s*(xelatex|pdflatex|lualatex)', first_line, re.IGNORECASE)
            if match:
                return match.group(1).lower()

        # Đọc lại nội dung để phân tích fallback
        with open(duong_dan_tex, 'r', encoding='utf-8', errors='ignore') as f:
            noi_dung = f.read(5000)
            
        # 🛡️ Fallback: Các gói bắt buộc phải dùng XeLaTeX/LuaLaTeX
        if re.search(r'\\usepackage\{fontspec\}', noi_dung) or \
           re.search(r'\\usepackage\{unicode-math\}', noi_dung) or \
           re.search(r'\\usepackage\{polyglossia\}', noi_dung):
            return 'xelatex'
            
        # 🛡️ Fallback: Nếu thấy tùy chọn pdftex trong documentclass
        if re.search(r'^[^%]*\\documentclass\[.*?pdftex', noi_dung, re.MULTILINE):
            return 'pdflatex'
            
    except Exception:
        pass
    
    return 'xelatex' # Mặc định an toàn cho Unicode


def bien_dich_latex(duong_dan_dau_ra: str, thu_muc_bien_dich: str = None, engine: str = None) -> tuple[bool, str]:
    """Biên dịch file .tex, trả về (thành_công, thông_báo_lỗi).
    
    engine: 'xelatex' hoặc 'pdflatex'. Nếu None sẽ tự phát hiện.
    thu_muc_bien_dich: override thư mục cwd (quan trọng cho ZIP template).
    """
    ten_file = os.path.basename(duong_dan_dau_ra)
    thu_muc = thu_muc_bien_dich or os.path.dirname(duong_dan_dau_ra)
    
    if engine is None:
        engine = phat_hien_engine(duong_dan_dau_ra)

    print(f"\n--- [LATEX] START: {engine} (file={ten_file}, cwd={thu_muc}) ---")
    cmd = [engine, '-interaction=nonstopmode', '-halt-on-error', '-quiet', f"./{ten_file}"]
    print(f"[LATEX] CMD: {' '.join(cmd)}")
    
    try:
        t_start = time.time()
        ket_qua = subprocess.run(
            cmd,
            cwd=thu_muc if thu_muc else '.',
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='ignore',
            timeout=LATEX_COMPILE_TIMEOUT_SECONDS,
        )
        duration = time.time() - t_start
        print(f"--- [LATEX] FINISHED in {duration:.2f}s (Exit code: {ket_qua.returncode}) ---")

        # Kiểm tra PDF tồn tại (nonstopmode có thể tạo PDF dù có lỗi nhỏ)
        pdf_path = os.path.join(thu_muc, ten_file.replace('.tex', '.pdf'))
        pdf_exists = os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0

        # Mặc định đọc log nếu thất bại
        error_msg = ""
        log_path = os.path.join(thu_muc, ten_file.replace('.tex', '.log'))

        if ket_qua.returncode == 0:
            print(f"[LATEX] SUCCESS: {ten_file.replace('.tex', '.pdf')}")
            return True, ""
        elif pdf_exists:
            print(f"[LATEX] WARNING: PDF created with minor errors.")
            return True, ""
        else:
            print(f"[LATEX] FAILED: {ten_file} (exit code: {ket_qua.returncode})")
            if os.path.exists(log_path):
                try:
                    with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                        # Chỉ lấy 1000 dòng cuối để tránh memory crash nếu log quá lớn
                        error_msg = "".join(lines[-1000:])
                except Exception as e:
                    error_msg = f"Không thể đọc file log: {e}"
            else:
                # Nếu không có file log, ưu tiên dùng stderr/stdout để biết tại sao (ví dụ: lệnh không tồn tại)
                error_msg = ket_qua.stderr.strip() or ket_qua.stdout.strip() or "Không tìm thấy file .log và không có output từ compiler"
            
            if error_msg:
                print(f"[LATEX] Error Snippet (last lines): ... {error_msg[-300:]}")
            return False, error_msg
    except FileNotFoundError:
        msg = f"LỖI: Không tìm thấy '{engine}'. Kiểm tra PATH hoặc cài đặt LaTeX."
        return False, msg
    except subprocess.TimeoutExpired as e:
        timeout_output = e.stdout or ''
        if isinstance(timeout_output, bytes):
            timeout_output = timeout_output.decode('utf-8', 'ignore')
        msg = f"TIMEOUT: Quá {LATEX_COMPILE_TIMEOUT_SECONDS}s. Output log:\n{timeout_output}"
        return False, msg
    except Exception as e:
        import traceback
        msg = f"CRITICAL CRASH: {str(e)}\n{traceback.format_exc()}"
        return False, msg


def phat_hien_loai_tai_lieu(template_src: str) -> str:
    """Detect document class from template source. Returns normalized class name.
    Shared between preprocessor and renderer.
    """
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
    elif cls in ('oscmjournal', 'oscmjournalv2', 'oscmjournalv2.0'):
        return "oscm"
    elif cls in ('jov',):
        return "jov"
    else:
        return "generic"

def giai_nen_mau_zip(zip_path: str, target_dir: str = None) -> str:
    """Giải nén file ZIP template vào thư mục đích.

    - Kiểm tra bảo mật path traversal trước khi giải nén.
    - Nếu ZIP chứa duy nhất 1 thư mục con, tự động dời nội dung lên gốc.

    Args:
        zip_path: Đường dẫn tới file .zip template.
        target_dir: Thư mục đích. Nếu None sẽ tạo tempdir mới.

    Returns:
        Đường dẫn tuyệt đối tới thư mục đã giải nén.

    Raises:
        ValueError: Nếu file ZIP bị hỏng hoặc chứa đường dẫn không an toàn.
    """
    if target_dir is None:
        target_dir = tempfile.mkdtemp(prefix="w2l_zip_")
    os.makedirs(target_dir, exist_ok=True)

    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            for member in zf.namelist():
                member_norm = os.path.normpath(member)
                if member_norm.startswith('..') or os.path.isabs(member_norm):
                    raise ValueError(f"ZIP chứa đường dẫn không an toàn: {member}")
            zf.extractall(target_dir)
    except zipfile.BadZipFile:
        raise ValueError("File ZIP bị hỏng hoặc không hợp lệ")

    # Nếu ZIP chỉ chứa 1 thư mục duy nhất ở cấp gốc → dời nội dung lên
    items = [i for i in os.listdir(target_dir)
             if not i.startswith('.')]  # bỏ qua dotfiles
    if len(items) == 1:
        single = os.path.join(target_dir, items[0])
        if os.path.isdir(single):
            for child in os.listdir(single):
                src = os.path.join(single, child)
                dst = os.path.join(target_dir, child)
                shutil.move(src, dst)
            os.rmdir(single)

    return os.path.abspath(target_dir)


def tim_file_tex_chinh(directory: str) -> str:
    """Tìm file .tex chính trong thư mục (đệ quy bằng os.walk).

    File chính được xác định bằng việc chứa ``\\documentclass``.
    Nếu có nhiều ứng cử viên, ưu tiên:
        1. File không nằm trong blacklist (guide, sample…)
        2. File tên ``main.tex``
        3. File ở thư mục nông nhất (gốc)

    Args:
        directory: Thư mục gốc để tìm kiếm.

    Returns:
        Đường dẫn tuyệt đối tới file .tex chính.

    Raises:
        FileNotFoundError: Nếu không tìm thấy file .tex chính.
    """
    BLACKLIST = ['guide', 'instruction', 'sample', 'example',
                 'readme', 'howto', 'template_guide']
    candidates = []

    for dirpath, _dirnames, filenames in os.walk(directory):
        for fname in filenames:
            if not fname.lower().endswith('.tex'):
                continue
            fpath = os.path.join(dirpath, fname)
            try:
                with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                if '\\documentclass' not in content:
                    continue
                rel = os.path.relpath(fpath, directory)
                depth = rel.count(os.sep)
                stem_lower = fname.lower().replace('.tex', '')
                is_bl = any(kw in stem_lower for kw in BLACKLIST)
                candidates.append((fpath, fname.lower(), depth, is_bl))
            except Exception:
                continue

    if not candidates:
        raise FileNotFoundError(
            "Không tìm thấy file .tex chính (chứa \\documentclass) trong thư mục"
        )

    # Sắp xếp: không blacklist → tên main.tex → nông nhất
    candidates.sort(key=lambda c: (c[3], c[1] != 'main.tex', c[2]))
    return os.path.abspath(candidates[0][0])


def dong_goi_thu_muc_dau_ra(work_dir: str, output_zip_path: str,
                             exclude_suffixes: set = None, generated_tex_name: str = None) -> str:
    """Đóng gói thư mục làm việc thành file ZIP (dành cho Overleaf upload).

    CHỈ bao gồm: .tex (đã render), .pdf, .bib, .cls, .sty, .bst, và thư mục images/.
    Loại trừ: file rác LaTeX, file Word gốc, thư mục template giải nén rác,
    và chính file ZIP đầu ra. Đổi tên file .tex sinh ra thành main.tex để Overleaf dễ nhận diện.

    Args:
        work_dir: Thư mục làm việc cần đóng gói.
        output_zip_path: Đường dẫn file ZIP đầu ra.
        exclude_suffixes: Tập hợp đuôi file cần bỏ qua (không dùng nữa, giữ cho tương thích).
        generated_tex_name: Tên file tex được sinh ra (để đổi tên thành main.tex).

    Returns:
        Đường dẫn tới file ZIP đã tạo.
    """
    # Chỉ cho phép các đuôi file này vào ZIP
    ALLOWED_EXTENSIONS = {
        '.tex', '.pdf', '.bib', '.cls', '.sty', '.bst', '.csl',
        '.png', '.jpg', '.jpeg', '.eps', '.gif', '.svg', '.tif', '.tiff',
        # Biblatex styles & font definitions
        '.bbx', '.cbx', '.lbx', '.dbx', '.fd', '.cfg', '.def',
        # Font files (for custom templates with bundled fonts)
        '.ttf', '.otf', '.woff', '.woff2', '.pfb', '.tfm',
    }
    # Danh sách các thư mục rác cần loại bỏ (Blacklist)
    EXCLUDE_DIRS = {'.git', '.svn', '.hg', '__pycache__', '.venv', 'node_modules', '.idea', '.vscode', 'temp_jobs', 'outputs'}
    # File không có extension nhưng cần thiết cho Overleaf
    ALLOWED_NOEXT_FILES = {'latexmkrc', 'makefile', 'Makefile'}

    abs_zip = os.path.abspath(output_zip_path)

    generated_pdf_name = generated_tex_name.replace('.tex', '.pdf') if generated_tex_name else None

    # Detect which .bst is actually used in the generated .tex
    used_bst = set()
    if generated_tex_name:
        gen_tex_path = os.path.join(work_dir, generated_tex_name)
        if os.path.isfile(gen_tex_path):
            try:
                with open(gen_tex_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for m in re.finditer(r'\\bibliographystyle\{([^}]+)\}', f.read()):
                        used_bst.add(m.group(1) + '.bst')
            except Exception:
                pass  # If can't read, include all .bst

    with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for dirpath, _dirnames, filenames in os.walk(work_dir):
            rel_dir = os.path.relpath(dirpath, work_dir)
            # Skip temp_jobs / nested job folders that sometimes leak in
            if 'temp_jobs' in rel_dir or 'job_' in rel_dir:
                continue
            # Restrict sub-directories to the whitelist
            if rel_dir not in ('', '.'):
                top_dir = rel_dir.split(os.sep)[0].lower()
                if top_dir in EXCLUDE_DIRS:
                    continue
            for fname in filenames:
                fpath = os.path.join(dirpath, fname)

                # Bỏ qua chính file ZIP đầu ra
                if os.path.abspath(fpath) == abs_zip:
                    continue

                # Tránh lỗi clashing với compiler Overleaf (This compile didn't produce a PDF ... output.pdf)
                if fname.lower() == "output.pdf":
                    continue

                _, ext = os.path.splitext(fname)
                if ext.lower() not in ALLOWED_EXTENSIONS and fname not in ALLOWED_NOEXT_FILES:
                    continue

                # At root level, skip template variant / sample files
                if rel_dir in ('', '.'):
                    # Only keep the generated .tex (skip template variant .tex)
                    if ext.lower() == '.tex':
                        if generated_tex_name and fname != generated_tex_name:
                            continue
                    # Only keep references.bib (skip template sample .bib)
                    if ext.lower() == '.bib' and fname.lower() != 'references.bib':
                        continue
                    # Only keep the generated .pdf (skip template sample .pdf)
                    if ext.lower() == '.pdf':
                        if generated_pdf_name and fname != generated_pdf_name:
                            continue
                    # Only keep the .bst referenced in the output (skip unused variants)
                    if ext.lower() == '.bst' and used_bst and fname not in used_bst:
                        continue

                rel_path = os.path.relpath(fpath, work_dir)
                arcname = rel_path

                # Chỉ rename file sinh ra ở root để tránh đổi nhầm file trùng tên trong subdir
                if generated_tex_name and os.path.dirname(rel_path) in ('', '.'):
                    if fname == generated_tex_name:
                        arcname = "main.tex"
                    elif fname == generated_pdf_name:
                        arcname = "main.pdf"
                    elif fname == "main.tex":
                        arcname = "template_main.tex"  # Tránh trùng tên
                    elif fname == "main.pdf":
                        arcname = "template_main.pdf"

                zf.write(fpath, arcname)

    return output_zip_path
