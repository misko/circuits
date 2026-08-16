# Layout precedents — finding how others routed the same local circuit

For any HARD part (dense escapes, switching power, >0.5A analog, RF), a
routed reference almost always exists. Consulting it is cheaper and safer
than deriving the local layout from first principles — and canon M6 says
the manufacturer's own routed example WINS over your derivation. This doc
is the source catalog, in authority order, with what to extract and the
rules that keep it canon-clean.

## Contents

1. Study-then-rederive contract
2. Sources in authority order
3. Transfer and licensing caveats

## The contract: STUDY, THEN RE-DERIVE

- Extract DECISIONS, never copper: adjacency (which passive hugs which
  pin), package orientation, escape pattern (which pins drop vias, where,
  staggered how), hot-loop shape, sense/feedback dress, layer-drop points,
  corridor reservations, thermal via counts.
- The decisions land in OUR sources: `part.yaml` `gotchas:` +
  `layout_refs:`, `floorplan.yaml` placement, `route.yaml` config. Never
  import board files, never trace over someone's copper (canon M3:
  everything regenerable from our source — the same line ADR-0002 draws
  for tscircuit's own PCB output).
- Record every reference consulted in the part.yaml `layout_refs:` list
  and harvest it into `proven-parts.yaml` at release — the search is paid
  once per part, ever.

## Sources, in authority order

### 1. The datasheet's Layout Guidelines / Layout Example section
Nearly every power/analog IC carries one (often with a routed figure and
a layer-by-layer description). This is the part maker's own answer for
the exact local circuit. ALWAYS read it — the pin-map extraction habit
stops at the pinout table; the layout section is later in the document
and routinely skipped. What to extract: the hot loop, which ground is
quiet vs power, Kelvin connections, "place X within Y mm" rules, thermal
via guidance.

### 2. Any OPEN-HARDWARE reference design with PUBLISHED LAYOUT
TI / ADI / onsemi / MPS publish complete EVM layouts — schematics,
board files or gerbers, and assembly drawings — for most converters.
An EVM is a TESTED, routed instance of the local circuit at a known
current. Find it from the part's product page ("Design & development" /
"Evaluation boards"). What to extract: the escape pattern at the real
package, component orientation relative to the inductor, where they
accepted vias in sense lines, stitching density.

**THIS TIER IS WIDER THAN "EVM", AND MISREADING IT AS EVM-ONLY IS HOW IT
GETS SKIPPED FOR NON-CONVERTERS.** It is any reference design whose LAYOUT
is published — a vendor's own reference board, a chip maker's minimal
design example, a foundation's open board. MCUs, radios and codecs have
these as often as converters do.

**AN EDITABLE DESIGN FILE OUTRANKS A RENDERED FIGURE.** A figure is read
by eye at whatever DPI the PDF carries; a design file opens in KiCad and
is MEASURED. So a tier-1 figure does NOT discharge this tier when files
exist — search for them explicitly. Formats rank by what you can do with
them: KiCad (open and measure) > gerbers (measure, no netlist) > Allegro /
Altium (openable only if you have the tool) > a rendered figure.

WORKED CASE — RP2040 (canon P-PREC; verified 2026-07-30 at
`raspberrypi.com/documentation/microcontrollers/rp2040.html`). Raspberry
Pi publishes a **"Minimal Viable Board" reference design in KiCad** —
schematic AND PCB layout — plus the full Pico and Pico W designs in
Cadence Allegro and a VGA carrier board in KiCad. All are free and carry
"Raspberry Pi grants permission to use, copy, modify, and distribute the
following designs for any purpose, with or without fee". `pluto-rx2-8way`
read the *Hardware design with RP2040* Figure 6 raster at 200 dpi
instead — a careful consult that stopped one tier short of a free,
editable, permissively licensed layout for the exact part.

Licence is a tier-2 question: a permissive licence is what makes the file
openable at all. It never licenses copying — study-then-re-derive is canon
M3 regardless of licence.

### 3. OSHWLab / EasyEDA open projects — SEARCH BY LCSC CODE
The highest-leverage source for THIS pipeline: we select parts by LCSC
code, and oshwlab.com search accepts the same code — returning real,
usually JLC-FABBED boards using the exact orderable part, with copper
viewable in the browser. Ground truth for "what actually manufactures at
JLC at which tier." Quality varies: prefer projects with fab photos /
order history, and treat a lone hobby board as a hint, not an authority.
NEVER import the EasyEDA board file — view, extract decisions, close.

### 4. Open KiCad projects (GitHub, Kitspace)
`filename:*.kicad_pcb <MPN>` on GitHub code search, or Kitspace's part
index. Weakest tier: unvetted, often unfabbed, sometimes wrong — use
only when 1–3 come up empty, and weigh a project by evidence it was
actually built (photos, fab outputs, issues discussing bring-up).

## Caveats

- License hygiene: EVM files and OSH projects are for study; we re-derive
  into our own config, which keeps us clean regardless of license. Do not
  vendor anyone's board files into the repo.
- A precedent at a DIFFERENT current/tier transfers only partially — a
  7A EVM's escape pattern may assume vias our standard tier forbids;
  re-check every via against `fab_tiers.yaml` floors (the ADR-0008
  lesson: hole-to-hole is the binding constraint at fine pitch).
- **DOES IT TRANSFER? THE REFERENCE'S SURROUNDINGS ARE PART OF ITS
  EVIDENCE.** A reference proves its local pattern works IN ITS OWN
  NEIGHBOURHOOD. Compare neighbourhoods before adopting it: how much free
  space does the reference leave on each side of the part, and does this
  board leave the same? A reference with open room on four sides, adopted
  onto a board that pushes the part to an edge or fills the middle with an
  RF star, can hand you a LOCAL pattern that still holds while the ESCAPE
  BUDGET does not — and the escape budget is what bites at stage 6, not
  the decoupling. Do the arithmetic at placement: escapes per side x
  (track + clearance) against the band actually left. MEASURED on
  `pluto-rx2-8way`: 8 escapes on the north 0.400 mm side into a 3.2 mm
  band is exactly 8 x (0.25 + 0.15), and that board carries 28 unconnected
  nets and 21 via-clearance findings in the MCU field. The RP2040 consult
  was right about the flash corner and the decoupling rows; nothing asked
  whether the FANOUT survived a different surrounding.
- RECORD THE SEARCH IN THE GRADED FORM. `layout_refs:` entries take a
  mapping form — `{tier:, artifact:, reached:, why:}` — graded as canon
  **P-PREC** by `policy_audit.py`. THE LADDER MUST NAME ITS CEILING: if
  the best tier reached is below 4, name the stronger artifact you did NOT
  reach and why. Stopping at tier 1 is often right; it must be a STATED
  call. The bare-string form stays legal and is counted OWED, never
  failed.
- Precedent disagreement: datasheet beats EVM beats OSH beats GitHub.
  If our derivation must depart from the datasheet figure, that is an
  ADR-worthy decision, not a silent choice.
