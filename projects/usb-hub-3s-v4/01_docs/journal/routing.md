# Routing journal

## 2026-08-11 10:03 — start

- did: Entered Stage 4 from the pushed v0.4.0 placement checkpoint and ran the cheap rule, pad-launch and fabrication-tier preflights before invoking KRT.
- result: P-LAND stopped in 6.52 seconds on seven real land-to-class-width mismatches. No router ran and the hash-reviewed placement remained unchanged.
- next: Express only spatially bounded pad tapers and plane drops in the generic rule/tap contracts, then repeat the preflights before spending on route search.

## 2026-08-11 10:55 — iterate 1: pre-route fabrication and fill defects

- did: Regenerated the track-free board, refilled zones and ran full-severity DRC/parity while validating the declared advanced-tier via geometry.
- result: The cheap pre-route pass found three independent source defects before route search: a self-intersecting VIN zone that KiCad accepted but partially discarded during fill; 40 thermal holes encoded as footprint pads rather than fabrication vias; and via emitters screening against a hole-to-copper value below the adopted JLC advanced floor. All were repaired in shared, configuration-driven machinery with clean/known-bad tests. The final pre-route state passed tier preflight with 0 FAIL / 0 WARN and retained zero schematic-parity findings.
- next: Route only signal groups with KRT; leave the high-current rails to declared pours plus deterministic source/tap geometry.

## 2026-08-11 11:52 — iterate 2: all-dirty race and stale connectivity

- did: Ran the two-candidate bounded route race, imported the best candidate, replayed named power taps, stitched/fill-gated and compared the in-process result with a fresh KiCad CLI refill/DRC.
- result: The first race incorrectly returned success although every candidate retained routed opens; promotion was changed to require a CLEAN candidate and now clears stale `FINAL` state. A later in-process stitch gate said clean while fresh CLI DRC found 35 unconnected items and one dangling via. The stage added a forced save/fresh-interpreter reload, same-net island healing and stitch-via pruning, while retaining CLI refill plus schematic parity as authority.
- next: Add explicit plane drops for every SMD power landing that remains isolated after fresh fill, then rerun the race and the complete serialized chain.

## 2026-08-11 12:06 — iterate 3: clean promoted route

- did: Added four reviewed B.Cu output drops for U5/U6, ran the two-lane route race, promoted the exact clean winner, then replayed import, 20 named taps, 19 stitch/fill passes, rules-last and authoritative DRC.
- result: Both route candidates were CLEAN with zero routed opens and zero copper violations; the winner was promoted as `03_src/route/r4.kicad_pcb` at SHA-256 `c1cfade37cc50b02acb4796e09952f566b20e518c4077b143ebf3bf9c8fce56b`. The final board contains 379 imported segments, 10 imported/seed vias, 20 named taps, 30 pour zones and 129 saved filled-polygon blocks. Fresh read-back, critical-connectivity and full KiCad gates report 0 violations / 0 unconnected / 0 schematic-parity findings.
- next: Replay the promoted artifact through both canonical rebuild drivers and run the focused regression battery before freezing the checkpoint.

## 2026-08-11 12:17 — stuck: host resource pressure looked like a silent pipeline

- did: Re-ran the from-source driver under captured logging and inspected the live process tree plus kernel journal when the command appeared to end at `Generating circuit JSON...`.
- result: The driver had not ended: it continued through schematic conversion, board generation, route replay and DRC, but the host entered global OOM pressure with about 190 GiB active anonymous memory. Kernel logs show an unrelated 9.1 GiB Python process killed at 12:16:57 and repeated user-session OOM kills; a KiCad child temporarily sat in uninterruptible I/O. Once pressure cleared, the same run completed route replay, stitch in 3.143 seconds and DRC in 1.511 seconds at 0/0/0. The final stop was instead a loud M-STATE ledger defect: a passed architecture gate lacked required evidence paths.
- next: Record the missing maturity evidence, add bounded heartbeat/timeout coverage to the previously direct TSX producer step, and distinguish host-resource stalls from router work in future status reports.

## 2026-08-11 12:29 — finish and pause

- did: Put `tsci build` under the bounded runner, corrected the maturity ledger, made full/pinned exports share one electrical topology digest, replayed both drivers, plotted and visually inspected both outer copper layers, and ran the focused generator/review/template/tier/route regression suites.
- result: The final from-source run reports TSX build 8.960 seconds, stitch 3.029 seconds, DRC 1.636 seconds, M-PROV 4/4, GG 25/25 observed with no shadow/resolve finding, M-STATE 9/9 at DESIGN_CLEAN, and DRC 0/0/0. The pinned deterministic driver independently reports ROUTING GATE 0/0/0. The exact promoted route remains `c1cfade37cc5...`; top/bottom routed-review PNGs hash to `66f69374a498...` / `e49e8662ec7f...`. Visual inspection finds coherent cell-local signal escape, broad plane-fed power regions, clear connector mouths/mounting holes and no visually unexplained copper crossing; this is a routing-stage sanity lens, not the Stage 5 independent layout review.
- tests: MEASURED 230 passed, 0 failed and 2 slow tests intentionally skipped: generator 48, tier preflight 31, route/stitch 99, rebuild template 42 and pre-route review 10. Of these, 117 known-bad fixtures failed their gates as required.
- spent: MEASURED wall clock about 2 hours 26 minutes from the 10:03 stage marker. The successful two-lane route race took about 27 seconds; ordinary rebuild stages were seconds. Most time was diagnosis and source correction: the invalid VIN polygon, fabrication-via representation, stale in-process fill connectivity, orphaned power-plane landings, full/reuse netlist-hash contradiction and late maturity-ledger failure. One apparent multi-minute stall was host-wide OOM/I/O pressure, not router search.
- generalized: Validate polygons before KiCad; treat thermal via-in-pad as true fabrication vias without sacrificing library parity; route plane landings deterministically before stochastic search; promote only CLEAN route candidates; cross a serialization/process boundary after fill; keep CLI refill/parity authoritative; bind topology to electrical facts rather than export location; and put every quiet external producer behind the same heartbeat/deadline runner.
- instruction changes: IMP-005/006/007/009/010/011/012/013 are complete. IMP-008/014/016 remain proposed and IMP-015 remains implementing. The next canonical work should move all source-only schema/maturity checks ahead of TSX, reduce producer warning noise without losing logs, and separate orchestration metadata from adopted-design-rule review hashes.
- next: PAUSE. The board is DESIGN_CLEAN but deliberately DO-NOT-ORDER. On user continuation, Stage 5 must perform fresh exact routed-board pin/layout/render and adversarial power-integrity review before any fabrication/assembly or release claim.
