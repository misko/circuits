# brief: pluto-rx2-8way-v2

status: in-progress
prompt_sha256: 1182e2cf4dfc80dd72ec1463cd5ef6e48a43088a7cb3ea4fbb8639b894f69301
current_release: no

## Original prompt

<!-- prompt-verbatim-begin -->
please try a new board , pluto-rx2-8way-v2 with the pico class module
<!-- prompt-verbatim-end -->

- date: 2026-07-30
- channel: Claude Code session (commissioning message relayed verbatim in the
  agent brief)

`prompt_sha256` reproduces with the runnable command in `01_docs/contracts.md`
("Validate — BRIEF.md"). **That command is deliberately NOT quoted here**: its
own literal marker text would match `sed`'s range pattern and restart the range,
so a BRIEF that quotes its own check can never pass it. Verified 2026-07-30 —
quoting it produced `dda04c78...` against a recorded `1182e2cf...`, and deleting
the quotation made the two agree.

## What this board IS, and what it is not

`pluto-rx2-8way-v2` is an **experiment against a named alternative**, not a
successor. `projects/pluto-rx2-8way` (v1) is **NOT superseded** and must not be
written to: it stays as the bare-RP2040 arm of a two-arm comparison. v2 changes
exactly one thing — the MCU becomes a **pre-built Pico-class RP2040 module** —
and holds every RF decision of v1 fixed so the two boards differ in one variable.

### The measurement that motivates it (MEASURED by me on v1, 2026-07-30)

A `pcbnew` walk of v1's `U_MCU` (QFN-56, LCSC `C2040`) counts **19 named nets on
its pads**. Exactly **5** of them are the board's function:

| the board's function (5) | the chip keeping itself alive (14) |
|---|---|
| `SEL_V1` `SEL_V2` `SEL_V3` `SEL_V4` `LED_STAT` | `QSPI_SCLK` `QSPI_CSN` `QSPI_SD0..SD3` (6) · `XIN` `XOUT` (2) · `USB_DM_MCU` `USB_DP_MCU` (2) · `RUN_N` · `DVDD_1V1` · `3V3` · `GND` |

26 further pads carry `unconnected-(...)` auto-nets. **74% of the escape demand
on the hardest package on the board buys nothing the board sells.** A module
moves flash, crystal, USB, reset and the 1V1 core rail off-board and leaves an
interface of ~5 signals on a coarse castellated pitch.

This is **Ossmann's rule 2** — *"use the most integrated components you can
find"* — which `skills/kicad-pcb/references/rf-design.md` section 1 already
quotes as canon and which v1 did not follow.

## End goal — definition of done

The same instrument as v1 — one of eight antennas onto PlutoPlus RX2 under
free-running parallel control, element 8 shared with RX1 through a resistive
pickoff, with a published per-path phase/loss table — built around a Pico-class
RP2040 **module** instead of a bare RP2040, so that the escape problem which
dominates v1's MCU field is removed by PART SELECTION rather than by routing
effort. Done when the board is orderable and assembled at the declared tier and
the two arms can be compared.

| # | Criterion | Source | Status |
|---|---|---|---|
| G1 | 8 antennas selectable onto RX2, one at a time | P (v1 P1, inherited) | unmet |
| G2 | element 8 is a tap of the RX1 antenna; RX1 keeps its own path (2x220R split-arm pickoff) | P (v1 P2) | unmet |
| G3 | switching is sequenced, not operator-driven | P (v1 P3) | unmet |
| G4 | dwell 8192 on each element, 4096 at the reference, 128 blank | P (v1 P4/D1) | unmet |
| G5 | one 499,712-sample buffer holds exactly 8 sweeps at 30 Msps | P (v1 P5) | unmet |
| G6 | every antenna has an SMA connector (10 jacks total) | P (v1 P6) | unmet |
| G7 | per-path phase/loss deltas CONSTANT and PUBLISHED | P (v1 P8) | unmet |
| **G8** | **the MCU is a Pico-class RP2040 module, not a bare RP2040** | **P (this prompt)** | unmet |
| **G9** | **the module contributes no NEW continuous in-band spur source to the receiver** | **A2** | unmet — settled at D-SPEC, see T1 |
| **G10** | **the module's assembly posture is a RECORDED DECISION, not a discovered outcome** | **A3** | unmet — see T2 |
| G11 | orderable + assembled at the declared tier | D-TIER | unmet |

