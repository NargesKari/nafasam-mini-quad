"""Generate editable KiCad design from a shared, reviewable connectivity manifest."""
import sys, json, uuid, math, copy, csv, shutil
from pathlib import Path
from sexpr import *
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'design'; OUT.mkdir(exist_ok=True)
LIB=Path('E:/kiCad/share/kicad')
uid=lambda: str(uuid.uuid4())
stable=lambda s: str(uuid.uuid5(uuid.NAMESPACE_URL,'dronepcb/'+s))
symbols={}; parts=[]

def sym(lib,name):
    key=lib+':'+name
    if key not in symbols:
        s=load_symbol(lib,name); s[1]=key; symbols[key]=s
    return key

def custom(name,pindefs,fp):
    key='Drone:'+name; height=2.54*(max(len(pindefs[0]),len(pindefs[1]))+1)/2
    ptxt=[]
    for side,defs in enumerate(pindefs):
        for i,(num,n,typ) in enumerate(defs):
            x=-15.24 if side==0 else 15.24; y=height-2.54*(i+1)
            ptxt.append(f'(pin {typ} line (at {x} {y} {0 if side==0 else 180}) (length 2.54) (name "{n}" (effects (font (size 1 1)))) (number "{num}" (effects (font (size 1 1)))))')
    s=parse(f'(symbol "{key}" (pin_names (offset 1)) (in_bom yes) (on_board yes) (property "Reference" "U" (at 0 {height+3} 0) (effects (font (size 1.27 1.27)))) (property "Value" "{name}" (at 0 {height+1} 0) (effects (font (size 1.27 1.27)))) (property "Footprint" "{fp}" (at 0 0 0) (effects (font (size 1 1)) hide)) (symbol "{name}_0_1" (rectangle (start -12.7 {height}) (end 12.7 {-height}) (stroke (width 0.254) (type default)) (fill (type background)))) (symbol "{name}_1_1" {" ".join(ptxt)}))')
    symbols[key]=s; return key

def add(ref,lib,value,nets,page,x,y,px,py,rot=0,fp=None,note='',onboard=True):
    s=symbols[lib]
    if fp is None: fp=next((p[2] for p in children(s,'property') if p[1]=='Footprint'),'')
    p=dict(ref=ref,lib=lib,value=value,nets={str(k):v for k,v in nets.items()},page=page,sch=[x,y],pcb=[px,py,rot],fp=fp,note=note,onboard=onboard,uuid=stable(ref))
    parts.append(p); return p

R=sym('Device','R'); C=sym('Device','C'); CP=sym('Device','C_Polarized'); Q=sym('Transistor_FET','AO3400A'); D=sym('Device','D_Schottky'); L=sym('Device','L'); CON2=sym('Connector_Generic','Conn_01x02'); CON6=sym('Connector_Generic','Conn_01x06')
FLAG=sym('power','PWR_FLAG')
RFP='Resistor_SMD:R_0402_1005Metric'; CFP='Capacitor_SMD:C_0402_1005Metric'
def r(ref,value,n1,n2,page,x,y,px,py,rot=0,note='1%, 0402'):
    return add(ref,R,value,{1:n1,2:n2},page,x,y,px,py,rot,fp=RFP,note=note)
def c(ref,value,n1,page,x,y,px,py,rot=0,fp=CFP,note='X7R, 10V; use specified voltage where marked',n2='GND'):
    return add(ref,C,value,{1:n1,2:n2},page,x,y,px,py,rot,fp=fp,note=note)

