# Changelog — usb-hub-3s-v3

Board internal name `usb_hub_3s_v2`; project directory `usb-hub-3s-v3`.

## v1.5 — 2026-07-25

Released: `07_releases/v1.5-2026-07-25/`. **CPL-CORRECTION supersede of
v1.4-2026-07-23** (v1.4 gains `SUPERSEDED.md`, otherwise immutable).
**v1.4 and every earlier release are DO-NOT-ORDER. Order from v1.5.**

**Why: a P0 in the CPL, not in the copper.** Sealed v1.4 places **C1 and C2 —
100 uF / 35 V POLARIZED polymer electrolytics — at CPL 270.0 where the measured
correct value is 90.0**: 180 degrees reversed, directly across the 9.0-12.6 V 3S
LiPo input behind a 10 A fuse. A reverse-biased polymer electrolytic on a
near-zero-impedance pack heats, gasses and **vents**, at first power-up, before
any bench gate can run. Found by a pre-order PCBA audit
(`08_reviews/2026-07-25_v1.4_pcba-audit_assembly.md`, 15 findings, dispositions
PCBA-1..15) — the earlier reviews had audited the board, not what the machine
would build.

- **fab/cpl.csv — EXACTLY FOUR changed cells, and nothing else:**
  `C1 270.0->90.0`, `C2 270.0->90.0`, `Q7 270.0->180.0`, `J1 90.0->0.0`.
  108 placements both sides, 0 rows added or removed.
  - **C1/C2** (PCBA-1, P0): no per-LCSC rotation row existed for C2982822, so the
    exporter fell through to the footprint-NAME DB, which a per-part fact cannot
    live in. Polarity re-verified independently of the pad fit: JLC's own library
    silk draws a crossed **"+" over its pad 1** and a bar **"-" over pad 2**, and
    our pad 1 is on VIN.
  - **J1** (PCBA-2, P1): the name-DB pattern `^AMASS_XT60PW-M` is START-ANCHORED
    and this board uses a vendored `XT60PW-M_EdgeTrim`, so **no rule fired at
    all** and the offset silently defaulted to 0. Four-pad fit (2 blades + 2
    anchors) gives rms **0.0000 mm @270**, 12.0 mm out at 90.
  - **Q7** (PCBA-3, P1): `^SOT-23` = -90 is wrong for C78284. 3-pad asymmetric
    fit, rms 0.062 mm @180 vs 1.95 mm @270. Would have left Q6 un-gated — a dead
    or silently unprotected Pi rail.
  - Root cause behind all three, fixed at source before this release: a
    **handedness bug in `jlc_twin.xform()`** that NEGATED every rotation offset
    the tool ever reported (repo `e0d735c`, `9078ad9`, `95a8180`, `1b69760`).
- **NO COPPER CHANGE.** Gerbers, both drill files, `source/`, `3d/` and `pdf/`
  are **sha256-IDENTICAL to v1.4** — 20 files. Proven by RE-EXPORT from the
  unchanged board: 13/13 zip members identical once the plot's own timestamp
  comments are stripped (`verification/cpl_acceptance_gate.md`).
- **fab/bom.csv**: identical to v1.4 row-for-row except the **MPN column is now
  populated on all 43 lines** (was 0/43). Cross-checked against the
  independently datasheet-authored `02_parts/` directory names: **26/26 hard-part
  MPNs matched, 0 directories unaccounted for** (PCBA-10).
- **NEW `03_src/rules/assembly.yaml`** (PCBA-5) — the population set finally has a
  machine-readable home: `service` (incl. **THROUGH-HOLE assembly**, 4 refdes /
  22 plated holes, J1-J4), `sides: [top]` (measured 108/108), `fiducials: none`
  (deliberate: the smallest centre-to-centre distance between two distinct
  pads is a measured **0.500 mm** at J5, > 0.4 mm),
  `build_quantity: 5`, and F1/SW1 as the only `not_assembled` refdes with dated
  evidence. The MANIFEST `not_assembled:` line is GENERATED from it.
- **NEW `01_docs/DETAIL_DESIGN.md`** (PCBA-7) — it did not exist, although three
  sealed `part.yaml` files have cited sec.1/2/5 as authority since 2026-07-21.
  Derivations from the datasheets directly (LM5116 SNVS499I eq. 7-24; USBLC6-2
  Doc ID 11265 Rev 5). The sec.5 citation was wrong three ways and is corrected.
- **ORDER-PREVIEW HUMAN GATE** in ORDER_README (PCBA-8). v1.4 mentioned the JLC
  preview **zero times** while **12** twin findings are waived on exactly that
  gate — **C1/C2 among them**. P1-P7 now say what to look for and what rejects.
