# journal — stage 4/5, pluto-rx2-8way-v2

## 2026-07-30 — START: the footprint was OWED, and the cross-check found two defects

Entered at the declared handoff boundary with the schematic gate green and
three things OWED: the `RP2040_Zero_LCC23_18x23.5` footprint, `floorplan.yaml`
+ `route.yaml`, and the vendor PDFs. Before drawing anything I went looking for
the independent module read the previous agent had launched and not received.

**IT WAS WAITING**, in this session's scratchpad: vendor schematic PDF, the
dimension drawing, the vendor pinout figure, and — the artifact that decides
everything below — **the Waveshare Creo STEP assembly**. A full second dossier
(`DOSSIER-part.yaml`, 756 lines, artifacts sha256'd) arrived mid-stage.

Canon M1 says checker and checked must not share a method. Two reads of one pad
map is a free instance of it, and it earned its keep twice.

### FINDING 1 — the numbering was INVENTED, and it is the EXACT REVERSE of the vendor's

The schematic gate closed on a numbering this project authored: a
counter-clockwise perimeter walk from the top-left, `1=5V … 23=GP0`, on the
stated premise that *"Waveshare labels the pads by FUNCTION and does not number
them."*

**That premise is false.** Waveshare numbers them, twice:

* the schematic's `Pin Out` sheet draws the 23 castellations as connector **P1,
  "Header 23"**, pins numbered 1..23: `1=GPIO0 … 16=GPIO15, 17=GPIO26,
  18=GPIO27, 19=GPIO28, 20=GPIO29, 21=3V3, 22=GND, 23=VSYS`;
* the wiki FAQ prose independently calls VSYS **"Pin23"** and 3V3 **"Pin 21"**.

The vendor walk runs **CLOCKWISE FROM THE TOP-RIGHT** — the mirror of every IC.
Ours ran counter-clockwise from the top-left. The two are the **exact reversal**:
`ours_n = 24 - vendor_n`, verified on all 23 pads, no exceptions.

That is the worst available collision. Every number is valid in both systems and
names a different pad, so a reviewer, a revision author or a bench debugger who
reaches for the vendor's number — the obvious source — gets a board that is a
perfect mirror image, assembles, powers up, and reads every GPIO on the wrong
pad. The part's own `gotchas:` block named this exact failure class as the
reason `jlc_twin` exists. It was a live instance, not a hypothetical.

**WITHDRAWN. The vendor numbering is adopted**, at the source: `part.yaml`, the
`.tsx` `pinLabels` + `connections`, and the tscircuit footprint pad indices.

A second trap the dossier names and I confirm: **the silkscreen prints GPIO
numbers, not pad numbers, and they agree for SIXTEEN CONSECUTIVE PADS** (1..16 =
GP0..GP15) before diverging at pad 17. Sixteen agreements is exactly long enough
to convince a reviewer the mapping is the identity.

**WHAT SURVIVED BOTH READS UNCHANGED:** the PHYSICAL map — which function sits
at which position. Four artifacts agree (drawing silkscreen, schematic P1 order,
vendor pinout figure, STEP): left edge top→bottom `5V GND 3V3 29 28 27 26 15 14`,
bottom left→right `13 12 11 10 9`, right edge bottom→top `8 7 6 5 4 3 2 1 0`.
The previous agent's read of the *board* was right; only its *numbering* was
invented.

### FINDING 2 — the module is NOT FLAT-BACKED, and that overturns the assembly posture

MEASURED off the vendor STEP, independently by me and by the dossier, agreeing to
the digit: **23 components sit on the module's CARRIER-FACING face** — 12 MHz
crystal **1.000 mm proud**, RP2040 QFN-56 0.850, RT9013 LDO 0.700, twenty 0201s
0.300. The 23 castellation lands are 0.010 mm of copper on that *same face*, so
**the joint plane and the collision plane are the same plane** and the part
cannot sit down. No reflow bridges a 1.0 mm standoff at 2.54 mm pitch; there is
no pick-and-place nozzle target and no inspectable joint.

The tree carried `consigned: [U_MCU]` — JLC places a module we ship them — and
the commission agent had explicitly refused hand-solder as *"a fake sourcing
wall"* because that rung looked open. **The rung is not open; it is blocked by
physics, and the commission agent did not have this fact.** Note the shape of the
error: `part.yaml` and `ARCHITECTURE.md` both said the module *"stands on
castellations with components on its top face"* — wrong about the face that
matters, and unfalsifiable from a photo of the top.

`03_src/rules/assembly.yaml` is now `not_assembled: [U_MCU]`,
`reason: user_supplied`, `on_bom: false`, with the **mechanical** evidence
first and two independently-sufficient seconds recorded (thermal: a populated
FR-4 PCBA with no MSL and no second-reflow profile, its own bottom-side joints
facing down through the oven; sourcing: C9900173620 now additionally flagged
*"no longer manufactured"*, C5350143 marked *"SMT Assembly (Fixture Required)"*).
The distinction is written down deliberately — *"we preferred to hand-solder"*
and *"no reflowable joint exists"* are different claims and only one is true.

`msl:` is still **not invented**. Under hand-solder the module never enters
JLC's oven, so no bake and no desiccant is owed; asserting a level we made up
would put a fabricated moisture obligation into a release.

### The footprint, authored twice

I drew it once to my own derivation (2.20 × 1.50, straddle 1.10/1.10) and threw
that away when the dossier landed. The dossier's land is **2.60 × 1.20,
straddling the module edge 1.00 outboard / 1.60 inboard**, and its derivation is
strictly better: the inboard 1.60 must reach past the **castellation hole centre
at 1.38 mm** so the barrel wets over its full exposed height. My 1.10 mm inboard
does not reach it. That 1.38 is the drawing's one unlabelled dimension — I could
not resolve its datum; the dossier resolved it by photogrammetry and grades it
honestly as an ESTIMATED datum on a CITED number. The outboard 1.00 mm tail is
not decoration: the fillet outside the module outline is the **only inspectable
feature of a castellated joint**.

**ONE DEPARTURE FROM THE DOSSIER, AND IT IS THIS BOARD'S CALL, NOT A CORRECTION.**
The dossier specifies paste on the inboard 1.60 mm only. This footprint carries
**no `F.Paste` apertures at all**, because on *this* board the part is not on the
CPL: paste printed under a part that is never placed reflows into solder balls,
and JLC cuts the stencil from the paste gerber. The dossier's aperture spec is
recorded in the footprint `descr` for anyone who ever adopts a reflow posture.

**THE GRID IS SELF-PROVING, and that is why it is trusted over any pixel read:**
9 side pads at 2.54 centred on 23.50 gives **1.59 mm** from the top and bottom
edges; 5 bottom pads at 2.54 centred on 18.00 gives **3.92 mm** from the side
edges. Both are numbers the vendor drawing *publishes*, and both fall out of
centring arithmetic alone. A wrong datum would not close like that. Corroborated
by the STEP's own board solid: 18.018 × 23.517 mm, +0.02 on both axes.

### The two carrier keepouts — drawn, not described

Neither is expressible as a `keep_short` budget and **nothing in the pipeline
grades either one**. Both are now drawn into the footprint so they travel with
the part instead of living in prose (module frame → footprint frame):

| keepout | module frame | footprint frame | layer | why |
|---|---|---|---|---|
| HEIGHT | X 4.0..14.0, Y 2.5..22.5 | (-5.00,-10.75)..(5.00,9.25) | `Dwgs.User` | bottom-side parts, 1.000 mm proud. No carrier parts, no proud plating, no silk build-up. **If a reflowable joint is ever wanted this becomes a CUTOUT of the same rectangle — that is the only route to one.** |
| COPPER | X 2.4..3.6, Y 4.8..17.0 | (-6.60,-5.25)..(-5.40,6.95) | `User.Comments` | ten live underside SMD pads (GP17..GP25 + GND), 1.270 mm pitch, MEASURED from the STEP. Zero height, so the height keepout does **not** cover them, and they sit outside it. Bare live copper facing the carrier at ~1.1 mm — a solder ball or a flexed board shorts nine GPIO. |

My own STEP read of the underside pad row reproduces the dossier exactly:
10 pads, 1.011 × 0.609 mm, X centre 2.986, spacing 1.270 mm on every one of the
nine steps. Two independent extractions of the same machine-readable geometry.

Also drawn to `Dwgs.User`: **BOOT and RESET, 2.500 mm tall at (4.45, 7.60) and
(13.45, 7.60)**, with a caption. Verified against the schematic — BOOT, RESET and
SWD reach **no castellation**. Once this module is soldered down those two
buttons are the only hardware route into the bootloader, and there is no
in-circuit debug, ever. And to `F.Fab`: the USB-C receptacle, which overhangs the
module's `-Y` edge by **1.216 mm** (STEP-measured).

### THREE MORE DEFECTS FOUND BY INSPECTION WHILE FIXING THE ABOVE

1. **Two FPIDs pointed into v1's library.** `PE42482A-X` and `KH-SMA-KE-Z` named
   `pluto_rx2_8way:…`. v1 is a separate, NOT-superseded project, so those are
   dangling refs from here and `03_src/lib/contracts.md` forbids them. Both
   footprints are now **vendored** into `03_src/lib/pluto_rx2_8way_v2.pretty/`,
   byte-identical (same part, same vendor land), and the FPIDs repointed. v2 is
   regenerable standalone, which is what canon M3 asks for. `04_kicad/fp-lib-table`
   authored, `${KIPRJMOD}`-relative.
2. **`rebuild_all.sh` still carried the TEMPLATE's knobs** — `BOARD=power3s`,
   `TSX=power3s`. The full-pipeline driver had therefore **never been run** on
   this board; the schematic gate was assembled step by step. Set correctly.
3. **`tsci build` writes `dist/`, not `build/`, and the driver converts
   `build/`.** My first conversion silently consumed a 23-minute-old
   `circuit.json` and produced a netlist with the OLD numbering — caught only
   because I went looking for `U_MCU-…-Pad*` in the netlist by hand. Every gate
   was green against it. **A stale intermediate is invisible to a battery that
   grades self-consistency.** Worked around by copying `dist/` → `build/`;
   the driver line is a skill-owned fix and is reported, not edited here.

### GATE STATE after the change — all UNPIPED, real exit codes

| gate | result |
|---|---|
| TSX-PRE `tsx_preflight.py` | PASS 6/6, exit 0 |
| `tsci build` | exit 0 |
| S-NETMERGE `net_label_survival.py` | PASS 23/23 labels survive, exit 0 |
| E-INV `electrical_invariants.py` | OK 20/20, exit 0 |
| E-ADR `--adr-coverage` | OK 1/1, exit 0 |
| E-TOPO `power_topology.py` | OK 1/1 rails, PD 202 mW of 400 (50 %), exit 0 |
| E-MARGIN `--margin` | PASS, headroom 934 mV vs IR 10 mV × 1.20, exit 0 |
| E-OFF `--off-control` | N-A stated (usb_bus_powered_5v), exit 0 |
| S-COUNT `count_parity.py` | PASS 3/3 pairs, 28 refdes, exit 0 |
| E-NETREF `net_reference_audit.py` | PASS **78/78**, 0 ghost, 0 unreached, exit 0 |
| M-BOM leg C `bom_source_check.py` | PASS, exit 0 |
| P-FACT `part_facts_check.py` | OK 1/8 graded, **7 UNREACHED and listed** (they grade a stage-7 fab BOM), exit 0 |
| ERC `kicad-cli sch erc --severity-all` | **0 errors** / 248 warnings |

**THE NETLIST WAS CHECKED DIRECTLY, NOT INFERRED FROM A GREEN GATE** — this is
the one defect class the whole battery is blind to, because a mirrored map is
self-consistent everywhere:

```
pad  1 -> SEL_V1    (GP0)      pad 21 -> 3V3_MOD
pad  2 -> SEL_V2    (GP1)      pad 22 -> GND
pad  3 -> SEL_V3    (GP2)      pad 23 -> unconnected (5V/VSYS, deliberate)
pad  4 -> SEL_V4    (GP3)
pad  5 -> LED_STAT  (GP4)
```

GP0..GP3 remain consecutive AND physically adjacent down the right edge, which
is what lets a PIO `out pins, 4` write all four select bits in one instruction —
the property survived the renumbering, which is worth saying because it was the
reason the mapping was chosen.

**ERC WARNINGS MOVED 183 → 248 AND I AM NOT CALLING THAT A REGRESSION OR A
BASELINE.** 0 errors both times. All 248 are three cosmetic classes — 131
`endpoint_off_grid`, 89 `lib_symbol_issues`, 28 `footprint_link_issues` (= one
per component; `kicad-cli sch erc` does not read `fp-lib-table`). The movement
is the documented `tsci build` non-determinism, which is the entire reason this
repo keeps a PINNED `03_tscircuit/kicad/*.kicad_sch` and a separate
`rebuild_reuse.sh`. The pinned schematic has been re-synced to the new source.

### E-NETREF `keep_short` — a regression I caused and caught

Installing the dossier wholesale dropped the four `SEL_V1..V4` 25 mm coupling
budgets and the `3V3_MOD` budget: E-NETREF fell 78 → 74 references. The dossier
cannot carry them — it does not know this board, and it says so in the block
itself, instructing the lander to re-point rather than delete. Restored, with the
vendor pad numbers as anchors (`SEL_V1`=pad 1 … `SEL_V4`=pad 4). The dossier's
`3V3` @ 5 mm is re-pointed to **`3V3_MOD`** — on this carrier `3V3` is the
FILTERED rail downstream of `FB_3V3` and the module's pad-21 node is `3V3_MOD` —
and its 5 mm is kept over the 10 mm previously declared, because the tighter of
two budgets on one node binds. Back to **78/78, 0 ghost**.

### WHAT IS NOT DONE, AND WHY — this is the handoff

**The two arithmetic floors are NOT MEASURED, and I will not report an
estimate.** Both are pad arithmetic that refuse an impossible board in
milliseconds, and both need something that does not exist yet:

* **P-LAND (min landable width)** is `escape_check.py --board`, which needs a
  `.kicad_pcb`. It cannot be run against part dossiers.
* **The octilinear floor** `max(dx,dy) + 0.4142·min(dx,dy)` is not a property of
  the parts at all — it is a property of the **star geometry**, i.e. of a
  `floorplan.yaml` that has not been authored. v1's 1.4966 mm is meaningless
  here and was correctly forbidden. What v1's table *does* transfer is the
  LEVER, and it should shape the floorplan before a router ever runs: v1's ten
  slots sat at 15/45/75/105/… so only 3 of 9 radials lay on a 45° multiple and
  the other six each paid a 1.0731× penalty. **Choosing star angles that are
  multiples of 45° drives the octilinear excess to zero by construction.** That
  is the first thing to test against v2's own pads.

`floorplan.yaml` and `route.yaml` remain OWED, deliberately, and the module's
mechanical facts now constrain them in ways the previous agent's floorplan
assumptions did not anticipate: the USB-C edge must sit **at or beyond the
carrier's board edge** (the receptacle overhangs 1.21 mm and a plug's overmould
runs ~1.0 mm *below* the module's bottom face — even at the 1.1 mm standoff it
only just clears), both buttons must stay physically accessible, and **GND is
ONE castellation** (pad 22, top of the left edge, diagonally opposite most
signal pads) carrying every return from 20 GPIO — land it on a direct via drop
to the plane and expect the module's ground reference to be worse than the
carrier's everywhere else.

