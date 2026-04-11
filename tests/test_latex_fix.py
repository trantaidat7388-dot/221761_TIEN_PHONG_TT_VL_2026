import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from backend.core_engine.ast_parser import WordASTParser
import re

file_path = r"input_data/Template_word/-TUAN_Magazine_01-12- Customer Churn Prediction in Vietnam's Enterprise Market Using Machine Learning Methods in a Streaming Data (1).docx"
p = WordASTParser(file_path, mode='latex')
ir = p.parse()

# Check authors
print('=== AUTHORS ===')
for a in ir['metadata']['authors']:
    name = a.get('name', '')
    print(f'  Name: {name!r}')
    for af in a.get('affiliations', []):
        print(f'    Affil: {af!r}')

# Check for textbackslash in body
body_text = ' '.join(n.get('text', '') for n in ir['body'])
if 'textbackslash' in body_text:
    for m in re.finditer(r'.{20}textbackslash.{20}', body_text):
        print(f'FOUND textbackslash: ...{m.group()}...')
    print('BAD: textbackslash found!')
else:
    print('NO textbackslash found in body - GOOD!')

# Check image widths
for m in re.finditer(r'width=[\d\.]+\\\\(columnwidth|textwidth)', body_text):
    print(f'Image width: {m.group()}')

# Check references  
print(f'=== REFERENCES: {len(ir["references"])} entries ===')
for r in ir['references'][:3]:
    txt = r.get('text', '')[:80]
    print(f'  {txt!r}')

# Check references for textbackslash
ref_text = ' '.join(r.get('text', '') for r in ir['references'])
if 'textbackslash' in ref_text:
    print('BAD: textbackslash found in references!')
else:
    print('NO textbackslash in references - GOOD!')
