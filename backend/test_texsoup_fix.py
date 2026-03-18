from TexSoup import TexSoup

latex_sample = r"""
\documentclass{article}
\title{Dummy Title}
\author{John Doe \thanks{Thanks}}
\begin{document}
\maketitle
\begin{abstract}
Old abstract.
\end{abstract}
Some body.
\end{document}
"""

def test_mutation():
    soup = TexSoup(latex_sample)
    
    # 1. Title mutation
    titles = list(soup.find_all('title'))
    for t in titles:
        if t.args:
            # Replicating existing logic (but correctly)
            for arg in reversed(t.args):
                if hasattr(arg, 'contents'):
                    arg.contents = ['<< metadata.title >>']
                    break
    
    # 2. Author mutation
    authors = list(soup.find_all('author'))
    for a in authors:
        if a.args:
            a.args[-1].contents = ['<< metadata.author_block >>']
    
    # 3. Abstract mutation
    abstracts = list(soup.find_all('abstract'))
    for ab in abstracts:
        if ab.args:
            ab.args[-1].contents = ['<< metadata.abstract >>']
        else:
            ab.replace_with('\\begin{abstract}\n<< metadata.abstract >>\n\\end{abstract}')
            
    modified = str(soup)
    print("--- MODIFIED LATEX ---")
    print(modified)
    
    if '<< metadata.title >>' in modified and '<< metadata.author_block >>' in modified:
        print("\nSUCCESS: Mutation persisted in str(soup)!")
    else:
        print("\nFAILURE: Mutation lost!")

if __name__ == "__main__":
    test_mutation()
