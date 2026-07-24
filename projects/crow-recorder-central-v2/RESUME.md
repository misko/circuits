# RESUME — crow-recorder-central-v2 (6-layer CENTRAL, the crow pair's other half)

**Stopped:** 2026-07-23 ~18:55, mid P0 fix pass, on the Fable-5 session quota (resets 8:10pm PT).
Sibling **crow-mic-pod-v2 is SEALED** — sealing this completes the pair.

## Where it stands
- **Routing gate GREEN + committed** (`3bee9ec`): DRC 0/0/0 (from 79/8 at session start). The prior
  "placement-density D-BACK" was mostly a generator config artifact (`try_via hole_to_copper=0.205`
  stricter than the 0.15 board floor — see task #47).
- **Reproducibility driver committed** (`03_src/rebuild_reuse.sh`): reproduces 0/0/0 from committed
  source (deterministic promoted-chain import; also fixed `--schematic-parity` which had been silently
  skipping). Beacon: `01_docs/STATUS.md`. Journal: `01_docs/journal/routing.md`.
- **Fresh red-team ran → DO-NOT-ORDER**, one confirmed **P0**.

## The P0 (fix pass IN PROGRESS, uncommitted tree)
- **P5VA_4** — port-4 +5V-audio was **merged into an audio signal net by board-generation net-binding**
  (authoring is correct; the board-side net-bind collapsed it). Port 4's pods would get NO power rail.
  Invisible to DRC (a consistently-wrong binding routes "cleanly"); caught by the red-team's per-pad port check.
- The lead was mid-rebuild ("rebuild with the pours + per-port silk and measure").

## Next steps to seal
1. **Root-cause the P5VA_4 net-bind** + re-verify **all 8 audio ports pin-for-pin**; add a **permanent
   per-pad port check** so this class can never pass silently again.
2. The **P1 set** the red-team raised: U7 PFM-vs-ADR, 5V ampacity / netclasses-in-chain + beep-bus PTC,
   layout spans, **per-port NOT-ETHERNET silk**, the PoE-class ADR (shares pod-v2's RJ45-everywhere PoE
   exposure — carry the same accepted-waiver posture).
3. **GUARD — do NOT "fix" Q1's reverse-polarity protection; it is CORRECT as-built** (a rejected finding).
4. Rebuild → DRC 0/0/0 → **scoped** re-verify (targeted fix-confirmation + one integrated fresh lens) →
   independent seal-verify (DRC + MANIFEST + ignore-sweep + freshness gate + semantic M-BOM) → seal
   `crow-recorder-central-v2-v1.0`.

## Watch-outs
- **Schematic-stage non-determinism** (pre-existing, skills-frozen): `tsci build` regenerates a divergent
  `.kicad_sch` (UUID/ordering churn; connectivity STABLE per count_parity) and `kicad_sch_parity.py`
  crashes vs the sealed board. Disposition at seal: pin the committed `.kicad_sch` as canonical +
  rely on count_parity/netlist-parity; the parity-script crash is 2-strike (also hit v1.3) — a harvest item.
- Converter `tie:GND` emission check was run CLEAN here (no isolated domain; RJ45 shield = intended bond-at-central).
- No committed board *seal* driver yet beyond `rebuild_reuse.sh`. Task #36 (this board), #42, #47.
