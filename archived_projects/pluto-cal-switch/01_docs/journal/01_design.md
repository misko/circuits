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

## 2026-07-27 — iterate (D-MATE backfill, ADR-0005 phases 2-4)

- did: became the first consumer of `spf/`. Wrote
  `03_src/rules/mates.yaml` — 15 fact IDs, `use:` + `where:` each, **and no
  numbers** — against the new machine index `spf/plutoplus_hardware/facts.yaml`
  (16 entries, each carrying a `quote:` that must appear in the README record
  VERBATIM). Added the BRIEF's `## Mating fact-lock` table as the user-facing
  half.
- result: `import_provenance_check.py .` → **15/15 facts graded, 0 fails**:
  9 MEASURED (caliper), 3 ESTIMATED (one dimensional — `connector_outline_width`
  8.13 mm ±1.5 %/±0.12 mm — and two informational), 2 OWED, 1 superseded plot
  number kept visible with its grade attached. The two OWED are the RF-axis
  height above the Pluto's PCB and the mounting-hole positions: declared, not
  invented, and the gate FAILS either if it is ever consumed dimensionally.
- the thing worth recording: `case_barrel_protrusion` (≈7 mm) is ESTIMATED with
  **no error bar anywhere in the record**, so it is indexed but deliberately
  NOT consumed. A dimensional reference to it fails M-BAR — which is the
  correct answer, not a defect in the file.
- next: unchanged — stage 4 still waits on three user answers; the three
  physical measurements now have machine-visible OWED rows instead of prose.

## 2026-07-27 14:05 — start (re-spec: A8 cables + A9 40 dB minimum)

- did: read the two user decisions that landed together — A8 "lets not do the
  fixed bulkhead version, lets use SMA cables to connect our board to the
  pluto" (+ the confirmation that the PlutoPlus RF ports are SMA FEMALE and
  that the Pluto is in a case, so its PCB is not the mating reference at all),
  and A9 raise the cal-path attenuation 30 -> 40 dB and specify it as a
  MINIMUM across 70 MHz-6 GHz. Re-read BRIEF/ARCHITECTURE/DETAIL_DESIGN, the
  14 ADRs, `03_src/rules/*.yaml`, and canon M-IMPORT / M-QUOTE.
- result: scoped the blast radius before touching anything. A8 kills ADR-0006
  (SMA->SMP adapters, $101), ADR-0014/D6 (the 34.88 mm midpoint), the whole
  +/-0.05 mm rigid-SMA tolerance analysis and 13 of the 15 `mates.yaml`
  consumptions; it promotes ADR-0007's KH-SMA-KE-Z from 2 ports to 5. A9 kills
  ADR-0013/D5 (minimax reference frequency) by REFRAMING rather than by
  answering it. Both are edits, not supersedes: nothing on this board is
  sealed (`04_kicad/` and `07_releases/` hold only `contracts.md`).
- next: verify the connector gender from the datasheet FIELD (not the
  part-number suffix — the repo has already paid $101 for a gender inference
  on this board), confirm pad-vs-switch topology, then re-derive the chain.

## 2026-07-27 14:35 — iterate 1 (gender, verified two ways, and a bad citation found)

- did: opened `02_parts/KH-SMA-KE-Z/KH-SMA-KE-Z-C504007.pdf` and read the
  PRINTED FIELDS rather than the model string; rendered sheet 2/2 at 400 dpi
  and cropped the end view.
- result: **it IS a jack.** the p.1 `产品名称` (product-name) field reads
  **`SMA 直式印制面板插座`** — 插座 = receptacle/socket. Sheet 2/2 shows the
  mating end as a FIXED barrel with an EXTERNAL `1/4-36UNEF` thread at Ø6.2
  and NO coupling nut, which is the jack shell form. **But neither page states
  the CENTRE-CONTACT polarity in words**, so those two prove FEMALE SHELL and
  do NOT exclude RP-SMA (whose receptacle also has an external thread and a
  male pin). Closed on a second, independent source — LCSC C504007 product
  page, read 2026-07-27: `CONN RCPT SMA TH`, interface type **"Inner hole"**.
  **AND A DEFECT IN OUR OWN RECORD:** `part.yaml` said the gender was *"read
  from the part-number decode on p.1"*. **There is no part-number decode on
  p.1** — the page carries the model string in the 型号 field and nothing
  else. The claim named a source that does not exist, and it was the ONLY
  provenance behind the gender of five connectors. Corrected in place.
- next: the topology question, then the two RF numbers' provenance.

