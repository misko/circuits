# learnings — cooksense v1.1 routing (188x92 comb), 2026-07-24

1. **Deterministic seed stubs are REALIZATION-COUPLED.** Three stub
   derivations (U_EXP.9 v1.0-carryover, C_ULNB x2) each collided the NEXT
   race's copper. Rules that held: (a) never carry stub coords across a
   placement change; (b) derive sites with the pass's OWN primitives
   (tk.via_site_ok + tk.collides) — an approximate scanner accepted a site
   via_site_ok refused (RAIL_EN_B B.Cu); (c) prefer a PLACEMENT fix (seed the
   pad into serviceable copper) over a stub when a re-race is already needed.
   candidate-canon: yes (kicad-pcb skill: stub-derivation protocol)
2. **Three races, same finding class = the D-BACK trigger works.** Each race
   stranded a different plane-net passive in the same escape funnel
   (x128-136/y82-92). The placement fix (move the passive strip out of the
   funnel) ended the class; stub whack-a-mole did not. candidate-canon: no
   (instance of existing D-BACK canon)
3. **Post-refill dangling-via prune belongs at the END of the chain.**
   prune_stitch_dangling runs mid-stitch; the final refill shifted fills and
   left 2-4 In1-only rescue vias dangling per realization. The 6b step (fill,
   then count DISTINCT connected layers: segment-true track touch, HitTest
   via-in-pad, filled-poly containment) is generic and idempotent. Two bugs
   paid for: bbox pad-containment kept useless vias inside big THT pad
   bboxes; endpoint-only track touch deleted a legit mid-track layer-swap
   via. candidate-canon: yes (harvest 6b into route_and_stitch_generic as a
   final pass)
4. **JLC stock API returns transient 0s.** C25744 (basic 10k 0402) read
   stock=0 twice, then 12,622 on a direct probe minutes later. Do not
   substitute on a single reading; re-probe before acting. candidate-canon:
   yes (jlc_stock_check: retry a 0-stock reading before failing)
