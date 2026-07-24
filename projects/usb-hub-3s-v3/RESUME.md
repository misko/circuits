# RESUME — usb-hub-3s-v3

**Stopped:** 2026-07-23 ~18:55, mid-v1.3 fix pass, on hitting the Fable-5 session quota
(resets 8:10pm America/Los_Angeles). All state is committed or staged in the tree.

## Where it stands
- **v1.0 / v1.1 / v1.2** — all sealed, all **SUPERSEDED / DO-NOT-ORDER**. There is **no
  currently-orderable release**. (v1.1 + v1.2 killed by external reviews; v1.0 the old baseline.)
- **v1.3** — fix pass IN PROGRESS. Gate (i) committed (`ecd82c0`); a release is **STAGED** at
  `07_releases/v1.3-2026-07-23/` (37 files) with the tree **DIRTY/uncommitted** (the orchestrator
  was to verify + commit). Beacon: `01_docs/STATUS.md` (stage `v1.3-fix-gate-ii`, state `blocked`).

## What v1.3 already fixed (verified)
- **R12** wrong-part (the v1.2 order blocker): C2933210 = 3.74k → replaced with **C2984354**
  (Viking AR03BTCX4121, catalog-verified 4.12k 0.1%), baked in the tsx by MPN. Setpoint re-derived
  vs the real Q6+F2 path (eFuse model removed); E-MARGIN passes (640 > 528 mV).
- **D5** directionality: C140903 was catalog-BIDIRECTIONAL → replaced with **C113976** (SMBJ6.0A
  unidirectional, same footprint).
- **OV decision** recorded (BRIEF A3/D3): **Option 2** — discrete TVS+PPTC as SECONDARY protection,
  supervised-prototype/replaceable-Pi context, NO active OVP/SCR; escalation boundary recorded
  verbatim. ORDER_README carries the bench-qualification tests as required pre-Pi gates. SW1 off-CPL.
- Gate (ii): board DRC 0/0/0; twin exit 0.

## BLOCKER before v1.3 can seal
- **R30 wrong-part** (found late, by the semantic-BOM gate seeding): **C2933195 = catalog 3.09kΩ but
  LABELED 100kΩ** — Q6's gate pull-up (QG→PMID). Functional but wrong-value (wastes ~4mA when ON).
  The staged v1.3 BOM fixed ONLY R12+D5, **not R30** (the staged "M-BOM PASS" is the OLD identity
  check, blind to value). v1.2's SUPERSEDED addendum `688a8af` already notes R30.
  **FIX:** assign a catalog-verified 100k 0603, bake the LCSC in tsx like R12, re-check Q6 gate-drive
  margins, re-run gate (ii).

## Next steps to seal v1.3
1. Fix R30 (above) → re-run the board/artifact regen (gate ii).
2. Merge the **semantic M-BOM gate** (branch `worktree-agent-aee58d73b4cb57970` HEAD `6ca2298`;
   accepted — fails sealed v1.2 naming R12) → run it on v1.3's BOM; must be CLEAN (no R12/R30/other
   value mismatch). Also merge the compute-discipline layer (`worktree-agent-a269ec8c0bed3bf6d` `544cf94`).
3. **Scoped** fresh red-team (checker≠checked) on the discrete-protection + R30 change (targeted, not a
   new full 5-lens fan-out — per the verification-scoping rule).
4. Independent seal-verify: DRC 0/0/0 + MANIFEST sha256 self-check + `git check-ignore` sweep +
   the live **freshness gate** (`skills/jlcpcb-fab/scripts/release_freshness_check.py`) + semantic M-BOM.
5. 2-commit seal (source S → stamp MANIFEST git_sha=S/git_dirty:false → seal commit) + write
   SUPERSEDED.md on v1.2.

## Watch-outs
- Do NOT reseal — v1.2 is immutable; v1.3 is a NEW release.
- kicad-cli regenerates `source/*.kicad_prl` on any board-open — strip gitignored files LAST before the
  seal sweep (bit pod-v2 + v1.2; see task #45).
- Master coordination state: `scratchpad/ORCHESTRATION_STATE.md`. Task list persists (#48 = this board).
