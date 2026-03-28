"""Test that TemplatePreprocessor correctly handles authblk-style \author commands."""
import sys
sys.path.insert(0, r'd:\221761_TIEN_PHONG_TT_VL_2026')

from backend.core_engine.template_preprocessor import TemplatePreprocessor

# Simulate a Rho/authblk template
tex = r"""% !TeX program = xelatex
\documentclass[9pt]{extarticle}
\usepackage{authblk}
\title{Test Title About Machine Learning}
\author[a,1]{Author One}
\author[b,2]{Author Two}
\author[c,3]{Author Three}
\affil[a]{University A, City A, Country A}
\affil[b]{University B, City B, Country B}
\affil[c]{University C, City C, Country C}
\begin{document}
\maketitle
\section{Introduction}
Some content here.
\end{document}
"""

print("=== ORIGINAL ===")
print(tex[:300])
print("...")

result = TemplatePreprocessor.auto_tag(tex)

print("\n=== PROCESSED ===")
print(result[:500])
print("...")

# Verify critical tags
assert '<< metadata.title >>' in result, "FAIL: title tag missing"
assert '<< metadata.author_block >>' in result, "FAIL: author_block tag missing"
assert '<< body >>' in result, "FAIL: body tag missing"

# Verify NO orphaned fragments
assert ',a,1]{Author One}' not in result, "FAIL: orphaned authblk fragment still present"
assert ',b,2]{Author Two}' not in result, "FAIL: orphaned authblk fragment still present"
assert ',c,3]{Author Three}' not in result, "FAIL: orphaned authblk fragment still present"
assert 'Author One' not in result, "FAIL: original author name not cleaned"
assert 'Author Two' not in result, "FAIL: original author name not cleaned"

print("\n=== ALL TESTS PASSED ===")
