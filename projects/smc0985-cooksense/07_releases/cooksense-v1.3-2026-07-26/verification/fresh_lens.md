# FRESH-LENS REVIEW — cooksense v1.3, zero context, frozen archive

Five zero-context reviews were run against the staged v1.3 archive. Each was
given **only** the release directory — no journals, no STATUS files, no
`08_reviews/`, no git history, no conclusions from any earlier review — and the
archive was `chmod a-w` for the duration so it could not shift underneath the
reader. **Four of the five beat a seal.** This file records the last one, which
is the one whose findings are dispositioned in `dispositions.md`.

## Verdict history

| lens | verdict | what it stopped |
|---|---|---|
| 1 | DO-NOT-SEAL | four artifacts still reading DO NOT SHIP/FAIL; the P1-1 rail fix had invalidated the evidence behind them (via count 1045 -> 1047) |
| 2 | DO-NOT-SEAL | `MANIFEST.txt` and `ORDER_README.md` were not a faithful index of what `verification/` already knew |
| 3 | DO-NOT-SEAL | the CH0/CH3 ADC transfer function was a declared gap under a MANDATORY acceptance test |
| 4 | DO-NOT-SEAL | eight defects incl. the `fp-lib-table` pointing outside the archive |
| **5** | **DO-NOT-SHIP** | **the eleven items below** |

## Lens 5 — what it was asked

To decide whether the archive is safe to send to a fab and to a customer, and to
hunt six named failure classes: internal contradiction, stale artifact, false or
overclaimed pass, unshippable output, "the archive does not stand alone", and
safety. It was told to recompute every derivation and to report measured numbers
rather than adjectives.

## Findings, and what happened to each

Full dispositions with measurements are in `dispositions.md`, section
**"CLOSED AFTER THE FIFTH LENS"**. In summary:

- **Nine findings VALID and FIXED** — the missing review file, the §6 rotation
  *provenance* overclaim, the opto loop's 50 mA-vs-3.2 mA rating, the 136-vs-121
  island population, a stale "one finding is OPEN" header, an unmarked
  historical ledger carrying superseded isolation wiring, the un-propagated
  V_CEO/inductive-load warning, a stale 3.107 V comment in the TSX, and the H4
  notch quoted 0.10 mm outside the board.
- **Two findings REFUTED BY MEASUREMENT**, and both refutations improved the
  archive:
  - **The claim that seven CPL rows ship 180° out, U_OPTO included.** The
    disagreeing operator applied a counter-clockwise rotation matrix to
    coordinates whose Y axis points **down**, which mirrors the fit. Re-run as a
    direct comparison of two `.kicad_mod` files — no board frame, no operator —
    **all seven codes agree with the authority table.** This also closes a
    disagreement the archive had been carrying as explicitly unresolved.
  - **The claim that F.Cu is not the binding layer for the 2.0000 mm ISO
    minimum.** Re-measured per layer: F.Cu, In1.Cu, In2.Cu and B.Cu are **all
    2.0000 mm**.
- **One defect the lens did NOT find, discovered while fixing L5-8:** the
  archive ships `verification/parity.md` reading `REAL DISCREPANCIES: 1 -> FAIL`
  and nothing explained it. It is `J_KEY_MATRIX.MP` — a board-stage bond to
  `GND_ISO` that `parity_padmap.txt` declares and the board does not implement.
  Measured, it is not an isolation defect (two-hop creepage **13.8960 mm** vs a
  6.000 mm requirement); it costs the connector shell its ESD drain. It is now
  §13 item 11. **The transferable part is why no gate caught it:** the
  `keypad_isolation_6mm` DRU rule is conditioned on `B.NetName != ''`, which
  exempts unnetted copper by construction — so "0 DRC violations" was never
  evidence about floating copper.

## What lens 5 checked and found correct