- **U12 over-voltage: ACCEPTED + MEASURED** (user decision; MANIFEST waiver
  **W-U12**). 5.352 V nominal / 5.479 V worst corner vs the 5.25 V at which ST
  characterizes leakage — but ST's absolute-ratings table carries **no V_BUS
  limit** and V_BR is **6.0 V minimum**, cleared by 521 mV. R12 deliberately NOT
  changed. Bench gate Q1 now RECORDS measured VBUSC/VBUSA.
- **Stock, at build_quantity 5:** PASS, 43/43 lines OK, 0 uncoded. Split **12
  Basic / 31 Extended** (~31 feeder setups, priced before the order). Tightest
  ceilings: C473910 = **37 boards**, C5337088 = 90, C408523 = 225. Table rebuilt
  sorted by tightness with a named alternate per row (PCBA-13/14).
- **Panel-rail policy, measured:** three of the four edges cannot take a rail —
  J1 (-6.82 mm), J2-J4 (-4.29 mm) and J5 (-2.90 mm) physically OVERHANG the
  outline. Only the edge opposite the USB-C connector is usable (+1.43 mm).
- **TWO fresh review lenses, both ORDER**, both archived in `verification/`:
  a zero-context lens over the STAGED release (0 P0 / 3 P1 / 9 P2 — it
  re-derived the four CPL cells five ways and got **107/107 parts agreeing with
  the shipped CPL to <1°**, and it found real defects in this release's own
  paperwork, all fixed), and the **FIRST layout/thermal/power-integrity lens
  ever run against THIS copper** (0 P0 / 5 P1 / 7 P2). The prior layout lens was
  written against the **v1.0** board; 10 footprints were added afterwards
  (C53, C54, D5, F2, Q6, Q7, R30, R34, R35, SW1; tracks 642→1061), so the whole
  discrete VBUS protection chain had never been layout-reviewed — v1.3 and v1.4
  both sealed carrying that claim.
- **Build note that changes what you do (RL-3):** H3's mounting hole has **5VA
  and GND copper both starting at r = 1.80 mm, on BOTH outer layers**. A metal
  M3 screw head bridges the 6 A USB-A rail to GND through solder mask alone.
  **Fit a nylon screw, or leave H3 unfitted.** ORDER_README section 3a, B1.
- **The Pi-rail margin is thinner than any previous release said.** The board
  copper on the 5 A path was a **~3 mΩ estimate** carried since v1.3; the layout
  lens MEASURED it at **≥9.32 mΩ** (mesh solve; true ≈10.4-11.6). Three figures
  have now been published for this one margin — **157 mV → 69 mV → 15 mV** —
  each step removing an optimistic assumption without the hardware changing.
  `power_tree.yaml` synced (`vout_min` 5.27→5.227, `vout_max` 5.43→5.479,
  `ir_budget_mohm` 88→97); E-MARGIN re-run **PASS**. 15 mV of paper slack is not
  a margin to ship on — bench gates Q2/Q5 measure the delivered voltage.
- **The archive is self-contained for the first time (PCBA-16).** `source/
  fp-lib-table` pointed at `${KIPRJMOD}/../03_src/lib/` — OUT of the release —
  so a standalone re-measure of v1.3/v1.4 raises **6 `lib_footprint_issues`**
  despite the vendored `.pretty` folders being shipped, and their MANIFESTs
  claim the path they do not have. v1.5 points it at the vendored copies:
  standalone `kicad-cli pcb drc` from inside the archive now reads **0
  violations / 0 unconnected**. Cost: `fp-lib-table` is the ONE payload file not
  byte-identical to v1.4 (19, not 20) — a library-path line, not copper.

## v1.4 — 2026-07-23

Released: `07_releases/v1.4-2026-07-23/`. **DOCS-ONLY supersede of
v1.3-2026-07-23** (v1.3 gains `SUPERSEDED.md`, otherwise immutable — the one
allowed addition). **Board, BOM, CPL, gerbers, source and PDFs are
byte-identical to v1.3** (22/22 files sha256-verified; the freshness gate's
9 identical-artifact findings are the release's declared purpose, waived with
evidence in `verification/freshness_waiver.md`). v1.3's electrical state and
verification battery stand unchanged. **Order from v1.4.**

Driven by a post-seal user-supplied external review
(`08_reviews/2026-07-23_v1.3_external-user_full.md`, dispositions EXT13-1..8):