## 2026-07-27 14:50 — iterate 2 (Decision C: pad vs switch)

- did: traced every path from `TX_PLUTO` to an RX port in ARCHITECTURE §3 and
  `electrical_invariants.yaml`.
- result: **UPSTREAM, and by a wide margin.** `TX_PLUTO` connects to exactly
  one thing — PAD_A1's input — and every route to an RX port crosses
  A1 → split → A2 → switch, in that order. So no switch state and no switch
  FAULT (including a die shorting RFin–RF1–RF2) can present raw TX to a
  receiver: the minimum TX→RX attenuation is the same in every state, and the
  switch's own 20–43 dB of isolation sits ON TOP of it in antenna mode. **The
  property was already bought and had never been stated**: ADR-0004 put A2 in
  the ARM on isolation / open-cable / antenna-mode-reflection / AGC arguments,
  none of which was about faults. Counted what the alternative would have
  cost: pads downstream of the switch ⇒ a shorted die puts TX on an RX at the
  splitter's 6.02 dB alone = **+2 dBm from a +8 dBm TX, i.e. AT the abs-max
  rating**. Added a `series_chain` invariant citing ADR-0016 so the property
  is machine-checked and not merely true.
- next: provenance on the two RF numbers before touching the pad value.

## 2026-07-27 15:05 — iterate 3 (the two RF numbers, and a premise corrected)

- did: went after primary sources. `analog.com` PDF timed out at 60 s to
  WebFetch and `curl` was refused by the sandbox on two attempts (HTTP/2
  INTERNAL_ERROR, then HTTP/1.1); DigiKey's HTML mirror returned **410 Gone**,
  reproducing what the sourcing spike and its adversarial pass had both hit.
  Found a page-for-page mirror of the vendor PDF and walked it page by page.
- result: **both numbers are now CITED with a page.**
  **RX abs max = +2.5 dBm** — AD9363 Rev. D, printed **p.15 of 32**, ABSOLUTE
  MAXIMUM RATINGS, row `RF Inputs (Peak Power)`. The secondary EngineerZone
  source was RIGHT, and confirming it was still worth doing: the row says
  **PEAK**, a qualifier the old text did not carry, and the same table's
  `Tx Monitor Input Power (Peak Power) 9 dBm` is a DIFFERENT port that could
  be misread as the RX limit.
  **TX max = +8 dBm** — printed **p.4 of 32**, TRANSMITTERS 800 MHz,
  `Maximum Output Power`, *"1 MHz tone into 50 Ω load"*; the three
  characterized bands are **8.0 / 7.5 / 7.0 dBm** at 800 MHz / 2.4 GHz /
  3.5 GHz. **The board's "+7 dBm" was the LOWEST of the three being carried as
  a ceiling — the design was 1 dB optimistic about its own input**, and the
  user's suspicion that some bands run hotter was correct. Also found the
  honest residual: these are the TRANSCEIVER's numbers, and they bound the SMA
  PORT only if the Pluto's TX front end is passive, which nobody has
  established for a PlutoPlus — declared OWED in `spf/` with how to obtain it,
  and bounded (19 dB of undiscovered gain before the board's own +27 dBm
  ceiling binds). All three facts moved into `spf/plutoplus_hardware/` and are
  consumed through `mates.yaml`, because they are facts about foreign hardware
  and were living as ungraded prose in DETAIL_DESIGN.
- next: re-derive the chain with cables in it, then size the pad.

## 2026-07-27 15:25 — iterate 4 (the chain, and sizing a floor instead of a target)

- did: re-derived the whole TX→RX budget with two SMA cables replacing the two
  adapters and the two SMP mated pairs, then sized the pad against the new
  specification.
- result: **chain tilt 3.09 → 6.13 dB** — the two cables are +2.60 dB of that
  at 6 GHz and are now the largest single non-pad term at the top of the band.
  **Sizing a MINIMUM inverts the method**: instead of centring a pad on a
  target you take the LOWER BOUND of every term. Taken to its end, the design
  credits only the pad's datasheet MIN column and the splitter's 5.97 dB
  worst case, with **both cables, all four coax interfaces, 65 mm of
  microstrip, the SPDT and the splitter parasitics all credited at ZERO**.
  `A1 = 2×YAT-10A+ + 3×YAT-2A+`, `A2` untouched ⇒ path min **34.8 dB**
  (DC–5 GHz) / **34.1 dB** (5–15 GHz) ⇒ **≥40.07 dB, binding at 6 GHz**;
  typical **44.59 → 50.16 dB**. Checked the build one chip either side:
  `3×10 + 3×2` gives **38.67 dB and FAILS**, so the last YAT-2A+ is what buys
  the guarantee for $3.40; `4×10` clears easily but lands 8.7 dB above spec
  and would have to come out of A2, dropping isolation 29.9 → 26.0 dB.
  **The whole 18 dB went pre-split**, so isolation, the open-cable masking and
  the antenna-mode reflection are all unchanged — three numbers that three
  separate arguments had pinned.
  **And the result that mattered most was not the one the decision was made
  on:** at this board's own declared +27 dBm abuse ceiling, the 30 dB build
  left the user's receiver **2.7 dB** from its absolute maximum; ≥40 dB makes
  it **15.6 dB**. Two ratings that had never been put in the same table.
