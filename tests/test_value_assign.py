from TexSoup import TexSoup

latex = r"\Title{Original}"
soup = TexSoup(latex)
node = soup.find('Title')
node.args[-1].value = "New Title"

print(f"Result: {str(soup)}")
print(f"Ends with brace? {str(soup).endswith('}')}")
