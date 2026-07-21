# Layout precedents — finding how others routed the same local circuit

For any HARD part (dense escapes, switching power, >0.5A analog, RF), a
routed reference almost always exists. Consulting it is cheaper and safer
than deriving the local layout from first principles — and canon M6 says
the manufacturer's own routed example WINS over your derivation. This doc
is the source catalog, in authority order, with what to extract and the
rules that keep it canon-clean.

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

### 2. Manufacturer evaluation-board (EVM) design files
TI / ADI / onsemi / MPS publish complete EVM layouts — schematics,
board files or gerbers, and assembly drawings — for most converters.
An EVM is a TESTED, routed instance of the local circuit at a known
current. Find it from the part's product page ("Design & development" /
"Evaluation boards"). What to extract: the escape pattern at the real
package, component orientation relative to the inductor, where they
accepted vias in sense lines, stitching density.

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
- Precedent disagreement: datasheet beats EVM beats OSH beats GitHub.
  If our derivation must depart from the datasheet figure, that is an
  ADR-worthy decision, not a silent choice.
