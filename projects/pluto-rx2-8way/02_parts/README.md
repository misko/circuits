# 02_parts — folder status + deviations register

**Status: FIFTEEN dossiers (2026-07-28).** Started as the D-SPEC sourcing-spike
output (2026-07-27/28), amended at the stage-3 design gate, extended at the
stage-2 continuation to **thirteen — one per part in
`01_docs/DETAIL_DESIGN.md`** — and then **back-filled by TWO more at stage 4**,
when the schematic showed that "one per part in `DETAIL_DESIGN.md`" was the
wrong denominator (deviation 8). Nothing here is in a BOM yet, because there is
no BOM yet — that is still a deviation from the contract's flow and it is
registered below, but it is now a deviation of TIMING rather than of COVERAGE.

| MPN | role | LCSC | JLC lib | PDF present |
|---|---|---|---|---|
| `PE42482A-X` | the SP8T antenna selector (`U_SW`) | C5121458 | extended | **yes** |
| `KH-SMA-KE-Z` | 10x SMA jack (8 antenna + RX1 out + RX2 out) | C504007 | extended | **yes** |
| `0402WGF2200TCE` | **220R — one of the two series arms of the RX1 pickoff** (`R_T1`, `R_T2`) | C25091 | base | **yes** |
| `MCP1755S-3302E/DB` | the 3V3 linear regulator (`U_LDO`) — SOT-223-3 | C638611 | extended | **yes** |
| `RP2040` | the sequencer (`U_MCU`) — QFN-56 7x7 P0.4 | C2040 | extended | **yes** |
| `W25Q128JVSIQ` | QSPI XIP flash (`U_FLASH`) — SOIC-8 208mil | C97521 | **base** | **yes** |
| `ABM8-272-T3` | 12 MHz crystal (`Y_XTAL`) — 3225-4P | C20625731 | extended | **yes** |
| `TYPE-C-31-M-12A` | USB-C 2.0 16P receptacle (`J_USB`) | C5337088 | extended | **yes** |
| `USBLC6-2SC6` | USB data-line ESD array (`U_ESD`) — SOT-23-6 | C7519 | extended | **yes** |
| `1206L050/24WR` | 500 mA PPTC (`F_IN`) — 1206 | C2154056 | extended | **yes** |
| `SMBJ6.0A` | **6.0 V** standoff unidirectional TVS (`D_TVS`) — SMB | C83270 | extended | **yes** |
| `BLM21SP601SN1D` | 600R ferrite (`FB_IN`) — 0805 | C3716677 | extended | **yes** |
| `KT-0603R` | red 0603 indicator — **ONE MPN serves BOTH** `LED_PWR` and `LED_ST` | C2286 | **base** | **yes** |
| `TS-1187A-B-A-B` | SMD tact switch — **ONE MPN serves BOTH** `SW_BOOT` and `SW_RUN` | C318884 | **base** | **yes** |
| `0402WGF4700TCE` | 470R single-arm pickoff — **REJECTED ALTERNATE**, not on the board | C25117 | base | no, by contract |

**ELEVEN OF FOURTEEN POPULATED PARTS ARE `extended` LIBRARY** (was eleven of
twelve). Only C25091, C97521 and the two parts added on 2026-07-28 — **C2286
and C318884, both `base`** — are not. That is the one piece of good sourcing
news this board has had: the two back-filled lines are the deepest-stocked on
the BOM (7.59 M and 1.36 M) and neither needed an extended-tier part to get
there. Every extended line still needs an order-day `jlc_stock_check` re-run,
and two of them are thin enough to name here: **`C638611` (U_LDO) at 86** and
**`C5337088` (J_USB) at 84**, measured 2026-07-28. Neither is a blocker at
prototype quantity; both are single-source lines for a function the board
cannot omit.

**THE PRIMARY CHANGED ON 2026-07-28.** The user confirmed BRIEF D3 with the
SPLIT-ARM variant, so the pickoff is **2 x 220 ohm in series** and the single
470 ohm part is the alternate that lost (ADR-0002). The 470 dossier is KEPT and
RE-LABELLED rather than deleted — see deviation 3.

## The standalone gap is CLOSED for two of the three parts that had one

