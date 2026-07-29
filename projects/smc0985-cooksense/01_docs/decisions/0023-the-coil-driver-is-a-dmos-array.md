# 0023 — The reed-coil driver is a DMOS array, not a Darlington array

Status: accepted, 2026-07-29
Board: cooksense (MAIN). The interposer is unaffected.
Supersedes: nothing. Amends ADR-0003 (the coil-driver stage) in ONE respect —
the part. The safety architecture, the AND-chain gating, the COM-clamped
switched rail and the DO-NOT-SUBSTITUTE posture on the relays are unchanged.
Discharges: ADR-0007's own worked example ("reed coil pull-in margin at 70 °C |
coil R, V_CE(sat), tempco → margin < 0 → FAIL"). Closes red-team TOPO P1-2,
re-graded P0 on 2026-07-29.

## Context — the board does not guarantee that its relays close

`U_ULNA`/`U_ULNB` were **ULN2803ADWR** (TI, SOIC-18W DW), sinking twelve
`DIP05-1A72-13L` reed coils from the AND-chain-gated `5V_KEY_RELAY` rail. On
2026-07-29 the pull-in margin was computed for the first time in this tree —
before that date it was computed **nowhere**, which is why six sealed releases
carry it.

The coil's own datasheet (Standex DIP-series V03, p.2 "Coil Data (**at 20 °C**)"
— note 20, not 25) gives pull-in ≤ 3.500 V and a footnote, verbatim: *"The
Pull-In, Drop-Out Voltage and Coil Resistance will change at rate of 0.4% per
K."* So

    V_PI(T) = 3.500 × (1 + 0.004 × (T − 20))
    margin(T) = 4.740 − V_driver − V_PI(T)          (4.740 V = 5V_KEY_RELAY
                                                     vout_min, power_tree.yaml)

| enclosure (BRIEF §"enclosure ≤50 / 55 / 65 / 75") | V_PI | ULN2803A typ 0.67 V | ULN2803A worst 0.88 V |
|---|---|---|---|
| −20 (cold corner) | 2.940 | +1.130 | +0.920 |
| +25 (bench)       | 3.570 | +0.500 | +0.290 |
| **≤50 — the brief's NORMAL band** | 3.920 | +0.150 | **−0.060** |
| +55 warn          | 4.140 | +0.080 | **−0.130** |
| +65 stop          | 4.320 | −0.060 | −0.270 |
| +70 envelope top  | 4.200 | **−0.130** | −0.340 |
| +75 hard          | 4.270 | −0.200 | −0.410 |

Crossover: **60.7 °C typical, 45.7 °C worst case.** 45.7 °C is **below the
brief's own ≤50 °C NORMAL enclosure band.** Cross-checked in the other
currency, because pull-in is an ampere-turn condition and the two views must
agree: I_PI = 3.500/500 = **7.00 mA and temperature-independent**, while
delivered current falls to **6.81 mA at +70 °C** (typ drop, nominal 500 Ω).
Both views say the relay is not guaranteed to close.

**−20 °C is comfortable (+1.130 V), so a room-temperature bench test will never
find this.** That is the property that makes it a P0 rather than a note.

### The Darlington drop IS the entire deficit

0.67–0.88 V of a 4.740 V budget is spent inside the driver. Nothing else in the
chain is wrong: the rail is at its specified floor, the coil is at its specified
maximum pull-in, and the tempco is the coil's own published number.

There is a second, independent reason to remove the ULN2803A, and it is an
evidence-quality reason (ADR-0005 / M-ENTRY): **SLRS049G specifies V_CE(sat)
only at I_C = 100 / 200 / 350 mA**, two orders above the 7 mA coil. The 10 mA
figure had to be **digitized off Figure 1 at 900 dpi** (band 0.629–0.674 V) and
its worst case **derived** from the EC table's own max/typ ratio. The whole
verdict rested on a number read off a curve. Swapping the part does not win the
argument about that number — it makes the number irrelevant.

## Options considered

