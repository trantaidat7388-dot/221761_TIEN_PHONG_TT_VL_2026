import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.core_engine.template_preprocessor import TemplatePreprocessor

tex = (
    "\\documentclass[preprints,article,submit,pdftex,moreauthors]{Definitions/mdpi}\n"
    "\\begin{document}\n"
    "Hello World\n"
    "\\end{document}\n"
)
result = TemplatePreprocessor.auto_tag(tex)
with open("dump_result.txt", "w", encoding="utf-8") as f:
    f.write(result)
