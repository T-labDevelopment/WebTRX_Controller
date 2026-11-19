from pathlib import Path
import re, json, uuid, csv, zipfile, hashlib, math
from collections import Counter, defaultdict

BASE=Path(__file__).resolve().parent.parent if Path(__file__).resolve().parent.name=='tools' else Path('/mnt/data/WebTRX_Controller_RevA_Custom_2026-11-19')
BASE.mkdir(exist_ok=True)
LIB=BASE/'WebTRX_Custom.pretty'; LIB.mkdir(exist_ok=True)
PROJECT='WebTRX_Controller'
SRC=Path(BASE/'WebTRX_Controller.kicad_sch').read_text(encoding='utf-8')

# General S-expression helpers

def findblock(s, start):
    dep=0; quote=False; esc=False
    for i in range(start,len(s)):
        ch=s[i]
        if quote:
            if esc: esc=False
            elif ch=='\\': esc=True
            elif ch=='"': quote=False
        elif ch=='"': quote=True
        elif ch=='(': dep+=1
        elif ch==')':
            dep-=1
            if dep==0:return s[start:i+1]
    raise ValueError('unterminated s-expression')

def block_named(s, prefix):
    pos=s.index(prefix)
    return findblock(s,pos)

UID_COUNTER=0
def _id():
    global UID_COUNTER
    UID_COUNTER+=1
    return str(uuid.uuid5(uuid.NAMESPACE_URL,f'WebTRX_Controller/RevA2/2026-11-19/{UID_COUNTER:05d}'))
def q(s):return json.dumps(str(s),ensure_ascii=False)
def f(v):return f'{v:.4f}'.rstrip('0').rstrip('.') if isinstance(v,float) else str(v)
def eff(sz=1.27,hide=False,justify=''):
    return f'(effects (font (size {f(sz)} {f(sz)}))'+(f' (justify {justify})' if justify else '')+(' (hide yes)' if hide else '')+')'

def sympin(name,num,x,y,angle=0,elect='bidirectional'):
    return f'(pin {elect} line (at {f(x)} {f(y)} {angle}) (length 5.08) (name {q(name)} {eff(1.27)}) (number {q(num)} {eff(1.27)}))'

def make_module_symbol(symname):
    pins={1:'P3.2',2:'P1.4',3:'P1.5',4:'P1.6',5:'P1.7',6:'RST',7:'P1.0',8:'P1.1',9:'P3.1',10:'P3.0',
          11:'P3.3',12:'P3.4',13:'P3.5',14:'P3.6_USB_DP',15:'P3.7_USB_DM',16:'P1.3',17:'P1.2',18:'GND',19:'5V_VBUS',20:'3V3'}
    sub=[]
    for n in range(1,11):
        y=22.86-(n-1)*2.54
        sub.append(sympin(pins[n],n,-20.32,y,0,'passive' if n==6 else 'bidirectional'))
    for n in range(20,10,-1):
        y=22.86-(20-n)*2.54
        sub.append(sympin(pins[n],n,20.32,y,180,'passive' if n in (18,19,20) else 'bidirectional'))
    properties=[
        ('Reference','A','0 29.21 0',False),
        ('Value','WeAct_CH552_Core_Board_V1_0','0 26.67 0',False),
        ('Footprint','WebTRX_Custom:WeAct_CH552_Core_Board_V1_0','0 0 0',True),
        ('Datasheet','https://github.com/WeActStudio/WeActStudio.CH552CoreBoard','0 0 0',True),
        ('Description','WeAct CH552T development module 2x10 DIP, USB on module, no external USB/PSU','0 0 0',True)
    ]
    props='\n'.join(f'    (property {q(k)} {q(v)} (at {xyz}) {eff(hide=hid)})' for k,v,xyz,hid in properties)
    return f'''(symbol {q(symname)}
    (pin_names (offset 1.016))
    (exclude_from_sim no) (in_bom yes) (on_board yes) (in_pos_files yes)
    {props}
    (symbol {q(symname+'_0_1')} (rectangle (start -15.24 25.4) (end 15.24 -2.54) (stroke (width 0.254) (type default)) (fill (type background))))
    (symbol {q(symname+'_1_1')}\n      {'\n      '.join(sub)}\n    )
  )'''

