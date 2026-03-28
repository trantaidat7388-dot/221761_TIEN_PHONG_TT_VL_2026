"""Test that apacite/jovcite patches are injected correctly."""
import sys
sys.path.insert(0, r'd:\221761_TIEN_PHONG_TT_VL_2026')

from backend.core_engine.template_preprocessor import TemplatePreprocessor

# Simulate a JOV template that uses jovcite (old apacite)
tex = r"""% !TeX program = xelatex
\documentclass{jov}
\title{Test Title}
\author{Author Name \thanks{University}}
\keywords{keyword1, keyword2}
\begin{document}
\maketitle
\section{Introduction}
Content here.
\begin{thebibliography}{1}
\bibitem{ref1} Reference 1. \url{http://example.com}
\end{thebibliography}
\end{document}
"""

result = TemplatePreprocessor.auto_tag(tex)

# Check all apacite patches are present
assert r'\providecommand{\BRetrievedFrom}' in result, "FAIL: BRetrievedFrom patch missing"
assert r'\providecommand{\PrintOrdinal}' in result, "FAIL: PrintOrdinal patch missing"
assert r'\providecommand{\CardinalNumeric}' in result, "FAIL: CardinalNumeric patch missing"
assert r'\providecommand{\APACmonth}' in result, "FAIL: APACmonth patch missing"
assert r'\providecommand{\APACrefYearMonthDay}' in result, "FAIL: APACrefYearMonthDay patch missing"
assert r'\if@APAC@natbib@apa' in result, "FAIL: APAC@natbib@apa flag missing"

# Standard patches still present
assert r'\providecommand{\onemaskedcitationmsg}' in result, "FAIL: onemaskedcitationmsg patch missing"
assert r'\providecommand{\maskedcitationsmsg}' in result, "FAIL: maskedcitationsmsg patch missing"

# All patches should be BEFORE \begin{document}
begin_doc_pos = result.find(r'\begin{document}')
bretrieved_pos = result.find(r'\providecommand{\BRetrievedFrom}')
assert bretrieved_pos < begin_doc_pos, "FAIL: BRetrievedFrom patch is AFTER \\begin{document}"

print("=== ALL APACITE PATCH TESTS PASSED ===")

# Show patched preamble section
lines = result.split('\n')
for i, line in enumerate(lines):
    if 'providecommand' in line or 'APAC' in line or 'begin{document}' in line:
        print(f"  L{i+1}: {line[:100]}")