- next: retire the 13 geometric mates.yaml consumptions, then run the gates.

## 2026-07-27 16:20 — iterate 5 (gates, and a NEW gate gap)

- did: ran `import_provenance_check.py`, `contracts_audit.py`,
  `electrical_invariants.py --adr-coverage` and `tests/run_tests.sh`.
- result: **import provenance PASS, 18/18 graded, 0 fails** (was 15/15 — 13
  geometric consumptions retired in place with their cause, 2 survive, and 3
  ELECTRICAL facts arrived to replace them). **contracts_audit 237 files, 0
  violations.** **tests 641 passed / 6 failed / 369 known-bad**; all six
  failures are `t1_electrical_invariants` tests that need the GITIGNORED
  `projects/smc0985-cooksense/06_build/netlists/cooksense.net`, absent in this
  worktree (`git check-ignore` confirms `06_build/*`) — KNOWN pre-existing,
  reported and not chased.
  **NEW FINDING — E-ADR FAIL 11/12 is a GATE GAP, not a design defect.**
  `electrical_invariants.py:protection_adrs()` excludes only `0000-example`
  and never reads `status:`, so it still demands an invariant from **ADR-0006,
  whose decision was reversed** and for which no design intent exists to
  assert. The intent loop IS closed — ADR-0015 emits 3 assertions, ADR-0016
  emits 1. Checked whether this is fleet-wide: **pluto-cal-switch is the FIRST
  board to supersede a protection/topology-TAGGED ADR** (the only other
  superseded ADR under `projects/`, cooksense 0005, carries no `tags:` line
  and so was never in the denominator), which is why nothing had hit it.
  Declared as ARCHITECTURE §12 **O8b** and spun out as a task; **not worked
  around**, because retagging the ADR to silence it is exactly the silent
  downgrade this canon exists to prevent.
- next: commit. Stage 4 is unblocked — no hardware question remains.

## 2026-07-27 16:30 — finish (re-spec complete)

- did: completed the A8 + A9 re-spec as an EDIT, not a supersede — nothing on
  this board is sealed (`04_kicad/` and `07_releases/` hold only their
  `contracts.md`).
- result: 2 new ADRs (0015 cables, 0016 the 40 dB minimum); 4 marked
  `superseded-by-NNNN` with a `## Superseded` section appended carrying the
  reversal, its date and its cause (0004 — half superseded, half carried
  forward verbatim; 0006, 0013, 0014); 1 EXTENDED not superseded (0007, 2 → 5
  ports). `02_parts/SMP-MSLD-PCE-5T/` deleted per the 02_parts repair rule,
  closing a PDF-not-vendored deviation **by deletion rather than by obtaining
  the drawing** — worth noting which way that went. `spf/plutoplus_hardware/`
  gained an electrical section and 3 facts; `sma_gender` moved
  ESTIMATED → MEASURED on the owner's statement. BRIEF: A8/A9 logged, D5 and
  D6 struck, T4 and T5 resolved, **T8 added** (the pad had been sized against
  the wrong quantity), the Mating fact-lock re-shaped into Consumed/Retired,
  and six of eleven Open items closed.
- **the thing worth recording, and it is not the dB value:** BOTH user
  decisions removed a dependency rather than resolving one. A8 did not answer
  "which PlutoPlus?" — it stopped consuming the PlutoPlus's geometry, so the
  0.32 mm disagreement between two physical units that motivated this repo's
  entire M-IMPORT canon **now costs this design nothing**. A9 did not answer
  "30 dB at which frequency?" — it made the question meaningless, and then
  absorbed a doubling of the chain tilt without changing. **A tension you stop
  consuming beats a tension you decide.**
- next: stage 4, schematic authoring.