def make_encoder_symbol(symname):
    prop='\n'.join(f'    (property {q(k)} {q(v)} (at {xyz}) {eff(hide=hid)})' for k,v,xyz,hid in [
        ('Reference','SW','0 8.89 0',False),('Value','EC12E2420801','0 -8.89 0',False),
        ('Footprint','WebTRX_Custom:EC12E2420801','0 0 0',True),
        ('Datasheet','https://tech.alpsalpine.com/e/products/detail/EC12E2420801/','0 0 0',True),
        ('Description','EC12E2420801 24-detent incremental A/B with 2 mechanical mounting tabs','0 0 0',True)])
    return f'''(symbol {q(symname)}
    (pin_names (offset 1.016))
    (exclude_from_sim no) (in_bom yes) (on_board yes) (in_pos_files yes)
{prop}
    (symbol {q(symname+'_0_1')}
      (rectangle (start -5.08 5.08) (end 5.08 -5.08) (stroke (width 0.254) (type default)) (fill (type background)))
      (circle (center 0 0) (radius 2.54) (stroke (width 0.254) (type default)) (fill (type none)))
      (polyline (pts (xy -1.27 1.27) (xy 1.27 -1.27)) (stroke (width 0.254) (type default)) (fill (type none)))
    )
    (symbol {q(symname+'_1_1')}
       {sympin('A','A',-10.16,2.54,0,'passive')}
       {sympin('C','C',-10.16,0,0,'passive')}
       {sympin('B','B',-10.16,-2.54,0,'passive')}
       {sympin('Mount_1','M1',10.16,2.54,180,'passive')}
       {sympin('Mount_2','M2',10.16,-2.54,180,'passive')}
    )
  )'''

MOD_NAME='WeAct_CH552_Core_Board_V1_0'
ENC_NAME='EC12E2420801'
moddef=make_module_symbol(MOD_NAME)
encdef=make_encoder_symbol(ENC_NAME)
(BASE/'WebTRX_Custom.kicad_sym').write_text('(kicad_symbol_lib\n  (version 20251024)\n  (generator "kicad_symbol_editor")\n  (generator_version "10.0")\n'+moddef+'\n'+encdef+'\n)\n',encoding='utf-8')

(BASE/'sym-lib-table').write_text('(sym_lib_table\n  (lib (name "WebTRX_Custom")(type "KiCad")(uri "${KIPRJMOD}/WebTRX_Custom.kicad_sym")(options "")(descr "WeAct CH552 module and ALPS EC12E2420801"))\n)\n',encoding='utf-8')
(BASE/'fp-lib-table').write_text('(fp_lib_table\n  (lib (name "WebTRX_Custom")(type "KiCad")(uri "${KIPRJMOD}/WebTRX_Custom.pretty")(options "")(descr "Project specific WeAct module and EC12E2420801 footprints"))\n)\n',encoding='utf-8')

# Custom footprints. WeAct 2x10 plated positions validated against rgoulter/keyboard-labs open-source actual board.
# EC12 mounting pattern is made from ALPS ALPINE product-catalog-ec-all.en.pdf D-13 (drawing no 1).

def fp_txt(s,x,y,size=1.0,layer='F.SilkS'):
    return f'(fp_text user {q(s)} (at {f(x)} {f(y)}) (layer {q(layer)}) (effects (font (size {f(size)} {f(size)}) (thickness 0.15))))'

def fp_line(x1,y1,x2,y2,layer='F.SilkS',w=0.12):
    return f'(fp_line (start {f(x1)} {f(y1)}) (end {f(x2)} {f(y2)}) (stroke (width {f(w)}) (type default)) (layer {q(layer)}))'

def fp_rect(x1,y1,x2,y2,layer='F.Fab',w=.10):
    return f'(fp_rect (start {f(x1)} {f(y1)}) (end {f(x2)} {f(y2)}) (stroke (width {f(w)}) (type default)) (fill none) (layer {q(layer)}))'

