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

## analog-audio-pod (sensor capsule → analog cell → line driver → single cable port)

FOUNDED from the sealed crow-array-pod v1.1 / crow-mic-pod v1.0 floorplan
(2-layer, 94.5x44.5, enclosure-max outline). The shape (long axis = signal
flow, port end WEST, sensor end EAST):

- **WEST edge: the cable port** (RJ45/terminal), mating face toward the
  enclosure gland wall. Entry protection (ESD array) HARD AGAINST the
  port's signal tails (D-ADJ), on the port side of any choke/filter
  provision. Reserve the port's dense tail field an escape corridor and
  set its GND tails to SOLID zone connection (2-layer thermal starvation).
- **CENTER-EAST: the quiet analog cell** — amp + its passive web (bias
  divider, feedback, coupling caps) clustered within 2-5mm of their pins;
  midpoint/VMID reference beside the amp, not across the board.
- **FAR EAST: the transducer/sensor** (mic pads) — maximum physical
  separation from both the port and any switched/noisy block.
- **SW CORNER (port end, opposite edge from audio): the switched block**
  (beeper/actuator + clamp) — its return pair runs straight to the port
  without crossing the analog cell.
- **SOUTH strip: rail filtering** (RC filter, bulk caps) between port
  power pins and the analog cell; test points along the south edge.
- **GND = both-layer pours + stitch ring**; no routed GND. Power as
  DRU-floored tracks (PWR 0.5 / switched 0.6 / signal 0.3 on the sealed
  instance).
- Escape corridors: the port tail field's interior pads route FIRST
  (hardest-first: their single escape lane gets walled in by end-pad nets
  otherwise — measured on the sealed board).

Scaling notes: one analog channel, one port. For multi-channel pods,
replicate the analog cell along the long axis before widening the board.

---

## mixed-signal-audio-hub (port bank fan-IN → analog ADC spine → digital MCU + USB out)

FOUNDED from the sealed crow-recorder-central v1.0 floorplan (6-layer JLC
small-via, 176x122, F/In1-GND/In2/In3/In4-GND/B). The INVERSE of the
analog-audio-pod: many cable ports fan IN to one board. The organizing
principle is a THREE-BAND HORIZONTAL STRIPE with the quiet analog cell as a
spine between the two noisy bands, so ADC copper never shares a band with
either the switching supplies or the beeper-return currents:

- **NORTH edge: the port bank** — the repeat pattern of cable jacks (8x
  RJ45) with each port's ESD array HARD against its signal tails and its
  per-port protection (audio/beep PTCs, low-side switched-return FET) in
  the same north strip. The switched-return (beeper) current path lives
  ENTIRELY in this north band — it never crosses south into the analog
  band (a placement invariant, audit-enforced by net-separation).
- **CENTER band: the analog ADC spine** — the ADC(s) (2x PCM1865) spread
  left/right flanking the board centerline, the quiet analog LDO (XC6227
  3V3A) between them, and every ADC's coupling/bias web within 2-5mm of its
  pins. This band is the electrical firewall: it is fed by its OWN LDO rail
  (3V3A) off the 5V input, NOT the digital buck rail, and is joined to the
  digital domain only inside the ADC die and at GND.
- **SOUTH: the digital cell** — the big MCU (XU316 TQFP-128) centered with
  its flash, crystal, and clock buffer clustered on its hard-net side, and
  the off-board data port (USB-C device) at the south edge, mating face to
  the board edge (verified flush/overhung, not set back). The MCLK tree
  (source → buffer → per-ADC 33R series links) runs north from the buffer
  into the analog band on short, series-terminated legs.
- **WEST/SW corner: the power cluster** — DC/barrel input + protection
  chain (PTC → TVS → reverse-FET) in series-current order, then the
  step-down converters (2x buck for the digital 3V3 + core 0V9, sequenced
  by power-good) and the 1V8 LDO. Kept in one corner, off the analog spine.
- **GND = In1 + In4 solid planes + F/B pours + heavy stitch** (this board:
  95% plane fill, 414 stitch vias). Power is DRU-floored TRACKS on the
  signal layers (no dedicated power plane on 6L); switch nodes are tight
  track-only islands, no pour.

Scaling notes: add ADC channels by widening the CENTER band along the long
axis (keep the analog LDO central); add ports by extending the NORTH repeat.
The failure mode to watch (measured on the sealed instance, dispositioned
P1): the USB-HS pair and the long analog-input runs are the two hardest
routes — reserve the USB pair a short F.Cu-only lane from the port to the
MCU BEFORE placing the port bank, and keep balanced-audio input legs short
and symmetric rather than letting one leg wander the 176mm board.

---

_No other class has shipped enough boards to earn an archetype yet.
Candidates when they do: sensor-chain (cook-loadcell family),
mcu-hub (cook-hub). Found them from the sealed floorplans, not memory._