Both missing datasheets were fetched and committed on 2026-07-28, and the
mechanism that had blocked them is worth recording: **the LCSC
`datasheet.lcsc.com/lcsc/<id>_<part>_<code>.pdf` URLs now serve an HTML landing
page**, to a browser User-Agent as well as to a plain fetch. The real document
is reachable from a CDN link embedded in that page's own markup
(`datasheet.lcsc.com/datasheet/pdf/<hash>.pdf`), which is what was used.

- **`KH-SMA-KE-Z`** — fetched independently and hashes to
  `05257621aa124d9a077a47230c4ffc0030b23477c0e5c5e694abffa5f8daee08`, **byte
  for byte the value this README recorded as the expected hash on 2026-07-27**
  from the sibling project's read-only copy. That is an independent
  confirmation, not a copy: the file committed here came off the vendor CDN
  today and agrees with a hash recorded before it was fetched.
- **`0402WGF2200TCE` / `0402WGF4700TCE`** — one document serves both: the
  UniOhm *Thick Film Chip Resistors — 1-CHIP SERIES* sheet, V.3 Feb.12,2019,
  9 pages, sha256 `11cd644d…`. It is committed once, with the part that is
  actually on the board. Every electrical fact in both dossiers is now CITED
  from that document (ordering-code decode section 3 p2, tempco section 4.8 p5,
  rated power / voltage / temperature section 5 p5) instead of from an LCSC
  parametric record.
- **`KT-0603R` and `TS-1187A-B-A-B`** — added 2026-07-28 and fetched by the
  SAME mechanism, which is the third and fourth independent confirmation that
  it works: both `www.lcsc.com/datasheet/lcsc_datasheet_*.pdf` URLs served HTML
  landing pages (50,921 and 51,906 bytes, confirmed with `file`), and the real
  documents came off the `datasheet.lcsc.com/datasheet/pdf/<hash>.pdf` links
  embedded in that markup. `KT-0603R` hashes to `a3bac1cc…` (11 pages, Hubei
  KENTO's own 承认书 / spec-for-approval, Rev A.0, 2018-12-06);
  `TS-1187A-B-A-B` to `64b75233…` (1 page, XKB's own drawing TS-1187A-X-X-X rev
  A0). The switch drawing is corroborated from an unexpected direction: KiCad's
  `SW_Push_1P1T_XKB_TS-1187A` footprint carries
  `(descr "... http://www.helloxkb.com/public/images/pdf/TS-1187A-X-X-X.pdf")`
  — **the footprint and the datasheet name each other**, which is why its land
  matches to zero deviation.

## Deviations from `contracts.md`

1. **FIFTEEN `part.yaml` exist for parts not yet on a BOM** (four at the
   sourcing spike, thirteen on 2026-07-28, fifteen after the stage-4 back-fill
   the same day). The contract forbids "a `part.yaml` for a part not on the
   board (stale after a swap)".
   These are pre-BOM by design: the D-SPEC gate requires the sourcing spike to
   VERIFY the spec-critical part before architecture, precisely so stage 2
   never DISCOVERS feasibility. **The deviation is NARROWER than it was, not
   wider**: at the spike it was four dossiers covering an unknown fraction of
   an undecided design; it is now one dossier per part the design NAMES.
   ~~so the set can be checked against `DETAIL_DESIGN.md` §8 rather than against
   nothing.~~ **THAT SENTENCE WAS THE DEFECT — struck, not deleted, because it
   is the record of how two parts went missing.** §8 is a VALUE index, and a
   part with no value is absent from it; see deviation 8 for the denominator
   that actually works. The pre-BOM window is what remains, and it closes when
   a BOM exists. **Before bring-up:** each must appear in the BOM or its
   directory must be deleted, and the swap noted in `01_docs/CHANGELOG.md`.

2. **`part.yaml` files were EDITED without a datasheet revision change.** The
   contract says "edit a `part.yaml` only when the datasheet REVISION
   changes". Two were edited on 2026-07-28: `0402WGF4700TCE` (re-labelled
   `status: rejected_alternate`, datasheet provenance resolved from OWED to a
   real hash, `asserts:` emptied) and this README. The reason is a DESIGN
   decision, not a document change, and it is registered here rather than
   done quietly.

