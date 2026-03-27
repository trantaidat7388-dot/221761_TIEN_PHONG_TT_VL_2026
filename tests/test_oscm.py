import sys, os, re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from backend.core_engine.template_preprocessor import TemplatePreprocessor

template_path = r'backend\storage\custom_templates\OSCM_Journal\main.tex'
with open(template_path, 'r', encoding='utf-8') as f:
    tex = f.read()

from pylatexenc.latexwalker import LatexWalker, LatexMacroNode
walker = LatexWalker(tex)
nodelist, _, _ = walker.get_latex_nodes()

def traverse(nodes):
    if not nodes: return []
    found = []
    for n in nodes:
        found.append(n)
        if getattr(n, 'nodelist', None):
            found.extend(traverse(n.nodelist))
        if getattr(n, 'nodeargd', None) and getattr(n.nodeargd, 'argnlist', None):
            for arg in n.nodeargd.argnlist:
                if arg:
                    found.append(arg)
                    if getattr(arg, 'nodelist', None):
                        found.extend(traverse(arg.nodelist))
    return found

all_nodes = traverse(nodelist)
author_nodes = [n for n in all_nodes if getattr(n, 'macroname', '') == 'author']

for i, node in enumerate(author_nodes):
    print(f"=== Traversing Author {i} ===")
    end_pos = node.pos + node.len
    print(f"Start end_pos: {end_pos} ('{tex[end_pos:end_pos+10]}...')")
    
    while end_pos < len(tex):
        rest = tex[end_pos:]
        match = re.match(r'^(\s|%.*?\n)*', rest)
        skip_len = match.end() if match else 0
        
        if end_pos + skip_len < len(tex):
            next_char = tex[end_pos + skip_len]
            print(f"  skip_len: {skip_len}, next_char: {next_char!r} at {end_pos + skip_len}")
            
            if next_char == '{':
                next_end = TemplatePreprocessor._find_matching_brace(tex, end_pos + skip_len)
                if next_end != -1:
                    print(f"    Consumed Brace block: {tex[end_pos+skip_len:next_end+1]!r}")
                    end_pos = next_end + 1
                    continue
            elif next_char == '[':
                closing = tex.find(']', end_pos + skip_len)
                if closing != -1:
                    print(f"    Consumed Bracket block.")
                    end_pos = closing + 1
                    continue
            elif next_char in ('*', ']'):
                print(f"    Consumed custom char '{next_char}'")
                end_pos = end_pos + skip_len + 1
                continue
        
        print("  Break hit")
        break
    print(f"Final end_pos: {end_pos}")
    print(f"Text removed: {tex[node.pos:end_pos]!r}")
