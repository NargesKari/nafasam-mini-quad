from pathlib import Path
from datetime import datetime,timezone
import json,zipfile,hashlib
R=Path(__file__).resolve().parents[1]
erc=json.loads((R/'reports/erc.json').read_text())
drc=json.loads((R/'reports/drc-final.json').read_text())
con=json.loads((R/'reports/connectivity.json').read_text())
ec=sum(len(s.get('violations',[])) for s in erc['sheets'])
assert ec==0 and not drc['violations'] and not drc['unconnected_items'] and not con['mismatches']
summary={'status':'Engineering prototype; not released for manufacture or flight',
 'generated_utc':datetime.now(timezone.utc).isoformat(),'kicad_version':'10.0.6',
 'board':{'width_mm':50,'height_mm':50,'thickness_mm':0.8,'copper_layers':4,'motor_drain_track_width_mm':0.8,'finished_copper_target_um':35},
 'checks':{'erc_violations':ec,'drc_violations':len(drc['violations']),'unconnected_items':len(drc['unconnected_items']),'connected_pins_compared':con['pcb_connected_pins'],'pin_net_mismatches':len(con['mismatches'])},
 'erc_ignored_checks':erc.get('ignored_checks',[]),'drc_ignored_checks':drc.get('ignored_checks',[]),
 'pending':['Exact camera flex pinout and mechanical compatibility','C11 manufacturer part number, ESR and ripple rating','Manufacturer stackup and assembler stencil/via treatment','Motor stall/startup and battery sag measurements','Power transient, thermal, IMU and camera bench tests','Flight firmware implementation and testing','Actual assembled mass, efficiency and thrust margin'],
 'sha256':{str(p.relative_to(R)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in [R/'design/DroneFC.kicad_pcb',R/'design/DroneFC.kicad_sch',R/'BOM.csv']}}
(R/'reports/validation-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
files=[]
for p in (R/'design').rglob('*'):
    if p.is_file() and (p.suffix in {'.kicad_pro','.kicad_pcb','.kicad_sch','.kicad_sym','.kicad_mod'} or p.name in {'fp-lib-table','sym-lib-table'}):files.append(p)
for name in ['README.md','BOM.csv','design_manifest.json','pin-map.json','drone_pins.h','reports/erc.json','reports/drc-final.json','reports/connectivity.json','reports/schematic.net.xml','reports/validation-summary.json','preview/board-final.svg','preview/board-final.png','preview/battery-plane.svg','preview/battery-plane.png','references/ESP32_CAM_V1.6.pdf']:
    files.append(R/name)
files.extend((R/'preview/schematic').glob('*.svg'))
out=R/'DroneFC-prototype-A0.zip'
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(files):z.write(p,str(p.relative_to(R)))
with zipfile.ZipFile(out) as z:
    assert z.testzip() is None
    assert 'design/Drone.pretty/TI_DSJ14_TPS63021.kicad_mod' in z.namelist()
print(json.dumps({'archive':str(out),'file_count':len(files),'bytes':out.stat().st_size,'checks':summary['checks']},indent=2))