- **SW1 fallback-header shunt polarity was REVERSED in the v1.3 README.**
  The tsx wires SW1 pin1=T1→GND, pin2=COM→ENKILL; grounding ENKILL shuts both
  bucks down and opens Q6. Correct: **COM-T1 shunted = OFF; shunt removed =
  ON.**
- **F1 was misdescribed as "KH-AF90DIP-112"** (the USB-A connector family).
  F1 = **Keystone 3568 MINI-blade fuse holder, C5249699** (BOM row 38).
- **Tolerance-inclusive worst-case rail table** replaces the Vref-only
  numbers: R13/R4 = C5126242 = FRC0603F1211TS **±1 %** (ledger row 150) was
  omitted. 5VC static range **5.227-5.479 V** (was 5.272-5.432); low-corner
  headroom **597 mV vs the 440 mV IR budget — E-MARGIN still PASS** (157 mV
  slack); 5VA top corner 5.273 V slightly above the 5.25 V USB-A intent
  (accepted, no-data charge ports; 0.1 % R13/R4 recorded as next-rev option).
- **Packaging note:** F1 (C5249699) + SW1 (C2939728) are on `fab/bom.csv` but
  intentionally off `fab/cpl.csv` (hand-solder) — JLC upload shows 2 unmatched
  designators; README instructs marking both DNP + a hand-fit purchasing list
  (incl. the off-BOM 10 A MINI blade fuse element).
- **Bench qualification TIGHTENED** (Q0-Q7, adopted from the review): R12 AND
  R30 ohmmeter pre-power; no-load rails with a **5.45 V firm ceiling**;
  VBUSC@5A ≥5.00 V at the board; 5 A→0 A load-release overshoot capture;
  cable-end hot ≥4.80-4.85 V; SW1/header continuity logic; `vcgencmd
  get_throttled` through the Pi stress test. OV posture (Option 2) carried
  VERBATIM.

Verification scoping (canon): docs-only fix-pass — targeted source-evidence
confirmations (`verification/2026-07-23_v1.4_docfix_confirmation.md`), M-BOM
re-run PASS, policy_audit re-run 0 FAIL; no fresh review lens (no new
electrical state).

## v1.3 — 2026-07-23

Released: `07_releases/v1.3-2026-07-23/`. **Supersedes v1.2-2026-07-23**
(v1.2 was found **DO-NOT-ORDER** by an external human review after seal; it gains
`SUPERSEDED.md`, otherwise immutable). v1.3 is the FIX PASS for the confirmed
blockers — a BOM + docs + artifact-regen revision; the netlist topology and
routing are unchanged (same promoted KRT chain).

**R12 catalog-verified (THE order blocker).** v1.2's BOM resolved R12 to
**C2933210 = 3.74 kΩ** (tscircuit value-resolution; the tsx left R12 uncoded),
driving the buck-C setpoint to ~4.97 V undervoltage. v1.3 bakes the LIVE-catalog-
verified **C2984354** (AR03BTCX4121, Viking **4.12 kΩ ±0.1 % ±25 ppm** 0603,
stock 15 353 on 2026-07-23) into the tsx (`fbtopMpn`); verified alternate
C861436 (Yageo RT0603BRD074K12L). The buck-C setpoint is RE-DERIVED against the
ACTUAL Q6+F2 delivery path (Q6 AON6403 ~4.3 mΩ + F2 SMD2920-700 R1max 18 mΩ
catalog-verified — NOT the removed eFuse 34-48 mΩ model): 5VC 5.352 V nom /
5.27 V worst-case; **E-MARGIN PASS** (640 mV headroom vs 528 mV need at
ir_budget 88 mΩ).

**D5 directionality fixed.** v1.2's C140903 is listed **BIDIRECTIONAL** by the
JLC catalog (LRC SMB-FL) — the design's uni-directional cathode-on-VBUSC
assumption was unverifiable against it. v1.3 uses **C113976** (SMBJ6.0A
**UNIDIRECTIONAL** DO-214AA/SMB, catalog-verified, stock 74 758).

**R30 catalog-verified (2nd wrong-part, caught by the semantic M-BOM gate).**
v1.2's BOM resolved R30 (Q6 gate pull-up, QG→PMID) to **C2933195 =
FRC0603F3091TS = 3.09 kΩ** while labeled 100 kΩ (v1.2 SUPERSEDED addendum,
`688a8af`) — functional but burning ~1.7 mA through Q7 whenever the port FET was
ON. v1.3 bakes **C25803** (UNI-ROYAL 0603WAF1003T5E, **100 kΩ ±1 %** 0603, JLC
Basic, ledger-verified; MPN E96 decode `1003` = 100×10³) — the same code the
board's other 100 k 0603s (R1/R8/R17) resolve to, so the BOM row merges (43
grouped lines). Q6 margins re-derived at 100 k from the AON6403 STATIC table:
OFF/back-feed |Vgs| ≈ 60 mV (Q7 Idss 0.5 µA + Q6 IGSS 0.1 µA × 100 k), 20×
below |Vgs(th)|min 1.2 V → blocks; ON Vgs = −5.35 V (fully enhanced); pull-up
waste 54 µA vs ~1.7 mA at 3.09 k.

