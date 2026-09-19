from pathlib import Path
import pcbnew as p
R=Path(__file__).resolve().parents[1]
old='Package_DFN_QFN:DFN-14-1EP_3x4mm_P0.5mm_EP1.7x3.3mm'
new='Drone:TI_DSJ14_TPS63021'
src=R/'design/Package_DFN_QFN.pretty/DFN-14-1EP_3x4mm_P0.5mm_EP1.7x3.3mm.kicad_mod'
f=p.FootprintLoad(str(src.parent),src.stem)
def correct(f):
    f.SetFPID(p.LIB_ID('Drone','TI_DSJ14_TPS63021'))
    for pad in f.Pads():
        if pad.GetNumber()=='15': pad.SetSize(p.VECTOR2I(p.FromMM(1.58),p.FromMM(2.85)))
        elif pad.GetNumber()=='':
            local=pad.GetPosition()-f.GetPosition()
            pad.SetPosition(f.GetPosition()+p.VECTOR2I(round(local.x*1.58/1.7),round(local.y*2.85/3.3)))
            pad.SetSize(p.VECTOR2I(p.FromMM(.635),p.FromMM(.575)))
    f.SetLibDescription('TI DSJ14 TPS63021; 1.58x2.85mm exposed pad per TI 4208549-3/E. Peripheral lands 0.70x0.25mm on 0.5mm pitch, 2.90mm row spacing; enlarged relative to TI nominal example. Segmented paste about 65 percent coverage; assembler to qualify stencil.')
correct(f)
p.FootprintSave(str(R/'design/Drone.pretty'),f)
b=p.LoadBoard(str(R/'design/DroneFC.kicad_pcb'))
u=next(f for f in b.GetFootprints() if f.GetReference()=='U2')
correct(u)
p.ZONE_FILLER(b).Fill(b.Zones())
p.SaveBoard(str(R/'design/DroneFC.kicad_pcb'),b)
for path in list((R/'design').glob('*.kicad_sch'))+[R/'design_manifest.json',R/'BOM.csv']:
    t=path.read_text(encoding='utf-8');path.write_text(t.replace(old,new),encoding='utf-8')
print('Corrected U2 exposed copper and segmented paste; retained compatible enlarged peripheral lands.')
