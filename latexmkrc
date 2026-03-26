# Force XeLaTeX for full Unicode support (Vietnamese, CJK, etc.)
# Required for Overleaf: default compiler is pdfLaTeX which cannot handle Unicode
$pdf_mode = 5;
# Fallback for older latexmk versions
$pdflatex = 'xelatex -interaction=nonstopmode -halt-on-error -synctex=1 %O %S';