def footprint_module():
    lines=['(footprint "WeAct_CH552_Core_Board_V1_0" (version 20241229) (generator "pcbnew") (layer "F.Cu")',
           '(descr "WeAct CH552 Core Board V1.0, 2x10 THT, 2.54 pitch, 15.24 row distance, USB at pin 1/20 end")',
           '(tags "WeAct CH552 Core 20 pin 2x10 USB")',
           '(attr through_hole)',
           '(property "Reference" "REF**" (at 7.62 -6.7 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))',
           '(property "Value" "WeAct_CH552_Core_Board_V1_0" (at 7.62 27.0 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))',
           fp_rect(-.7,-1.5,15.94,24.36,'F.Fab'),
           fp_rect(-1.75,-7.3,16.99,25.42,'F.CrtYd',.05),
           fp_line(-.9,-1.7,-.9,24.5),fp_line(16.1,-1.7,16.1,24.5),
           fp_line(-.9,24.5,16.1,24.5),
           fp_line(-.9,-1.7,5.2,-1.7),fp_line(10.0,-1.7,16.1,-1.7),
           fp_txt('USB',7.6,-3.5,1.0),fp_txt('USB ->',7.6,-1.5,0.65,'F.Fab'),
           fp_txt('PIN1',-3.0,0,0.8,'F.Fab'),
           ]
    pins=['P3.2','P1.4','P1.5','P1.6','P1.7','RST','P1.0','P1.1','P3.1','P3.0','P3.3','P3.4','P3.5','P3.6','P3.7','P1.3','P1.2','GND','5V','3V3']
    for n in range(1,21):
        x,y=(0,(n-1)*2.54) if n<=10 else (15.24,(20-n)*2.54)
        lines.append(f'(pad {q(n)} thru_hole {"rect" if n==1 else "oval"} (at {f(x)} {f(y)}) (size 1.72 1.72) (drill 0.9) (layers "*.Cu" "*.Mask"))')
        # additional small FAB-only pin identity; no silk overlap on fine-pitch pins
        if n in (1,2,3,4,5,18,19,20):
            xx=x+2.5 if n<=10 else x-2.5
            lines.append(fp_txt(f'{n}:{pins[n-1]}',xx,y,0.55,'F.Fab'))
    lines.append(')')
    return '\n'.join(lines)+'\n'

def footprint_encoder():
    lines=['(footprint "EC12E2420801" (version 20241229) (generator "pcbnew") (layer "F.Cu")',
           '(descr "ALPS Alpine EC12E2420801: A-C-B at 2.5 mm, 7.5 mm to mounting tabs, 13.2 mm support span")',
           '(tags "EC12E2420801 ALPS 24 detent")',
           '(attr through_hole)',
           '(property "Reference" "REF**" (at 0 -11.5) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))',
           '(property "Value" "EC12E2420801" (at 0 5.5) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))',
           fp_rect(-6.2,-10.75,6.2,2.45,'F.Fab'),
           fp_rect(-8.3,-11.0,8.3,3.1,'F.CrtYd',.05),
           fp_line(-6.4,-10.8,6.4,-10.8),fp_line(-6.4,2.6,6.4,2.6),
           fp_line(-6.4,-10.8,-6.4,-6.0),fp_line(6.4,-10.8,6.4,-6.0),
           fp_txt('A    C    B',0,3.85,0.8,'F.Fab'),
           '(pad "A" thru_hole circle (at -2.5 0) (size 1.8 1.8) (drill 1.05) (layers "*.Cu" "*.Mask"))',
           '(pad "C" thru_hole circle (at 0 0) (size 1.8 1.8) (drill 1.05) (layers "*.Cu" "*.Mask"))',
           '(pad "B" thru_hole circle (at 2.5 0) (size 1.8 1.8) (drill 1.05) (layers "*.Cu" "*.Mask"))',
           '(pad "M1" thru_hole oval (at -6.6 -7.5) (size 3.3 3.6) (drill oval 2.0 2.1) (layers "*.Cu" "*.Mask"))',
           '(pad "M2" thru_hole oval (at 6.6 -7.5) (size 3.3 3.6) (drill oval 2.0 2.1) (layers "*.Cu" "*.Mask"))',
           ')']
    return '\n'.join(lines)+'\n'

module_mod=footprint_module();encoder_mod=footprint_encoder()
(LIB/(MOD_NAME+'.kicad_mod')).write_text(module_mod,encoding='utf8')
(LIB/(ENC_NAME+'.kicad_mod')).write_text(encoder_mod,encoding='utf8')

# Extract stock Switch:SW_Push definition from previously incorporated full standard library (do not rebuild abbreviated cache).
stock=block_named(SRC,'(symbol "Switch:SW_Push"')
baseUuid='ecce73c4-fb92-423b-88c2-ec12e2420801'
# Symbol source root id user-defined and fixed for this revision.

INSTANCE_UUIDS={}
def item_symbol(defn,ref,value,origin,fp,instance_pins,projectPath,opts={}):
    x,y=origin; lib_id=defn;u=_id();INSTANCE_UUIDS[ref]=u
    p=[]
    for key,val,offset,hide in [('Reference',ref,(-12.7,-8.89),False),('Value',value,(-12.7,-6.35),False),('Footprint',fp,(0,0),True),('Datasheet',opts.get('datasheet',''),(0,0),True)]:
        ox,oy=offset;p.append(f'(property {q(key)} {q(val)} (at {f(x+ox)} {f(y+oy)} 0) {eff(1.0,hide)})')
    pinmap=' '.join(f'(pin {q(n)} (uuid {q(_id())}))' for n in instance_pins)
    return f'''(symbol (lib_id {q(lib_id)}) (at {f(x)} {f(y)} 0) (unit 1) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no)
 (uuid {q(u)}) {' '.join(p)} {pinmap}
 (instances (project {q(PROJECT)} (path "/{baseUuid}" (reference {q(ref)}) (unit 1))))
)''',u

