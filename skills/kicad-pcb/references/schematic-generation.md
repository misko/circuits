# Generator-driven schematics

## The paradigm

One Python generator = single source of truth. It emits `.kicad_sch`
(KiCad 7 dialect) with embedded symbols, every pin carrying a global net
label (no wires needed for connectivity), physical package pad numbers
verified against datasheets. The netlist drives pcbnew directly. Layout,
BOM identity, and net map all live in ONE reviewable file.

Rules that keep it safe:
- The generator must NEVER overwrite `.kicad_pro` if it exists (write-if-
  missing only) — the project file carries DRC rule floors, netclasses,
  severity policy. This was violated once and silently destroyed the
  DRC-clean state.
- After ANY regeneration: netlist parity check. Export with
  `kicad-cli sch export netlist`, parse `(net (name) (node ref pin))`,
  compare net→{(ref,pin)} maps node-for-node (apply expected pin remaps,
  e.g. a package change, through an explicit table). PASS or explain.
- Package changes: remap pins via PORT names from the datasheet, not
  guessed offsets; cross-check anchor pins (GND/VDD/UPDI) against the old
  net map; drop EP pins that don't exist in the new package; update the
  board generator's in-pad-via lists (an EP heuristic will happily punch
  GND vias through a SOIC signal pin).

## Readability: sections + validated structure links

A label-only schematic is netlist-complete but reads as a parts field.
Two additions fix it without touching the netlist:

1. **Section boxes**: track per-section extents during placement, emit
   `(rectangle ...)` graphics padded clear of titles (top +4.5) and labels
   (±2), clamped inside the sheet frame. Titles sized into the bbox
   (`x + 1.9*len(title)`).
2. **Structure links as GRAPHICS, never wires**: dashed `(polyline ...)`
   between pin endpoints. Two safety properties: graphics cannot alter
   connectivity, and `link(refA,pinA,refB,pinB)` asserts both pins already
   share a net — a wrong link is a build error, not a lie on the drawing.
   Route side-aware (H-V-H through facing gaps; outward lane ~8.5 mm for
   same-side runs) so lines never cross symbol bodies.
3. **Auto-derive most links from the netlist**: (a) every 2-pin
   point-to-point net (gate drives, series junctions, port feeds) is
   unambiguous — link it; (b) every rail bypass part (2-pin passive, one
   leg GND) links to its NEAREST same-net pin (≤60 mm), visualizing which
   IC each decoupler serves. Keep a small hand list for multi-pin
   structural edges (SW nodes, FB chains). Dedupe hand vs auto.

## Text collision rules (from a fresh-eyes review that found 8 defect classes)

- Stacked 2-pin passives need ≥10 mm pitch or refdes/value texts collide.
- Long title-block comments clip off-sheet — keep them under ~60 chars.
- Parts at x<~30 put left-side labels into the sheet frame.
- Check L/R label direction against dense neighbors.

## Verification loop (non-negotiable for generated figures)

1. `kicad-cli sch export svg` → `rsvg-convert -w 6000` → PIL crops.
2. Look at the renders yourself.
3. **Spawn a fresh-context agent to describe the figures back** — it
   catches what the author cannot see (box-title strikethroughs, caption
   collisions, lines through symbols, off-frame elements). Fix, re-render,
   repeat once.
4. Netlist parity as above; ERC if wires are ever introduced.

## Analysis companion

kicad-happy `analyze_schematic.py` detects subcircuits (dividers,
decoupling groups, bridges, USB buses) — useful to cross-confirm structure
links and as a review sweep. Known false-alarm classes on label-only
generated captures: rail-source/PWR_FLAG warnings, pull-ups on unused
open-drain pins, "22R USB series" advice, missing-decoupling claims that a
board-level proximity check disproves. Triage against physical evidence
before acting.