### RF — one debit that got worse, and it belongs in the floorplan

The WS2812 is **hard-wired to 3V3 with NO power-enable GPIO** (the XIAO gates
its NeoPixel supply; this module does not). Its controller free-runs whenever
the module is powered and **keeps running with the LED commanded black** — the
only off switch is VSYS. MEASURED: it sits **directly over the RP2040 with
1.091 mm of laminate between them**, so there is no plane to add and no distance
to buy. And it is **not a 5050 WS2812B**: the STEP body is 1.50 × 1.80 mm, a
1615-class variant whose **exact MPN is OWED** — which matters, because
oscillator frequency and edge rate are variant-specific. This is a
distance-and-orientation constraint on the star, and **powering the module down
between measurements composes well with the self-timed dwell scheme this board
already has.**

## 2026-07-30 — finish (placement gate GREEN): the 45-degree lever, spent

- did: authored `03_src/floorplan.yaml`, generated the board, and MEASURED the
  two floors that were owed at handoff. Both needed a `.kicad_pcb` and both are
  now measured off the real one, not estimated.
- result: **OCTILINEAR FLOOR SPREAD 0.0007 mm = 0.01 deg at 6 GHz**
  (`copper_length_audit.py`, from pads alone) against v1's 1.4966 mm / 19.74 deg
  — a 2100x reduction bought at placement, for free, before a router ran.
  **P-LAND PASS**, 50 pads graded of 130 copper pads, 0 failing, after one
  scoped clearance earned by this board's own measurement.