**(a) Raise the coil rail.** REFUTED ARITHMETICALLY. The margin needs
+0.130 V at +70 °C on typ and +0.340 V on worst case, i.e. `5V_KEY_RELAY`
vout_min ≥ 5.080 V. ADR-0021 specifies the supply 4.85–5.25 V; `5V_PROTECTED`
vout_min is 4.754 V and Q_COIL's RDS(on) costs 11 mV, so the absolute ceiling
reachable without a new converter is **4.839 V — worth +0.099 V**, less than
either requirement. Getting above it means a BOOST, i.e. a new converter, a new
rail and a collision with ADR-0021's OV divider, whose 26.1k/100k legs are
pinned between a 5.25 V ceiling and the SMBJ5.0A's 6.40 V V_BR floor with
±118 mV / ±161 mV of slack. There is no room to move it. Rejected.

**(b) Narrow the declared temperature envelope.** NOT ADMISSIBLE. The
worst-case crossover, 45.7 °C, is **below the brief's own ≤50 °C normal band**,
so this is not a trim of a hard limit — it is a redefinition of *normal* on a
COOKING appliance. Rejected on the spec, per D-SPEC (a requirement is not
silently downgraded).

**(c) Discrete MOSFETs.** Works electrically — it is what `K_STOP` already
does — but it replaces two SOIC-18 lands with 12 FETs **plus 12 flyback
diodes**, because the internal COM clamp goes away. New footprints, new
placement, a re-plan of the isolation comb and a full re-route. Rejected
against a drop-in.

**(d) CHOSEN — a pin-compatible DMOS array: Toshiba TBD62083AFWG**
(LCSC **C165895**, TOSHIBA `TBD62083AFWG,EL`, package string `SOIC-18-300mil`,
stock **2334**, $1.2252, live read 2026-07-29; alternate **C108880** stock
6851). Cheaper than the part it replaces.

## Decision

> Replace `U_ULNA` and `U_ULNB` with **TBD62083AFWG**, and make the pull-in
> margin a `node_level` invariant rather than a table in an ADR.

Three things had to be TRUE for this to be a drop-in rather than a redesign, and
each was read from the datasheet, not from the part's reputation:

1. **The pin map is identical.** p.2 "Pin explanations" — a TABLE, not a figure:
   1–8 = I1–I8, 9 = GND, 10 = COMMON, 11–18 = O8–O1. Same order, same
   reverse-order outputs, same OUTn-faces-INn geometry.
2. **The land is the same.** p.9 `P-SOP18-0812-1.27-001`, read at 300 dpi: body
   11.35–11.68 × 7.37–7.62 mm, lead span 10.01–10.64 mm, pitch 1.27 mm. TI
   SLRS049G p.1 gives DW as 11.50 × 7.50 mm — dead centre of that band. Both are
   JEDEC 300-mil 18L SOIC; LCSC gives C165895 and the outgoing C9683 the *same*
   package string. `Package_SO:SOIC-18W_7.5x11.6mm_P1.27mm` is unchanged.
3. **The freewheel path survives.** p.2 "Equivalent circuit (each driver)"
   shows a **clamp diode with its anode at OUTPUT and its cathode at COMMON** —
   functionally the ULN2803A's COM diode — with VF ≤ 2.0 V at 350 mA in the p.5
   EC table. The twelve reed coils have NO external flyback diode; the COM path
   is their only clamp, and losing it would have made this a topology change.
   Verified from the FIGURE, not inferred from the pin name.

And the input side is checked rather than assumed: on this board IN1–8 come from
SN74HC238 decoders whose VCC is **3V3, not 5 V**. TBD62083A V_IN(ON) MAX is
**2.5 V** (p.4 Operating Ranges and p.5 EC), so 3.3 V clears it by 0.8 V. (The
`TBD62084A` in the same datasheet needs **7.0 V** and would not switch at all —
recorded in the dossier as a DO-NOT-ORDER.)

### The new margin

R_ON is quoted at three current points — 100/200/350 mA — and all three resolve
to **one resistance: 2.0 Ω typ, 3.25 Ω MAX** (p.5 EC table, Test Circuit 2
defines `RON = VDS / IOUT`). A resistance may legitimately be extrapolated DOWN
in current; two V_BE drops may not. No R_ON tempco is published, so the check
uses a deliberately pessimistic **6.50 Ω = 2× the 25 °C maximum** (a 60 V-class
DMOS typically shows ~+0.7 %/K, i.e. 4.3 Ω at +70 °C):

    V_DS(7 mA) = 7.0 mA × 6.50 Ω = 0.046 V     (0.023 V at the 25 °C table max)

