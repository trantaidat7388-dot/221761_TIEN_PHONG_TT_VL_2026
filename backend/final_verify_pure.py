import re
from TexSoup import TexSoup

class MockBDC:
    def __init__(self, parsed_data):
        self.parsed_data = parsed_data

    # COPY OF REPAIRED FUNCTION
    def inject_into_template(self, template: str) -> str:
        ket_qua = template
        try:
            from TexSoup import TexSoup
            soup = TexSoup(ket_qua)
            
            # 1. Title
            title = self.parsed_data.get('title', '').strip()
            if title:
                for t_tag in ['title', 'Title']:
                    for t in soup.find_all(t_tag):
                        if t.args:
                            thanks = t.find('thanks')
                            thanks_str = f"\\thanks{{{thanks.args[0].value}}}" if thanks and thanks.args else ""
                            t.args[-1].contents = [title + thanks_str]
            
            # 2. Author
            author_block = self.parsed_data.get('author_block', '').strip()
            if author_block:
                authors = []
                for a_tag in ['author', 'Author']:
                    authors.extend(list(soup.find_all(a_tag)))
                
                if authors:
                    if authors[0].args:
                        authors[0].args[-1].contents = [author_block]
                    else:
                        authors[0].contents = [author_block]
                    for other in authors[1:]:
                        try: other.delete()
                        except: pass
            
            for cmd in ['affil', 'affiliation', 'address', 'email', 'institute', 'authornote', 'orcid', 'AuthorNames']:
                for node in soup.find_all(cmd):
                    try: node.delete()
                    except: pass

            # 3. Abstract
            abstract = self.parsed_data.get('abstract', '').strip()
            if abstract:
                abstracts = []
                for ab_tag in ['abstract', 'Abstract']:
                    abstracts.extend(list(soup.find_all(ab_tag)))
                for ab in abstracts:
                    if ab.args: ab.args[-1].contents = [f"\n{abstract}\n"]
                    else: ab.contents = [f"\n{abstract}\n"]

            # 4. Keywords
            keywords = self.parsed_data.get('keywords', '').strip()
            if not keywords: keywords = self.parsed_data.get('keywords_str', '').strip()
            if keywords:
                for cmd in ['keywords', 'keyword', 'IEEEkeywords', 'IndexTerms', 'Keywords']:
                    for kw in soup.find_all(cmd):
                        if kw.args: kw.args[-1].contents = [keywords]
                        else: kw.contents = [keywords]
            ket_qua = str(soup)
        except Exception as e:
            print(f"Error: {e}")
        return ket_qua

# Test cases
mock_data = {
    'title': 'Real Title',
    'author_block': 'Real Authors',
    'abstract': 'Real Abstract',
    'keywords': 'k1, k2'
}
bdc = MockBDC(mock_data)

test_templates = [
    (r"\Title{Template Title}", r"\\Title\{Real Title\}"),
    (r"\Author{Old Authors}", r"\\Author\{Real Authors\}"),
    (r"\abstract{Text}", r"\\abstract\{\nReal Abstract\n\}"),
    (r"\keyword{k1; k2}", r"\\keyword\{k1, k2\}"),
    (r"\author{A1}\author{A2}", r"\\author\{Real Authors\}")
]

for template, expected in test_templates:
    result = bdc.inject_into_template(template)
    print(f"Template: {template}")
    print(f"Result: {result.strip()}")
    pattern = expected.replace(r'\n', r'\s+')
    match = re.search(pattern, result, re.DOTALL)
    if match:
        print("MATCH: OK")
    else:
        print("MATCH: FAIL")
    print("-" * 20)
