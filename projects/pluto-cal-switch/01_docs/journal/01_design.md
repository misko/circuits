# journal — stage 1-3 (design docs, parts, rules)

## 2026-07-27 09:10 — start
- did: read BRIEF.md, pluto-plus-mechanical.md, the D-SPEC sourcing spike output
  (6 functions, each with an adversarial refutation pass), SKILL.md stages 1-3,
  design-policies.md, and the 02_parts / 01_docs / decisions / rules contracts.
- result: spike verdicts are 6/6 `sourceable`, but FIVE of the six adversarial
  passes returned `WEAKENED` and the SMA pass returned **REFUTED**. The
  refutations are not cosmetic — they change three part choices and reverse two
  layout rules. Enumerated: (a) BGS12WN6 (C534203) is pin/truth-table/footprint
  identical to the picked BGS12P2L6 and publishes a 50-698 MHz row the pick
  lacks; (b) KH-SMA-KE-Z (C504007, 19252 stock, VSWR <=1.35 spec'd, 13.5 mm)
  strictly dominates BWSMA-KE23 (C5250061, 2956, no VSWR spec, 28.6 mm) on the
  same land pattern; (c) the SMA launch antipad rule was stated BACKWARDS
  (>=O3.5 mm, not O2.6 mm); (d) the 6 GHz splitter budget used the typ column
  where max belongs; (e) the GPIO header cannot be read by an RP2040 GPIO —
  PlutoPlus IO is 1.8 V, RP2040 VIH is a flat 2.0 V.
- next: two research gaps fanned out (SMP + SMA->SMP adapter sourcing, which the
  spike never covered because the mating strategy was decided after it ran;
  BGS12WN6 primary-datasheet extraction). Write ARCHITECTURE + DETAIL_DESIGN
  from the MEASURED datasheet terms, not the spike's summary numbers.

## 2026-07-27 10:40 — iterate 1
- did: re-derived the whole TX->RX loss budget from datasheet terms rather than
  carrying the spike's, because the spike's interconnect term assumed a 1.6 mm
  substrate (0.013 dB/mm) while the 6 GHz pad-matching requirement forces a
  0.2104 mm top prepreg (0.036 dB/mm) — a 2.7x error on the single largest
  non-pad term.
- result: chain tilt is **3.18 dB across 70 MHz-6 GHz**, not the 1.64 dB the
  spike reported. Non-pad loss 6.51 dB @70 MHz / 9.69 dB @6 GHz. Minimax pad =
  21.90 dB; nearest realizable from stocked YAT parts = **22 dB**, giving
  28.5 / 30.0 / 31.7 dB at 70 MHz / 2.9 GHz / 6 GHz.
- next: adjudicate pad placement (one pre-split pad vs pre-split + per-arm) —
  the splitter and attenuator agents returned OPPOSITE recommendations.

## 2026-07-27 11:20 — iterate 2
- did: adjudicated the pad-placement conflict on numbers.
- result: per-arm pads WIN on four independent counts, three of which the
  attenuator pick never costed: (1) inter-channel isolation 6.02 -> 6.02+2*A2;
  (2) an unplugged RX SMA adds +3.52 dB to the SURVIVING channel with no error
  indication unless masked by 2*A2; (3) in ANTENNA mode both splitter arms face
  reflective SPDT shorts, so with no arm pad Zin(splitter) = infinity and TX
  sees Gamma = +1; (4) AD936x RX return loss MOVES with AGC index, so the
  contamination is non-stationary and not calibratable. Split chosen:
  **A1 = 10 dB pre-split, A2 = 12 dB per arm** -> isolation 6.02+24 = 30.0 dB,
  open-port error ~0.2 dB, TX-port Gamma in antenna mode |0.063| not 1.
- next: write the ADRs, then 02_parts, then the rules yaml.

## 2026-07-27 11:55 — iterate 3
- did: adjudicated the MCU and the fab tier together, after datasheet-verifying
  the one candidate that could have avoided ADVANCED tier.
- result: **CH32X035F8U6 is BLOCKED**, and not on the reset state. (1) It is
  **QFN-20-EP 3x3 at 0.40 mm pitch**, not TSSOP-20 at 0.65 — WCH's own naming
  rule (`U` = QFN, DS V2.2 p.44), the package table (p.38) and both LCSC and
  the JLC API agree, so the entire fab-tier savings argument rested on a pitch
  the part does not have. (2) **No crystal option exists** — `HSE` appears ZERO
  times in the datasheet and the 262-page reference manual — and the internal
  HSI is spec'd at -2.6/+2.2 % over -40..85 C against USB FS +/-0.25 %, i.e.
  **10x over budget at every documented temperature range**, with no documented
  SOF auto-trim. (3) ISP entry needs a strap on PC17, which IS USB D+, and
  whether a virgin part auto-enters the bootloader without it is not stated.
  Plus a fourth finding that cuts on the safety axis itself: its reset state is
  FLOATING INPUT with no internal pull, so the external pull-down does 100 % of
  the work — **RP2040 is fail-safe with the resistor missing and CH32X035 is
  not**.
- next: fab_tier `jlc_4layer_advanced`, and note it is forced TWICE
  independently (RP2040 QFN-56 escape AND the BGS12WN6 pin-2 ground via), so
  the tier does not ride on the MCU choice alone.

## 2026-07-27 12:05 — iterate 4
- did: ran the rules gates against the authored yaml.
- result: E-ADR **FAIL** first pass — 5 protection/topology ADRs cited by no
  invariant. Closed all five with real netlist assertions rather than by
  retagging the ADRs. Second pass then failed EVERYTHING, because
  `load_invariants` raises on the first schema problem and `--adr-coverage`
  treats a broken file as citing nothing. Root cause was a two-word `why:` the
  checker judged non-substantive — the gate was right. **AND A YAML TRAP WORTH
  RECORDING: an unquoted `adr: 0011` parses as OCTAL 9, and `adr: 0012` as 10**,
  so those two would have silently satisfied ADR-0009 and ADR-0010 instead.
  Every `adr:` value is now quoted. Final: **E-ADR OK, 39 invariants, 14 ADRs**.
- next: E-TOPO exits 2 on a GATE GAP, reported not worked around.

## 2026-07-27 12:10 — finish
- did: completed stages 1-3 and stopped before the schematic, as scoped.
- result: `ARCHITECTURE.md`, `DETAIL_DESIGN.md`, 14 ADRs, 11 `02_parts/`
  entries (7 complete with figure-cited pin maps, 4 with declared deviations),
  `nets.yaml` / `power_tree.yaml` / `electrical_invariants.yaml` /
  `assembly.yaml`, BRIEF updated with D5/D6/D7, tensions T4-T7 and a full
  decision register. Gates: E-ADR OK, E-MARGIN N-A, E-OFF N-A, E-INV and
  E-TOPO exit 2 for reasons stated in the beacon. `contracts_audit.py` clean.
- next: stage 4 (schematic authoring) — but THREE user answers and THREE
  physical measurements are owed first, all listed in `STATUS.md`.