| enclosure | V_PI | margin, hot-bound driver 0.046 V | margin, 25 °C table max 0.023 V |
|---|---|---|---|
| −20 | 2.940 | +1.754 | +1.777 |
| +25 | 3.570 | +1.124 | +1.147 |
| **+50 (brief NORMAL)** | 3.920 | **+0.774** | **+0.797** |
| +55 | 4.140 | +0.554 | +0.577 |
| +65 | 4.320 | +0.374 | +0.397 |
| +70 (envelope top) | 4.200 | +0.494 | +0.517 |
| **+75 (hard)** | 4.270 | **+0.424** | **+0.447** |

**Positive at every corner, on the pessimistic driver bound.** Ampere-turn
cross-check at +70 °C: 4.740 / (600 + 6.5) = **7.815 mA delivered against
7.00 mA required, +11.6 %** (was 6.81 mA, a −2.7 % deficit). At +75 °C,
7.689 mA, +9.8 %.

The conclusion is insensitive to the one unpublished number: even at **10×** the
table max (32.5 Ω) the drop is 0.228 V against a +70 °C budget of 0.540 V. That
is why accepting an unpublished tempco was safe here and was not safe for the
Darlington.

## The claim becomes a check (ADR-0007)

A margin table in an ADR is exactly the artifact ADR-0007 exists to abolish. The
invariant, authored against `03_src/cooksense/rules/electrical_invariants.yaml`:

```yaml
  - assert: node_level
    net: COIL_U1_N
    receiver: K_U1.2                 # DIP05 tsx pad2 = COIL_B, the driven end
    driver_state: contended
    aggressor: K_U1.1                # the coil, pulling UP to 5V_KEY_RELAY
    defender: U_ULNA.18              # the DMOS channel, pulling DOWN
    must_be: logic_low
    adr: "0023"
```

with `v_il_max: 0.540` on the DIP05 dossier's pad 2 — **`v_il_max` here is the
pull-in BUDGET, not a logic threshold**: node ≤ 0.540 V ⟺ coil sees
≥ 4.740 − 0.540 = 4.200 V = V_PI(+70 °C). The equivalence is exact, and it
converts the whole table above into one arithmetic assertion.

**IT IS NOT COMMITTED YET, AND THE REASON IS A CHECKER GAP, NOT A DESIGN
DOUBT — see `01_docs/journal/verify_cooksense.md` for the measured RED/GREEN
proof and the three-line patch it waits on.** `_load_part_electrical()` joins a
dossier to a netlist component through `sourcing.lcsc` + `sourcing.alternates`,
i.e. through an **LCSC code**. The thirteen reed relays are SELF-SUPPLIED: JLC
stocks none of them, so their netlist `value` is the **MPN**
`DIP05-1A72-13L`, and no LCSC code identifies them. The join therefore cannot
resolve, `node_level` returns UNREACHED, and E-INV would go from 136/136 to a
red gate on a limitation rather than on a defect. Writing the MPN into
`sourcing.alternates:` to force the join was considered and REJECTED: that field
means "pin-compatible substitute", this part is DO-NOT-SUBSTITUTE (spec 15.4),
and its own note records an alternate already WITHDRAWN for being a different
pin-out code. An inherited-defect-shaped fix to make a gate green is the thing
this repo keeps paying for.

The invariant was proven anyway, against a locally patched copy of the checker:
**GREEN with TBD62083AFWG (0.056 V ≤ 0.540 V), RED with ULN2803ADWR restored**.
Numbers and command lines in the journal.

## The two A-ROT rows the new codes need (MEASURED, and NOT YET LANDED)

