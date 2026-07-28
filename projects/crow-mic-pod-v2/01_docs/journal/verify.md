# verify journal — crow-mic-pod-v2

## 2026-07-23 (fix pass) — finish (machine gates)
- did: re-ran all machine verify gates on the fixed board.
- result: ERC 0 / count_parity 35/35 (circuit.json==kicad_sch==netlist==manifest);
  DRC **0/0/0** (--severity-all --refill-zones --schematic-parity, reproducible);
  audit_board OK (8 polarity+mate/keepout); policy_audit **0 FAIL** / 23 PASS /
  1 WAIVED (S-OCCL, evidence-backed converter-machine-artifact) / 7 HUMAN / 7 N-A;
  contracts_audit 0/153; bom_source_check (M-BOM) **PASS**; jlc_twin exit 0,
  24 OK / 60 checked, 0 unadjudicated criticals (D3 NOW twin-verified fit=0.19mm;
  J1/MK1 evidence-backed NO-CAD). BOM: MK1 LCSC blanked (hand-solder), D3 in
  BOM+CPL. J1.7/8 zone_connect=FULL confirmed on board.
- open (order-day): enclosure panel-cutout vs 1.05mm RJ45 mouth overhang (finding
  H, mechanical dependency — no enclosure CAD in repo); PoE-injection deployment
  constraint (A1/ADR-0005); J1 pad-1→contact-1 continuity backstop (defense-in-
  depth, footprint already certified correct); stock re-check.
- next: fresh 4-lens red-team → if no NEW P0, seal v1.0.

## 2026-07-28 10:14 — start (v1.4 CAL-1 fix, commissioned as a BOM-only supersede)
- did: opened the commission "seal a v1.4 BOM-only supersede of v1.3 fixing CAL-1
  with R4=33k/R5=18k", with two binding pre-conditions: RE-DERIVE CAL-1 rather
  than accept it, and establish FIRST whether the change is genuinely BOM-only.
  Read CLAUDE.md, SKILL.md stage 7, the 07_releases contract's 2-commit seal
  ritual, jlcpcb-fab SKILL, the CHANGELOG, `git show f8427c5` (the audit),
  08_reviews/ and the contracts. Opened v1.3 READ-ONLY.
- result: sealed v1.3 board md5 `c7b8512ccf0810997116c8c2e59dcad9` == 04_kicad's,
  sha256 `2f936fd8…` == its MANIFEST line; 62 files in the release dir. R4/R5
  confirmed PLACED, both `R_0603_1608Metric`, F.Cu, attr 0x2, at (57.3,34.2) and
  (54.0,35.0) — so the "same package, already placed" half of the premise holds.
- next: re-derive CAL-1 from the datasheets and the .tsx; then test the BOM-only
  premise by experiment before writing anything.

## 2026-07-28 10:32 — stuck (v1.4 NOT sealed — both pre-conditions fired)
- did: re-derived CAL-1 end-to-end with no code shared with the audit (pcbnew on
  a COPY of the sealed board; SBOS855E re-read with pdftotext; transfer function
  re-derived from the .tsx), then ran a two-export experiment to test whether a
  value change is BOM-only.
- result (1) — THE DEFECT REPRODUCES, THE FIX'S MARGIN DOES NOT.
  Stimulus 100 dB @10cm at |LS1-MK1| = **45.61798 mm** -> **106.817 dB SPL**.
  Load correction [3.9/6.1]/[2.2/4.4] = **+2.135 dB** -> S = **80.68 mV/Pa**.
  v1.3 ceiling **106.81 / 103.81 / 101.31 dB** (nominal / +3dB / +3dB at 4.75V)
  — every audit figure reproduces to the second decimal. But the audit's fix
  claim ("+3.4 dB worst-case") recovers an implied op-amp output headroom of
  **exactly 0.1000 V** in both of its published numbers, while its own ceiling
  claim ("binds 2.3x") recovers **0.800 V** — the datasheet's guaranteed
  `VO = (V-)+0.8 .. (V+)-0.8` at RL=2k. Under 0.800 V, R4=33k/R5=18k reaches
  **105.17 dB worst-case = -1.65 dB, STILL CLIPPING**; under 0.200 V, +2.88 dB;
  under 0.100 V, +3.45 dB. Under the guaranteed limit NO divider clears by more
  than +0.86 dB and the optimum sits at VMID ~2.07 V — the OPPOSITE direction
  from the proposed change. The fix is a strict improvement under every model
  (+2.2..+4.2 dB) and proven sufficient under none.