# Controller: keep straps, flash/PSRAM and USB pins free of motor outputs.
mcu=sym('RF_Module','ESP32-S3-MINI-1')
mn={str(i):'GND' for i in [1,2,42,43,*range(46,66)]}
mn.update({'3':'3V3','4':'BOOT','5':'VBAT_SENSE','8':'CAM_PWDN','9':'CAM_SDA','10':'CAM_SCL','11':'CAM_XCLK_SRC','20':'CAM_PCLK','21':'CAM_HREF','22':'CAM_VSYNC','25':'IMU_INT','28':'IMU_SDA','29':'IMU_SCL','35':'PWM1','36':'PWM2','37':'PWM3','38':'PWM4','39':'UART_TX','40':'UART_RX','45':'ESP_EN'})
mn.update({str(12+i):f'CAM_D{i}' for i in range(8)})
add('U1',mcu,'ESP32-S3-MINI-1-N4R2',mn,1,100,90,125,107,note='4MB flash / 2MB PSRAM; module antenna extends beyond top board edge')
c('C1','10uF','3V3',1,195,45,115,105,90,fp='Capacitor_SMD:C_0603_1608Metric')
c('C2','100nF','3V3',1,245,45,115,107,90)
r('R1','10k','3V3','ESP_EN',1,195,95,136,102,90)
c('C3','1uF','ESP_EN',1,245,95,136,104,90)
r('R2','10k','3V3','BOOT',1,195,145,115,109,90)
add('J1',CON6,'3.3V UART programmer pads',{1:'GND',2:'3V3',3:'UART_TX',4:'UART_RX',5:'BOOT',6:'ESP_EN'},1,315,90,141,108,fp='Drone:Programming_6',note='External programmer: 3.3V logic only; pin2 reference only with battery attached')
r('R3','100k','VBAT','VBAT_SENSE',1,195,200,112,119,90)
r('R4','100k','VBAT_SENSE','GND',1,245,200,114,119,90)
c('C4','100nF','VBAT_SENSE',1,295,200,116,119,90)

# Efficient fixed 3.3V buck-boost supply, TI TPS63021 reference architecture.
reg=custom('TPS63021DSJ',([('1','VINA','power_in'),('10','VIN','power_in'),('11','VIN','passive'),('12','EN','input'),('13','PS/SYNC','input'),('8','L1','passive'),('9','L1','passive')],[('4','VOUT','power_out'),('5','VOUT','passive'),('3','FB','input'),('14','PG','open_collector'),('6','L2','passive'),('7','L2','passive'),('2','GND','power_in'),('15','PGND_EP','passive')]),'Package_DFN_QFN:DFN-14-1EP_3x4mm_P0.5mm_EP1.7x3.3mm')
add('U2',reg,'TPS63021DSJR',{1:'VBAT',10:'VBAT',11:'VBAT',12:'VBAT',13:'GND',8:'SW1',9:'SW1',4:'3V3',5:'3V3',3:'3V3',6:'SW2',7:'SW2',2:'GND',15:'GND'},2,115,85,112,135,note='Fixed3.3V; power-save mode; 1A electronics design target at VBAT>=3.0V subject to bench testing')
add('L1',L,'1.5uH XFL4020-152MEC',{1:'SW1',2:'SW2'},2,205,85,112,139,fp='Drone:XFL4020',note='Coilcraft reference inductor; confirm exact suffix and DCR at sourcing')
c('C5','10uF','VBAT',2,65,155,115.5,135,90,fp='Capacitor_SMD:C_0603_1608Metric')
c('C6','10uF','VBAT',2,115,155,115.5,137,90,fp='Capacitor_SMD:C_0603_1608Metric')
c('C7','100nF','VBAT',2,165,155,109,132,90)
for i,(x,px,py) in enumerate([(215,108,135),(265,108,137),(315,108,139)],8):
    c('C'+str(i),'22uF','3V3',2,x,155,px,py,90,fp='Capacitor_SMD:C_0805_2012Metric',note='X5R 10V; verify effective capacitance under DC bias')
add('J2',CON2,'1S LiPo 700mAh 20C',{1:'VBAT',2:'GND'},2,55,85,125,147,fp='Drone:Battery_2',note='Direct solder pads; no charger or reverse-polarity protection; disconnect battery when unused')
add('C11',CP,'220uF 10V',{1:'VBAT',2:'GND'},2,315,85,119,141,fp='Capacitor_SMD:CP_Elec_6.3x5.8',note='Low ESR aluminum/polymer; ripple-current rating >=1A; final exact part depends on sourcing')

