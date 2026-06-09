from TexSoup import TexSoup
import os

def test_tiem_du_lieu_parsing():
    path = os.path.join('backend', 'storage', 'custom_templates', 'template.tex')
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()

    def tiem_du_lieu(ket_qua):
        try:
            soup = TexSoup(ket_qua)
            for t_cmd in ['title', 'Title']:
                node = soup.find(t_cmd)
                if node:
                    node.contents = ["<< metadata.title >>"]
            for a_cmd in ['author', 'Author']:
                nodes = soup.find_all(a_cmd)
                for node in nodes:
                    node.contents = ["<< metadata.author >>"]
            for ab_cmd in ['abstract']:
                node = soup.find(ab_cmd)
                if node:
                    node.contents = ["\n<< metadata.abstract >>\n"]
            for k_cmd in ['keywords', 'keyword']:
                node = soup.find(k_cmd)
                if node:
                    node.contents = ["<< metadata.keywords >>"]
            return str(soup)
        except Exception as e:
            print(f"TexSoup failed: {e}")
            return ket_qua

    new_tex = tiem_du_lieu(text)
    assert "<< metadata.title >>" in new_tex
