#!/usr/bin/env python3
import re, sys
def parse(path):
    txt = open(path).read()
    comp = {}
    body = txt[txt.index("(nets"):]
    for m in re.finditer(r'\(net\s+\(code\s+"[^"]*"\)\s*\(name\s+"([^"]*)"\)(.*?)(?=\(net\s+\(code|\Z)', body, re.S):
        net = m.group(1)
        for nm in re.finditer(r'\(node\s+\(ref\s+"([^"]+)"\)\s*\(pin\s+"([^"]+)"\)', m.group(2)):
            comp.setdefault(nm.group(1), {})[nm.group(2)] = net
    return comp
sealed = parse(sys.argv[1]); demo = parse(sys.argv[2])
MODS = ["RS","RP","RN","CD","CB","U"]; overall=True; addr={}; canon_by={}
for i in range(1,7):
    print(f"\n=== CHANNEL {i} (U{i}, expect 0x{0x3f+i:02X}) ===")
    ok=True; canon={}
    for base in MODS:
        ref=f"{base}{i}"; s=sealed.get(ref); d=demo.get(ref)
        if s is None: print(f"  {ref}: MISSING in sealed"); ok=False; continue
        if d is None: print(f"  {ref}: MISSING in demo"); ok=False; continue
        if s!=d:
            print(f"  {ref}: MISMATCH\n      sealed:{s}\n      demo  :{d}"); ok=False
        else: print(f"  {ref}: OK  {s}")
        for pad,net in d.items():
            canon[(base,pad)]=re.sub(r'^(VF|VP|KA|KB)'+str(i)+r'$', r'\1', net)
    canon_by[i]=canon
    u=demo.get(f"U{i}",{}); addr[i]=(u.get("1"),u.get("2"))
    print(f"  -> channel {i}: {'PASS' if ok else 'FAIL'}"); overall&=ok
print("\n=== CHANNEL MUTUAL ISOMORPHISM ===")
ref=canon_by[1]; iso=all(canon_by[i]==ref for i in range(2,7))
print(f"  all 6 identical after channel-normalization: {'YES' if iso else 'NO'}")
print("\n=== INA238 ADDRESS STRAPS (A1 pad1 / A0 pad2) ===")
for i in range(1,7): print(f"  U{i} (0x{0x3f+i:02X}): A1={addr[i][0]}  A0={addr[i][1]}")
distinct=len(set(addr.values()))==6
print(f"  all 6 strap-pairs distinct: {'YES' if distinct else 'NO'}")
print("\n=== KELVIN SENSE PRESERVED ===")
kok=True
for i in range(1,7):
    rp=demo[f"RP{i}"]; rn=demo[f"RN{i}"]; u=demo[f"U{i}"]; rs=demo[f"RS{i}"]
    ok=(rp["1"]==rs["1"] and rp["2"]==u["10"] and rn["1"]==rs["2"] and rn["2"]==u["9"]==u["8"])
    print(f"  ch{i}: RP {rs['1']}->{u['10']}(IN+), RN {rs['2']}->{u['9']}(IN-/VBUS): {'OK' if ok else 'BAD'}"); kok&=ok
print("\n"+"="*50)
print(f"NODE-FOR-NODE PARITY vs sealed: {'PASS' if overall else 'FAIL'}")
print(f"CHANNELS MUTUALLY ISOMORPHIC: {'PASS' if iso else 'FAIL'}")
print(f"ADDRESSES DISTINCT 0x40..0x45: {'PASS' if distinct else 'FAIL'}")
print(f"KELVIN PRESERVED: {'PASS' if kok else 'FAIL'}")
sys.exit(0 if (overall and iso and distinct and kok) else 1)