schlist=[]; connections=[]; pinwires=[];nocon=[]

def label_wire(ref,pin,net,start,end,rot=0):
    assert start[0] != end[0] or start[1] != end[1]
    schlist.append(f'(wire (pts (xy {f(start[0])} {f(start[1])}) (xy {f(end[0])} {f(end[1])})) (stroke (width 0) (type default)) (uuid {q(_id())}))')
    # label at the exact end, IEC global label passive and rotation 0 for signal-left and 180 for right-ground.
    schlist.append(f'(global_label {q(net)} (shape passive) (at {f(end[0])} {f(end[1])} {rot}) {eff(1.27,False,"right" if rot==180 else "left")} (uuid {q(_id())}))')
    connections.append((ref,pin,net,start,end))

def nc(x,y):
    schlist.append(f'(no_connect (at {f(x)} {f(y)}) (uuid {q(_id())}))');nocon.append((x,y))

# Custom module symbol exact pin geometry: 10 left, 10 right; 1-20 match DIP pads.
Upos=(106.68,81.28)
# y of pin1 is centerY - 22.86; pin20 same
# left pin #i y centerY - (22.86 - (i-1)*2.54)
connected_mod={1:'KEY_PTT',2:'ENC_A',3:'ENC_B',4:'KEY_F1',5:'KEY_F2',18:'GND'}
for n in range(1,21):
    if n<=10: pos=(round(Upos[0]-20.32,4),round(Upos[1]-22.86+(n-1)*2.54,4)); isleft=True
    else: pos=(round(Upos[0]+20.32,4),round(Upos[1]-22.86+(20-n)*2.54,4));isleft=False
    if n in connected_mod:
        end=(round(pos[0]+(-12.7 if isleft else 12.7),4),pos[1]);label_wire('A1',str(n),connected_mod[n],pos,end,0 if isleft else 180)
    else:nc(*pos)

# EC12E2420801 pin A/C/B to P1.4/P1.5/GND; mounting tab pins intentionally unconnected.
SW1pos=(45.72,83.82)
for pin,offset,net in [('A',-2.54,'ENC_A'),('C',0,'GND'),('B',2.54,'ENC_B')]:
    start=(round(SW1pos[0]-10.16,4),round(SW1pos[1]+offset,4));end=(round(start[0]-12.7,4),start[1]);label_wire('SW1',pin,net,start,end)
for offset in (-2.54,2.54):nc(round(SW1pos[0]+10.16,4),round(SW1pos[1]+offset,4))

SWpos={'SW2':(48.26,120.65),'SW3':(48.26,135.89),'SW4':(48.26,151.13)}
for ref,(x,y) in SWpos.items():
    signal={'SW2':'KEY_F1','SW3':'KEY_F2','SW4':'KEY_PTT'}[ref]
    label_wire(ref,'1',signal,(round(x-5.08,4),y),(round(x-20.32,4),y))
    label_wire(ref,'2','GND',(round(x+5.08,4),y),(round(x+17.78,4),y),180)

schlist.append(item_symbol('WebTRX_Custom:'+MOD_NAME,'A1',MOD_NAME,Upos,'WebTRX_Custom:'+MOD_NAME,list(range(1,21)),baseUuid)[0])
schlist.append(item_symbol('WebTRX_Custom:'+ENC_NAME,'SW1',ENC_NAME,SW1pos,'WebTRX_Custom:'+ENC_NAME,['A','B','C','M1','M2'],baseUuid)[0])
for ref,pos in SWpos.items():
    schlist.append(item_symbol('Switch:SW_Push',ref,{'SW2':'F1_12mm','SW3':'F2_12mm','SW4':'PTT_12mm'}[ref],pos,'Button_Switch_THT:SW_PUSH-12mm',['1','2'],baseUuid)[0])

texts=[('WeAct Studio CH552 Core Board V1.0 — onboard Micro-USB, 5V source, BOOT, RESET',(167.64,53.34),1.27),('24 detents / 24 pulses, EC12E2420801: A-B to GPIO input, C=GND',(99.06,111.76),1.27),('F1 / F2 / PTT: standard 12mm NO tactile switches, internal pull-ups',(99.06,168.91),1.27),('USB D+/D- are internal to the WeAct module. DO NOT add external USB or use P3.6/P3.7.',(134.62,179.07),1.27)]
for t,(x,y),sz in texts:
    schlist.append(f'(text {q(t)} (at {f(x)} {f(y)} 0) {eff(sz)} (uuid {q(_id())}))')
