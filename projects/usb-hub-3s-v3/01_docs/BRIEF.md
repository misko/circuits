# brief: usb-hub-3s-v3

status: active
current_release: 07_releases/v1.5-2026-07-25

## Original prompt / decision

<!-- prompt-verbatim-begin -->
> v3 supersedes usb-hub-3s-v2. v2 was electrically correct (all-buck, no
> buck-boost) and its placement re-place succeeded, but its ONE hard part —
> the TPS25740A USB-C PD source controller (a 0.5mm-pitch QFN) — resisted
> routing across two frozen agents and multiple thrashed attempts. The PD
> controller existed for exactly one requirement: deliver 5V/**5A** on the
> USB-C port to a Raspberry Pi, which normally requires USB-PD negotiation of
> the 5A profile.
>
> THE FINDING (user + web-confirmed 2026-07-22): the Raspberry Pi 5 can be told
> to SKIP PD negotiation and assume a 5A supply via the bootloader EEPROM
> setting `PSU_MAX_CURRENT=5000` (or `usb_max_current_enable=1`). With that set,
> the Pi draws its full 5A from a plain 5V source that physically delivers it —
> no PD controller required on the supply side. Since this board is a DEDICATED
> Pi power supply, the PD PHY is unnecessary complexity.
>
> v3 = v2 MINUS the PD cell. Drop the TPS25740A + its two pass FETs + PD-config
> passives. The USB-C port becomes: the 5VC buck rail brought directly to VBUS,
> two CC pull-up (Rp) resistors advertising a source is present, VBUS bulk caps,
> ESD, and (optional) a simple e-fuse / current-limit switch for short-circuit
> protection. Everything else — input protection, the two LM5116 5V bucks, the
> 3x USB-A ports with TPS2557 + DCP — carries forward UNCHANGED from v2 (all
> proven-routable). The board ships with a documented required Pi setting.
<!-- prompt-verbatim-end -->

- date: 2026-07-22
- channel: interactive design session (v2 routing pain -> simplification)
- lineage: v3 supersedes usb-hub-3s-v2 (parked at a clean placement checkpoint,
  commit 1936291; routing open). v2 remains reference for the reusable cells
  (input protection, both bucks, USB-A ports — all carry forward). v1
  (usb-hub-3s) and v2 are NOT edited.

## End goal — definition of done

A 3S-LiPo (9-12.6V) powered supply delivering:
- 3x USB-A @ 5V/2A (2.5A burst) — via 2x LM5116 buck? no: the USB-A rail buck.
- 1x USB-C @ 5V/**5A** to a Raspberry Pi, delivered as a plain regulated 5V rail
  (no PD negotiation); the Pi is configured `PSU_MAX_CURRENT=5000`.
Orderable, DRC 0/0/0, verified JLCPCB release. Target fab tier: STANDARD (the
advanced-tier driver — the TPS25740A QFN — is gone).

## Spec tensions (D-SPEC / S9)

Surfaced at commission; each real tension links a decisions/NNNN ADR.

| id | requirement | tension / cap | how honoured | ADR | user-flagged |
|----|-------------|---------------|--------------|-----|--------------|
| T1 | USB-C delivers 5V/**5A** to the Pi | USB-C 5A normally REQUIRES PD negotiation (a PD source controller = the routing-hard QFN that stalled v2) | Provide a plain 5V/5A rail; the Pi skips PD via `PSU_MAX_CURRENT=5000` EEPROM override. Drop the PD PHY. Port is Pi-DEDICATED (a generic USB-C device would see a non-PD source, cap at 3A). | ADR-0001 | YES — user chose the override path over PD |
| T2 | 5A over USB-C wants an e-marked cable | Without PD, the cable e-marker is not enforced | Ship a doc note: use a short, 5A-rated USB-C cable. Board cannot enforce this. | ADR-0001 | noted |
| T3 | full Pi USB-peripheral current needs the override set | If the user forgets `PSU_MAX_CURRENT=5000`, the Pi caps downstream USB at 600mA (still boots/runs) | Document the required Pi setting in the release README + silk hint. | ADR-0001 | noted |

_none beyond the above — the buck rails are plain step-downs (see power_tree.yaml, E-TOPO PASS)._

## Reuse ledger (carried from v2, proven-routable)
- Input protection: XT60 -> fuse -> reverse-polarity P-FET -> TVS-on-VIN (the
  D1-corrected chain). REUSE verbatim.
- USB-A rail: LM5116 5V buck -> 5VA -> 3x TPS2557 + 2x TPS2513A DCP -> 3 USB-A.
- USB-C rail: LM5116 5V buck -> 5VC. (v3: 5VC now feeds VBUS directly, not a PD
  controller.)
- Both bucks route cleanly (leaded HTSSOP). The ONLY thing removed is the PD cell.

## Decision log (A# assumptions / D# decisions)

- **D1 (2026-07-22, ADR-0001):** Drop the TPS25740A PD cell; deliver a plain
  regulated 5V/5A USB-C rail, Pi skips PD via `PSU_MAX_CURRENT=5000`. (See T1-T3.)

- **A2 / D2 (2026-07-23) — DROP THE eFUSE, DISCRETE VBUS PROTECTION (USER DECISION).**
  - *Context:* v1.1 added a TPS26631 eFuse (U13) to protect the USB-C VBUS. It
    proved OVER-BUILT for a 5V/5A Pi-dedicated rail and was the ROOT CAUSE of both
    (a) the v1.2 board routing wall — its 20-pin HTSSOP IN_SYS pin is boxed mid-row
    in the fine-pitch west escape field (2 pour-fed 5VC taps unroutable), and
    (b) v1.1's two electrical ORDER-BLOCKERS — post-eFuse FB runaway (fixed by
    local-sense) and the SHDN 5.5V-abs-max destruction (7.56V at a 12.6V fault).
  - *Decision (user, relayed via the orchestrating session):* REMOVE the eFuse cell
    (U13 + its OVP/SHDN/dVdT/ILIM control passives R31/R32/R33/R36/C51/C52 + the
    control-pin clamps D6/D7) and replace it with a SIMPLE DISCRETE chain, reusing
    the on-BOM FETs (NOT an ideal-diode controller):
      `5VC -> Q6 (AON6403 P-FET, reverse-block, ENABLE-GATED via Q7 BSS138 off ENKILL)
       -> PMID -> F2 (PPTC polyfuse ~6A hold, over-current)
       -> VBUSC (protected connector; D5 TVS to GND, over-voltage) -> J5`
  - *Reverse-current realization (user-decided):* enable-gated P-FET — Q6's body
    diode (D=5VC / S=PMID) blocks VBUS->pack back-feed whenever Q6 is OFF; Q7
    inverts ENKILL so Q6 is ON (low-drop forward) when the hub is on and OFF on
    master-off. This covers the RT-T4 concern in the OFF state (a powered device on
    a switched-off port). It does NOT block reverse current while the port is
    actively ON (bounded by the polyfuse); an always-on ideal-diode controller was
    explicitly declined as unnecessary for a Pi-dedicated sink.
  - *Kept:* buck-C FB on LOCAL 5VC (v1.1 fix, R12=4.12k -> 5VC 5.352V). *Reverted:*
    buck-C EN re-merged to ENKILL (the eFuse FLT->EN_C un-merge + D6 coupling gone).
  - *Refdes delta:* REMOVE U13, R31, R32, R33, R36, C51, C52, D6, D7 (9). ADD F2 (1).
    RE-ROLE (same refdes): Q6 AON6354->AON6403 (P-FET reverse-block), R30 ILIM->Q6
    gate pull-up (100k), D5 SHDN-Zener->VBUSC TVS; Q7 BSS138 -> ENKILL gate inverter.
    118 -> **110 components**.
  - *E-INV:* re-derived (24 assertions) to the new chain
    `5VC -> Q6(P-FET, ENKILL-gated via Q7) -> F2(polyfuse) -> VBUSC(w/ TVS) -> J5`,
    buck-C FB on local 5VC, EN merged to ENKILL.
  - *STOCK FLAG (2 parts unverified in the sealed env):* **F2** (PPTC ~6A-hold 1812,
    MF-MSMF600 candidate — Vmax MUST be re-checked >=16V for the fault case) and
    **D5** (SMBJ6.0A TVS candidate). Parts-research to confirm sourceability + assign
    REAL LCSC before seal; NOT blocking the schematic gate.
  - *Schematic gate (Checkpoint A, MEASURED):* ERC **0**; parity **110 == 110 == 110**
    (circuit.json == kicad_sch == exported netlist == manifest); E-INV **24/24**.

- **A3 / D3 (2026-07-23, v1.3 FIX PASS) — OVER-VOLTAGE STRATEGY: DISCRETE SECONDARY
  PROTECTION (Option 2, USER-DECIDED).** v1.2 was sealed then found DO-NOT-ORDER by an
  external review (07_releases/v1.2-2026-07-23/SUPERSEDED.md). v1.3 is a NEW release
  fixing the confirmed blockers. The over-voltage architecture DECISION (Option 2):
  - *KEEP the existing v1.2 discrete protection* (Q6 AON6403 enable-gated P-FET + Q7
    BSS138 + F2 SMD2920-700 PPTC polyfuse + D5 SMBJ6.0A TVS) as **SECONDARY** protection.
    Do NOT design an SCR crowbar / active OVP for this revision.
  - *OV posture (HONEST):* the discrete chain protects against shorts, overload, and
    reverse-feed in the OFF state. It is **NOT guaranteed against a buck high-side
    short** (a sustained 12.6V fail-high): D5 clamps ~10.3V and F2 must trip to end the
    exposure - a crowbar, not a fast deterministic cutoff. This is acceptable in the
    intended context: a **supervised prototype with a replaceable Pi** (the sink is
    cheap and the operator is present). No doc may claim "Pi-protected against fail-high".
  - *ESCALATION BOUNDARY (verbatim):* "add active OVP if the system becomes unattended,
    hard-access, carries valuable storage, or powers expensive SDR".
  - *R12 fix (the confirmed order blocker):* assign the CATALOG-VERIFIED 4.12k 0.1%
    R12 = **C2984354** (AR03BTCX4121, Viking; JLC live-catalog verified 2026-07-23:
    4.12k +-0.1% +-25ppm 0603, stock 15353) - code now BAKED in the tsx so tscircuit
    can no longer value-resolve it to C2933210 (3.74k, the v1.2 undervoltage bug).
    Buck-C setpoint RE-DERIVED against the ACTUAL Q6+F2 path (Q6 ~4.3 mOhm + F2 R1max
    18 mOhm catalog-verified, hot ~31 mOhm), NOT the removed eFuse 34-48 mOhm model:
    5VC 5.352V nom / 5.27V @Vref-1.5%; E-MARGIN PASS (640mV headroom vs 528mV need).
  - *D5 fix:* C140903 is listed BIDIRECTIONAL by JLC (fails the uni-directional design
    assumption) -> replaced with **C113976** (SMBJ6.0A UNIDIRECTIONAL DO-214AA/SMB,
    catalog-verified 2026-07-23, stock 74758).
  - *SW1 (DECISION, implemented at artifact-regen):* move OFF automated assembly
    (hand-solder / off-CPL) until the SS12D07 VG4-vs-VG6 pitch is physically confirmed,
    or use the documented header+shunt fallback - see ORDER_README.

- **A4 / D4 (2026-07-25, v1.5 PCBA FIX PASS) — THE ASSEMBLY BOUNDARY.** Sealed v1.4
  was audited for PCBA correctness (not electrical correctness, which had already been
  red-teamed twice) and found **DO-NOT-ORDER**:
  `08_reviews/2026-07-25_v1.4_pcba-audit_assembly.md`, 15 findings, dispositions
  PCBA-1..15. v1.5 is a NEW release; v1.4 is immutable and gains only `SUPERSEDED.md`.
  - *P0 (PCBA-1):* **C1 and C2** — 100 uF/35 V POLARIZED polymer electrolytics across
    the 9.0-12.6 V pack — were on the CPL at **270.0** where the measured value is
    **90.0**: 180 deg REVERSED. They vent at first power-up, before any bench gate.
    Root cause: no per-LCSC rotation row for C2982822, so the exporter fell through to
    the footprint-NAME DB (a name cannot carry a per-part fact). Fixed at source
    (repo commits `9078ad9`, and `e0d735c` which corrected the handedness bug that had
    NEGATED every rotation the twin ever reported).
  - *Also corrected, same mechanism:* **J1** XT60 90.0 -> 0.0 (the name-DB pattern is
    start-anchored and never matched our vendored `XT60PW-M_EdgeTrim`), **Q7** BSS138
    270.0 -> 180.0 (`^SOT-23` = -90 is wrong for this part).
  - *ACCEPTANCE GATE (met):* v1.5's CPL differs from v1.4's in **EXACTLY FOUR CELLS**
    and nothing else; gerbers, drills, source, 3d and pdf are **sha256-IDENTICAL** to
    v1.4 (20 files). **No copper respin** is justified by anything found.
  - **USER DECISION 1 (U12 over-voltage): ACCEPT + MEASURE.** The USBLC6-2SC6 V_BUS pin
    on the C rail runs 5.352 V nominal / 5.479 V worst corner against the 5.25 V at
    which ST characterizes its leakage. Read from the datasheet directly: Table 1
    "Absolute ratings" carries NO V_BUS limit; 5.25 V is the I_RM test condition and
    V_BR is 6.0 V MINIMUM, which the worst corner clears by 521 mV. The mode is
    elevated leakage, not breakdown. **R12 is NOT changed** (lowering 5VC would spend
    the Pi undervoltage slack, which is only 69 mV once the E-MARGIN gate's own 1.2x
    derate is applied). Bench gate Q1 now RECORDS measured VBUSC and
    VBUSA; the derating ships as an evidence-backed MANIFEST waiver (canon M4).
    U8/U9/U10 on 5VA are in the same class at +23 mV worst corner (DETAIL_DESIGN sec.5.3).
  - **USER DECISION 2 (through-hole): ORDER JLC THT ASSEMBLY.** J1-J4 (4 refdes /
    22 plated holes) STAY on the CPL and are machine-assembled. Declared in
    `03_src/rules/assembly.yaml` and ORDER_README section 1a. F1 and SW1 remain the
    only two `not_assembled` refdes, each with dated evidence.
  - **USER DECISION 3 (build quantity): 5 boards.** Stock graded at 5 x per-board qty:
    **43/43 lines OK**, tightest ceiling C473910 = 37 boards, C5337088 = 90.
    Basic/Extended split **12 / 31**.
  - *Documents that did not exist and now do:* `01_docs/DETAIL_DESIGN.md` (three sealed
    part.yaml files had cited sec.1/2/5 as authority since 2026-07-21) and
    `03_src/rules/assembly.yaml` (the population set had no machine-readable home).
