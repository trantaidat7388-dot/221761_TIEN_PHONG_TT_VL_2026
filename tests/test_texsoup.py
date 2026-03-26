from TexSoup import TexSoup
import os

path = os.path.join('backend', 'storage', 'custom_templates', 'template.tex')
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

try:
    soup = TexSoup(text)
    print("TexSoup parsed successfully.")
    
    # Try finding Title (notice uppercase)
    title_node = soup.find('Title')
    if title_node:
        print(f"Found Title: {title_node.contents}")
    else:
        print("Title (uppercase) not found.")
        
    title_node_lower = soup.find('title')
    if title_node_lower:
        print(f"Found title (lowercase): {title_node_lower.contents}")
    else:
        print("title (lowercase) not found.")

except Exception as e:
    print(f"TexSoup failed: {e}")
