#!/usr/bin/env python3
"""Final width-floor backstop: lift any track below its nets.yaml class
floor (EXACT nm compare). Runs at the end of the rebuild chain — repair
passes and tap routing can (re)introduce sub-floor segments after the
stitcher's early lift."""
import sys
from pathlib import Path
import pcbnew
try:
    import yaml
except ImportError:
    sys.exit("needs pyyaml")

HERE = Path(__file__).parent
b = pcbnew.LoadBoard(str(HERE.parent / "04_kicad" / "shitty_kitty.kicad_pcb"))
cfg = yaml.safe_load(open(HERE / "rules" / "nets.yaml"))
FLOOR = {}
for c in cfg["classes"].values():
    w = float(str(c["min_width"]).replace("mm", ""))
    for n in c["nets"]:
        FLOOR[n] = w
lifted = 0
for tr in b.GetTracks():
    if tr.GetClass() != "PCB_TRACK":
        continue
    fl = FLOOR.get(tr.GetNetname())
    if fl and tr.GetWidth() < int(fl * 1e6):
        tr.SetWidth(int(fl * 1e6))
        lifted += 1
if lifted:
    b.Save(str(HERE.parent / "04_kicad" / "shitty_kitty.kicad_pcb"))
print(f"final floor lift: {lifted} segments")
