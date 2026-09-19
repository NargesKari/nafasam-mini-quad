"""Create a separate module-and-wire KiCad schematic; never modifies the SMD design."""
import sys,json,math,uuid,collections,csv
from pathlib import Path
from sexpr import *
R=Path(__file__).resolve().parents[1]; O=R/'prototype'; O.mkdir(exist_ok=True)
uid=lambda:str(uuid.uuid4())
stable=lambda s:str(uuid.uuid5(uuid.NAMESPACE_URL,'drone-perfboard/'+s))
symbols={}; parts=[]
def sym(lib,name):
 k=lib+':'+name;s=load_symbol(lib,name);s[1]=k;symbols[k]=s;return k
def module(name,left,right):
 h=(max(len(left),len(right))+1)*2.54/2; pintexts=[]
 for side,defs in enumerate([left,right]):
  for i,(num,label,typ) in enumerate(defs):
   pintexts.append(f'(pin {typ} line (at {(-20.32 if side==0 else 20.32)} {h-2.54*(i+1)} {0 if side==0 else 180}) (length 5.08) (name "{label}" (effects (font (size 1 1)))) (number "{num}" (effects (font (size 1 1)))))')
 k='Perfboard:'+name
 symbols[k]=parse(f'(symbol "{k}" (pin_names (offset 1)) (in_bom yes) (on_board yes) (property "Reference" "U" (at 0 {h+5} 0) (effects (font (size 1 1)))) (property "Value" "{name}" (at 0 {h+2.5} 0) (effects (font (size 1 1)))) (symbol "{name}_0_1" (rectangle (start -15.24 {h}) (end 15.24 {-h}) (stroke (width .254) (type default)) (fill (type background)))) (symbol "{name}_1_1" {" ".join(pintexts)}))')
 return k
def add(ref,lib,val,nets,page,x,y,note=''):
 parts.append(dict(ref=ref,lib=lib,value=val,nets={str(k):v for k,v in nets.items()},page=page,x=x,y=y,note=note))
res=sym('Device','R'); cap=sym('Device','C'); pol=sym('Device','C_Polarized'); fet=sym('Transistor_FET','AO3400A'); diode=sym('Device','D_Schottky'); conn=sym('Connector_Generic','Conn_01x02'); flag=sym('power','PWR_FLAG')
mcu=module('Freenove_S3_CAM_Interface',[('5V','5V_IN','power_in'),('GND','GND','power_in'),('3V3','3V3_OUT','power_out'),('1','GPIO1_ADC','input'),('41','GPIO41_SDA','bidirectional'),('42','GPIO42_SCL','output'),('40','GPIO40_INT','input')],[('14','GPIO14_M1','output'),('21','GPIO21_M2','output'),('47','GPIO47_M3','output'),('39','GPIO39_M4','output')])
imu=module('MPU6050_Breakout_Interface',[('VIN','VIN_3V3','power_in'),('GND','GND','power_in'),('AD0','AD0','input')],[('SDA','SDA','bidirectional'),('SCL','SCL','input'),('INT','INT','output')])
boost=module('U3V40F5_Interface',[('VIN','VIN_1S','power_in'),('GND','GND','power_in')],[('VOUT','VOUT_5V','power_out'),('EN','EN_LEAVE_OPEN','input')])
add('U1',mcu,'Freenove FNK0085 + supplied OV2640',{'5V':'5V','GND':'GND','3V3':'3V3','1':'VBAT_SENSE','41':'IMU_SDA','42':'IMU_SCL','40':'IMU_INT','14':'PWM1','21':'PWM2','47':'PWM3','39':'PWM4'},1,105.41,78.74,'Interface pin identifiers are header labels, not sequential physical pin numbers. No SD card.')
add('U2',imu,'Adafruit MPU-6050 breakout',{'VIN':'3V3','GND':'GND','AD0':'GND','SDA':'IMU_SDA','SCL':'IMU_SCL','INT':'IMU_INT'},1,281.94,78.74,'VIN at 3.3V; leave 3Vo and auxiliary pins unused; address 0x68')
add('U3',boost,'Pololu U3V40F5 / fixed 5V',{'VIN':'VBAT','GND':'GND','VOUT':'5V'},2,111.76,63.5,'EN left open; tie both VIN pads to VBAT and both GND pads to ground. No motor current through regulator.')
add('J1',conn,'1S LiPo battery connector',{1:'VBAT',2:'GND'},2,40.64,63.5,'Battery connector must support measured aggregate current; unplug to disconnect')
for i,net,x in [(9,'IMU_SDA',233.68),(10,'IMU_SCL',330.2)]:add('R'+str(i),res,'4.7k',{1:'3V3',2:net},1,x,132.08)
add('R11',res,'100k 1%',{1:'VBAT',2:'VBAT_SENSE'},1,50.8,162.56)
add('R12',res,'100k 1%',{1:'VBAT_SENSE',2:'GND'},1,111.76,162.56)
add('C13',cap,'100nF 16V',{1:'VBAT_SENSE',2:'GND'},1,172.72,162.56)
add('C14',cap,'100nF 16V',{1:'3V3',2:'GND'},1,233.68,190.5)
add('C15',pol,'10uF 10V',{1:'3V3',2:'GND'},1,330.2,190.5)
for ref,val,net,x,y in [('C9','470uF 10V LOW ESR','VBAT',172.72,132.08),('C10','47uF 10V','VBAT',233.68,132.08),('C11','100uF 10V','5V',294.64,132.08)]:add(ref,pol,val,{1:net,2:'GND'},2,x,y)
add('C12',cap,'100nF 16V',{1:'5V',2:'GND'},2,355.6,132.08)
for i in range(1,5):
 page=3+(i-1)//2;y=73.66+((i-1)%2)*101.6
 add('Q'+str(i),fet,'AO3400A on SOT-23 adapter',{1:f'GATE{i}',2:'GND',3:f'MOTOR{i}_NEG'},page,175.26,y)
 add('R'+str(i),res,'100R',{1:f'PWM{i}',2:f'GATE{i}'},page,40.64,y)
 add('R'+str(i+4),res,'10k',{1:f'GATE{i}',2:'GND'},page,106.68,y)
 add('D'+str(i),diode,'1N5822 3A 40V',{1:'VBAT',2:f'MOTOR{i}_NEG'},page,246.38,y,'Banded cathode pin1 to battery positive; anode pin2 to drain')
 add('J'+str(i+1),conn,f'8520 MOTOR {i}',{1:'VBAT',2:f'MOTOR{i}_NEG'},page,332.74,y)
 add('C'+str(i),cap,'100nF 16V AT MOTOR',{1:'VBAT',2:f'MOTOR{i}_NEG'},page,332.74,y+36.83,'Solder directly across motor terminals')
 add('C'+str(i+4),pol,'10uF 10V LOCAL',{1:'VBAT',2:'GND'},page,246.38,y+36.83)
