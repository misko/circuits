# ORDER README — cooksense MAIN board **v1.7** (project smc0985-cooksense)

---

# ⚠️⚠️ THE BOARD DOES NOT FUNCTION WITHOUT THE `J_ESTOP` SHORTING PLUG. ⚠️⚠️
# ⚠️⚠️ THE PLUG BRIDGES CIRCUITS **2–3**. NEVER **1–2**. ⚠️⚠️

**Read this before you unpack anything else. With `J_ESTOP` open the board is
INERT BY DESIGN — no relay will close, no key will be emulated — and that is
INDISTINGUISHABLE FROM A DEAD BOARD to a technician who does not know.**

---

# 🛑🛑 AND BEFORE YOU ORDER: ONE BOM LINE CANNOT BE BOUGHT TODAY. 🛑🛑
# 🛑🛑 GO READ **§5-0** FIRST. 🛑🛑

    SOURCING: BLOCKED-1 (C265111; measured 2026-07-30, stock 5 / MOQ 21)

**THE BLOCKER IS THE MOQ, NOT THE STOCK, AND IT HAS NEVER ONCE BEEN THE
STOCK.** `C265111` (JST `SM08B-GHS-TB(LF)(SN)`, `J_THERM_A`/`J_THERM_B`, 2 per
board) has read **0 → 5 → 0 → 5 → 5** across five measurements in 48 h on a
board whose md5 never moved, while `minPurchaseNum` has read **21** at every
single one. 21 exceeds every stock reading ever taken here, so **the line
cannot be bought AS SEALED at any quantity on any of those days.** Anyone who
re-reads 5 and calls it recovery has watched the wrong number. **Re-measure on
order day; carry none of these readings.** Details and the escape routes: §5-0.

*Fifth reading MEASURED 2026-07-30 21:29 local (2026-07-31T04:29Z), direct
`urllib` against `selectSmtComponentList`, with both controls in the same run
(POSITIVE `C6186` → 1,615,823; NEGATIVE `C99999999` → NO_EXACT_MATCH over 25
fuzzy rows). **This project dates in LOCAL time** — see
`03_src/cooksense/rules/assembly.yaml`'s date-convention note; the UTC instant
is kept in prose, never in a date field that three files join on.*

    SECOND WATCH ITEM — NOT BLOCKING TODAY, FALLING FASTEST ON THIS BOM:
    C587657 (Molex 436500224, J_PWR, 1/board)  130 -> 80 -> 70 -> 70
      MEASURED 2026-07-30, same run, same controls: stock 70, MOQ 1.
      SINGLE-SOURCE with NO drop-in fallback -- the only listed alternative,
      Molex 43650-0215 (C293740), is THROUGH-HOLE, so it changes the
      footprint and therefore the CPL and the copper. Re-specify BEFORE it
      reaches the build quantity, not after it reaches zero.

# ⛔⛔ AND v1.7 IS **NOT SEALED**. THIS IS A CANDIDATE, NOT A RELEASE. ⛔⛔

**Re-gate 3, 2026-07-30 — ALL THREE P0s ON THE 3V3 RAIL ARE CLOSED (ADR-0026 +
ADR-0027), AND NONE OF THEM WAS COPPER.** The board's md5 has not moved
(`9f4fd5fae810f40a52b1035df727243c`) through any of the three rounds.

1. **the declared LOAD** omitted four switched sensor rails — closed, ADR-0026;
2. **the declared thermal CEILING** was a 25 °C figure on a 75 °C board —
   closed, ADR-0026 (`pdiss_max_mw` 1200 → **497**, derived);
3. **the declared SERIES RESISTANCE counted three named components and none of
   the board's own copper** — closed, **ADR-0027**.

**On (3), the number is WORSE than the lens that found it reported, and that is
said out loud rather than quietly adopted.** The re-gate-2 topology lens
measured 109 mΩ of omitted copper by a minimum-resistance path walk; an exact
DC nodal solve of the whole 5 V chain measures **137.79 mΩ** (the lens took the
two eFuse IN-pad routes as disjoint parallel branches, and allowed 0.5 mΩ per
via where a 0.15 mm barrel at 18 µm plating is 3.5 mΩ). **No 5 V net has a zone
anywhere on this board** — independently re-confirmed — so tracks are the whole
conductor.

**TWO ERRORS POINTED IN OPPOSITE DIRECTIONS AND WERE NOT ALLOWED TO CANCEL:**
the omitted copper costs **−52 mV**, the fictitious 0.50 A board current the old
`vin_min` was derived at gives back **+26 mV**. Carried separately:

    vin_min  4.754 -> 4.728 V        headroom  +55 mV (claimed) -> +29 mV (MEASURED)
    E-TOPO   headroom 1329 mV vs dropout 1300 mV -> PASS, RAW_EXIT 0

The file's stated robustness envelope — *"It still passes at 0.60 A (+37 mV)"* —
is **DELETED because it is FALSE**: at 0.60 A the real answer is −35.8 mV, and
break-even is **0.4910 A**. One new operating constraint falls out and is now
**§7a-3**: the two SHT45 heaters must never fire coincidentally at the 200 mW
level. See `verification/0027-*.md`.

**There is still no orderable cooksense board.** `cooksense-v1.6-2026-07-27`
remains the newest SEALED release and it is DO-NOT-ORDER (pin-out-12 relay
land). Do not build from any sealed release, and do not build from this
directory either.

---

**`C265111` (`J_THERM_A` / `J_THERM_B`) reads stock 5 against a minimum order
quantity of 21** — so it is not *short*, it is **unbuyable at any quantity**.
**§5-0 carries the live numbers, the measured drop-in substitute, exactly which
file to change, and the one physical check a substituting buyer owes.**

Everything below is the candidate's own documentation and every gate number in
it was measured. Read it as a work-in-progress record, not as order paperwork.

---

**`C265111` (`J_THERM_A` / `J_THERM_B`) reads stock 5 against a minimum order
quantity of 21** — so it is not *short*, it is **unbuyable at any quantity**.
This was the blocker for eight successive passes and it is no longer the
blocker: under the two-claim vocabulary a sourcing red does not veto a design.
**§5-0 carries the live numbers, the measured drop-in substitute, exactly which
file to change, and the one physical check a substituting buyer owes.**

`J_ESTOP` is a **JST SH `SM03B-SRSS-TB`, LCSC `C160403`, 1.00 mm pitch, 3
circuits**. It is the ONLY 1.00 mm connector on this board; everything else in
the pod family is JST GH at 1.25 mm and `J_MODE` is JST ZH at 1.50 mm. MEASURED
on this archive's own `source/cooksense.kicad_pcb`:

| circuit | net | pitch from previous |
|---|---|---|
| **1** | `GND` | — |
| **2** | `3V3` | 1.0000 mm |
| **3** | `ESTOP_RAW_IN` | 1.0000 mm |

**The plug must bridge circuit 2 to circuit 3** — `3V3` to `ESTOP_RAW_IN`. That
is what asserts `ESTOP_OK` and lets the safety AND-chain leave its restrictive
default.

**A 1–2 bridge shorts `3V3` STRAIGHT TO `GND`.** Circuit 2 is the **main 3V3
logic rail** — the AMS1117-3.3's output, the rail that feeds every gate, the
shift register, the ADC, the expander and the watchdog. Bridging 1–2 collapses
the whole board's logic supply into a dead short at the LDO output, and the only
thing between you and it is the AMS1117's internal short-circuit protection.
**Get this wrong and you do not get a non-working E-stop; you get a board whose
logic rail is shorted every time the plug is inserted.**

> **A CORRECTION, recorded rather than smoothed over.** An earlier statement of
> this warning described the 1–2 pair as shorting *"a sensor rail behind an
> AO3401A"*. Re-measured from the netlist on 2026-07-30, that is WRONG and it is
> wrong in the reassuring direction: circuit 2 is `3V3`, the LDO's own output —
> **not** one of the four `3V3_SW_*` rails that sit behind an AO3401A load
> switch. There is no series FET in the path. The hazard is larger than the
> sentence it replaced, not smaller.

**Why the pinout is a SAFETY MECHANISM and not a convention.** The plug is a
loose object that travels; the connector it might be forced into is not.
MEASURED pitches on this board: SH 1.0000 mm (`J_ESTOP`), GH 1.2500 mm (all five
pod housings), ZH 1.5000 mm (`J_MODE`). A 3-circuit SH bridge presents contacts
at 0 / 1.000 / 2.000 mm; a GH shroud's posts sit at 0 / 1.250 / 2.500 mm.
Circuit 2 misaligns by 0.250 mm and **circuit 3 by 0.500 mm — circuit 3 is the
one circuit that cannot align in any foreign shroud on this board**, which is
exactly why the sense line was put there. A shorting plug whose live pair is
2–3 cannot COMPLETE its short anywhere else. A 1–2 plug could.

**Sourcing the plug.** `SHR-03V-S-B` / `C268100` read LCSC stock **0**. Stocked
equivalents, all 3-circuit 1.00 mm SH-family housings: `C2909166` (HDGC1002H-3P),
`C2962274` (HC-1.0-3Y), `C338906` (A1002H-3P), `C392108` (APSHR-03V-S); contacts
`C263995` (SSH-003T-P0.2-H). **The SH crimp accepts AWG #32–#28 only.** For the
~5 mm bridge inside the plug that is irrelevant. For any FUTURE field run to a
real E-stop button it is not: splice #28 to #24/#26 INSIDE the enclosure and run
the heavier gauge to the button.

**When a real E-stop is fitted, the plug comes out and nothing else changes** —
that is the whole point of ADR-0025's asymmetry. No copper revision is needed.

---

> ## RELEASE v1.7 — A NEW BOARD. THE FIRST cooksense RELEASE THAT IS NOT DO-NOT-ORDER.
>
> **v1.0 through v1.6 are ALL DO-NOT-ORDER** and remain so. They carry the
> pin-out-**12** reed-relay land (`Relay_StandexDIP_1A_pinout12`); the part that
> exists is pin-out **13**. Nothing about those six releases is orderable and no
> amount of documentation changes that. **v1.7 is a new board, not a re-issue:**
> `source/cooksense.kicad_pcb` is md5 `9f4fd5fae810f40a52b1035df727243c`, and
> every gerber, drill, BOM row and CPL row in `fab/` is derived from it.
>
> **What changed since v1.6, all of it material:**
>
> 1. **THE RELAY LAND IS PIN-OUT 13** (`Relay_StandexDIP_1A_pinout13`), and the
>    part on the BOM is **`DIP05-1A72-13L`**. This is the defect the whole
>    DO-NOT-ORDER banner existed for.
> 2. **THE COIL DRIVER IS NOW A DMOS ARRAY — `TBD62083AFWG` (`C165895`),
>    replacing the ULN2803A Darlington (ADR-0023).** The reed pull-in margin at
>    the brief's +70 °C envelope top went from **−0.340 V to +0.494 V**. The
>    Darlington's V_CE(sat) crossed over at **45.7 °C worst case — below the
>    brief's own ≤50 °C NORMAL band** — i.e. six sealed releases could not
>    guarantee that their relays would close.
> 3. **`J_DOOR` IS DELETED FROM THE NETLIST** — not marked DNP, REMOVED, together
>    with `R_DOORPD`, `R_DOORS`, `D_DOOR` and `R_DOOROKPD` (ADR-0025). The user
>    has no access to the appliance's door signal and never will. `BRIEF.md` §3's
>    "Door:" clause is WITHDRAWN and the amendment is written out in full in the
>    ADR. `DOOR_OK` leaves the logic; `OS_CLR_N = ESTOP_OK · STOP_REQ_N`.
>    **Everything §2-0 and §2a of the v1.6 README said about a door harness is
>    void — there is no door connector to build a harness for.**
> 4. **`J_ESTOP` STAYS POPULATED, BEHIND THE REMOVABLE KEYED SHORTING PLUG** —
>    see the banner above, which is the loudest thing in this document.
> 5. **THE KEYPAD ISOLATION DRU RULE WAS REPAIRED.** `keypad_isolation_6mm`
>    carried a `B.NetName != ''` conjunct, so UNNETTED copper was exempt BY
>    CONSTRUCTION — and the nearest unnetted copper to a `KEYPAD_ISO` net was
>    `J_KEY_MATRIX.MP`, the keypad connector's own shell tab, i.e. the exact
>    thing the rule was written for. The rule could not fire on its own subject.
>    Repaired, it now measures **0 violations** with a named-refdes exemption,
>    and the 67/67 pre-fix pairs were all `J_KEY_MATRIX.MP` against 100 %
>    `KEYPAD_ISO`-class far sides — **zero domain crossings. The barrier held;
>    only the rule was blind.**
> 6. **TWELVE COMB SLOTS WIDENED 0.600 → 1.000 mm** against JLCPCB's own
>    published minimum slot width. At 0.600 mm they were **40 % under the fab's
>    floor** and would have been quoted as unroutable or silently widened.
>
> **The gate set, re-measured on 2026-07-30 against THIS archive, unpiped:**
> DRC **0 violations / 0 unconnected / 0 schematic parity**;
> `policy_audit` **FAIL=0, PASS=28, WAIVED=6, HUMAN=6, N-A=5**;
> E-INV **167/167**; E-ADR **11/11**; S-COUNT **4/4 over 239 refdes**;
> F-LEGIBLE **60 checks, 0 findings**; A-ROT **64 measured authority rows**;
> `jlc_twin` **exit 0, bodies 208/208**; M-BOM **PASS, 208 coded**.
> Every exit code and every verdict line is in `verification/build_gates.md`,
> including the three that were non-zero and why each is dispositioned as it is.

---

> ## RELEASE v1.6 — DOCUMENTATION ONLY. THREE SAFETY-PAPERWORK DEFECTS, ONE OF THEM A WITHDRAWN CLAIM.
>
> **HISTORICAL. v1.6 is DO-NOT-ORDER (pin-out-12 relay land). Kept because its
> engineering notes — §10's cross-plug matrix and §7a's firmware invariants —
> are still true of v1.7 except where this document says otherwise.**
>
> **NOTHING ABOUT THE BOARD OR THE ORDER CHANGED.** `fab/`, `source/` and `3d/`
> are **byte-for-byte identical** to v1.5's — not re-plotted, not regenerated,
> carried across unopened, and that identity is ASSERTED by
> `release_freshness_check.py --docs-only-supersede`, which sha256s every file
> in both directions and FAILs on any difference, addition or omission.
> `source/cooksense.kicad_pcb` is still md5 `420445b5141dd1111eccab038c68511b`,
> the same file v1.3, v1.4, v1.5 and `04_kicad/` carry. **If you hold v1.5, its
> gerbers, BOM and CPL are still correct and orderable — order them. What you
> are missing is this document.**
>
> **WHAT CHANGED IS WHAT THIS DOCUMENT TELLS YOU TO DO**, and one of the three
> is a claim being WITHDRAWN rather than a note being added:
>
> 1. **SECTION 10 IS REWRITTEN, AND ITS OLD CENTRAL CLAIM IS WITHDRAWN.** Every
>    version up to v1.5 said the unkeyed 5-pin GH family is "J_MODE / J_DOOR /
>    J_ESTOP" and that "any single cross-plug is fail-safe". **There are FIVE
>    identical housings, not three** — `J_RH_AMBIENT` and `J_RH_EXHAUST` use the
>    same `C189896` SM05B-GHS-TB — and one of the twenty cross-plug combinations
>    is **not** fail-safe: an SHT45 pod harness in `J_MODE` puts the module's SCL
>    pull-up on `COIL_EN`, whose only hold is `R_COILENPD` **100 kΩ**, and
>    **energises the relay coil rail with all seven AND-chain terms AND the
>    Manual rail-cut bypassed**. Section 10 now names all five, publishes the
>    complete 20-cell matrix, and makes the labeling discipline the mitigation it
>    actually is.
> 2. **NEW SECTION 7a — TWO HOST-FIRMWARE INVARIANTS THE HARDWARE CANNOT
>    ENFORCE.** `REARM_N` must be PULSED: held low it forces the fault latch's
>    forbidden state and the latch permanently loses its memory. And `GPPUB` must
>    be written `0x00`: four AND-chain permissions have no pull resistor, and one
>    MCP23017 register write turns their failure mode from indeterminate into
>    deterministically PERMISSIVE.
> 3. **SECTION 13 GAINS FIVE DECLARED GAPS (19-23)**, including the measured
>    statement that **11 of the 18 safety-chain nets carry no restrictive default
>    at all**, and two stale source comments that a harness builder could act on.
>
> All three came from the 2026-07-27 adversarial audit, were RE-VERIFIED here
> against the archive's own `source/cooksense.net` by a method that shares
> nothing with the generator, and are written up with their numbers in
> `verification/crossplug_and_permission_defaults.md`. Two of the three
> re-verifications DISAGREED with the audit in detail; both disagreements are
> recorded there rather than smoothed over.
>
> **THE FIXES FOR ALL THREE ARE COPPER, AND COPPER IS A USER DECISION.** They are
> deferred to the next ELECTRICAL revision so that this release ships the same
> board v1.5 shipped. Read section 10 twice before you build a harness.

---

> ## RELEASE v1.5 — A BUYABLE BOM, A READABLE BOM, AND ONE GRADED RAIL THAT DOES NOT PASS
>
> **The BOARD is unchanged and the silkscreen still reads revision v1.3** — that
> is correct. `source/cooksense.kicad_pcb` is md5-identical
> (`420445b5141dd1111eccab038c68511b`) to v1.4's, v1.3's and `04_kicad/`'s;
> `fab/cpl.csv` and `fab/rotation_human_gate.txt` are byte-identical to v1.4's,
> so every rotation and coordinate in this document still holds. `3d/` and `pdf/`
> are byte-identical. Poured copper area is equal to six decimal places on all
> four copper layers — see `verification/copper_did_not_move.md`.
>
> **THIS RELEASE EXISTS BECAUSE v1.4's BOM CANNOT BE ORDERED, AND BECAUSE JLC
> COULD NOT READ IT.** Three things changed, all of them in the BOM:
>
> 1. **`C25744` -> `C60490`** (17 refs: R_BID0/1, R_DOORPD, R_ESTOPPD, R_EXPRST,
>    R_MODEPD, R_OE, R_OS2, R_REF0-7, R_TEMPOK). The 10 kΩ 0402 read
>    **`stockCount: 0`** live on 2026-07-27. It is the SAME code and the SAME
>    shortage that forced usb-hub-3s-v3 v1.11 the same day on a different board.
>    In: YAGEO **RC0402FR-0710KL**, stock 8 404 363, catalog `describe` string
>    **CHARACTER-IDENTICAL** to the part it replaces.
> 2. **`C25862` -> `C138040`** (R_ILM, the eFuse current-limit programming
>    resistor). Not out of stock — **unorderable in this quantity**:
>    `minPurchaseNum` 7463 against a `stockCount` that read 25 / 65 / 90 across
>    one afternoon. In: YAGEO **RC0402FR-071K2L**, stock 472 208, `describe`
>    again character-identical (the SPEC STRING was matched, not just the value —
>    a ±5% 1.2 kΩ also reads "1.2k" and would double the tolerance on a
>    protection part).
> 3. **The BOM is now legible to JLC's matcher.** v1.4 graded F-LEGIBLE **FAIL,
>    83 findings**: every coded row shipped a BLANK MPN (JLC leaves those at
>    "No Part Selected"), 26 Comments were the LCSC code repeated, and `Ω` shipped
>    with no UTF-8 byte-order-mark (a cp936 reader sees `惟`). v1.5: **0 findings,
>    56 checks**. 54 MPNs filled and 28 Comments rewritten; **0 Footprint changes,
>    0 rows added, 0 rows removed**.
>
> **Both swaps are EXTENDED-library parts.** C25744 was the only basic-library
> 10 kΩ 0402 in the catalog, so the one-time feeder fee is a property of the
> shortage, not of the choice.
>
> **If you hold v1.4: its gerbers are correct and orderable. Its BOM is not —
> use this one.**

---

## 0. ⚠️ THE SUPPLY SPECIFICATION — READ THIS BEFORE YOU BUY A POWER BRICK

**This is the one `policy_audit` row that does NOT pass, and it is a decision
for you, not a defect in the board.**

`power_topology.py` learned to grade LINEAR regulators on 2026-07-27. Until
then this board declared `rails: []` and E-TOPO graded **0 of 1** converters —
an LDO-only board reached a green gate by showing it nothing. v1.5 declares the
3V3 rail properly, with both required numbers CITED to Advanced Monolithic
Systems **ds1117 (2009-08 RoHS)**, and the gate now says:

    rail '3V3' LINEAR (AMS1117-3.3):
      headroom 1101 mV (Vin_min 4.500 - Vout_max 3.399) vs dropout 1300 mV
      PD 690 mW ((Vin_max 5.500 - Vout_min 3.201) x 0.3 A) vs rating 1200 mW (57%)
      -> FAIL DROPOUT: only 1101 mV of headroom against a 1300 mV dropout

- **1300 mV** is ds1117 p.3, "Dropout Voltage (VIN − VOUT)", **MAX**, at
  **IOUT = 0.8 A** (Note 4). C6186's own JLC catalog record agrees:
  `describe` contains `1.1V@(800mA)`.
- **1200 mW** is ds1117 p.3 Note 2: "maximum power dissipation of **1.2 W for
  SOT-223**". U_LDO is the SOT-223. Dissipation passes at 57%.
- **3.201 / 3.399 V** is ds1117 p.2, AMS1117-3.3 at VIN = 4.8 V, boldface (the
  full-operating-temperature limits).

**THIS RAIL DRAWS 0.3 A, AND THE DATASHEET PUBLISHES NO DROPOUT FIGURE THERE.**
p.1 says only that dropout is "guaranteed maximum 1.3V, *decreasing at lower load
currents*"; Note 4 bounds the HIGH side only; and the TYPICAL PERFORMANCE
CHARACTERISTICS page (p.6) has six curves, **not one of them dropout-vs-load**.
So the 0.3 A dropout is **OWED** — nobody has it — and the number graded is the
only CITED one, measured at **2.67× this rail's load**. `vin_min` was
deliberately left at 4.5 V: raising it to 4.75 makes the gate pass with 51 mV to
spare, and that would be fitting a number to a gate rather than measuring a
board.

**WHAT YOU MUST ACTUALLY DO.** The arithmetic says the LDO input needs

    Vout_max + dropout_max  =  3.399 + 1.300  =  4.699 V

**"5 V SELV" (BRIEF §3.5) does not state a tolerance, and that is the real
finding: this board's supply has never been specified tightly enough.** A ±10%
brick (4.50 V) is short by 199 mV; even a ±5% brick (4.75 V) lands at ~4.67 V
after the F1 / Q_REV / eFuse chain drop. So:

1. **Buy a 5 V supply that holds ≥ 4.85 V at J_PWR under full load**, i.e.
   ±3% or a 5.1 V nominal unit — not a generic ±10% adapter.
2. **MEASURE IT AT BRING-UP, and retire the OWED fact while you are there.** At
   step 4 of §7, with the board at its real load, measure VIN and VOUT at U_LDO
   and record `VIN − VOUT` at IOUT = 0.3 A. That single measurement is the number
   the datasheet does not publish; write it into
   `02_parts/AMS1117-3.3/part.yaml` as `dropout_mv` (MEASURED) and E-TOPO grades
   the real part instead of an 0.8 A worst case.
3. **Do NOT substitute another vendor's "AMS1117-3.3".** C6186's
   `componentBrandEn` is *Advanced Monolithic Systems* (read live 2026-07-27), so
   ds1117 is the authoritative document; a clone die's dropout curve is a fact
   about a different part.

Nothing here blocks fabrication or assembly. The boards are exactly as orderable
as v1.4's were.

## MECHANICAL GATES CLEAN — v1.7, `policy_audit` **FAIL=0**, and E-TOPO PASSING ON NUMBERS THAT ARE NOW ALL DERIVED

> ⚠️⚠️ **THIS HEADING SURVIVED TWO CORRECTIONS AND THE HISTORY IS KEPT ON
> PURPOSE.** It once read "ORDERABLE", was corrected to "DESIGN-CLEAN" on
> 2026-07-30, and then had to be corrected again because **E-TOPO's PASS was
> being computed on 43 % of the LDO's own declared load** and on a 1200 mW
> package ceiling that is a 25 °C figure used with no ambient term — a P0 about
> the numbers the gate was GIVEN, not about the gate. A third round then found
> the same defect class in the DROPOUT input: `vin_min` counted three named
> component resistances and none of the board's own copper.
>
> **ALL THREE ARE NOW CLOSED (ADR-0026 + ADR-0027) AND EVERY INPUT E-TOPO READS
> IS DERIVED**: `iout_max_A` 0.200 is an itemised sum over **116.859 mA** of
> cited maxima × a declared 1.5 margin; `pdiss_max_mw` 497 is
> `(125−75)/90 × 1000 − 5.250 × 11` at the BRIEF's hard ambient; `vin_min` 4.728
> is an exact nodal solve of the routed copper with each load charged the trunk
> it actually crosses. **The lesson kept from all three: "the gate PASSES" and
> "the number the gate was handed is right" are separate claims, and only the
> first is machine-checked.** See `MANIFEST.txt` and `verification/0026-*.md` /
> `verification/0027-*.md`.

> ⚠️ **THIS HEADING IS ABOUT THE DESIGN, NOT ABOUT WHETHER YOU CAN BUY IT.**
> It used to read "ORDERABLE" and that contradicted §5-0, 690 lines below,
> which says in as many words that this release **cannot be ordered today**
> — one BOM line (`C265111`, `J_THERM_A`/`J_THERM_B`) has a minimum order
> quantity above its entire stock. **Read §5-0 BEFORE you order anything.**
> The two claims are separate and both are true: the design is clean; the
> parts list is not currently buyable. (Corrected after the v1.7 topology
> re-gate, RG-P2-4.)

