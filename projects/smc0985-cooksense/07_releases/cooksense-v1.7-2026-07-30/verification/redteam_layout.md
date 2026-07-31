# v1.7 RE-GATE 4 — ADVERSARIAL RED TEAM, LAYOUT / THERMAL / POWER-INTEGRITY LENS

**Subject:** `06_build/staging/cooksense-v1.7/` (pre-seal staging archive)
**Board:** `04_kicad/cooksense.kicad_pcb`, md5 `9f4fd5fae810f40a52b1035df727243c` — **VERIFIED BY ME**
(`md5sum`), so the copper under review is the copper the release claims.
**Reviewer:** zero-context adversarial lens, no prior involvement. Work class: JUDGMENT.
**Date:** 2026-07-30
**Material change under review:** a DECLARATION change only — declared operating ambient narrowed
75 °C → 65 °C (ADR-0029), plus a new MANDATORY six-measurement bench gate in `ORDER_README.md` §7b.
No copper, netlist, BOM or CPL change.

```
design_verdict: SOUND
order_verdict:  BLOCKED-SOURCING
```

**P0 count: 0.** Two P1s, six P2s. Every load-bearing number below is marked MEASURED (with the
command and the value) or INHERITED (with its source, not re-verified).

---

## 1. What I did, and what I refused to do

I did not read any prior review, disposition, journal, learnings or status file. Every number in
this document is either produced by me from `04_kicad/cooksense.kicad_pcb` and `02_parts/` /
`03_src/` with `/usr/bin/python3` + `pcbnew` (KiCad `10.0.4`), or explicitly marked INHERITED.

Where the release publishes a number I re-derived it from the copper rather than repeating it.
**Four of the release's headline numbers reproduce exactly under an independent method**
(`Tj` 107.0795 °C, the 5V_IN segment 26.29 mΩ, the 5V_FUSED segment 7.17 mΩ, and the uniform
board-rise band +1.55…+4.65 °C). That is the strongest evidence in this review, and it is the
reason the verdict is SOUND rather than hedged.

---

## 2. Findings