# MPU6050 operating circuit. Reserved pins and auxiliary bus left unconnected.
imu=sym('Sensor_Motion','MPU-6050')
add('U3',imu,'MPU-6050',{1:'GND',8:'IMU_3V3',9:'GND',10:'IMU_REGOUT',11:'GND',12:'IMU_INT',13:'IMU_3V3',18:'GND',20:'IMU_CPOUT',23:'IMU_SCL',24:'IMU_SDA'},3,100,80,125,127,note='I2C address0x68; use genuine bare chip, orientation must be calibrated in firmware')
r('R5','10R','3V3','IMU_3V3',3,195,55,122,123,90)
c('C12','1uF','IMU_3V3',3,245,55,124,123,90)
c('C13','100nF','IMU_3V3',3,195,105,128,125,0)
c('C14','10nF','IMU_3V3',3,245,105,122,126,0)
c('C15','100nF','IMU_REGOUT',3,195,155,122,128,0)
c('C16','2.2nF 50V','IMU_CPOUT',3,245,155,126,130,90,note='X7R 50V +/-10%; charge pump capacitor')
r('R6','4.7k','3V3','IMU_SDA',3,195,205,123,131,90)
r('R7','4.7k','3V3','IMU_SCL',3,245,205,121,131,90)

# OV2640 camera flex matching the AI-Thinker v1.6 reference pinout.
camdefs=[('1','Y0_UNUSED','passive'),('2','Y1_UNUSED','passive'),('3','Y4_D2','passive'),('4','Y3_D1','passive'),('5','Y5_D3','passive'),('6','Y2_D0','passive'),('7','Y6_D4','passive'),('8','PCLK','passive'),('9','Y7_D5','passive'),('10','DGND','passive'),('11','Y8_D6','passive'),('12','XCLK','passive'),('13','Y9_D7','passive'),('14','DOVDD','passive'),('15','DVDD','passive'),('16','HREF','passive'),('17','PWDN','passive'),('18','VSYNC','passive'),('19','RESET_N','passive'),('20','SIOC','passive'),('21','AVDD','passive'),('22','SIOD','passive'),('23','AGND','passive'),('24','NC','passive')]
cam=custom('OV2640_FLEX_24',(camdefs[:12],camdefs[12:]),'Connector_FFC-FPC:Hirose_FH12-24S-0.5SH_1x24-1MP_P0.50mm_Horizontal')
add('J3',cam,'OV2640 flex / FH12-24S-0.5SH(55)',{3:'CAM_D2',4:'CAM_D1',5:'CAM_D3',6:'CAM_D0',7:'CAM_D4',8:'CAM_PCLK',9:'CAM_D5',10:'GND',11:'CAM_D6',12:'CAM_XCLK',13:'CAM_D7',14:'3V3',15:'CAM_1V2',16:'CAM_HREF',17:'CAM_PWDN',18:'CAM_VSYNC',19:'CAM_RESET',20:'CAM_SCL',21:'CAM_2V8',22:'CAM_SDA',23:'GND'},4,90,75,125,136,180,note='ONLY pin-compatible 24pin0.5mm OV2640 flex; bottom-contact connector, confirm flex contact side/length before purchase')
ldo=sym('Regulator_Linear','TLV70012_SOT23-5')
add('U4',ldo,'TLV70028DDCR',{1:'3V3',2:'GND',3:'3V3',5:'CAM_2V8'},4,190,65,134,135,note='2.8V analog camera rail,200mA')
add('U5',ldo,'TLV70012DDCR',{1:'3V3',2:'GND',3:'3V3',5:'CAM_1V2'},4,295,65,139,135,note='1.2V core camera rail,200mA')
c('C17','1uF','3V3',4,160,130,135,132,90)
c('C18','1uF','CAM_2V8',4,210,130,134,138,90)
c('C19','1uF','3V3',4,260,130,140,132,90)
c('C20','1uF','CAM_1V2',4,310,130,139,138,90)
c('C21','100nF','3V3',4,65,200,125.5,140,90)
c('C22','100nF','CAM_2V8',4,115,200,130,140,90)
c('C23','100nF','CAM_1V2',4,165,200,128,140,90)
r('R8','4.7k','3V3','CAM_SDA',4,215,200,131,132,90)
r('R9','4.7k','3V3','CAM_SCL',4,265,200,133,130,90)
r('R10','10k','3V3','CAM_RESET',4,315,200,135,130,90)
c('C24','100nF','CAM_RESET',4,65,250,137,130,90)
r('R11','10k','CAM_PWDN','GND',4,150,250,129,132,90)
r('R12','33R','CAM_XCLK_SRC','CAM_XCLK',4,240,250,115,114,90,note='Source series damping; tune with scope')