> **v1.7 CHANGES THIS HEADING'S OWN CLAIM.** v1.6's heading said *"every gate
> green except E-TOPO"*. **E-TOPO PASSES on v1.7** — `policy_audit` row,
> verbatim: `E-TOPO PASS: 1/1 rail(s) topology-correct, covering 1/1 converter
> part(s)`. The supply-envelope decision of §0 (ADR-0021: J_PWR is SPECIFIED
> 4.850–5.250 V, not "5 V nominal") is what closed it, and re-gate 3 (ADR-0027)
> is what made the number honest: the LDO dropout headroom is
> 4.728 − 3.399 = **1329 mV against a cited 1300 mV, +29 mV** — **NOT the
> +55 mV that stood here, which rested on a series resistance that omitted 42 %
> of itself.** §0 still
> governs what power brick you may buy and it is still a user-held decision —
> it is just no longer a failing gate. **`policy_audit` FAIL=0, PASS=28,
> WAIVED=6, HUMAN=6, N-A=5.**
>
> **⚠️ FIRST, THE ONE THING THAT STOPS THE BOARD WORKING AT ALL: the `J_ESTOP`
> SHORTING PLUG, bridging circuits 2–3 and NEVER 1–2.** It is the banner at the
> very top of this document and it is bring-up §7 step 0.
>
> **BEFORE YOU BUILD ANY FIELD HARNESS, READ §10 — AND READ ITS v1.7 BOX
> FIRST.** v1.6's §10 was about five identical unkeyed GH-5 housings and one
> cross-plug that was not fail-safe (an SHT45 pod in `J_MODE` energising the
> relay coil rail). **On v1.7 the GH-5 family is TWO housings** — `J_MODE` moved
> to keyed JST ZH 1.50 mm (ADR-0018) and `J_ESTOP` to keyed JST SH 1.00 mm
> (ADR-0025), and `J_DOOR` is deleted — **so the combination that was not
> fail-safe is mechanically unreachable.** The labeling discipline still applies:
> `J_RH_AMBIENT` ↔ `J_RH_EXHAUST` and `J_THERM_A` ↔ `J_THERM_B` are each a
> same-part pair, and swapping either silently inverts every thermal comparison.
>
> **AND BEFORE YOU WRITE HOST FIRMWARE, READ §7a** — two invariants the hardware
> cannot enforce: `REARM_N` must be PULSED, and MCP23017 `GPPUB` must be `0x00`
> (**on v1.7 that matters for bits 1, 2 and 7; bit 3 is now `GPB3_SPARE`, not
> `DOOR_OK`**).

`kicad-cli pcb drc --severity-all --refill-zones --schematic-parity` on
`04_kicad/cooksense.kicad_pcb`: **0 violations / 0 unconnected / 0 schematic
parity**. Placement gate P-COLLIDE **0 pad shorts / 0 anchored courtyard
overlaps**. E-INV **85/85 (v1.7: 167/167)**. A-ROT **189/189 CPL rotations
sourced from measured per-LCSC rows (v1.7: 206/206)**. A-POS **189/189 CPL rows
on the pad-centre datum (v1.7: 206/206), worst
deviation 0.0000 mm**. M-REPRO **green across three from-source regenerations**
(**1047** vias each, identical track/via/footprint hashes, and all three match the
board in this archive).

**The three v1.3 P0s are closed and each one is named here because the fix
changed what you order:**

1. **P0-A — the isolated loop is now ONE connector.** `J_ESTOPLOOP` and
   `J_CONTACTOR` are merged into a single 4-pole isolated terminal block
   **`J_ISOLOOP`** (KF350-3.5-4P). Both only ever carried isolated-domain nets,
   so the merge is isolation-neutral-or-better: one isolated body with one
   2.0 mm moat and one pour keepout instead of two adjacent bodies. **Any
   earlier text naming J_ESTOPLOOP or J_CONTACTOR is obsolete — neither exists.**
   See §11 for the pole legend, which is the field-wiring gate.
2. **P0-B — `R_OPENT` was ORDERED at 6.2 kΩ where the design needs 62 kΩ.** The
   open-thermistor detect threshold would have sat at 3.1073 V, above the
   LMV393's 2.500 V common-mode ceiling, so an open, broken or unplugged
   thermistor would have read FINE instead of OVER-TEMP. Now **C37825**
   (0402WGF6202TCE, 62 kΩ ±1%). See §12.
3. **P0-C — `R_WDPETPD` was ORDERED at 100 kΩ where the design needs 1 kΩ.** The
   TPS3823's WDI input *sources* I_IL 190 µA and V_IL is 0.3·VDD = 0.99 V, so the
   largest hold-down that works is **5.21 kΩ**. At 100 kΩ the node sits above
   V_IH and **the watchdog is silently disabled** — the board's primary runaway
   backstop would not exist, and it fails only in the case it exists for. Now
   **C11702** (1 kΩ). Same root cause as P0-B: a value-authored passive with no
   pinned LCSC, resolved by a picker that returned a wrong decade. See §12.
4. **P0-D — the ISO moat is enforced on routed copper**, not just declared. The
   `opto_isolation_2mm` DRU rule (IEC 60664-1 basic insulation, 30 V working,
   pollution degree 3) is green. **State the metric beside the number — three
   different measurements of one geometry are all correct and they answer
   different questions:**

   | metric | minimum | binding pair |
   |---|---|---|
   | **all copper, all layers** (pads + tracks + FILLED pours) | **2.0000 mm** | CONTACTOR_C at `J_ISOLOOP.1` → **GND zone edge**. Re-measured per layer 2026-07-26: F.Cu 2.0000, In1.Cu 2.0000, In2.Cu 2.0000, B.Cu 2.0000 — **the minimum is 2.0000 on all four**, because the moat keepout is a 2.0 mm offset on all four and the pours are clipped to it. |
   | pad-to-pad, true polygon distance (**method: rounded-rectangle pad outlines, corner radii included**) | 2.1661 mm | `U_OPTO.3[CONTACTOR_E]` ↔ `J_RH_EXHAUST.5[SHIELD_DRAIN]` |
   | pad-to-pad, bounding-box | **2.1400 mm** (v1.7, re-measured 2026-07-30) | `U_OPTO.3[CONTACTOR_E]` ↔ `J_RH_EXHAUST.5[SHIELD_DRAIN]`. **v1.6 reported 2.126 mm at `J_ISOLOOP.4[CONTACTOR_E]` ↔ `J_DOOR.MP[GND]`; that pair NO LONGER EXISTS — `J_DOOR` is deleted (ADR-0025) — and the new binding pair is 0.014 mm FURTHER apart. The barrier improved.** |

   **2.0000 mm is the honest headline.** The margin is 0.000 mm *by
   construction*: the `iso_moat_block` pour keepout IS defined as exactly the
   2.0 mm offset of the isolated copper, so the pour edge lands exactly on it.
   That is the rule being met precisely, not a near miss. v1.2 measured
   **0.199 mm** at this rule, and the same cross-layer scanner run unchanged
   against the sealed v1.1 board returns **915 pairs under 2.0 mm, worst
   0.0000 mm** — which is what makes the 2.0000 believable rather than merely
   printed.

**v1.0 and v1.1 remain DO-NOT-ORDER** — see `07_releases/*/SUPERSEDED.md`. Three
independent defects, any one of which is disqualifying: R_OPENT at 6.2 kΩ
defeating the open-thermistor safety detect, CE1 shipped at CPL rotation 180°
(a reversed 220 µF polarized electrolytic across a live 5 V rail), and 22 wrong
CPL rotations including the ten safety-chain SOT-23-6 gates, which at 90° out do
not connect their intended nets.

---

Cooktop safety-interlock sidecar for a Raspberry Pi: keypad reed-relay matrix
(isolated COMB — vertical relays, contact columns pocketed between pairs),
watchdog + hardware AND-chain interlock, 12× reed coil drivers, Type-K
thermocouple front-end (MAX31856), dual-comparator thermistor window
(over-temp + open-detect, new in v1.3), opto-isolated contactor dry-contact
loop on its own connector (new in v1.3). Board **188 × 92 mm**, **4 layer**,
**222 components** placed (v1.3 generate_board; 223 -> 222 on the J_ISOLOOP
merge), E-INV **83/83** on the v1.3
netlist (v1.6 raises the invariant count to **85** — two `part_value` asserts, §13
table; the netlist itself is unchanged). v1.3 is the second electrical revision (v1.2 was never sealed);
schematic deltas vs v1.2: door pull-down, open-detect comparator half,
comparator rail move, isolated-loop connector move (§2, §11).

---

