import sys
import os

# Thêm thư mục gốc vào sys.path để import được core_engine
sys.path.append(os.getcwd())

from backend.core_engine.template_preprocessor import TemplatePreprocessor

# GIẢ LẬP mẩu LaTeX giống Rho-Class main.tex
dummy_tex = r"""
\documentclass{rho-class}
\begin{document}

\begin{abstract}
Mô phỏng Abstract thật sự.
\end{abstract}

\maketitle

\section{Rho Class}
Đây là phần hướng dẫn dùng template.
\inlinecode{\begin{abstract}Abstract mẫu trong documentation\end{abstract}}
Tiếp tục hướng dẫn...

\end{document}
"""

print("--- Source TeX Snippet ---")
# print(dummy_tex)

# Chạy tiền xử lý body
result_tex = TemplatePreprocessor._process_body(dummy_tex)

print("\n--- Result TeX Snippet ---")
print(result_tex)

# Kiểm tra vị trí << body >>
# Nếu bug xảy ra, << body >> sẽ nằm ngay sau ...\end{abstract} của inlinecode
# và dấu ngoặc } của inlinecode sẽ bị mất.

if r"\inlinecode{\begin{abstract}Abstract mẫu trong documentation\end{abstract}}" in result_tex:
    print("\n[SUCCESS] Documentation block was PRESERVED.")
else:
    # Nếu bị mất ngoặc }, chuỗi sẽ bị cắt
    if "inlinecode" in result_tex and "}" not in result_tex.split("inlinecode")[-1]:
         print("\n[FAILURE] Missing brace detected! The 'Time Bomb' exploded.")
    else:
         print("\n[FAILURE] Documentation block was modified or deleted unexpectedy.")

# Kiểm tra xem << body >> có được chèn đúng chỗ không
if "<< body >>" in result_tex:
    print("[SUCCESS] Found << body >> tag.")
else:
    print("[FAILURE] << body >> tag missing.")

# Kiểm tra xem body_start có đúng là sau \maketitle hay không
# (Trong ví dụ này, \maketitle ở trước documentation)
# Nếu body_start dùng cái \end{abstract} ở line 128, thì \maketitle sẽ biến mất?
# Không, body_start là vị trí CẮT.
# Nếu body_start = line 128, thì tex[:body_start] sẽ bao gồm cả \maketitle.

if r"\maketitle" in result_tex:
     print("[SUCCESS] \maketitle was preserved in preamble part.")
else:
     print("[FAILURE] \maketitle was accidentally deleted!")

# THỬ NGHIỆM VỚI Keywords
dummy_tex_kw = r"""
\begin{abstract}Real abstract\end{abstract}
\maketitle
\inlinecode{\begin{IEEEkeywords}Example keywords\end{IEEEkeywords}}
\section{Intro}
"""
result_tex_kw = TemplatePreprocessor._process_body(dummy_tex_kw)
if "Example keywords" in result_tex_kw:
    print("[SUCCESS] IEEEkeywords in documentation was preserved.")
else:
    print("[FAILURE] IEEEkeywords in documentation was cut!")