# Four low-side brushed motor drivers. Diode cathode to VBAT, anode to drain.
for i,(px,py) in enumerate([(106,113),(144,113),(106,143),(144,143)],1):
    sx=65+(i-1)*95
    add('Q'+str(i),Q,'AO3400A',{1:f'GATE{i}',2:'GND',3:f'MOTOR{i}_NEG'},5,sx,100,px,py,note='SOT23 G1/S2/D3; verify stall current and heating with actual prop')
    r('R'+str(12+i),'100R',f'PWM{i}',f'GATE{i}',5,sx,150,px-2,py-3,90)
    r('R'+str(16+i),'10k',f'GATE{i}','GND',5,sx,200,px,py-3,90)
    add('D'+str(i),D,'SS34',{1:'VBAT',2:f'MOTOR{i}_NEG'},5,sx,50,px,py+3,fp='Diode_SMD:D_SMA',note='3A40V Schottky flyback; cathode pad1 to VBAT')
    add('J'+str(3+i),CON2,'8520 motor '+str(i),{1:'VBAT',2:f'MOTOR{i}_NEG'},5,sx,250,102 if px<125 else 148,py,90,fp='Drone:Motor_2',note='Direct motor wire solder pads; motor body not on PCB')
    c('C'+str(24+i),'10uF','VBAT',6,sx,60,px+2.5,py-3,90,fp='Capacitor_SMD:C_0603_1608Metric')
    p=add('C'+str(100+i),C,'100nF 16V motor-mounted',{1:'VBAT',2:f'MOTOR{i}_NEG'},6,sx,120,0,0,fp='',note='Solder directly across motor terminals; included in BOM, off-board',onboard=False)

# Local, portable pad footprints.
pretty=OUT/'Drone.pretty'; pretty.mkdir(exist_ok=True)
def padfp(name,pads,body=None):
    lines=[f'(footprint "{name}" (version 20241229) (generator "pcbnew") (layer "F.Cu") (attr smd)',f'(fp_text reference "REF**" (at 0 -3) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.12))))',f'(fp_text value "{name}" (at 0 3) (layer "F.Fab") (effects (font (size 0.8 0.8) (thickness 0.12))))']
    for num,x,y,w,h in pads: lines.append(f'(pad "{num}" smd roundrect (at {x} {y}) (size {w} {h}) (layers "F.Cu" "F.Mask") (roundrect_rratio 0.2))')
    if body:
        x,y=body
        lines += [f'(fp_rect (start {-x/2} {-y/2}) (end {x/2} {y/2}) (stroke (width 0.1) (type default)) (fill none) (layer "F.Fab"))',f'(fp_rect (start {-x/2-.25} {-y/2-.25}) (end {x/2+.25} {y/2+.25}) (stroke (width 0.05) (type default)) (fill none) (layer "F.CrtYd"))']
    lines.append(')'); (pretty/(name+'.kicad_mod')).write_text('\n'.join(lines))
padfp('Motor_2',[(1,-1.5,0,2,2),(2,1.5,0,2,2)],(5.5,2.5))
padfp('Battery_2',[(1,-2.5,0,3.5,3),(2,2.5,0,3.5,3)],(9,3.5))
padfp('Programming_6',[(i+1,0,(i-2.5)*1.5,1.1,1.1) for i in range(6)],(1.6,9.1))
padfp('XFL4020',[(1,-1.675,0,.98,3.4),(2,1.675,0,.98,3.4)],(4,4))
# The inductor needs paste, unlike wire pads.
f=pretty/'XFL4020.kicad_mod'; f.write_text(f.read_text().replace('"F.Cu" "F.Mask"','"F.Cu" "F.Paste" "F.Mask"'))

