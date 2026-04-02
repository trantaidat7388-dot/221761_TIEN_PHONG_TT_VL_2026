from TexSoup import TexSoup

latex_text = r"\Title{Original Title}"
soup = TexSoup(latex_text)
node = soup.find('Title')

print(f"Original: {node}")

# Try modifying the contents of the BraceGroup argument
if node.args:
    arg0 = node.args[0]
    # BraceGroup has .contents list
    arg0.contents = ["<< metadata.title >>"]

print(f"Modified: {soup}")
print(f"Full text: {str(soup)}")