Reported as measured agreement, because a checked-and-agrees result is a result:
all sha256 digests match (78 at the time that lens ran; the archive now
carries 79, the extra one being this file); the gerbers re-export flash-identical from the
shipped board on every copper, mask, paste and edge layer; BOM 205 refdes minus
CPL 189 equals exactly the 16 declared `not_assembled` refs; schematic `Value`
matches CPL `Val` on 189/189; A-POS reproduces 189/189 at worst 0.00000 mm; both
P0 fixes (`R_OPENT` 62 kΩ/C37825, `R_WDPETPD` 1 kΩ/C11702) and the P1-1 rail fix
are present in schematic, BOM, CPL and stock check; 1047 vias all 0.25/0.15;
DRC 0/0/0 reproduces from `source/` alone; the silk disclosure is exact at 78
violations with **zero** touching a safety caption and all seven ADR-0012 texts
at the 0.150 mm floor; ISO minimum 2.0000 mm with 0 pairs under, on a scanner
demonstrated able to read 0.1500 mm elsewhere; the J_ISOLOOP pole legend matches
the board pad-for-pad; and every arithmetic derivation re-computed correctly
(2.03704 V, 3.10734 V, 5.21 kΩ, 2.26875 V, 8.40 °C, 72.81 °C, and three spot-
checked rows of the §2b error table).

## Standing caveat

This file is written by the same agent that built the release. **It is a record
of an independent review, not itself an independent review.** The lens's raw
verdict was DO-NOT-SHIP; that verdict was earned, and the eleven items above are
why. A sixth lens was run against the archive after these fixes landed.

---

# LENS 6 — run against the archive after the lens-5 fixes landed

**Verdict: DO-NOT-SHIP — "narrowly, and on paper only."** No P0. No board
change, no re-export, no re-route. Every ordered artifact reproduced; the
blockers were two P1s in **§6, the mandatory order-preview human gate**, which
is the worst place in the document to carry a false statement.

Twelve findings, **all twelve valid, all twelve fixed** — dispositioned in
`dispositions.md` under "CLOSED AFTER THE SIXTH LENS". The two that matter most:

- **§6 item 15 claimed two polarized diode codes "carry `two-channel` rows".**
  They do not. This archive's own `rotation_measurements_v13.txt` records both
  as `single-channel / ROW: (WITHHELD)` and `twin_report.csv` marks all three
  affected refs **POLARITY-FIT-BLIND** — the twin could not fit them at all.
  The eyeball was the sole defence and the text said it was a double-check.
- **`GND_ISO` does not exist on this board**, and §13 item 11 had called for
  bonding the keypad connector's tabs to it in v1.4. Measured: the tab sits
  **0.5810 mm** from KEYPAD_ISO copper, so bonding it to the ground that DOES
  exist would fire `keypad_isolation_6mm` at 0.581 mm against 6.000 — **a 10.3x
  violation, the worst on the board.** The tab is floating because there is
  nowhere safe to land it. The instruction is retracted and inverted.

## What lens 6 independently verified as correct

All 79 sha256 digests. 226 footprints / 3925 tracks / **1047 vias all
0.25/0.15** / 188.000 × 92.000 mm / H4 notch at x[191.500, 200.000] with 200.000
the east edge / 12 slots at 0.600 mm. A **canonical gerber re-export from
`source/` matching the shipped set flash-for-flash and draw-for-draw** on every
copper, mask, paste and edge layer, with the drill counts reconciling to the
drill-mark count exactly (105 non-via holes ↔ 105 marks). BOM ≡ BOM_JLC, CPL ≡
CPL_JLC, 205 designators = 226 − 21 exempt, 189 CPL rows = 226 − 37 excluded,
Value == Val on 189/189, **51 distinct LCSC codes each with a single consistent
rotation offset across all its refs**, and all 22 in-archive measured offsets
matching the shipped CPL. Both P0 fixes present in every ordered artifact.
Isolation re-measured with an independent polygon scanner: ISO_CONTACTOR
**2.0000 mm on each of F.Cu / In1.Cu / In2.Cu / B.Cu**, KEYPAD_ISO **6.1200 mm** (lens 6 reported 6.1236 and lens 7 measured the pair analytically at exactly 6.1200 — two 1.500 mm circular pads 7.620 mm apart; the four-decimal variants erred toward extra margin).
DRC **0/0/0** from a bare extraction of `source/` alone; the four silk checks
re-enabled reproduce **78** violations with **zero** touching a safety caption.
**§2b re-derived from scratch — all eight error-table rows, the open-NTC node
(2.26875 V → naive 8.40 °C), the 72.80 °C over-temp trip, the 2.03704 V and
3.10734 V thresholds, the 5.21 kΩ WDI limit, I_F 6.36 mA → I_C 3.18 mA, and the
16.7 % V_CEO margin — every figure landed.** The only number it could not
reproduce exactly was a worst-case separation the archive states as 193 mV where
the lens computes 202 mV: the archive is **9 mV conservative**, by one V_IO.

**Caveat, unchanged:** this file is written by the agent that built the release.
It records independent reviews; it is not itself one.
