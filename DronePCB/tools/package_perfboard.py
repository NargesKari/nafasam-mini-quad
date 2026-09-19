from pathlib import Path
import zipfile,json
R=Path(__file__).resolve().parents[1];O=R/'prototype';out=R/'Drone-perfboard-P1.zip'
files=[p for p in O.rglob('*') if p.is_file() and p.suffix not in {'.kicad_prl','.lck'}]
files += [R/'shopping-list-original-PCB.md',R/'BOM.csv']
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
 for p in files:z.write(p,str(p.relative_to(R)))
with zipfile.ZipFile(out) as z:assert z.testzip() is None
print(json.dumps({'archive':str(out),'files':len(files),'bytes':out.stat().st_size},indent=2))
