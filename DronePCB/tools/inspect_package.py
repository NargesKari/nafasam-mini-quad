from pathlib import Path
import pypdf, pypdfium2
p=Path('E:/DronePCB/references/TPS63021.pdf')
r=pypdf.PdfReader(p)
for i,page in enumerate(r.pages):
    t=page.extract_text() or ''
    if i>=len(r.pages)-5: print(i,t)
d=pypdfium2.PdfDocument(str(p))
for i in range(len(d)-4,len(d)):
    d[i].render(scale=1.5).to_pil().save(f'E:/DronePCB/preview/package-{i}.png')
