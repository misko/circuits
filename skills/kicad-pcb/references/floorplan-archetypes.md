# Floorplan archetypes — placement as ADAPTATION, not derivation

The ledger's placement twin: one entry per proven BOARD CLASS — the
placement SHAPE that shipped, with its adjacency groups and escape
corridors, so a new board of a known class starts from a working floorplan
instead of deriving one. Same rules as `proven-parts.yaml`: entries carry
provenance (board names only — C-ISO), are harvested at release (new class
→ new entry; refinement → update with provenance), and record judgment,
never coordinates to copy blindly — adapt to THIS board's outline and
parts (canon M3: the floorplan.yaml you write is the source of truth).

---

## power-hub (battery/DC in → protection → converter(s) → port bank out)

**Provenance:** usb-power-3s v1.0-1.3 (shipped), xt60-usb-supply-rerun
v1.0-1.0.2 (shipped), lipo3s-usb-hub, lipo3s-tsc, usb-pwr-hub-3s
(cleanroom v3), usb-hub-3s (cleanroom v4) — six boards of the same shape.

**The shape (regions, in current-flow order):**

    [input edge]                                   [port edge (opposite)]
    XT60 → RPP FET → fuse → TVS   ...open...   port1 port2 port3 portC
        \ INPUT PROTECTION corner               PORT BANK: connectors on
          (all series elements in a line,       the edge, mouths outward;
          pours widen monotonically)            per-port switch/polyfuse/
                                                ESD DIRECTLY behind its
              CONVERTER ISLAND(S), center:      connector (repeat: bank)
              controller + FETs + L + sense
              in ONE tight hot loop each;
              islands separated (>= ~20mm on
              shipped boards); fine-pitch side
              of each IC faces OPEN copper
              with an ESCAPE CORRIDOR reserved

**The rules the shipped boards obeyed:**
- Current flows ONE WAY across the board (input edge → converters → port
  edge); no power net doubles back. Return is the unbroken In1 GND plane.
- Each converter is an ISLAND: controller, FETs, inductor, sense parts in
  one tight loop; islands far enough apart that their pours never compete
  (~20mm+ at 6-15A on 4-layer 1oz).
- The QFN/controller's hard-net side (SW/BST/FB or fine-pitch bank) faces
  open copper, with the escape corridor kept free of other placements —
  this is the difference between xt60-rerun's standard-tier SY8368 escape
  (outward-only, adjacent passives) and the v2 stall (same part,
  stranded passives).
- Port bank is a REPEAT pattern (floorplan `repeat:` banks): connector +
  its switch + polyfuse + ESD as one repeated unit, mouths on the edge.
- Protection corner parts placed in series-current order — the pour
  narrows at each protection element exactly once, never zig-zags.
- Sense/feedback dividers hard against their IC pins (D-ADJ), never in
  the corridor.

**Known scaling limits:** proven 50x50 to 119x72mm, 1-2 converters,
3-5 ports, 6-15A aggregate, 4-layer. Beyond 2 converters or ~20A, expect
to re-derive the island spacing (and harvest the result back here).

---

_No other class has shipped enough boards to earn an archetype yet.
Candidates when they do: sensor-chain (cook-loadcell/crow-array family),
mcu-hub (cook-hub). Found them from the sealed floorplans, not memory._