# KiCad embedded lib names for custom symbols should be prefixed with library id
customEmbedded=[moddef.replace(f'(symbol "{MOD_NAME}"',f'(symbol "WebTRX_Custom:{MOD_NAME}"',1),encdef.replace(f'(symbol "{ENC_NAME}"',f'(symbol "WebTRX_Custom:{ENC_NAME}"',1)]
sch=f'''(kicad_sch (version 20250114) (generator "eeschema")
 (uuid {q(baseUuid)})
 (paper "A4")
 (title_block (title "WebTRX USB Controller - CH552 Core Board / EC12E2420801") (date "2026-11-19") (rev "A.2"))
 (lib_symbols
 {stock}
 {customEmbedded[0]}
 {customEmbedded[1]}
 )
 {'\n '.join(schlist)}
)
'''
(BASE/(PROJECT+'.kicad_sch')).write_text(sch,encoding='utf-8')
(BASE/(PROJECT+'.kicad_pro')).write_text(json.dumps({'meta':{'filename':PROJECT+'.kicad_pro','version':3}},indent=2)+'\n',encoding='utf-8')

# PCB model: pin1 at top for USB accessible along north edge. 2-layer manually routed Rev.A trial board.
NETS={'GND':1,'ENC_A':2,'ENC_B':3,'KEY_F1':4,'KEY_F2':5,'KEY_PTT':6}

# Simple official standard 12mm switch PCB instance geometry. Same pad positions as KiCad standard library.
def boardfp(ref,libid,val,origin,pads,drawn,attrs='through_hole'):
    ox,oy=origin
    parts=[f'(footprint {q(libid)} (layer "F.Cu") (at {f(ox)} {f(oy)})',
            f'(property "Reference" {q(ref)} (at 0 -6 0) (layer "F.SilkS") {eff(.9)})',
            f'(property "Value" {q(val)} (at 0 11 0) (layer "F.Fab") {eff(.8)})',
            f'(attr {attrs})',
            f'(path "/{baseUuid}/{INSTANCE_UUIDS[ref]}")',
            f'(uuid {q(_id())})']
    parts+=drawn
    for pad in pads:
        num,x,y,shape,size,drill,net,mode=pad
        fmt='(drill '+(f'oval {f(drill[0])} {f(drill[1])}' if isinstance(drill,tuple) else f(drill))+')'
        parts.append(f'(pad {q(num)} {mode} {shape} (at {f(x)} {f(y)}) (size {f(size[0])} {f(size[1])}) {fmt} (layers "*.Cu" "*.Mask")'+
                     (f' (net {NETS[net]} {q(net)})' if net else '')+f' (uuid {q(_id())}))')
    return '\n'.join(parts)+')'

boardFootprints=[];padsByRef={}
# A1 DIP 2x10 center rows x 0 and15.24, y 0..22.86. Module 3V3/USB reserved nets are not copied to accessory board.
A1pos=(76.2,10.16)
modulePads=[]
for n in range(1,21):
    x,y=(0,(n-1)*2.54) if n<=10 else (15.24,(20-n)*2.54)
    net=connected_mod.get(n,None)
    modulePads.append((str(n),x,y,'rect' if n==1 else 'oval',(1.72,1.72),0.90,net,'thru_hole'))
    padsByRef[('A1',str(n))]=(round(A1pos[0]+x,4),round(A1pos[1]+y,4),net)
moduleDrawn=[fp_rect(-.7,-1.5,15.94,24.36),fp_rect(-1.75,-7.3,16.99,25.42,'F.CrtYd',.05),
             fp_line(-.9,-1.7,-.9,24.5),fp_line(16.1,-1.7,16.1,24.5),fp_line(-.9,24.5,16.1,24.5),fp_txt('USB',7.6,-3.4),fp_txt('USB port at top',7.6,-6,0.65,'F.Fab')]
