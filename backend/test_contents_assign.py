from TexSoup import TexSoup

latex = r"\Title{Original}"
soup = TexSoup(latex)
node = soup.find('Title')
node.args[0].contents = ["New Title"]

print(f"Result: {str(soup)}")
print(f"Ends with brace? {str(soup).endswith('}')}")
