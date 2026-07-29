# Handoff — usb-hub-3s-v2 (planned split at the schematic gate)

## 2026-07-22 — handoff (schematic gate → routing)

- did: Drove commission → D-SPEC/E-TOPO → architecture/ADRs → parts → tscircuit
  schematic → ERC/parity/E-INV. All gates GREEN (see 03_schematic.md).
- result: The board is fully specified and schematic-clean. A successor resumes
  from the tree alone.

### STATE (what exists, all committed)
- `01_docs/`: BRIEF (D1-D4, T1-T4), ARCHITECTURE, DETAIL_DESIGN, ADR-0001
  (input protection), 0004-v2 (TPS25740A PD source), 0010 (two-buck), 0011
  (advanced tier); journals 00/03/handoff.
- `02_parts/`: reused ledger parts + NEW `TPS25740ARGER/part.yaml` (full pin map
  + straps + gotchas from SLVSDG8B).
- `03_tscircuit/`: `src/usb_hub_3s_v2.tsx` (112 parts), manifest.yaml,
  parity_padmap.txt, net_aliases.txt; build/ (circuit.json, schematic.pdf),
  kicad/usb_hub_3s_v2.kicad_sch (WIRED converter output), verification/ (ERC,
  parity).
- `03_src/rules/`: power_tree.yaml (E-TOPO green), nets.yaml (fab_tier
  jlc_4layer_advanced, netclasses), electrical_invariants.yaml (15 hold).
- `06_build/netlists/usb_hub_3s_v2.net` (exported for E-INV).

### GATE SCOREBOARD (measured)
| Gate | Result |
|---|---|
| E-TOPO | PASS — 2 BUCK rails, trunk 6.8 A @ 9 V |
| S-COUNT preflight | PASS |
| tsci build | 112 components |
| ERC (converter) | 0 errors / 869 baselined warnings |
| count_parity | 112 == 112 == 112 |
| E-INV | 15/15 hold |
| E-ADR | PASS |

### NEXT STEP — ROUTING WORK ORDER (next session)
The KiCad backend for a NEW board is HAND-WRITTEN and is the bulk of routing
work (tsx_to_board.sh is a REBUILD driver — it needs these to exist first):

1. **`03_src/generate_board.py`** — place the 112 parts from a
   `03_src/floorplan.yaml`. ARCHETYPE: power-hub (check
   `kicad-pcb/references/floorplan-archetypes.md`). Three cells, each
   self-contained (the v2 win — no shared hot loop):
   - Input cell: XT60 → F1 → Q1 → D1/D2 → C1/C2 → VIN fan-out. Q1 copper pour
     (only ~0.32 W now). D1 on VIN (INV-D1-PLACEMENT).
   - Buck A cell + Buck C cell (IDENTICAL layout — copy the placement): LM5116
     + AON6354 pair hard against SW, 10 mΩ shunt Kelvin, 6.8 µH, tight hot loop
     (VIN cap → HS → LS → shunt). D-ADJ: boot cap/FB divider/UVLO divider hard
     against their pins. LM5116 is HTSSOP-20 leaded → escapes at standard.
   - USB-A ×3: TPS2557 + USBLC6 + KH-AF90DIP along the board edge (v1 layout).
   - PD cell: TPS25740A (the ONLY advanced-tier escape — via-in-pad EP, Kelvin
     ISNS per SLVSDG8B Fig 67) + back-to-back Q6/Q7 + Rs + J5 at the edge.
2. **`03_src/rules/generate_rules.py`** — emit netclasses + `.kicad_dru` from
   nets.yaml BEFORE route-prep AND LAST (canon R1). fab_tier
   jlc_4layer_advanced → advanced via/annular floors (0.25/0.15, via-in-pad).
3. **`03_src/route.yaml`** + `route_and_stitch_generic.py` — KRT fanout-first,
   track-free board, import once, promote the final chain to `03_src/route/`.
   Hardest nets first: the two SW nodes + the PD path.
4. **`03_src/stitch_and_fill.py` + `audit_board.py`** — pours (VIN In2 plane,
   GND In1 plane, 5VA/5VC/VBUS islands), thermal vias on the LM5116 EPs +
   TPS25740A EP + Q1/FET pours (R6/R-THERM), refdes on F.SilkS (I8), functional
   silk on J*/F* (P-SILK-FN).
5. **DRC gate:** `kicad-cli pcb drc --severity-all --refill-zones
   --schematic-parity` = 0/0/0. Then the verify stage (twin, pin review, render
   review, red-team, policy_audit) and release.

### OPEN HYPOTHESES / RISKS for the router
- **fab_tier is advanced** ONLY for the TPS25740A. If the user relaxes USB-C to
  5V/3A, delete U1+Q6+Q7+Rs+straps, add 2 CC pull-ups, drop to STANDARD tier
  (ADR-0011, BRIEF T4). Confirm the 5A intent before committing to advanced.
- **TPS25740A is NRND** + stock ~2974 — order-day recheck mandatory (ADR-0004-v2).
- **TPS25740A OVP/UVP window [3.9, 5.8] V is tight** — buck-C transient response
  must stay inside it; a first-power / bring-up check (part.yaml gotcha).
- **First-power ritual:** PD-analyzer read of the advertised PDO list (confirm
  5V/5A, no 9V/12V) — the strap-trap verification (ORDER_README).
- Routing should be MUCH easier than v1: run the grind at the cheap tier.