# Schematics: root index plus six named sheets; all connections use global net labels.
rootid=stable('root'); sheetids={i:stable('sheet'+str(i)) for i in range(1,7)}
titles={1:'Controller and programming',2:'Battery and 3.3V buck-boost',3:'MPU-6050 inertial sensor',4:'OV2640 camera interface',5:'Four brushed motor drivers',6:'Motor decoupling and assembly notes'}
def esc(s): return json.dumps(str(s))
def text(s,x,y,size=1.5): return f'(text {esc(s)} (at {x} {y} 0) (effects (font (size {size} {size})) (justify left)) (uuid {uid()}))'
def label(s,x,y,ang=0): return f'(global_label {esc(s)} (shape bidirectional) (at {x} {y} {ang}) (effects (font (size 0.9 0.9)) (justify {"right" if ang==0 else "left"})) (uuid {uid()}) (property "Intersheetrefs" "${{INTERSHEET_REFS}}" (at {x} {y} 0) (effects (font (size 1 1)) hide)))'
def schematic(page):
    pp=[p for p in parts if p['page']==page]; ids={p['lib'] for p in pp}|{FLAG}
    out=[f'(kicad_sch (version 20250114) (generator "eeschema") (uuid {sheetids[page]}) (paper "A3") (title_block (title {esc(titles[page])}) (date "2026-09-07") (rev "A0 DRAFT") (company "DronePCB") (comment 1 "Not released for fabrication; see design review and validation reports"))', '(lib_symbols '+' '.join(dump(symbols[k]) for k in sorted(ids))+')',text(titles[page],25,20,2.5)]
    for p in pp:
        s=symbols[p['lib']]; x,y=[round(v/1.27)*1.27 for v in p['sch']]; ats=[]
        for pin in pins(s):
            at=child(pin,'at'); ats.append((float(at[1]),float(at[2])))
        top=y-max(a[1] for a in ats)-12.7
        props=f'(property "Reference" "{p["ref"]}" (at {x} {top} 0) (effects (font (size 1.27 1.27)))) (property "Value" {esc(p["value"])} (at {x} {top+2.5} 0) (effects (font (size 1.1 1.1)))) (property "Footprint" {esc(p["fp"])} (at {x} {y} 0) (effects (font (size 1 1)) hide))'
        pinids=' '.join(f'(pin {esc(child(pi,"number")[1])} (uuid {uid()}))' for pi in pins(s))
        out.append(f'(symbol (lib_id {esc(p["lib"])}) (at {x} {y} 0) (unit 1) (in_bom yes) (on_board {"yes" if p["onboard"] else "no"}) (dnp no) (uuid {p["uuid"]}) {props} {pinids} (instances (project "DroneFC" (path "/{rootid}/{sheetids[page]}" (reference "{p["ref"]}") (unit 1)))))')
        seen=set()
        for pin in pins(s):
            num=child(pin,'number')[1]; at=child(pin,'at'); dx,dy,angle=map(float,at[1:]); xx,yy=x+dx,y-dy
            if (xx,yy) in seen: continue
            seen.add((xx,yy)); net=p['nets'].get(num)
            if net:
                # Vertical pins have short jogs to avoid overlapping supply labels.
                vx=-math.cos(math.radians(angle)); vy=math.sin(math.radians(angle))
                ex=round(xx+vx*5.08,4); ey=round(yy+vy*5.08,4)
                out.append(f'(wire (pts (xy {xx} {yy}) (xy {ex} {ey})) (stroke (width 0) (type default)) (uuid {uid()}))')
                out.append(label(net,ex,ey,(0 if dx<0 else 180) if abs(vx)<.1 else (0 if vx<0 else 180)))
            else: out.append(f'(no_connect (at {xx} {yy}) (uuid {uid()}))')
    flag_nets={2:['VBAT','GND'],3:['IMU_3V3']}.get(page,[])
    for j,net in enumerate(flag_nets):
        xx=round((50+j*60)/1.27)*1.27; yy=round(235/1.27)*1.27; ref='#FLG'+str(page)+str(j)
        out.append(f'(symbol (lib_id "power:PWR_FLAG") (at {xx} {yy} 0) (unit 1) (in_bom no) (on_board yes) (dnp no) (uuid {uid()}) (property "Reference" "{ref}" (at {xx} {yy-4} 0) (effects (font (size 1 1)) hide)) (property "Value" "PWR_FLAG" (at {xx} {yy-3} 0) (effects (font (size 1 1)))) (instances (project "DroneFC" (path "/{rootid}/{sheetids[page]}" (reference "{ref}") (unit 1)))))')
        out.append(label(net,xx,yy))
    if page==6:
        out += [text('C101-C104 are installed at the motor terminals, not on this PCB.',35,175),text('1S LiPo only: 4.2V maximum. Do not connect a 2S battery.',35,185),text('No on-board charging. External charger required. Disconnect battery after use.',35,195),text('Firmware must keep motors disabled at boot and on link loss / watchdog timeout.',35,205),text('Verify motor startup/stall current, regulator transients and actual camera flex before fabrication.',35,215)]
    out.append(')'); (OUT/f'sheet{page}.kicad_sch').write_text('\n'.join(out),encoding='utf-8')
