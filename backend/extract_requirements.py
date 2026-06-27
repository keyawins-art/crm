from pathlib import Path
import docx

p = Path(r'C:\Users\vikas\Downloads\Enterprise_CRM_Requirements_Document.docx')
print('exists', p.exists(), p)
if not p.exists():
    raise SystemExit(1)

doc = docx.Document(p)
text = '\n'.join([para.text for para in doc.paragraphs if para.text.strip()])
print(text[:30000])
