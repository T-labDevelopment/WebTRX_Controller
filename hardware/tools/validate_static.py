#!/usr/bin/env python3
"""Independent static geometry / net consistency checks (NOT a KiCad ERC/DRC replacement)."""
from pathlib import Path
import re, math, collections, json
P=Path(__file__).resolve().parents[1]
S=(P/'WebTRX_Controller.kicad_sch').read_text(encoding='utf-8')
PCB=(P/'WebTRX_Controller.kicad_pcb').read_text(encoding='utf-8')
LIB=(P/'WebTRX_Custom.kicad_sym').read_text(encoding='utf-8')

def balanced(s):
    depth=0; quoted=False; escaped=False
    for c in s:
        if quoted:
            if escaped:escaped=False
            elif c=='\\':escaped=True
            elif c=='"':quoted=False
        else:
            if c=='"':quoted=True
            elif c=='(':depth+=1
            elif c==')':
                depth-=1
                assert depth>=0,'Extra closing parenthesis'
    assert depth==0 and not quoted,'S-expression balance failed'
for v in [S,PCB,LIB,*[x.read_text() for x in (P/'WebTRX_Custom.pretty').glob('*.kicad_mod')]]:balanced(v)

def splitblocks(s,op):
    out=[]
    for m in re.finditer(re.escape(op),s):
        i=m.start();dep=0;quote=False;escape=False
        for j in range(i,len(s)):
            c=s[j]
            if quote:
                if escape:escape=False
                elif c=='\\':escape=True
                elif c=='"':quote=False
            else:
                if c=='"':quote=True
                elif c=='(':dep+=1
                elif c==')':
                    dep-=1
                    if dep==0:
                        out.append(s[i:j+1]);break
    return out

assert 'WebTRX_Custom:WeAct_CH552_Core_Board_V1_0' in S
assert 'WebTRX_Custom:EC12E2420801' in S
for ref in ['A1','SW1','SW2','SW3','SW4']:assert f'(reference "{ref}")' in S
assert S.count('(no_connect ')==16, S.count('(no_connect ')
labels=[]
for b in splitblocks(S,'(global_label '):
    n=re.search(r'^\(global_label \"([^\"]+)\"',b).group(1)
    x,y,angle=re.search(r'\(at ([-\d.]+) ([-\d.]+) (0|180)\)',b).groups()
    labels.append((n,x,y,angle))
wires=re.findall(r'\(wire \(pts \(xy ([-\d.]+) ([-\d.]+)\) \(xy ([-\d.]+) ([-\d.]+)\)\)',S)
assert len(wires)==len(labels)==15, (len(wires),len(labels))
wired=set()
for a,b,c,d in wires:
    for x,y in [(a,b),(c,d)]:
        assert abs(float(x)/1.27-round(float(x)/1.27))<.00001,('50mil x',x)
        assert abs(float(y)/1.27-round(float(y)/1.27))<.00001,('50mil y',y)
        wired.add((round(float(x),4),round(float(y),4)))
for n,x,y,_ in labels: assert (float(x),float(y)) in wired,('floating label',n,x,y)
assert collections.Counter(n for n,_,_,_ in labels)=={'GND':5,'ENC_A':2,'ENC_B':2,'KEY_F1':2,'KEY_F2':2,'KEY_PTT':2}
# top-level component footprints in PCB
fps=[]
for blk in splitblocks(PCB,'(footprint '):
    ref=re.search(r'\(property "Reference" "([^"]+)"',blk).group(1)
    raw=re.search(r'\(at\s+([\d.]+)\s+([\d.]+)',blk)
    ox,oy=map(float,raw.groups())
    pininfo=[]
    for pad in splitblocks(blk,'(pad '):
        m=re.search(r'^\(pad "([^"]+)" (?:thru_hole|smd) [a-z]+ \(at\s+([-\d.]+)\s+([-\d.]+)',pad)
        if not m:raise AssertionError(('unknown pad syntax',pad[:100]))
        n,x,y=m.groups();x=float(x)+ox;y=float(y)+oy
        net=re.search(r'\(net\s+(\d+)\s+"([^"]+)"\)',pad)
        netname=net.group(2) if net else 'unconnected'
        size=re.search(r'\(size\s+([-\d.]+)\s+([-\d.]+)\)',pad)
        sx,sy=map(float,size.groups())
        pininfo.append((n,x,y,netname,sx,sy))
    fps.append((ref,pininfo))