for page in titles: schematic(page)
out=[f'(kicad_sch (version 20250114) (generator "eeschema") (uuid {rootid}) (paper "A4") (title_block (title "DroneFC - 1S brushed quadcopter") (rev "A0 DRAFT")) (lib_symbols)',text('DroneFC / ESP32-S3 + OV2640 + MPU-6050',25,25,2.5),text('Editable prototype design - not a fabrication release',25,35,1.5)]
for i in titles:
    x=30+((i-1)%2)*125; y=55+((i-1)//2)*40
    out.append(f'(sheet (at {x} {y}) (size 100 25) (stroke (width 0.15) (type default)) (fill (color 0 0 0 0)) (uuid {sheetids[i]}) (property "Sheetname" {esc(titles[i])} (at {x} {y-1} 0) (effects (font (size 1.1 1.1)) (justify left bottom))) (property "Sheetfile" "sheet{i}.kicad_sch" (at {x} {y+26} 0) (effects (font (size 1 1)) (justify left top))) (instances (project "DroneFC" (path "/{rootid}" (page "{i+1}")))))')
out.append(f'(sheet_instances (path "/" (page "1"))) )'); (OUT/'DroneFC.kicad_sch').write_text('\n'.join(out))

# Copy every used footprint to a project-local library for portability.
tables=['(fp_lib_table (version 7) (lib (name "Drone") (type "KiCad") (uri "${KIPRJMOD}/Drone.pretty") (options "") (descr "Project-local custom footprints"))']
for library in sorted({p['fp'].split(':')[0] for p in parts if p['fp'] and not p['fp'].startswith('Drone:')}):
    folder=OUT/(library+'.pretty'); folder.mkdir(exist_ok=True)
    for p in parts:
        if p['fp'].startswith(library+':'):
            name=p['fp'].split(':')[1]+'.kicad_mod'; shutil.copyfile(LIB/'footprints'/(library+'.pretty')/name,folder/name)
    tables.append(f'(lib (name "{library}") (type "KiCad") (uri "${{KIPRJMOD}}/{library}.pretty") (options "") (descr "Copied from KiCad10 library"))')
(OUT/'fp-lib-table').write_text('\n'.join(tables)+')')
# Save custom symbols as well as cached schematic copies.
(OUT/'Drone.kicad_sym').write_text('(kicad_symbol_lib (version 20250114) (generator "kicad_symbol_editor") '+ ' '.join(dump([s[0],s[1].split(':')[1],*s[2:]]) for k,s in symbols.items() if k.startswith('Drone:'))+')')
stab=['(sym_lib_table (version 7)']
for lib in sorted({k.split(':')[0] for k in symbols}):
    (OUT/(lib+'.kicad_sym')).write_text('(kicad_symbol_lib (version 20250114) (generator "kicad_symbol_editor") '+ ' '.join(dump([s[0],s[1].split(':')[1],*s[2:]]) for k,s in symbols.items() if k.startswith(lib+':'))+')')
    stab.append(f'(lib (name "{lib}") (type "KiCad") (uri "${{KIPRJMOD}}/{lib}.kicad_sym") (options "") (descr "Project-local symbols"))')
(OUT/'sym-lib-table').write_text('\n'.join(stab)+')')
(ROOT/'design_manifest.json').write_text(json.dumps(parts,indent=2))
with (ROOT/'BOM.csv').open('w',newline='') as f:
    w=csv.writer(f); w.writerow(['Reference','Value_or_MPN','Footprint','On_PCB','Notes'])
    for p in parts: w.writerow([p['ref'],p['value'],p['fp'],p['onboard'],p['note']])
project={'meta':{'filename':'DroneFC.kicad_pro','version':1},'board':{'design_settings':{'rules':{'min_clearance':0.127,'min_track_width':0.15,'min_via_diameter':0.45,'min_through_hole_diameter':0.2,'min_copper_edge_clearance':0.25},'defaults':{'zones':{'min_clearance':0.2}}}},'net_settings':{'classes':[{'name':'Default','clearance':0.127,'track_width':0.2,'via_diameter':0.5,'via_drill':0.25,'microvia_diameter':0.3,'microvia_drill':0.1,'diff_pair_width':0.2,'diff_pair_gap':0.2,'diff_pair_via_gap':0.25,'wire_width':6,'bus_width':12,'schematic_color':'rgba(0, 0, 0, 0.000)','pcb_color':'rgba(0, 0, 0, 0.000)'}]}}
(OUT/'DroneFC.kicad_pro').write_text(json.dumps(project,indent=2))
print(f'Created {len(parts)} component entries and seven schematic pages')

if '--pcb' in sys.argv:
    import pcbnew as p
    b=p.BOARD(); b.SetCopperLayerCount(4); b.GetDesignSettings().SetBoardThickness(p.FromMM(.8))
    nets={n for a in parts for n in a['nets'].values()}; netobj={}
    for n in sorted(nets):
        netobj[n]=p.NETINFO_ITEM(b,n); b.Add(netobj[n])
    for a in parts:
        if not a['onboard']: continue
        lib,name=a['fp'].split(':'); fp=p.FootprintLoad(str(OUT/(lib+'.pretty')),name)
        fp.SetReference(a['ref']); fp.SetValue(a['value']); fp.SetFPID(p.LIB_ID(lib,name))
        path=p.KIID_PATH(); path.push_back(p.KIID(rootid)); path.push_back(p.KIID(sheetids[a['page']])); path.push_back(p.KIID(a['uuid'])); fp.SetPath(path)
        for pad in fp.Pads():
            if pad.GetNumber() in a['nets']: pad.SetNet(netobj[a['nets'][pad.GetNumber()]])
        fp.SetPosition(p.VECTOR2I(p.FromMM(a['pcb'][0]),p.FromMM(a['pcb'][1]))); fp.SetOrientationDegrees(a['pcb'][2]); fp.Reference().SetTextSize(p.VECTOR2I(p.FromMM(.65),p.FromMM(.65))); fp.Reference().SetTextThickness(p.FromMM(.1)); fp.Value().SetVisible(False)
        b.Add(fp)
    for a,z in [((100,100),(150,100)),((150,100),(150,150)),((150,150),(100,150)),((100,150),(100,100))]:
        line=p.PCB_SHAPE(); line.SetShape(p.SHAPE_T_SEGMENT); line.SetStart(p.VECTOR2I(p.FromMM(a[0]),p.FromMM(a[1]))); line.SetEnd(p.VECTOR2I(p.FromMM(z[0]),p.FromMM(z[1]))); line.SetLayer(p.Edge_Cuts); line.SetWidth(p.FromMM(.05)); b.Add(line)
    for x,y in [(103,103),(147,103),(103,147),(147,147)]:
        hole=p.FootprintLoad(str(LIB/'footprints'/'MountingHole.pretty'),'MountingHole_2.2mm_M2'); hole.SetReference('H'+str(x)+str(y)); hole.SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(y))); hole.Value().SetVisible(False); hole.Reference().SetVisible(False); b.Add(hole)
    t=p.PCB_TEXT(b); t.SetText('DroneFC A0\nENGINEERING PROTOTYPE'); t.SetPosition(p.VECTOR2I(p.FromMM(125),p.FromMM(122))); t.SetTextSize(p.VECTOR2I(p.FromMM(.65),p.FromMM(.65))); t.SetTextThickness(p.FromMM(.1)); t.SetLayer(p.F_SilkS); b.Add(t)
    p.SaveBoard(str(OUT/'DroneFC.kicad_pcb'),b); print('PCB created')