rootid=stable('root');pages={i:stable(str(i)) for i in range(1,5)};titles={1:'Controller, IMU and battery sensing',2:'Battery and electronics power',3:'Motor channels 1 and 2',4:'Motor channels 3 and 4'}
def esc(x):return json.dumps(str(x))
def text(t,x,y,size=1.5):return f'(text {esc(t)} (at {x} {y} 0) (effects (font (size {size} {size})) (justify left)) (uuid {uid()}))'
def label(net,x,y,angle):return f'(global_label {esc(net)} (shape bidirectional) (at {x} {y} {angle}) (effects (font (size 1 1)) (justify {"right" if angle==0 else "left"})) (uuid {uid()}) (property "Intersheetrefs" "" (at {x} {y} 0) (effects (font (size 1 1)) hide)))'
for page,title in titles.items():
 pp=[a for a in parts if a['page']==page];ids={a['lib'] for a in pp}|{flag}
 out=[f'(kicad_sch (version 20250114) (generator "eeschema") (uuid {pages[page]}) (paper "A3") (title_block (title {esc(title)}) (rev "P1 PROTOTYPE") (comment 1 "Soldered perfboard / follow named nets and manufacturer header labels"))','(lib_symbols '+' '.join(dump(symbols[k]) for k in sorted(ids))+')',text(title,20.32,17.78,2.54)]
 for a in pp:
  s=symbols[a['lib']];x=a['x'];y=a['y'];top=y-max(float(child(pi,'at')[2]) for pi in pins(s))-12.7
  props=f'(property "Reference" "{a["ref"]}" (at {x} {top} 0) (effects (font (size 1.27 1.27)))) (property "Value" {esc(a["value"])} (at {x} {top+3} 0) (effects (font (size 1.1 1.1))))'
  out.append(f'(symbol (lib_id {esc(a["lib"])}) (at {x} {y} 0) (unit 1) (in_bom yes) (on_board yes) (dnp no) (uuid {stable(a["ref"])}) {props} (instances (project "Perfboard" (path "/{rootid}/{pages[page]}" (reference "{a["ref"]}") (unit 1)))))')
  for pi in pins(s):
   num=child(pi,'number')[1];dx,dy,angle=map(float,child(pi,'at')[1:]);xx=round(x+dx,4);yy=round(y-dy,4);net=a['nets'].get(num)
   if net:
    vx=-math.cos(math.radians(angle));vy=math.sin(math.radians(angle));ex=round(xx+vx*5.08,4);ey=round(yy+vy*5.08,4)
    out.append(f'(wire (pts (xy {xx} {yy}) (xy {ex} {ey})) (stroke (width 0) (type default)) (uuid {uid()}))');out.append(label(net,ex,ey,(0 if dx<0 else 180) if abs(vx)<.1 else (0 if vx<0 else 180)))
   else:out.append(f'(no_connect (at {xx} {yy}) (uuid {uid()}))')
 if page==2:
  for j,net in enumerate(['VBAT','GND']):
   x=40.64+j*50.8;y=193.04;ref='#FLG'+str(j)
   out.append(f'(symbol (lib_id "power:PWR_FLAG") (at {x} {y} 0) (unit 1) (in_bom no) (on_board yes) (dnp no) (uuid {uid()}) (property "Reference" "{ref}" (at {x} {y-4} 0) (effects (font (size 1 1)) hide)) (property "Value" "PWR_FLAG" (at {x} {y-3} 0) (effects (font (size 1 1)))) (instances (project "Perfboard" (path "/{rootid}/{pages[page]}" (reference "{ref}") (unit 1)))))');out.append(label(net,x,y,0))
 notes={1:['U1 is the FNK0085 camera board. Use header labels, not schematic pin positions.','Camera stays on the supplied flex. No SD card: GPIO39 and GPIO40 are reused.','U2 is a complete 3.3V-compatible MPU-6050 breakout; not the bare chip.','Do not use this pin map on an AI-Thinker ESP32-CAM or another board without checking.'],2:['C9 at battery distribution; C10 at boost VIN; C11/C12 at ESP board 5V input.','Battery powers motors directly. Only electronics receive boosted 5V.','Disconnect LiPo before USB programming. All grounds meet at battery negative.','The boost is not a LiPo cutoff. Firmware voltage monitoring and disarming are required.'],3:['Repeat identical driver wiring for each motor. Diode band points to VBAT.','Q pin1=gate, pin2=source/GND, pin3=drain. Check adapter pad mapping.','C1/C2 go directly on motors; C5/C6 go near the driver power wiring.'],4:['Repeat identical driver wiring for each motor. Motor numbering is assigned in firmware.','Use short soldered power wires; no Dupont leads or perfboard solder bridges for motor current.','AO3400A adapter thermal performance must be measured with actual motor load.']}[page]
 for n,t in enumerate(notes):out.append(text(t,20.32,245+n*6,1.35))
 out.append(')');(O/f'sheet{page}.kicad_sch').write_text('\n'.join(out))
