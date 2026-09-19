import pcbnew as p, math, json, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; b=p.LoadBoard(str(ROOT/'design/DroneFC.kicad_pcb'))
def v(x,y): return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
def pos(a): return p.ToMM(a.GetPosition().x),p.ToMM(a.GetPosition().y)
fs={f.GetReference():f for f in b.GetFootprints()}
fs['L1'].SetOrientationDegrees(180)
# Move board title onto the clear underside and clip the module's off-board silk.
for t in b.GetDrawings():
    if isinstance(t,p.PCB_TEXT) and t.GetLayer()==p.F_SilkS:
        t.SetLayer(p.B_SilkS); t.SetMirrored(True); t.SetTextSize(v(1,1)); t.SetPosition(v(125,120)); t.SetText('DroneFC A0 - DRAFT')
for g in list(fs['U1'].GraphicalItems()):
    if g.GetLayer()==p.F_SilkS and p.ToMM(g.GetBoundingBox().GetY())<100.3: g.SetLayer(p.F_Fab)

pads=[a for f in b.GetFootprints() for a in f.Pads() if a.GetLayerSet().Contains(p.F_Cu)]
obstacles=[]
for a in pads:
    bb=a.GetBoundingBox(); obstacles.append((a.GetNetname(),p.ToMM(bb.GetX()),p.ToMM(bb.GetY()),p.ToMM(bb.GetRight()),p.ToMM(bb.GetBottom())))
vias=[]; traces=[]
def clearpoint(x,y,net,r):
    if not(100.3+r<x<149.7-r and 102.1+r<y<149.7-r): return False
    for other,x1,y1,x2,y2 in obstacles:
        if other==net: continue
        dx=max(x1-x,0,x-x2); dy=max(y1-y,0,y-y2)
        if dx*dx+dy*dy<(r+.15)**2: return False
    for nx,ny,other,rr in vias:
        if other!=net and (nx-x)**2+(ny-y)**2<(r+rr+.15)**2:return False
    for ax,ay,bx,by,other,w in traces:
        if other==net:continue
        dx,dy=bx-ax,by-ay; u=max(0,min(1,((x-ax)*dx+(y-ay)*dy)/(dx*dx+dy*dy+1e-12)))
        if (x-ax-u*dx)**2+(y-ay-u*dy)**2<(r+w/2+.15)**2:return False
    return True
def clearline(a,z,net,w):
    d=math.dist(a,z); n=max(1,math.ceil(d/.08))
    return all(clearpoint(a[0]+(z[0]-a[0])*i/n,a[1]+(z[1]-a[1])*i/n,net,w/2) for i in range(n+1))
def track(a,z,net,width):
    if math.dist(a,z)<.001:return
    t=p.PCB_TRACK(b);t.SetStart(v(*a));t.SetEnd(v(*z));t.SetLayer(p.F_Cu);t.SetWidth(p.FromMM(width));t.SetNet(net);b.Add(t)
    traces.append((*a,*z,net.GetNetname(),width))
def via(x,y,net,d=.5,dr=.25):
    vv=p.PCB_VIA(b);vv.SetPosition(v(x,y));vv.SetWidth(p.FromMM(d));vv.SetDrill(p.FromMM(dr));vv.SetViaType(p.VIATYPE_THROUGH);vv.SetLayerPair(p.F_Cu,p.B_Cu);vv.SetNet(net);b.Add(vv);vias.append((x,y,net.GetNetname(),d/2))
failed=[]
for netname in ['GND','VBAT']:
    for a in [a for a in pads if a.GetNetname()==netname]:
        xy=pos(a); ref=p.Cast_to_FOOTPRINT(a.GetParent()).GetReference()
        high=ref in ['J2','J4','J5','J6','J7','D1','D2','D3','D4','Q1','Q2','Q3','Q4']
        count=6 if ref=='J2' else (3 if high else 1)
        diameter=.6 if high else .45; drill=.3 if high else .2
        # Wide source pad fanout for motor current; thin signal-cap fanout otherwise.
        width=.55 if high else .2
        candidates=[(0,0)]+[(r*math.cos(t*math.pi/8),r*math.sin(t*math.pi/8)) for r in [.6,.8,1,1.2,1.5,1.8,2.2,2.7] for t in range(16)]
        made=[]
        for dx,dy in candidates:
            z=round(xy[0]+dx,4),round(xy[1]+dy,4)
            if any(math.dist(z,(nx,ny))<diameter+.12 for nx,ny,nn,rr in vias):continue
            if clearpoint(*z,netname,diameter/2) and clearline(xy,z,netname,width):
                via(*z,a.GetNet(),diameter,drill);track(xy,z,a.GetNet(),width);made.append(z)
                if len(made)>=count:break
        if len(made)<count:failed.append([ref,a.GetNumber(),netname,len(made),count])
    layer=p.In1_Cu if netname=='GND' else p.In2_Cu
    zone=p.ZONE(b);zone.SetLayer(layer);zone.SetNet(next(a.GetNet() for a in pads if a.GetNetname()==netname));zone.SetLocalClearance(p.FromMM(.2));zone.SetPadConnection(p.ZONE_CONNECTION_FULL);zone.SetMinThickness(p.FromMM(.2));zone.Outline().NewOutline()
    for x,y in [(100.3,102.1),(149.7,102.1),(149.7,149.7),(100.3,149.7)]:zone.Outline().Append(p.FromMM(x),p.FromMM(y))
    b.Add(zone)
p.ZONE_FILLER(b).Fill(b.Zones())
p.SaveBoard(str(ROOT/'design/DroneFC.kicad_pcb'),b)
p.ExportSpecctraDSN(b,str(ROOT/'design/DroneFC.dsn'))
# Supply planes occupy internal layers; autorouting is constrained to outer layers.
f=ROOT/'design/DroneFC.dsn';s=f.read_text()
s=s.replace('(layer In1.Cu\n      (type signal)','(layer In1.Cu\n      (type power)').replace('(layer In2.Cu\n      (type signal)','(layer In2.Cu\n      (type power)')
# KiCad API exports default net classes; add explicit motor and logic-power classes.
special={'MOTOR1_NEG':800,'MOTOR2_NEG':800,'MOTOR3_NEG':800,'MOTOR4_NEG':800,'SW1':450,'SW2':450,'3V3':350,'CAM_1V2':300,'CAM_2V8':300}
start=s.index('    (class kicad_default'); end=s.index('      (circuit',start)
head=s[start:end]
for n in special: head=re.sub(r'(?<![\w])'+re.escape(n)+r'(?![\w])','',head)
s=s[:start]+head+s[end:]
idx=s.rfind('  (wiring')
classes='\n'.join(f'    (class cls_{n} {n} (circuit (use_via "Via[0-3]_600:300_um")) (rule (width {w}) (clearance 200)))' for n,w in special.items())
# Insert inside network, before its closing parenthesis.
close=s.rfind('  )',0,idx);s=s[:close]+classes+'\n'+s[close:]
f.write_text(s)
(ROOT/'reports/power-fanout.json').write_text(json.dumps({'via_count':len(vias),'shortfalls':failed},indent=2));print('Power fanout',len(vias),'vias; shortfalls',failed)


