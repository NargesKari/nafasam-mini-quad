import pcbnew as p, math, heapq, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];b=p.LoadBoard(str(ROOT/'design/DroneFC.kicad_pcb'))
def v(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
def xy(a):return p.ToMM(a.x),p.ToMM(a.y)
def distseg(q,a,z):
    dx=z[0]-a[0];dy=z[1]-a[1];u=max(0,min(1,((q[0]-a[0])*dx+(q[1]-a[1])*dy)/(dx*dx+dy*dy+1e-20)))
    return math.hypot(q[0]-a[0]-u*dx,q[1]-a[1]-u*dy)
padobs=[]
for f in b.GetFootprints():
    for pad in f.Pads():
        box=pad.GetBoundingBox();padobs.append((pad.GetNetname(),p.ToMM(box.GetX()),p.ToMM(box.GetY()),p.ToMM(box.GetRight()),p.ToMM(box.GetBottom()),pad.GetAttribute()==p.PAD_ATTRIB_NPTH))
vias=[];tracks=[]
for t in b.GetTracks():
    if isinstance(t,p.PCB_VIA):vias.append((*xy(t.GetPosition()),t.GetNetname(),p.ToMM(t.GetWidth(p.F_Cu))/2))
    else:tracks.append((xy(t.GetStart()),xy(t.GetEnd()),t.GetNetname(),p.ToMM(t.GetWidth()),t.GetLayer()))
def clear(q,net,rad,layer):
    x,y=q
    if not(100.6+rad<x<149.4-rad and 102.2+rad<y<149.4-rad):return False
    for n,x1,y1,x2,y2,hole in padobs:
        if n==net or (layer!=p.F_Cu and not hole):continue
        if math.hypot(max(x1-x,0,x-x2),max(y1-y,0,y-y2))<rad+.153:return False
    for xx,yy,n,r in vias:
        if n!=net and math.hypot(x-xx,y-yy)<rad+r+.153:return False
    for a,z,n,w,ly in tracks:
        if n!=net and ly==layer and distseg(q,a,z)<rad+w/2+.153:return False
    return True
def lineclear(a,z,net,w,layer):
    steps=max(1,math.ceil(math.dist(a,z)/.05));return all(clear((a[0]+(z[0]-a[0])*i/steps,a[1]+(z[1]-a[1])*i/steps),net,w/2,layer) for i in range(steps+1))
def track(a,z,net,layer=p.F_Cu,w=.15):
    if math.dist(a,z)<.001:return
    t=p.PCB_TRACK(b);t.SetStart(v(*a));t.SetEnd(v(*z));t.SetLayer(layer);t.SetWidth(p.FromMM(w));t.SetNet(net);b.Add(t);tracks.append((a,z,net.GetNetname(),w,layer))
def via(q,net):
    vv=p.PCB_VIA(b);vv.SetPosition(v(*q));vv.SetWidth(p.FromMM(.45));vv.SetDrill(p.FromMM(.2));vv.SetViaType(p.VIATYPE_THROUGH);vv.SetLayerPair(p.F_Cu,p.B_Cu);vv.SetNet(net);b.Add(vv);vias.append((*q,net.GetNetname(),.225))
def escape(a,net):
    n=net.GetNetname()
    offsets=[(0,0)]+[(r*math.cos(t*math.pi/16),r*math.sin(t*math.pi/16)) for r in [.5,.7,.9,1.1,1.4,1.8,2.2,2.7,3.2] for t in range(32)]
    for dx,dy in offsets:
        z=(round((a[0]+dx)*10)/10,round((a[1]+dy)*10)/10)
        if clear(z,n,.225,p.F_Cu) and clear(z,n,.225,p.B_Cu) and lineclear(a,z,n,.15,p.F_Cu):
            track(a,z,net);via(z,net);return z
    # A short bent escape may be necessary between neighbouring camera traces.
    queue=[(0,(0,0))];cost={(0,0):0};prev={};cache={}
    def point(q):return round(a[0]+q[0]*.1,5),round(a[1]+q[1]*.1,5)
    def ok(q):
        if q not in cache:cache[q]=clear(point(q),n,.076,p.F_Cu)
        return cache[q]
    while queue:
        g,q=heapq.heappop(queue)
        if cost[q]!=g:continue
        z=point(q)
        if g>0 and clear(z,n,.225,p.F_Cu) and clear(z,n,.225,p.B_Cu):
            path=[q]
            while path[-1]!=(0,0):path.append(prev[path[-1]])
            path.reverse()
            for aa,zz in zip(path,path[1:]):track(point(aa),point(zz),net)
            via(z,net);return z
        for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
            nxt=q[0]+dx,q[1]+dy
            if abs(nxt[0])>60 or abs(nxt[1])>60 or not ok(nxt):continue
            if dx and dy and (not ok((q[0]+dx,q[1])) or not ok((q[0],q[1]+dy))):continue
            ng=g+(1.414214 if dx and dy else 1)
            if ng<cost.get(nxt,1e99):cost[nxt]=ng;prev[nxt]=q;heapq.heappush(queue,(ng,nxt))
    raise RuntimeError('No front escape '+n+' '+str(a))
def route(a,z,net):
    name=net.GetNetname();st=(round(a[0]*10),round(a[1]*10));en=(round(z[0]*10),round(z[1]*10));cache={}
    def ok(q):
        if q not in cache:cache[q]=clear((q[0]/10,q[1]/10),name,.081,p.In2_Cu)
        return cache[q]
    def h(q):return math.hypot(q[0]-en[0],q[1]-en[1])
    queue=[(h(st),0,st)];cost={st:0};prev={}
    while queue:
        _,g,q=heapq.heappop(queue)
        if q==en:break
        if cost[q]!=g:continue
        for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
            nxt=q[0]+dx,q[1]+dy
            if not ok(nxt):continue
            if dx and dy and (not ok((q[0]+dx,q[1])) or not ok((q[0],q[1]+dy))):continue
            ng=g+(1.414214 if dx and dy else 1)
            if ng<cost.get(nxt,1e99):cost[nxt]=ng;prev[nxt]=q;heapq.heappush(queue,(ng+h(nxt),ng,nxt))
    else:raise RuntimeError('No inner route '+name)
    path=[en]
    while path[-1]!=st:path.append(prev[path[-1]])
    path.reverse();points=[a]+[(q[0]/10,q[1]/10) for q in path]+[z]
    # Compress collinear grid steps, preserving the verified path.
    simple=[points[0]]
    for i in range(1,len(points)-1):
        u=points[i][0]-simple[-1][0],points[i][1]-simple[-1][1];w=points[i+1][0]-points[i][0],points[i+1][1]-points[i][1]
        if abs(u[0]*w[1]-u[1]*w[0])>1e-8:simple.append(points[i])
    simple.append(points[-1])
    for aa,zz in zip(simple,simple[1:]):track(aa,zz,net,p.In2_Cu)
    return len(simple)-1
fs={f.GetReference():f for f in b.GetFootprints()};jp={a.GetNumber():a for a in fs['J3'].Pads()}
results=[]
for name,pin,other in [('CAM_RESET','19',(135.486,133.072)),('CAM_PCLK','8',(122.547,120.361))]:
    net=jp[pin].GetNet();start=escape(xy(jp[pin].GetPosition()),net)
    end=other if name=='CAM_RESET' else escape(other,net)
    results.append({'net':name,'start_via':start,'end_via':end,'inner2_segments':route(start,end,net)})
p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(ROOT/'design/DroneFC.kicad_pcb'),b)
(ROOT/'reports/manual-completion.json').write_text(json.dumps(results,indent=2));print(results)