3. **`0402WGF4700TCE` keeps its dossier despite being a rejected candidate.**
   The contract says a rejected candidate keeps its REASON and not its binary,
   and normally not its dossier either. This one was PRIMARY for a day, its
   numbers are cited in `01_docs/journal/02_parts.md`, and deleting it would
   leave those citations dangling and erase the record that the primary
   changed. It carries `status: rejected_alternate`, an empty `asserts:` (an
   assertion that can never reach a board ref should read UNREACHED, not PASS)
   and **no committed PDF** — the binary lives with the part that is on the
   board.

4. ~~**`footprint:` names do not exist yet** for `PE42482A-X` and
   `KH-SMA-KE-Z`.~~ **CLOSED 2026-07-28.** Both `.kicad_mod` are AUTHORED into
   `03_src/lib/pluto_rx2_8way.pretty/` from the vendor land drawings — pSemi
   Figure 23's RECOMMENDED LAND PATTERN inset (DOC-75785-4 p21) and the
   Kinghelm sheet-2/2 PCB inset (2021.08.10). Neither was copied; the sibling's
   `pluto_cal_switch:SMA_Vertical_5.08sq_D1.4` is declared in its `part.yaml`
   and emitted by nothing, so there was no source to copy even had it been
   allowed. Verified by an INDEPENDENT parser that re-derives every dimension
   from the emitted file text and compares it against the drawing numbers
   re-typed by hand (canon M1), plus a `pcbnew.FootprintLoad`: **48 geometry
   properties + 6 silk/courtyard clearances, all PASS.**
   Two facts the footprints now CARRY rather than leave to the board:
   the SMA's `>= D3.5` bottom/inner-plane antipad, encoded as a **0.80 mm local
   clearance on pad 1** (1.9 + 2 x 0.8 = 3.5) so it opens in every ground plane;
   and `zone_connect 2` (SOLID) on the four ground posts, because the posts ARE
   the launch return path and a thermal spoke is not one.
   **And the stock KiCad footprint would have been WRONG**, which is why this
   was authoring and not a lookup: `Package_DFN_QFN:QFN-24-1EP_4x4mm_P0.5mm_
   EP2.65x2.65mm` is IPC-generated with 0.85 mm pads at r = 1.95 and a 2.65 mm
   EP, against the vendor's 0.60 mm pads at r = 1.90 and a 2.75 mm EP.
   `03_src/floorplan.yaml` now binds `libraries: [03_src/lib, /usr/share/kicad/
   footprints]` with the project library FIRST for exactly that reason.
   **AND THE 2026-07-28 BACK-FILL WENT THE OTHER WAY — NO FOURTH FOOTPRINT IS
   OWED**, which is worth recording because "the stock land is wrong" had been
   true three times running on this board. Both new parts were checked
   pad-by-pad against the vendor drawing by an independent parser (re-deriving
   from the `.kicad_mod` TEXT and confirmed against `pcbnew.FootprintLoad`):
   `Button_Switch_SMD:SW_Push_1P1T_XKB_TS-1187A` is XKB's own recommended land
   **dimension for dimension, 8 of 8 exact, delta 0.0000 on every one** — it is
   not an IPC generation that happens to agree, and KiCad's `(descr ...)` names
   the very drawing committed here. `LED_SMD:LED_0603_1608Metric` matches the
   KENTO land on the dimension that matters — **inner gap 0.700 vs 0.70 CITED,
   exact** — with only the standard IPC toe/side expansion outward
   (0.875 × 0.95 pads vs 0.70 × ~0.70), and the pad fully covers the termination
   band (pad |x| 0.350–1.225 against band |x| 0.50–0.80).

