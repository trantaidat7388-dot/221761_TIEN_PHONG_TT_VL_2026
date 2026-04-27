"""
Patch script: fixes the 'image_inserted' NameError in word_ieee_renderer.py
by merging the two separate `for image_path in paths` loops into one.
"""
import re
import sys

FILE = "backend/core_engine/word_ieee_renderer.py"

with open(FILE, "r", encoding="utf-8") as f:
    content = f.read()

# Normalize CRLF -> LF for matching
content_n = content.replace("\r\n", "\n")

# Strategy: use regex to find and remove the second (buggy) fallback loop
# that appears AFTER the caption block in _add_figure_node
pattern_second_loop = re.compile(
    r"\n        for image_path in paths:\n"
    r"            resolved = self\._resolve_image_path\(image_path\)\n"
    r"            if not resolved or not resolved\.exists\(\):\n"
    r"                fallback = doc\.add_paragraph\(f\"\[Image: \{image_path\}\]\"\)\n"
    r"                fallback\.alignment = WD_ALIGN_PARAGRAPH\.CENTER\n"
    r"                for run in fallback\.runs:\n"
    r"                    run\.font\.size = Pt\(8\)\n"
    r"                    run\.italic = True\n",
    re.MULTILINE,
)

matches = list(pattern_second_loop.finditer(content_n))
print(f"Found {len(matches)} match(es) for the second loop pattern")

if matches:
    # Remove the second (and only the second) occurrence — the first occurrence
    # is the primary insert loop which we keep and extend.
    # The second loop starts after the caption paragraph block.
    # We want to remove matches that come AFTER the caption code.
    # Since there's exactly 1 match for the second loop, just replace all.
    content_patched = pattern_second_loop.sub("\n", content_n, count=1)
    print("Second (buggy) loop removed")
else:
    print("Pattern not found with regex - trying direct string search")
    # Print lines around 1233 for diagnostic
    lines = content_n.split("\n")
    for i in range(1228, 1245):
        print(f"{i+1}: {repr(lines[i])}")
    sys.exit(1)

# Now update the first loop's except clause to include inline fallback
OLD_LOOP_END = (
    "                except Exception:\n"
    "                    pass        # IEEE figure caption below image: \"Fig. 1. Caption text\"\n"
    "        if caption:\n"
)
NEW_LOOP_END = (
    "                except Exception:\n"
    "                    pass\n"
    "            else:\n"
    "                # Image file missing - show a visible placeholder\n"
    "                fallback = doc.add_paragraph(\"[Image: \" + image_path + \"]\")\n"
    "                fallback.alignment = WD_ALIGN_PARAGRAPH.CENTER\n"
    "                for run in fallback.runs:\n"
    "                    run.font.size = Pt(8)\n"
    "                    run.italic = True\n"
    "        if caption:\n"
)

if OLD_LOOP_END in content_patched:
    content_patched = content_patched.replace(OLD_LOOP_END, NEW_LOOP_END, 1)
    print("First loop updated with inline fallback")
else:
    print("WARNING: Could not find first-loop-end marker")
    # Show what we have
    idx = content_patched.find("IEEE figure caption below image")
    if idx >= 0:
        print("Context around comment:")
        print(repr(content_patched[idx-50:idx+200]))

# Write back
with open(FILE, "w", encoding="utf-8", newline="\r\n") as f:
    f.write(content_patched.replace("\n", "\r\n"))
print("File written")

# Verify syntax
import py_compile
try:
    py_compile.compile(FILE, doraise=True)
    print("Syntax check PASSED")
except py_compile.PyCompileError as e:
    print(f"Syntax ERROR: {e}")
    sys.exit(1)
