#!/usr/bin/env bash
# rebuild_schematic.sh — cooksense SCHEMATIC stage driver (v1.7, canon M3).
#
# `rebuild_all.sh` rebuilds placement+route from a netlist it treats as frozen.
# This is the stage that PRODUCES that netlist, and it exists as a committed
# script because it is NOT just `gen_tscircuit.sh`: this board has to force the
# converter's `--mode grid`, and the reason is a measured cross-net short.
#
# ############################ WHY --mode grid ##############################
# `circuit_json_to_kicad_sch.py` defaults to `--mode layout` (WIRED): it imports
# tscircuit's own schematic wire geometry.  It carries a guard that detects
# cross-net LABEL merges after import and auto-falls-back to `--mode grid`, and
# on 2026-07-28 that guard FIRED on one input (root labels
# ['SHIELD_DRAIN','TH_CAM_A']) and did not fire on another.
#
# MEASURED, 2026-07-28, on this board with the ADR-0020-correction netlist:
#   layout/WIRED  -> "4 segs dropped as cross-net", and the exported netlist has
#                    NO net `AND1` AT ALL.  Its three nodes — R_AND1PD.1,
#                    U_AND1.4 (the AND gate's OUTPUT) and U_AND3.1 — appear
#                    inside `3V3`, which is a 79-node power rail.
#                    THAT IS A HARD SHORT OF A SAFETY-CHAIN INTERMEDIATE TO 3V3:
#                    AND1 = MODE_AUTO_HW . WD_OK . ESTOP_OK, so three of the
#                    seven KEY_RELAY_ALLOWED terms would be permanently TRUE.
#   grid          -> 193 nets, `AND1` = {R_AND1PD.1, U_AND1.4, U_AND3.1},
#                    `3V3` = 76 nodes, every other net node-for-node as authored.
#
# The board has ALWAYS been built from grid mode (the guard fell back to it on
# every prior run), so this is not a change of substance — it is the same output,
# obtained deterministically instead of by luck.  The converter defect is
# REPORTED upstream, not patched here: this agent may not edit `skills/`, and it
# is the same family as commit fd76c6d ("the cross-net guard watched PINS, but
# the merge happens on LABELS").
#
# The HUMAN schematic document is unaffected — it is tscircuit's OWN render
# (build/schematic.pdf, ADR-0002), never the converter's sheet.
# ###########################################################################
#
# Usage:  bash 03_src/cooksense/rebuild_schematic.sh
set -euo pipefail
export PATH="$HOME/.bun/bin:$PATH"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
PROJ="$ROOT/projects/smc0985-cooksense"
S="$ROOT/skills/kicad-pcb/scripts"
T="$PROJ/03_tscircuit"
PY=/usr/bin/python3
cd "$ROOT"

echo "== 1/4 gen_tscircuit (tsx -> circuit.json, human schematic PDF, tsc netlist) =="
bash "$S/gen_tscircuit.sh" "$PROJ" || true      # its own parity leg compares against
                                                # the OLD 04_kicad board and is expected
                                                # to differ until rebuild_all.sh runs

# ############################ WHY --rev IS PASSED #########################
# `circuit_json_to_kicad_sch.py --rev` DEFAULTS TO "dev" (script line 1159), and
# this driver never passed it — so every sheet this board has ever published to
# `04_kicad/` carried `(rev "dev")` in its title block, including the one copied
# into six sealed release archives. A sheet whose own title block says "dev" is
# the one artifact a reader opens FIRST when a board comes back wrong, and it
# disclaims the release it is the source of. MEASURED 2026-07-30 on the v1.7
# candidate: `04_kicad/cooksense.kicad_sch` line 4 read
#   (title_block (title "cooksense") (date "2026-07-29") (rev "dev")
# The fix is HERE, not a hand-edit of 04_kicad/ (canon M3: 04_kicad must be fully
# regenerable from source; a hand-edited title block regenerates back to "dev" on
# the next run and nothing would notice).
# BUMP THIS WITH THE RELEASE. The board silk carries the same token
# (floorplan.yaml `cooksense  SMC0985KS  sidecar v1.7`), so the two must move
# together or a fabricated board and its schematic disagree about what they are.
SCH_REV="v1.7"

echo "== 2/4 converter FORCED to --mode grid (see the header: layout mode shorts AND1 to 3V3), --rev $SCH_REV =="
$PY "$S/circuit_json_to_kicad_sch.py" "$T/build/circuit.json" \
    -o "$T/kicad/cooksense.kicad_sch" --project cooksense --mode grid --rev "$SCH_REV"

echo "== 3/4 ERC + netlist export from the grid sheet =="
kicad-cli sch erc --severity-all -o "$T/verification/erc_converter.rpt" \
    "$T/kicad/cooksense.kicad_sch" >/dev/null 2>&1 || true
ERRS=$(grep -c '; error' "$T/verification/erc_converter.rpt" 2>/dev/null || echo 0)
WARN=$(grep -c '; warning' "$T/verification/erc_converter.rpt" 2>/dev/null || echo 0)
echo "   converter ERC: $ERRS errors, $WARN warnings"
kicad-cli sch export netlist -o "$T/verification/converter_netlist.net" \
    "$T/kicad/cooksense.kicad_sch" >/dev/null 2>&1
mkdir -p "$PROJ/06_build/netlists"
cp "$T/verification/converter_netlist.net" "$PROJ/06_build/netlists/cooksense.net"