- next: `route.yaml`, then route/stitch, then `generate_rules` LAST, then DRC.

### THE STAR: EIGHT GRADED ARMS ON EIGHT COMPASS POINTS, AND IT IS FORCED

The eight members of `RF_ARMS` leave U_SW pads 24/2/4/6/13/15/17/22 at bearings
135/180/225/270/315/0/45/90. That is the ONLY assignment that is monotone in
the QFN's own CCW RF pin order (RF1, RF2, RF3, RF4, [control], RF5, RF6, RF7,
[RF8 pickoff], RFC) AND seats eight members on eight 45-degree multiples. It
was not chosen from a menu; there is one.

The control escape then lands in the 45-degree sector between the S arm (270)
and the SE arm (315), centred on 292.5 — which is where U_SW's own control pads
already point (pads 9..12 sit at theta 262..303). Nothing was bent for it.

**ARM LENGTHS 14.00 (axis) AND 9.90 PER AXIS (diagonal), and the pair is the
whole trick.** 9.90*sqrt(2) = 14.000714, because 99/70 is the convergent of
sqrt(2) (99^2 = 9801 vs 2*70^2 = 9800). Both numbers are exact multiples of the
0.05 mm router grid, which rf-design 4(c) says is the FIRST cause of a launch
that will not route. The 0.000714 mm residue is the price of staying on-grid
and it is 0.0094 deg at 6 GHz.