## 0-T. ⚠️ THE THERMAL ENVELOPE — **65 °C DECLARED, 75 °C SURVIVE**, AND A BENCH GATE YOU MUST NOT SKIP

    DECLARED OPERATING AMBIENT:  Ta = 65 C     (the BRIEF's own `stop` rung)
    SURVIVE CORNER:              Ta = 75 C     (the BRIEF's HARD enclosure rung)
    MANDATORY BEFORE USE ABOVE BENCH CONDITIONS:  §7b, measurements B1-B6

**Do not operate this board above 65 °C ambient until §7b has been done.**
`TH_ENCLOSURE` is one of the eight monitored ADC channels, so the host can see
the violation; nothing on the board prevents it.

**Why 65 and not 75** (user decision 2026-07-30, ADR-0029). The board is
**thermally** limited, not dropout-limited. The 3V3 rail has two margins and
they bind in different places:

| | at 75 °C (the old declaration) | **at 65 °C (declared)** |
|---|---|---|
| `U_LDO` junction margin, **CITABLE** form `Tj = Ta + PD·θ_JA` | 7.92 °C | **17.92 °C** |
| the same margin **carrying the board's other 0.958 W** (+1.55…+4.65 °C, DERIVED) | **3.3…6.4 °C** | **13.3…16.4 °C** |
| dropout margin, worst case, CITED 2 × 10 mΩ Micro-Fit contacts | +18.1 mV | **+19.5 mV** |
| dropout margin at the aged 2 × 30 mΩ contact allowance (INHERITED) | +2.0 mV | +3.4 mV |

**THE 7.92 °C THIS RELEASE USED TO PUBLISH WAS WRONG REGARDLESS OF THE
ENVELOPE**, and it is corrected here rather than rounded away. The arithmetic
was right; the FORM was incomplete. `θ_JA` is a junction-to-**ambient-air**
figure measured with only the device under test dissipating, and ds1117's own
Thermal Considerations says *"additional heat sources mounted near the device
must be considered."* This board's other **0.958 W** — 12 reed relay coils at
0.705 W dominate — raises the copper the tab sinks into by **+1.55…+4.65 °C**,
which is **20–59 % of the number that was being published as the margin.**

Derivation, so it is checkable rather than quotable (MEASURED from CITED
constants only — ds1117 `θ_JA` 90 °C/W SOT-223 package figure, `Tj_max` 125 °C,
`Iq_max` 11 mA, and `power_tree.yaml`'s own graded keys):

    PD_pass = (vin_max 5.250 - vout_min 3.201) x iout_max_A 0.200 = 409.800 mW
    PD_q    = vin_max 5.250 x Iq_max 0.011                        =  57.750 mW
    rise    = (409.800 + 57.750) mW x 90 C/W                      =  42.0795 C
    Tj(65)  = 65 + 42.0795 = 107.0795 C   ->  margin 17.9205 C   [CITABLE]
    honest  = 17.9205 - (1.55 ... 4.65)   ->  16.37 / 15.13 / 13.27 C

Citable ambient ceiling `Tj ≤ 125 °C`: **82.92 °C**; honest, carrying the board
term: **78.3…81.4 °C**. The declared 65 °C sits inside the HONEST ceiling by
13.3…16.4 °C. It sits below `F1`'s own −40…+85 °C operating range with room,
which 75 °C does not once the board term is carried.

**Narrowing the ambient bought the dropout almost nothing, and that is the
finding, not a footnote.** The dropout margin moves **−0.31 mV/K** — copper is
42 % of the series sum at 0.393 %/K — so 75 → 65 buys **+1.4 mV**. Anyone who
reaches for the ambient knob to fix the dropout will find it connected to
almost nothing. **The dropout problem is an EVIDENCE problem, not a design
problem:** the whole comparison is a **1300 mV dropout figure ds1117 publishes
only at 0.8 A, applied to a 0.2 A rail**, and that is §7b item B3.

## 🛑 THE PART THAT ACTUALLY BINDS IS NOT THE LDO — IT IS THE REED RELAY, AT +70 °C

**`DIP05-1A72-13L` is rated −20…+70 °C, twelve of them are fitted (including
`K_STOP`), and that +70 °C is the NARROWEST operating-temperature rating on this
board.** MEASURED by me across all 47 `02_parts/*/part.yaml` dossiers: **+70 °C
is the UNIQUE minimum** — the next-lowest is `F1`'s +85 °C, which is what the
first version of this section and ADR-0028/ADR-0029 named instead, 15 °C looser.
Three independent fresh-context lenses found this in the same pass.

    Ta 65 C DECLARED   ->  5.00 C of relay margin on the plain ambient comparison
    Ta 75 C            -> -5.00 C.  75 C WAS NEVER INSIDE THE RELAY'S RATING.

**This does not change the decision — it changes the REASON, and it makes the
decision more necessary rather than less.** 65 °C is the only rung on the
BRIEF's enclosure ladder that fits twelve DO-NOT-SUBSTITUTE relays at all. The
release chose it for the LDO junction and got the relay for free without knowing
it. At 65 °C the relay is the tightest positive margin on the board (5.00 °C,
against the LDO's 13.3…16.4 °C), so **it, not the LDO, is what an integrator
must design the enclosure around.**

**⛔ CORRECTION TO THIS DOCUMENT'S OWN EARLIER CLAIM — “PASSING §7b MAY REOPEN
75 °C” IS FALSE AS IT WAS WRITTEN, AND IT IS WITHDRAWN.** B1–B6 measure the
LDO's dropout, `F1`'s tempco, `θ_JA`, the board rise and a thermal time
constant. **None of them moves a catalogue relay rating**, and 75 °C is 5 °C
above one. The honest form:

> **Passing B1–B6 is NECESSARY BUT NOT SUFFICIENT to reopen 75 °C.** Reopening it
> additionally requires re-rating or replacing the twelve `DIP05-1A72-13L`
> relays — a BOM change and therefore a new board revision, **not** a
> documentation-only supersede. What B1–B6 alone can reopen is the range
> **between 65 °C and 70 °C**, and even that is bounded by the relay.

The 75 °C envelope is not merely unproven; on the relay axis it is **refuted**.

**RECOMMENDED FOR THE NEXT COPPER REVISION, NOT DONE HERE:** six more thermal
vias in the **existing** `U_LDO` tab pad (2 → 8 × 0.15 mm) — **−18.0 °C/W and
+8.4 °C of junction margin with NO BOM, schematic, netlist or feature change.**
Beside ADR-0027's deferred 5 V pour (+28.1 mV) those two retire both margins by
construction. Not done in v1.7 because the fab set is otherwise invariant and a
copper edit re-opens routing, DRC and a full material-change re-gate.

**One thing in `power_tree.yaml` will look wrong and is not.** The graded key
`rails[3V3].pdiss_max_mw` is **497 mW — the 75 °C derating — and it is HELD
there on purpose** (ADR-0029 Decision 4). At 65 °C the correct derating is
608 mW, but the gate was never red (PD 409.8 mW against 497 is 82.5 %, E-TOPO
PASSES), so moving it would buy nothing except a looser ceiling. Narrowing a
declared envelope must not become the mechanism by which a machine gate is
weakened. The declared corner is still machine-checked — ADR-0029's bound
`LDO_TJ_DECLARED_AMBIENT` regenerates it from the same keys and prints 999 if
the declaration drifts back to 75.

---

## 1. ⚠️ MECHANICAL / ENCLOSURE — THE LOAD-BEARING ASSUMPTION

**Ambient: see §0-T. The declared operating ambient for this board is 65 °C,
not the enclosure ladder's 75 °C HARD rung.**

The board's keypad-contact domain is isolated from SELV logic by **>= 6.000 mm
creepage** (brief §4/§7, ADR-0001). That figure is only held **because the
enclosure is NON-CONDUCTIVE and no conductive plate, bracket, rail or standoff
set bonds two or more of the four mounting holes together** (user decision,
2026-07-25, ADR-0012).

Under that assumption the governing rule is **PER-HOLE**: `a_i + s_i >=
6.000 mm` for each hole, where `a` = hardware-to-keypad-copper and `s` =
hardware-to-SELV-copper, with the hardware modelled as a **3.0 mm-radius
conductive disc** (M2.5 pan head + DIN125 washer + nut). At H3 and H4 the
fastener is SELV-BONDED (the GND pour reaches 0.200 mm from the hole wall, so
s < 0) and the requirement collapses to `a` alone.

MEASURED on filled copper by the `I-HW` gate, **re-measured 2026-07-26 on the
ROUTED board** (the earlier table was taken on track-free copper and both its
H1 and H2 rows are superseded), all against 6.000 mm.

**EVERY FIGURE BELOW NOW STATES THE METHOD THAT PRODUCED IT**, because this
board has now shipped three numbers whose metric was left implicit (the ISO pair
— bbox vs true-polygon vs all-copper; this I-HW table; and the H4 geodesic that
the ruling below overturned). A creepage number without its method is not a
measurement.

| Hole | a (keypad approach) | s (SELV approach) | governing figure | method | verdict |
|---|---|---|---|---|---|
| H1 | **−0.050** (track KP_D1) | 13.631 (pad K_U1.2) | keypad-BONDED -> s alone = 13.631 | **straight line, crosses no void** | PASS |
| H2 | **−0.050** (track KP_U6) | 13.000 (pad K_STOP.1) | keypad-BONDED -> s alone = 13.000 | **straight line, crosses no void** | PASS |
| H3 | 40.933 (pad K_U1.4) | −1.450 (GND pour) | SELV-bonded -> a alone = 40.933 | **straight line; crosses a void but irrelevant at 40.9 mm** | PASS |
| **H4** | **6.5984** (pad K_STOP.3, RSTOP_MID) | −1.4493 (GND pour) | SELV-bonded -> a alone = **6.5984** | **CREEPAGE — surface path around the outline notch** (clearance, for comparison, is 4.0286 mm straight-line) | **PASS** |

**H1 and H2 changed sign when the board was routed, and the verdict logic is why
that is still a PASS.** On track-free copper the nearest keypad copper to those
two fasteners was a pad, 2.305 mm and 3.129 mm away. On the routed board a
keypad TRACK passes under each fastener disc (a = −0.050 mm, i.e. touching), so
each fastener is now KEYPAD-BONDED and the requirement becomes the SELV approach
`s` alone — 13.631 mm and 13.000 mm, both far clear. The per-hole rule is
`a + s >= 6.000` with a negative approach meaning "bonded to that domain, so
measure the other side alone". Nothing got worse; the binding item changed.

**H4 is the tight hole, at 6.5984 mm of CREEPAGE against 6.000 mm required.**
State the method with every figure — leaving it implicit is what let a reviewer
read the clearance as if it were the creepage and rule the barrier failing:

| figure | to what | method | answers |
|---|---|---|---|
| **6.5984 mm** | pad `K_STOP.3` (RSTOP_MID) | **creepage** — surface path around the outline notch | **the requirement** |
| 4.0286 mm | pad `K_STOP.3` | clearance — straight line | through-air, requirement well under 1 mm |
| 4.6166 mm | nearest `RSTOP_MID` **track** | clearance — straight line | informational |
| ~~8.500 mm~~ | — | — | does not reproduce |

An earlier revision attributed both the 6.598 and the 4.617 to the same pad;
they are to different copper AND different metrics, which is exactly why each now
names its target and its method. All are north of the notch. Do not let
a rework shrink the notch or grow keypad copper near it.

> ## H4 — TWO NUMBERS, TWO DIFFERENT QUESTIONS. BOTH PASS.
>
> H4 was ruled a FAIL on 2026-07-26 and the ruling was **reversed the same day**.
> **Both the ruling and the reversal were made by the PROJECT OWNER**, the
> decision-maker of record for this board; the release agent escalated rather than
> deciding, which is why `dispositions.md` records "it is not the release agent's
> call". **No external or third-party qualified sign-off is recorded, and this
> archive does not claim one.** If your process requires an independent reading of
> IEC 60664-1 for a mains-adjacent interlock, this release does not provide it.
> It is recorded here because the reversal turns on a distinction every figure in
> this document now states explicitly.
>
> | figure | method | the question it answers | requirement | verdict |
> |---|---|---|---|---|
> | **6.5984 mm** | **CREEPAGE** — surface path, around the outline notch | how far must contamination track **along a surface**? | **>= 6.000 mm** (`keypad_isolation_6mm`, brief §4/§7, ADR-0001) | **PASS** |
> | 4.0286 mm | **CLEARANCE** — straight line, disc edge to pad edge | how far is it **through air**? | **not derivable from this archive — see the note below** | PASS by a wide margin |
>
> **⚠️ THE CLEARANCE REQUIREMENT FOR THIS BARRIER IS NOT IN THIS ARCHIVE, AND
> EARLIER REVISIONS QUOTED A FIGURE BELONGING TO A DIFFERENT RULE.** They said it
> was "well under 1 mm at 30 V working, PD3, material group IIIa". **That string
> is the comment on `opto_isolation_2mm` (`cooksense.kicad_dru` line 34), whose
> condition is `A.NetClass == 'ISO_CONTACTOR'` — the contactor loop, a DIFFERENT
> domain.** The rule that actually requires the 6 mm, `keypad_isolation_6mm`
> (line 30), cites only "brief section 4/7 + ADR-0001" and states **no working
> voltage, no pollution degree, no material group**; neither `BRIEF.md` nor
> ADR-0001 ships here (§13 item 14). **So a reader holding only this archive
> cannot tell whether 6.000 mm is a ~3x design margin over an IEC minimum at low
> voltage, or is itself the minimum at a mains-referenced potential** — and that
> is what decides how much the notch credit matters. The 4.0286 mm clearance is
> reported here as a MEASUREMENT, not as a pass against a requirement this
> archive can show you. **v1.4 must ship the keypad domain's working voltage and
> pollution degree, or the brief section that sets them.**
>
> **The rule requires CREEPAGE.** `cooksense.kicad_dru` line 30 says so in as
> many words: *"must hold >=6mm creepage"*. The 4.0286 mm straight line is the
> **clearance**, a different and far smaller requirement, so the two numbers were
> never in conflict — they answer different questions, and quoting one without
> naming which was the whole defect.
>
> **Why the notch counts, stated with the numbers a reviewer needs to check it.**
> **The notch is 1.000 mm wide** (y[48.800, 49.800]) and IEC 60664-1's minimum
> **groove** width at pollution degree 3 is **X = 1.5 mm**. So the notch IS below
> X — **say that plainly, because omitting it is what let a reviewer apply the
> groove rule and rule this barrier FAILING on 2026-07-26.** The X rule does not
> apply, for a reason that has nothing to do with width: it governs a **groove —
> a channel with material at the bottom** — where the question is whether
> contamination bridges across the channel. This is a **THROUGH-notch reaching
> the east board edge** (x[191.500, **200.000**],
> and 200.000 IS the board edge; that is why ADR-0012 records it as OUTLINE
> geometry with no router-bit minimum and no internal-cutout surcharge). There is
> no surface across it to creep along, there is nothing to bridge, and it drains
> at the open end. Creepage genuinely must go around it. (For completeness: the
> provision that reduces X to one third of the associated clearance is also not
> what licenses this — it applies where the associated CLEARANCE is below 3 mm.
> It is not needed here, and an earlier note in this archive mis-stated it by
> comparing X against the 6 mm CREEPAGE requirement instead.)
>
> **One more measured fact, recorded because it looks alarming and is not:** the
> 3.000 mm fastener disc **overhangs the notch by 0.800 mm** (H4 centre y52.000,
> notch south edge y49.800, so the disc reaches y49.000 — 0.800 mm past it). A
> disc roofing a blind slot would be a capillary trap. This notch is **open at
> the east board edge**, and the disc spans only x[190.000, 196.000] of a notch
> running x[191.500, 200.000], so **4.000 mm of its length stays open and it
> drains.** The overhang does change the geometry of the creepage path, and the
> derivation below accounts for it: the disc covers the notch's SW corner, which
> is why the taut path skirts the west edge rather than running straight at the
> NW corner.
>
> **The 6.5984 mm re-derived independently** (canon M1 — not the gate's method).
> The taut path is not the naive one, because the fastener disc **overhangs the
> notch**: |centre → notch SW corner| = 2.6627 mm < the 3.000 mm disc radius, so a
> straight run at the NW corner would cross the void. The path therefore skirts
> the west edge:
>
> | leg | from → to | length |
> |---|---|---|
> | 1 | disc boundary at x=191.500, y = 52 − √(3² − 1.5²) = **49.4019**, up the notch's west edge | **0.6019 mm** |
> | 2 | notch NW corner (191.500, 48.800) → `K_STOP.3` pad edge (197.450, 45.620, r 0.750) | **5.9965 mm** |
> | | **total** | **6.5984 mm** |
>
> Matches the `I-HW` gate's 6.598 mm to 0.0004 mm by a different construction.
>
> **A caveat that survives the reversal:** KiCad's DRU language has no creepage
> primitive, so the rule is written `(constraint clearance (min 6.0mm))` — it
> **requires** creepage and **measures** clearance. It therefore cannot see the
> notch either, in either direction. `keypad_isolation_6mm` returning 0
> violations is not evidence about creepage; the `I-HW` gate is what measures it.
> See §13 item 15.

**`verification/audit.txt` is the generating evidence for this table, but the two
are NOT digit-identical:** audit.txt prints 3 decimals from a polygon
approximation (H1 13.631, H3 40.933, H4 s −1.450); this table prints analytic
4-decimal figures (13.6299, 40.9324, −1.4493). Where they differ in the last
place the 4-decimal values are the true ones and audit.txt is ~0.001 mm high.
**Where they differ in SUBSTANCE, audit.txt wins** — that is how the H2 error was
caught (this table carried 13.1525 from a circle model on a rectangular pad;
audit.txt's 13.000 was right).

**BOLT THIS BOARD TO A METAL PLATE AND THE ISOLATION DEFECT RE-OPENS.** A
conductive plate bonding H1 (keypad side) to H4 (SELV side) makes the
governing rule the PAIRING form `min_i(a_i) + min_j(s_j)`, **which this board
FAILS** (it re-opens at **0.000 mm** — a DIRECT keypad-to-SELV bond, not a reduced clearance (measured: min_a -0.050 + min_s -1.450; see verification/audit.txt)). This is a mains-adjacent
cooking interlock: the consequence is keypad-domain contact voltage reaching
SELV logic.

**REQUIRED FASTENER SPEC — explicit line item for the assembler/integrator:**

> **(1) DOMAIN BONDING.** Mounting hardware MUST be **non-conductive
> (nylon/polyamide) M2.5**, OR metal M2.5 hardware **only** in a non-conductive
> enclosure where **no conductive plate, bracket, rail or standoff set bonds any
> two mounting holes**.
>
> **(2) MAXIMUM CONDUCTIVE DIAMETER AT H4 — 6.0 mm. HARD LIMIT 6.3 mm.**
> If ANY conductive part of the H4 stack (washer, screw head, nut flats,
> standoff) exceeds **6.3 mm across**, **THE H4 ISOLATION BARRIER FAILS.**
> Use a **DIN 125 A2.7 washer (OD 6.000 mm)** or smaller. Nothing larger.
> **Do not substitute a shakeproof/star washer (typically 6.5 mm), a DIN 9021
> body washer (8.0 mm), or a hex standoff (6 mm A/F = 6.93 mm across corners).**
>
> **THE MECHANISM, because "max 6.0 mm" invites someone to wonder why and the
> answer is what stops them:** H4's isolation is **creepage that goes AROUND the
> edge notch** — that detour is the whole barrier.
>
> **Mind which edge.** H4's centre (y52.000) is **2.200 mm from the notch's NEAR
> (south) bank at y49.800, and 3.200 mm from its FAR (north) bank at y48.800.**
> **The governing distance is 3.200 mm to the FAR bank**, because bridging
> requires the washer to REACH THE FAR SIDE. A washer whose radius exceeds
> 2.200 mm merely overhangs the notch — the specified DIN 125 A2.7 (r 3.000)
> does exactly that, and is fine, because the notch is still open beneath it.
> **A washer of radius 3.200 mm or more (OD 6.400 mm) lands on solid board on
> BOTH SIDES — so the FASTENER ITSELF BRIDGES THE NOTCH.** The detour vanishes,
> creepage runs directly from the washer's landing on the far bank to the pad,
> and the barrier drops from **6.3815 mm to 4.7195 mm** — a FAIL — with nothing
> visible to show it.
> **The notch and the washer are one mechanism, not two parts.** This section
> already tells you not to shrink the notch and not to grow keypad copper;
> **growing the washer is the same defect, and it is only 0.4 mm away.****

**WHY (2) EXISTS — it is a CLIFF, not a slope, and it is 0.4 mm wide.** H4's
6.5984 mm figure is CREEPAGE around the edge notch, and the fastener is modelled
as a conductive disc. As the disc grows it eventually touches the board on
**both** sides of the notch — at which point **the fastener itself bridges the
notch**, the creepage path stops going around, and the barrier collapses to the
straight line. Measured:

**Every figure in this table is CREEPAGE — the surface path — computed the same
way on both sides of the cliff.** (An earlier revision printed the post-collapse
rows as straight-line CLEARANCE, which silently switched metric mid-column; the
verdicts were unaffected but ADR-0015 Decision 2 makes stating the method
binding.) The straight-line clearance is given alongside for comparison only.

| conductive OD | example | **CREEPAGE** (surface path) | clearance (straight line) | verdict |
|---|---|---|---|---|
| 5.4 mm | small washer | 6.9515 mm | 4.3286 mm | PASS |
| **6.0 mm** | **DIN 125 A2.7 — SPECIFIED** | **6.5984 mm** | 4.0286 mm | **PASS** |
| 6.2 mm | | 6.4837 mm | 3.9286 mm | PASS |
| 6.3 mm | | 6.4265 mm | 3.8786 mm | PASS — hard limit |
| 6.38 mm | | 6.3815 mm | 3.8386 mm | PASS — last passing value |
| **6.4 mm** | | **4.7195 mm** | 3.8286 mm | **FAIL — the washer reaches the FAR bank and bridges the notch** |
| 6.5 mm | shakeproof washer | 4.2683 mm | 3.7786 mm | FAIL |
| 6.93 mm | 6 mm A/F hex standoff, across corners | 3.7061 mm | 3.5636 mm | FAIL |
| 8.0 mm | DIN 9021 body washer | 3.0286 mm | 3.0286 mm | FAIL |

**The cliff is a genuine discontinuity, not a steep slope:** 6.38 mm → 6.3815 mm
creepage, 6.40 mm → 4.7195 mm. **1.66 mm of barrier lost to 0.02 mm of
diameter**, because at that point the path stops going around the notch and
starts going straight from the washer's far-bank landing. (The two metrics
converge only above OD ~7.8 mm, where the washer's landing is far enough north
that the direct line no longer clips the notch at all.)

The transition is at **OD 6.400 mm** (disc radius 3.200 = the 3.200 mm from H4's
centre y52.000 to the notch's north edge y48.800). **There is 0.400 mm of
diameter between the specified washer and barrier collapse, and a 0.5 mm larger
washer is an unremarkable substitution on a bench.** §1 already tells the
integrator not to shrink the notch and not to grow keypad copper; growing the
washer is the same defect and was previously unstated.

**CLAUSE (2) IS NOT ON THE SILKSCREEN.** The board's silk carries the
nylon/no-bonding-plate rule (clause 1) and the ADR-0012 captions; it has **no
maximum-washer marking**, and there was no room for one. A 0.4 mm-wide cliff with
no board-level evidence is exactly the kind of thing a service replacement years
from now will not know about. **This document is the only record — keep it with
the unit.**

Sign both clauses off at integration; they are safety properties, not
preferences.

**The H4 edge notch is deliberate — do not let the fab "clean it up".** H4 has
an edge notch milled at x[191.50, **200.00**] y[48.8, 49.8] (board coordinates;
200.000 IS the east board edge — an earlier revision printed 200.10, which is
0.10 mm outside the board and cannot be a notch coordinate).
It is OUTLINE geometry reaching the east board edge, NOT an internal slot, so
there is no router-bit minimum and no JLC internal-cutout surcharge. **And it is
OUTLINE geometry that makes the notch creditable toward creepage at all** — see
the H4 box below. It is not re-specified as an internal slot because the corridor
there is 0.55 mm,
narrower than any router bit. Confirm in the fab preview that the notch
survives exactly as drawn.

The board carries this warning **on the silkscreen next to the mounting
holes**: "MOUNTING HW: NYLON M2.5 — OR METAL IN A NON-CONDUCTIVE ENCLOSURE
ONLY." / "A PLATE BONDING ANY 2 HOLES BREAKS THE 6mm KEYPAD ISOLATION.
ADR-0012", plus a "NYLON HW" flag at each of H1–H4.

## 2. ⚠️ MANDATORY SAFETY MITIGATIONS (both MANDATORY — the board design assumes them)

### 2-0. ⚠️ THERE IS NO DOOR INPUT ON THIS BOARD — `J_DOOR` IS DELETED (ADR-0025)

**EVERYTHING PREVIOUS REVISIONS OF THIS DOCUMENT SAID ABOUT A DOOR HARNESS IS
VOID.** There is no `J_DOOR` connector, no `DOOR_RAW` net, no `R_DOORPD`,
`R_DOORS`, `D_DOOR` or `R_DOOROKPD`, and no `DOOR_OK` term in the safety AND
chain. Do not look for the connector; do not build the harness; do not wire a
reed switch to anything.

**Why, stated as the brief amendment it is.** The user has no access to the
appliance's door signal and no expectation of obtaining one. `BRIEF.md`'s own
scope line is a PROHIBITION list — *"no custom board may connect to the
magnetron, HV circuit, convection-heater power, fan mains, **OEM door
interlocks**, OEM thermal cutoffs, or internal mains"* — so `J_DOOR` could
never have been fed from an OEM interlock in the first place. Any door signal
was always going to be a custom sensor the researcher adds, and the researcher
has told us there will not be one. Removing it is a scope decision the user
made; ADR-0025 writes the amendment out in full rather than doing it silently.

**Removal, NOT "do not populate", and that distinction was MEASURED.**
`fix_silk_placement.py` carries no `dnp` / `exclude_from_bom` / `population`
reference at all, so a DNP part still gets a designator placed on silk and frees
**zero** silk area. Marking `J_DOOR` DNP could never have dissolved the silk
collision that forced the decision. It is out of the netlist.

**What happened to the freed AND-chain input — it got a real term, not a rail
tie-off.** `DOOR_OK` was never in `KEY_RELAY_ALLOWED` (`BRIEF.md`:82 has no door
term); its only consumer was `U_OSCLR.1`. So:

```
OS_CLR_N  =  ESTOP_OK  ·  STOP_REQ_N
```

which is exactly the *"hardware key-relay inhibit"* `BRIEF.md`:89 commissions and
which the board did **not** previously have. **There is no 3V3 tie-off anywhere**
— tying the freed input to the permissive rail was considered and rejected.

**The consequence you must plan around** is the banner at the top of this
document: with `J_ESTOP` unfitted the AND chain is INERT, not permissive, and
the board does nothing at all until the shorting plug is in.

### 2a. ⚠️ THE INTERLOCK YOU HAVE, STATED HONESTLY

The board no longer claims a door interlock of any kind. What it has is:

| term | source | default with nothing plugged in |
|---|---|---|
| `ESTOP_OK` | `J_ESTOP` circuit 3 (`ESTOP_RAW_IN`), via `R_ESTOPPD` 470 Ω to GND | **LOW = not-OK = restrictive** |
| `STOP_REQ_N` | host, through the expander | restrictive |
| `MODE_RAW` | `J_MODE` (keyed JST ZH, ADR-0018) via `R_MODEPD` | restrictive |
| `TEMP_OK` | the hardware thermal window (§2b) | restrictive |

`R_ESTOPPD` is **470 Ω and that value is a BOUND, not a preference** — see
`02_parts/0402WGF4700TCE/part.yaml`, which carries the derivation as a machine
assertion. It is load-bearing twice over: it sets the pod-mismate corner
(ADR-0024: an SHT45 pod cross-plugged into the safety housing drives 500 µA into
this node; at 470 Ω that is 0.591 V against the 74HC14's `V_T−` floor, passing by
**+92 mV**, and the worst-case ceiling is **559.3 Ω** — the next standard value
UP, 560 Ω, gives 0.7007 V and **FAILS by 0.7 mV**), and with `J_ESTOP` unfitted
it is the **sole DC path** on `ESTOP_RAW_IN`, holding it at
(1 µA × 470) + (1 µA × 680) = **1.15 mV** against a `V_T−(min)` of 0.500 V.
**A substituted 10 kΩ would still read LOW unfitted and would silently fail the
mismate corner — the defect would be invisible until a pod met the E-stop
connector.** Do not substitute it.

**The interlock this board asserts about the world is PHYSICAL, not logical:**
the keypad contact domain is isolated from SELV logic by the milled comb and the
6 mm `KEYPAD_ISO` barrier (§1, and the DRU repair in the v1.7 banner). Cooking
safety remains with the OEM controller and the OEM safety systems, which is what
`BRIEF.md` commissions — this is a keypad-emulation system that presses 18
buttons on a 6×3 membrane matrix with reed relays, and it drives no mains.

### 2b. P1-3 — Host runtime thermistor cross-check (ACCEPTANCE ITEM)

The hardware window (U_COMP over-temp + U_COMP2 open-detect, both LMV393 on
3V3_ANALOG) is the backstop, not the monitor. **The host software MUST
cross-check the two thermistor channels against each other and against the
MCP3208 ADC readings at runtime, every control cycle, and refuse HOST_AUTH on
disagreement.** Acceptance: demonstrate that (a) an unplugged NTC harness and
(b) a shorted NTC each drop TEMP_OK in hardware AND are independently detected
and reported by the host from the ADC path before the hardware trip.

Measured v1.3 open-detect facts (commit 16ae67b / STATUS):
- Open-circuit sense node reads **2.2687 V** (worst-high 2.2829 V) against the
  LMV393 VICR ceiling of **2.500 V** at VCC 3.3 V — **+217 mV margin**. Every
  reading either comparator sees, open included, is inside VICR.
- Open-detect threshold **2.0370 V**; worst-case separation to an open reading
  **193 mV** vs the LMV393 VIO of **9 mV**.
- Nuisance-trip floor **−10.4 °C typical / −7.4 °C worst** (a connected NTC
  colder than that trips the open-half — irrelevant in a cooktop enclosure).
- Over-temp trip **72.80 °C** on the unchanged 68 k / 10 k divider, inside the
  brief's 70–75 °C window.
- Do NOT "clean up" R_CLMPA/R_CLMPB (22 k sense-node bleeds): they are what
  keep an open reading inside VICR. Without them the open-detect is INERT.

#### ⚠️ CH0 and CH3 DO NOT USE THE SAME TRANSFER FUNCTION AS THE OTHER SIX

The 22 k bleeds sit ACROSS the camera-A/B thermistors, so those two channels
divide differently from CH1/CH2/CH4–CH7. **If you implement this acceptance test
with the plain 10 k/NTC model it will not work, and it will fail in the
direction that matters.**

Divider, CH0 and CH3 only:

```
3V3_ANALOG --[ R_REF 10k ]--+-- node --[ R_SER 1k ]-- ADC (high-Z, no DC load)
                            |
                            +--[ NTC 10k B25/85=3987 ]-- GND
                            +--[ R_CLMP 22k ]---------- GND
```

**Correct host inversion for CH0/CH3 — use this, not the naive one:**

```
R_par = 10000 * V / (3.3 - V)              # what the naive model stops at
R_ntc = 1 / (1/R_par - 1/22000)            # THE STEP THE NAIVE MODEL OMITS
T_C   = 1/(1/298.15 + ln(R_ntc/10000)/3987) - 273.15
```

**Error if you omit the clamp term** (computed, B25/85 = 3987):

| true °C | node V | naive model reports | error |
|---|---|---|---|
| 0.0 | 1.8872 | 18.7 | **+18.7** |
| 10.0 | 1.6949 | 23.8 | +13.8 |
| 25.0 | 1.3444 | 33.6 | +8.6 |
| 40.0 | 0.9845 | 45.4 | +5.4 |
| 55.0 | 0.6804 | 58.4 | +3.4 |
| 70.0 | 0.4564 | 72.3 | +2.3 |
| 72.8 (hw trip) | 0.4231 | 74.9 | +2.1 |
| 85.0 | 0.3041 | 86.5 | +1.5 |

**AND THIS IS WHY IT MATTERS FOR TEST (a).** An OPEN NTC drives the node to
**2.2687 V** — which the derivation above reproduces exactly, confirming the
model. Fed to the naive inversion that reads as **8.4 °C**: a plausible, healthy,
cold reading. **The host would not report a fault, and acceptance test (a) —
"an unplugged NTC harness is independently detected and reported by the host from
the ADC path before the hardware trip" — would pass a board on which the host
detects nothing.** With the corrected inversion, `1/R_par − 1/22000 → 0`, so
R_ntc → ∞ and the open is unmistakable.

**Recomputed accept/reject thresholds for the host, CH0/CH3:**

| condition | node V | corrected R_ntc | host must |
|---|---|---|---|
| open / unplugged | **≥ 2.2000** | ≥ **220 kΩ** | declare FAULT, refuse HOST_AUTH |
| plausible operating band 0–85 °C | 0.3040 – 1.8872 | **1.064 kΩ – 34.005 kΩ** | accept |
| shorted NTC | ≤ 0.05 | ≤ **155 Ω** | declare FAULT, refuse HOST_AUTH |

> **⚠️ CORRECTED 2026-07-26 — the resistance column of this table was WRONG in
> two rows, and both errors pushed a host toward the unsafe or the useless. Use
> the VOLTAGE column as the primary test.**
>
> **Row 2 said `3.0 k – 32.6 k`.** Recomputed with this section's own inversion,
> the 0–85 °C band is **1063.8 Ω to 34 004.6 Ω** (equivalently, the voltage
> endpoints 0.3040 V and 1.8872 V invert to **1063.8 Ω** and **34 004.6 Ω**). The old
> band `3.0 k – 32.6 k` corresponds to **54.5 °C … 0.79 °C** — so a host
> implementing it literally would declare FAULT and refuse HOST_AUTH for any
> camera thermistor above **54.5 °C, i.e. 18 °C BELOW the 72.80 °C hardware
> trip.** The appliance would refuse to cook once merely warm, and the
> technician chasing that nuisance lockout is exactly the person who would
> widen or disable the board's only software backstop.
>
> **Row 1 said `→ ∞ (≥ 1 MΩ)` beside `≥ 2.20 V`. Those are not the same test.**
> V = 2.2000 inverts to **R_ntc = 220 kΩ**, not 1 MΩ — a factor of 4.5. Going
> the other way, **R_ntc ≥ 1 MΩ requires V ≥ 2.2533 V**, and the worst-case open
> reading with ±1 % on R_REF (10 k) and R_CLMP (22 k) is
> `3.3 · 21780/(10100+21780) =` **2.2545 V**, which the nominal inversion turns
> into 1.089 MΩ. That is **1.2 mV of margin** before ADC INL — so a host
> implementing the RESISTANCE form can miss an unplugged NTC on a
> worst-case-tolerance board. **That is acceptance test (a) failing in exactly
> the way this section was written to prevent.** The voltage form has **54 mV**
> of margin (2.2545 worst-low against a 2.2000 threshold). **Implement the
> voltage test; treat the resistance column as explanatory.**

CH1/CH2/CH4–CH7 keep the unclamped model: `R = 10000·V/(3.3−V)`, same B and R25.
Deriving one curve and applying it to all eight is the mistake this box exists to
prevent. **This is arithmetic, not calibration — no bench step is required.**

## 3. JLCPCB order options

| Setting | Value |
|---|---|
| Layers | **4** (In1 = GND plane, In2 = 3V3 plane; NO plane north of y53 — keypad band, relay row, pockets and coil gaps are plane-free) |
| Dimensions | **188.000 × 92.000 mm** (measured from Edge.Cuts); **12 milled 1.000 mm isolation slots** as internal routs **plus the H4 east-edge notch (§1)** — confirm the fab preview keeps all 12 slots as internal routs and the notch as outline |
| Via tier | **ADVANCED small-via option required** — 0.25 mm via / 0.15 mm drill (via-in-pad escapes). Do NOT order standard 0.45/0.30. |
| Assembly | Standard SMT, TOP side only (**MEASURED: all 206 CPL rows are `top`; 0 footprints on B.Cu**), qty 5 (JLC minimum for this board; A-STOCK grades stock at qty × 5). Upload `fab/` FROM THIS ARCHIVE — nothing from `06_build/`. |
| CPL population | The **16** self-supplied refs (§4) carry `exclude_from_pos_files` — they are OFF the CPL entirely. **206 CPL rows**, every rotation sourced from a MEASURED per-LCSC authority row and every one on the pad-array-centre datum (**worst deviation 0.00050 mm, at `J_ESTOP`**, against a 0.05 mm tolerance). **READ THIS PRECISELY — the two directions are not the same.** A CPL row with no matching BOM line is a real defect: **stop.** The REVERSE is expected and must NOT stop the order: the BOM carries **208 coded designators over 61 rows** and the CPL **206**, so a handful of designators are on the BOM with no placement row **by design** — `J_ISOLOOP`, `J_LOADCELL`, `J_PI`, `J_TC` and the **12 reed relays** (K_U1–K_U6, K_D1–K_D4, K_PRESS, K_STOP). JLC reports that class too. Do not "fix" it by re-adding THT placements to an SMT-only run. |

**Order-day gate:** (a) stock recheck per §5 — **BLOCKING, one line is under the
floor today**; (b) preview shows all 12 slots as internal routs AND the H4 edge
notch intact; (c) ADVANCED 0.25/0.15 via option selected; (d) the §6 human gate
signed off, all ten A-POL rows; (e) the §3a web query answered.

### 3a. ⚠️ OPEN DFM QUERY — THE **0.850 mm WEB AT `H4`**, AND JLC'S OWN Q&A DOES NOT ANSWER IT

> **CORRECTION, 2026-07-30, recorded rather than quietly fixed.** This section
> first said the minimum web was **1.000 mm**. That figure came from scanning
> slot-END-to-OUTLINE pairs only and **missed the tightest pair on the board
> entirely**. The fresh-context layout lens found it; re-measured and confirmed
> exactly: **`H4`'s Ø2.700 mm hole wall stands 0.8500 mm from the east notch
> segment (191.500, 49.800)–(200.000, 49.800).** The query below is therefore
> about **0.850 mm**, not 1.000 mm, and there are now TWO features to ask about.

**Ask JLCPCB both of these before you pay, and get an answer in writing.**

**(1) THE 0.850 mm WEB AT `H4` — the tightest feature on the board.**
`H4` is an NPTH Ø2.700 mm mounting hole at (193.000, 52.000). Its wall is
**0.8500 mm** from the milled east notch. For comparison, the other three
mounting holes measure 2.650 mm (`H1`), 2.650 mm (`H2`) and 3.650 mm (`H3`) to
their nearest edge feature — H4 is the outlier by a factor of three.

> **RE-CONFIRMED AT SEAL TIME (2026-07-30) BY A DIFFERENT CONSTRUCTION.** Every
> drilled hole on the board was swept against the Edge.Cuts geometry: **105
> drilled holes**, and `H4` is the smallest web of all of them, with
> `J_ISOLOOP.1` next at **1.1500 mm** — the same two features in the same order.
> The raw sweep returns 0.8000 mm because `Distance()` measures to the EDGE of
> the outline stroke, and every Edge.Cuts graphic on this board is **0.1000 mm**
> wide (56 of 56); adding the 0.0500 mm half-stroke back gives **0.8500 mm to
> the cut centreline**, which is the figure the fab cuts to and the figure
> published above. Both numbers are right under their own definitions; **0.8500
> mm is the one to quote to JLCPCB.**

**AND `H4` CARRIES THREE MORE PROBLEMS AT THE SAME FEATURE, so read this as a
DO-NOT-FIT note as well as a DFM query:**

* Its copper clearance is **0.200 mm on all four layers** — GND on F.Cu/In1/B.Cu
  and **the 3V3 plane on In2**. A metal M2.5 fastener there sits 0.1 mm from a
  GND/3V3 sandwich. **DRC cannot see this**, because `min_hole_clearance` is
  itself set to 0.2 mm while JLCPCB publishes 0.254 mm.
* Its courtyard is the only one on the board that **overlaps a milled slot**
  (4.025 × 0.325 mm).
* `J_MODE` at 2.73 mm blocks any standard washer or standoff.

> **⚠️ DO NOT FIT A CONDUCTIVE FASTENER AT `H4` ON THESE FIVE BOARDS.** Use H1,
> H2 and H3 for mounting; leave H4 empty, or use a nylon screw with no washer.
> The `H4` creepage argument in §1 and the MANIFEST is about a washer bridging
> the NOTCH; this is a *different* and additional problem — the hole's own
> copper clearance to two different planes.

**(2) THE COMB SLOTS.** MEASURED from `source/cooksense.kicad_pcb` Edge.Cuts on
2026-07-30, all twelve slots and every slot web:

* **12 internal slots, every one exactly 1.000 mm wide.** Lengths 9.600 mm (×1)
  and 8.440 mm (×11). They sit in two staggered rows at y 49.100–50.100 and
  y 25.800–26.800.
* **Slot-to-slot web within a row: 22.040 mm**, all ten gaps identical.
* **Row-to-row web: 22.300 mm**, and the two rows never overlap in x at all, so
  nothing narrower exists between them.
* **Slot-to-board-outline web: the minimum over all 24 slot ends is
  `1.000 mm` — exactly once**, at the row-A slot 1 WEST end (slot x starts
  13.000 mm; the board outline is at x = 12.000 mm). **Every other web is
  ≥ 9.760 mm.**

**THE QUESTION, in the two parts it actually has:**

JLCPCB publishes a minimum *slot width* of 1.0 mm, which all twelve comb slots
meet **exactly, with zero margin** — they were widened from 0.600 mm for this
revision precisely because 0.600 was 40 % under that published floor. What JLC
does **not** publish is a minimum **remaining wall (web)**, and its Q&A on the
point is unanswered. So:

1. **Is a 0.850 mm FR4 web between a Ø2.700 mm NPTH wall and a milled notch
   acceptable?** (feature `H4`, above — the binding case)
2. **Is a 1.000 mm FR4 web between an internal rout and the board outline
   acceptable?** (row-A slot 1's west end: slot starts x = 13.000, outline is at
   x = 12.000. Every other one of the 24 slot ends is ≥ 9.760 mm from the
   outline, so this is one feature, not a pattern.)
3. **And confirm the 1.0 mm slots themselves route at exactly 1.0 mm** rather
   than being widened or refused, since there is no margin in them at all.

**BOTH WEBS ARE UNVERIFIED AGAINST THE FAB'S REAL CAPABILITY.** If JLC says (2)
is too thin, the fix is to shorten row-A slot 1 at its west end — it is the
longest slot (9.600 mm against 8.440 mm for the other eleven) and has 1.160 mm
of length to give before it merely matches its siblings. If JLC says (1) is too
thin, `H4` moves, which is a placement change. **Either is a source edit and a
new revision — never a hand-edit of the gerbers** (canon M3).

## 4. ⚠️ SELF-SUPPLIED / HAND-SOLDER — 16 REFS, 14 OF THEM DO-NOT-SUBSTITUTE

**Sixteen** refdes are not JLC-assembled, self-supplied and hand-soldered at
integration. **14 of the 16 are DO-NOT-SUBSTITUTE; exactly 2 may be
substituted.** The count has been stated three inconsistent ways in earlier
revisions, so here it is once, exhaustively, and the table below carries a row
for every one:

| class | refs | count | substitute? |
|---|---|---|---|
| reed relays | K_U1..K_U6, K_D1..K_D4, K_PRESS, K_STOP | 12 | **NO** (ADR-0006 isolation comb) |
| thermocouple jack | J_TC | 1 | **NO** (cold-junction interface) |
| isolated terminal block | J_ISOLOOP | 1 | **NO** (ADR-0013; it is the mains-side barrier connector) |
| through-hole connectors | J_LOADCELL, J_PI | 2 | **YES** |
| | | **16** | **14 no / 2 yes** |

The release MANIFEST's `not_assembled:` line is GENERATED from
`03_src/cooksense/rules/assembly.yaml` as a bare refdes list (canon A-POP:
refdes only in manifest lines, no prose).

```
K_U1 K_U2 K_U3 K_U4 K_U5 K_U6 K_D1 K_D2 K_D3 K_D4 K_PRESS K_STOP   (12 reeds)   NO SUBSTITUTE
J_TC                                                               (TC jack)    NO SUBSTITUTE
J_ISOLOOP                                                          (v1.3)       NO SUBSTITUTE
J_LOADCELL  J_PI                                                   (THT conns)  substitutable
```

**J_LOADCELL and J_PI are new to this list and that is a v1.0/v1.1 CORRECTION,
not a v1.3 change.** Both are pure through-hole (MEASURED: 5/5 and 40/40 plated
drilled pads, F.Paste on none) on a `service: standard, sides: [top]` order,
which is reflow SMT only — no process solders them. Both sealed releases
nevertheless shipped them as CPL placement rows. They keep their LCSC codes on
the BOM so the order sheet still says what to buy; they simply stop being
machine-placement instructions. **Substitution IS allowed for these two** (any
B5B-XH-A equivalent; any 2x20 2.54 mm female header).

| Ref(s) | Part | Notes |
|---|---|---|
| K_U1..K_U6, K_D1..K_D4, K_PRESS, K_STOP (×12) | **Standex `DIP05-1A72-13L`** reed relay | **THE PIN-OUT IS 13, NOT 12, AND THAT IS THE ENTIRE REASON v1.0–v1.6 ARE DO-NOT-ORDER.** The land on this board is `Relay_StandexDIP_1A_pinout13` (BOM row 1, verbatim). If you are holding an older release, its land is `…_pinout12` and the relays will not fit it. **No substitutes** — the isolation-comb creepage and the coil/contact column pinout ARE the safety argument (ADR-0006). Approved alternate: the `-13D` variant (identical pin-out, internal coil diode). Order 16 (12 + 4 spares). THT hand-solder. |
| **THE `J_ESTOP` SHORTING PLUG** | JST SH 3-circuit housing + 2 contacts | **NOT ON THE BOM AND NOT ON THE CPL — AND THE BOARD DOES NOT WORK WITHOUT IT.** See the banner at the top of this document for the pinout (**bridge 2–3, never 1–2**) and the stocked equivalents. This is the one self-supplied item whose absence is indistinguishable from a dead board. |
| J_TC | **Omega PCC-SMP-K** panel Type-K jack | All 7 catalog hits stock 0 (2026-07-25). Ø1.77 mm PC pins + 2 NPTH bracket holes match the Omega PCC-OST-SMP drawing. **No substitutes** — the chromel/alumel jack contacts ARE the cold-junction interface; a brass lookalike injects a parasitic junction. THT hand-solder. |
| J_ISOLOOP | **KF350-3.5-4P** 4-pole isolated terminal block | LCSC C42400616, stock 0 by design — off the CPL, JLC has no CAD for it (§6 item 17). **No substitutes** — it is the connector that carries the isolated contactor loop across the barrier, and its 3.50 mm pitch plus the 2.0000 mm pour moat are the `opto_isolation_2mm` argument (ADR-0013). Pole legend and the polarity/shared-net warnings are in §11. THT hand-solder. |

## 5-0. 🛑 **`J_THERM_A` / `J_THERM_B` — YOU CANNOT BUY THIS PART TODAY. READ THIS BEFORE YOU ORDER ANYTHING.**

> **This board is CORRECT. It is not ORDERABLE today, and the reason is one BOM
> line — not one millimetre of copper.** Nothing on this page asks you to change
> the board. It asks you to make one purchasing decision.
>
> *(**v1.7 IS NOT SEALED** — see the first screen. Under the two-claim review
> vocabulary introduced 2026-07-30 (`217ea175`) the TOPOLOGY lens grades this
> candidate `design_verdict: SOUND` + `order_verdict: BLOCKED-SOURCING`, which is
> exactly the sentence eight previous passes had no field for: the design is
> correct AND you cannot buy it today. **The sourcing line is no longer what
> blocks the seal.** What blocks it is the LAYOUT lens, re-gated on the same
> vocabulary, returning `design_verdict: DEFECTIVE` on two P0s about the LDO's
> declared load and thermal ceiling — neither of them copper, both confirmed by
> independent re-measurement. The gate line `SOURCING: BLOCKED-1 (C265111;
> measured 2026-07-30)` is carried in `MANIFEST.txt` and on this document's first
> screen, and `release_freshness_check.py` check (f) A-BUY grades the count, the
> code and the date against the shipped measurement in both directions — a
> release may neither hide a blocked line nor invent one. Mechanical design
> gates: DRC 0/0/0, `policy_audit` FAIL=0. See `verification/A-STOCK_waiver.md`
> §5 and `verification/redteam_layout.md`.)*

**This release's BOM names the GENUINE JST part, `C265111`, deliberately.** The
substitution below is an **ORDER-TIME** path, not a design change: it is a
BOM-line swap and nothing else.

### The live reading, with its timestamp

Measured **2026-07-30T21:33:59Z** against JLC's own catalog
(`selectSmtComponentList`), queried both through `jlc_stock_check` and
independently of it — the two agreed:

| LCSC | part | brand | stock | **MOQ** | buyable today? |
|---|---|---|---|---|---|
| **`C265111`** (**what the BOM says**) | SM08B-GHS-TB(LF)(SN) | **JST** | **5** | **21** | **NO** |
| `C22391766` | SM08B-GHS-TB | JST | 0 | 444 | NO |
| `C42376901` | SH-SM08B-GHS-TB(LF)(SN) | SHOU HAN | **6030** | **1** | yes |

Control query the same minute: `C5620` (74HC238D) = 5212 in stock, so the 5 and
the 0 are the catalog's answer, not a dead field.

### ⚠️ THE NUMBER TO WATCH IS **21**, NOT 10 — AND THE PART IS **UNBUYABLE**, NOT MERELY SHORT

The build needs **10** pieces (2 per board × 5 boards) and the stock gate's floor
is 10. **Ignore both.** `C265111` carries `minPurchaseNum` **21** against a
`stockCount` of **5**:

> **You cannot order 21 pieces when 5 exist, and you cannot order 5.**
> The minimum order quantity is above the entire stock, so *no purchase of this
> part is possible at any quantity today.* "Wait for stock ≥ 10" is the WRONG
> thing to watch. **Watch for `stockCount` ≥ 21** — the first point at which any
> purchase is possible at all. The build then only consumes 10 of the 21.

`C265111` read **0** on 2026-07-29 and **5** on 2026-07-30, so the line is
restocking rather than discontinued — but that says nothing about *when* it
crosses 21.

### The substitute, and exactly how far it is from the board

`C42376901` (SHOU HAN SH-SM08B-GHS-TB) is stocked 6030 deep at MOQ 1. Its fit to
**this board's copper** was measured, not assumed — JLC's own recommended land
for each code read out of the EasyEDA `packageDetail` pad records, this board's
pads read out of `source/cooksense.kicad_pcb` with `pcbnew`, then a
translation-only rigid fit (no rotation, no reflection):

| | signal pads 1–8 | mechanical tabs | mirrored? |
|---|---|---|---|
| `C265111` (genuine) vs board | **0.0002 mm** | 0.0002 mm | no |
| `C42376901` (clone) vs board | **0.0100 mm** | **0.0399 mm** | no |

Pitch: board 1.2500 / genuine 1.2499 / clone 1.2499 mm. Tab \|x\|: board 6.2250 /
genuine 6.2249 / clone 6.2249 mm. The two deltas that make up the clone's
residual, decomposed rather than buried: its own recommended land is
0.100 × 0.100 mm **larger** per signal pad (a fillet preference), and its
signal-row-to-tab-row separation is 3.1501 mm against the board's 3.2000 — a
0.0499 mm row offset absorbed inside a 1.700 mm-tall pad. JLC's two lands also
number the mechanical tabs **oppositely** (pad 9 sits at x −6.225 on one and
+6.225 on the other); that is electrically null **on this board and only on this
board**, because both tabs are on `GND` **and both are numbered `MP`** on the
board, so the vendors' numbering difference cannot reach it.

**PAD SIZES, INCLUDING THE MECHANICAL TABS — and this one cuts TOWARD the
clone.** The residual above is a centre-position fit and is structurally blind
to pad size, which is the one term that governs a solder-fillet retention tab —
i.e. the exact axis this section flags as unverified. Published here after the
v1.7 topology re-gate pointed out the omission (RG-P2-2):

| | board copper | `C265111` recommended | `C42376901` recommended |
|---|---|---|---|
| signal pad | 0.600 × 1.700 | **0.600 × 1.700 (exact)** | 0.700 × 1.800 |
| **mechanical tab** | **1.000 × 2.700** | **1.210 × 2.700** (board is 0.210 mm / 17.4 % narrow) | **1.000 × 2.500** (width matches board exactly) |

So "the board's footprint IS the genuine part's land" is true **only on the
eight signal pads**. On the retention tabs the board's copper is 17.4 % narrower
than JLC recommends for the genuine part and **matches the clone's tab width
exactly**. This is a KiCad-library-vs-JLC-library difference, it pre-dates the
substitution question entirely, and it is stated because a waiver that hides a
term on its own declared-unverified axis is not a waiver.

### 🛑 HOW TO ACTUALLY SUBSTITUTE — AND WHY "EDIT ONE BOM CELL" IS WRONG

> **An earlier version of this section said the swap "changes ZERO BYTES of the
> fab set — you edit one cell of `fab/bom.csv`." THAT INSTRUCTION IS WRONG AND
> WOULD HAVE COST YOU AN ORDER.** It is corrected here rather than quietly
> reworded, because a buyer who followed it exactly would have shipped the
> unbuyable part. Found by the v1.7 topology re-gate (RG-P1-1).

Two things were wrong with it:

1. **`fab/bom.csv` is not the file JLC receives.** The assembly step uploads
   **`fab/bom_jlc.csv`** and **`fab/cpl_jlc.csv`** — `export_jlc_package.py`
   says so in its own header: *"the zip contains gerbers + drills + job file
   ONLY (JLC's PCB uploader); bom_jlc.csv / cpl_jlc.csv upload separately in
   the assembly step."* The two BOMs happen to be byte-identical today, so
   nothing would have warned you that you had edited the wrong one.
2. **The CPL carries the code too.** On this board `fp.GetValue()` for these
   two footprints *is* the string `C265111`, and the exporter feeds that one
   value to both the BOM `Comment` column and the CPL `Val` column. Edit only
   the BOMs and you ship a CPL naming `C265111` against a BOM naming
   `C42376901` — the exact BOM/CPL disagreement `release_freshness_check.py`
   treats as proof that a CSV was hand-edited.

**The complete cell census of `C265111` inside `fab/` — 6 cells, 4 files:**

| file | line(s) | column | uploaded to JLC? |
|---|---|---|---|
| `fab/bom.csv` | 51 | `LCSC` | no — reference copy |
| **`fab/bom_jlc.csv`** | 51 | `LCSC` | **YES — assembly step** |
| `fab/cpl.csv` | 77, 78 | `Val` | no — reference copy |
| **`fab/cpl_jlc.csv`** | 77, 78 | `Val` | **YES — assembly step** |
| all 11 gerbers + both `.drl` | — | — | **0 occurrences — nothing changes** |

**✅ THE CORRECT REMEDY IS TO REGENERATE, NOT TO HAND-EDIT (canon M3).** The
LCSC code is authored in `03_tscircuit/src/cooksense.tsx` at lines 1216 and
1218 — `supplierPartNumbers={{ jlcpcb: ["C265111"] }}` on both refs. Change it
there and rebuild; every one of the six cells then follows from source and the
BOM/CPL cannot disagree. Hand-editing four CSVs is what this repo's own gates
are written to detect.

**If you hand-edit anyway** (e.g. the order desk will not wait for a rebuild):
edit **all six cells**, and re-check the BOM and CPL against each other before
paying — §6's order-preview gate is your last chance to catch a dropped line.

**What genuinely does not move, and it is the engineering claim that matters:**
all 11 gerbers, both drill files (`J_THERM_*` has **0 drilled pads** — there is
no hole that could move), the footprint, and every CPL **coordinate, layer and
rotation** — `J_THERM_A` stays at `(32.0, −96.75, top, 0.0)` and `J_THERM_B` at
`(54.0, −96.75, top, 0.0)` either way. That geometric invariance is what the
land-pattern table above establishes.

### 🛑 THE ONE THING A SUBSTITUTING BUYER MUST CHECK — IT IS **NOT** VERIFIED HERE

> **Pad correspondence is not MATE compatibility, and mating is the part nobody
> has measured.**
>
> `J_THERM_A` / `J_THERM_B` are the connectors that carry the **thermistor
> pods** — third-party SHT45 modules on **genuine JST GHR-08V pigtails**.
> **Whether a genuine GHR-08V plug seats and RETAINS in a SHOU HAN shroud is
> UNVERIFIED.** ADR-0024's pod-mismate analysis is written about the **GH
> family's** geometry; a clone shroud is outside what it measured. The vendor
> describe strings differ on body material (LCP vs PA9T) and colour (beige vs
> white) — and a retention feature is exactly the kind of thing a
> dimensionally-equivalent clone gets subtly wrong.
>
> **If you substitute: mate one clone header with one genuine GHR-08V pigtail
> and pull it, BEFORE you commit the assembly order.** This check costs one part
> and five minutes.
>
> **⚠️ CORRECTION — WHAT A DROPPED POD ACTUALLY DOES, MEASURED.** An earlier
> version of this box said a pod falling out *"removes the `TEMP_OK` term from
> the safety chain."* **That is backwards, and being wrong in the alarming
> direction is still wrong** (found by the v1.7 topology re-gate, RG-P2-3). A
> dropped pod **ASSERTS** the term restrictively — the open-thermistor detect
> exists for exactly this. Measured on the board's own values (`R_REF0` 10 kΩ,
> `R_CLMPA` 22 kΩ, `R_OPENT` 62 kΩ, `R_OPENB` 100 kΩ):
>
> ```
> TH_CAM_A, pod UNPLUGGED  = 22/(10+22)   = 0.68750 of rail
> TCAM_OPEN threshold      = 100/(62+100) = 0.61728 of rail
> margin  = 0.07022 of V_rail  ->  231.7 mV at 3.300 V, 224.8 mV at 3.201 V
>           RAIL-INDEPENDENT and positive at every rail voltage
> ```
>
> ⇒ `U_COMP2` output LOW ⇒ **`TEMP_OK` LOW** ⇒ `KEY_RELAY_ALLOWED` and
> `CTR_SAFE` drop and the fault latch **sets**. Opening pin 2 (GND) gives the
> same node voltage and the same result. Only pin 5 (`TH_CAM_*`) of the eight
> reaches a permission at all.
>
> **So the real cost of a bad clone shroud is nuisance latched stops in the
> field, not a defeated interlock** — a chattering pod repeatedly stops the
> machine. Still worth five minutes; not a safety hazard. The same mechanism is
> why boards that arrive with these connectors unpopulated announce themselves
> rather than running unprotected.

### Your three options, ranked

1. **WAIT** for `C265111` `stockCount` ≥ **21**, then order exactly as sealed.
   Zero new risk, zero rework, no paperwork. **This is the intended path and it
   is why the BOM names the genuine part.**
2. **SUBSTITUTE `C42376901`** — after the mate/pull check above, change the code
   in `03_tscircuit/src/cooksense.tsx` (lines 1216/1218) and **regenerate**; or,
   if you must hand-edit, change **all six cells** listed in the census above —
   **`bom_jlc.csv` and `cpl_jlc.csv` are the files JLC actually receives.**
   Gerbers, drill and all CPL geometry stay byte-identical either way.
3. **HAND-FIT.** Possible (14 refs are already hand-fit) but worst: it needs
   `exclude_from_pos_files` and a **board regeneration**, i.e. a copper
   revision's worth of verification spent on a sourcing problem, on a 1.25 mm
   8-circuit SMD header that is a harder hand-solder than any of the 14.

*(Machine-readable home of all of the above: `03_src/rules/assembly.yaml`
`sourcing_plan:`. The full A-STOCK waiver argument with its raw command output:
`verification/A-STOCK_waiver.md` in this archive.)*

---

## 5. ⚠️ MANDATORY ORDER-DAY STOCK RECHECK

**THIS IS BLOCKING AND ONE LINE IS UNDER THE FLOOR TODAY.** Re-run
`jlc_stock_check` on order day against `fab/bom.csv`. Every figure below is a
LIVE LCSC catalog read on **2026-07-30** and is shipped in
`verification/stock_check.json` / `stock_check.txt` in this archive.

| Ref(s) | LCSC | stock 2026-07-30 | qty | verdict |
|---|---|---|---|---|
| **`J_THERM_A`, `J_THERM_B` (SM08B-GHS-TB)** | **`C265111`** | **5** (MOQ **21**) | 2 | **`LOW_STOCK` — THE ONE FAILING LINE. The gate wants 10 (qty × 5), but `minPurchaseNum` 21 > stock 5 means it is UNBUYABLE AT ANY QUANTITY today. Watch for stock ≥ 21 — see §5 note.** |
| `U_EFUSE` (TPS259573DSGR) | `C2653844` | **103** (re-read 21:02Z, unchanged) | 1 | OK — the thinnest passing line, watch it |
| `R_OVB` (26.1 kΩ, the OVLO divider leg) | `C407739` | **227** | 1 | OK |
| `J_PWR` Micro-Fit (43650-0224) | `C587657` | **140** | 1 | OK |
| `J_KEY_MATRIX` (2.54-2*20PPC104) | `C35165` | **4275** | 1 | OK |
| `U_ULNA`, `U_ULNB` (TBD62083AFWG) | `C165895` | **2300** | 2 | OK — the NEW coil driver |
| `U_AND*` etc. (SN74LVC1G11DBVR) | `C22046` | **3974** | 10 | OK |

`jlc_stock_check` verdict, verbatim: `FAIL: 57/58 coded BOM lines have stock >=
5 x qty (1 with problems); 3/61 lines carry NO LCSC and were NOT graded by this
tool`. The three ungraded lines are the declared `not_assembled` self-supplied
parts (12 reed relays, `J_ISOLOOP`, `J_TC`) — they have no LCSC by design.

**`C265111` READ STOCK 0 ON 2026-07-29 AND 5 ON 2026-07-30.** It is restocking,
not discontinued. `03_src/rules/assembly.yaml` `sourcing_plan:` carries the
measured three-option plan and its evidence:

1. **RE-QUERY AT ORDER TIME** — `minPurchaseNum` on the genuine JST part is 21
   (not 444), so one reel restock clears a 5-board build twice over. Zero new
   risk. **This is the intended path and it is why the line stays on the CPL
   with its genuine JST code.**
   > ⚠️ **READ THE THRESHOLD CORRECTLY — IT IS 21, NOT 10** (measured
   > 2026-07-30T21:02Z, live `selectSmtComponentList`). `C265111` reads
   > `stockCount` **5** against `minPurchaseNum` **21**. Because the MOQ
   > exceeds the stock, the genuine JST part is **not merely SHORT — it is
   > UNBUYABLE AT ANY QUANTITY TODAY**: you cannot order 21 pieces when 5
   > exist, and you cannot order 5. So "wait for stock ≥ 10 (the gate's
   > 5 × qty 2)" is the WRONG thing to watch. **Watch for `stockCount` ≥ 21**,
   > which is the first point at which any purchase is possible at all; the
   > build only needs 10 of the 21. The 0 → 5 move in one day says the line is
   > restocking, not discontinued, but nothing about *when* it crosses 21.
2. **SUBSTITUTE `C42376901`** (SHOU HAN SH-SM08B-GHS-TB, stock **6030** and
   `minPurchaseNum` **1** — re-read live 2026-07-30T21:02Z; it was 6086 on
   07-29, so it is moving but deep). **Its land pattern is MEASURED drop-in**: `jlc_twin` fitted
   JLC's own footprint for that code against this board's
   `JST_GH_SM08B-GHS-TB_1x08-1MP_P1.25mm_Horizontal` at **0.01 mm residual,
   NON-MIRRORED, `jlc_offset` 0, independently on both refs**. No copper, no CPL
   rotation and no footprint change follows the swap. **WHAT IS NOT MEASURED,
   said plainly: pad correspondence is not MATE compatibility.** Whether a
   genuine GHR-08V plug from a third-party SHT45 pod pigtail seats and retains
   in a SHOU HAN shroud has NOT been verified, and ADR-0024's pod-mismate
   analysis is written about the GH FAMILY's geometry — a clone shroud is
   outside what it measured. **This option needs a plug-mate confirmation
   first, and it is the user's call, not the design's.**
3. **DECLARE `not_assembled` AND HAND-FIT.** The mechanism exists (14 refs
   already hand-fit) but a 1.25 mm 8-circuit SMD header is a harder hand-solder
   than any of them, and it needs `exclude_from_pos_files` plus a board
   regeneration — a new copper revision's worth of verification for a sourcing
   problem.

**A-STOCK is satisfied by that entry's MEASURED NUMBER AND DATE, which is what
the gate asks for. It is NOT satisfied by the claim that stock will return.**

**RE-CONFIRMED AT SEAL TIME, 2026-07-30T21:33:59Z**, by a second read taken
independently of `jlc_stock_check` (raw `selectSmtComponentList`, no shared
code): `C265111` stock **5** / MOQ **21**; `C42376901` stock **6030** / MOQ
**1**; `C22391766` stock **0** / MOQ **444**; control `C5620` = **5212**. Every
figure in the table above stands. The decision this release seals against, and
the mate/pull check a substituting buyer owes, are in **§5-0 above** — read that
first.

## 6. ⚠️ ORDER-PREVIEW HUMAN GATE — tick EVERY row against the JLC assembly preview BEFORE paying

CPL rotation is this board's proven failure mode (v1.0/v1.1 banner). **Every
one of the 206 CPL rotations resolves from a per-LCSC row in the authority
table** — A-ROT green, `jlc_rotation_audit --table` **64 rows OK** (re-run
2026-07-30, verdict verbatim: *"ROTATION-TABLE OK: 64 rows, each an
independently MEASURED authority (M-PROV) with its polarity channel declared
(A-POL)"*), and no `--allow-unsourced-rotations`, so not one row fell back to
the name-keyed DB.

**Two honest qualifiers on that sentence, because an earlier revision of this
paragraph said "nothing below is guesswork any more" and that claimed more than
the archive can show you:**

1. **You cannot re-derive it from this archive alone.** The 61-row authority
   table lives in the fleet repo, not here. What ships here is
   `verification/rotation_measurements_v13.txt` — the **15** codes measured for
   this revision, covering **26 of the 189** CPL rows out of 51 distinct codes.
   **And that overstates the in-archive evidence: 13 of those 15 read
   `ROW: (WITHHELD — single-channel)`.** Only **C6186 (U_LDO) and C8185**
   (4 refs) were landed as authority rows from measurements that ship here, so
   the in-archive LANDED provenance is **2 codes / 5 CPL rows**, not 15/26. The
   13 withheld codes are all covered either by the §6 A-POL human gate or by the
   bidirectional-part exclusion, so nothing is unguarded — but a withheld
   measurement must not be mistaken for a landed one. For the other 36 codes you
   are trusting a table you cannot open. That is why §6 exists at all.
2. **One disagreement inside this archive is now RESOLVED, and the resolution
   was against my own earlier measurement.**
   `verification/rotation_C22046_measurement.md` reports a second operator that
   disagreed by 180° with the authority table on **C189896** (**on v1.7 that
   code is `J_RH_AMBIENT` and `J_RH_EXHAUST` ONLY** — `J_DOOR` is deleted, and
   `J_ESTOP` and `J_MODE` have left the GH family for SH and ZH
   respectively) and **C2683602** (J_KEY_MATRIX), and by
   **180°** on **C125121** (U_OPTO, the isolation part — that operator returned
   90 where the table says 270). **Re-measured 2026-07-26:
   the authority table is right and that second operator was wrong.** It applied
   a standard counter-clockwise rotation matrix to KiCad coordinates, whose Y
   axis points DOWN — which mirrors the fit and therefore swaps 0 with 180 and
   90 with 270. Verified empirically against pcbnew on `J_KEY_MATRIX` at
   orientation −90°: pcbnew puts pad 1 at (+1.850, −5.625) from the anchor, the
   y-down matrix reproduces it exactly and the CCW matrix returns
   (−1.850, +5.625). Re-run with the correct matrix, a comparison of the two
   raw `.kicad_mod` files — **no board frame and no operator involved** — agrees
   with the landed table on **all seven** codes:

   | LCSC | rms 0 / 90 / 180 / 270 | best | separation | landed | |
   |---|---|---|---|---|---|
   | C189896 | 0.0000 / 2.5000 / 3.5355 / 2.5000 | 0 | exact | 0 | AGREE |
   | C265111 | 0.0050 / 4.0520 / 5.7304 / 4.0520 | 0 | 810x | 0 | AGREE |
   | C2683602 | 0.0049 / 5.0792 / 7.1831 / 5.0792 | 0 | 1037x | 0 | AGREE |
   | C157991 | 7.1276 / 5.0402 / 0.0566 / 5.0402 | 180 | 89x | 180 | AGREE |
   | C587657 | 2.7500 / 1.9526 / 0.2500 / 1.9526 | 180 | 8x | 180 | AGREE |
   | C125121 | 7.1366 / 10.0899 / 7.1366 / 0.2350 | 270 | 30x | 270 | AGREE |
   | C2887273 | 0.0300 / 3.7972 / 5.3700 / 3.7972 | 0 | 127x | 0 | AGREE |

   **Nothing in the CPL changes.** The shipped CPL was already correct on all
   seven. What changed is that a documented open disagreement is now closed, and
   closed by a method that shares no code with either operator (canon M1).

What remains is a narrower and sharper obligation.

**A-POL SINGLE-CHANNEL — 10 codes across 13 refs.** For these, the rotation was
fitted by pad NUMBER and **no numbering-free channel could corroborate it**,
because a dual-row SOIC/TSSOP/SSOP pad cloud is its own 180° reflection. A high
fit margin is not confidence: on another board this same fit returned 180° at a
17.7x margin and the true answer was 0°. The generated list ships as
`fab/rotation_human_gate.txt` — **that file is the checklist, and it is a list,
not a sentence**:

```
C10092:   U_SR1            C2653162: U_TC          C6820:  U_SCHM
C133954:  U_ONESHOT        C2653844: U_EFUSE       C7984:  U_COMP, U_COMP2
C16939:   U_ADC            C558584:  U_EXP         C5620:  U_DECD, U_DECU
C165895:  U_ULNA, U_ULNB
```

**THIS LIST IS REGENERATED FOR v1.7 AND TWO CODES MOVED.** `C165895`
(TBD62083AFWG) replaces the old `C9683` — it is the NEW DMOS coil driver of
ADR-0023, it is a SOIC-18W whose pad cloud is its own 180° reflection, and it
drives twelve relay coils: **a 180° error here puts twelve coil returns on the
wrong pins.** `C558584` (MCP23017 SSOP-28, `U_EXP`) replaces the old `C506653`.
Both are on this gate for the first time. The file that governs is
`fab/rotation_human_gate.txt` IN THIS ARCHIVE, not the text above.

(C5158048 was on this list until its datasheet was read: the PESD5V0S1BA is
**bidirectional — both pins are cathodes** — so it has no orientation for a human
to confirm and it is excluded. Its refs on v1.7 are D_COILEN, D_ESD_IN, D_ESTOP,
D_LCCLK and D_LCDAT — `D_DOOR` was deleted with the door channel (ADR-0025). Note our footprint still draws a cathode band; that is a
cosmetic defect logged for v1.4, not an assembly risk.)

A human must confirm each item below in JLC's rendered assembly preview against
our silk/fab layers:

| # | Item | What to look at |
|---|---|---|
| 1 | **U_OPTO** (LTV-817S, C125121, SMDIP-4) | Pin-1 dot on the JLC render matches OUR silk pin-1 (LED side, west). **The three-way disagreement earlier revisions recorded here (name-DB 0 / twin 270 / independent fit 90) is RESOLVED:** the independent operator had a Y-axis frame error, and the operator-free re-fit gives **270 at 30x**, agreeing with the shipped CPL (§6 preamble). Check it anyway — this is the isolation part and the board's only 90/270-class rotation. A rotated opto swaps LED and transistor sides across the isolation barrier. |
| 2 | ~~**J_DOOR**~~ | **DELETED FROM THE NETLIST (ADR-0025). There is no such connector on this board. Nothing to tick.** If the preview shows anything at all here, STOP — you are looking at the wrong archive. |
| 3 | **J_ESTOP** (**JST SH SM03B-SRSS-TB, `C160403`, 1.00 mm, 3 circuits** — NOT the GH-5 earlier revisions named) | Mouth EAST; **circuit 1 = `GND`, circuit 2 = `3V3`, circuit 3 = `ESTOP_RAW_IN`**, per silk. This is the connector the SHORTING PLUG goes into and the whole board is inert without it — re-read the banner at the top of this document. A 180° error here puts the sense line where GND belongs. |
| 4 | **J_MODE** (**JST ZH S4B-ZR-SM4A-TF, `C485354`, 1.50 mm, 4 circuits** — the ADR-0018 mechanical key; NOT the GH-5 earlier revisions named) | Mouth EAST; pin-1 matches silk. Its export applies a MEASURED `90 + 180 -> 270` correction — confirm it landed. |
| 5 | **J_RH_AMBIENT** (JST-GH SM05B, C189896) | Mouth SOUTH; pin-1 matches silk. |
| 6 | **J_RH_EXHAUST** (JST-GH SM05B, C189896) | Mouth SOUTH; pin-1 matches silk. |
| 7 | **J_THERM_A** (JST-GH SM08B, C265111) | Mouth SOUTH; pin-1 matches silk. |
| 8 | **J_THERM_B** (JST-GH SM08B, C265111) | Mouth SOUTH; pin-1 matches silk. |
| 9 | **J_KEY_MATRIX** (JST-GH SM10B, C2683602) | Mouth WEST (keypad ribbon); pin-1 matches silk. Formerly one of the three disputed codes; the dispute was **resolved 2026-07-26 in the authority table's favour** (offset 0, 1037x separation, operator-free file comparison — see the §6 preamble). Still on this gate, because a resolved dispute is a reason to look, not a reason to stop looking. |
| 10 | **J_PWR** (Molex Micro-Fit, C587657) | Polarizing peg orientation AND pin-1 (5 V) position vs silk. The 2.9× separation an earlier revision quoted came from the operator with the Y-axis frame error; the operator-free re-fit gives **180 at 8×** (2.7500 / 1.9526 / 0.2500 / 1.9526). Still on this gate — a polarising peg is worth an eyeball. |
| 11 | **J_LOADCELL** (JST-XH B5B-XH-A, C157991) | **WILL NOT APPEAR IN THE PREVIEW — it is off the CPL** (`exclude_from_pos_files`; one of the 37 excluded refs, see §3/§4). There is nothing to tick here at JLC. Confirm instead that the preview shows NOTHING placed at J_LOADCELL, and check pin-1 vs silk **on the bare board at hand-solder time**. |
| 12 | **CE1** (220 µF POLARIZED electrolytic, C2887273) | **v1.0 AND v1.1 shipped this cap at rotation 180 = REVERSED across a live 5 V rail.** Confirm the "+" / crescent on the render matches OUR pad 1 (west end, net 5V_PROTECTED). The measured `C2887273,0` row now governs and the export deliberately raises ROT-XCHECK-180 against the stale name-DB rule. Independent fit says 0 at 126.6×; "polarized part shipped reversed" is verbatim the usb-hub-3s-v3 v1.5 incident. |
| 13 | **J_PI** (2×20 socket, C35165) | **WILL NOT APPEAR IN THE PREVIEW — it is off the CPL** (same exclusion list). Carried from v1.1: JLC's library winds pin numbering by ROW where ours winds by COLUMN (adjudicated MIRRORED finding — symmetric hole grid, no physical mirror possible). Nothing to tick at JLC; pin-1 identity comes from our netlist + silk, not JLC's numbering, and is checked **on the bare board**. |
| 14 | **SOIC-16 — THREE parts, two codes** (**C5620 = U_DECD + U_DECU**; **C10092 = U_SR1**, SN74HC595DR) | Carried from v1.1: ROT-DB-SUGGEST 90° class — confirm pin-1 on **all three**. An earlier revision printed "U_DECU/U_DECD, C5620/C10092" as if both codes were the decoders; **C10092 is U_SR1**, which is separately on the A-POL single-channel list, so a reviewer following the old text would have skipped it. |
| 15 | **Diode cathode bands — the THREE that HAVE a cathode** (**D_KSTOP**, **D_REVCLAMP** — both C8678/SS34 — and **D_TVS**, C113974/SMBJ5.0A) | The board carries **8** diodes: **3** with a cathode band and **5** bidirectional. Band matches silk on those three. **DO NOT "correct" D_ESD_IN, D_ESTOP, D_COILEN, D_LCCLK or D_LCDAT for band direction — they are PESD5V0S1BA, which is BIDIRECTIONAL: both pins are cathodes** (JLC's own model name ends `_BI`; see §13 gap 4). An earlier revision demanded "band matches silk on every one" for all eight, which invites a false-reject on five parts that have no polarity to get wrong. **D_KSTOP is the K_STOP coil flyback** (`.1 -> 5V_STOP`, `.2 -> COIL_STOP_N`): reversed it is a forward-biased short from the STOP rail into the coil driver and the STOP relay loses its clamp. It was missing from this list until 2026-07-26. **CORRECTED 2026-07-26 — why D_KSTOP (C8678) and D_TVS (C113974) are NOT in the A-POL list above but ARE here.** An earlier revision said these two "HAVE" a numbering-free channel and "carry `two-channel` rows". **That was false and this archive's own evidence contradicts it:** `verification/rotation_measurements_v13.txt` records both as `polarity=single-channel`, `NO usable numbering-free channel`, `ROW: (WITHHELD — single-channel)`, and `verification/twin_report.csv` marks C8678/D_KSTOP, C8678/D_REVCLAMP and C113974/D_TVS as **POLARITY-FIT-BLIND** — *"the numbering-free channel cannot run, so ONLY the human order-preview gate stands between this part and a 180deg reversal."* No cathode-band shape measurement exists for either code. **They are absent from the generated A-POL list because the generated list is keyed to codes the twin could FIT and these three could not be fitted at all — which is worse, not better.** Counting them, the true single-channel population is **12 codes / 16 refs**, not the 10/13 the generated `fab/rotation_human_gate.txt` prints. **Treat THIS row as the only defence for these three refs.** |
| 16 | **The 10 SOT-23-6 gates** (U_AND1-3, U_CAND1-2, U_DECUEN, U_DECDEN, U_FAULTAND, U_LATCHG, U_OSCLR, C22046) | The measured C22046,180 rotation row must be in effect (v1.2 re-export proved exactly 10 changed cells, 270→180). Confirm pin-1 on at least U_AND1 in the preview. |
| 17 | **J_ISOLOOP** (KF350-3.5-4P, C42400616) | **Will NOT appear in the preview** — it is off the CPL and JLC has no CAD for the part. Confirm instead that the preview shows NOTHING placed at the south-east corner block, and that the 4 poles are bare. Wiring is a human job: §11 pole legend. |

## 7. BRING-UP ORDER — an ordered ritual, in THIS sequence

> ### ⚠️ STEP 0 FOR v1.7 — **FIT THE `J_ESTOP` SHORTING PLUG, AND FIT IT ON 2–3.**
>
> **Do this BEFORE you conclude anything from steps 1–4 below.** With `J_ESTOP`
> open, `ESTOP_RAW_IN` sits at **1.15 mV** (measured derivation: 1 µA × 470 Ω +
> 1 µA × 680 Ω, `R_ESTOPPD` being the sole DC path) against a `V_T−(min)` of
> 0.500 V, so `ESTOP_OK` is LOW, `OS_CLR_N` is asserted, and **no relay will
> ever close no matter how perfectly the rest of the ritual goes.** That is
> correct, deliberate, restrictive-default behaviour — and it looks exactly
> like a dead board.
>
> **Verify the plug with a meter BEFORE inserting it**, because the failure mode
> of getting it wrong is a short across the logic rail, not a non-working
> E-stop: with the plug OUT of the board, there must be continuity between the
> two bridged contacts and **NO continuity from either of them to the third**.
> Then confirm on the board, unpowered: **`J_ESTOP` circuit 1 = `GND`,
> circuit 2 = `3V3`, circuit 3 = `ESTOP_RAW_IN`** (silk and §banner). The bridge
> goes on **2–3**. A 1–2 bridge shorts `3V3` to `GND`.
>
> **After fitting, before powering:** ohm-meter `J_ESTOP` circuit 2 to circuit 1
> (i.e. `3V3` to `GND`) — it must NOT read a short. If it does, the plug is on
> the wrong pair. **Do not power the board until that reads open.**
>
> With the plug correctly fitted, `ESTOP_RAW_IN` is pulled to `3V3` through the
> 680 Ω series element and `ESTOP_OK` goes HIGH — one of the AND-chain terms is
> now permissive, and the ritual below can prove the others.

Pre-power (carried from v1.1, still binding):

1. **J_PWR pin-1 harness check (BRING-UP-CRITICAL):** multimeter the mating
   harness: pin 1 blade must beep to +5 V, pin 2 to RTN, peg orientation
   noted. The keyed housing prevents reverse MATING only — it cannot fix a
   mis-assumed pin-1 side.
2. Continuity: 5V_IN → F1 → 5V_FUSED → Q_REV → 5V_RPP → U_EFUSE →
   5V_PROTECTED.
3. **Isolation spot-check:** with relays UNPOPULATED, megger/DMM between any
   keypad net (J_KEY_MATRIX pin) and GND — must be open (the comb carries no
   galvanic path; only the reed contacts bridge domains).
4. Power at current-limited 5 V / 0.5 A; check 3V3 (U_LDO) and 3V3_ANALOG.
5. Pi host config before any arming (from `01_docs/pin_map.md`, verified
   against RP1 datasheet + kernel overlays):

   ```ini
   # /boot/firmware/config.txt — cooksense v1.2+ pin map
   dtparam=i2c_arm=on                 # I2C1 GPIO2/3  (MCP23017 0x20)
   dtoverlay=i2c2-pi5                 # I2C2 GPIO4/5  (cam A 0x33 + ambient SHT45 0x44)
   dtoverlay=i2c3-pi5,pins_14_15      # I2C3 GPIO14/15 (cam B 0x33 + exhaust SHT45 0x44)
   enable_uart=0                      # GPIO14/15 default to UART0 — console MUST stay off
   dtparam=i2c_arm_baudrate=100000
   ```
   Also remove `console=serial0,...` from cmdline.txt.

**The arming ritual. Four steps, in this exact order — each step proves one
AND-chain input while the later inputs are still held safe by their
pull-downs:**

1. **HEARTBEAT.** Start the host heartbeat toggling WD_PET (GPIO17, phys
   pin 11 → TPS3823 WDI through the 1 k R_WDPETPD).
   *Proves:* host software owns the pet pin and can drive it against the 1 k
   hold-down (≈3.3 mA while high — that current is a safety property, see the
   TPS3823 dossier; do NOT "normalise" R_WDPETPD to 100 k, a 100 k hold lets
   the supervisor pet ITSELF and silently disables the watchdog).
   *Failure means:* wrong GPIO, config, or drive strength — nothing downstream
   can be trusted yet.
2. **TP_WDOK steady > 2.5 s.** Watch TP_WDOK with the heartbeat running: it
   must come up and stay steady for longer than **2.5 s = the TPS3823 maximum
   watchdog timeout** (t_WD 0.9 / 1.6 / 2.5 s min/typ/max, datasheet §6.8).
   Steady beyond the max timeout proves the watchdog is being GENUINELY petted,
   not coasting. Then run the negative test: set the heartbeat GPIO to input —
   **WD must bite (TP_WDOK drop / RESET assert) within 2.5 s.**
   *Failure means:* if TP_WDOK never comes up, the pet edge is not reaching
   WDI; if TP_WDOK stays high with the heartbeat STOPPED, the watchdog is
   self-petting (the R_WDPETPD-value defect) — **STOP, the board's primary
   runaway backstop does not exist.**
3. **REARM_N — ⚠️ A PULSE, AND NOTHING IN HARDWARE ENFORCES THAT.** Pulse
   REARM_N low (MCP23017 U_EXP GPA5, pin 26; R_REARMPU 100 kΩ pull-UP, so a
   floating expander cannot clear the latch) to clear the hardware fault latch,
   **then drive it HIGH again**. See §7a — held low it permanently defeats the
   latch.
   *Proves:* every latch SET input is clear — WD_OK (step 2), ESTOP_OK
   (E-stop loop closed), TEMP_OK (both NTCs connected and cool; note the v1.3
   open-detect means an UNPLUGGED thermistor harness is a latched fault BY
   DESIGN).
   *Failure means:* one SET input is still faulted — read TP_ESTOP, TP_TEMPOK,
   TP_FAULT to find which; do not proceed by jumpering anything.
4. **HOST_AUTH.** Drive HOST_AUTH high (GPIO22, phys pin 15; 100 k pull-down —
   the default is unauthorized). This is the last AND-chain input:
   KEY_RELAY_ALLOWED (TP_ALLOW) must go true and the coil rail becomes
   available.
   *Proves:* the full 7-condition chain end-to-end.
   *Failure means:* with steps 1–3 green the fault is isolated to the AND
   chain itself (the ten §6-item-16 gates) or MCU_RELAY_ENABLE — check
   TP_ALLOW and TP_RKEY.

First-use functional checks (after the ritual, folded from v1.1):

- **J_TC thermocouple polarity:** dip the probe in a known reference (ice
  water / boiling water) — a REVERSED junction reads an inverted delta from
  ambient: obvious and harmless. Swap at the MAX31856 inputs if needed.
- **KEY_RESET_N floats during Pi boot** — R_OE holds the 595 outputs disabled;
  no relay can fire until the Pi drives the interface. Observe on first boot.
- **Door input direction (§2a):** with the door harness unplugged the board
  must read DOOR-OPEN (non-permissive). If it reads closed, the harness or the
  pull is wrong — stop.

## 7a. ⚠️ THREE HOST-FIRMWARE INVARIANTS THE HARDWARE CANNOT ENFORCE (7a-1/7a-2 NEW IN v1.6, 7a-3 NEW IN v1.7)

The first two are single register writes on the MCP23017 expander, both defeat
a hardware safety property, and **neither is detectable at any test point while
the board is healthy.** The third (7a-3) is a POWER constraint on the SHT45
heaters. Write all three into the host software's own safety requirements and
re-check them at every firmware release.

### 7a-1. `REARM_N` MUST BE PULSED. HELD LOW IT PERMANENTLY DEFEATS THE FAULT LATCH.

**The topology** (netlist-verified): a cross-coupled /S-/R NAND latch.
`U_LATCHA` = NAND(`FAULT_SET_N`, `FAULT_LATCH_CLEAR`) → `FAULT` (= Q);
`U_LATCHB` = NAND(`REARM_N`, `FAULT`) → `FAULT_LATCH_CLEAR` (= /Q).
`FAULT_SET_N` = `U_FAULTAND`.Y = `WD_OK` · `ESTOP_OK` · `TEMP_OK`, so /S is
asserted (low) by any of those three faulting.

**`REARM_N` has exactly one driver in the whole board:**
`REARM_N = {R_REARMPU.1, U_EXP.26 (GPA5), U_LATCHB.1}`. No button, no connector
pin, no test point, no jumper. BRIEF.md:85-86 requires "explicit manual re-arm";
in this build that is a register write from the same Pi the hardware chain
exists to bound (brief §12 threat model, T6).

**What happens if it is held low** — driven, not pulsed:

- /R asserted → `FAULT_LATCH_CLEAR` is forced **HIGH permanently**, i.e.
  permissive at `U_AND3.C` (coil rail) and `U_CAND2.B` (external contactor) at
  all times;
- with a fault ALSO present, /S and /R are both low: the NAND latch's
  **forbidden state**, Q = /Q = 1, `FAULT` and `FAULT_LATCH_CLEAR` asserted
  together;
- `U_LATCHA` degenerates to `FAULT` = NOT(`FAULT_SET_N`) — a combinational
  repeater. **The latch loses its memory.**

**What survives:** the LIVE terms. `WD_OK`, `ESTOP_OK` and `TEMP_OK` still gate
the coil rail (`U_AND1`) and the contactor (`U_CAND1`) while the fault is
present. **What is lost is MEMORY** — a fault that clears (a camera cooling by
1 °C, a watchdog restored, an E-stop released) re-permits cooking with **no
re-arm**, which is exactly what ADR-0011 §2 and the v1.2 TEMP_OK-into-SET fix
were for.

**It also removes this design's most elegant property.** At every power-up
`WD_OK` is LOW for the TPS3823 reset delay (t_d = 120/200/300 ms, datasheet
§6.8) → `FAULT_SET_N` low → the latch is FORCED SET → the coil rail cannot come
up after ANY power interruption without an explicit re-arm. The MCP23017 helps
here: `IODIR` POR value is `1111 1111` (DS20001952C register table), so GPA5 is
an INPUT at power-on and `R_REARMPU` holds `REARM_N` high. **A held-low
`REARM_N` therefore does NOT survive a 3V3 power cycle — but it DOES survive
every Pi reboot**, because `EXP_RST_N = {R_EXPRST.1, U_EXP.18}` has **no
driver**: nothing on this board can reset the expander, so its registers hold
until 3V3 drops.

**REQUIRED BRING-UP TEST (negative, do it once per build):** with the machine
otherwise armed, hold `REARM_N` low, induce a fault (open the E-stop, or unplug
one thermistor head), then clear the fault. **`TP_ALLOW` must stay LOW and
`TP_5VKR` must stay at 0 V until `REARM_N` has been returned high and pulsed
again.** On this revision it will NOT — that is the defect being documented;
record the result and treat the software rule as the mitigation.

**What would fix it in hardware** (next electrical revision): an edge-detect /
one-shot on `REARM_N`, so that only a TRANSITION clears the latch. A stated
driver invariant is what v1.6 ships instead.

### 7a-2. `GPPU` MUST STAY `0x00` ON PORT B BITS 1, 2 AND 7 (**BIT 3 IS NOW SPARE**).

`WD_OK`, `ESTOP_OK` and `MODE_AUTO_HW` carry **no pull resistor of
any kind** (§13 gap 8). They are read back by the expander — **RE-MEASURED from
this archive's board on 2026-07-30:**
`U_EXP.8` = GPB7 = `WD_OK_EXP`, `U_EXP.3` = GPB2 = `ESTOP_OK_EXP`,
`U_EXP.2` = GPB1 = `MODE_AUTO_HW_EXP`, and **`U_EXP.4` = GPB3 = `GPB3_SPARE`**.

> **v1.7: GPB3 IS NO LONGER `DOOR_OK`.** The door channel is deleted (ADR-0025)
> and GPB3 now lands on `GPB3_SPARE`. There are **THREE** permissions on port B,
> not four. `grep -c DOOR source/cooksense.net` returns **0** — no door net of
> any kind survives anywhere in the netlist. Leaving `GPPU` at its `0x00` POR
> value is still correct and still mandatory for bits 1, 2 and 7.

MCP23017 DS20001952C §3.5.7, verbatim: *"The GPPU register controls the pull-up
resistors for the port pins. If a bit is set and the corresponding pin is
configured as an input, the corresponding port pin is internally pulled up with
a 100 kΩ resistor."* POR value is `0000 0000` — **the safe default, and it must
be left alone.**

With the driver alive a 100 kΩ pull-up is harmless (a push-pull HC14 or TPS3823
output wins easily), **so setting these bits has no visible effect on a healthy
board.** In the failure case it is decisive: an unfitted, cracked or dead
`U_SCHM` / `U_WD` leaves an indeterminate float today, and a 100 kΩ pull-up to
3V3 converts that into a **deterministic PERMISSIVE** reading of all four
permissions — including "E-stop clear" with the mushroom pressed. There is no
software way to add a pull-DOWN on these pins; the register can only make the
default worse.

**RULE:** the host's expander init must write `GPPUB = 0x00` explicitly (not
merely leave it at POR), and any library that enables pull-ups by default —
several Python MCP23017 wrappers do — must be configured off for port B.

### 7a-3. 🔥 THE TWO SHT45 HEATERS ARE **NEVER** FIRED COINCIDENTALLY AT THE 200 mW LEVEL. STAGGER THEM. (NEW IN v1.7, ADR-0027)

**This one is a POWER constraint, not a safety one, and it is the only load on
this board that the copper-counted dropout budget cannot absorb.**

The SHT45 carries an on-package heater with 200 / 110 / 20 mW levels; at the
200 mW level it draws up to **100 mA**, and the brief commissions the exhaust
pod into a condensing duct — the case Sensirion §4.9 lists the heater FOR. So
firmware WILL want it. Sensirion's own **≤10 % duty limit** (SHT4x D1 §4.9 /
Table 9, `tHeater` long pulse 0.9/1/1.1 s with automatic shutoff) is already
carried in the rail budget. **What that limit does not constrain is whether the
two pods' pulses OVERLAP — and that is this system's choice.**

MEASURED (ADR-0027, exact nodal solve of the routed 5 V chain on this
archive's own board, md5 `9f4fd5fae810f40a52b1035df727243c`, at 75 °C):

| case | whole-board current | LDO input headroom | vs 1300 mV dropout |
|---|---|---|---|
| continuous, declared worst case | 0.4024 A | 1329.1 mV | **+29.1 mV** |
| **both heaters @ 200 mW coincident (≤1.1 s)** | 0.4990 A | 1297.4 mV | **−2.6 mV FAIL** |
| **heaters STAGGERED, one at a time** | 0.4090 A | 1327.0 mV | **+27.0 mV PASS** |

Break-even whole-board current is **0.4910 A**.

**RULE:** the host's sensor driver must SERIALISE heater pulses across the two
SHT45 pods — never both `activate heater` commands outstanding at once at the
200 mW level. A single pod at 200 mW, or both at 20 mW, are both fine.

**Honest framing, so this is not over-read:** −2.6 mV is 0.2 % of a dropout
figure ds1117 specifies at `IOUT = 0.8 A`, applied here to a rail drawing
0.30 A, and the datasheet's own General Description says dropout *decreases at
lower load currents*. The coincident pulse is very probably harmless in
silicon. It is a RULE rather than a footnote because the alternative was to
invent the low-current dropout number this project has refused to invent since
v1.5 — and because the same pulse's junction excursion is **not bounded by any
cited number either** (ds1117 publishes no thermal time constant; the answer is
between +3.0 °C adiabatic and +17.8 °C steady-state, and the upper end would
put `Tj` at 134.9 °C against a 125 °C limit). **Staggering removes both
questions instead of answering them**: staggered, the excursion is +0.2…+1.2 °C
and `Tj` stays at 117.1–118.3 °C.

The G4 bench measurement in §7 retires the uncertainty behind this rule — see
§13's OWED list. Until it is taken, the rule stands.

## 7b. 🛑 **MANDATORY BENCH GATE — SIX MEASUREMENTS, ONE SITTING. THE BOARD IS NOT TRUSTED ABOVE BENCH CONDITIONS UNTIL THIS IS DONE.**

**This is a GATE, not a suggestion** (user decision 2026-07-30, ADR-0029). This
repo has precedent for a mandatory bench obligation in order paperwork —
pod-v2's continuity check, usb-hub's 5 A-hot check, and this board's own §7a-3
heater-stagger rule are all the same shape. Do these at G4 bring-up, in one
sitting, before the board is operated at its declared 65 °C ambient or trusted
in an enclosure.

**WHY IT EXISTS.** Six numbers this board's margins depend on **cannot be
cited** — no datasheet publishes them and no amount of further analysis will
produce them. They have been OWED since v1.5 and they have been re-argued
across five analysis passes. **One hour with a bench supply, an electronic
load, a hotplate/oven and a thermocouple retires four of the six**, and the
first of those four dominates everything else on the rail.

| # | measure | how | what it retires — and why no paper substitute exists |
|---|---|---|---|
| **B1** | `F1` resistance vs temperature | MF-MSMF200/8X, 4-wire, 23 → 85 °C in an oven or on a hotplate, ≥5 points | **`F1` R-vs-T.** `F1` is a **PTC — rising resistance with temperature is the mechanism the part is sold for** — and **Bourns publishes NO resistance-vs-temperature data anywhere in the datasheet.** Every claim above 23 °C currently rests on inverting Bourns' own `Ihold` derating table under a NAMED assumption. |
| **B2** | `J_PWR` Micro-Fit contact resistance **in THIS build** | 4-wire across the mated pair, both legs (supply and return), after ≥5 mating cycles, with THESE crimps and THIS wire gauge | **the contact resistance in this build.** 10 mΩ/contact is a specification MAXIMUM, not a measurement; the aged ≤60 mΩ allowance is INHERITED from a Molex product spec this tree could not fetch. Two contacts are in the loop, so this term is 8.1–24.1 mV against a ~+29 mV margin — **28 % to 83 % of it.** |
| **B3** | 🛑 **AMS1117-3.3 dropout at 0.2 A** | load `3V3` to its real total (~0.2 A), sweep `V_IN` **down** until `V_OUT` leaves regulation; record `V_IN − V_OUT` at **0.2 A and at 0.4 A** | 🛑 **THE ONE THAT DOMINATES.** ds1117 publishes dropout **only at 0.8 A**, has **no dropout-vs-load curve** (six curves on p.6, none of them dropout), and says only that it *"decreases at lower load currents"*. **The entire dropout argument on this board is a 0.8 A number applied to a 0.2 A rail.** If it lands anywhere near the 300–500 mV a 1 A LDO typically shows at a quarter load, the margin goes from **+19.5 mV to ~+800 mV** and every remedial option — tab-vias, a 5 V pour, a switching regulator — **becomes unnecessary.** |
| **B4** | `θ_JA` on THIS mounting | thermocouple on the `U_LDO` tab, rail at its real total load, known still-air ambient; `θ_JA = (T_tab − Ta)/PD` | **`θ_JA` on this mounting.** 90 °C/W is the PACKAGE figure used because the mounting cannot be claimed. An independent thermal network gives 81.6…92.3 °C/W across h = 18…6, i.e. **90 is central-to-slightly-optimistic, not conservative** — the opposite of how a package figure is usually read. |
| **B5** | `ΔT_board` | board copper temperature near `U_LDO`, **all FOUR simultaneously-reachable coils energised** (see the correction below) vs all coils off, same ambient | **the board's own rise.** +1.55…+4.65 °C is a MODEL OUTPUT, not a measurement, and it is **20–59 % of the thermal margin** — the exact term that makes 7.92 °C at 75 °C actually 3.3…6.4 °C. |
| **B6** | SOT-223 thermal time constant | step the load and log tab temperature to steady state | **the thermal time constant.** ds1117 publishes none, so **no transient excursion on this package is bounded by any cited number** — the answer sits between +3.0 °C adiabatic and +17.8 °C steady state, and the upper end puts `Tj` at 134.9 °C against a 125 °C limit. §7a-3's staggering rule exists to remove that question rather than answer it; B6 answers it. |

**⛔ CORRECTION TO B5, FOUND BY A FRESH-CONTEXT LENS AND RE-MEASURED BY ME:
"ALL 12 REED COILS ENERGISED" IS A STATE THIS HARDWARE CANNOT PRODUCE.** The
selector lines come from **two SN74HC238 1-of-8 decoders** (`C5620`, one BOM row
covering `U_DECD` + `U_DECU`), so at most **one U coil + one D coil + PRESS +
STOP = FOUR coils** can be energised simultaneously — the interlock forbids more,
by design. The instruction as first written asked for a measurement nobody can
take, and the release already contained the contradicting fact: its own `R-POUR`
waiver calls the all-12 case "un-reachable … which the interlock forbids". Two
files that were never read together.

**So B5 measures the FOUR-coil case and the 12-coil figure is EXTRAPOLATED, and
the report must say which.** The published +1.55…+4.65 °C board-rise term was
modelled on the board's full 0.958 W; the reachable steady state is ~4/12 of the
coil contribution. **That makes the published band CONSERVATIVE, which is the
right direction** — but it is now conservative for a reason that is written down
instead of accidental. Record the measured 4-coil rise, the coil count, and the
extrapolation you apply; do not silently report a 12-coil number.

**RECORD THE RESULTS AS AN ADR** in `01_docs/decisions/`, with the instrument,
the ambient, and the raw numbers — not conclusions. Then:

* **PASSING B1–B6 IS NECESSARY BUT NOT SUFFICIENT TO REOPEN 75 °C — see the
  correction in §0-T.** B1–B6 can reopen at most the range **65 → 70 °C**.
  Going above 70 °C additionally requires re-rating or replacing the twelve
  `DIP05-1A72-13L` relays (−20…+70 °C, the board's narrowest rating), which is a
  BOM change and therefore a NEW BOARD REVISION, **not** a documentation-only
  supersede. The earlier unqualified "may reopen 75 °C" in this document is
  WITHDRAWN.
* **A RESULT WORSE THAN THE ASSUMPTION IS ALSO AN OUTCOME.** If B1 shows `F1`
  rising steeply, or B2 lands near the aged allowance, the dropout margin at
  the aged corner is +3.4 mV at 65 °C and the answer is the next copper
  revision's 5 V pour (+28.1 mV) or a non-PTC fuse (+16.1 mV), not a narrower
  ambient — see §0-T for why ambient is the wrong knob for this one.
* **UNTIL B1–B6 EXIST, EVERY THERMAL AND DROPOUT NUMBER IN THIS DOCUMENT IS
  COMPUTED, NOT MEASURED**, and §0-T's tables are the honest form of that
  computation rather than a reassurance about it.

---

## 8. ⚠️ RELAY-COUPLING BENCH MEASUREMENT (carried from v1.1 — licenses any future denser repack)

This board places the reeds at the **15.24 mm coupling-vetted pitch in the
rot0 orientation the figure came from, with anti-parallel adjacent coils**
(the datasheet's own alternate-orientation mitigation). To license any FUTURE
revision below 15.24 mm pitch or a two-row repack, measure ON THIS BOARD:
- Energize a **U + D + PRESS triple** (worst-case simultaneous neighbours,
  e.g. K_U6 + K_D1 + K_PRESS via the decoder/one-shot paths).
- For the relay ADJACENT to each energized one, sweep its coil voltage and
  record the **operate (pull-in) voltage shift** vs the datasheet 3.5 V max in
  isolation, both coil polarities.
- A shift < 10% of the 1.5 V worst-case margin (operate stays ≤ 3.65 V) is a
  CLEAN result → record it in 01_docs/decisions/ as the coupling evidence.
  Any larger shift: keep ≥ 15.24 mm forever and note the -12M/Q/R/S
  magnetic-shield variants as the fallback for denser layouts.

## 9. Pi interconnect (J_PI — ribbon SIDECAR, NOT a direct stack)

- Use a 40-way ribbon with a **MALE DIL-IDC transition plug at the board end**
  — standard Pi ribbons are FEMALE-FEMALE and cannot mate this board's socket.
- The socket is UNSHROUDED: mark pin 1 on both ribbon ends and observe strict
  pin-1 keying discipline at every mating.
- The socket's stack tails protrude ~12 mm below the board — trim them or fit
  standoffs of at least that height.

## 10. ⚠️ HARNESS LABELING DISCIPLINE — THE GH-5 FAMILY IS NOW **TWO** HOUSINGS, NOT FIVE, AND THE HAZARD THAT CLOSED IS THE ONE THAT MATTERED

> ### v1.7 — READ THIS BEFORE THE REST OF §10. THE POPULATION CHANGED.
>
> v1.6's §10 was written about **five** cross-mateable `C189896` GH-5 housings
> and correctly identified one of the twenty combinations as NOT fail-safe: an
> SHT45 pod harness in `J_MODE` energising the coil rail. **THREE OF THOSE FIVE
> ARE GONE FROM THE FAMILY IN v1.7**, and the one that mattered is the one that
> left. From `fab/bom.csv` in THIS archive, verbatim:
>
> | LCSC | part | pitch | refs on v1.7 |
> |---|---|---|---|
> | `C189896` | SM05B-GHS-TB | 1.25 mm | **`J_RH_AMBIENT`, `J_RH_EXHAUST` — and nothing else** |
> | `C265111` | SM08B-GHS-TB | 1.25 mm | `J_THERM_A`, `J_THERM_B` |
> | `C2683602` | SM10B-GHS-TB | 1.25 mm | `J_KEY_MATRIX` (unique) |
> | `C485354` | **S4B-ZR-SM4A-TF (JST ZH)** | **1.50 mm** | `J_MODE` — **MECHANICALLY KEYED OUT OF THE GH FAMILY (ADR-0018)** |
> | `C160403` | **SM03B-SRSS-TB (JST SH)** | **1.00 mm** | `J_ESTOP` — **MECHANICALLY KEYED OUT OF THE GH FAMILY (ADR-0025)** |
> | — | — | — | `J_DOOR` — **DELETED FROM THE NETLIST (ADR-0025)** |
>
> **`J_MODE` LEAVING THE GH FAMILY IS WHAT CLOSES v1.6's §10.2 HAZARD.** The
> whole 20-cell matrix below existed because a pod harness could reach
> `J_MODE.4` = `COIL_EN`. At 1.50 mm ZH it cannot: a GH plug's contacts sit at
> 1.25 mm and cannot register in a ZH shroud. **The remaining GH-5 pair is two
> IDENTICAL SHT45 pod housings, so the only cross-plug left inside that family
> swaps ambient with exhaust** — a channel-identity error the host will see as
> two plausible humidity readings on the wrong labels, not an energised coil
> rail. `J_THERM_A` ↔ `J_THERM_B` (both `C265111`) is the same shape of error on
> the thermistor pods.
>
> **THE DISCIPLINE BELOW STILL APPLIES IN FULL.** Two identical unkeyed housings
> is still two, "the host will notice" is not a safety argument, and the
> ambient/exhaust swap silently inverts every thermal decision that compares the
> two. **LABEL BOTH ENDS OF EVERY HARNESS.** Read §10.2–§10.6 as the record of
> the class and of what a cross-plug can do when the pinouts are not keyed —
> it is why `J_MODE` and `J_ESTOP` are now keyed, and it is the reasoning to
> re-apply the moment anyone adds a sixth connector.

### 10.1 The housings, as v1.6 found them (HISTORICAL — see the box above)

**One part, one footprint, one unkeyed housing, five instances:**
`SM05B-GHS-TB` / `JST_GH_SM05B-GHS-TB_1x05-1MP_P1.25mm_Horizontal` / `C189896`
→ `J_DOOR, J_ESTOP, J_MODE, J_RH_AMBIENT, J_RH_EXHAUST`.
**On v1.7 that list is `J_RH_AMBIENT, J_RH_EXHAUST`.**

Nothing mechanical distinguished them. Board positions from `fab/cpl.csv`:
`J_MODE` (196.75, −60.00) and `J_RH_EXHAUST` (186.00, −96.75) are **38.29 mm
apart**, both field-accessible, on adjacent edges.

| connector | pin 1 | pin 2 | pin 3 | pin 4 | pin 5 | harness type | v1.7 |
|---|---|---|---|---|---|---|---|
| `J_DOOR` | 3V3 | DOOR_RAW | GND | DOOR_RAW | GND | PASSIVE — dry Form-A reed | **DELETED** |
| `J_ESTOP` | 3V3 | ESTOP_RAW | GND | GND | GND | PASSIVE — dry E-stop contact | **NOW SH-3: 1=GND, 2=3V3, 3=ESTOP_RAW_IN** |
| `J_MODE` | 3V3 | MODE_RAW | KEY_RELAY_ALLOWED | **COIL_EN** | GND | PASSIVE — DPDT mode switch | **NOW ZH-4: 1=3V3, 2=MODE_RAW, 3=KEY_RELAY_ALLOWED, 4=COIL_EN_IN** |
| `J_RH_AMBIENT` | 3V3_SW_RHA | GND | SDA_A | SCL_A | SHIELD_DRAIN | **POWERED — SHT45 pod** | unchanged |
| `J_RH_EXHAUST` | 3V3_SW_RHE | GND | SDA_B | SCL_B | SHIELD_DRAIN | **POWERED — SHT45 pod** | unchanged |

### 10.2 THE HAZARD — an SHT45 pod harness in `J_MODE` energises the coil rail

An RH pod harness is `1 = VCC, 2 = GND, 3 = SDA, 4 = SCL, 5 = SHIELD`. Plugged
into `J_MODE` its conductors land like this:

| pod wire | lands on | consequence |
|---|---|---|
| 1 VCC | `3V3` | **the pod powers up normally** |
| 2 GND | `MODE_RAW` | pod return through `R_MODEPD` 10 kΩ |
| 3 SDA | `KEY_RELAY_ALLOWED` | pod's SDA pull-up fights a CMOS output — benign |
| 4 **SCL** | **`COIL_EN`** | **the pod's module SCL pull-up drives the coil-rail gate** |
| 5 SHIELD | `GND` | — |

`COIL_EN` has exactly three nodes in the netlist — `J_MODE.4`,
`Q_COILDRV.1` (gate), `R_COILENPD.1` — so its **only** hold is `R_COILENPD =
100 kΩ` to GND. It has **no ESD device and no series resistor**; `J_MODE` is the
only one of the five housings whose field pins carry neither (`J_DOOR` has
`D_DOOR`, `J_ESTOP` has `D_ESTOP`).

The pod's SCL pull-up returns to the pod's **VDD pin**, which wire 1 has just
tied to the real 3V3 rail — so it is a clean pull-up to 3.3 V regardless of
where the pod's ground floated to:

| pod pull-up | V(COIL_EN) = 3.3 · 100/(100 + R) | 2N7002 gate |
|---|---|---|
| **10 kΩ** (`01_docs/DETAIL_DESIGN.md`: "SHT pods carry module 10k pullups") | **3.000 V** | fully on |
| **4.7 kΩ** (BRIEF C7, Adafruit-class module) | **3.152 V** | fully on |

2N7002 `V_GS(th)` is specified 1.0 V min / 2.5 V max at I_D = 250 µA, so at
3.00 V **every** device in the specification window is on, and `Q_COILDRV` has
only to sink the `R_HSG` 100 kΩ current — 10 µA to bring `HS_GATE_COIL` to 4.0 V
(`Q_COIL` `V_GS` = −1.0 V), 45 µA to hold it at 0.5 V (`V_GS` = −4.5 V, the
condition `AO3401A` `R_DS(on)` < 60 mΩ is specified at). `Q_COIL` then connects
`5V_PROTECTED` to **`5V_KEY_RELAY`** — all twelve reed coils plus `K_PRESS` and
both ULN2803 commons — with **all seven AND-chain terms bypassed**
(`MODE_AUTO_HW`, `WD_OK`, `ESTOP_OK`, `TEMP_OK`, `MCU_RELAY_ENABLE`,
`HOST_AUTH`, `FAULT_LATCH_CLEAR`) **and the Manual/Auto physical rail cut
bypassed with them** — the rail cut IS the `J_MODE` pin 3→4 pole, and this
cross-plug drives pin 4 directly.

**The bound, for any external pull-up whatever:** solving
3.3 · 100 kΩ/(100 kΩ + R) ≥ 1.2 V gives **R ≤ 175 kΩ**. Any external pull-up
under 175 kΩ on that pin can energise the coil rail. (The 1.2 V figure assumes a
minimum-threshold 2N7002 conducting in subthreshold — that is the
worst-case-hazard bound and is softer than the 10 kΩ / 4.7 kΩ result above,
which needs no subthreshold assumption at all.) For comparison the three
passive-harness safety inputs `R_DOORPD` / `R_ESTOPPD` / `R_MODEPD` are all
**10 kΩ** — the one pin that directly enables the relay rail is held **ten times
more weakly** than the pins that merely report a switch.

### 10.3 WHY THE OLD CLAIM WAS WRONG — the model, not the arithmetic

The pin-review-Q re-pinning of 2026-07-23 (DISPOSITIONS #6) was correct as far
as it went and is not being reversed: it moved 3V3 away from `COIL_EN` so that
`COIL_EN`'s neighbours are the AND-chain output (pin 3) and GND (pin 5), and it
reasoned that "any cross-plug bridge either applies the intended gating or holds
the rail OFF." **That reasoning models a cross-plug as a passive BRIDGE between
pins.** It is the right model for the three dry-contact harnesses and the wrong
model for a harness that *sources* current onto a pin. The two powered housings
were not in the analysis, so the conclusion was generalised past its evidence.

### 10.4 THE COMPLETE CROSS-PLUG MATRIX — all twenty combinations

Rows = the harness you are holding; columns = the socket you plug it into. Each
cell is analysed on its own — "this one harness is in the wrong socket and
everything else is right."

| mark | meaning |
|---|---|
| **☠ RAIL** | energises the coil rail with the AND chain and the Manual rail-cut bypassed |
| **⚡ SHORT** | a rail short or an unlimited over-current path |
| **✗ FALSE-CLEAR** | a SAFETY INPUT is forced or driven to its PERMISSIVE state |
| **? INDETERMINATE** | a safety input is driven into its threshold band — the reading depends on the individual part, so it is not fail-safe either |
| **○ CANNOT ARM** | an input is falsified but `COIL_EN` is unconnected, so the rail cannot come up: annoying, not dangerous |
| **↔ SILENT SWAP** | works electrically, and transposes two channels with nothing to detect it |

| harness ↓ / socket → | `J_DOOR` | `J_ESTOP` | `J_MODE` | `J_RH_AMBIENT` | `J_RH_EXHAUST` |
|---|---|---|---|---|---|
| **DOOR** — 2-wire dry Form-A reed on positions 1–2 | — | **✗** the reed now drives `ESTOP_RAW`: **door closed ⇒ E-STOP READS CLEAR**. The E-stop's own isolated pole on `J_ISOLOOP` is untouched, so the external contactor loop still breaks; the SELV permission does not | **○** reed drives `MODE_RAW` ⇒ reads AUTO with no mode switch fitted; `COIL_EN` unconnected ⇒ `R_COILENPD` holds the rail **OFF** | **⚡** reed shorts `3V3_SW_RHA` to GND — no current limit ahead of `Q_SWRHA` (only while `RAIL_EN_RHA` is asserted) | **⚡** same on `3V3_SW_RHE` |
| **ESTOP** — 2-wire dry NC contact on positions 1–2 | **✗** contact drives `DOOR_RAW`: **E-stop not pressed ⇒ DOOR READS CLOSED**. `DOOR_OK` gates `OS_CLR_N` (the press one-shot) only, not the rail | — | **○** as the DOOR row: AUTO reported, rail OFF | **⚡** as above | **⚡** as above |
| **MODE** — 4-wire DPDT, poles on 1–2 and 3–4, both closed in AUTO | **⚡** pole 1–2 ties 3V3→`DOOR_RAW` and pole 3–4 ties GND(pin 3)→`DOOR_RAW`(pin 4): **in AUTO 3V3 is shorted to GND through two switch contacts in series.** In MANUAL both open ⇒ door reads OPEN, safe | **✗** pole 1–2 ties 3V3→`ESTOP_RAW` ⇒ **in AUTO the E-stop reads CLEAR permanently**; pole 3–4 lands GND on GND (pins 3/4 are both GND). In MANUAL: safe | — | **⚡** pole 1–2 shorts `3V3_SW_RHA` to GND; pole 3–4 shorts `SDA_A` to `SCL_A` | **⚡** same on bus B |
| **RH POD** — 5-wire POWERED SHT45 module | **?** pod GND **and** pod SCL both land on `DOOR_RAW`. The module's SCL pull-up alone puts `DOOR_RAW` at **3.3·10/(10+10) = 1.65 V** — half the rail — and the pod's own return current through `R_DOORPD` adds to it. `U_SCHM` is an SN74HC14 and 1.65 V is **inside its V_T+ spread at 3.3 V**, so whether the door reads CLOSED depends on the individual part. Not fail-safe | **?** pod GND lands on `ESTOP_RAW` (SCL and SDA land on real GND). The pod's supply return flows through `R_ESTOPPD` 10 kΩ, lifting `ESTOP_RAW` by I·10 kΩ until the module browns out — an unbounded, part-dependent voltage on the E-stop input. Not fail-safe | **☠ THE HAZARD — §10.2. COIL RAIL ENERGISED, ALL SEVEN AND-CHAIN TERMS AND THE MANUAL RAIL-CUT BYPASSED** | — | **↔** if the two pod harnesses are swapped with each other both buses work: the ambient and exhaust humidity channels are TRANSPOSED IN SOFTWARE and nothing on the board or in the protocol detects it (both SHT45s are address 0x44 on their own bus) |

**How the twenty are counted.** Five harnesses (DOOR, ESTOP, MODE, POD-ambient,
POD-exhaust) into five sockets = 25 matings, of which 5 are correct, leaving
**20 cross-plugs**. The two pod harnesses are identical, so the table renders
them as one row of four cells that stands for eight cross-plugs. Class totals
over all twenty:

| class | count | which |
|---|---|---|
| **☠ RAIL** | **2** | either pod harness into `J_MODE` |
| **⚡ SHORT** | **7** | any dry-contact harness into either pod socket (6) + MODE into `J_DOOR` (1) |
| **✗ FALSE-CLEAR** | **3** | DOOR→`J_ESTOP`, ESTOP→`J_DOOR`, MODE→`J_ESTOP` |
| **? INDETERMINATE** | **4** | either pod into `J_DOOR` or `J_ESTOP` |
| **○ CANNOT ARM** | **2** | DOOR or ESTOP into `J_MODE` |
| **↔ SILENT SWAP** | **2** | the two pod harnesses exchanged |

**Not one of the twenty is fail-safe in the sense the old §10 claimed for all of
them.** How each class announces itself, which is what decides how much the
labeling discipline has to carry:

- the **7 ⚡** cells announce themselves loudly — a dead sensor rail, a supply
  that current-limits or shuts down, a jammed I²C bus;
- the **2 ○** cells announce themselves by the machine refusing to arm;
- the **2 ☠** cells announce themselves by the machine arming when it must not,
  which is the wrong way round, and they are why §10.5 item 1 is not optional;
- the **3 ✗** and **4 ?** cells are **SILENT**. Nothing on the board detects
  them. Their only defences are the harness labels and the §7 bring-up steps
  that exercise the E-stop and the door directly (press the mushroom and watch
  `TP_ESTOP`; open the door and watch the press interlock) — do both, per
  harness, after any harness work;
- the **2 ↔** cells are silent too, and are a data-integrity failure rather than
  a safety one: the two humidity channels are transposed and both read
  plausibly.

### 10.5 THE MANDATORY DISCIPLINE

1. **LABEL EVERY HARNESS AT BOTH ENDS AND MATCH LABELS BEFORE POWER.** This is
   the only defence the board has for the ☠ cell. It is not optional and it is
   not a quality nicety.
2. **PHYSICALLY DISTINGUISH `J_MODE`.** Before commissioning, give the `J_MODE`
   harness a permanent mechanical difference the other four cannot have — a
   different jacket colour AND a cable tie / heatshrink collar at the housing —
   so that a `J_MODE` plug is identifiable by touch in a hot, wet cabinet.
3. **DRESS THE TWO POD HARNESSES AWAY FROM THE EAST EDGE.** `J_MODE`,
   `J_DOOR` and `J_ESTOP` are the east-edge column; the pods and thermistor
   heads are on the south edge. Route them so a pod plug cannot physically reach
   the east column.
4. **TP_ALLOW / TP_5VKR ARE THE CHECK.** After any harness work, with the mode
   switch in MANUAL, `TP_5VKR` must read **0 V**. If it does not, a harness is
   in the wrong socket — do not proceed.
5. The v1.3 improvement still stands and still matters: `J_ESTOP` is **SELV-only**
   (pins 3/4/5 are GND, the isolated contactor loop moved to `J_ISOLOOP`, §11),
   so no cross-plug can close the contactor loop through GND any more.
6. The **§2a door-short residual** (a conductor-to-conductor short between
   harness wires 1 and 2 reads DOOR-CLOSED) is unchanged and is a
   harness-quality failure.

### 10.6 WHAT WOULD ACTUALLY FIX IT — for the next ELECTRICAL revision

Copper changes, deliberately NOT made in this documentation-only release:

- `R_COILENPD` 100 kΩ → **10 kΩ** raises the bound from R ≤ 175 kΩ to
  R ≤ 17 kΩ. That is a real improvement but it does **not** clear a 10 kΩ pod
  pull-up (3.3 · 10/20 = 1.65 V, still above threshold) and only just clears
  4.7 kΩ. **It is not sufficient on its own.**
- A series element into `J_MODE.4`, or a **different housing / keyed housing**
  for `J_MODE`, or moving `COIL_EN` off a field connector entirely. Any of the
  three closes the class rather than trimming it. This is the recommendation.
- An ESD device on `MODE_RAW` and `COIL_EN`, which `J_DOOR` and `J_ESTOP`
  already have and `J_MODE` does not.

## 11. ⚠️ THE ISOLATED LOOP — ONE CONNECTOR, `J_ISOLOOP`, AND ITS POLE LEGEND

**Any v1.0/v1.1 statement that "J_ESTOP pins 3/4 carry the contactor loop" is
WRONG, and so is any earlier v1.3 text naming `J_ESTOPLOOP` or `J_CONTACTOR` —
neither connector exists.** J_ESTOP pins 3/4 are GND and that housing is
SELV-only. The opto-isolated loop left the SELV connector because ESTOP_RAW and
CONTACTOR_C sat 0.650 mm apart on 1.25 mm pitch in ONE field harness, making a
single damaged harness a common-cause failure across the isolation boundary.

The whole isolated domain now lands on **ONE** 4-pole 3.5 mm screw terminal,
`J_ISOLOOP` (KF350-3.5-4P, south-east corner, mouth EAST). Merging the two
2-pole blocks is isolation-neutral-or-better: both only ever carried
isolated-domain nets, so this is one isolated body with one 2.0 mm moat and one
pour keepout to defend instead of two adjacent bodies each needing their own.

### THE POLE LEGEND — THIS IS THE GATE

`J_ISOLOOP` is hand-soldered and OFF the CPL, so there is no machine rotation to
get wrong. **The entire risk is a person landing four wires.** Pole 1 is the
SOUTH-most pole (the square pad); wiring runs SOUTH to NORTH.

| pole | board net | function | board Y |
|---|---|---|---|
| **1** | CONTACTOR_C | opto collector out -> E-stop pole B **in** | 100.250 |
| **2** | CONTACTOR_LOOP | E-stop pole B **out** (return) | 96.750 |
| **3** | CONTACTOR_LOOP | -> contactor circuit | 93.250 |
| **4** | CONTACTOR_E | contactor circuit return -> opto emitter | 89.750 |

External loop, in order: `1 -> E-stop dry pole B -> 2`, then `3 -> contactor
permission circuit -> 4`.

**Poles 2 and 3 are ONE board net on TWO screws, deliberately.** On a safety
interlock a single loosening screw must not be able to drop both the E-stop
return and the contactor feed. Do not "tidy" this by landing both wires in one
screw — that reintroduces the single point of failure the two screws exist to
remove. Asserted in `electrical_invariants.yaml` (`J_ISOLOOP.3 -> CONTACTOR_LOOP`).

Silk reads `J_ISOLOOP (SE CORNER) = ISOLATED 30V CONTACTOR LOOP -- NOT SELV` in
the north caption band. It is deliberately NOT beside the block: a scan for a
free silkscreen box against pads, existing silk and every courtyard found no
site within 41.9 mm, and the caption in fact ended up **155.3 mm** from the
block — at (62.000, 15.400) against J_ISOLOOP at (195.300, 95.000), diagonally
opposite. **Within 25 mm of the block the ONLY J_ISOLOOP silk is its outline box
and the refdes at (189.300, 101.000). Use this legend, not the board, to
identify the poles** — the one physical cue at the block is that **pole 1 is the
only RECTANGULAR pad**; poles 2, 3 and 4 are round.

> **⚠️ THE LOOP IS POLARISED. POLE 1 IS POSITIVE. It is NOT a dry contact.**
> `CONTACTOR_C = [J_ISOLOOP.1, U_OPTO.4]` is the phototransistor **COLLECTOR**;
> `CONTACTOR_E = [J_ISOLOOP.4, U_OPTO.3]` is its **EMITTER**. Earlier revisions
> of this section called the output a "DRY CONTACT" — language that means
> polarity-free, and it is wrong. **Current must flow IN at pole 1 and OUT at
> pole 4.** Wired backwards the loop simply never conducts (contactor never
> closes — discovered after the harness is built), and a reversed **30 V** sits
> across an emitter-collector junction rated about **6 V**, an order of
> magnitude over. A phototransistor that fails from reverse breakdown fails
> **SHORT**, and short is the **PERMISSIVE** state. Forward, the part is safe by
> a wide margin: even at the CTR 600 % bin ceiling I_C self-limits to
> 600 % x 6.364 mA = **38.2 mA**, under the 50 mA absolute maximum.
>
> **⚠️ POLES 2 AND 3 ARE THE SAME NET — AND THAT MEANS A SPECIFIC WIRING
> MISTAKE IS SILENT.** `CONTACTOR_LOOP = [J_ISOLOOP.2, J_ISOLOOP.3]`: two screws
> on one node, deliberately, so the loop passes through the field device in
> series (2 → device → 3). **If you land BOTH wires of that device on poles 2
> and 3 in the wrong sense — or bridge 2 to 3 — you SHORT the device out of the
> loop and the loop still reads CLOSED.** For the E-stop that is a **permissive**
> failure: the interlock reports healthy with the E-stop electrically absent.
> Nothing on the board can detect it. Verify continuity through the device
> between poles 2 and 3 with the device OPEN before energising: an open device
> must read OPEN across 2-3.

**Rating — CORRECTED, and the old number was the dangerous half of the pair.**
The loop is the LTV-817S opto DRY CONTACT. Earlier revisions of this section
printed only "**<= 30 V / <= 50 mA**". That is the **ABSOLUTE MAXIMUM** — a
do-not-exceed limit — and quoting it alone invites an integrator to design a
loop that draws tens of milliamps. **The current this loop can actually SINK is
15x smaller and is set by the LED drive, not by the collector rating:**

| quantity | value | where it comes from |
|---|---|---|
| LED drive rail | 3.3 V | `CONTACTOR_DRV`, `U_CAND2.4`, 3V3 CMOS |
| series resistor | **330 Ω** | `R_OPTOLED`, LCSC **C23138**, measured off the shipped board and BOM |
| LED forward drop | ~1.2 V | LTV-817S V_F at a few mA |
| **I_F** | **(3.3 − 1.2)/330 = 6.36 mA** | |
| CTR, **worst-case bin minimum** | **50 %** | `02_parts/LTV-817S-TA1/part.yaml` `limits.ctr: "50-600% (TA1 bin)"` |
| **I_C GUARANTEED** | **6.36 × 0.50 = 3.18 mA** | |

**DESIGN THE FIELD LOOP TO NEED <= 3.0 mA, not 50 mA.** A loop built to the
50 mA figure — a relay coil, a long line with a low-value pull-up, an input with
a milliamp-class threshold — will read as *permanently open* on a worst-case-CTR
device, and the contactor will simply never close. The failure is in the safe
direction, but it presents at commissioning after the harness is built.

**V_CEO is 35 V against a 30 V working loop — 17 % margin, and there is no
clamp.** `CONTACTOR_C`/`CONTACTOR_E` carry no snubber or TVS on this board.
**The field loop MUST be non-inductive, or you must snub it at the load.** An
unclamped inductive kick past 35 V fails a phototransistor SHORT, and a shorted
opto output is the **PERMISSIVE** state — it asserts the interlock the board
exists to withhold. This is the one failure mode in the isolated domain that is
not fail-safe; the board cannot defend against it, so the harness must.

Do not repurpose this loop to switch a contactor coil directly. The
nets carry the ISO_CONTACTOR netclass and the `opto_isolation_2mm` DRU rule
(IEC 60664-1 basic insulation, 30 V working, pollution degree 3, material group
IIIa), which is **GREEN on v1.3 routed copper**. Minimum over ALL copper on ALL
layers (pads, tracks and filled pours) is **2.0000 mm** — **method: true-polygon
copper clearance, all four layers, filled pours included** — at CONTACTOR_C on
`J_ISOLOOP.1` against the **GND zone edge**, and it is 2.0000 mm on each of
F.Cu / In1.Cu / In2.Cu / B.Cu independently — margin 0.000 mm by
construction, because the pour keepout IS the 2.0 mm offset. Pad-to-pad only,
the minimum is 2.1661 mm (`U_OPTO.3` <-> `J_RH_EXHAUST.5`, true polygon
distance). v1.2 measured 0.199 mm at this rule.

## 12. ⚠️ R_OPENT IS 62 kOhm — ORDER C37825, NOT C25915

The open-thermistor detect threshold divider is `3V3_ANALOG -> R_OPENT ->
TCAM_OPEN -> R_OPENB (100 kOhm) -> GND`. Its job is that an open, broken or
unplugged thermistor reads **OVER-TEMP**, not "fine".

**v1.3 was first coded with the wrong part and it was caught before release.**
The row carried **C25915, which is 6.2 kOhm** — one decade low. Verified twice,
from the catalog rather than by decoding a part number: JLC
`selectSmtComponentList` returns MPN `0402WGF6201TCE`, describe "6.2kOhm"; the
LCSC product page for C25915 says the same.

| | R_OPENT | TCAM_OPEN threshold |
|---|---|---|
| design intent | 62 kOhm | **2.0370 V** |
| C25915 as first coded | 6.2 kOhm | **3.1073 V** |

At 6.2 kOhm an open head reads 2.2687 V — *below* the 3.1073 V threshold — so
the comparator never trips. 3.1073 V is also above the LMV393's 2.500 V
common-mode ceiling, so the input sits outside its guaranteed range. The tsx
comment block above these resistors already documented 3.107 V as the REJECTED
first cut, so the wrong code silently reinstated the exact defect the v1.3
second pass exists to remove.

**Root cause, and it is the transferable one.** R_OPENT carried no pinned LCSC,
so the part was coded by an automatic picker, and **all three** of its candidates
for "62k" are 6.2 kOhm (`C25915` 0402WGF6201TCE, `C137946` RC0402FR-07**6K2**L,
`C2909371` FRC0402F**6201**TS) — it reads "62k" as RKM "6k2". The same picker
returned three candidates for "510k" that were all 390 kOhm on R_OS, and put
`R_WDPETPD` on a 100 kOhm line where the design needs 1 kOhm. **That is three
times on this board alone.** The other three resistors in this divider were correct only because of
the order the candidate list happened to come back in, **which is not the same
as being right** — so all four are now pinned explicitly and catalog-verified:

| ref | value | LCSC |
|---|---|---|
| R_OPENT | 62 kOhm | **C37825** |
| R_OPENB | 100 kOhm | C25741 |
| R_CLMPA, R_CLMPB | 22 kOhm | C25768 |

**Order-day checks — BOTH of them, on the BOM you upload:**

| ref | must read | if it reads | consequence |
|---|---|---|---|
| `R_OPENT` | **C37825** (62 kΩ) | C25915 (6.2 kΩ) | open-thermistor detect does not exist |
| `R_WDPETPD` | **C11702** (1 kΩ) | C25741 (100 kΩ) | **watchdog silently disabled** |

Either one reading wrong: **STOP.** Both are wrong-decade substitutions from the
same automatic picker, and neither is visible in the board, the netlist, the CPL
or any geometry check.

**Generalise it:** a coded passive with no pinned LCSC is resolved by a picker
that has now twice returned a wrong decade. Any value-authored passive whose
value matters — a threshold, a timing constant, a current limit — should carry
its code explicitly and be listed in `lcsc_passives_ledger.yaml` so
`bom_source_check` leg C can verify it offline forever.

## 13. VERIFICATION STATUS AND DECLARED GAPS

Everything below is a measured number, including the gaps. A gap that has been
counted is a finding; a gap nobody counted is how things drift.

> **THE TABLE IMMEDIATELY BELOW IS THE v1.6 SNAPSHOT AND IS SUPERSEDED.** The
> v1.7 numbers, RE-MEASURED AT SEAL TIME on 2026-07-30 against THIS archive with
> every exit code captured raw and unpiped, are in
> **`verification/build_gates.md`**. Headline: DRC **0 violations / 0 unconnected
> / 0 parity, exit 0** — and **the same command returns 0/0/0 on `source/`
> copied OUTSIDE the repository**, so the archive stands alone; `policy_audit`
> **FAIL=0, PASS=28, WAIVED=6, HUMAN=6, N-A=5**; ERC **exit 0, 411 violations
> ALL severity `warning`, 0 errors**; E-INV **167/167**; E-ADR **11/11**;
> S-COUNT **4/4 over 239 refdes**; A-ROT **64 measured authority rows**,
> **206/206** CPL rotations sourced; A-POS **206/206** on the pad-array-centre
> datum, worst **0.00050 mm** (`J_ESTOP`) against a 0.05 mm tolerance;
> F-LEGIBLE **60 checks, 0 findings**; `jlc_twin` **exit 0, 207 OK / 465 finding
> rows, bodies mounted 206/206 AGAINST THE CPL** (206 is the CPL denominator —
> `--cpl` scopes it, and a coverage number quoted without its population is the
> defect canon M-COVER exists for); M-BOM **PASS**;
> **A-RENDER `twin_overlay` exit 0** at 15.3907 px/mm, 52 measured / 208, zero
> resolvable-but-unmeasured.
>
> **TWO gates exited non-zero, and neither is a copper defect.**
> **(1) A-STOCK** — one line, `C265111`, §5-0: the SOURCING claim, not the
> design claim. **(2) E-NETREF** — 21 ghost net references, **all of them kind
> K7 `02_parts/*/part.yaml layout.keep_short[].net`**, i.e. adjacency BUDGETS
> that grade nothing. Every other reference kind is 0 ghost, including all 140
> invariant nets and all 40 netclass memberships, so **no ghost reaches copper,
> silk, the netlist or the BOM**; the same 21 are already inside `policy_audit`'s
> evidenced `P-ADJ-UNREACHED` waiver (23/38 budgets — a superset, because an
> absent net has 0 pads). Pre-existing `02_parts/` debt, first counted here.
>
> **A-RENDER's low-resolution FAIL is recorded rather than deleted.** At
> `jlc_twin`'s own 5.1356 px/mm render the gate FAILs on `U_LDO` and
> `Q_SWDRVRHA`; at 9.7448 px/mm it FAILs on a DIFFERENT ref (`J_KEY_MATRIX`);
> at 15.3907 px/mm it passes clean. The board never moved — only the picture
> did, which is the whole finding. Both reports ship
> (`twin_overlay.md`, `twin_overlay_lowres.md`).

| gate | result (v1.6 snapshot — superseded, see above) |
|---|---|
| DRC (`--severity-all --refill-zones --schematic-parity`) | **0 / 0 / 0** — see the qualifier immediately below; **9 checks are set to `ignore`** |
| P-COLLIDE (placement) | 0 pad shorts, 0 anchored courtyard overlaps |
| E-INV | **85 / 85** (v1.7: **167/167**) |
| A-ROT | 189 / 189 CPL rotations from measured rows (v1.7: **206 / 206**) |
| A-POS | 189 / 189 CPL rows on the pad-centre datum, worst 0.0000 mm (v1.7: **206 / 206**, worst 0.00050 mm at `J_ESTOP`) |
| A-POL | **10 codes / 13 refs GENERATED; TRUE population 12 codes / 16 refs** -> §6 human gate item 15. The three extra refs (D_KSTOP, D_REVCLAMP on C8678; D_TVS on C113974) are `POLARITY-FIT-BLIND` in `twin_report.csv` — the twin could not fit them at all, so they never reached the generated list |
| I-HW (mounting-hardware creepage) | **PASS. H4 tightest at 6.5984 mm CREEPAGE** (surface path around the outline notch; its straight-line CLEARANCE is 4.0286 mm, against a sub-1 mm clearance requirement at 30 V / PD3). H1 13.6299 / H2 13.000 cross no void so their creepage and clearance coincide; **H3's line DOES cross an internal slot** (v1.6 quoted x[13.000,22.600] y[49.300,49.900]; **on v1.7 that same slot is x[13.000,22.600] y[49.100,50.100]** — the width went 0.600 → 1.000 mm, so the crossing is WIDER and the detour LONGER), so its true creepage EXCEEDS the 40.9324 straight line — conservative, and irrelevant at 40.9 mm |
| ISO barrier (`opto_isolation_2mm`) | **2.0000 mm**, all copper all layers incl. filled pours (GND zone edge at J_ISOLOOP.1). Pad-to-pad true polygon: 2.1661 mm. Margin 0.000 by construction — the moat keepout IS the 2.0 mm offset. |
| M-REPRO | 3 from-source rebuilds, **1047** vias each, identical fp/track/via hashes, matching the shipped board |
| Stranded pour islands | **121 islands** on the fill THAT SHIPS (GND F.Cu 106, GND B.Cu 13, GND In1.Cu 1, 3V3 In2.Cu 1), **121 bonded, 0 stranded**. The 136 printed in earlier revisions came from a refill-in-memory, not from the stored fill — same conclusion, wrong population. |
| jlc_twin | 420 rows: 184 OK, 184 MODEL-REG-OK, 31 PAD-GEOM, 9 POLARITY-CHECK, **6 POLARITY-FIT-OK, 3 POLARITY-FIT-BLIND**, 1 MIRRORED, 1 FETCH-FAILED, 1 NO-BODY — **all adjudicated**. Earlier revisions collapsed the two POLARITY-FIT classes into one "9 POLARITY-FIT", which hid the **3 BLIND** rows (C8678/D_KSTOP, C8678/D_REVCLAMP, C113974/D_TVS) — the ones with no numbering-free channel at all. They are §6 item 15. |
| contracts_audit | 243 files, 0 violations (the repo grew; the count is the fleet's, not this board's) |

### ⚠️ THE DRC CLAIM HAS A QUALIFIER — nine checks are OFF

`0/0/0 at --severity-all` is true and **incomplete**. `source/cooksense.kicad_pro`
sets these nine to `ignore`, so `--severity-all` never reports them:

```
silk_overlap        silk_over_copper     silk_edge_clearance    text_thickness
missing_courtyard   footprint_filters_mismatch   footprint_type_mismatch
track_not_centered_on_via   tuning_profile_track_geometries
```

**MEASURED with the four SILK checks turned back on** (extract `source/` to a
bare directory, set them to `warning`, re-run): **78 violations** —
`silk_over_copper` 49, `text_thickness` 24, `silk_edge_clearance` 3,
`silk_overlap` 2. They are off as documented fleet policy (silk is resolved at
fab silk-finalisation), and they remain off for v1.3.

**Why you should care anyway:** this board's ADR-0012 safety warnings are on
silk, and §6's human gate asks you to compare the JLC render against our silk.
**Silk legibility is therefore UNGATED on a board that depends on it twice.**
Judge the silk visually from `pdf/assembly.pdf` and
`verification/render_top_bare.png` before ordering, and treat the §6 gate as the
place where silk quality actually gets checked.

### Declared gaps — known, bounded, and NOT fixed in v1.3

> **THREE GAPS ADDED AT THE v1.7 SEAL (2026-07-30), NUMBERED 0a/0b/0c so the
> historical numbering below stays stable.**
>
> **0a. THE MECHANICAL TAB PADS DISAGREE WITH THE GENUINE PART'S OWN
> RECOMMENDED LAND, ON THE EXACT AXIS §5-0 DECLARES UNVERIFIED — AND THEY MATCH
> THE CLONE.** MEASURED from JLC's `packageDetail` PAD records and this board's
> copper (pcbnew), independently of `jlc_twin`:
>
> | | board copper | `C265111` (genuine) | `C42376901` (clone) |
> |---|---|---|---|
> | signal pad | 0.600 × 1.700 | **0.600 × 1.700 (exact)** | 0.700 × 1.800 |
> | **mechanical tab** | **1.000 × 2.700** | **1.210 × 2.700** | **1.000 × 2.500** |
>
> The board's retention tab is **0.210 mm / 17.4 % narrower** than JLC
> recommends for the genuine part, and its width matches the CLONE exactly. So
> **"the board IS the genuine part's land" is true on the eight SIGNAL pads
> only** — and the tab is precisely the feature that governs solder-fillet
> retention, which is the axis §5-0 says nobody has verified. It is a
> KiCad-library-vs-JLC-library difference that pre-dates the substitution
> question entirely, it is UNRESOLVED, and it is stated because **a waiver that
> hides a term on its own declared-unverified axis is not a waiver.**
>
> Recorded with it: **the inherited "0.01 mm measured drop-in" for the clone was
> NOT EVIDENCE.** Its whole triple (`fit=0.01 / NON-MIRRORED / jlc_offset 0`) is
> verbatim the GENUINE part's own rows in `twin_run.log`, no `jlc_twin` artifact
> for `C42376901` exists anywhere in `06_build/`, and `fit=` prints `0.01` for
> the genuine part too — so the number **cannot discriminate the two parts** and
> never could. Re-derived by a method that is not `jlc_twin` (raw EasyEDA `PAD~`
> records + pcbnew, translation-only rigid fit): genuine **0.0002 mm**, clone
> **0.0100 mm** on the signal pads and **0.0399 mm** on the tabs — a 4× worse
> residual on exactly the feature above.
>
> **0b. E-NETREF: 21 ghost net references in `02_parts/`.** All kind K7
> (`layout.keep_short[].net`). No ghost reaches copper, silk, the netlist or the
> BOM — the exposure is that a P-ADJ adjacency budget grades nothing, which
> `policy_audit`'s `P-ADJ-UNREACHED` waiver already declares. Pre-existing
> dossier debt, first COUNTED at this seal. Fix is 21 dossier edits; not made
> here, because they are part-selection inputs to a board whose fab set is
> already frozen and graded.
>
> **0c. A-RENDER's verdict is a function of its INPUT's resolution.** Same
> board, three renders, three verdicts: FAIL on `U_LDO`+`Q_SWDRVRHA` at
> 5.1356 px/mm, FAIL on `J_KEY_MATRIX` at 9.7448 px/mm, PASS at 15.3907 px/mm.
> The shipped verdict is the high-resolution one and the low-resolution report
> ships beside it. A gate whose answer moves with its input's pixel count is
> reported upstream, not silently re-run until it agrees.

1. **P-FACT coverage is 4 of 41 part.yaml.** Only four dossiers declare an
   executable `asserts:` block (the twelve reeds, J_TC, CE1, U_OPTO). The other
   37 carry their facts as prose that no gate reads. Backfilling all 41 is a
   fleet campaign, not a board task; the four chosen are the ones where an
   assert would have caught a defect that actually shipped.
2. **`keepout_region` is declared but ungradeable.** U_OPTO's 5000 Vrms barrier
   is asserted in its part.yaml, and P-FACT reports it DEFERRED because the
   checker cannot yet read board geometry. The barrier is held by three other
   mechanisms (`opto_barrier` 4-layer keepout, the `opto_isolation_2mm` DRU
   rule — **and the metric belongs beside the number**: all-copper-all-layers
   minimum **2.0000 mm** (the binding figure), pad-to-pad true polygon 2.1661 mm,
   pad-to-pad bounding-box 2.126 mm. Earlier revisions quoted only the 2.126
   bounding-box figure here, the loosest of the three, inside a safety
   justification — and the land's own 7.530 mm clear strip).
3. **P-FACT has no kind for "off the CPL but on the BOM as a buy-line."**
   Three of the 16 self-supplied refs (J_ISOLOOP, J_LOADCELL, J_PI) are
   deliberately coded on the BOM and excluded from the CPL. The nearest assert,
   `not_on_assembly_bom`, conflates "not placed" with "not purchased".
4. **Our SOD-323 land draws a cathode band on a bidirectional part** (D_DOOR,
   D_ESD_IN, D_ESTOP, D_LCCLK, D_LCDAT). Assembly risk is nil — JLC places from
   the CPL, not our silk — but a reviewer hand-checking the board may "correct"
   a placement that was already right. v1.4.
5. **CLOSED, not deferred — the CH0/CH3 transfer function is now derived in
   §2b.** The 22 k clamps put CH0 and CH3 on a different divider from the other
   six channels. This was a declared gap until 2026-07-26; it is now arithmetic
   in §2b with the corrected inversion, an 8-point error table and recomputed
   accept/reject thresholds. Recorded here because the reason it could not stay
   a gap is general: §2b is a **MANDATORY acceptance test**, and a mandatory
   procedure specified against a knowingly wrong curve is worse than no
   procedure — whoever runs it fails a good board or passes a bad one and trusts
   the result either way. The sharp case: an open NTC reads 8.4 °C under the
   naive model, so acceptance test (a) would have passed a board on which the
   host detects nothing.
6. **The open-detect comparator has no hysteresis (`R_HYS` is negative feedback
   on U_COMP2).** `TH_CAM_A` is one node feeding U_COMP's IN+ and U_COMP2's IN−,
   so a single 1 M resistor cannot be positive feedback for both. A real open
   still latches solidly (the node moves 15.5 mV against 232 mV of overdrive);
   the exposure is chatter at the −10.4 °C nuisance boundary, and the direction
   is **lockout, not permissive**. Fixing it needs a new part that re-specs the
   threshold to ~2.0836 V. v1.4.
7. **The thermistor sense nets are ~12× their declared length budget.**
   `TH_CAM_A` routes **93.62 mm** and `TH_CAM_B` **87.75 mm** against a declared
   `keep_short max_span_mm: 8` in the LMV393 dossier; closest same-layer
   aggressor is `SPI_SCLK` at **0.206 mm**. Direction is fail-safe (a glitch
   drives TEMP_OK low → latched lockout). Needs re-placement; v1.4. Note the
   budget was never enforced — `audit_board`'s I-PROX has no span check.
8. **The digital twin does not cover 2 of the 54 coded BOM lines.** MEASURED,
   by comparing `fab/bom_jlc.csv` against `verification/twin_report.csv`:
   52 of 54 coded lines were twin-checked; the two that were not are
   **C25768** (`R_CLMPA`, `R_CLMPB` — the 22 kΩ sense bleed) and **C37825**
   (`R_OPENT` — the 62 kΩ open-detect threshold). Both entered the BOM after the
   twin run: C37825 in the R_OPENT decade fix, C25768 when the divider was
   pinned. Their JLC land pattern and 3D body were never compared against ours.
   (Lens A estimated six affected parts by REFDES; by CODE the true figure is
   two, because R_OPENB, C_COMP2 and R_DOORPD share already-checked codes. The
   measured number is the one that belongs here.)
   Not a blocker: both are 0402 chip passives on the `R_0402_1005Metric` land
   class the twin checked 30+ times on this board, both resolve from measured
   A-ROT rows, and both catalog values match their tsx value props under the
   circuit-only check. But it IS a gap, and the twin's whole value is that it
   does not assume — so it is declared rather than rounded away.
9. **The narrative pin and render reviews were NOT re-run for v1.3.** Their
   MACHINE halves are current and ship: 74 pin_audit dossiers regenerated from
   this board, `audit_board` I-POL 18/18, P-FACT `pad1_net_polarity` executing on
   CE1, schematic-parity 0, E-INV 83/83, and renders regenerated from this
   board. Their NARRATIVE halves — a human-equivalent reading of every pin map
   and of the silk — were last run at v1.0/v1.2 and are **not** reproduced;
   `pin_review.md` and `render_review.md` each say so in their first paragraph.
   **What covers the gap instead:** this board has had **four independent
   reviews since**, two adversarial red-team lenses (topology and layout) and
   two zero-context cold lenses over the frozen archive, whose findings are in
   `redteam_topology.md`, `redteam_layout.md`, `fresh_lens.md` and
   `dispositions.md`. That is different from "nobody looked", and it is also
   different from a completed narrative pin review. If your process requires the
   latter, this release does not provide it.
10. **The 61-row rotation authority table is NOT in this archive.** A-ROT is
   green and no row fell back to the name-keyed DB, but the table it resolves
   against lives in the fleet repo. What ships here is
   `verification/rotation_measurements_v13.txt`: the **15** rows measured for
   this revision, covering **26 of 189** CPL rows across 15 of the 51 distinct
   LCSC codes. For the remaining 36 codes a reader holding only this archive is
   trusting a document they cannot open. Partially offset by the operator-free
   re-measurement of seven codes recorded in
   `verification/rotation_C22046_measurement.md` (all seven agree with the
   table, including U_OPTO and CE1), and by §6, which puts every rotation-risky
   part in front of a human at the JLC preview. **Shipping the resolved 189-row
   provenance list as an artifact is the v1.4 fix.**
11. **`verification/parity.md` in this archive reads `REAL DISCREPANCIES: 1 ->
   FAIL`, and here is what that one is.** It is **`J_KEY_MATRIX` pad `MP`** —
   the two mechanical solder tabs on the 10-pin keypad connector.
   `source/parity_padmap.txt` line 14 declares a board-stage bond
   `SM10B-GHS-TB MP GND_ISO`; **on the shipped board those two pads carry NO
   NET.** Every other connector's tabs ARE bonded — **RE-MEASURED
   2026-07-30 on the v1.7 board: `J_ESTOP`, `J_MODE`, `J_RH_AMBIENT`,
   `J_RH_EXHAUST`, `J_THERM_A`, `J_THERM_B`, `J_PWR` all carry `GND` on both MP
   tabs** (`J_DOOR` is deleted, so it drops off this list). **`J_KEY_MATRIX`
   alone still reads `(NO NET)` on both tabs, and that is unchanged in v1.7.**

   **MEASURED CONSEQUENCE — it is NOT an isolation defect, and the measurement
   is the reason to believe that rather than the argument:**

   | path | measured | requirement |
   |---|---|---|
   | path | measured | method | requirement |
   |---|---|---|---|
   | KEYPAD_ISO → all other netted copper (the rule as written) | **6.1200 mm** | true polygon, copper clearance, all four layers incl. filled pours; **not creepage — see the blind-spot note below** | >= 6.000 |
   | floating MP → KEYPAD_ISO copper | 0.5810 mm | true polygon, copper clearance | — |
   | floating MP → all other netted copper | **13.3151 mm** | true polygon, copper clearance | — |
   | **two-hop KEYPAD_ISO → floating MP → other** | **13.8960 mm** | sum of the two hops above | >= 6.000 |

   A floating conductor inside a barrier is only dangerous when it *splits* the
   gap; this one sits **0.581 mm** from the keypad domain and **13.315 mm** from
   everything else, so it is electrically part of the keypad side and adds
   nothing to any leakage path. What is actually lost is the **ESD/shield drain
   for that connector's shell** — the tabs float instead of returning to
   `GND_ISO`.

   **THE FLOATING TAB IS CORRECT AND MUST STAY FLOATING. Do not "fix" it.**
   An earlier revision of this item called for bonding it to `GND_ISO` in v1.4.
   **That instruction was wrong twice over and is retracted:**

   - **`GND_ISO` DOES NOT EXIST.** Measured: 0 occurrences in
     `source/cooksense.net` and 0 in `source/cooksense.kicad_sch`. The only
     ground net on this board is `GND`. The name survives in exactly two places,
     both of which are now known defects: `source/parity_padmap.txt` line 14,
     and the F.Silkscreen caption at (106.000, 21.000) reading
     "KEYPAD ISOLATION COMB >=6mm creepage **GND_ISO ONLY**". **Both name a net
     that was never created.**
   - **Bonding the tab to the ground that DOES exist would BREAK the barrier.**
     The tab sits **0.5810 mm** from KEYPAD_ISO copper. Put `GND` on it and
     `keypad_isolation_6mm` fires at 0.581 mm against a 6.000 mm requirement —
     **a 10.3x violation**, and the worst one on the board. The tab is floating
     *because* there is nowhere safe to land it.

   **What is actually true:** the keypad connector's shell has no ESD drain, and
   it cannot have one until an isolated ground net exists. That is an
   isolation-topology change, not a re-route. **v1.4 items:** (a) delete the
   `GND_ISO` token from `parity_padmap.txt` and from the silk caption, or create
   the net properly; (b) drop the `B.NetName != ''` clause from the barrier
   rules so floating copper is in scope.

   **Why no gate caught the naming defect:** that trailing `B.NetName != ''`
   **exempts unnetted copper by construction** — DRC is structurally unable to
   see a floating pad, so `0 violations` was never evidence about it. The
   converter-parity check DID see it and said FAIL; the artifact shipped and
   nothing read it until the fifth review.
12. **Silkscreen: the safety captions are 0.60 mm character height, and NOTHING
   IN THIS ARCHIVE CHECKS TEXT HEIGHT AGAINST A FAB FLOOR.** Every gate that
   looked at silk checked **stroke width** (0.150 mm, exactly on JLCPCB's 0.15 mm
   floor). JLCPCB publishes a minimum silkscreen **character height** of about
   **1 mm**; all seven ADR-0012 safety captions are **0.60 mm**. They may print
   thin, broken or not at all. **The captions are a backup to this document, not
   the other way round — treat ORDER_README §11 and §1 as the authority for
   field wiring and enclosure, and inspect the first article's silk before
   assuming any board-level warning is legible.** Related, and previously
   undisclosed: **both** J_ISOLOOP silk features are inside the 78 ignored silk
   violations — its refdes at (189.300, 101.000) is one of the 24
   `text_thickness` items and is **worse than earlier revisions stated**: KiCad
   reports *"min thickness 0.1500 mm; actual 0.1125 mm"* — the stored field is
   0.150 mm but the PLOTTED pen is clamped to 25 % of the 0.45 mm character
   height, so it prints **25 % BELOW the fab floor**, not at it, and its outline box
   is **all three** `silk_edge_clearance` items. The earlier disclosure said
   "zero of the 78 involve a safety caption", which is true and was verified, but
   it never checked the two silk features on the isolated 30 V block itself.
13. **The gerbers were plotted WITH drill marks; a default `kicad-cli pcb export
   gerbers` does not reproduce them byte-for-byte.** F.Cu/In1/In2/B.Cu each carry
   1047 extra 0.150 mm and 105 extra 0.350 mm dark flashes, and F.Mask/B.Mask 105
   extra 0.350 mm openings. Every mark was verified concentric inside an existing
   via pad, PTH pad or NPTH hole, so all are inert — but a reviewer re-exporting
   to compare must enable drill marks or they will see thousands of spurious
   differences.
14. **Documents this archive CITES but does not CONTAIN.** ADR-0001, ADR-0006,
   ADR-0012, ADR-0013, `BRIEF.md`, `01_docs/pin_map.md`,
   `02_parts/LTV-817S-TA1/part.yaml` (the CTR 50 % bin the whole §11 current
   budget rests on), `electrical_invariants.yaml` (the assert §11 cites as the
   two-screw guarantee), `floorplan.yaml`, and the `SUPERSEDED.md` files of the
   earlier releases. Individually minor; **collectively, several load-bearing
   safety numbers cannot be re-checked from inside this archive.** v1.4 should
   ship the cited ADRs and part.yaml files.
15. **THE DRC GATE CANNOT SEE CREEPAGE, AND THE RULE THAT REQUIRES IT IS
   WRITTEN IN THE ONLY PRIMITIVE KiCad HAS.** `keypad_isolation_6mm` reads
   *"must hold >=6mm creepage"* in its comment and
   `(constraint clearance (min 6.0mm))` in its body, because the DRU language has
   no creepage primitive. **It requires one property and measures another.**
   Creepage is a surface path; whether an outline notch interrupts that path is a
   question a clearance rule cannot express, in either direction. So
   `0 violations` from DRC is **not evidence about creepage** — the `I-HW` gate,
   which models the fastener and walks the board surface, is what measures it,
   and it reports **6.5984 mm** at H4 against 6.000 mm required.

   **The episode that made this legible, recorded without drama because the
   lesson is transferable.** On 2026-07-26 a reviewer applied IEC 60664-1's
   minimum-groove-width rule (X = 1.5 mm at PD3) to this notch and ruled the
   barrier FAILING at 4.0286 mm. **The X rule governs a groove — a channel with
   material at the bottom — where the question is whether contamination bridges
   across it. This is a through-notch reaching the board edge**, so there is no
   surface across it and it drains at the open end. The ruling was reversed the
   same day. Before it was, three placement attempts were made to "fix" a barrier
   that was not broken; they are in item 16 because what they proved is worth
   keeping.

   **THE TRANSFERABLE POINT: CHECK WHICH QUANTITY THE REQUIREMENT NAMES BEFORE
   MEASURING.** Creepage and clearance are different properties and a notch
   affects exactly one of them. The same release had already shipped three
   numbers with the metric left implicit (bbox vs true-polygon vs all-copper on
   the ISO pair; the I-HW table; the H4 geodesic). **Every isolation figure in
   this document now states its method beside it**, which is the durable fix.
16. **K_STOP IS LOAD-BEARING GEOMETRY, NOT A FREE PART — and a corridor is a
   routing resource, not margin.** Established by three re-races during the H4
   episode and kept so nobody rediscovers it:
   - **`K_STOP.1`'s NORTH PAD EDGE IS A CREEPAGE CONSTANT.** Pad centre y30.380,
     radius 0.750 → north edge **y29.630** — and that number is already in
     `route.yaml`'s header as *"gap pads 29.63"*. With the keypad band cap at
     y23.200 it sets the **PRIMARY** keypad↔SELV creepage:
     **29.630 − 23.200 = 6.430 mm by construction.** Moving K_STOP north eats
     that 1:1, so **north travel is capped at 0.430 mm by the primary barrier**.
   - **East travel is capped at 1.500 mm** by the board edge.
   - **The 1.800 mm between the relay's east pads and the board edge is a
     CORRIDOR, not slack** — `RSTOP_MID` and `KP_U6` climb it to reach the keypad
     domain. Taking 1.000 mm of it leaves 0.100 mm after the 0.700 mm
     `edge_band`; the router then goes around the west side and past the SELV
     coil pads, which measured 2 × `keypad_isolation_6mm` (5.2700, 5.4246) and 3
     unconnected.
   - Moving the part north far enough also puts `K_STOP.1` inside `route.yaml`'s
     full north band (User.2, y[9.9, 29.4]), where logic copper is forbidden, so
     `5V_STOP` cannot be routed to it at all — reproduced twice, not stochastic.
17. **THE KEYPAD BARRIER'S WORKING VOLTAGE, POLLUTION DEGREE AND MATERIAL GROUP
   ARE NOT IN THIS ARCHIVE — AND THE FIGURE PREVIOUSLY QUOTED FOR THEM BELONGED
   TO A DIFFERENT DOMAIN.** `keypad_isolation_6mm` is the rule that requires the
   6.000 mm; it cites only *"brief section 4/7 + ADR-0001"* and states **no
   working voltage, no pollution degree and no material group**. Neither
   `BRIEF.md` nor ADR-0001 ships here. Earlier revisions filled the gap with
   *"30 V working, PD3, material group IIIa"* — **that string is the comment on
   `opto_isolation_2mm`, whose condition is `A.NetClass == 'ISO_CONTACTOR'`: the
   CONTACTOR LOOP, a different domain.** It was reached for because it was
   adjacent and plausible, which is the same error class as §13 item 15's
   measuring-the-wrong-quantity.

   **What this costs a reader:** you cannot tell whether 6.000 mm is a ~3x design
   margin over an IEC minimum at low voltage, or is itself the minimum at a
   mains-referenced potential. That is exactly what decides how much the notch
   credit matters, and how much of a safety factor the 6.5984 mm represents. The
   4.0286 mm clearance is therefore reported in §1 as a **measurement**, not as a
   pass against a requirement this archive can show you.

   **v1.4 DEBT, named: ship the keypad domain's working voltage, pollution degree
   and material group — or the brief section that sets them — and cite them in
   the `keypad_isolation_6mm` rule comment where the requirement lives.**
18. **M-REPRO is green by metric, not by bytes.** Three from-source rebuilds are
   geometrically identical, but the files differ because the generator mints
   fresh UUIDs and KiCad serialises footprints in UUID order. A fleet-level fix
   is owned elsewhere; on this board the nondeterminism never reaches a via
   decision (via count has not varied across 5 observed builds).
19. **⚠️ NEW IN v1.6 — `J_MODE` IS A CROSS-PLUG HAZARD, NOT A FAIL-SAFE
   CONNECTOR.** An SHT45 pod harness in `J_MODE` energises the coil rail with
   all seven AND-chain terms and the Manual rail-cut bypassed. This gap is
   **mitigated by discipline only** (§10.5) and the mitigation is a human
   procedure, not a hardware property. The fix is copper — §10.6 — and it is
   deliberately deferred to the next ELECTRICAL revision so that this
   documentation-only release ships the same board as v1.5. **If you are
   commissioning this machine, §10 is the section to read twice.**
20. **⚠️ NEW IN v1.6 — ELEVEN OF THE EIGHTEEN SAFETY-CHAIN NETS HAVE NO
   RESTRICTIVE DEFAULT, AND FOUR OF THEM ARE PERMISSIONS.** Measured over the
   netlist: of the 18 nets feeding a permission/gating input on this board,
   **7 carry a pull resistor and 11 carry none at all** —
   `WD_OK`, `ESTOP_OK`, `MODE_AUTO_HW` and (**on v1.6 only**) `DOOR_OK` (the
   permissions driven by `U_WD` and `U_SCHM`; **on v1.7 `DOOR_OK` is deleted, so
   this set is THREE, not four**), plus `AND1`, `AND2`, `CTR_SAFE`, `FAULT`,
   `FAULT_SET_N`, `FAULT_LATCH_CLEAR`, `STOP_REQ_N` (internal nodes driven by
   the chain's own gates). Every one is a single push-pull CMOS output into
   LVC/HC inputs that have no bus-hold, so an unfitted, tombstoned or cracked
   part leaves an INDETERMINATE level that may read HIGH = permissive.

   The sharpest single-part cases: a dead **`U_SCHM` (SN74HC14, SOIC-14)**
   floats `ESTOP_OK` and `MODE_AUTO_HW` simultaneously (**and, on v1.6,
   `DOOR_OK` as well — deleted in v1.7**) — the
   E-stop can then read clear with the mushroom pressed, and the expander
   readbacks sample the SAME floating nets so software sees the same wrong
   answer with no independent cross-check. A dead **`U_LATCHB` (SN74LVC1G00,
   SOT-23-5)** floats `FAULT_LATCH_CLEAR` into both `U_AND3.C` and `U_CAND2.B`,
   removing the fault-latch permission from the coil rail and the external
   contactor at once. A dead **`U_WD` (TPS3823)** floats `WD_OK` into five CMOS
   inputs. **No single part floats all four permissions** — `U_SCHM` accounts
   for three and `U_WD` for the fourth.

   **This is what the source's own claim missed, and the correction is a matter
   of SCOPE, not arithmetic.** `03_tscircuit/src/cooksense.tsx` says "TEMP_OK
   was the ONLY permission in the safety chain actively pulled toward
   permissive. The other twelve are pulled restrictive". Checked here: those
   **twelve are exactly the Pi/expander authorization lines of BRIEF D10 item 8**
   — `HOST_AUTH`, `MCU_RELAY_ENABLE`, `CONTACTOR_REQ`, `KEY_RESET_N`,
   `STOP_REQ`, `RAIL_EN_A/B/RHA/RHE`, `DECU_G1_RAW`, `DECD_G1_RAW`, `REARM_N` —
   and **all twelve genuinely ARE pulled restrictive** (eleven × 100 kΩ to GND,
   plus `REARM_N` × 100 kΩ to 3V3, which is restrictive because it is
   active-low). The sentence is not wrong about its twelve. It is wrong as a
   statement about "the safety chain", because it counts only the
   SOFTWARE-driven lines and the four HARDWARE-derived permissions are in
   neither group.

   **Partly caught at bring-up** (§7 step 2 exercises the watchdog; step 3 reads
   TP_ESTOP / TP_TEMPOK / TP_FAULT). **An in-service failure — ESD, thermal
   cycling, a solder crack — is not caught at all.** Cost of the hardware fix:
   four 0402 pull-downs for the permissions (eleven for the whole chain), which
   is a copper change and therefore not in this release. Firmware mitigation
   available today: §7a-2 (`GPPUB = 0x00`), which prevents the failure being
   made *deterministically* permissive by a register write.
21. **⚠️ NEW IN v1.6 — `REARM_N` HELD LOW PERMANENTLY DEFEATS THE FAULT LATCH.**
   Full analysis and the required negative bring-up test are in §7a-1. Mitigated
   by a stated software invariant only; the hardware fix (an edge-detect on
   `REARM_N`) is deferred to the next electrical revision.
22. **The `SN74HC14DR` dossier's gotcha is STALE, and it is the only doc that
   describes the part's usage.** `02_parts/SN74HC14DR/part.yaml` says "gates
   A/B: E-stop chain […]; unused inputs 3A/4A/5A/6A tied GND, outputs NC". On
   this board **all six gates are used** — 1A/1Y+2A/2Y = E-stop, 3A/3Y+4A/4Y =
   mode, 5A/5Y+6A/6Y = door (netlist-verified). The text describes the
   v1.0/v1.1 build. No electrical consequence — the netlist, not the prose, is
   what the board is built from — but it is recorded because this is the third
   inherited-prose defect found on this board and the pattern is the finding.
23. **The `J_MODE` pole labels contradict themselves in the source, and one of
   the two is WRONG.** `03_tscircuit/src/cooksense.tsx` line 632 says "pole A
   (pins1-2) = physical coil-EN gate […]; pole B (pins3-4) = MODE_RAW logic";
   six lines later the same block says "pole B (mode sense) = pins 1-2 (3V3 ->
   MODE_RAW); pole A (coil gate) = pins 3-4". **The netlist settles it: pins 1-2
   are 3V3/MODE_RAW and pins 3-4 are KEY_RELAY_ALLOWED/COIL_EN**, so the second
   statement is right and line 632 is a survivor of the pre-re-pin layout. A
   harness built from line 632 would put the coil-gate pole across 3V3 and
   MODE_RAW and leave `COIL_EN` open — the machine would be permanently
   unable to arm (fail-safe, but a wasted commissioning day). **The pinout in
   §10.1 of this document is the authority; build the mode-switch harness from
   that table, not from the source comment.**

---

## 14. ⚠️ FINDINGS FROM THE SEAL RE-GATE — the v1.8 work order

Both red-team lenses were RE-GATED fresh-context for this seal attempt (see
`verification/redteam_topology.md` and `verification/redteam_layout.md`).

- **topology / protection / ratings** — `design_verdict: SOUND`,
  `order_verdict: BLOCKED-SOURCING`. No design P0. Three P1s, below.
- **layout / thermal / power-integrity** — `design_verdict: DEFECTIVE`,
  `order_verdict: BLOCKED-SOURCING`. **TWO P0s, which is why v1.7 did not
  seal.** They are in `MANIFEST.txt` under "THE TWO P0s" with the independent
  re-measurement; in one line each: the LDO is graded at 0.30 A while the same
  file declares 0.40 A of switched sensor rails hanging off net `3V3`
  (measured on the board — all four `AO3401A` sources are on `3V3`), and
  `pdiss_max_mw: 1200` is a 25 °C figure applied with no ambient term on a
  board the brief places in a 50–75 °C enclosure. **Both are declarations in
  `power_tree.yaml`, not copper.** Plus two P1s: the fastener-disc creepage
  model was derived at H4 and applied nowhere else (at H1 it goes NEGATIVE
  against an isolated keypad line, −0.0500 mm to `KP_D1`), and no stackup or
  copper weight is declared anywhere, so every ampacity and isolation number
  here is unverifiable at the fab.

The P1s below land in the buyer's document and the next revision's work order,
which is what P1 means in this repo — they do not block a release. The P0s do.

### P1-A — the PRESS one-shot's **500 ms HARD bound is claimed from a tolerance stack that omits the timing capacitor's dielectric**

`BRIEF.md` §4 sets *"max key 500 ms"* as a HARD sequencing bound, and it is one of
the four pillars of the "the LLM can at most press valid keys" safety argument.
Four documents publish the same worst case — **436 ms** — and all four compute it
as `K × R × C` with `C+10%`, the ±10 % PART tolerance measured at 25 °C.

**The fitted part is `C_OS` = `CL10A105KB8NNNC`, a Samsung 0603 1 µF 25 V X5R
±10 %. `X5R` is an EIA Class-II code whose second and third characters mean
±15 % capacitance change over −55…+85 °C, relative to the 25 °C value** — a term
that is MULTIPLICATIVE with the tolerance and absent from every one of the four
stacks:

```
C_max  = 1.00 uF x 1.10 (tol @25C) x 1.15 (X5R tempco)  = 1.265 uF
tw_max = 0.770 x 515.1k x 1.265u                        =  501.7 ms   > 500 ms HARD
tw_max = 0.784 x 515.1k x 1.265u  (K from SCHS166F's own EC table) = 510.9 ms
       ... and at that table's upper ratio,                           524.5 ms
```

**The claimed headroom is 64 ms and the X5R temperature coefficient alone is
±65 ms at this pulse width — the stated margin is exactly the size of the term
that was left out.** DC-bias derating on a 25 V 0603 pushes the other way and the
real part is probably inside 500 ms, but that is a hope, not the stack, and the
stack is what four documents publish.

From the same arithmetic: `tw_min` = 0.63 × 505.1 k × 0.765 µF = **243 ms**, so
the board cannot produce the brief's "typical 100–200 ms" press. **The one-shot
is always at least ~240 ms** — plan commissioning around that, not around 150 ms.

**v1.8 remedy (actionable):** make the timing capacitor **C0G/NP0** (±30 ppm/°C —
the tempco term vanishes), or drop `R_OS` to ~430 kΩ, which restores >100 ms of
true headroom against the hard bound.

### P1-B — the LDO dropout margin that unblocked E-TOPO **goes NEGATIVE once the board's own copper and a cited connector resistance are counted**

`power_tree.yaml` derives `vin_min` from three cited datasheet maxima (F1 70.0 +
`Q_REV` 73.5 + eFuse 47.0 = 190.5 mΩ at 0.50 A). All three are right; two whole
classes of series resistance are missing. The ladder, measured:

```
 +55.0 mV   declared
 +15.4 mV   with the board copper at 20 C   (two independent methods agree: +15.4 / +16.3)
  +5.4 mV   with the connector at 20 C
  -2.5 mV   with the connector at 70 C
  -5.5 mV   using the eFuse's -40..125 C RON row (53 mOhm instead of 47)
```

**This is a DECLARATION defect, not necessarily a board defect**, and the
distinction is the whole point: the 1300 mV dropout figure is a datasheet MAX at
**0.8 A** applied here at **0.3 A**, where the same datasheet says only that
dropout "decreas[es] at lower load currents" and publishes no curve. The archive
is honest that the 0.3 A dropout is OWED. The physical board is very probably
fine. What is not fine is that **E-TOPO's PASS is owed to the omitted terms
rather than to margin.**

**⚠️ THIS PROMOTES §0 STEP 2 FROM ENCOURAGED TO MANDATORY: measure V_IN − V_OUT
at `U_LDO` at bring-up.** That single measurement retires the OWED fact
completely.

### P1-C — **E-MARGIN cannot fail on this board**, and the rail it would have caught declares a drop no `AO3401A` can deliver

**(a) The gate is inert.** `policy_audit` prints
`E-MARGIN | N-A | no rail declares load_uv_threshold`. The board has at least SIX
regulated rails feeding known fixed-brownout loads — TPS3823-33 at 3.00 V,
MAX31856 at 3.00 V, MCP3208 at 2.70 V, two MLX90640 at 3.10 V, HX711 at 2.60 V.
E-MARGIN is OPTIONAL-ACTIVATED by a key nobody wrote, so it grades nothing and
prints a green-looking N-A **that has never had the chance to be red.** That is
the `jlc_twin`-exit-0 shape `tests/README.md` names, appearing in the power gate.

**(b) The rail it would have graded tightest carries an impossible declaration.**
`power_tree.yaml` declares the four switched sensor rails at `vin_min: 3.201` /
`vout_min: 3.2` at `iout_max_A: 0.1` — **1 mV of drop at 100 mA, i.e. a 10 mΩ
switch.** The switch is an `AO3401A` whose own dossier cites **60 mΩ MAX at
V_GS = −4.5 V, 25 °C** = 6.0 mV at 100 mA — six times the declared figure — and
**these four run at V_GS = −3.3 V, below the lowest V_GS the datasheet specifies
at all**, so the real R_DS(on) is higher than 60 mΩ and is not bounded by any
published number.

**v1.8 work order:** write `load_uv_threshold` + `ir_budget_mohm` for all six
rails so E-MARGIN can actually fail, and correct the switched-rail drop
declaration to the AO3401A's real R_DS(on) at this board's gate drive.

### P2s

Recorded in `verification/redteam_topology.md` and
`verification/redteam_layout.md` and in the findings ledger
(`verification/DISPOSITIONS.md`). Two worth a buyer's eye:

- **`fab/bom.csv` row 55 names `SN74HC238DR` (TI) beside `C5620`, and `C5620` is
  `74HC238D,653` (Nexperia).** JLC matches on the CODE, so the part fitted will
  be the Nexperia one — pin- and function-compatible, so this is paperwork rather
  than electrical. But `02_parts/SN74HC238DR/part.yaml` is the TI dossier, and it
  is the file every V_OH / V_IH argument about the decoder reads from. (Two other
  rows differ only cosmetically and are NOT findings: `C558584` is
  `MCP23017T-E/SS` vs the BOM's `MCP23017-E/SS`, a tape-and-reel suffix; `C16939`
  is `MCP3208-CI/SL` vs `MCP3208-CI-SL`, slash versus dash.)
- **Three reel MOQs sit far above the build need** and are disclosed nowhere in
  `fab/`. They are not blockers — unlike `C265111`, their MOQ is BELOW their
  stock, so the parts are buyable; you will simply buy more than you need.