boardFootprints.append(boardfp('A1','WebTRX_Custom:'+MOD_NAME,MOD_NAME,A1pos,modulePads,moduleDrawn))
# Encoder 3 terminals, 2 mechanical ground-free tabs
SW1pcb=(26.0,30.48)
encPads=[('A',-2.5,0,'circle',(1.8,1.8),1.05,'ENC_A','thru_hole'),('C',0,0,'circle',(1.8,1.8),1.05,'GND','thru_hole'),('B',2.5,0,'circle',(1.8,1.8),1.05,'ENC_B','thru_hole'),('M1',-6.6,-7.5,'oval',(3.3,3.6),(2.0,2.1),None,'thru_hole'),('M2',6.6,-7.5,'oval',(3.3,3.6),(2.0,2.1),None,'thru_hole')]
for num,x,y,_,_,_,net,_ in encPads:padsByRef[('SW1',num)]=(round(SW1pcb[0]+x,4),round(SW1pcb[1]+y,4),net)
encoderDrawn=[fp_rect(-6.2,-10.75,6.2,2.45),fp_rect(-8.3,-11.0,8.3,3.1,'F.CrtYd',.05),fp_line(-6.4,-10.8,6.4,-10.8),fp_line(-6.4,2.6,6.4,2.6),fp_txt('A C B',0,3.8,.75,'F.Fab')]
boardFootprints.append(boardfp('SW1','WebTRX_Custom:'+ENC_NAME,ENC_NAME,SW1pcb,encPads,encoderDrawn))
# Tact switches standard KiCad SW_PUSH-12mm pad layout, 4 pads with repeated numbers 1/2.
SWPCB={'SW2':(20.0,54.0),'SW3':(48.0,54.0),'SW4':(76.0,54.0)}
for ref,pos in SWPCB.items():
    net={'SW2':'KEY_F1','SW3':'KEY_F2','SW4':'KEY_PTT'}[ref]
    buttonPads=[]
    for n,x,y in [('1',0,0),('1',12.5,0),('2',0,5),('2',12.5,5)]:
        sig=net if n=='1' else 'GND'
        buttonPads.append((n,x,y,'oval',(3.048,1.85),1.3,sig,'thru_hole'))
        padsByRef[(ref,n,x)]=(round(pos[0]+x,4),round(pos[1]+y,4),sig)
    graphics=[fp_rect(.25,-3.5,12.25,8.5,'F.Fab'),fp_rect(-1.77,-3.75,14.25,8.75,'F.CrtYd',.05),fp_line(.1,-3.65,12.4,-3.65),fp_line(.1,8.65,12.4,8.65),fp_line(.1,-3.65,.1,-1),fp_line(.1,5.9,.1,8.65),fp_line(12.4,-3.65,12.4,-1),fp_line(12.4,5.9,12.4,8.65),fp_txt('12mm',6.25,2.5,1,'F.Fab')]
    boardFootprints.append(boardfp(ref,'Button_Switch_THT:SW_PUSH-12mm',{'SW2':'F1_12mm','SW3':'F2_12mm','SW4':'PTT_12mm'}[ref],pos,buttonPads,graphics))

# Routing: all B.Cu, 0.35 mm tracks. Ground manually connected by star/bus. All 6 nets routed.
routes={
'ENC_A':[[ (76.2,12.70),(60,12.70),(23.5,12.70),(23.5,30.48)]],
'ENC_B':[[ (76.2,15.24),(59,15.24),(28.5,15.24),(28.5,30.48)]],
'KEY_F1':[[ (76.2,17.78),(54,17.78),(54,40),(20,40),(20,54)]],
'KEY_F2':[[ (76.2,20.32),(60,20.32),(60,46),(48,46),(48,54)]],
'KEY_PTT':[[ (76.2,10.16),(84,10.16),(84,48),(76,48),(76,54)]],
'GND':[[ (91.44,15.24),(102,15.24),(102,64),(76,64),(48,64),(20,64),(10,64),(10,36.5),(26,36.5),(26,30.48)],
       [(76,59),(76,64)],[(48,59),(48,64)],[(20,59),(20,64)]]
}
# Avoid GND routing dangerously close to other pad: GND x102 line within board x105 edges okay.
segments=[]
for net,paths in routes.items():
    for path in paths:
        for a,b in zip(path,path[1:]):
            if a==b: continue
            segments.append((net,a,b,.35 if net!='GND' else .5))

