import sys
import os
import re
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.core_engine.template_preprocessor import TemplatePreprocessor
from backend.core_engine.template_preprocessor import PUBLISHERS_MANIFEST

template_path = r'backend\storage\custom_templates\MDPI_Article_Template__1\template.tex'
with open(template_path, 'r', encoding='utf-8') as f:
    tex = f.read()

config = PUBLISHERS_MANIFEST.get('mdpi', {})

try:
    from pylatexenc.latexwalker import LatexWalker, LatexMacroNode, LatexEnvironmentNode, LatexGroupNode
    walker = LatexWalker(tex)
    nodelist, _, _ = walker.get_latex_nodes()

    replace_ops = []
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
    print(f"Total nodes: {len(all_nodes)}")
    
    # 1. Processing Title
    title_cmd_raw = config.get("title_command", "title").replace("\\", "")
    titles = [n for n in all_nodes if isinstance(n, LatexMacroNode) and n.macroname.lower() == title_cmd_raw.lower()]
    for t in titles:
        print(f"Title Node: pos={t.pos} len={t.len} end={t.pos+t.len}")
        print(f"   Content: {tex[t.pos:t.pos+t.len]!r}")
        
    for n in all_nodes:
        if isinstance(n, LatexMacroNode) and n.macroname in ['Author', 'AuthorNames', 'address', 'corres', 'abstract']:
            print(f"Macro {n.macroname}: pos={n.pos} len={n.len} end={n.pos+n.len}")
            print(f"   Content: {tex[n.pos:n.pos+min(n.len, 50)]!r}...")
        if isinstance(n, LatexEnvironmentNode) and n.environmentname == 'document':
             print(f"Environment {n.environmentname}: pos={n.pos} len={n.len} end={n.pos+n.len}")
             print(f"   Content: {tex[n.pos:n.pos+min(n.len, 50)]!r}...")

    replace_ops = []
    
    for t in titles:
        if getattr(t, 'nodeargd', None) and getattr(t.nodeargd, 'argnlist', None):
            for arg in reversed(t.nodeargd.argnlist):
                if arg and isinstance(arg, LatexGroupNode):
                    replace_ops.append((arg.pos + 1, arg.pos + arg.len - 1, '<< metadata.title >>'))
                    break
                    
    # 2. Author & Affiliations
    related_cmds = {'author', 'Author', 'affil', 'affiliation', 'address', 'email', 'institute',
                    'authornote', 'orcid', 'corres', 'firstnote', 'AuthorNames'}
    author_nodes = [n for n in all_nodes if isinstance(n, LatexMacroNode) and n.macroname in related_cmds]
    if author_nodes:
        first_author = author_nodes[0]
        insert_pos = first_author.pos
        replace_ops.append((insert_pos, insert_pos, '<< metadata.author_block >>'))
        
        for node in author_nodes:
            end_pos = node.pos + node.len
            while end_pos < len(tex):
                rest = tex[end_pos:]
                match = re.match(r'^(\s|%.*?\n)*', rest)
                skip_len = match.end() if match else 0
                if end_pos + skip_len < len(tex) and tex[end_pos + skip_len] == '{':
                    next_brace = end_pos + skip_len
                    next_end = TemplatePreprocessor._find_matching_brace(tex, next_brace)
                    if next_end != -1:
                        end_pos = next_end + 1
                        continue
                break
            replace_ops.append((node.pos, end_pos, ''))
            
    # Abstract
    ab = [n for n in all_nodes if isinstance(n, LatexMacroNode) and n.macroname.lower() == "abstract"]
    if ab:
        o = ab[0]
        if getattr(o, 'nodeargd', None) and getattr(o.nodeargd, 'argnlist', None):
            for arg in reversed(o.nodeargd.argnlist):
                if arg and isinstance(arg, LatexGroupNode):
                    replace_ops.append((arg.pos + 1, arg.pos + arg.len - 1, '<< metadata.abstract >>'))
                    break
                    
    for op in replace_ops:
        start, end, text = op
        deleted = tex[start:end]
        print(f"op: start={start} end={end} repl={text!r}")
        print(f"Content deleted: {deleted!r:.100}...")
except Exception as e:
    import traceback
    traceback.print_exc()
