> Adopted 2026-07-21 into crow-recorder-central from archived_projects/crow-array-central (provenance ADR 0011; re-verified by this project's own gates before any release). Original text follows.

# ADR-0010 — GND F.Cu/B.Cu pour micro-sliver "Zone unconnected" is waived (fill-engine artifact, zero electrical impact)

Status: accepted 2026-07-18. Companion to the D24 GND-bonding work and the
D19-D24 DRC-cleanup register.

## Context

After the root-cause GND bonding (gnd_rescue.py + close_gnd.py — every boxed
GND pad, incl. U3.7 via an I2C_SCL In3 reroute, U1.42, R34.2, U3.10/12/26,
tied to the In1/In4 solid reference planes), the `kicad-cli pcb drc
--severity-all --refill-zones` gate reports exactly **2 residual unconnected
items, BOTH of the form `Zone [GND] <-> Zone [GND]`** (F.Cu/B.Cu/In1/In4,
priority 0). **No component pad, track, or via is unconnected** — every one of
the 234 parts' GND pads is tied to the plane (verified: all unconnected items
are Zone-vs-Zone).

The disconnected copper is a set of **6 tiny (<1.4 mm) isolated GND pour
fill slivers** on F.Cu that the pour deposits in the dense escape pockets
(U3/PCM area x115-126 y59-93, tile-0 x71-63, R34 x104-118). Each sliver
carries **no pad, no via, no track** — it is unused floating copper that
cannot short or float any signal.

## Why it is irreducible via the generator toolchain (all attempted, live)

The `kicad-cli` DRC zone-fill engine produces these micro-slivers at
geometry that the scriptable `pcbnew.ZONE_FILLER.Fill()` does NOT reproduce,
so nothing computed from the Python fill can target the DRC's slivers:

- `SetIslandRemovalMode(ALWAYS)` — set on the F/B GND pours and saved
  (`island_removal_mode 0` present in the board file); neither the Python
  fill nor `kicad-cli --refill-zones` removes the slivers.
- Via-in-polygon bonding — a 0.30/0.15 GND via dropped INSIDE all 6
  Python-fill sliver polygons (via_site_ok green): count unchanged (the DRC
  fill's slivers are elsewhere).
- Keepout rule-areas over every sliver (tight 0.15 mm and generous 1.8 mm
  boxes): count unchanged.
- `SetMinThickness` 0.4/0.5 mm on the F/B pours: makes it WORSE (thicker min
  drops legitimate GND-pad thermal necks -> more unconnected).
- Removing the F/B GND pours entirely: 14 GND pads lose their pour
  connection -> far worse (the pours are load-bearing for those pads).
- A 405-via GND infill grid over the fragmenting regions: count unchanged.

The KiCad GUI's "remove islands" pass (which runs a fuller fill than the CLI)
is expected to clear these, but the release gate is the headless `kicad-cli`,
which does not.

## Decision

**Waive the 2 `Zone [GND] <-> Zone [GND]` unconnected items** as a headless-
fill-engine artifact. Evidence, recorded in `06_build/` and the release
`verification/`:

- 0 component pads/tracks/vias unconnected — full functional GND connectivity.
- The flagged copper is isolated sub-1.4 mm GND pour fill with no electrical
  function (no short path, no floated net) -> zero electrical and zero
  manufacturing impact (JLC builds isolated same-net pour copper without issue).
- Exhaustive generator-side remediation attempts above all fail to change the
  headless count.

The board's other DRC classes (clearance, dangling, holes, shorts, parity)
are driven to real 0 independently; this waiver covers ONLY the 2 Zone-vs-Zone
items.

## Consequence / follow-up

- If a future spin wants a literal headless 0 unconnected, the lever is a
  KiCad-GUI "remove islands" fill baked into the released board (manual step),
  or restricting the F/B GND pour outlines to exclude the dense escape
  pockets so the slivers never form. Neither changes electrical behaviour.
- Re-verify on the next KiCad point release: the CLI fill may gain island
  removal, retiring this waiver.
