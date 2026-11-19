#!/usr/bin/env python3
"""Generate KiCad 10 schematic using *verbatim* installed official library symbols.

The complete standard symbol bodies, including all pin alternate definitions,
are read from KiCad 10. This tool does not synthesize a simplified symbol cache.
Generated .kicad_sch has to be checked with KiCad 10 CLI/ERC on the target machine.
"""
from __future__ import annotations
import argparse
import os
from pathlib import Path
import re
import sys
import uuid

NAME = 'USB_Rotary_Dial'
SCHEMA_VERSION = '20250114'

def uid():
    return str(uuid.uuid4())

def q(s):
    return '"' + str(s).replace('\\', '\\\\').replace('"', '\\"') + '"'

def fmt(x):
    return f'{x:.4f}'.rstrip('0').rstrip('.') if x else '0'

def sexpr_at(src: str, start: int) -> str:
    """Return exact balanced S-expression beginning at start, respecting escapes."""
    if src[start] != '(':
        raise ValueError('Expected (')
    depth, quoted, esc = 0, False, False
    for idx in range(start, len(src)):
        c = src[idx]
        if quoted:
            if esc: esc = False
            elif c == '\\': esc = True
            elif c == '"': quoted = False
        elif c == '"': quoted = True
        elif c == '(': depth += 1
        elif c == ')':
            depth -= 1
            if depth == 0: return src[start:idx + 1]
    raise ValueError('Unbalanced S-expression')

def locate_lib(root: Path, lib: str, sym: str) -> Path:
    p = root / f'{lib}.kicad_symdir' / f'{sym}.kicad_sym'
    if p.is_file(): return p
    legacy = root / f'{lib}.kicad_sym'
    if legacy.is_file(): return legacy
    raise FileNotFoundError(f'{sym}: Official KiCad 10 symbol not found at {p}')

def load_symbol(root: Path, lib: str, name: str) -> tuple[str, str]:
    p = locate_lib(root, lib, name)
    s = p.read_text(encoding='utf-8')
    m = re.search(r'\(symbol\s+"' + re.escape(name) + r'"', s)
    if not m:
        raise ValueError(f'{name} missing in {p}')
    original = sexpr_at(s, m.start())
    # The only modification to the *original official symbol* is the qualified ID.
    modified = original.replace(f'(symbol "{name}"', f'(symbol "{lib}:{name}"', 1)
    return modified, str(p)

def pins_from_symbol(symbol: str):
    """Read direct pin blocks; preserve all multi-pin/hide information."""
    pins = {}
    for m in re.finditer(r'\(pin\s+(?:bidirectional|passive|power_in|power_out|input|output|tri_state|open_collector|open_emitter|unspecified|no_connect)\s+\w+', symbol):
        b = sexpr_at(symbol, m.start())
        a = re.search(r'\(at\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\s+(-?\d+)', b)
        n = re.search(r'\(number\s+"([^"]+)"', b)
        if not (a and n): raise ValueError('Could not parse pin block')
        # KiCad10 has hide=yes on direct pin field, not on the alternate pins.
        hidden = bool(re.search(r'^\s*\(hide yes\)', b, re.M))
        pins[n.group(1)] = (float(a.group(1)), float(a.group(2)), int(a.group(3)), hidden)
    return pins

def find_root(override: str | None):
    candidates=[]
    if override: candidates.append(Path(override))
    for key in ('KICAD10_SYMBOL_DIR', 'KICAD_SYMBOL_DIR'):
        v=os.getenv(key)
        if v: candidates.append(Path(v))
    candidates += [Path('C:/Program Files/KiCad/10.0/share/kicad/symbols'),
                   Path('C:/Program Files/KiCad/10.0/share/kicad/symbols/kicad-symbols'),
                   Path('/usr/share/kicad/symbols'),
                   Path('/usr/local/share/kicad/symbols')]
    for p in candidates:
        if (p/'MCU_Module.kicad_symdir'/'RaspberryPi_Pico.kicad_sym').is_file(): return p
    raise FileNotFoundError('KiCad 10 official symbols directory not found. Use --symbol-root.')

def effects(hide=False, justify=''):
    return f'(effects (font (size 1.27 1.27)) {f"(justify {justify})" if justify else ""} {"(hide yes)" if hide else ""})'

def wire(a, b):
    return f'\t(wire (pts (xy {fmt(a[0])} {fmt(a[1])}) (xy {fmt(b[0])} {fmt(b[1])})) (stroke (width 0) (type default)) (uuid {q(uid())}))'

def glabel(n, p, rot=0):
    return (f'\t(global_label {q(n)} (shape passive) (at {fmt(p[0])} {fmt(p[1])} {rot}) '
            f'{effects(justify="left") } (uuid {q(uid())}))')