echo "== 4/4 SAFETY-CHAIN SANITY: the nets a cross-net merge would eat =="
$PY - "$PROJ/06_build/netlists/cooksense.net" <<'PYCHK'
import re, sys
s = open(sys.argv[1]).read()
nets = re.findall(r'\(net\s+\(code "\d+"\)\s+\(name "([^"]*)"\)(.*?)\n\t\t\)', s, re.S)
d = {n: re.findall(r'\(ref "([^"]+)"\)\s*\(pin "([^"]+)"\)', b) for n, b in nets}
# every AND-chain intermediate and permission, with the node count it MUST have
EXPECT = {
    "AND1": 3, "AND2": 3, "KEY_RELAY_ALLOWED": 3, "CTR_SAFE": 3,
    "FAULT_SET_N": 3, "FAULT_LATCH_CLEAR": 5, "WD_OK": 10, "WD_OK_EXP": 2,
    "EF_OVLO": 3, "COIL_EN": 2, "COIL_EN_IN": 4,
    # v1.8 (ADR-0024, amended by ADR-0025). The ONE surviving field-fed safety
    # input is SPLIT at a series element, and the split is the fix — so the node
    # counts are what pins it. ESTOP_RAW_IN = {J_ESTOP.3, R_ESTOPPD.1, R_ESTOPS.1,
    # D_ESTOP.1}: four nodes. ESTOP_RAW = {R_ESTOPS.2, U_SCHM.1}: exactly two, i.e.
    # the logic node is reachable from the field ONLY through a resistor. If a
    # future edit re-merges them this fails before any gate that grades geometry.
    # DOOR_RAW_IN / DOOR_RAW are GONE — ADR-0025 deleted the door channel from the
    # netlist. Their absence is asserted NEGATIVELY below, because a check that
    # only counts nodes on nets it expects cannot notice a net that should not
    # exist at all.
    "ESTOP_RAW_IN": 4, "ESTOP_RAW": 2,
    # ADR-0025: the PRESS one-shot's reset is now OS_CLR_N = ESTOP_OK . STOP_REQ_N.
    # ESTOP_OK gains U_OSCLR.1 and so carries EIGHT nodes: U_SCHM.4 (driver),
    # U_AND1.6, U_FAULTAND.3, U_CAND1.3, U_OSCLR.1, R_ESTOPOKPD.1, R_ESTOPOKSER.1,
    # TP_ESTOP.1. If the count drops to 7 the new term silently left the circuit.
    "ESTOP_OK": 8, "OS_CLR_N": 2,
    # ADR-0025: the freed MCP23017 GPB3 is pulled DOWN through 10k, never open and
    # never hard-tied. Two nodes: R_GPB3PD.2 + U_EXP.4.
    "GPB3_SPARE": 2,
    # 5V_RPP gains C_EFIN, the eFuse input capacitor that did not exist for five
    # releases (SLVSE57C sec.10 Fig.67): Q_REV.2 + U_EFUSE.3 + U_EFUSE.4 + R_OVT.1
    # + C_EFIN.1.
    "5V_RPP": 5,
}
# ADR-0025: nets that MUST NOT EXIST. A node-count table is blind to a net that
# should have been deleted, and "the door channel is gone" is the whole change.
FORBIDDEN = ["DOOR_RAW_IN", "DOOR_RAW", "DOOR_NI", "DOOR_OK", "DOOR_OK_EXP"]
bad = []
for k in FORBIDDEN:
    if k in d:
        bad.append(f"{k}: STILL EXISTS ({len(d[k])} nodes) — ADR-0025 deletes the door channel")
for k, n in EXPECT.items():
    got = d.get(k)
    if got is None:
        bad.append(f"{k}: MISSING (merged into another net?)")
    elif len(got) != n:
        bad.append(f"{k}: {len(got)} nodes, expected {n} -> {sorted(got)}")
print(f"   {len(nets)} nets; spot-check {len(EXPECT)+len(FORBIDDEN)-len(bad)}/{len(EXPECT)+len(FORBIDDEN)} ({len(EXPECT)} node-counts + {len(FORBIDDEN)} must-not-exist)")
for b in bad:
    print("   FAIL " + b)
sys.exit(1 if bad else 0)
PYCHK
# ############################ CANON M3 GAP, FIXED #########################
# This script produced `03_tscircuit/kicad/cooksense.kicad_sch` and the netlist
# and STOPPED. `04_kicad/cooksense.kicad_sch` — the sheet `kicad-cli pcb drc
# --schematic-parity` actually compares the board against — was never written
# by any script; it had been copied by hand in some earlier session and then
# went STALE. MEASURED 2026-07-28: after the -12L -> -13L part change the board
# was correct and the 04_kicad sheet still said
# `cooksense:Relay_StandexDIP_1A_pinout12`, so parity read **37 issues** — 24 of
# them the twelve relays disagreeing about their own footprint and value, and
# every one of them an artefact of a stale COPY rather than a real disagreement.
# A hand-copied file in `04_kicad/` is exactly the thing canon M3 forbids: the
# directory must be fully regenerable from `03_src/` + `03_tscircuit/`.
echo "== 5/5 publish the sheet to 04_kicad (canon M3 — parity grades THIS file) =="
cp "$T/kicad/cooksense.kicad_sch" "$PROJ/04_kicad/cooksense.kicad_sch"
echo "   $PROJ/04_kicad/cooksense.kicad_sch <- $T/kicad/cooksense.kicad_sch"

echo "== DONE: $PROJ/06_build/netlists/cooksense.net =="
echo "   next: bash 03_src/cooksense/rebuild_all.sh --reroute"
