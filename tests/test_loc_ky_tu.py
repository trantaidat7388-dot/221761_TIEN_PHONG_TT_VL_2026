import sys
import os

# Set up paths to import from backend
sys.path.append(os.path.abspath('backend'))

from core_engine.utils import loc_ky_tu

test_cases = [
    ("100%", "100\\%"),
    ("Profit & Loss", "Profit \\& Loss"),
    ("Path C:\\Users", "Path C:\\textbackslash Users"),
    ("Already \\% escaped", "Already \\% escaped"),
    ("Double \\\\ backslash", "Double \\\\ backslash"), # Wait, what should this be?
    ("Math $x^2$", "Math \\$x\\textasciicircum{}2\\$"), # loc_ky_tu is meant for TEXT, so it escapes $
    ("Complex #_&", "Complex \\#\\_\\&"),
    ("Nested { braces }", "Nested \\{ braces \\}"),
    ("Tilde ~", "Tilde \\textasciitilde{}"),
]

for inp, expected in test_cases:
    out = loc_ky_tu(inp)
    print(f"Input: {inp}")
    print(f"Output: {out}")
    if out == expected:
        print("Result: PASS")
    else:
        print(f"Result: FAIL (Expected: {expected})")
    print("-" * 20)
