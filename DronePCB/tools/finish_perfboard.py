from pathlib import Path
import json,csv,collections,xml.etree.ElementTree as ET,zipfile
R=Path(__file__).resolve().parents[1];O=R/'prototype'
parts=json.loads((O/'connections.json').read_text()); expected={}
for a in parts:
 for pin,net in a['nets'].items():expected[(a['ref'],pin)]=net
actual={}
for net in ET.parse(O/'netlist.xml').getroot().find('nets'):
 name=net.attrib['name']
 if name.startswith('unconnected-'):continue
 for n in net.findall('node'):
  if not n.attrib['ref'].startswith('#'):actual[(n.attrib['ref'],n.attrib['pin'])]=name
diff=[{'ref':k[0],'pin':k[1],'expected':expected.get(k),'exported':actual.get(k)} for k in expected.keys()|actual.keys() if expected.get(k)!=actual.get(k)]
assert not diff,diff
# Independent topology assertions for four complete low-side motor stages.
for i in range(1,5):
 assert actual[(f'Q{i}','1')]==f'GATE{i}'
 assert actual[(f'Q{i}','2')]=='GND'
 assert actual[(f'Q{i}','3')]==actual[(f'D{i}','2')]==actual[(f'J{i+1}','2')]==actual[(f'C{i}','2')]==f'MOTOR{i}_NEG'
 assert actual[(f'D{i}','1')]==actual[(f'J{i+1}','1')]==actual[(f'C{i}','1')]=='VBAT'
 assert actual[(f'R{i}','1')]==f'PWM{i}' and actual[(f'R{i}','2')]==f'GATE{i}'
 assert actual[(f'R{i+4}','1')]==f'GATE{i}' and actual[(f'R{i+4}','2')]=='GND'
gpio={'motor1':14,'motor2':21,'motor3':47,'motor4':39,'imu_sda':41,'imu_scl':42,'imu_int':40,'battery_adc':1}
assert len(set(gpio.values()))==len(gpio)
assert not(set(gpio.values()) & {0,3,4,5,6,7,8,9,10,11,12,13,15,16,17,18,19,20,35,36,37,43,44,45,46,48})
for i in range(1,5):assert actual[('U1',str(gpio[f'motor{i}']))]==f'PWM{i}'
assert actual[('U1','1')]==actual[('R11','2')]==actual[('R12','1')]==actual[('C13','1')]=='VBAT_SENSE'
erc=json.loads((O/'erc.json').read_text());v=[a for s in erc['sheets'] for a in s['violations']]
report={'status':'Wiring reference for prototype; no physical assembly or flight validation','schematic_components':len(parts),'connected_pins_checked':len(actual),'connection_mismatches':diff,'erc_violations':v,'erc_ignored_checks':erc.get('ignored_checks',[]),'topology_checks':['Four MOSFET source/gate/drain connections','Four flyback diode polarities','Four motor-mounted capacitors across motors','Four gate resistors and source pulldowns','Battery divider midpoint','GPIO uniqueness and camera/strap/memory/USB exclusions'],'gpio':gpio,'constraints':['No SD card; GPIO39/40 repurposed','No GPIO JTAG on reused pins','Exact Freenove FNK0085 pinout','Use documented 3.3V-compatible MPU6050 module','AO3400A adapters require thermal/current checks','Firmware and assembled flight performance untested']}
(O/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
groups=collections.OrderedDict()
with (R/'BOM.csv').open(encoding='utf-8-sig') as f:
 for a in csv.DictReader(f):
  # Board wire pads do not require purchasing a separate connector.
  if a['Reference'].startswith('J') and a['Reference']!='J3':continue
  k=(a['Value_or_MPN'],a['Footprint']);groups.setdefault(k,[]).append(a)
lines=['# Shopping list — original SMD PCB A0','',
'This is the grouped parts list for the original custom PCB, **not** the perfboard prototype. Use prototype/shopping-list.md for the module build. Fit quantities are exact from BOM.csv; buy quantities include inexpensive spares. Reuse motors/battery and shared frame/propeller/charger/wiring items from the prototype shopping list. Do not purchase these bare-chip support circuits for the module version.','',
'Before ordering the custom PCB parts, confirm the selected camera flex matches the documented J3 pinout and choose the exact low-ESR bulk capacitor. Connector pads J1/J2/J4-J7 are solder pads already on the PCB, not purchased headers. A 3.3 V logic USB-UART programmer is required for this original board.','']
for (val,fp),items in groups.items():
 n=len(items);refs=', '.join(a['Reference'] for a in items);passive=items[0]['Reference'][0] in 'RC'
 buy=max(5,n+2) if passive else n+1 if items[0]['Reference'][0] in 'QD' else n
 lines.append(f'- [ ] **{val} — fit {n}; buy {buy}.** {refs}. Package: {fp or "off-board radial ceramic at motor terminals"}. {items[0]["Notes"]}')
lines.extend(['','## Additional original-board items','',
'- [ ] 1 × OV2640 flex camera assembly with the exact AI-Thinker v1.6 24-pin pinout and compatible contact side; the camera connector above does not include the sensor/lens assembly.',
'- [ ] 1 × USB-UART adapter using 3.3 V logic, plus programming wires; use the programming instructions in README.md.',
'- [ ] Custom four-layer PCB and appropriate stencil/assembly service or reflow tools; the bare QFN packages are not intended for direct perfboard installation.',
'- [ ] Four motors, battery and suitable connector, charger, frame, matched propellers, wiring and mechanical supplies: see the shared-hardware section of prototype/shopping-list.md.','',
'Original BOM.csv remains the per-reference source of truth. Electrical passives must meet the voltage/dielectric notes; CPOUT is 2.2 nF / 50 V. Manufacturer part numbers for generic resistors/capacitors and C11 remain sourcing choices.'])
(R/'shopping-list-original-PCB.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({'connected_pins':len(actual),'mismatches':len(diff),'erc_violations':len(v),'original_pcb_purchase_groups':len(groups)},indent=2))
assert not v
