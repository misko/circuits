#!/usr/bin/env python3
"""SUPERSEDED (2026-07-19) — NO LONGER IN THE BUILD CHAIN. Kept as the historical
record of the five converter gaps this adapter used to patch; all five are now
FOLDED INTO the converter (skills/kicad-pcb/scripts/circuit_json_to_kicad_sch.py),
so build_from_tsx.sh copies the converter output directly with no transform.
See NOTES.md and ADR-0001 "Backend completion". Do not reintroduce into the chain.

----------------------------------------------------------------------------
Phase-3 integration adapter (the ONE adapter the TSX path needed).

Turns the Phase-2 converter kicad_sch into a BACKEND-READY kicad_sch that the
UNCHANGED cook-loadcell 03_src pipeline (netlist export -> generate_board ->
rules -> KRT import -> stitch -> DRC --schematic-parity) consumes with node-for-
node fidelity to the sealed 04_kicad board.

WHY an adapter is needed — the converter kicad_sch was built for the Phase-2
NETLIST-parity gate (kicad_sch_parity.py compares exported ref/pad/net nodes).
It clears that gate WITHOUT three things the DOWNSTREAM KiCad backend needs:

  1. CANONICAL NET NAMES. tscircuit can't author leading-digit net names, so the
     converter carries `5V`->`N5V`, `3V3`->`N3V3`. generate_board.py's polarity
     asserts (`padnet("Q1","2")=="5V"`), rules/nets.yaml's PWR netclass patterns,
     and the promoted KRT route r2 (routed on 5V/3V3) all key on the canonical
     names; and KiCad's DRC --schematic-parity flags a net_conflict on every
     N5V/N3V3 pin vs a board that uses 5V/3V3. Rename the net labels.
  2. KiCad FOOTPRINT FPIDs. The converter leaves each symbol's Footprint field
     EMPTY (the netlist-parity gate never inspects it). generate_board.py LOADS
     named footprints by FPID and hard-errors on a blank one; DRC parity flags
     footprint_symbol_mismatch on every empty field. Fill each symbol's Footprint
     from the tscircuit footprint TOKEN authored in the .tsx (token -> KiCad FPID,
     the role schwriter2's sym_fp plays; `0603`/`0805` resolve per R/C class).
  3. NO UNMATCHED SYMBOL FIELDS. tscircuit stamps an `MPN` field onto every
     symbol; the KiCad library footprints carry none, so DRC parity flags 20
     footprint_symbol_field_mismatch. Drop MPN (sourcing lives in 02_parts/ +
     bom_seed, exactly as on the sealed board).

Plus: tscircuit's verbose default component Value for a testpoint
(`simple_test_point`) renders as footprint value silk that gets clipped by the
board edge -> silk_edge_clearance. Give TPs a concise silk-safe Value.

Once prepared, `kicad-cli sch export netlist` emits canonical nets + FPIDs
automatically, so NO netlist-level patching is needed and the 03_src backend is
byte-for-byte unchanged.

Usage: prepare_backend_sch.py CONVERTER_SCH TSX_SRC OUT_SCH
"""
import re
import sys

from assign_footprints import token_for, fpid_for

NETMAP = {"N3V3": "3V3", "N5V": "5V", "N5V_A": "5V_A", "N5V_C": "5V_C"}


def main():
    conv, tsx_path, out = sys.argv[1], sys.argv[2], sys.argv[3]
    tok = token_for(open(tsx_path).read())
    lines = open(conv).read().splitlines(keepends=True)

    # 1. canonical net labels (global_label / label)
    renamed = 0
    for a, b in NETMAP.items():
        pat = re.compile(r'((?:global_label|label) ")' + re.escape(a) + r'(")')
        for i, ln in enumerate(lines):
            ln2, k = pat.subn(r'\g<1>' + b + r'\g<2>', ln)
            if k:
                lines[i] = ln2
                renamed += k

    # 2/3/silk: walk symbols; lib_id "elt:SYM_<REF>" carries the refdes
    cur = None
    fp_set = mpn_drop = tp_val = tp_bom = 0
    out_lines = []
    sym_re = re.compile(r'\(symbol \(lib_id "elt:SYM_([A-Za-z0-9]+)"')
    for ln in lines:
        m = sym_re.search(ln)
        if m:
            cur = m.group(1)
            # KiCad TestPoint footprints default to exclude-from-BOM; the
            # converter marks every symbol in_bom=yes, so TP symbol vs footprint
            # BOM attrs differ (footprint_symbol_mismatch). Mark TPs no-BOM to
            # match, exactly as schwriter2's no_bom_syms={"TP"} does.
            if cur.startswith("TP") and "(in_bom yes)" in ln:
                ln = ln.replace("(in_bom yes)", "(in_bom no)")
                tp_bom += 1
        elif ln.lstrip().startswith('(symbol '):
            cur = None                      # GND / power / other symbol: skip
        if cur:
            if '(property "Footprint" ""' in ln:
                ln = ln.replace('"Footprint" ""',
                                f'"Footprint" "{fpid_for(cur, tok[cur])}"')
                fp_set += 1
            elif '(property "MPN"' in ln:
                mpn_drop += 1
                continue                    # drop the MPN field line
            elif cur.startswith("TP") and '(property "Value"' in ln:
                ln = re.sub(r'(\(property "Value" ")[^"]*(")', r'\g<1>TP\g<2>', ln)
                tp_val += 1
        out_lines.append(ln)

    if not (renamed and fp_set):
        sys.exit(f"prepare_backend_sch: expected renames+footprints, got "
                 f"renamed={renamed} fp_set={fp_set} (converter format drift?)")
    open(out, "w").write("".join(out_lines))
    print(f"prepared backend sch: {renamed} net-label renames, {fp_set} footprints "
          f"assigned, {mpn_drop} MPN fields dropped, {tp_val} TP values shortened, "
          f"{tp_bom} TP symbols set no-BOM")


if __name__ == "__main__":
    main()
