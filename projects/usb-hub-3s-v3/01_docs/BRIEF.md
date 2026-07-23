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
