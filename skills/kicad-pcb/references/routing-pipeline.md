# The canonical routing pipeline

Proven end-to-end on a 136-part, 100×65 mm, 4-layer board: 0 unconnected,
0 shorts, 0 fab-illegal copper. Order is load-bearing — each deviation below
reintroduces a failure that was already debugged once.

## Step 0 (BEFORE anything routes): ampacity guardrails

Define current-tiered netclasses (SWITCH_NODE / PWR_RAIL / VBUS / signal)
in `.kicad_pro` and per-class `track_width (min ...)` rules in
`.kicad_dru`. Plan >1A trunks as priority-N F.Cu pours, not tracks.
Sub-floor tap corridors (gate-drive returns) get named rule areas with a
scoped lower floor. With this in place, every later routing pass —
including KRT's thin pass — is gated by standard DRC. Retrofit cost when
skipped: a full repair campaign (SPF 2026-07: both 6A switch nodes shipped
as 0.15mm until a manual walk caught them).

## Steps

1. **Start from a TRACK-FREE, UNFILLED pcbnew board.** KRT mis-parses
   filled zones AND pcbnew-dialect tracks, then routes straight through
   existing copper (400+ crossings observed twice). Strip tracks
   (`board.Delete`), `z.UnFill()` every zone, save.
2. **Keepouts.** Draw `gr_poly` squares on `User.2` around mounting holes
   (screw-head radius ~3.35 mm); pass `--keepout --keepout-layer User.2`
   to every KRT invocation. Edge strips only where no connector pads live.
3. **Fanout FIRST.** `bga_fanout.py` each fine-pitch IC (VQFN/BGA) before
   any routing claims the escape lanes:
   ```
   python3 ~/gits/KiCadRoutingTools/bga_fanout.py BOARD --output BOARD \
     --component U1 --layers F.Cu B.Cu --track-width 0.15 --clearance 0.13 \
     --via-size 0.45 --via-drill 0.2 --fab-tier advanced
   ```
   Peripheral 0.4 mm QFNs cannot be fanned out or routed between pads at
   any legal geometry — their nets go in the hardest-first set instead
   (and the durable fix is a larger package).
4. **Hardest-first thin pass.** Route the escape-bound / historically
   failing nets on the empty board at 0.15 track / 0.13 clearance /
   0.45-0.2 vias (`--fab-tier advanced`, `--max-iterations 500000`).
   Don't over-stuff one wave: too many hard nets compete; two waves
   beat one big one.
5. **Main pass.** Everything else at standard geometry. The full
   invocation (THE workhorse command — entry point is `route.py`):
   ```
   python3 ~/gits/KiCadRoutingTools/route.py BOARD.kicad_pcb \
     --output OUT.kicad_pcb --layers F.Cu B.Cu \
     --clearance 0.2 --track-width 0.3 --via-size 0.6 --via-drill 0.3 \
     --fab-tier standard --keepout --keepout-layer User.2 \
     --max-iterations 300000 \
     --power-nets VSW 5V_A 5V_B --power-nets-widths 1.2 1.2 1.2
   ```
   `--power-nets` and `--power-nets-widths` are PARALLEL lists (one width
   per net). The hardest-first/reconcile passes are the same command with
   `--nets ...`, `--track-width 0.15 --clearance 0.13 --via-size 0.45
   --via-drill 0.2 --fab-tier advanced --max-iterations 500000`.
   Each `--output` file is a **chain file**: KRT-dialect, re-parseable by
   KRT, the ONLY safe input for repair passes. Name them sequentially
   (`pb_s1`, `pb_s2`, ...) and keep every one until the board ships.
6. **Thin reconciliation.** `--nets <fails>` at the thin geometry. Nets
   served by planes/pours (GND to an inner plane, rails with pours) often
   "fail" in KRT but resolve at zone fill — judge by DRC, not KRT's tally.
7. **Import once, then ground truth.** Textual import of segments+vias into
   the pcbnew base (see `scripts/import_krt.py`), `ZONE_FILLER.Fill`, save,
   then classified DRC + audit gates. KRT's JSON summary is NOT the truth;
   the filled board's DRC is.

## Repairing a routed board

Never re-run KRT on the imported pcbnew board. Instead run
`--nets NET1 NET2 --rip-existing-nets NET3` on the **KRT-dialect chain
file** from the previous pass (which it parses perfectly), then re-import
everything into the clean base in one shot.

For last-mile gaps KRT can't close, use the verified micro-tools
(`scripts/pcb_toolkit.py`): blocker listing → rip single track-only
blockers → direct/L/Z join scan → verified A* → re-route ripped nets.
Every added segment/via must pass the exact-collide check; re-run the
green check after every edit including your own fixes.

## Decision rule: router ordering vs package swap

When airlines cluster at a fine-pitch part, split them: nets that fail
because escape LANES were consumed are fixed by fanout-first +
hardest-first (free); nets that must pass between pads or need a via where
no legal landing zone exists are fixed only by the package swap or a
human. On the reference board: 14 airlines at the QFN -> ~10 were
ordering-fixable, 4-5 were mathematically stuck -> SOIC swap closed all.
Run the (free) ordering fix first; swap the package if stragglers survive.

## Empirics worth trusting (provenance: SPF power board, 2026-07)

- More layers do NOT fix routing failures that are escape-bound: bare-board
  (all planes removed) and spread-out placements plateaued at the same
  completion. The ceiling is pad-escape geometry + via landing zones.
- Smaller vias (0.45/0.2 advanced tier) did NOT beat 0.6/0.3 at the router
  level either — the stragglers were lane-blocked, not via-blocked.
- Hardest-first ordering closed 21/22 nets that retry-based strategies
  never closed. Fanout-first closed the rest.
- A finished dense board typically carries fab-legal margin items
  (0.10–0.20 mm spacings from thin passes). Classify, don't panic
  (see drc-discipline.md).

## Loop economics: quick vs the full cycle, and when grind_driver escalates

Measured on the v4 usb-hub-3s clean-room canary (112 parts, 2026-07-21):
one FULL cycle — rebuild chain + `kicad-cli` severity-all DRC + a frontier
agent reading the report — runs **~8-10 minutes**, and the whole grind
historically burned **~500k tokens per board**. A routing iteration only
ever changes unconnected + copper clearance/track_width, so paying the
full cycle per iteration is waste.

The cheap loop: `route_and_stitch_generic.py quick` on the post-import,
pre-stitch board — pcbnew ratsnest unconnected (split routed vs
pour-deferred nets) + clearance/track_width from an unfilled-zone DRC.
**Measured 0.65 s** on cook-loadcell; expect seconds-to-a-minute on a
dense 4-layer board. Iterate routing against `quick`; run the full gate
once quick is clean. quick is a loop tool — the severity-all 0/0/0 full
DRC after stitch stays the only release gate.

`scripts/grind_driver.py` mechanizes the loop between those two levels,
with `references/grind_fixes.yaml` as the class table. It AUTO-applies
only conservatively-safe generator reruns (the v4 batch classes:
track_width wave/class alignment, silk floor normalization,
fp-lib-table emission, refdes de-collision) and ESCALATES everything else
into `06_build/grind_escalation.md` — clearance clusters and opens are
design work, and the D-BACK ladder maps them to the owning stage. Hard
stops (exit codes): 0 = full 0/0/0; 2 = table-escalate; 3 = novel class;
4 = D-BACK (3 consecutive cycles without total-count improvement) or the
--max-cycles cap. The driver is deliberately UNABLE to loop forever; when
it exits nonzero, the expensive agent is summoned ONCE, with counts and
samples, instead of once per cycle.
