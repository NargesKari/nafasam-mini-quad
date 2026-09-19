import pcbnew as p, json, math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
b=p.LoadBoard(str(ROOT/'design/DroneFC.kicad_pcb'))
def vec(x,y): return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
def box(f):
    gs=[g.GetBoundingBox() for g in f.GraphicalItems() if g.GetLayer()==p.F_CrtYd]
    if not gs: gs=[a.GetBoundingBox() for a in f.Pads()]
    return [min(p.ToMM(g.GetX()) for g in gs),min(p.ToMM(g.GetY()) for g in gs),max(p.ToMM(g.GetRight()) for g in gs),max(p.ToMM(g.GetBottom()) for g in gs)]
def overlap(a,z): return a[0]<z[2]+.05 and a[2]>z[0]-.05 and a[1]<z[3]+.05 and a[3]>z[1]-.05
fs={f.GetReference():f for f in b.GetFootprints()}
# Move mounting holes away from antenna and motor paths; retain 44 x 26mm pattern.
for ref,f in fs.items():
    if ref.startswith('H'):
        old=p.ToMM(f.GetPosition().y); f.SetPosition(vec(p.ToMM(f.GetPosition().x),106 if old<120 else 132))
for ref in ['C5','C6','C8','C9','C10']:
    fs[ref].SetOrientationDegrees(0)
for ref,xy in {'U2':(111,125),'L1':(111,129),'C5':(114,125),'C6':(114,127),'C7':(108,122),'C8':(108,125),'C9':(108,127),'C10':(108,129),'R1':(136,104),'C3':(136,106),'C14':(121,126),'C15':(121,128),'C13':(129,125),'C11':(116,145),'D1':(106,118),'D2':(144,118),'D3':(107,138),'D4':(144,147)}.items(): fs[ref].SetPosition(vec(*xy))
priority=['U1','C11','U2','L1','U3','J3','U4','U5','J2','J1']
priority += [k for k in fs if k.startswith('H')]
priority += [f'J{i}' for i in range(4,8)]+[f'Q{i}' for i in range(1,5)]+[f'D{i}' for i in range(1,5)]
priority += [k for k in fs if k not in priority]
occupied=[[102.3,82.25,147.7,102.0]]; changed=[]
offsets=sorted([(dx*.5,dy*.5) for dx in range(-16,17) for dy in range(-16,17)],key=lambda xy:xy[0]**2+xy[1]**2)
for ref in priority:
    f=fs[ref]; original=f.GetPosition(); x,y=p.ToMM(original.x),p.ToMM(original.y)
    if ref=='U1': occupied.append([117,102,133,117.6]); continue
    found=False
    for dx,dy in offsets:
        f.SetPosition(vec(x+dx,y+dy)); bb=box(f)
        if min(bb[:2])<100.25 or max(bb[2:])>149.75: continue
        if any(overlap(bb,z) for z in occupied): continue
        occupied.append(bb); found=True
        if dx or dy: changed.append([ref,x+dx,y+dy])
        break
    if not found: raise RuntimeError('Cannot place '+ref+' occupied='+str(occupied)+' current='+str(box(f)))
for f in b.GetFootprints():
    f.Reference().SetVisible(False)
    # Reference graphics go in assembly layer; keep component-outline silkscreen.
    f.Value().SetVisible(False)
for f in b.GetFootprints():
    if f.GetReference().startswith(('J','Q','U')):
        bb=box(f); t=p.PCB_TEXT(b); t.SetText(f.GetReference()); t.SetPosition(vec((bb[0]+bb[2])/2,bb[3]+.7)); t.SetTextSize(vec(.8,.8)); t.SetTextThickness(p.FromMM(.12)); t.SetLayer(p.F_Fab); b.Add(t)
p.SaveBoard(str(ROOT/'design/DroneFC.kicad_pcb'),b)
(ROOT/'reports/placement-adjustments.json').write_text(json.dumps(changed,indent=2))
print('Placed',len(fs),'footprints with nonoverlapping courtyards')