5. ~~**Two thirds of the board still has no dossier.**~~ **CLOSED
   2026-07-28.** All nine remaining dossiers written and merged. The set is
   graded, not merely present: **S-VER**, **P-ESC 13/13** (**15/15** after the
   stage-4 back-fill — `escape_check.py` over every `part.yaml` prints
   `P-ESC PASS: 15/15 part.yaml graded, 0 problem(s)`), **P-TIER PASS at
   `jlc_4layer_advanced`** (both new parts escape at `jlc_2layer_default`, three
   tiers of headroom), **P-LAYOUT 8/8 in-scope parts carry a datasheet
   `layout:` block** (still 8/8 — neither new part is in P-LAYOUT scope, and
   both carry a `layout:` block anyway). `U_LDO` = `MCP1755S-3302E/DB` clears all three derived
   constraints (500 mV / +17.6 V / 62 °C/W against 1.23 V / 10.3 V / 195 °C/W),
   so `03_src/rules/power_tree.yaml` now declares the 3V3 rail and **E-TOPO
   PASSES** instead of turning red.
   **Two of the three constraints MOVED while the set was being built, and both
   moves came from OTHER parts** — which is the argument for merging centrally
   rather than trusting nine independent dossiers:
   - dropout ≤ 1.35 V became **≤ 1.23 V**, because `F_IN` (R_1max 0.75 Ω) and
     `FB_IN` (DCR 0.06 Ω) drop **121.5 mV** at 0.15 A and the 1.35 V was
     measured at the USB-C VBUS pin, not at the regulator. This CHANGED THE
     ANSWER: AMS1117-3.3, the obvious JLC-Basic default, is 1.3 V max and
     passes 1.35 while failing 1.23.
   - `V_IN` abs max ≥ 10 V became **≥ 10.3 V**, because the 5.0 V-standoff TVS
     the constraint was derived from was rejected at selection (VBUS max
     5.25 V sits above its 5.0 V working voltage) and `SMBJ6.0A` clamps at
     10.3 V. A part rated exactly 10 V is now out of spec.

6. **A THIRD footprint became OWED while closing deviation 4.**
   `USB_C_Receptacle_HRO_TYPE-C-31-M-12A`. KiCad ships
   `Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12` and it does NOT match
   this vendor's RECOMMEND P.C.B LAYOUT — measured pad by pad, the pad-centre
   to alignment-hole distance differs by **0.375 mm** and the SMT pad length by
   0.31 mm, so the contact tails would land off-centre and cover only ~0.95 of
   the sheet's 1.14 mm pad at the heel. **Ruled out as an M-12-vs-M-12A variant
   difference**: the base M-12 sheet was fetched and its recommended layout is
   dimension-for-dimension identical to the M-12A's. Two HRO sheets two years
   apart agree with each other and disagree with KiCad.

7. **Directory names sanitise `/` out of the MPN.** `1206L050-24WR` holds
   `mpn: 1206L050/24WR`, and `MCP1755S-3302E-DB` holds
   `mpn: MCP1755S-3302E/DB`. The contract says `part.yaml.mpn == directory
   name`; a `/` cannot be a path component. The `mpn:` field is authoritative
   and is the string to type at a distributor. This is established fleet
   practice, not a local invention — `MCP23017-E/SS`, `LM5116MHX/NOPB`,
   `SMD2920-700/16N`, `1277AS-H-2R2M=P2`, `KNTC0603/10KF3950` and
   `10FDZ-BT(S)(LF)(SN)` all sit in directories with the punctuation removed.

