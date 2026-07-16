# pcbnew Python scripting — gotchas and patterns

All verified on KiCad 7.0.x standalone (`/usr/bin/python3`, `import pcbnew`).

## Crash & noise patterns

- **Segfault after `board.Remove(t)`** followed by geometry ops or Save —
  and SWIG floods stderr with "memory leak of type 'PCB_TRACK'" at exit.
  Pattern: do removals, `board.Save()`, then do EVERYTHING ELSE in a fresh
  process on the reloaded file. Write script results to a file
  (`print(..., file=out)`) because the exit crash eats buffered stdout;
  run heredocs as `python3 - >/dev/null 2>&1 <<'EOF' || true` and `cat`
  the result file after. `board.Delete(t)` is the milder call but the
  save/reload discipline still applies.
- **`ZONE_FILLER(board).Fill()` / `WriteDRCReport` on a heavily-modified
  in-memory board** can segfault: save, reload, then fill/DRC.

## API correctness

- `GetNetsByName()` is broken standalone → use `board.FindNet(name)`
  (check `GetNetCode() > 0`).
- `LoadBoard()` reads the sibling `.kicad_pro` (netclasses, severities)
  and `.kicad_dru` — rule changes live in the PROJECT file, so committing
  a "board rules change" means committing `.kicad_pro`.
- Netclass edit: `board.GetAllNetClasses()` → `nc.SetClearance(FromMM(x))`.
- Design-rule floors: `ds = board.GetDesignSettings()`; `m_MinClearance`,
  `m_TrackMinWidth`, `m_ViasMinSize`, `m_MinThroughDrill`,
  `m_ViasMinAnnularWidth`, `m_HoleClearance`, `m_HoleToHoleMin`,
  `m_CopperEdgeClearance`.
- Exact collision: `SHAPE_SEGMENT(VECTOR2I_MM(x1,y1), VECTOR2I_MM(x2,y2),
  FromMM(width)).Collide(item.GetEffectiveShape(layer), FromMM(clearance))`.
  Pads: `p.GetEffectiveShape(layer)` with `p.FlashLayer(layer)` guard.
  NEVER approximate pads as circles of max(sx,sy)/2 — elongated pads make
  everything look blocked (or worse, the opposite mistake passes crossings).
- Footprint swap in place: `FootprintLoad(libdir, name)`, set reference/
  value, `board.Add`, re-`SetNet` each pad from the captured old mapping,
  `board.Remove(old)`. Pin NUMBERS differ between packages of the same
  part — remap via port names against the datasheet, and cross-check one
  anchor pin (e.g., GND) against the old netlist.
- Per-pad zone connection: `pad.SetZoneConnection(pcbnew.ZONE_CONNECTION_FULL)`
  — the correct fix for starved_thermal (spoke-count) items.
- Zone island policy: `zone.SetIslandRemovalMode(...)` — but pad-attached
  islands are NOT "isolated" to the filler and survive; see drc-discipline.
- Silk/ref text: `f.Reference().SetPosition/.SetTextSize/.SetVisible` —
  de-collide against BOTH other ref boxes and footprint bboxes; hiding
  refs in hopeless zones is legitimate (identity lives on fab layer + CPL).

## Headless vs GUI

- **Zone fills differ subtly.** `starved_thermal` may be invisible to a
  headless `WriteDRCReport` yet real in the GUI. Treat GUI DRC as
  authoritative for fill-dependent checks; ask the user to re-run it after
  headless changes, and to close+reopen (or Revert) since the file changed
  on disk.
- KiCad 7's `kicad-cli` has `sch export netlist|svg|pdf` but NO `pcb drc`.
- Rasterize SVG with `rsvg-convert -w 6000`, crop with PIL for review.

## Shell discipline

- Background/long-lived shells drift cwd — use absolute paths ALWAYS.
- Timestamps in filenames beat overwriting; keep chain files (`pb_s1`,
  `pb_s2`…) so any stage can be re-imported or diffed.
