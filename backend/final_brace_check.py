from TexSoup import TexSoup
import os

latex_text = r"\Title{Original Title}"
soup = TexSoup(latex_text)
node = soup.find('Title')

if node.args:
    arg0 = node.args[0]
    arg0.contents = ["<< metadata.title >>"]

result = str(soup)
print(f"Result length: {len(result)}")
print(f"Ends with brace? {result.endswith('}')}")
print(f"Last 5 chars: '{result[-5:]}'")
