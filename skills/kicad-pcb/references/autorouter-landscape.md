# Autorouter & placement tool landscape (empirical, 2026-07)

Head-to-head data from one real 136-part 4-layer board. Re-verify numbers
if tools have had major releases since.

| Tool | Routing completion | Time | Cost | Verdict |
|---|---|---|---|---|
| KiCadRoutingTools (KRT) | ~85% naive; **100% with fanout-first + hardest-first** | seconds–minutes | free | THE workhorse |
| freerouting (all of 1.x/2.1/2.2.x) | n/a | n/a | free | broken matrix, see below |
| DeepPCB cloud (routing) | ~23% | 23 min | ~12 credits | not competitive |
| DeepPCB cloud (placement) | n/a (placement) | 12 min | ~12 credits | genuinely good — see below |
| custom A*/maze (manhattan) | plateaued early | hours | free | superseded by KRT |
| KiCad built-in | none exists | — | — | interactive push-and-shove only |

## KRT (github drandyhaas/KiCadRoutingTools)

- Permanent clone: `~/gits/KiCadRoutingTools`. Never rely on /tmp copies.
- Needs `shapely` + a one-time `build_router.py` (Rust core).
- Writes KiCad-9 dialect that KiCad 7 cannot open → textual import
  (`scripts/import_krt.py`).
- **Parser bug (critical):** given a pcbnew-saved board containing tracks
  or filled zones, KRT drops some copper from its obstacle map and routes
  straight through it, while reporting success. Feed it only track-free
  pcbnew boards or its own outputs. Chain passes on ITS files.
- `--power-nets` and `--power-nets-widths` are parallel lists (one width
  per net, repeated).
- Has `--nets`, `--rip-existing-nets`, `--keepout/--keepout-layer User.2`,
  `--guide-corridor`, `bga_fanout.py`, and DRC/analysis helpers.
- Its JSON_SUMMARY tail may cover only a reconciliation subset — grep the
  FIRST summary for the full tally, and trust only import+DRC ground truth.

## freerouting: why it's a dead end (tested exhaustively)

Version matrix all broken for KiCad-7 4-layer DSN: 1.x parser crashes
unless `Cust` padstacks are stripped (plus needs xvfb); 2.1 routes but
exports an EMPTY .ses; 2.2.x reader NPEs. Java version chaos on top
(class file 52/55/61/65/69). Also: an exported SES contains the FULL
wiring — wipe before import or you duplicate. Don't sink time here again.

## DeepPCB (cloud, api.deeppcb.ai) — placement yes, routing no

Placement result was real: fitness 0.9936, respected a 54-part protection
map exactly, and its placement measurably improved routability (42→28
unconnected at the time). BUT it optimizes ratlines only — it stranded
decoupling caps up to 66 mm from their ICs. Mandatory post-pass: snap
electrically-critical satellites back to anchors (see
placement-and-proximity.md). API details + billing traps: deeppcb-api.md.

## Escape geometry (why routers fail and tuning won't help)

To pass between two pads: `track + 2×clearance ≤ pad gap`.
0.4 mm pitch QFN → ~0.2 mm gaps; even at JLC's absolute 4L floors
(0.076 track / 0.10 clearance) you need 0.276 mm. Physically closed.
Each pin escapes radially only, so a QFN's escape count is hard-capped;
neighboring congestion eats it fast. Vias need a clear landing zone of
roughly `via_dia/2 + clearance` in all directions (~0.85 mm for 0.45/0.2 at
0.13) — dense quadrants simply run out of legal via sites.

Levers in order of value when escapes saturate:
1. Interactive human hour (push-and-shove necking) — always works.
2. **Package change** (0.4 mm QFN → SOIC/TSSOP): eliminates the problem
   class; pin remap via port names keeps firmware unchanged.
3. KRT fanout-first + hardest-first (this got us from 14 airlines to 0
   after the package swap; before it, 4-5 nets were mathematically stuck).
4. Micro-moves of small passives to open via sites (copper-aware!).
5. More layers: LAST — verified useless for escape-bound failures.
