# Changelog — usb-hub-3s-v3

Board internal name `usb_hub_3s_v2`; project directory `usb-hub-3s-v3`.

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
