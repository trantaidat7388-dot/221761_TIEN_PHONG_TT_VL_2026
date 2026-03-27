import re

s1 = r"\documentclass[preprints,article,submit,pdftex,moreauthors]{Definitions/mdpi}"
print("Original:", s1)
s2 = re.sub(r'(\\documentclass\[[^\]]*)pdftex,?([^\]]*\])', r'\1\2', s1)
print("Fix 1:", s2)
s3 = re.sub(r'(\\documentclass\[[^\]]*),?pdftex([^\]]*\])', r'\1\2', s2)
print("Fix 2:", s3)

tex = r"""\PassOptionsToPackage{table,xcdraw}{xcolor}
\PassOptionsToPackage{hidelinks}{hyperref}
\documentclass[journal,article,submit,pdftex,moreauthors]{Definitions/mdpi}
\usepackage{fontspec}"""

print("\nFull tex:")
content_fixed = re.sub(r'(\\documentclass\[[^\]]*)pdftex,?([^\]]*\])', r'\1\2', tex)
content_fixed = re.sub(r'(\\documentclass\[[^\]]*),?pdftex([^\]]*\])', r'\1\2', content_fixed)
print(content_fixed)
