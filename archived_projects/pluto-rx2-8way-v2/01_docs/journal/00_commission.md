# journal: commission (stage 0) — pluto-rx2-8way-v2

## 2026-07-30 08:10 — start
- did: created `projects/pluto-rx2-8way-v2/` with the eight numbered stage
  folders; copied all 16 `contracts.md` from the SKILL's OWN canonical set
  (`skills/pcb-design/templates/contracts/`), never from a sibling project;
  seeded `03_src/{floorplan,route}.yaml`, `03_src/rules/{nets,power_tree,
  electrical_invariants}.yaml`, `rebuild_*.sh` and the `01_docs` docs from
  `skills/pcb-design/templates/`.
- result: 16 contracts present. `rules/mates.yaml` deliberately NOT seeded —
  see the D-MATE entry below; an empty one fails `import_provenance_check.py`
  as M-COVER.
- next: re-verify the brief's load-bearing MEASURED claims against v1's own
  artifacts before spending any of them.

## 2026-07-30 08:25 — iterate 1 (brief re-verification, canon "report back")
Every claim the commissioning brief handed me was re-measured against
`projects/pluto-rx2-8way` (read-only). Four confirmed, three corrected.

- did: `pcbnew` walk of `pluto_rx2_8way.kicad_pcb` U_MCU pads + nets; read of
  v1 `03_src/rules/nets.yaml`; parse of v1's own newest DRC json; independent
  Hammerstad-Jensen derivation of the stackup constants (script:
  scratchpad/ustrip.py, reproduced in DETAIL_DESIGN section 1).
- result:
  - **CONFIRMED** — U_MCU (QFN-56, `C2040`) carries **19 named nets** on its
    pads, of which exactly **5** are the board's function (`SEL_V1..SEL_V4`,
    `LED_STAT`) and 14 are the chip keeping itself alive (QSPI x6, XIN/XOUT,
    USB_DM/DP, RUN_N, DVDD_1V1, 3V3, GND). 26 further pads carry
    `unconnected-(...)` auto-nets. This is the whole case for the module and
    it survives contact with the board.
  - **CONFIRMED** — perimeter pitch measures **0.4000 mm** exactly, pad
    **0.8750 x 0.2000 mm**, so the pad half-width in the via-in-pad arithmetic
    is 0.100 mm as the brief states.
  - **CONFIRMED** — `min_via_diameter: 0.25` at `jlc_4layer_advanced`
    (fab_tiers.yaml), so the tier minimum in the arithmetic is right.
  - **CONFIRMED** — `lambda_g/20 = 1.37 mm`. My own HJ derivation at the
    declared stackup (w 0.36, h 0.2104, Dk 4.4, t 0.035) gives eps_eff
    **3.3286**, lambda_g(6 GHz) **27.387 mm**, /20 = **1.3693 mm**. The
    brief's eps_eff 3.328 is right.
  - **CORRECTED** — the brief says v1 "carries 11 unconnected nets". v1's own
    newest DRC (`06_build/drc/drc_2026-07-30.json`) reports **28 unconnected
    items and 88 violations** (70 clearance, 17 track_width, 1
    starved_thermal). 11 is not a number that appears anywhere in that report.
  - **CORRECTED** — the 0.200 mm in "0.175 mm against a 0.200 mm floor" is
    **v1's own declared netclass clearance**, not a fab capability. The
    `jlc_4layer_advanced` fab floor is `min_space: 0.09`, and v1 itself
    already relaxes to 0.14 for its RF launches (`scoped_clearances`). So the
    via-in-pad wall is a POLICY wall at v1's chosen clearance, not an absolute
    arithmetic one. The module's case does not need it — see ADR-0001.
  - **CORRECTED (canon, not the brief)** — `skills/kicad-pcb/references/
    rf-design.md` 4(d) and v1's own `nets.yaml` phase block publish eps_eff
    **3.350** / t_pd 6.105 / lambda_g 27.29 / 13.19 deg-per-mm. My derivation
    reproduces none of them at any w in {0.35, 0.36, 0.37} x t in {0, 0.035}.
    v1 ALSO carries a second, disagreeing set inside the SAME FILE (line 74:
    "lambda_g = 27.41 mm", which implies eps_eff 3.3229). That is the
    rf-design 4(d) one-stackup-one-constant-set defect occurring INSIDE one
    board. Proposed skill patch reported to the caller; `skills/` not edited.
- next: D-SPEC. Two spikes launched concurrently (module sourcing with a live
  JLC stock read; RT6150/PFM + alternative-module regulator topology). Write
  BRIEF.md while they run.
