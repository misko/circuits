# Fresh-context pin review — crow-array-central v1.0 (2026-07-18)

Protocol: ~/.claude/skills/kicad-pcb/references/pin-review-protocol.md.
Four independent fresh-context agents, no session context, dossiers from
pin_audit.py (06_build/pin_audit/) + primary datasheets. Q9 (AO3401A
reverse-FET polarity) was resolved in a prior dedicated review (D19:
board correct; part.yaml doc errors fixed) and was NOT re-reviewed.

## Verdicts

| Group | Parts | Verdict | Disposition |
|---|---|---|---|
| XU316 | U1 (TQFP-128 + EP, 129 pins) | PASS | winding CCW pin-1 top-left matches datasheet Fig.2 exactly (no mirror); all 128+EP functions/nets agree incl. QSPI SIO order, MIPI-unused-to-GND, EP=VSS with 4x4 via grid. 2 QUESTIONs resolved below. |
| PCM1865 pair | U2, U3 (TSSOP-30) | PASS | winding matches SLAS831D p.10 (no mirror, no EP); 30/30 pins agree; pairwise symmetry clean; the single divergence (pin 25 MS/AD: U2=GND 0x4A, U3=3V3 0x4B) is the required I2C address split. |
| RJ45 group | J1..J6 (RJHSE-5384) | FAIL -> ADJUDICATED PASS (D28) | reviewer proved footprint numbering correct (180-deg rotation, not mirror; all 12 contact/LED holes + 2 SH + 2 NPTH present) and found the board's 5/7 contacts contradict 02_parts/RJHSE-5384/part.yaml. Adjudication: the SEALED pod v1.0 terminal map (J1: 4=5V, 5=GND, 7=5V, 8=GND, git 17ceffe) is the mating authority — the central board matches it contact-for-contact on all six jacks; the part.yaml note was the wrong document and is FIXED (Q9-class doc error). Shield SH->GND at central = deliberate single-point star bond (pod leaves SHIELD floating w/ DNP R15). |
| Substitutes | U12 (TLV70018DDCR), Y1 (X322524MOB4SI) | PASS / PASS | D27 drop-in checks from TI SLVSA00E DDC pin figure (IN/GND/EN/NC/OUT = board 3V3/GND/3V3-tie/NC/1V8; EN>0.9V satisfied) and YXC YSX321SL top-view figure (1/3 diagonal crystal, 2/4 case-GND; CL 12pF = FA-238 code, USB clock unchanged). |

## QUESTION resolutions (U1 reviewer)

1. "RST_N/JTAG live in the fixed-1.8V VDDIOB18 domain — what pulls them?"
   RESOLVED: R50 = 10k pull-up to **1V8** (generate_schematic region 11
   "RST_N RC (10k->1V8, 10n)") — correct domain. TDI/TMS/TCK/TDO go to the
   bare xSYS debug headers J13/J14 only; NOTE for users (ORDER_README): any
   attached debug adapter must drive these at 1.8V (xTAG senses target IO
   voltage).
2. "PLL_AVDD needs a filtered clean supply."
   RESOLVED: PLL_AVDD is fed from 0V9 through FB3 (600R@100MHz ferrite) +
   C123 1uF (generate_schematic region 6, per XMOS ref design / part.yaml
   H.2) — the datasheet-recommended filter, at the correct 0.9V rail.

## Non-blocking notes

- U2/U3 VREF/LDO decoupling caps exist as C-lines in the BOM (VREF_A/B,
  LDO_A/B nets); placement proximity gated by audit_board.
- Part.yaml citation label for TLV70018 said SBVS181; TI serves SLVSA00E
  at the cited URL — label corrected in review, content verified.
- Dossier "side" column mislabels TSSOP corner pads (classifier quirk);
  coordinates authoritative.

Any FAIL above would block the order; after the D28 adjudication the
review stands at 4/4 groups PASS.
