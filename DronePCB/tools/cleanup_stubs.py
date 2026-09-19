import subprocess, json, os, sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];os.environ['KICAD_CONFIG_HOME']=str(R/'config')
if '--worker' in sys.argv:
    import pcbnew as p
    d=json.loads((R/'reports/drc-final.json').read_text())
    ids={i['uuid'] for x in d['violations'] if x['type'] in ['track_dangling','via_dangling'] for i in x['items']}
    b=p.LoadBoard(str(R/'design/DroneFC.kicad_pcb'))
    for t in list(b.GetTracks()):
        if t.m_Uuid.AsString() in ids:b.Remove(t)
    p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(R/'design/DroneFC.kicad_pcb'),b)
    sys.exit(0)
for attempt in range(15):
    subprocess.run(['E:/kiCad/bin/kicad-cli.exe','pcb','drc','--format','json','-o',str(R/'reports/drc-final.json'),str(R/'design/DroneFC.kicad_pcb')],capture_output=True,check=True)
    d=json.loads((R/'reports/drc-final.json').read_text())
    assert not d['unconnected_items'], 'Cleanup must not break connectivity'
    ids={i['uuid'] for x in d['violations'] if x['type'] in ['track_dangling','via_dangling'] for i in x['items']}
    if not ids:
        print('Final DRC:',len(d['violations']),'violations;',len(d['unconnected_items']),'unconnected');break
    subprocess.run([sys.executable,__file__,'--worker'],check=True,capture_output=True)
    print('Removed',len(ids),'unused routing pieces')
else:raise RuntimeError('More cleanup required')
