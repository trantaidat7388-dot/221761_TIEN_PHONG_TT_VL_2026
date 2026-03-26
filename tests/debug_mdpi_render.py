import os
import sys
from backend.core_engine.template_preprocessor import TemplatePreprocessor
from backend.core_engine.jinja_renderer import JinjaLaTeXRenderer

def test_mdpi_render():
    template_path = r'c:\221761_TIEN_PHONG_TT_VL_2026\backend\storage\temp_jobs\debug_mdpi\template.tex'
    with open(template_path, 'r', encoding='utf-8') as f:
        tex = f.read()
    
    # Auto-tag
    tagged = TemplatePreprocessor.auto_tag(tex)
    with open('debug_tagged.tex', 'w', encoding='utf-8') as f:
        f.write(tagged)
    
    # Render with EMPTY authors
    ir = {
        "metadata": {
            "title": "Debug Title",
            "authors": [], # EMPTY
            "abstract": "Debug Abstract",
            "keywords_str": "k1, k2"
        },
        "body": []
    }
    
    renderer = JinjaLaTeXRenderer('.')
    renderer.render('debug_tagged.tex', ir, 'debug_final.tex')
    
    with open('debug_final.tex', 'r', encoding='utf-8') as f:
        final = f.read()
        
    print("\n--- Diagnostic: Check if tags exist in 'final' output ---")
    tags = ["<< metadata.title >>", "<< metadata.author_block >>", "<< metadata.abstract >>"]
    for t in tags:
        print(f"Tag '{t}' STILL present in final: {t in final}")
    
    if "<< metadata.author_block >>" in final:
        print("\nCRITICAL FAILURE: Jinja2 DID NOT replace the tag!")

if __name__ == "__main__":
    test_mdpi_render()
