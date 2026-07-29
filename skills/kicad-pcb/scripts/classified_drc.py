"""Severity-classified DRC report: real vs margin vs same-net.

    /usr/bin/python3 classified_drc.py BOARD.kicad_pcb [--fab-floor 0.10] [--refill]

Real = different-net AND below the fab floor -> exit 1.
WARNING: --refill SAVES THE INPUT BOARD IN PLACE (fill + save). Omit it to
keep the gate read-only. Note "margin" here = different-net >= floor;
same-net items are counted separately (audit_template.py lumps same-net
into *_margin — don't compare baselines across the two scripts).
Margin (>= floor) and same-net items are reported but do not fail.
Remember: GUI DRC remains authoritative for zone-fill-dependent checks
(starved_thermal); this is the scriptable gate, not a replacement.

G-COVER (canon M-COVER, 2026-07-27). `VERDICT: PASS` carried no denominator,
so a report this script could not PARSE — a KiCad release that changed the
`[type]: ` block format, a truncated write, an empty file — produced zero
categories, zero clearance items, and a confident PASS. It now reports
`N classified / M violations in the report` and FAILS when the report cannot
be parsed into blocks at all, rather than reading an unreadable report as a
clean board.
"""
import argparse
import collections
import os
import re
import sys
from pathlib import Path

import pcbnew

def _write_drc_report(board, board_path, rpt):
    if hasattr(pcbnew, "EDA_UNITS_MILLIMETRES"):
        # KiCad 7/8: in-process report works headless
        pcbnew.WriteDRCReport(board, rpt, pcbnew.EDA_UNITS_MILLIMETRES, False)
    else:
        # KiCad >= 9: WriteDRCReport segfaults without the GUI Pgm() instance;
        # kicad-cli (v8+) emits the same [type]-tagged report format
        import subprocess
        subprocess.run(
            ["kicad-cli", "pcb", "drc", "--severity-all", "--refill-zones",
             "--format", "report", "-o", rpt, str(board_path)],
            check=True, capture_output=True)


ap = argparse.ArgumentParser()
ap.add_argument("board")
ap.add_argument("--fab-floor", type=float, default=0.10,
                help="fab clearance floor in mm (JLC 4L+: 0.10)")
ap.add_argument("--refill", action="store_true",
                help="refill zones (and save) before DRC")
ap.add_argument("--report", default="",
                help="CLASSIFY AN EXISTING DRC REPORT instead of running DRC. "
                     "The board is not opened at all. This is a REPLAY path "
                     "(and the seam the G-COVER known-bad fixture uses to "
                     "hand this script a report it cannot parse); it is NOT a "
                     "substitute for grading the board, and the verdict names "
                     "the report file so a stale one is visible.")
args = ap.parse_args()

if args.report:
    rpt = args.report
    print(f"NOTE: --report REPLAY — DRC was NOT run; classifying the existing "
          f"report at {rpt}. The board was not opened.")
else:
    board = pcbnew.LoadBoard(args.board)
    if args.refill:
        pcbnew.ZONE_FILLER(board).Fill(board.Zones())
        board.Save(args.board)
        board = pcbnew.LoadBoard(args.board)

    # pid-suffixed: the old fixed /tmp/classified_drc.txt collided across
    # concurrent sessions (a live clean-room canary's DRC clobbered a test-suite
    # run's report mid-read, 2026-07-21 — the t4 clearance pair flaked with
    # another board's categories in its output)
    rpt = f"/tmp/classified_drc.{os.getpid()}.txt"
    _write_drc_report(board, args.board, rpt)
txt = Path(rpt).read_text(encoding="utf-8-sig")

blocks = re.split(r"\[(\w+)\]: ", txt)
cats = collections.Counter(blocks[1::2])
real, margin, samenet = [], 0, 0
for i in range(1, len(blocks) - 1, 2):
    cat, body = blocks[i], blocks[i + 1]
    if cat not in ("clearance", "hole_clearance"):
        continue
    m = re.search(r"actual ([0-9.]+) mm", body)
    v = float(m.group(1)) if m else -1.0
    nets = set(re.findall(r"\[([A-Za-z0-9_/.+-]+)\]", body))
    if len(nets) > 1 and 0 <= v < args.fab_floor:
        real.append((cat, round(v, 3), sorted(nets)))
    elif len(nets) > 1:
        margin += 1
    else:
        samenet += 1

# G-INPUT: name the board AND the report actually graded, so a reader can tell
# a sealed board from a 06_build reconstruction (canon M-SHIP) and can find the
# raw report this verdict summarises.
print(f"input: board  = {Path(args.board).resolve()}")
print(f"input: report = {rpt} ({len(txt)} bytes)")

total_items = sum(cats.values())
clearance_items = cats.get("clearance", 0) + cats.get("hole_clearance", 0)
classified = len(real) + margin + samenet

# G-COVER: the report must have PARSED. `re.split` on a format this script no
# longer recognises yields one block and zero categories, which used to render
# as a clean board. An unparseable input is a FAIL, never a skip.
if total_items == 0 and txt.strip() and not re.search(
        r"\b0 (?:DRC )?(?:violations|errors|problems|unconnected)", txt, re.I):
    print(f"classified 0/0 — the DRC report at {rpt} is non-empty "
          f"({len(txt)} bytes) but yielded ZERO `[type]: ` blocks and does not "
          f"state a zero count either, so this script did not understand it. "
          f"An unparseable report is a FAIL, never a clean board "
          f"(canon M-COVER).")
    print("VERDICT: FAIL")
    sys.exit(1)

print("categories:", dict(cats.most_common()) or "NONE")
print(f"unconnected: {cats.get('unconnected_items', 0)}  "
      f"shorts: {cats.get('shorting_items', 0)}")
print(f"clearance-class items: REAL={len(real)}  margin(>= {args.fab_floor})="
      f"{margin}  same-net={samenet}")
if clearance_items != classified:
    print(f"  WARNING: {classified}/{clearance_items} clearance-class items "
          f"were classified — {clearance_items - classified} were counted by "
          f"category but did not reach a REAL/margin/same-net bucket")
for r in real[:20]:
    print("  REAL:", r)
if len(real) > 20:
    print(f"  ... and {len(real) - 20} more REAL items ({len(real)} TOTAL; "
          f"the list above is TRUNCATED at 20)")
fail = bool(real) or cats.get("unconnected_items", 0) or \
    cats.get("shorting_items", 0)
print(f"coverage: {classified}/{clearance_items} clearance-class items "
      f"classified, {total_items} violation(s) in the report")
print("VERDICT:", "FAIL" if fail else "PASS")
sys.exit(1 if fail else 0)