out=[f'(kicad_sch (version 20250114) (generator "eeschema") (uuid {rootid}) (paper "A4") (lib_symbols)',text('Drone perfboard prototype P1',20.32,20.32,2.54),text('Freenove ESP32-S3 camera board / MPU-6050 module / four AO3400A drivers',20.32,33.02,1.35)]
for i,title in titles.items():
 x=25.4+(i-1)%2*132.08;y=60.96+(i-1)//2*55.88
 out.append(f'(sheet (at {x} {y}) (size 111.76 30.48) (stroke (width .15) (type default)) (fill (color 0 0 0 0)) (uuid {pages[i]}) (property "Sheetname" {esc(title)} (at {x} {y-2} 0) (effects (font (size 1 1)) (justify left bottom))) (property "Sheetfile" "sheet{i}.kicad_sch" (at {x} {y+32.48} 0) (effects (font (size 1 1)) (justify left top))) (instances (project "Perfboard" (path "/{rootid}" (page "{i+1}")))))')
out.append('(sheet_instances (path "/" (page "1"))))');(O/'Perfboard.kicad_sch').write_text('\n'.join(out))
stab=['(sym_lib_table (version 7)']
for lib in sorted({k.split(':')[0] for k in symbols}):
 (O/(lib+'.kicad_sym')).write_text('(kicad_symbol_lib (version 20250114) (generator "kicad_symbol_editor") '+' '.join(dump([s[0],s[1].split(':')[1],*s[2:]]) for k,s in symbols.items() if k.startswith(lib+':'))+')')
 stab.append(f'(lib (name "{lib}") (type "KiCad") (uri "${{KIPRJMOD}}/{lib}.kicad_sym") (options "") (descr "Portable symbols"))')
(O/'sym-lib-table').write_text('\n'.join(stab)+')')
(O/'Perfboard.kicad_pro').write_text(json.dumps({'meta':{'filename':'Perfboard.kicad_pro','version':1}},indent=2))
(O/'connections.json').write_text(json.dumps(parts,indent=2))
nets=collections.defaultdict(list)
for a in parts:
 for pin,net in a['nets'].items():nets[net].append(a['ref']+'.'+pin)
(O/'wire-list.md').write_text('# Perfboard point-to-point connections\n\nModule pin identifiers below are **printed header labels**, not physical pin numbers. Q1-Q4 use the actual AO3400A pin numbers. All points on the same line connect together.\n\n'+'\n'.join('- **'+net+'**: '+', '.join(points) for net,points in sorted(nets.items()))+'\n')
(O/'perfboard_pins.h').write_text('''#pragma once
// Freenove FNK0085 only. Header definitions, not flight firmware.
// Do not enable the SD card or external GPIO JTAG.
#define MOTOR1_GPIO 14
#define MOTOR2_GPIO 21
#define MOTOR3_GPIO 47
#define MOTOR4_GPIO 39
#define IMU_SDA_GPIO 41
#define IMU_SCL_GPIO 42
#define IMU_INT_GPIO 40
#define BATTERY_ADC_GPIO 1
#define BATTERY_DIVIDER_RATIO 2.0f
#define IMU_I2C_ADDRESS 0x68
// Camera pin profile: CAMERA_MODEL_ESP32S3_EYE in Freenove's camera example.
// Give camera XCLK and motor PWM separate LEDC timers/channels.
''')
print('Created perfboard schematic:',len(parts),'components;',len(nets),'nets')
