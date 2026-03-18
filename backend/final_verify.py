import sys
import os
import re

# Set up paths
sys.path.append(os.path.abspath('backend'))
from core_engine.chuyen_doi import ChuyenDoiWordSangLatex

# Mock parsed_data
mock_data = {
    'title': 'Real Title',
    'author_block': 'Real Authors',
    'abstract': 'Real Abstract',
    'keywords_str': 'k1, k2',
    'body': 'Real Body'
}

# Fix: Use real class name and initialize correctly
bdc = ChuyenDoiWordSangLatex("dummy.docx", "template.tex", "out.tex")
bdc.parsed_data = mock_data

test_templates = [
    (r"\Title{Template Title}", r"\\Title\{Real Title\}"),
    (r"\Author{Old Authors}", r"\\Author\{Real Authors\}"),
    (r"\abstract{Text}", r"\\abstract\{\nReal Abstract\n\}"),
    (r"\keyword{k1; k2}", r"\\keyword\{k1, k2\}"),
    (r"\author{A1}\author{A2}", r"\\author\{Real Authors\}") # Should delete second author
]

for template, expected in test_templates:
    result = bdc.inject_into_template(template)
    print(f"Template: {template}")
    print(f"Result: {result.strip()}")
    # Use re.escape for the expected pattern but allow \n
    pattern = expected.replace(r'\n', r'\s+')
    match = re.search(pattern, result, re.DOTALL)
    if match:
        print("MATCH: OK")
    else:
        print("MATCH: FAIL")
    print("-" * 20)