# Build PCB file, with editable fully-routed copper and 2-layer rectangle. No external PCB program validation can be asserted.
boardHeader=f'''(kicad_pcb (version 20241229) (generator "pcbnew")
 (general (thickness 1.6))
 (paper "A4")
 (layers (0 "F.Cu" signal) (31 "B.Cu" signal) (32 "B.Adhes" user) (33 "F.Adhes" user) (34 "B.Paste" user) (35 "F.Paste" user) (36 "B.SilkS" user) (37 "F.SilkS" user) (38 "B.Mask" user) (39 "F.Mask" user) (40 "Dwgs.User" user) (41 "Cmts.User" user) (42 "Eco1.User" user) (43 "Eco2.User" user) (44 "Edge.Cuts" user) (45 "Margin" user) (46 "B.CrtYd" user) (47 "F.CrtYd" user) (48 "B.Fab" user) (49 "F.Fab" user))
 (setup (pad_to_mask_clearance 0))
'''
boardHeader+='\n'.join(f'(net {num} {q(name)})' for name,num in [('',0)]+list(NETS.items()))+'\n'
boardTracks='\n'.join(f'(segment (start {f(a[0])} {f(a[1])}) (end {f(b[0])} {f(b[1])}) (width {f(w)}) (layer "B.Cu") (net {NETS[net]}) (uuid {q(_id())}))' for net,a,b,w in segments)
boardShape='\n'.join(f'(gr_line (start {f(a)} {f(b)}) (end {f(c)} {f(d)}) (stroke (width 0.1) (type default)) (layer \"Edge.Cuts\") (uuid {q(_id())}))' for a,b,c,d in [(5,0,105,0),(105,0,105,70),(105,70,5,70),(5,70,5,0)])
boardTxt='\n'.join(f'(gr_text {q(txt)} (at {f(x)} {f(y)} 0) (layer "F.SilkS") {eff(.9)} (uuid {q(_id())}))' for txt,x,y in [
    ('WebTRX Rev.A',16,10),('F1',26,47),('F2',54,47),('PTT',82,47),('CW/CCW',26,41),('USB',84,7)])
board=boardHeader+'\n'.join(boardFootprints)+'\n'+boardShape+'\n'+boardTxt+'\n'+boardTracks+'\n)\n'
(BASE/(PROJECT+'.kicad_pcb')).write_text(board,encoding='utf8')

# BOM / pin CSV
with (BASE/'BOM_RevA.csv').open('w',newline='',encoding='utf-8-sig') as h:
    cw=csv.writer(h);cw.writerow(['Reference','Part','Quantity','Symbol','Footprint','Notes'])
    cw.writerow(['A1','WeAct Studio CH552 Core Board V1.0 / CH552T',1,'WebTRX_Custom:'+MOD_NAME,'WebTRX_Custom:'+MOD_NAME,'USB Micro-B onboard, module pin 1..20 direct; verify board mechanical fit'])
    cw.writerow(['SW1','ALPS Alpine EC12E2420801',1,'WebTRX_Custom:'+ENC_NAME,'WebTRX_Custom:'+ENC_NAME,'24 detents; M1/M2 mechanical mounting pads'])
    for name in ('SW2','SW3','SW4'):
        cw.writerow([name,'12mm square momentary NO tact switch, E-Switch TL1100 footprint compatible',1,'Switch:SW_Push','Button_Switch_THT:SW_PUSH-12mm','Match selected switch to 12.5x5 mm pin pattern'])

with (BASE/'PIN_ASSIGNMENT.csv').open('w',newline='',encoding='utf-8-sig') as h:
    cw=csv.writer(h);cw.writerow(['Reference','Pad','Signal','Connection'])
    for n,net in sorted(connected_mod.items()):cw.writerow(['A1',n,net,{1:'P3.2',2:'P1.4',3:'P1.5',4:'P1.6',5:'P1.7',18:'GND'}[n]])
    for p,net in [('A','ENC_A'),('C','GND'),('B','ENC_B')]:cw.writerow(['SW1',p,net,'EC12E2420801'])
    for ref,net in [('SW2','KEY_F1'),('SW3','KEY_F2'),('SW4','KEY_PTT')]:cw.writerow([ref,1,net,'12mm switch (2 paralleled pads numbered 1)']);cw.writerow([ref,2,'GND','12mm switch (2 paralleled pads numbered 2)'])