**OV honesty (BRIEF A3/D3, Option 2 — user decision).** The discrete Q6/Q7/F2/D5
chain is kept as **SECONDARY** protection; no active OVP added. Docs now state
plainly: protected against shorts / overload / reverse-feed-off; **NOT guaranteed
against a buck high-side short** (D5+F2 = best-effort crowbar). Context:
supervised prototype, replaceable Pi. Escalation boundary (verbatim): "add active
OVP if the system becomes unattended, hard-access, carries valuable storage, or
powers expensive SDR".

**Assembly:** SW1 (SS12D07) moved **off automated assembly** (hand-solder;
VG4-vs-VG6 pitch unconfirmed; header+shunt fallback documented). F1 holder's CPL
status corrected to match its documented hand-solder plan (was erroneously
machine-placed in v1.1/v1.2 CPLs). CPL 108 placements.

**ORDER_README:** bench-qualification plan baked as a REQUIRED pre-Pi-connection
deployment gate (Q1-Q5: assembled-R12 measurement, 8-24 h electronic-load soak,
switch-node scoping at 12.6 V, thermal soak, end-of-cable VBUSC verification).

All release artifacts regenerated fresh from v1.3 source and sha256-distinct from
v1.2 (the v1.2 stale-artifact defect class is machine-checked by
`release_freshness_check.py` this release).

## v1.2 — 2026-07-23

Released: `07_releases/v1.2-2026-07-23/`. **Supersedes v1.1-2026-07-23**
(v1.1 gains `SUPERSEDED.md`, otherwise immutable).

**Discrete VBUS protection — the eFuse is DROPPED (ADR-0002; BRIEF A2/D2 user
decision).** The v1.1 TPS26631 eFuse was over-built for a 5 V/5 A Pi rail and was
the root cause of BOTH the board routing wall (its 20-pin HTSSOP IN_SYS pin boxed
in a fine-pitch escape) AND v1.1's two electrical order-blockers. −9 parts / +1 =
**110 total**. New USB-C protection chain: `5VC → Q6 (AON6403 P-FET,
ENKILL-gated reverse-block via Q7 BSS138) → F2 (PPTC polyfuse 2920, 7 A/16 V) →
VBUSC → J5`, with **D5 (SMBJ6.0A TVS)** over-voltage clamp. buck-C FB stays on
**LOCAL 5VC** (R12 4.12k → 5.352 V; the v1.1 runaway fix). buck-C EN re-merged to
ENKILL. Removed: U13, R31/R32, R33/R36, C51/C52, D6, D7.

Gates at seal (git_sha in `MANIFEST.txt`, `git_dirty: false`):
- DRC **0/0/0** (severity-all, refill-zones, schematic-parity); source/ standalone
  re-measure **0/0** (V-REL-FPLIB).
- ERC 0; parity **110 ×5 sources**; E-INV **24/24**; E-ADR/E-TOPO/E-MARGIN/E-OFF PASS.
- policy_audit **0 FAIL** (PASS=27, WAIVED=2: R-THERM + R-POUR); M-BOM (BOM==source) PASS.
- jlc_twin **GREEN** — F2 (C6165170), D5 (C140903), Q6 (C2760089/AON6403) fetched +
  fit; all PAD-GEOM/PAD-MISMATCH/POLARITY-CHECK adjudicated.
- Fresh zero-context red-team: **ORDER** (architecture approved, no design P0; Q6
  5 A / 0.11 W OK, reverse-block correct). Report in `verification/`.
- 2 Extended-tier parts (F2, D5) carry a MANDATORY order-day `jlc_stock` recheck
  (ORDER_README); first-power OV caution documented (ADR-0002 tradeoff).

## v1.1 — 2026-07-23

Released: `07_releases/v1.1-2026-07-23/`. **Supersedes v1.0-2026-07-22**
(review-driven revision; v1.0 gains `SUPERSEDED.md`, otherwise immutable).

