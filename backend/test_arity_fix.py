
from TexSoup import TexSoup

def test_arity_fix():
    # Simulate jov.cls: \author{Name}{Affil}{URL}{Email}
    tex = r"""
\documentclass{jov}
\begin{document}
\title{Sample Title}
\author{Original Name}{Original Affiliation}{http://example.com}{email@example.com}

\abstract{This is the abstract that might be gobbled.}
\end{document}
"""
    soup = TexSoup(tex)
    
    author_nodes = list(soup.find_all('author'))
    if author_nodes:
        first_author = author_nodes[0]
        print(f"[*] Found first author: {first_author}")
        
        # In TexSoup, siblings are often harder to find directly. 
        # We can iterate through parent contents.
        parent = first_author.parent
        if parent:
            contents = list(parent.contents)
            try:
                # Find index. Note: content items might be strings or TexNodes
                idx = -1
                for i, item in enumerate(contents):
                    if item == first_author:
                        idx = i
                        break
                
                if idx != -1:
                    print(f"[*] Found first author at index {idx} in parent contents.")
                    to_delete = []
                    extra_braces_count = 0
                    for i in range(idx + 1, len(contents)):
                        item = contents[i]
                        s_item = str(item).strip()
                        # Skip whitespace/newlines
                        if not s_item:
                            continue
                        
                        # Check if it's a BraceGroup (starts with { and ends with })
                        # AND check if it's NOT another command (doesn't start with \)
                        if s_item.startswith('{') and s_item.endswith('}') and not s_item.startswith('\\'):
                            print(f"[*] Detected trailing argument: {s_item}")
                            extra_braces_count += 1
                            to_delete.append(item)
                        else:
                            # Stop at first non-bracegroup (like \abstract)
                            break
                    
                    for item in to_delete:
                        item.delete()
                    
                    padding = "{}" * extra_braces_count
                    first_author.insert_before(f'<< metadata.author_block >>{padding}\n')
            except Exception as e:
                print(f"[!] Error during scan: {e}")

    # Delete original authors
    for node in soup.find_all('author'):
        node.delete()

    result = str(soup)
    print("\n--- RESULTING TEX ---")
    print(result)

    
    # Verification
    if "<< metadata.author_block >>{}{}{}" in result:
        print("\nSUCCESS: Arity padding applied correctly!")
    else:
        print("\nFAILURE: Arity padding NOT applied.")
        
    if "\\abstract" in result:
        print("SUCCESS: Abstract survived!")
    else:
        print("FAILURE: Abstract missing!")

if __name__ == "__main__":
    test_arity_fix()
