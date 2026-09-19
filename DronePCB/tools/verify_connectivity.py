"""Independent schematic-export to PCB connectivity comparison."""
import pcbnew as p, xml.etree.ElementTree as E, json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
root=E.parse(R/'reports/schematic.net.xml').getroot()
expected={}
for net in root.find('nets'):
    if net.attrib['name'].startswith('unconnected-'):continue
    for n in net.findall('node'):expected[(n.attrib['ref'],n.attrib['pin'])]=net.attrib['name']
b=p.LoadBoard(str(R/'design/DroneFC.kicad_pcb'))
actual={}; mismatch=[]
for f in b.GetFootprints():
    for pad in f.Pads():
        key=f.GetReference(),pad.GetNumber()
        if pad.GetNetname():actual[key]=pad.GetNetname()
offboard={x['ref'] for x in json.loads((R/'design_manifest.json').read_text()) if not x['onboard']}
expected={k:v for k,v in expected.items() if k[0] not in offboard and not k[0].startswith('#')}
for key in expected.keys()|actual.keys():
    if expected.get(key)!=actual.get(key):mismatch.append({'ref':key[0],'pin':key[1],'schematic':expected.get(key),'pcb':actual.get(key)})
report={'schematic_connected_pins':len(expected),'pcb_connected_pins':len(actual),'mismatches':mismatch,'offboard_components':sorted(offboard)}
(R/'reports/connectivity.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2));assert not mismatch