- result (2) — IT IS NOT BOM-ONLY, MEASURED. `export_jlc_package.py:349` reads
  `val = fp.GetValue()` FROM THE BOARD and feeds it to the BOM Comment AND the
  CPL `Val` column; the schematic carries the same value. Two exports differing
  only in 2 `(property "Value" ...)` strings (a 4-line .kicad_pcb diff):
  gerbers+drills **11/11 byte-identical** (copper truly unmoved — and the sealed
  v1.3 zip re-plots **11/11** from its own source, validating the method), but
  `fab/cpl.csv` moves 2 `Val` cells, `fab/bom.csv` loses a row and gains one,
  `.kicad_pcb` md5 moves `c7b8512c` -> `2e0c98bd`, and DRC
  `--severity-all --refill-zones --schematic-parity` returns **2
  footprint_symbol_mismatch** against the sealed schematic (base run: **0/0/0**,
  an independent re-confirmation of v1.3's gate). All three supersede modes in
  the 07_releases contract FAIL this shape; the commissioned copper-identity
  proof (md5 unchanged + CPL byte-identical) is unsatisfiable without
  hand-editing the CSV, which canon M3 forbids.
- hypothesis carried upstream: the commission's premise ("no copper => BOM only")
  is false on this pipeline because VALUE is a BOARD property here. The decision
  — which value pair, and whether to spend a source revision — returns to the
  user. NOTHING was written to 07_releases/ or 04_kicad/; v1.3 has no
  SUPERSEDED.md and stays live.
- landed instead: `08_reviews/2026-07-28_v1.3_fix-verification_cal1.md` (the full
  re-derivation, the refutation, the experiment, and what a v1.4 would cost);
  DISPOSITIONS rows for the whole 2026-07-27 audit, which had NONE — CAL-1,
  FIX-1, FIX-2, and POE-1/PSR-1/DC-1/MECH-1 carried forward explicitly OPEN;
  and a correction to `02_parts/OPA1678IDR/part.yaml`, whose ceiling numbers were
  2.14 dB optimistic and whose "output still fits" was asserted, not measured.
- next: user decision. Parts side is already clean and dated: 33k = **C4216**
  (JLC Basic, 747 998), 18k = **C25810** (JLC Basic, 1 357 175), both the same
  Uni-Royal 0603 series as the 22k they replace (live query 2026-07-28).

## 2026-07-28 12:10 — iterate (CAL-1 closed from the OTHER board; nothing here moved)
- did: recorded, on this board, the resolution of CAL-1 by a system-level drive
  reduction at the sibling `crow-recorder-central-v2`. Read-only pass over this
  board's copper: `07_releases/` and `04_kicad/` opened read-only, `03_src/` and
  `03_tscircuit/` untouched.
- result: CAL-1 re-derived here once more before depending on it — pcbnew on a
  COPY of the SEALED v1.3 board (sha256 2f936fd8...): LS1 (33.000, 46.000),
  MK1 (74.000, 26.000), |d| = 45.61798 mm -> burst 106.8173 dB SPL; worst-case
  U1 input-common-mode ceiling 101.3144 dB; SHORTFALL 5.5028 dB. Fixed AT
  CENTRAL by duty 1/6 (-6.0206 dB) -> 100.7967 dB, clearing by 0.5178 dB.
  This board: NO copper, NO BOM, NO netlist, NO release change. v1.3 carries no
  SUPERSEDED.md and remains the live release. The 33k/18k pair of FIX-1 was NOT
  applied — the divider stays 22k/22k.
  Landed here: the binding constraint in `01_docs/ARCHITECTURE.md` (Calibration
  transducer), three gotchas on `02_parts/CMT-8504-100-SMT-TR/part.yaml` (the
  cap, the absent SPL-vs-drive curve, and the unspecified coil inductance), and
  the DISPOSITIONS row moving CAL-1 OPEN -> resolved with its fix location.
  POE-1, PSR-1, DC-1, MECH-1 re-stated individually as still OPEN; PSR-1
  explicitly NOT resolved — the drive change is on the galvanically separate
  beep domain and its dominant path is the 16 Hz R1*C1 corner, -11.4 dB at
  60 Hz, untouched.
- next: this board is unchanged and still orderable. The residual on CAL-1 is
  the user's: -6 dB clears a MINIMUM-output LS1 by 0.52 dB but leaves a
  TYPICAL-output one (ds curve ~104 dB @10cm) 3.48 dB over the ceiling.
