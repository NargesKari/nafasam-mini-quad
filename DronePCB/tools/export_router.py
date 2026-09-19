import pcbnew as p, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
b=p.LoadBoard(str(ROOT/'design/DroneFC.kicad_pcb'))
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
s=s.replace('(clearance 200)','(clearance 150)').replace('(width 200)','(width 150)')
s=s.replace('(use_via "Via[0-3]_600:300_um")','(use_via "Via[0-3]_450:200_um")').replace('(use_via "Via[0-3]_500:250_um")','(use_via "Via[0-3]_450:200_um")')
f.write_text(s)
