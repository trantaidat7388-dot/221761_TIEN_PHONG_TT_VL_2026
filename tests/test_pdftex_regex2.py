import re

def remove_pdftex_option(match):
    print("Match:", match.group(0))
    opts_str = match.group(1)
    opts = [o.strip() for o in opts_str.split(',')]
    opts = [o for o in opts if o.lower() != 'pdftex']
    return r'\documentclass[' + ','.join(opts) + ']' if opts else r'\documentclass'

tex = r"\documentclass[preprints,article,submit,pdftex,moreauthors]{Definitions/mdpi}"
print("Original:", tex)
tex = re.sub(r'\\documentclass\s*\[([^\]]*)\]', remove_pdftex_option, tex)
print("Result:", tex)
