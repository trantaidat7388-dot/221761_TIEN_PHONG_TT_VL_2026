from TexSoup import TexSoup
import os
import re

path = os.path.join('backend', 'storage', 'custom_templates', 'template.tex')
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# Logic from chuyen_doi.py
def tiem_du_lieu(ket_qua):
    try:
        soup = TexSoup(ket_qua)
        
        # Try both cases
        for t_cmd in ['title', 'Title']:
            node = soup.find(t_cmd)
            if node:
                print(f"Found {t_cmd}, replacing contents.")
                node.contents = ["<< metadata.title >>"]
                
        for a_cmd in ['author', 'Author']:
            nodes = soup.find_all(a_cmd)
            for node in nodes:
                print(f"Found {a_cmd}, replacing contents.")
                node.contents = ["<< metadata.author >>"]
                
        for ab_cmd in ['abstract']:
            node = soup.find(ab_cmd)
            if node:
                print(f"Found {ab_cmd}, replacing contents.")
                node.contents = ["\n<< metadata.abstract >>\n"]
                
        for k_cmd in ['keywords', 'keyword']:
            node = soup.find(k_cmd)
            if node:
                print(f"Found {k_cmd}, replacing contents.")
                node.contents = ["<< metadata.keywords >>"]
                
        return str(soup)
    except Exception as e:
        print(f"TexSoup failed: {e}")
        return ket_qua

new_tex = tiem_du_lieu(text)
print("--- Result Snippet ---")
# Print around Title and Author
lines = new_tex.split('\n')
for i, line in enumerate(lines):
    if '<< metadata.' in line:
        print(f"{i}: {line}")
