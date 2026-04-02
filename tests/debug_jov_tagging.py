import os
import sys

# Thêm backend vào path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

from core_engine.template_preprocessor import TemplatePreprocessor

def test_jov_tagging():
    tex = r"""
\documentclass{jov}
\begin{document}
\title{Test Title}
\author{NGUYEN-HOANG Anh-Tuan, TRAN Binh-An, NGUYEN Anh-Duy \thanks{Nam Can Tho University, Can Tho, Vietnam; Adhightech Ltd.,Can Tho, Viet Nam}}
\maketitle
\end{document}
"""
    # Detect doc class should be jov now
    tagged_tex = TemplatePreprocessor.auto_tag(tex)
    
    print("--- TAGGED TEXT ---")
    print(tagged_tex)
    print("-------------------")
    
    if "<< metadata.author_block >>" in tagged_tex:
        print("[SUCCESS] Author block tagged!")
    else:
        print("[FAILED] Author block NOT tagged!")

    if r"\author{" in tagged_tex and "<< metadata.author_block >>" not in tagged_tex:
        print("[ERROR] Original \\author remains!")

if __name__ == "__main__":
    test_jov_tagging()