README='''# WebTRX Controller Rev.A.2 — KiCad 10 編集可能データ

## 回路・採用部品

- A1: **WeAct Studio CH552 Core Board V1.0 / CH552T**。専用シンボル／専用フットプリント（2×10ピン、2.54mmピッチ・端子列間15.24mm）。ボード内蔵の Micro-USB を電源・USB HID・書き込みに使用する。外付けUSBコネクタやCH552T単体部品は実装しない。USBコネクタはPCB上端側を向く。
- SW1: **ALPS Alpine EC12E2420801** 24クリック／24パルス。メーカー取付寸法（端子A-C-B、2.5mm刻み、支持金具間13.2mm、端子列と支持穴間7.5mm）に基づく専用シンボル・フットプリント。金具M1/M2は電気的に未接続で、支持・はんだ付け用途。
- SW2, SW3, SW4: F1/F2/PTT、12mm角モーメンタリNO。KiCad標準シンボル `Switch:SW_Push` と標準フットプリント `Button_Switch_THT:SW_PUSH-12mm` を採用。標準フットプリントはE-Switch TL1100系の12.5×5mm穴ピッチ。**任意の12mm角タクトに合うわけではないため型番・実物寸法の一致確認が必須**。
- GPIO入力は内部プルアップを利用、押下時にGND。回転A=P1.4、B=P1.5、共通C=GND、F1=P1.6、F2=P1.7、PTT=P3.2。
- P3.6/P3.7/RSTをゲームボタンとして利用しない。モジュール側既存のUSB/書き込み機能を維持する。

## 部品実装と基板

`WebTRX_Controller.kicad_sch`: 専用モジュール・エンコーダー・標準タクトを接続した回路図。グローバルラベルを使用。未使用モジュール端子にはNo Connectを付与。

`WebTRX_Controller.kicad_pcb`: 100×70mm、2層、1ozを想定した**試作レイアウト**。5信号+GNDの配線をB.Cuに追加し、USBコネクタ方向と操作スイッチを上面に示す。**KiCad CLIのDRC検査は実行していないため、製造承認・Gerber確定ではない。**

`WebTRX_Custom.kicad_sym`, `WebTRX_Custom.pretty/`: 正規のKiCad編集可能な独立ライブラリ。エンコーダー・CH552専用シンボルのピン番号とPCBパッド番号を一致させる。`sym-lib-table` / `fp-lib-table` でプロジェクト相対パス登録。

既存 HID の「1クリック→X軸 0→±127」およびF1/F2/PTTの任意キー割り当ては変更なし。ソフトウェアのUSBデバイスIDも変更しない。

## 根拠と制約

- WeAct Studio: https://github.com/WeActStudio/WeActStudio.CH552CoreBoard
- ピン配列・20端子2.54mm/15.24mm: オープンソース実装例 https://github.com/rgoulter/keyboard-labs （`pcb/ProjectLocal.kicad_sym` と `pcb/keyboard-ch552-44.kicad_pcb`）。**外形・USBコネクタの立体干渉はメーカー機械図の現物確認未完了。**
- エンコーダー: https://tech.alpsalpine.com/e/products/detail/EC12E2420801/ および公式カタログ https://tech.alpsalpine.com/assets/catalog/product-catalog-ec-all.en.pdf のD-13 取付穴図。支持金具孔の現物適合を優先確認。
- KiCad標準12mmタクト: https://github.com/KiCad/kicad-footprints/blob/master/Button_Switch_THT.pretty/SW_PUSH-12mm.kicad_mod

## 重要: 検証状況

- 内部静的検査: ピン番号、ネット名、シンボル／フットプリント一致、50mil、基板トラック端点、ネット配線、カスタムライブラリ構文の整合をチェック。
- KiCad 10.0.x実アプリでの読み込み・ERC/DRC・描画・フットプリントからPCB同期: **未実行**。本環境にはKiCad CLI/GUIがない。
- 実機組立・クリック誤計数・PTT安全機能・WebTRX運用: **未検証**。
- **フットプリント機械寸法とUSB挿抜・コネクタ高さの干渉は、製造前に実機で確認すること。**

Power Flagは内蔵USB給電を独立部品として表現しないため、外部回路には不要と判断している。A1の5V/3V3はNC、GNDは受動端子とし誤った給電宣言を避けた。

Windows PowerShellのKiCad CLI検証例：

```powershell
& 'C:\\Program Files\\KiCad\\10.0\\bin\\kicad-cli.exe' sch erc .\\WebTRX_Controller.kicad_sch -o ERC_report.txt
& 'C:\\Program Files\\KiCad\\10.0\\bin\\kicad-cli.exe' pcb drc .\\WebTRX_Controller.kicad_pcb -o DRC_report.txt
```
'''
(BASE/'README_JA.md').write_text(README,encoding='utf8')

# JSON machine-readable origin info and derived objects
checks={
'pcb_pads_by_ref':{':'.join(str(v) for v in key):list(x) for key,x in padsByRef.items()},
'connection_count':len(connections),'nc_count':len(nocon),
'route_segment_count':len(segments),'route_nets':list(NETS),
'symbols':{'A1':20,'SW1':5,'SW2':2,'SW3':2,'SW4':2},
'net_refs':sorted([f'{r}.{p}={net}' for r,p,net,*_ in connections]),
'source_pinout':'rgoulter/keyboard-labs ProjectLocal WeAct_CH552CoreBoard',
'source_encoder':'ALPS Alpine EC12E2420801 manufacturer drawing D-13',
'expected_static_only':True}
(BASE/'CHECKS_DATA.json').write_text(json.dumps(checks,indent=2,ensure_ascii=False)+'\n',encoding='utf8')

print('OUTPUT',BASE)
print('SCHEMATIC',len(sch),'PCB',len(board),'custom library',len(moddef),len(encdef))
print('NETS',NETS,'WIRE',len(connections),'NC',len(nocon),'TRACK',len(segments))