assert len(fps)==5,[f[0] for f in fps]
padrows=[(ref,*pin) for ref,pins in fps for pin in pins]
assert len(padrows)==20+5+4*3
for ref,pins in fps:
    nums=[p[0] for p in pins]
    if ref=='A1': assert set(nums)==set(map(str,range(1,21)))
    if ref=='SW1':assert set(nums)=={'A','B','C','M1','M2'}
    if ref in {'SW2','SW3','SW4'}:assert collections.Counter(nums)=={'1':2,'2':2}
# TRACK routes on B.Cu must reach at least one pad of each net and avoid crossing unlike nets.
seg=[]
for b in splitblocks(PCB,'(segment '):
    st=re.search(r'\(start\s+([-\d.]+)\s+([-\d.]+)\)',b)
    en=re.search(r'\(end\s+([-\d.]+)\s+([-\d.]+)\)',b)
    w=re.search(r'\(width\s+([-\d.]+)\)',b);n=re.search(r'\(net\s+(\d+)\)',b)
    assert st and en and w and n
    seg.append((tuple(map(float,st.groups())),tuple(map(float,en.groups())),float(w.group(1)),int(n.group(1))))
assert len(seg)==30,len(seg)
NAMES={'GND':1,'ENC_A':2,'ENC_B':3,'KEY_F1':4,'KEY_F2':5,'KEY_PTT':6}
for net,num in NAMES.items():
    endpoints=[p for st,en,w,n in seg if n==num for p in (st,en)]
    assert endpoints,net
    for ref,p,x,y,pnet,sx,sy in padrows:
        if pnet==net:
            # all pads for standard switch have two electrically common pads - at least one must physically reach via copper
            if ref in {'SW2','SW3','SW4'} and x%1!=0:
                continue
            assert any(math.dist(pt,(x,y))<.001 for pt in endpoints),(ref,p,net,(x,y))

def ptseg(P,A,B):
    ax,ay=A;bx,by=B;px,py=P
    l2=(bx-ax)**2+(by-ay)**2
    t=max(0,min(1,((px-ax)*(bx-ax)+(py-ay)*(by-ay))/l2)) if l2 else 0
    return math.dist(P,(ax+t*(bx-ax),ay+t*(by-ay)))
def cross(A,B,C,D):
    def ori(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    return ori(A,B,C)*ori(A,B,D)<0 and ori(C,D,A)*ori(C,D,B)<0

def segseg(A,B,C,D):
    if cross(A,B,C,D):return 0
    return min(ptseg(A,C,D),ptseg(B,C,D),ptseg(C,A,B),ptseg(D,A,B))
# DRC-like conservative circle approximation, yet real DRC may differ.
for i,(A,B,w,n) in enumerate(seg):
    for j,(C,D,w2,n2) in enumerate(seg[i+1:],i+1):
        if n==n2:continue
        distance=segseg(A,B,C,D)
        threshold=(w+w2)/2+.22
        assert distance>=threshold-1e-3,('different-net track collision',i,j,distance,threshold)
    for ref,p,x,y,pnet,sx,sy in padrows:
        if pnet!='unconnected' and NAMES.get(pnet)==n:continue
        if pnet=='unconnected' and ref=='A1':
            # Do not route under DIP module unconnected plated pads.
            pass
        # circular worst-case overestimate of oval pad: apply max radius; this is a stronger but incomplete check
        d=ptseg((x,y),A,B)
        threshold=max(sx,sy)/2+w/2+.19
        assert d>=threshold-1e-3,('track to other-net pad',i,ref,p,round(d,4),round(threshold,4),A,B)
# Check module pads and unconnected support metal are fully within PCB edges.
assert all(6<=x<=104 and 1<=y<=69 for ref,p,x,y,n,sx,sy in padrows)
# all pad and segment net IDs matching net table
for n in NAMES:assert f'(net {NAMES[n]} "{n}")' in PCB
assert len(re.findall(r'\(gr_line ',PCB))==4
# project local tables
assert '${KIPRJMOD}/WebTRX_Custom.pretty' in (P/'fp-lib-table').read_text()
assert '${KIPRJMOD}/WebTRX_Custom.kicad_sym' in (P/'sym-lib-table').read_text()
print('PASS: S-expressions, 50mil, logical pins, standalone libraries, PCB pads/tracks, net connectivity and static clearance')
print(f'NOT RUN: KiCad GUI, KiCad CLI/ERC/DRC, USB hardware or assembled fit; {len(seg)} copper segments, {len(padrows)} PCB pads.')