MEASURED, `copper_length_audit.py .`:

    OCTILINEAR FLOOR (pads alone, no copper): spread 0.0007 mm = 0.01 deg at 6 GHz
      ARM_RF1 14.0007   ARM_RF2 14.0000   ARM_RF3 14.0007   ARM_RF4 14.0000
      ARM_RF5 14.0007   ARM_RF6 14.0000   ARM_RF7 14.0007   ARM_RFC 14.0000

The realized-copper half is UNREACHED and says so — the board is unrouted. That
is the correct reading, not a pass.

### THE BOARD DID NOT LOAD, AND THE CAUSE WAS A LAYER NAME

`pcbnew.LoadBoard` returned **None** and `kicad-cli` said only *"Failed to load
board"* — no line, no token. Bisected by rebuilding the file from its top-level
elements: the culprit is `RP2040_Zero_LCC23_18x23.5.kicad_mod`, which draws the
COPPER keepout on **`User.Comments`**. That is KiCad's GUI DISPLAY name; the
file token is **`Cmts.User`**, and the board's own layer table says so in the
same file: `(19 "Cmts.User" user "User.Comments")`.

Two lines fixed. The interesting part is the failure shape: the footprint was
authored last session and reviewed in prose ("both keepouts are now drawn into
the footprint so they travel with the part"), and it was TRUE that they were
drawn — one of them was drawn onto a layer that does not exist, which made
every board carrying the part unloadable, and nothing could see it until a
board existed. A footprint is not validated by anything in this pipeline until
a generator consumes it.

### P-LAND: SIX PADS, AND IT IS ARITHMETIC

`escape_check.py --board` BEFORE any router ran:

    U_SW.2  ANT2    RF50 floor 0.360  landable 0.300  short 0.060
    U_SW.4  ANT3    RF50 floor 0.360  landable 0.300  short 0.060
    U_SW.15 ANT6    RF50 floor 0.360  landable 0.300  short 0.060
    U_SW.17 ANT7    RF50 floor 0.360  landable 0.300  short 0.060
    U_SW.22 RX2_OUT RF50 floor 0.360  landable 0.300  short 0.060
    U_SW.8  3V3     PWR  floor 0.400  landable 0.300  short 0.100

The vendor land is 0.30 x 0.60 on a 0.50 pitch, so a neighbour's copper edge is
0.350 mm from the pad centre and the widest track that leaves at clearance c is
2*(0.350 - c): 0.300 at c=0.200, 0.420 at c=0.140. The three RF pads that do
NOT fail (24, 6, 13) are exactly the ones whose arm leaves DIAGONALLY — which
is independent evidence that the number is about pad geometry, not the router.

ONE scoped clearance (`rf_launch`, 5.40 x 5.40 mm about the switch centre,
bounded on both sides of the pair) at 0.14 mm. **FIVE of v1's six relaxations
are NOT re-adopted, and the reason is geometry rather than restraint:** v1's
`rf_jack_*` entries relax an arm against an SMA GROUND POST because v1's arms
cut across the post square at 15/45/75 degrees. v2's arms arrive on the post
square's own symmetry axes (axis jacks rotation 0, diagonal jacks rotation 45),
so every arm centreline clears the nearest post centre by 2.540 mm — 1.590 mm
of copper gap against a 0.20 mm floor. The rotation rule bought that.

Re-measured after: **P-LAND PASS, 0 failing, 10 pads graded against the scoped
clearance.**

### ALSO FIXED HERE

* `rules/nets.yaml` `length_match.RF_ARMS` had no `adr:` and `copper_length_audit`
  refused to grade it at all (exit 2, R-LEN UNGRADED). Pointed at **"0003"**,
  quoted — 0003 is where eps_eff -> t_pd -> deg/mm is derived with its command,
  which is what turns PE42482A-X's 13.2 deg window into the 1.00 mm ceiling.
  Unquoted, YAML 1.1 would read `0003` as octal and hand the gate the integer 3.
* `rules/assembly.yaml` carried **two** top-level `not_assembled:` keys. Last-wins
  made it harmless by accident (the second block was the complete one); an edit
  to the first would have been discarded silently. One home now.

### PLACEMENT GATES, UNPIPED

| gate | result |
|---|---|
| `generate_board_generic.py` | 28 placed, 28 anchored, asserts 12/12, exit 0 |
| P-COLLIDE | 0 pad shorts, 0 anchored courtyard overlaps, 134 copper pads |
| R-LEN-OCT `copper_length_audit.py` | floor spread **0.0007 mm**, exit 0 |
| P-LAND `escape_check.py --board` | **PASS** 50/130 graded, 0 failing, exit 0 |
| P-OUT `placement_gates.py` | PASS, tightest pad-to-outline 1.49 mm (U_MCU.1) |
| P-CAP | PASS, worst cut y=60.5: 5 nets vs 112 capacity, ratio 0.04 |

## 2026-07-30 — finish (ROUTING gate GREEN): DRC 0 / 0 / 0

- did: authored `03_src/route.yaml`, routed with KRT, promoted the chain,
  stitched, ran `generate_rules` LAST, and classified every DRC finding to a
  cause until there were none.
- result: **`kicad-cli pcb drc --severity-all --refill-zones
  --schematic-parity` = 0 violations / 0 unconnected / 0 parity.** R-LEN PASS:
  realized copper spread **0.5314 mm = 7.01 deg at 6 GHz** against the 1.0 mm
  ceiling, every arm 0 vias / 1 component / 2 ends.
- next: stage 6 verification, then seal.

### THE GRID WAS THE ANSWER TWICE, AND THE SECOND TIME WAS NOT AN RF PROBLEM

`SW_V2` — the one control pad with a routed neighbour on BOTH sides — failed
with *"ROUTE FAILED - no rippable blockers found"* in **eight of eight raced
candidate chains**. Eight identical failures is what an INFEASIBILITY looks
like when it is being read as congestion.

The cause is `rf-design.md` 4(c) arriving on the digital side: U_SW's control
pads sit at x = 40.75 / 41.25 / 41.75 / 42.25, ODD multiples of 0.05 mm,
because the QFN's own pad offsets are +/-0.25, +/-0.75, +/-1.25 about a centre
on the 0.05 grid — and at KRT's default `grid_step: 0.1` no centreline can land
on them. The first draft of `route.yaml` gave `grid_step: 0.05` to the rf wave
only, because that is where the canon records it. **The grid is a property of
the PAD COORDINATES, not of the net class.** Moved to `route.common`: 4/4 waves
routed, `quick` verdict CLEAN, zero clearance findings pre-stitch.

**AND THE OBVIOUS REMEDY WAS MEASURABLY WORSE.** Before finding the grid I
split the four select lines into four ordered west-to-east waves, reasoning
that escape lanes are claimed by whoever routes first (golden rule 4). MEASURED:
one `ctrl` wave leaves SW_V2 open (7 of 8 routed); four ordered waves leave
SW_V2, SW_V4 **and** LED_STAT_A open. KRT can only rip up WITHIN ITS OWN WAVE,
so splitting a congested field into single-net waves does not order the escapes
— it FREEZES the first choice. Ordering helps ACROSS independent fields; inside
one field the wave must stay whole.

### THE DRC BURN-DOWN: 21 -> 2 -> 1 -> 0, FIVE CAUSES, NEVER A COUNT

First stitched run, 21 findings. Grouped by CAUSE they are five unrelated
problems, and 12 of the 21 are one config line:

| n | class | cause |
|---|---|---|
| 12 | 8 clearance + 4 hole_clearance | **stitch-grid vias inside an SMA centre pin's own 0.80 mm LOCAL clearance.** Two grid sites at (31.0, 59.0) and (29.0, 61.0) measured 0.7312 and 0.7858 mm from J_ANT3 pad 1. Reported once per copper layer, which is why one geometric fact appears twelve times. |
| 5 | silk_over_copper | the MODULE FOOTPRINT's own silk: four corner brackets ending 0.10 mm from its own castellation lands, and the pin-1 dot 0.10 mm from pad 1. |
| 2 | clearance | **C_BULK placed 0.175 mm from U_MCU's east castellation column** — a placement error of 0.025 mm, invisible until copper existed. |
| 1 | track_width | KRT's via-in-pad stub for SW_V3 came out **0.1069 mm** over a 0.100 mm run against the 0.200 mm CTRL floor. |
| 1 | silk_overlap | J_ANT5's refdes vs **U_MCU's Value field, which the authored footprint put on F.SilkS** instead of F.Fab. |

Fixes, one per cause: a per-PIN `avoid` ring in `stitch_grid` (radius 1.90 =
pad 0.95 + local clearance 0.80 + via 0.125 — NOT a board-wide `pth_margin`
bump, which would push stitch vias away from all forty SMA ground posts too);
the footprint brackets shortened and the pin-1 dot moved; C_BULK and FB_3V3
0.40 mm east; the `width_floor` stitch pass added; and the module's Value field
moved to F.Fab, where KiCad's own convention puts it and where a JLC CONSIGN
PLACEHOLDER CODE for a part JLC is asked to place nothing of does not print on
the silkscreen.

### THE ONE FINDING THIS BOARD CREATED WHILE FIXING ANOTHER

Lifting SW_V3's 0.1069 mm stub to the 0.200 mm floor is right, and it cost
0.047 mm per side: the pair SW_V2/SW_V3 went from a 0.205 mm gap to **0.158 mm**
at 0.358 mm centre-to-centre. Recorded rather than folded in, because it is the
failure museum's *"fixing a nudged via into a new violation"* entry.

**AND THE FIRST FIX FOR IT DID NOTHING AT ALL, WHICH IS THE MORE USEFUL HALF.**
I added SW_V1..V4 to `rf_launch`'s `nets:` list. `rf_launch` is declared
`layers: [F.Cu]`; the pair is on **In2.Cu**; KiCad evaluates `insideArea` PER
LAYER — so the relaxation was declared, read as declared, and bound nothing.
The DRC finding was byte-identical afterwards. **A rule area is (rectangle AND
layer set), never a rectangle.** The real fix is `ctrl_escape`, a 1.10 x 0.90 mm
In2.Cu area containing exactly those two segments and their two barrels; SW_V1's
barrel and 3V3's In2.Cu run fall outside it and keep the 0.20 mm floor.

### FINAL SCOREBOARD, ALL UNPIPED, RAW EXIT CODES

| gate | result |
|---|---|
| `kicad-cli pcb drc --severity-all --refill-zones --schematic-parity` | **0 / 0 / 0** |
| R-LEN `copper_length_audit.py` | **PASS** spread **0.5314 mm = 7.01 deg**, ceiling 1.0; floor spread 0.0007 mm; 8/8 members measured, 0 vias each |
| P-LAND `escape_check.py --board` | **PASS** 45 graded / 130 copper pads, 0 failing, 9 against a scoped clearance; routed cross-check 45/45, 0 wider than the model allows |
| P-OUT / P-CAP `placement_gates.py` | **PASS** 0 fails 0 warns; tightest pad-to-outline 1.28 mm (C_BULK.1); worst corridor ratio 0.04 |
| E-NETREF `net_reference_audit.py` | **PASS 95/95**, 0 ghost, 0 unreached |
| R-PREFLIGHT `tier_preflight.py` | 0 FAIL / 1 WARN (PF-ROUTE-CLR, expected and answered by the two scoped clearances) |
| stitch `gate:` | clean; 493 grid vias, 528 emitted, 0 pruned |

### OWED, MEASURED, NOT MET — the via fence

ARCHITECTURE sec 6 asks for a ground-via fence flanking every arm at
**<= 1.35 mm** (guided lambda_g/20 = 1.3693, ADR-0003). The shared stitcher's
`stitch_grid` steps with `range(int(...))`, so its pitch is an INTEGER number of
millimetres — 1 mm (a ~2500-site via forest) or 2 mm. This board ships **2.0 mm
= lambda_g/13.7**, which is conservative against the SOURCED free-space
lambda/20 = 2.5 mm at 6 GHz and matches what `pluto-cal-switch` ships, but it
does NOT meet this board's own tighter bound. Stated as a measured gap.
A fractional step is silently TRUNCATED (`int(1.35)` = 1), which is a skill
finding reported upward, not worked around here.

## 2026-07-30 — finish (REGENERABILITY, canon M3 + M-FRESH)

- did: adopted the M-FRESH-corrected driver from the skill template and ran
  `03_src/rebuild_all.sh` END TO END, from the `.tsx` to the DRC gate.
- result: **exit 0, DRC 0/0/0.** `build_provenance.py audit` **M-FRESH PASS**.
  The board reproduces from `03_src/` + `03_tscircuit/` with ZERO board-specific
  generation Python.

**THE STALE-PATH DEFECT WAS STILL IN THIS BOARD'S OWN DRIVER.** The previous
session found it, worked around it by hand (`cp dist/ -> build/`) and reported
the driver line as skill-owned — and the driver line stayed wrong. VERIFIED
BEFORE TOUCHING ANYTHING that nothing here had been graded stale:
`03_tscircuit/build/circuit.json` and
`03_tscircuit/dist/src/pluto_rx2_8way_v2/circuit.json` are BYTE-IDENTICAL
(sha256 `59a5ad62…`), and both the schematic and the netlist post-date them.

**tsci NON-DETERMINISM, MEASURED RATHER THAN ASSUMED.** The driver's own
`tsci build` rewrote the schematic: the `.kicad_sch` and `.net` bytes both
CHANGED. Node-for-node they are IDENTICAL — **40 nets, 130 nodes, zero
differences** — so the churn is schematic geometry and the board is untouched.
Worth recording HOW that was measured: the first two comparison scripts
reported "identical" while matching NOTHING, because KiCad 10 pretty-prints the
netlist across lines and both regexes were written for the KiCad 7 same-line
form. The skill warns about exactly this. A comparison that finds nothing and a
comparison that finds no differences print the same word.

**ERC MOVED 248 -> 220 WARNINGS, 0 ERRORS BOTH TIMES**, and the 28 that left
are the `footprint_link_issues` — one per component — now that
`04_kicad/fp-lib-table` resolves every FPID. 131 `endpoint_off_grid` + 89
`lib_symbol_issues` remain, both converter-geometry artifacts, neither
electrical.

**THE TEMPLATE'S ERC LINE GATES ON WARNINGS.** `kicad-cli sch erc
--severity-all --exit-code-violations` exits non-zero on ANY violation, so this
board failed its own driver at 220 cosmetic warnings while carrying zero
errors. The canon gate is 0 ERRORS with warnings baselined. Split in this
project's copy into two runs — the full-severity report is still WRITTEN
(a baseline nobody records cannot be reviewed) and only the error-severity run
gates. Reported upward as a template finding.

FINAL, on the driver-produced board: DRC **0/0/0** · R-LEN **PASS** 0.5314 mm =
7.01 deg (floor spread 0.0007 mm) · P-LAND **PASS** 0 failing, routed
cross-check 45/45 · P-OUT/P-CAP **PASS** · E-NETREF **PASS 95/95** · M-FRESH
**PASS** · ERC **0 errors**.