8. **TWO PARTS WERE MISSED BY THE STAGE-2 SWEEP, AND THE REASON IS A
   DENOMINATOR, NOT AN OVERSIGHT.** The indicator LED (`KT-0603R`) and the
   pushbutton (`TS-1187A-B-A-B`) had no dossier until 2026-07-28, and were found
   at **stage 4** — late enough that the schematic's exported netlist already
   carried `LED_PWR`, `LED_ST`, `SW_BOOT` and `SW_RUN` with **empty footprint
   fields and the literal placeholder values `__LED_LCSC__` / `__SW_LCSC__`**,
   which is a hard error at `generate_board_generic.py`
   ("has no footprint FPID in the netlist and no 02_parts ... add
   `02_parts/<part>/part.yaml` with a `footprint:` line").

   **THE LESSON IS THE DENOMINATOR AND IT IS REUSABLE.** The stage-2 sweep
   declared itself complete against **`DETAIL_DESIGN.md` §8's value index** —
   see deviation 1, "the set can be checked against `DETAIL_DESIGN.md` §8 rather
   than against nothing", which is exactly what was done and exactly what was
   wrong. §8 lists **`R_LED1`, `R_LED2` | 680 Ω | §5 — 1.91 mA**: the
   **BALLASTS**, not the things they ballast. **At sweep time there was no row
   anywhere in `01_docs/` for the indicator LEDs as PARTS, and no mention of a
   button, BOOTSEL or RUN outside a netclass table in `ARCHITECTURE.md` §104.**
   (§5 gained `SW_BOOT`/`SW_RUN` and `R_BOOT` rows later on 2026-07-28, as part
   of this same discovery — the document has been amended, which is why this
   entry states the state that produced the miss rather than today's.) A value
   index answers "what value does each component have"; it does not answer "what
   components are there", and a part with no VALUE — an LED, a switch, a
   connector — can be absent from it while being present on the board. **The
   indicator LEDs are still absent from §8 today**, which is the point: the
   index is not the wrong document, it is the wrong KIND of document for this
   question.

   **The right denominator is the union of `03_src/floorplan.yaml`'s seeded
   refdes and `03_src/rules/nets.yaml`'s declared nets**, because those are the
   two artifacts the generator actually consumes. Both named these parts before
   the sweep ran: the floorplan seeded `LED_PWR`, `LED_ST`, `SW_BOOT` (and later
   `SW_RUN`); `nets.yaml` declared `LED_PWR`, `LED_STAT`, `BOOTSEL_N`, `RUN_N`.
   Checking a parts folder against prose is checking it against an author's
   memory; checking it against the floorplan and the netlist is checking it
   against the thing that will fail.

9. **THE `value:` ASSERT CONVENTION AND THE BOARD DISAGREE, AND NOTHING SAYS SO
   TODAY.** All fifteen dossiers assert `value: equals: <MPN>`. This board's
   schematic puts the **LCSC CODE** in `value` — measured 2026-07-28 from
   `06_build/netlists/pluto_rx2_8way.net`: `U_ESD` "C7519", `D_TVS` "C83270",
   `FB_IN` "C3716677", `F_IN` "C2154056", `U_LDO` "C638611", `Y_XTAL`
   "C20625731", `U_FLASH` "C97521" (passives carry the value instead: `R_T1`
   "220Ω"), and the two placeholders this back-fill exists to resolve read
   literally `__LED_LCSC__` and `__SW_LCSC__`. Every one of those asserts is
   currently **inert** for an unrelated reason — `part_facts_check.py` decodes
   `equals:` through a NUMERIC-ONLY `parse_si()`, so an MPN string grades
   nothing — which is why the disagreement has never surfaced. The day that
   checker gains a literal-string fallback, all fifteen go red at once. That is
   **one** board-owner decision (move the asserts to C-codes, or make the BOM
   Comment carry the MPN), not fifteen per-dossier ones, so the two new dossiers
   deliberately followed the house convention rather than diverging quietly.

## OWED measurements — named, not buried

| owed | why it matters |
|---|---|
| **port-to-port isolation across ten SMA barrels on one laminate** | it bounds the AoA leakage budget from BELOW, independently of the switch. A −21.5 dB switch behind a −18 dB connector field is a −18 dB board. The vendor sheet does not touch it. ADR-0005's all-ports-terminated dark state exists to measure it |
| SMA launch **dissipative** loss | the vendor publishes VSWR only, so `DETAIL_DESIGN.md` §2's 0.10 dB per launch is a mismatch-loss LOWER BOUND |
| `C_p` for the 0402 arms | CITED for the 0402 wrap-around class (Vishay TN 60107 Table 1 p1), **ESTIMATED 0.04 ± 0.02 pF for this thick-film part**. The 6 GHz tap tilt scales linearly with it — which is the whole reason the arm is split |
| RP2040 pad output impedance | ESTIMATED 25 ± 10 Ω at 12 mA. The 47 Ω series value holds the switch's absolute-maximum bound across the whole bar, which is what makes the estimate tolerable |
| **`KT-0603R` `pad1_net_polarity` assert — NOT SHIPPED, deliberately** | The graded kind reads pad 1's net from the netlist and matches it against a negative-net regex. Whether that passes depends on **where the ballast sits**, which was undecided on 2026-07-28: ballast on the ANODE side puts pad 1 on GND and the assert is a real gate; ballast on the CATHODE side puts pad 1 on `LED_PWR`/`LED_STAT` and the assert **fails on a correctly oriented board**. Shipping a coin-flip gate is how waiving becomes a habit. **To close: once the topology is fixed, add three lines to `KT-0603R/part.yaml` — `- assert: pad1_net_polarity / pad: 1 / polarity: negative` — iff the cathode returns directly to GND.** The unconditional half (pad 1 IS the cathode) is already in `pins:` and gotcha 1 |
| `KT-0603R` forward voltage at the ACTUAL operating point | The sheet characterises Vf only at **20 mA**, and the ballast runs the part at ~1.9 mA — 10× below it, where Vf is lower. There is **no Vf-vs-If curve and no Iv-vs-If curve** in the document (§7 has one spectrum plot). Current is therefore bounded, not known: **1.32 mA ≤ I ≤ ~2.6 mA**, the lower bound CITED from the 20 mA Vf max and the upper ESTIMATED from the low-current droop. Margin to the 25 mA DC limit is ≥ 9.6×, so nothing is at risk — but §5's "3.8 mA" line item is a nominal, not a maximum |
| `KT-0603R` moisture level | §11.4.2 states a **7-day floor life** at ≤30 °C/60 % RH and a bake to recover, and **never states a JEDEC MSL level**. 168 h is MSL 3's floor life, but the number is not the level and this dossier will not infer one. Not live while JLC supplies the reel; live the moment the part is hand-supplied — get it off the reel label |
| `TS-1187A-B-A-B` contact bounce | **Not specified anywhere in the one-page drawing** — no time, no envelope, no method. Irrelevant for `BOOTSEL_N` (sampled once across a held press); **real for `RUN_N`**, which is the RP2040 reset. `DETAIL_DESIGN.md` §5 and §8 list **no capacitor on RUN**. Either one is added or the omission is dispositioned |
| `TS-1187A-B-A-B` minimum switching current | The 50 mA/12 V rating is a **maximum**; the sheet gives no dry-circuit minimum and no gold-plating claim (its item table says fine-silver contacts, silver-plated terminals — LCSC's parametric says "Gold", and the drawing wins). The board runs the contact at ~0.3 mA, so reliable wetting is DERIVED from the switch class, not CITED |
| `TS-1187A-B-A-B` actuator height vs the enclosure | H = 1.5 mm leaves the plunger **0.3 mm proud** of the cover — a fingernail/tool button, not a fingertip one. Fine for a bench instrument, wrong behind a panel. The fix is a height code on the identical land (C318889 1.7 mm, C318887 2.5 mm, …), but **every taller code is `extended` tier** — the 1.5 mm part is the only `base` one |

## Rejected candidates — no PDF committed, reason recorded

Per the contract, rejected candidates get the reason, not the binary. The full
reasoning is in the D-SPEC spike report; the one-line verdicts:

| candidate | LCSC | verdict |
|---|---|---|
| `BGS12WN6` (7x SPDT tree) | C1854968 / C27749420 | **STOCK 0 on every catalogue entry**, and the tree's worst-case isolation is one switch's, not three |
| `BGS12P2L6E6327` (7x SPDT tree) | C3312945 | in stock (1225) but no published RF row at 70 MHz or 6 GHz; 3.4 V VDD max |
| `PE42462A-X` | C22419301 | **SP6T, not SP8T** — datasheet cover, `UltraCMOS SP6T RF Switch, 10 MHz-8 GHz` |
| `HMC321ALP4E` | C1526237 | **stock 0** ($34.90/1, would be self-supplied); and GaAs IL is 1.7 typ / **1.8 max** even in the DC-2.0 GHz row vs PE42482's 1.1 max at 70 MHz. **NOT a negative-rail part** — an earlier note in this project's own spike brief said so and was WRONG: the datasheet title reads `GaAs MMIC SP8T NON-REFLECTIVE POSITIVE CONTROL SWITCH, DC*-8 GHz`, single +5 V bias, 0/+5 V TTL control, integrated 3:8 decoder. Rejected on stock and loss, never on supply. Also needs 9 DC blocking caps (RFC + 8 RF ports) whose value sets the low corner |
| `HMC322ALP4E` | C1558622 | stock 0 both codes |
| `SKY13418-485LF` | C150871 | 100 MHz-3.8 GHz — fails both band ends |
| `SKY13322-375LF` | C151465 | **SP4T**, not SP8T |
| `PE42582A-X` | C500479 | qualifies on spec; stock 7 at $14.91 — kept as an alternate, not primary |
| `ADRF5040BCPZ` | C579319 | SP4T; stock 7+20 |
| `MASW-008322` | C3304131 | SPDT; stock 3 |
| `0402WGF4700TCE` | C25117 | **470R single-arm pickoff — the primary until 2026-07-28.** Its arithmetic is correct; it loses because a single arm carries the full 0402 shunt parasitic, so its 6 GHz tap tilt is +1.69 dB with a **2.73 dB-wide uncertainty band** against +0.43 dB / 0.83 dB for the split arm. Dossier KEPT (deviation 3) |

## Stock, MEASURED 2026-07-28 — and the pool trap

Against the **JLCPCB assembly parts library** (`jlc_stock_check.py`), which is
the pool a PCBA order allocates from:

| LCSC | MPN | library | stock | note |
|---|---|---|---|---|
| C25091 | 0402WGF2200TCE | base | **995,162** | and see the pool trap below |
| C25117 | 0402WGF4700TCE | base | 1,871,945 | rejected alternate |
| C5121458 | PE42482A-X | extended | **1,498** | |
| C504007 | KH-SMA-KE-Z | extended | **18,585** | 19,136 on 2026-07-27 — −551 in a day |
| C638611 | MCP1755S-3302E/DB | extended | **86** | **THINNEST LINE ON THE BOARD.** The T&R twin MCP1755ST-3302E/DB (C111176) is **stock 0**, so the tube code is the only buyable one |
| C2040 | RP2040 | extended | 65,244 | |
| C97521 | W25Q128JVSIQ | **base** | 104,716 | |
| C20625731 | ABM8-272-T3 | extended | 17,562 | |
| C5337088 | TYPE-C-31-M-12A | extended | **84** | second-thinnest, and the board's only USB connector |
| C7519 | USBLC6-2SC6 | extended | 29,868 | |
| C2154056 | 1206L050/24WR | extended | 4,209 | |
| C83270 | SMBJ6.0A | extended | 9,746 | C113976 is the ledger's catalog-verified unidirectional twin |
| C3716677 | BLM21SP601SN1D | extended | 6,368 | |
| C2286 | KT-0603R | **base** | **7,593,490** | deepest line on the board. x2 (`LED_PWR`, `LED_ST`) |
| C318884 | TS-1187A-B-A-B | **base** | **1,361,371** | x2 (`SW_BOOT`, `SW_RUN`). The only `base` height code in the TS-1187A family |

**Five `jlc_stock_check.py --json` runs, all five VERDICT lines PASS**, cached
in `06_build/cache/stock_{ldo,mcu,usb,prot,hmi}.json`. The verdict line is the
gate (canon A-STOCK) and it was READ, not assumed — a missing or unparseable
verdict is a FAIL, not a skip. The 2026-07-28 back-fill run printed
`PASS: 2/2 coded BOM lines have stock >= 5 x qty (0 with problems); 0/2 lines
carry NO LCSC and were NOT graded by this tool`, and its sidecar records
`"verdict": "PASS"` with both lines `"type": "base"`.
(`06_build/` is gitignored by this project's own `.gitignore`, so these caches
are measured and readable but **not tracked** — the same as the four before
them, and consistent with the contract's "stock lives in `06_build/cache/`,
never in a `part.yaml`".)

**The trap, worth the line it costs:** the LCSC RETAIL product page for
**C25091 reports stock 0** on the same day it shows 995,162 in the assembly
library. Two different pools. Measuring the retail page is measuring the state
of a catalog record, not the state of the part (canon M-QUOTE) — and this is
the code the whole confirmed pickoff design depends on, so a casual retail
check would have read as a blocker that is not one. It WOULD be a blocker if
the part ever had to be hand-supplied.

**AND THE TRAP WAS RE-CHECKED ON THE TWO PARTS ADDED 2026-07-28, WHERE IT DOES
NOT FIRE — which is why both pools get recorded rather than one.** Both new
lines are `base`, the same class as C25091, so the retail page was read for
each: **C2286 shows 4,975,100 retail against 7,593,490 assembly**, and
**C318884 shows 1,125,780 retail against 1,361,371 assembly**. Deep in both
pools, different numbers in each, no zero anywhere. A trap that fires on one
base part and not on two others is a property of the CATALOG RECORD, not of the
tier — so the rule is to read the pool you will actually order from, every time,
not to learn "base parts read 0 on retail".

(These figures are OBSERVATIONS with a date, recorded here because the folder
status is what they describe. The volatile numbers a build consumes live in
`06_build/cache/`, never in a `part.yaml`.)
