from TexSoup import TexSoup
import os

latex_text = r"\Title{Original Title}"
soup = TexSoup(latex_text)
node = soup.find('Title')

print(f"Original: {node}")
print(f"Node arguments: {node.args}")

# Try to change the first argument
if node.args:
    # TexSoup nodes represent arguments in .args
    # node.args[0] is a TexArg object like {Original Title}
    # We can try to replace its contents
    arg0 = node.args[0]
    print(f"Arg[0]: {arg0}, Type: {type(arg0)}")
    
    # In some versions of TexSoup, we can't just set .value
    # Let's try to see what we CAN set
    # Try replacing the whole node with a new one?
    node.replace_with(TexSoup(fr"\Title{{<< metadata.title >>}}"))

print(f"Modified: {soup}")