A new LCSC code has no measured rotation row, so `export_jlc_package` BLOCKED —
correctly. `jlc_rotation_measure.py` against the JLC cached models with the
pcbnew-verified operator (never `jlc_twin`'s `jlc_offset`, canon M1):

| code | model | offset | pad-number rms | next best | margin |
|---|---|---|---|---|---|
| C165895 | `SOIC-18_L11.6-W7.5-P1.27-LS10.3-BL` | **270** | 0.1500 mm | 8.1344 (0/180); 11.5027 (90) | 54× |
| C558584 | `SSOP-28_L10.2-W5.3-P0.65-LS7.8-BL` | **270** | 0.0403 mm | 6.1624 (0/180); 8.7149 (90) | 153× |

Both are byte-identical to the rows their predecessors C9683 and C506653 carry —
same board footprint, same JLC model file — and they were MEASURED rather than
copied precisely so that the identity is a RESULT. Both DECLARE
`single-channel` (a dual-row package is its own 180° reflection, the pad cloud is
degenerate at 90/270, there is no size-class channel, and a pin-1 dot follows pad
numbering so it is not admissible), and therefore both oblige the JLC
order-preview human gate, exactly as their predecessors do.

**These rows belong in `skills/jlcpcb-fab/scripts/jlc_lcsc_rotations.csv` and
this session could not write there.** The clean export (`A-ROT OK: all 208 CPL
rotations are sourced`) was proven through the resolver's OWN
`JLC_LCSC_ROTATIONS` env override pointing at a copy. **A-ROT WILL BLOCK AGAIN
UNTIL THEY LAND** — this is the one seal prerequisite outside this project's
pathspec, and the rows are reproduced here verbatim because `06_build/` is
gitignored and would not carry them:

```csv
C165895,270,"TBD62083AFWG octal DMOS sink driver in SOIC-18 (SOP-18-300mil); smc0985-cooksense U_ULNA + U_ULNB -- the reed-coil driver bank, ADR-0023 (replaces C9683 ULN2803ADWR, SAME land). Measured 2026-07-29 with jlc_rotation_measure.py against JLC's SOIC-18_L11.6-W7.5-P1.27-LS10.3-BL (the SAME model file C9683 resolves to) using the pcbnew-verified operator. PAD-NUMBER fit: offset 270, rms 0.1500mm vs 8.1344mm next best (0/180 both 8.1344, 90 11.5027) = 54x. NUMBERS ARE IDENTICAL TO THE C9683 ROW, as they must be: same board footprint, same JLC model, only the LCSC code changed -- and the row is measured rather than inherited precisely so that identity is a RESULT and not an assumption. DECLARED single-channel: dual-row SOIC-18 is its own 180 reflection, pad cloud DEGENERATE at 90/270 (both 0.1500), no size-class channel, pin-1 marking (270 at 1.3918mm) not admissible. NB the generic name-DB carries ^SOP-18_,0 which would resolve this part to 0 -- 270 degrees wrong -- so this row exists to displace that rule as well as to satisfy A-ROT. Per RULE 3 this row MUST pass the JLC ORDER-PREVIEW HUMAN GATE.",single-channel
C558584,270,"MCP23017T-E/SS I2C GPIO expander in SSOP-28; smc0985-cooksense U_EXP (replaces C506653 MCP23017-E/SS, which went to LCSC stock 0 on 2026-07-28 -- SAME die, SAME land, T = tape-and-reel identifier only per DS20001952C PRODUCT IDENTIFICATION SYSTEM). Measured 2026-07-29 with jlc_rotation_measure.py against JLC's SSOP-28_L10.2-W5.3-P0.65-LS7.8-BL (the SAME model file C506653 resolves to) using the pcbnew-verified operator. PAD-NUMBER fit: offset 270, rms 0.0403mm vs 6.1624mm next best (0/180 both 6.1624, 90 8.7149) = 153x. Numbers identical to the C506653 row, measured not inherited. DECLARED single-channel: dual-row SSOP-28 is its own 180 reflection, pad cloud DEGENERATE at 90/270, no size-class channel, pin-1 marking not admissible. Per RULE 3 this row MUST pass the JLC ORDER-PREVIEW HUMAN GATE.",single-channel
```

## class_sweep (ADR-0007 item 4 — name the CLASS, not the incident)

```yaml
class_sweep:
  defect_class: "reed coil whose low-side driver's on-state drop is a
    non-negligible fraction of the pull-in voltage budget"
  members: [K_U1, K_U2, K_U3, K_U4, K_U5, K_U6,
            K_D1, K_D2, K_D3, K_D4, K_PRESS, K_STOP]
  covered:  [K_U1, K_U2, K_U3, K_U4, K_U5, K_U6,
             K_D1, K_D2, K_D3, K_D4, K_PRESS]
  excluded:
    K_STOP: "not a Darlington and not on this rail. Its coil sits on the ungated
      5V_STOP (vout_min 4.754 V, a 0R link) and is sunk by a dedicated 2N7002
      (Q_STOPDRV) whose V_DS at ~7 mA is ~0.10 V: margin +1.714 / +1.084 /
      +0.734 / +0.454 V at -20/+25/+50/+70 C, which reproduces the review's
      '+450 mV at 70 C' exactly. CAVEAT CARRIED, not dismissed: the 2N7002
      datasheet is NOT COMMITTED (02_parts/2N7002 datasheet.url is an LCSC
      product page, not a PDF), so 0.10 V is an ESTIMATE. It is not load-bearing
      -- at an absurd 0.50 V the +70 C margin is still +0.054 V -- but it should
      be cited before anyone leans on it."
```

Eleven of the twelve keypad relays are covered by the same part change as
`K_U1`; the twelfth path, `K_STOP`, is excluded WITH ITS NUMBERS. That is the
M-WIDTH discipline ADR-0020 failed (it fixed one of six pins).

## Consequences

- **Margin:** +0.774 V at the brief's +50 °C normal band and +0.424 V at the
  +75 °C hard limit, on the pessimistic driver bound. Was −0.060 V and −0.410 V.
- **Evidence quality improves independently of the margin:** a guaranteed EC
  table row replaces a 900-dpi digitization of a typical curve.
- **BOM cost falls.** C165895 $1.2252 against C9683's $6.22 (2026-07-19 note).
- **Thermal demand falls ~20×:** 8 channels at once dissipate 2.5 mW against
  49 mW. The p.3 Note-4 board rating (1.31 W) stops being interesting.
- **Zero geometric change.** Same footprint, same placement, same nets, same
  isolation geometry, same route. The netlist differs from v1.7's only in
  component VALUES.
- **NEW, and named because it is the one place this part is worse:** a DMOS
  channel's R_on RISES with temperature where a Darlington's V_BE falls, and
  Toshiba publishes no tempco. Handled by checking against 2× the 25 °C max and
  by showing the verdict survives 10×. If a Toshiba app note ever publishes the
  real figure, tighten the dossier and re-run — do not assume it is better.
- **`02_parts/ULN2803ADWR/` IS RETAINED, AND THIS ADR IS WHERE THAT WAS GOT
  WRONG FIRST.** It was DELETED while landing this decision, citing the 02_parts
  contract's *"rejected candidates never get a committed PDF — the binary is
  worthless, the reason is not"*. `tests/run_tests.sh` went RED inside the hour:
  `t1_fleet_regrade.py` reported `F-MPN row 56 (U_ULNA,U_ULNB): LCSC C9683
  resolves NO MPN from any authority` against **`cooksense-v1.6-2026-07-27`, the
  LIVE release**. `02_parts/` is the MPN authority for EVERY release, and C9683
  is in the BOM of six of them; the contract line is about candidates that were
  never USED, and a part that SHIPPED is a different class. The same mistake
  orphaned `C506653` by moving the MCP dossier's `sourcing.lcsc` — fixed by
  moving `alternates:` to the `{lcsc:, mpn:}` MAPPING form, which is the only
  form `bom_legibility_check.py` reads (it silently skips bare code strings, so
  that file's long-standing `alternates: [C47023]` had never resolved anything).
  Both dossiers now carry the reason in their own text. **A superseded part's
  dossier is release paperwork, not clutter.**
- **Sourcing, same session:** `U_EXP`'s `C506653` MCP23017-E/SS read stock **0**
  (confirmed live, twice). Replaced by **C558584 MCP23017T-E/SS, stock 7490** —
  the *same die in the same SSOP-28 package*; DS20001952C's PRODUCT
  IDENTIFICATION SYSTEM lists (f) `MCP23017-E/SS` and (g) `MCP23017T-E/SS` as
  the same device, the `T` being the tape-and-reel identifier only. Pin- and
  register-identical by construction, and cheaper ($1.7105 vs $1.8749). This is
  a D-SPEC class (a) outcome — sourceable at the declared cost-ceiling tier — so
  no D-TIER decision is owed.
