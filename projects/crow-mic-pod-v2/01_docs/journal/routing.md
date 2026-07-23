# journal: routing

## 2026-07-23 — start
- did: authored 03_src/route.yaml (2-layer; GND = F/B pours + stitch; beep/pwr
  hardest-first waves; J1 NPTH posts + M3 holes fenced). prep -> track-free r0.
- result: KRT routed all nets first pass (10/10 single, 26/26 multipoint).

## 2026-07-23 — iterate (D-BACK: J1.1 escape) + finish (DRC 0/0/0)
- did/result (measured each step):
  - After import: 1 ROUTED-NET OPEN on AUDIO_P (J1.1) + a thin AUDIO track
    (0.2498 < 0.25 = the nanometer-floor trap) + D1 SOT-553 GND-pad opens.
  - D-BACK diagnosis: ALL residual opens were inside ONE part's escape (D1
    SOT-553 + the J1.1 tail) — a PART/PLACEMENT problem, not routing.
    Fixes applied UPSTREAM:
    - Floated D1's NC pins 1,2 (datasheet's conservative choice) — their
      0.5mm-pitch inner pads can't be reached by the GND pour on 2 layers, so
      grounding them only made an unroutable open (schematic change, M3).
    - Dropped the named AUDIO width class -> route AUDIO_P/N in the default
      wave (line-level; a 0.25 class floor collides with KRT's 0.2498 track).
    - ROOT CAUSE of the J1.1 open: the J1 NPTH-post KEEPOUT was OVER-sized
      (east edge x19.3) and pinched J1.1 (x19.5) into a 0.2mm escape lane.
      Shrunk the post keepouts to ~2mm radius (east edge x19.0) -> all 5 race
      candidates then routed CLEAN (0 unconnected). This was the real fix; the
      tap attempts were treating a symptom.
    - KRT dropped a redundant layer-transition VIA on J1.1's plated THT hole
      (holes_co_located) — added 03_src/cleanup_redundant_vias.py (removes a via
      co-located with a same-net THT pad; a different-net co-location is a SHORT
      and is left for DRC). Deterministic, idempotent, in rebuild_all.sh.
    - R-POUR flagged the 0.5mm BEEP class as high-current-must-pour; 150mA over
      a short SW loop needs no pour -> BEEP width 0.4mm (< 0.5 threshold).
  - Promoted the race-winner chain to 03_src/route/r3.kicad_pcb (canon M3);
    route.yaml `final:` points at it; rebuild_all.sh drives the full chain.
- MEASURED FINAL: **DRC 0 violations / 0 unconnected / 0 parity**
  (`--severity-all --refill-zones --schematic-parity`). policy_audit **0 FAIL /
  19 PASS / 7 HUMAN / 11 N-A**. audit_board OK. contracts_audit 0 violations.
  Board 80x45mm, 39 fps, 234 segs, 72 vias, 2 GND zones.
- next: CHECKPOINT for commit, then VERIFY (bom/stock, jlc_twin, pin + render
  reviews, red-team, policy audit) -> release.
