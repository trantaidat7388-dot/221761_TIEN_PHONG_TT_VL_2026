"""Debug md5 hash of ieee docx"""
import hashlib
from pathlib import Path

def get_md5(p):
    with open(p, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

print("File 1 (from reproduce bug):")
print(get_md5(r"c:\221761_TIEN_PHONG_TT_VL_2026\debug_output2\step1_ieee.docx"))

print("File 2 (from trace authors):")
print(get_md5(r"c:\221761_TIEN_PHONG_TT_VL_2026\debug_output4\ieee_output.docx"))