def node(lib, val, ref, x, y, rot, project_uuid, footprint, datasheet):
    # Keep all library symbols' official geometry; only instance properties change.
    def prop(field, value, x2, y2, hide=False):
        return f'\t\t(property {q(field)} {q(value)} (at {fmt(x2)} {fmt(y2)} 0) {effects(hide)})'
    ident=f'{lib}:{val}'
    u=uid()
    props=[prop('Reference', ref, x+19.05, y-37 if lib=='MCU_Module' else y-8.89),
           prop('Value', val, x+19.05, y-34.29 if lib=='MCU_Module' else y+8.89),
           prop('Footprint', footprint, x, y, True),
           prop('Datasheet', datasheet, x, y, True)]
    return (f'\t(symbol (lib_id {q(ident)}) (at {fmt(x)} {fmt(y)} {rot}) (unit 1) '\
            f'(exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (uuid {q(u)})\n'
            + '\n'.join(props) + '\n'
            + f'\t\t(instances (project {q(NAME)} (path "/{project_uuid}" (reference {q(ref)}) (unit 1))))\n'
            + '\t)')

def transform_pin(p, x, y):
    # Symbol local y+ points upward. Sheet coordinates y+ point downward.
    return round(x+p[0], 4), round(y-p[1], 4)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--symbol-root', help='KiCad 10 official symbol root folder')
    ap.add_argument('--output', default='hardware/USB_Rotary_Dial.kicad_sch')
    args=ap.parse_args()
    root=find_root(args.symbol_root)
    pico, ps=load_symbol(root,'MCU_Module','RaspberryPi_Pico')
    encoder, es=load_symbol(root,'Device','RotaryEncoder')
    pp=pins_from_symbol(pico)
    ep=pins_from_symbol(encoder)
    assert {'3','4','5','39'}.issubset(pp), pp.keys()
    assert {'A','B','C'}.issubset(ep), ep.keys()
    origin_p=(139.7,101.6)
    origin_e=(66.04,101.6)
    positions_p={k:transform_pin(v,*origin_p) for k,v in pp.items()}
    positions_e={k:transform_pin(v,*origin_e) for k,v in ep.items()}
    proj=uid()
    rootlines=[f'(kicad_sch (version {SCHEMA_VERSION}) (generator {q("eeschema")})',
               f'\t(uuid {q(proj)})', '\t(paper "A4")',
               '\t(title_block (title "USB Rotary Dial Gamepad") (date "2026-11-18") (rev "A"))',
               '\t(lib_symbols', '\t\t'+pico, '\t\t'+encoder, '\t)']
    # Separate global labels are intentional; note three nets use global labels per project policy.
    for net,epin,ppin in [('ENC_A','A','4'),('ENC_B','B','5'),('GND','C','3')]:
        pe=positions_e[epin]
        en=(round(pe[0]-7.62,4),pe[1])
        rootlines.extend([wire(pe,en),glabel(net,en)])
        pc=positions_p[ppin]
        pn=(pc[0],round(pc[1]+6.35,4)) if ppin=='3' else (round(pc[0]-8.89,4),pc[1])
        rootlines.extend([wire(pc,pn),glabel(net,pn,90 if ppin=='3' else 0)])
    # The Pico contains its own USB supply path; unused external pins are marked NC
    # so that ERC does not presume an unshown external power source on VSYS/ADC_VREF.
    for num,(x,y,a,hidden) in pp.items():
        if num in {'3','4','5'} or hidden: continue
        px,py=positions_p[num]
        rootlines.append(f'\t(no_connect (at {fmt(px)} {fmt(py)}) (uuid {q(uid())}))')
    rootlines.extend([node('MCU_Module','RaspberryPi_Pico','A1',*origin_p,0,proj,
                           'Module:RaspberryPi_Pico_Common_Unspecified',
                           'https://datasheets.raspberrypi.com/pico/pico-datasheet.pdf'),
                      node('Device','RotaryEncoder','SW1',*origin_e,0,proj,'',
                           'https://tech.alpsalpine.com/e/products/detail/EC12E2430803/'),
                      ')'])
    out=Path(args.output)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text('\n'.join(rootlines)+'\n',encoding='utf-8')
    print(f'Generated {out} with official KiCad symbols from:\n- {ps}\n- {es}')
    print('ERC and visual review have NOT been run. Do not submit PCB to fabrication.')

if __name__=='__main__':
    try: main()
    except Exception as exc:
        print(f'ERROR: {exc}',file=sys.stderr)
        sys.exit(1)