| finding | sev | evidence (MEASURED, with the command and the number) | disposition |
|---|---|---|---|
| **P1-1 — the declared envelope is justified against the wrong binding part.** `ADR-0029`, `BRIEF.md` D12 and `ORDER_README` §0-T all check the 65 °C declaration against **`F1`'s −40…+85 °C** ("It sits below `F1`'s own −40…+85 °C operating range with room"). The tightest cited operating ceiling on this board is not `F1`'s. It is the **reed relay's `t_op: [-20, 70]`** — **+70 °C**, 15 °C tighter, on **12 populated DO-NOT-SUBSTITUTE parts**. At the declared 65 °C the relay margin is **5.00 °C**, against the **13.3…16.4 °C** the release publishes as the board's thermal margin. The release's own board-rise term (+1.55…+4.65 °C) consumes **31 %…93 %** of that 5.00 °C. | **P1** | MEASURED: `grep t_op 02_parts/DIP05-1A72-13L/part.yaml` → `t_op: [-20, 70]` and `limits: {... t_op: "-20..+70C"}`. Swept ALL 47 part dossiers for temperature ratings — next-tightest are `AQY212GS`, `10FDZ-BT`, `MCP3208-CI-SL`, `TBD62083AFWG`, `TPS3823` all at **+85 °C**; `CD74HC221M96`/`SN74LVC1G123` at +125 °C; `KNTC0603` +125 °C. **+70 °C is the unique minimum.** MEASURED: `grep -n -- "-20\|+70\|t_op\|operating temp" ORDER_README.md` over all 187 kB → **zero hits** naming the relay's rating; `grep` of `ARCHITECTURE.md`/`DETAIL_DESIGN.md` → zero. MEASURED (pcbnew): all 12 `K_*` footprints carry value `DIP05-1A72-13L`, all at `y = 38.000`. | **v1.8 doc item, not a copper item.** Add the relay's −20…+70 °C to §0-T's component-ceiling sentence and to the BRIEF fact-lock row, and state the 5.00 °C margin beside the 13.3…16.4 °C one. **Note the declaration itself is SAFE (65 < 70) and narrowing 75 → 65 is what made it safe** — at the old 75 °C declaration the relay was 5 °C OUTSIDE its cited range. The defect is that the release does not know this is why. |
| **P1-2 — bench gate B5, MANDATORY and new in this very change, instructs a state the hardware cannot produce.** §7b B5 reads *"board copper temperature near `U_LDO`, **all 12 reed coils energised** vs all coils off"*. The coil select path is **two SN74HC238 1-of-8 decoders**. A '238 asserts exactly one output. Maximum simultaneous coils is **4** (1 U-coil + 1 D-coil + `K_PRESS` + `K_STOP`), not 12. **A technician cannot execute B5 as written**, and B5 is the gate that retires the term the release calls "20–59 % of the thermal margin". | **P1** | MEASURED (pcbnew netlist walk): `SEL_U1..SEL_U6` ← `U_DECU.15/.14/.13/.12/.11/.10`; `SEL_D1..SEL_D4` ← `U_DECD.15/.14/.13/.12`; `COIL_PRESS_N` ← `U_ULNB.16` ← `PRESS_TIMED` ← `U_ONESHOT.13`; `COIL_STOP_N` ← `Q_STOPDRV.3`. MEASURED: `grep C5620 fab/bom.csv` → `SN74HC238DR,"U_DECD,U_DECU"`; `02_parts/SN74HC238DR/part.yaml` line 3 → `type: decoder_3to8_active_high  # ... 3-to-8 line decoder/demux, ACTIVE-HIGH outputs`. **The release already contains the contradicting fact**: the `R-POUR` waiver in `03_src/cooksense/rules/policy_waivers.yaml` says all 12 coils is *"the un-reachable absolute ceiling (all 12 coils, which the interlock forbids)"*. Two files, never read together. | **Rewrite B5 before seal** (it is order paperwork, not copper — a documentation edit, zero fab impact). Correct form: *"1 U-coil + 1 D-coil + `K_PRESS` + `K_STOP` energised (the hardware maximum) vs all coils off"*. **AND — see P1-1 — extend B5 to record the temperature at the energised relay body/local board, not only near `U_LDO`.** B5 already creates the exact condition that grades the board's tightest part and currently throws that reading away. |
| **P2-1 — the 0.705 W / "12 reed relay coils" basis of the board-rise term is the same unreachable state.** Root cause of P1-2. The real hardware maximum is 4 coils = **235 mW**, so the board's other dissipation is **0.488 W**, not 0.958 W. | P2 | MEASURED: FD solve on my copper map. At 0.488 W the rise at `U_LDO` is **0.72 / 1.30 / 2.17 °C** at h = 18/10/6, versus the published **1.55 / 2.77 / 4.65 °C**. Traceable to a stale comment: `power_tree.yaml` `linear_rails[5V_KEY_RELAY]` reads `iout_max_A: 0.15  # reed coils ~120mA worst (only 1U+1D+PRESS energised at once)` — **the comment contradicts its own number in the same line** (120 mA is twelve coils; the parenthetical says three). | **ACCEPT as-is for v1.7; fix the comment in v1.8.** The error is in the SAFE direction — it makes the published margin pessimistic by ~2 °C. Do not "fix" it by relaxing anything. |
| **P2-2 — `verification/build_gates.md` line 155 asserts a pour that does not exist**, and cites, as its authority, the waiver that says the opposite. It reads *"the trunk current rides POURS, which `policy_audit`'s evidenced `R-POUR` waiver names for exactly these four nets"*. | P2 | MEASURED (pcbnew zone census): the board has **exactly four filled zones** — `GND` on F.Cu 2701.426 mm², `GND` In1.Cu 8465.524, `3V3` In2.Cu 8420.028, `GND` B.Cu 7385.828. **No 5 V net has a zone on any layer.** The cited `R-POUR` waiver itself says *"The four PWR_IN-class 5V nets … are distributed as TRACKS, not pours"*. `power_tree.yaml`'s ADR-0027 header says *"NO 5 V NET HAS A ZONE ANYWHERE"*. Three sources against one sentence. | **Correct the sentence before seal.** The waiver's real justification (worst continuous draw < 1 A against 1.4 A of 0.5 mm/35 µm ampacity) is correct and sufficient; the sentence substitutes a false one. I re-derived the file's own INHERITED-and-unchecked ampacity numbers and **both reproduce exactly** (see §6) — so the paragraph's arithmetic is right and only its physical claim is wrong. |
| **P2-3 — the published 5 V copper sum is 3.0 % low.** | P2 | MEASURED (my own DC nodal solve, §6): copper sum **141.89 mΩ** vs published **137.79 mΩ**, +4.10 mΩ. The one via-free segment reproduces EXACTLY (26.29), so the delta is entirely a via-barrel-model difference. Costs **~1.1–1.7 mV** of the published **+29.1 mV** dropout headroom (3.8–5.7 % of it). Direction: published is slightly optimistic. | ACCEPT. Does not move the verdict; B3 retires the term that dominates this margin by two orders of magnitude. Record the 3 % in the next dropout pass so it is not rediscovered. |
| **P2-4 — `R-THERM` cannot fail on a thermal question.** The gate reads *"all pads >=4.0mm2 have >=2 nearby same-net vias"*. `U_LDO`'s tab is 7.6000 mm² dissipating 0.4675 W and has **exactly 2** vias. It passes on the same evidence a 0 W pad would. | P2 | MEASURED: tab pad `2.000 × 3.800 = 7.6000 mm²`; vias inside it = **2**, drill 0.150, pad 0.250. `verification/policy_audit.md`: `R-THERM | PASS`. The gate takes no dissipation input, so the board's single hottest part clears the floor with zero margin and the gate says nothing. | **Owed skill patch (`skills/`, outside this board's partition).** Canon says *"test the checkers"* — a gate whose floor is a fixed count cannot grade a thermal claim. Checkable form: `R-THERM` should take `pdiss` from `power_tree.yaml` and require a via count derived from it. |
| **P2-5 — the tab vias are open inside the tab's own solder aperture, and the 8-via recommendation multiplies that by 4.** | P2 | MEASURED: the tab is an SMD pad with layer set `0x2003` = F.Cu + F.Mask + F.Paste, i.e. one solder aperture over the whole 2.000 × 3.800 mm. Both vias sit at (25.150, 68.900) and (25.150, 70.000), **inside** x 24.150…26.150 / y 68.100…71.900. The board's `(tenting (front yes)(back yes))` cannot apply to a via inside a pad aperture. | ACCEPT for v1.7 (2 × 0.15 mm wicks a negligible volume). **The v1.8 work order must specify** via fill/cap (or a windowpane paste aperture) when it goes 2 → 8, or the tab joint starves. |
| **P2-6 — `90 − 18.0 = 72 °C/W` is not a citable figure.** 90 °C/W is ds1117's ABS-MAX **package** bound; −18.0 °C/W is a **model delta for this mounting**. Subtracting one from the other produces a number with no grade. | P2 | The claim itself is sound (§5 — I get −20.5…−21.4 °C/W independently, so −18.0 is conservative) and the +8.4 °C arithmetic is exact (0.46755 W × 18.0 = 8.416 °C). The defect is only the composition. | Present the next-revision item as *"θ_JA on this mounting improves by ≥18 °C/W"* rather than as a new θ_JA value, until B4 measures the baseline. |

---

## 3. DRC — BOTH HALVES, RAW EXIT CODE, UNPIPED

```
kicad-cli pcb drc --severity-all --refill-zones --schematic-parity \
                  --exit-code-violations --format json -o <scratch>/drc_redteam.json \
                  04_kicad/cooksense.kicad_pcb
Found 0 violations
Found 0 unconnected items
Found 0 schematic parity issues
RAW_EXIT=0
```

MEASURED from the JSON I produced: `violations=0  unconnected_items=0  schematic_parity=0`.
**Both halves are zero, and so is parity.** `--exit-code-violations` was passed, so exit 0 is
meaningful rather than the default-zero the canon warns about.

**The nine suppressed checks are ALL non-copper** — MEASURED from `ignored_checks` in my own run:
`missing_courtyard`, `track_not_centered_on_via`, `tuning_profile_track_geometries`,
`footprint_filters_mismatch`, `silk_overlap`, `silk_over_copper`, `silk_edge_clearance`,
`text_thickness`, `footprint_type_mismatch`. **No clearance, width, annular-ring, hole-size or
hole-to-hole check is suppressed.** For this lens the DRC claim carries its full weight. The
suppression is disclosed in §13 of `ORDER_README.md`; I re-enumerated it rather than trusting it.

Nothing to classify. There are no findings in either half to classify.

---

## 4. THE THERMAL CLAIM AT 65 °C — RE-DERIVED FROM THE COPPER, BOTH FORMS

### 4.1 The geometry, measured

| item | MEASURED | how |
|---|---|---|
| `U_LDO` package / position | SOT-223, `(22.000, 70.000)`, rot 0, F.Cu | `pcbnew`, `FindFootprintByReference` |
| tab pad (pad 4, net `3V3`) | **2.000 × 3.800 = 7.6000 mm²**, rect x 24.150…26.150 / y 68.100…71.900 | `pad.GetSize()`, `GetPosition()` |
| vias in the tab pad | **exactly 2**, drill **0.150 mm**, via pad **0.250 mm**, both net `3V3`, through F.Cu→B.Cu, at (25.150, 68.900) and (25.150, 70.000) | swept all vias, point-in-rect against the tab |
| F.Cu `3V3` island around the part | **10.74 mm²** in a 10 × 10 mm window — the two 3V3 pads plus a stub. **There is no top-side 3V3 pour.** | polygon clip of tracks+pads+zones per net per layer |
| plane under the part | In1.Cu `GND` **98.76 mm²** (98.8 % fill), In2.Cu **`3V3` 98.72 mm²** (98.7 %), B.Cu `GND` 98.76 mm², same window | as above |
| tab-attached copper, total | In2.Cu `3V3` zone = **8420.028 mm²** — reached through the 2 vias | zone `GetFilledPolysList().Area()` |

The mounting is therefore: a **7.6 mm² tab pad with no top-side spread**, dropping into an
**8420 mm² same-net inner plane through two 0.15 mm barrels**, over a near-solid GND/GND pair.
`02_parts/AMS1117-3.3/part.yaml` already states the right reading of this — Table 1's smallest
row is 100 mm² of *tab-attached top-side* copper at 80 °C/W, and 7.6 mm² is 13× below it, so
Table 1 does not apply and the ABS-MAX package figure is the honest input. I agree, and I
tested it rather than accepting it.

### 4.2 Is θ_JA = 90 °C/W defensible on THIS mounting? — MEASURED: yes, and it is central-to-slightly-optimistic

My own network, built from the geometry above:

```
theta_JC (SOT-223)                                     15.0  C/W   INHERITED (ds1117 publishes none;
                                                                    typical SOT-223 junction-to-tab)
tab -> plane constriction, TWO PARALLEL PATHS:
  2 x barrel F.Cu->In2, L = 1.29 mm, drill 0.150 mm
     at 25 um plating: 341 K/W each -> 170.6 parallel
     at 18 um (spec floor):  449    ->  224.5 parallel
  dielectric under the 10.74 mm2 F.Cu 3V3 island,
     0.2104 mm prepreg, k = 0.3 W/m.K            ->   65.3
  => 170.6 || 65.3 = 47.2   (25 um)
     224.5 || 65.3 = 50.6   (18 um)
plane -> ambient (MY FD solve, below)             19.0 / 24.4 / 30.4 C/W at h = 18 / 10 / 6
--------------------------------------------------------------------
theta_JA (25 um plating)                          81.2 / 86.6 / 92.6 C/W
```

**90 °C/W sits inside my range and above its midpoint — i.e. central, tipping optimistic at low
h.** That is exactly what the release says (§7b B4: *"90 is central-to-slightly-optimistic, not
conservative"*) and what its cited 81.6…92.3 range says. **Independently confirmed. Not a
finding.** The honest reading — that the ABS-MAX package figure is being used as a *central*
estimate rather than a *bound* — is already stated in the release, in the right words, at the
right place, and B4 is the correct instrument to retire it.

### 4.3 The citable form — reproduces EXACTLY

```
PD_pass = (vin_max 5.250 - vout_min 3.201) x iout_max_A 0.200 = 0.409800 W
PD_q    =  vin_max 5.250 x Iq_max 0.011                       = 0.057750 W
PD                                                            = 0.467550 W
rise    = 0.467550 x 90                                       = 42.0795 C
Tj(65)  = 65 + 42.0795                                        = 107.0795 C
margin  = 125 - 107.0795                                      = 17.9205 C
```
MEASURED by me from `03_src/cooksense/rules/power_tree.yaml`'s own graded keys. **Matches the
published 107.0795 / 17.92 to the last digit.** The `LDO_TJ_DECLARED_AMBIENT` bound regenerates
the same four numbers and asserts the ambient is 65 — a well-formed guard against a silent drift
back to 75.

### 4.4 The board-rise term — the published range is the UNIFORM model, and it is PESSIMISTIC here

**First, I reproduced what the release actually did.** MEASURED: `Q/(2·h·A)` for `Q = 0.958 W`
over the board gives **1.54 / 2.77 / 4.62 °C** at h = 18 / 10 / 6 W/m²K per side (my `A` =
17296 mm²; the published 1.55 / 4.65 implies `A = 17168 mm²`). **The published +1.55…+4.65 °C is
the uniform, perfectly-spread board model.** Confirmed, and it is honestly labelled a MODEL
OUTPUT in both the ADR and §7b.

**Then I tested whether uniform is the right model here — and it is not.** MEASURED, a 2 mm
finite-difference solve over the real copper:

Copper coverage census (2 mm grid, zones + tracks + pads, per layer):

| region | F.Cu | In1.Cu | In2.Cu | B.Cu | sheet conductance `k·t` |
|---|---|---|---|---|---|
| **NORTH, y < 54 mm** (8272 mm², the keypad/relay half) | **10.1 %** | **1.5 %** | **1.5 %** | **2.1 %** | **0.00128 W/K** |
| SOUTH, y ≥ 54 mm (9024 mm²) | 51.3 % | 93.5 % | 93.4 % | 85.7 % | 0.04170 W/K |

**There is no plane of any kind, on any layer, north of y ≈ 54 mm** — 48 % of the board. That is
the keypad-isolated domain, and it is correct that it is bare (the barrier forbids a bond).
**All twelve reed relays sit at `y = 38.000`, in the middle of it**, on copper with **33× lower
lateral conductance** than the planed half.

MEASURED positions and distances from `U_LDO` (22.000, 70.000): `K_U1` (26.000, 38.000) at
**32.25 mm** — the nearest — through `K_STOP` (193.640, 38.000) at **174.6 mm**.

FD result, coil heat 0.705 W + other 0.253 W, **`U_LDO`'s own dissipation excluded** (θ_JA already
carries it):

| h (per side) | uniform model | **rise AT `U_LDO`** | rise at the relay row |
|---|---|---|---|
| 18 | 1.54 °C | **0.91 °C** (0.59×) | 4.37…5.37 °C |
| 10 | 2.77 °C | **1.82 °C** (0.66×) | 6.28…7.68 °C |
| 6 | 4.62 °C | **3.32 °C** (0.72×) | 8.63…10.44 °C |

**Answer to the brief's question 2 — the relay placement makes the board-rise term at `U_LDO`
BETTER than a uniform model implies, by 28…41 %,** because the 0.705 W is deposited ≥32 mm away
in a strip that is thermally decoupled from the plane the tab sinks into. **The published
+1.55…+4.65 °C is therefore PESSIMISTIC for the LDO, not optimistic.** Combined with P2-1's
correction of the coil census (0.488 W, not 0.958 W), the true rise at `U_LDO` is
**0.72 / 1.30 / 2.17 °C**.

### 4.5 The honest margin, my numbers vs the release's

Using MY θ_JA at each h and MY board rise at each h:

| h | release's honest margin | **mine, release coil basis (0.958 W)** | **mine, hardware-real basis (0.488 W)** |
|---|---|---|---|
| 18 | 16.37 °C | 21.12 °C | **21.31 °C** |
| 10 | 15.13 °C | 17.69 °C | **18.21 °C** |
| 6 | **13.27 °C** | **13.39 °C** | **14.54 °C** |

**The release's floor — 13.27 °C — reproduces under my independent model to 0.12 °C.** At every
other corner my number is more generous. **The published 13.3…16.4 °C is defensible and
conservative. It is not optimistic in any direction I can find.** This is the central question
the re-gate was called for, and the answer is that the release got it right.

The one shared assumption to name: my θ_JC = 15 °C/W is INHERITED (ds1117 publishes no θ_JC), and
FR-4 through-plane `k` = 0.3 W/m·K is a standard value, not a citation. Both feed my model and the
release's. **B4 is the only thing that retires them, and §7b already says so.**

---

## 5. THE 12 REED COILS — 0.705 W, AND THE PLACEMENT

**The number.** MEASURED from `02_parts/DIP05-1A72-13L/part.yaml`: coil `500 Ω ±10 %` at 20 °C,
`5.0 V` nominal, `coil_p_nom_mW: 50`, tempco `0.4 %/K`. Independent bounds:

```
nominal, 5.000 V across 500 R                       = 50.0 mW/coil -> 0.600 W for 12
worst case, rail vin_max 5.250 - driver 0.046 V
  across R_min 450 R (-10 %, at 20 C)               = 60.2 mW/coil -> 0.722 W for 12
the release's figure, 0.705 / 12                    = 58.75 mW/coil
```
**0.705 W is a defensible worst-case-ish figure**, 17 % above nominal and 2 % below my worst
bound. **The per-coil number is fine. The count is not** — see P1-2 / P2-1: two SN74HC238 1-of-8
decoders cap the simultaneous count at **4**, so the reachable coil dissipation is **235 mW**.

**The placement, judged.** Two opposite answers, and they must not be averaged:

* **For `U_LDO` the placement is FAVOURABLE.** The coils are 32.2…174.6 mm away, in a strip whose
  sheet conductance is 33× lower than the LDO's. MEASURED: the rise they deliver at the LDO is
  0.59×…0.72× the uniform model. **Better than the release assumes.**
* **For the relays themselves the placement is UNFAVOURABLE, and nothing in the release grades
  it.** MEASURED, FD: even at the hardware maximum of 4 coils, the hottest energised relay's local
  board sits **+5.25…+9.87 °C** above ambient (h = 18…6); a single energised coil gives
  +3.80…+6.51 °C. Independently, the package-convection bound for 58.75 mW into the DIP's
  388.7 mm² of exposed surface (19.3 × 6.5 × 5.1 mm, from the part dossier) at h_eff ≈ 15 W/m²K
  is **+10.1 °C**. **These are the parts with the +70 °C ceiling, sitting at a declared 65 °C
  ambient.** That is P1-1.

  **This is not a P0**, and the reason is worth stating so it is not lost: reed coils here are
  **pulsed, not continuous** — one U-coil and one D-coil during a keypress, with `K_PRESS` under a
  non-retriggerable one-shot. A 5 mm package's thermal time constant is minutes; a keypress is
  milliseconds. At realistic duty the relay's ambient is 65 °C plus the background rise from the
  other 0.253 W only (≈ +0.5…+1.5 °C), leaving **3.5…4.5 °C**. Thin, positive, and **never
  computed anywhere in the release.**

---

## 6. THE 5 V DELIVERY PATH — DOES THE PUBLISHED SERIES SUM MATCH THE COPPER?

**MEASURED by me**, an independent DC nodal solve: every track segment an edge
`R = ρ·L/(w·t)`, every via a plated barrel, every pad a node (endpoints inside a pad merged by
union-find), the eFuse's two IN pads (3, 4) bridged as the package bonds them, then `G·v = i`
solved by Gaussian elimination. Corner matched to the file's: ρ = 1.72e-8 × (1 + 3.93e-3 × 55) =
2.0918e-8 Ω·m at 75 °C, outer copper 35 µm, plating 18 µm (the spec floor).

| segment | **MEASURED (me)** | published | Δ |
|---|---|---|---|
| `5V_IN` `J_PWR.1` → `F1.1` (0 vias) | **26.29 mΩ** | 26.29 | **exact** |
| `5V_FUSED` `F1.2` → `Q_REV.3` | **7.17 mΩ** | 7.17 | **exact** |
| `5V_RPP` `Q_REV.2` → `U_EFUSE.3` | 25.44 mΩ | 24.07 | +1.37 (+5.7 %) |
| `5V_PROTECTED` `U_EFUSE.5` → `U_LDO.3` | 82.98 mΩ | 80.25 | +2.73 (+3.4 %) |
| **COPPER SUM** | **141.89 mΩ** | 137.79 | **+4.10 (+3.0 %)** |

**The two via-free comparisons are exact and the two with vias are not**, so the entire delta is a
via-barrel-length model difference, not a routing or width disagreement. MEASURED: the 5 V nets
live **only** on F.Cu (284.33 mm) and B.Cu (35.18 mm) — **zero inner-layer 5 V track** — so inner
copper thickness is not an input at all (re-run at 17.5 µm and 35 µm: byte-identical results).
That also independently confirms `power_tree.yaml`'s ADR-0027 claim that the tracks are the entire
conductor.

Cost: 4.10 mΩ × ~0.40 A ≈ **1.1–1.7 mV** of the published **+29.1 mV** headroom → **P2-3**,
not a verdict-mover. B3 (a 0.8 A dropout figure applied to a 0.2 A rail) dominates this by two
orders of magnitude, and §7b already says so in those words.

**Ampacity, MEASURED** (min widths from pcbnew; IPC-2221 external, 35 µm, 10 °C rise):

| net | min width | I(10 °C) | headroom vs 0.4024 A |
|---|---|---|---|
| `5V_IN` / `5V_FUSED` / `5V_STOP` | 0.500 mm | 1.45 A | 3.6× |
| `5V_PROTECTED` | 0.450 mm | 1.34 A | 3.3× |
| `5V_KEY_RELAY` | 0.400 mm | 1.23 A | 3.1× |
| `5V_RPP` | 0.250 mm (scoped eFuse pad entry only) | 0.88 A | 2.2× |
| `3V3` | 0.300 mm | 1.00 A | 2.5× |

I also re-derived the two numbers `build_gates.md` explicitly flags as INHERITED-and-unchecked:
**+0.9 °C at 0.5 A and +16.2 °C at 1.79 A both reproduce exactly** under IPC-2221 external for
0.5 mm / 35 µm. Those inherited figures are correct; only the sentence around them (P2-2) is not.

**Hot loops / switch node: there is none.** MEASURED: the only zones are GND and 3V3; `U_LDO` is
the only regulator; the board is all-linear, so no SW-node or loop-area budget applies. The
inductive loops are the coils, and MEASURED both `U_ULNA` and `U_ULNB` carry `5V_KEY_RELAY` on a
pad — the TBD62083 COM clamp is on the coil rail, at the driver, as the relay datasheet demands.
Coil loops are long (`K_U1` at x = 26.0 driven from `U_ULNA` at x = 95.0, ≈ 72 mm) but at 10 mA DC
into a clamped coil that is not a loop-area question.

**LDO decoupling adjacency, MEASURED:** `C_LDOOUT` (22 µF, the frequency-compensation cap the
`keep_short` budget actually names) is **2.900 mm** from the VOUT pad against a 5 mm budget;
`C_LDOIN` (10 µF) is **3.008 mm** from VIN against 8 mm. Both compliant. The `P-ADJ` waiver's
5.89 mm finding is measured to `C_3V3`, the 100 nF (I get 5.759 mm) — the gate graded a cap the
budget does not name. The waiver is sound.

---

## 7. THE KEYPAD ISOLATION BARRIER — I-ISO ≥ 6.000 mm

**MEASURED by an independent method** (canon M1: checker and checked must not share a method). I
did not read the DRC report for this. I built, per layer, the polygon set of all `KEYPAD_ISO`
copper (14 nets: `D_SEL_BUS`, `KP_U1..U6`, `KP_D1..D4`, `RKEY_MID`, `RSTOP_MID`, `U_SEL_BUS`) and
of all other copper — tracks, pads and zones, NPTH excluded as non-conductors — then bisected an
inflation radius to 2⁻²⁴ mm to find the true minimum gap:

| layer | **MEASURED min gap** | between |
|---|---|---|
| F.Cu | **6.3100 mm** | `D_SEL_BUS` track ↔ `K_U6.1` (`5V_KEY_RELAY`) |
| In1.Cu | **6.3492 mm** | `K_D3.4` (`D_SEL_BUS`) ↔ `K_D3.1` (`5V_KEY_RELAY`) |
| In2.Cu | **6.3492 mm** | same pair |
| B.Cu | **6.3492 mm** | same pair |

**The ≥ 6.000 mm claim HOLDS on all four layers, track-aware, with 0.310 mm to spare.** The
binding gap is the relay's own coil-to-contact column split, which is the geometry ADR-0002 and
the pin-out-code-13 part change were bought to obtain — so the barrier is set by the part, not by
a routing accident, which is the right place for it to be set.

The DRU's one exemption is real and finite: with `J_KEY_MATRIX.MP` included the F.Cu figure falls
to **0.9916 mm** (MEASURED). MEASURED: `J_KEY_MATRIX`'s shell tabs are the board's only unnetted
copper and it is the only connector on the isolated side, so bonding them would short the domain.
The exemption is enumerated by refdes rather than by `B.NetName != ''`, which is the difference
between an evidenced waiver and a blanket one. **Correct.**

Mounting-hole creepage: MEASURED, `KEYPAD_ISO` copper comes within **3.44…3.46 mm** of `H1`'s hole
edge (H1–H4 are NPTH `2.7 mm`, no annular, at (24, 14) / (194, 14) / (17, 90) / (193, 52) — two of
them inside the isolated domain). This is **already governed** by ADR-0012, which models the
hardware as a conductor and grades a per-hole `a + s` pairing sum (H1 15.936 mm, H2 16.129 mm,
both PASS). INHERITED, consistent with my measurement, no new finding.

---

## 8. THE `pdiss_max_mw` RATCHET (ADR-0029 Decision 4) — JUDGED, AND ENDORSED

MEASURED arithmetic, both derations:
```
75 C (held):  (125 - 75)/90 x 1000 - 5.250 x 11 = 555.556 - 57.75 = 497.806  -> 497  (the file)
65 C (correct at the new declaration): (125 - 65)/90 x 1000 - 57.75 = 608.917 -> 608
PD 409.800 mW  ->  82.45 % of 497   /   67.30 % of 608.   E-TOPO PASSES either way.
```

**Holding 497 is correct and I endorse it without qualification.** 497 < 608.917, so the gate
continues to enforce `Tj ≤ 125 °C` at the **SURVIVE** corner while the declaration sits at the
**operating** corner — strictly stronger than enforcing it where the product is declared. Nothing
is rescued by moving it (the gate was never red), so the only thing the move would buy is a looser
ceiling on a board whose envelope was just narrowed. That is precisely the mechanism a ratchet
exists to refuse, and the ADR says so in the words a future editor will need. The consequence —
a 75 °C derating sitting beside a 65 °C declaration — is stated out loud at the key rather than
left to be discovered. **This is the best-argued decision in the change.**

**One qualification, and it is P1-1 again.** "Survive at 75 °C" is evidenced **for the LDO only**.
At 75 °C the twelve reed relays are 5 °C outside their cited `-20..+70 °C` operating range, and
`02_parts/DIP05-1A72-13L/part.yaml` cites **no storage or non-operating rating at all** (MEASURED:
the dossier's only temperature fields are `t_op: [-20, 70]` and the coil tempco). So the SURVIVE
corner is an LDO property being carried as a board property. Say so, or cite the relay's storage
range.

---

## 9. THE 2 → 8 TAB-VIA RECOMMENDATION — CHECKED AGAINST THE ACTUAL PAD

**Geometrically and DRC feasible — MEASURED.** Eight 0.250 mm via pads on 0.150 mm drills fit the
2.000 × 3.800 mm tab as 2 columns × 4 rows at 1.000 mm x-pitch / 1.100 mm y-pitch: 0.375 mm side
margin, 0.125 mm end margin, hole edge-to-edge **0.850 mm** against the project's
`min_hole_to_hole` **0.250 mm** (MEASURED from `cooksense.kicad_pro`), and both
`min_via_diameter` 0.25 and `min_via_annular_width` 0.05 are already met by the two existing vias.
**No rule blocks it.**

**Thermally the −18.0 °C/W claim is CONSERVATIVE — MEASURED.** Same network as §4.2, only the via
count changes:

```
                        2 vias            8 vias          delta
25 um plating    170.6 || 65.3 = 47.2   42.6 || 65.3 = 25.8   -21.4 C/W
18 um plating    224.5 || 65.3 = 50.6   56.1 || 65.3 = 30.1   -20.5 C/W
```
**My independent range is −20.5…−21.4 °C/W; the release claims −18.0.** The claim understates its
own benefit by 12–16 %, which is the correct direction for a recommendation. **+8.4 °C is exact**:
0.467550 W × 18.0 °C/W = **8.416 °C**. **The claim is right. It is not a finding.** Two riders,
both P2: the composition `90 − 18 = 72` is not citable (P2-6), and the eight vias must be
specified filled/capped or the tab joint starves (P2-5).

---

## 10. VERDICTS

**`design_verdict: SOUND`.** The copper is unchanged, DRC is 0/0/0 in both halves with no copper
check suppressed, the ≥ 6.000 mm isolation barrier holds on all four layers under an independent
method, the 5 V series sum reproduces to 3 %, ampacity has ≥ 2.2× on every power net, and — the
question this re-gate exists for — **the thermal claim at 65 °C survives an independent
re-derivation from the copper in both its forms.** θ_JA = 90 °C/W is defensible on this mounting
(my network: 81.2…92.6 °C/W). `Tj = 107.0795 °C` and the 17.92 °C citable margin reproduce
exactly. The honest 13.3…16.4 °C band reproduces at its floor to 0.12 °C and is **conservative**
at every other corner, because the relay placement decouples the coil heat from the LDO's plane
by ~30–40 % relative to the uniform model the release used, and because the reachable coil count
is 4 rather than 12. **The two P1s are defects in the JUSTIFICATION and in one bench instruction,
not in the artifact.** Neither makes the board wrong to fabricate; both should be fixed before
seal because §7b is order paperwork and costs nothing to correct.

**`order_verdict: BLOCKED-SOURCING`.** One BOM line, `C265111` (JST SM08B-GHS-TB, `J_THERM_A` /
`J_THERM_B`), reads stock 5 against **minPurchaseNum 21** — unbuyable at any quantity today
(MEASURED, provided to me as measured; `A-STOCK` raw exit 1 in `build_gates.md`). That is a
sourcing state, not a design state, and it has **not** been allowed to touch `design_verdict`.
I found **no other order-side objection in this lens**: the fab payload, the 12 milled isolation
slots, the ampacity and the thermal envelope are all orderable as they stand.

---

```
design_verdict: SOUND
order_verdict:  BLOCKED-SOURCING
```

**P0: 0.**
**P1-1** — the 65 °C envelope is justified against `F1`'s +85 °C ceiling; the binding part is the
reed relay at **+70 °C** (5.00 °C of margin, on 12 populated DO-NOT-SUBSTITUTE parts), named
nowhere in the release.
**P1-2** — mandatory bench gate B5 instructs *"all 12 reed coils energised"*, which two
SN74HC238 1-of-8 decoders make impossible (max 4); the release's own `R-POUR` waiver already
says that state is unreachable.
