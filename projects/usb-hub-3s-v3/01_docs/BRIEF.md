# brief: usb-hub-3s-v3

status: active
current_release: no

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