## Spec tensions (D-SPEC) — flagged to the user, NOT silently resolved

| # | Requirement | Standard / parts cap it collides with | Resolution (ADR) | User flagged |
|---|---|---|---|---|
| **T1** | *"the pico class module"* on a board whose deliverable is a RADIO property | A Raspberry Pi **Pico** carries an **RT6150 buck-boost SMPS** whose PS pin (GPIO23) defaults to **PFM — a variable, load-dependent switching frequency**. A moving spur cannot be planned around. v1's own ARCHITECTURE names QSPI as *"the board's only continuous in-band spur source"*; adding a second, VARIABLE one to remove a routing problem is a trade that must be SETTLED WITH EVIDENCE, not assumed either way | `decisions/0001-*` | **yes** |
| **T2** | Every footprint machine-placed (SKILL.md's opening rule: PCBA is the deliverable) vs. a module that may not exist in JLC's SMT catalog | An uncoded line left on the CPL is a canon **A-POP** defect (cooksense v1.1 sealed 13). If no Pico-class module is machine-placeable, the module becomes an `assembly.yaml` entry with a closed-vocabulary `reason:` and dated `evidence:` — a DECISION with a record, never a discovered outcome | `decisions/0002-*` | **yes** |
| **T3** | The module's own USB connector vs v1's own USB-C | Two USB ports on one board is a decision, not an accident | `decisions/0002-*` | **yes** |
| **T4** | The via-fence pitch inherited as `lambda_g/20 = 1.37 mm` from "eps_eff 3.328" | **The fleet publishes THREE disagreeing constant sets for ONE stackup.** v1's `nets.yaml` phase block and `rf-design.md` 4(d) both say eps_eff **3.350** / t_pd 6.105 / lambda_g 27.29 / 13.19 deg-per-mm; v1's SAME FILE line 74 says lambda_g **27.41 mm** (implies 3.3229); my own Hammerstad-Jensen derivation at the declared stackup gives **3.3286** / 6.0857 / **27.387** / 13.145. Only the last is reproducible from the declared stackup. This is the rf-design 4(d) defect occurring INSIDE one board | `decisions/0003-*` | **yes** |

## Commission fact-lock

Rows marked **inherited-MEASURED** were carried from v1 by the commissioning
brief and RE-MEASURED by me today against v1's artifacts; rows marked
**inherited-UNVERIFIED** are v1's own user-confirmed commission facts, carried
forward and NOT re-derived here (v2 does not reopen them).

| row | value | grade / locked by |
|---|---|---|
| RF band | 70 MHz - 6 GHz | inherited-UNVERIFIED (v1 A2, user) |
| Ports | 8x SMA antenna + RX1-out + RX2-out = 10 jacks | inherited-UNVERIFIED (v1 P6, user) |
| Switch | PE42482A-X SP8T at a radial-star centre | inherited-UNVERIFIED (v1) |
| Antenna 8 | IS the RX1 antenna, via the 2x220R resistive pickoff | inherited-UNVERIFIED (v1 A6, user) |
| Dwell scheme | 8192 / 4096 clean + 128 blank, free-running PIO 3-bit sequencer | inherited-UNVERIFIED (v1 D1/A4) |
| Control interface | parallel 3-bit + LE, **never SPI** (SPI latency exceeds the whole blanking budget) | inherited-UNVERIFIED (v1 DERIVED) |
| Stackup / tier | `JLC04161H-7628` 4-layer at **`jlc_4layer_advanced`**, impedance-controlled | inherited-UNVERIFIED (v1 ADR-0003); **re-confirmed as still forced** — PE42482A-X QFN-24 at 0.50 mm pitch, standard-tier 0.30 mm drill leaves 0.20 mm hole-to-hole against a 0.50 mm floor. `min_via_diameter: 0.25` at this tier is **MEASURED by me** from `fab_tiers.yaml` |
| Reference plane | **In1.Cu is the SOLID UNBROKEN RF REFERENCE and is EXCLUDED from the routing layers.** RF on F.Cu only, no vias inside an arm | inherited-UNVERIFIED (v1 ADR-0006/0007); this is Ossmann rule 1 and is what makes nine phases comparable |
| Via fence | ground-via fence at **guided lambda_g/20**, from THIS board's own eps_eff — never free-space, never bulk eps_r | **MEASURED by me**: eps_eff 3.3286 -> lambda_g(6 GHz) 27.387 mm -> **1.3693 mm**. See T4 for the three-way disagreement this exposes |
| Length tolerance | governed by **DRIFT** (`d_tau = TC*dT*dL*t_pd`), NOT static mismatch. PE42482A-X's own part-to-part relative-phase window is **13.2 deg = 1.00 mm** of copper; a tighter obligation is not physics | inherited-UNVERIFIED (v1 ADR-0006(b)); v1's standing "+/-0.10 mm" was 1.3 deg and was WITHDRAWN as unreachable by any router and unheld by any process — v2 does not re-adopt it (A5) |
| Input rail | USB 5 V nominal, **4.75 - 5.25 V** device-end | inherited-UNVERIFIED (v1 D-SPEC) |
| Output rail | **3V3, 3.20 - 3.40 V** at the switch Vdd, ~0.15 A envelope | A1 — mirrored in `03_src/rules/power_tree.yaml`; the SOURCE of this rail is the T1 decision |
| Protection posture | inherited from v1 ADR-0004 and **re-opened by the module**: the module carries its own USB and its own regulator, so v1's PPTC -> TVS -> ferrite -> LDO chain may now sit on the wrong side of the boundary | A4 — `decisions/0002-*` |
| Off-control / source | bus-powered, de-energized by unplugging; `quiescent_ua: 0` — **E-OFF N-A, stated rather than inferred from silence** | inherited-UNVERIFIED (v1 ADR-0004) |
| Module choice + regulator topology | **the T1 decision** | `decisions/0001-*`, live evidence |
| Module assembly posture | **the T2 decision** | `decisions/0002-*`, live JLC stock read |

## Mating fact-lock (D-MATE)

**This board mates to nothing foreign, on the same reasoning v1 recorded.** All
Pluto-facing interfaces are SMA male-male cables, which absorb the mechanical
interface entirely — the conclusion `pluto-cal-switch` reached the expensive way
(ADR-0005: an SMA span read 35.60 mm off an undimensioned plot with three
extractions agreeing to 0.003 mm, and a caliper on two physical units read 35.04
and 34.72). **No `03_src/rules/mates.yaml` is carried**, deliberately: an empty
one fails `import_provenance_check.py` as M-COVER. Silence is not a declaration,
so this paragraph is the declaration.

**The module is explicitly considered and explicitly NOT a D-MATE subject.** It
is soldered to this board as a COMPONENT — its outline, castellation pitch and
pin count are a LAND PATTERN, and a land pattern's home is
`02_parts/<MPN>/part.yaml` with a CITED vendor drawing, graded by S-VER and
P-ESC. `spf/<device>/` exists for hardware the board mates WITH as a system, not
for parts it reflows. **If the chosen module's dimensions ever have to come off a
caliper or a photograph instead of a vendor drawing, that reclassifies them as
ESTIMATED and D-MATE reopens** — recorded here so a successor does not have to
re-reason it.

## Receiver configuration this design DEPENDS on (inherited from v1; firmware/host)

Carried in intent from v1: the 128-sample blanking allowance is only valid if the
host configures RX2 as **MGC not AGC**, **RX FIR bypassed or short**, and
**DC-offset / quadrature tracking FROZEN**. These are DESIGN INPUTS, not
preferences. INHERITED from v1, not re-derived here.

## Log

### A1 — 2026-07-30 — assumption (not asked; user absent)
Assumed: the 3V3 rail feeding the PE42482A-X keeps v1's **3.20 - 3.40 V @
0.15 A** envelope. Authority: v1's own D-SPEC lock, unchanged by the MCU swap —
the switch is the same part with the same Vdd requirement.
Escalate if: the chosen module's 3V3 output cannot hold that window under the
switch's load, or its regulator is on the wrong side of the T1 decision.

### A2 — 2026-07-30 — assumption (not asked; user absent)
Assumed: **G9 — the module must contribute no NEW *continuous* in-band spur
source.** Authority: the commissioning brief names this as the decisive
constraint and says it "may kill the idea", and the user is absent. The
conservative reading is that a board whose product is a radio measurement does
not knowingly acquire a second, VARIABLE-FREQUENCY emitter to save routing
effort. Note the word *continuous*: v1 already accepts QSPI, which is continuous
but FIXED, so the bar is "no worse in kind", not "silent".
Escalate if: the only sourceable module is a switcher-regulated one — that turns
G9 from a design constraint into a user trade-off, and the user decides.

### A3 — 2026-07-30 — assumption (not asked; user absent)
Assumed: **G10 — the assembly posture is decided at commission from a LIVE stock
read, and a not-machine-placeable module is acceptable ONLY as an
`assembly.yaml` entry with a closed-vocabulary `reason:` and dated
`evidence:`.** Authority: SKILL.md's opening rule ("an unpopulated part is a
DEFECT WITH A DECISION RECORD, never a free outcome") plus canon A-POP.
Escalate if: accepting it would require the whole fleet's PCBA posture to change.

### A4 — 2026-07-30 — assumption (not asked; user absent)
Assumed: v1's input-protection ADR is **re-opened, not inherited**. Authority:
canon M4 — *"a waiver copied from another board is not a judgement, it is an
inherited defect"* — and the same applies to a protection posture. The module
relocates the USB entry point and the regulator, which is exactly the boundary
v1's PPTC -> TVS -> ferrite -> LDO chain was drawn around.
Escalate if: the module's own protection turns out to be part of the answer —
that is a claim needing the vendor schematic, not an assumption.

### A5 — 2026-07-30 — assumption (not asked; user absent)
Assumed: **v2 does NOT re-adopt v1's withdrawn "+/-0.10 mm" length obligation.**
Authority: v1 measured it at 1.3 deg against the part's own 13.2 deg
part-to-part window and withdrew it as unreachable by any router and unheld by
any process. Re-adopting a withdrawn obligation on a new board is exactly the
inherited-defect pattern canon M4 names.
Escalate if: the user wants the tighter number for a reason v1 did not record.

### A6 — 2026-07-30 — assumption (not asked; user absent) — THE CONSTANT SET
Assumed: v2 derives its OWN microstrip constant set ONCE, from the declared
stackup, and every ADR cites the derived values rather than a re-typed copy
(rf-design 4(d), canon M-BOUND). Where v2's derivation disagrees with a number
inherited from v1 or from the canon, **v2 uses its own derivation and says so**.
Authority: rf-design.md section 5 — *"Declare the stackup ONCE and derive
eps_eff / t_pd / lambda_g from it"*.
Escalate if: someone can show which measurement 3.350 came from. It is not
reproducible from the stackup v1 declares, and if it has a provenance the canon
should carry it.

## Decision register

| id | decision (one line) | decided by | depth |
|---|---|---|---|
| ADR-0001 | which module, and its regulator topology vs the RF spur constraint (T1/G9) | agent (A2, P-delegation) | `decisions/0001-module-selection-and-the-rf-spur-question.md` |
| ADR-0002 | module assembly posture, protection boundary, and the second-USB question (T2/T3/G10) | agent (A3/A4) | `decisions/0002-assembly-posture-and-the-power-entry-boundary.md` |
| ADR-0003 | v2 derives its own microstrip constant set; the fleet's three sets disagree (T4) | agent (A6) | `decisions/0003-one-stackup-one-constant-set.md` |