Protected-VBUS revision. +15 parts (115 total). Adds a **TPS26631 eFuse** (U13)
with a **two-FET reverse-current block** (Q6 AON6354 + Q7 BSS138) on the USB-C
rail — **5.83 A current-limit, 5.91 V input-OV cutoff, soft-start, auto-retry**;
moves the USB-C setpoint to **5.151 V sensed at the connector** (buck-C FB → VBUSC,
resolving the Blocker-2 4.97 V finding); adds a **master-off slide switch (SW1)**
on the merged EN bus; raises buck caps to **50 V input / 10 V output** (RT-T2/T5);
adds optional (DNP) SW-node snubbers; relabels silk/docs to the honest framing
(Pi-dedicated 5 A, NOT USB-PD; power-distribution board, not a USB hub).

Gates at seal (git_sha in `MANIFEST.txt`, `git_dirty: false`):
- DRC **0/0/0** (severity-all, refill-zones, schematic-parity); source/ standalone
  re-measures **0/0/0** (V-REL-FPLIB, with vendored `usb_hub_3s.pretty` +
  `Button_Switch_THT.pretty`).
- policy_audit **0 FAIL** (PASS=27, WAIVED=2 [R-THERM + R-POUR ev-backed], HUMAN=6,
  N-A=2). **E-INV 16/16, E-ADR, E-TOPO, E-MARGIN, E-OFF PASS**; P-LAYOUT/P-ADJ PASS.
- JLC twin **exit 0** (88 OK / 232 checked; U13 fit 0.01 mm, Q7 0.08 mm; Q6 reuses
  the AON6354 merged-drain adjudication; SW1 new — pitch confirm at order).
- Pin review PASS, render review PASS. Fix-confirmation review resolves each
  external-review finding (`08_reviews/2026-07-23_v1.1_fix_confirmation.md`).

Carried decisions / open items (none blocks the order):
- **SW1 (SS12D07VG6) footprint pitch = MANDATORY JLC order-preview confirm** — our
  2.5 mm (standard SS-12D07) vs JLC's mislabeled-VG4 model 2.0 mm; jumper fallback.
- **Snubbers R34/R35/C53/C54 = DNP-by-design** (bench-tune footprints; removed from
  fab BOM/CPL, pads remain in gerbers). Encoding `doNotPopulate` in the tsx is a
  next-rev item.
- Bench: loop-stability Bode with the eFuse in-loop; OVP no-false-trip at 5 A.
- **RT-T3** (LM5116 UVLO ~9.65 V cold-start > 9.0 V nominal) accepted as documented
  P2 (LiPo deep-discharge protective) — unchanged from v1.0.

## v1.0 — 2026-07-22

Released: `07_releases/v1.0-2026-07-22/`

First orderable release. 3S-LiPo powered 3-port USB hub (3× USB-A 5 V + 1×
Pi-dedicated USB-C 5 V/5 A), 4-layer, 130.1 × 92.1 mm, XT60 input →
10 A MINI-blade fuse → dual synchronous LM5116 bucks.

Gates at seal (git_sha in `MANIFEST.txt`, `git_dirty: false`):
- DRC 0/0/0 (severity-all, refill-zones, schematic-parity); source/ re-measures
  0/0/0 standalone (V-REL-FPLIB).
- policy_audit 0 FAIL (PASS=19, WAIVED=1 R-THERM evidence-backed, HUMAN=6, N-A=9).
- E-INV / E-ADR / E-TOPO PASS; P-LAYOUT / P-ADJ PASS.
- JLC digital twin exit 0 (80 OK / 209 checked; all criticals adjudicated).
- Pin review PASS, render review PASS.
- Red-team **topology: ORDER** — the original memo's DO-NOT-ORDER was a pre-fix
  snapshot driven solely by P1 RT-T1 (fuse 20 A→10 A, fixed `071fe56`); an
  independent zero-context re-review returned ORDER and re-confirmed the 10 A
  sizing (`verification/…_topology_rereview.md`, `verification/RT-T1_regate_note.md`).
- Red-team **layout: ORDER**, zero P0/P1.

Key decisions carried in this release:
- USB-C port is Pi-dedicated; needs `PSU_MAX_CURRENT=5000` on the Pi 5 EEPROM
  for 5 A (ADR-0001).
- F1 10 A MINI blade element is hand-fit (off-CPL); the Keystone-3568 holder
  (C5249699) is JLC-placed.
- F-2.1 (LM5116 UVLO ≈ 9.65 V cold-start > 9.0 V nominal) accepted as a
  documented P2 per user decision (doubles as LiPo deep-discharge protection).
- P2 next-rev work order (RT-T2/T4/T5, AON6354 doc hygiene, LM5116 EP via-arrays
  + VBAT_F B.Cu pour) recorded in `ORDER_README.md`; none blocks this order.
