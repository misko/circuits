# contract: 06_build/

**Purpose** — everything a tool can regenerate. Disposable by definition.
`rm -rf 06_build/` must always be safe.

**Mutability** — free. **Gitignored in its entirety** except this file and
explicit stage-checkpoint certificates.

## Allowed

| Path | What | TTL |
|---|---|---|
| `renders/**` | PNG/SVG/PDF of schematic and board | regenerate |
| `netlists/**` | exported netlists | regenerate |
| `drc/**` | DRC/ERC/audit reports (`gate.json` = the current gate result) | regenerate |
| `route/**` | KRT routing chain inputs/outputs (`r0..rN`, `taps_*.kicad_pcb`) | regenerate (needs KiCadRoutingTools) |
| `fab/**` | JLC export: gerbers, `bom.csv` (carries LCSC codes between runs), `cpl.csv`, zip — the CONTRACT's names, so a seal COPIES rather than renames (07_releases/contracts.md requires `fab/bom.csv` + `fab/cpl.csv`) | regenerate; bom LCSC column is the seed store |
| `pdf/**` | release PDF set + PNG verification renders | regenerate |
| `cache/**` | **volatile market data**: stock, price, distributor attrs | hours |
| `proof/**` | regenerated candidate boards for comparison against the sealed `04_kicad` (never written back) | regenerate |
| `twin/**` | jlc_twin fetch/compare workspace | regenerate |
| `tmp/**` | scratch workspace for in-flight stage work | regenerate |
| `pin_review/**` `pin_audit/**` | fresh-context pin-review dossiers + verdicts (either spelling; boards have used both) | regenerate |
| `verification/**` | **the SEAL STAGING AREA** — every gate's evidence, written here and COPIED into `07_releases/<ver>/verification/` at seal time. It had no row until 2026-07-31 despite being live on a shipping board (smc0985-cooksense carries 27 files here), because `--projects`' exit code was never read. Same names as the sealed copy, so the seal COPIES and never renames — see the `fab/**` row for what a rename costs | regenerate |
| `checkpoints/*.json` | tracked stage-boundary certificate over exact artifact/tool/source hashes; lets a later task resume without rerunning an expensive or human-reviewed producer | regenerate only by deliberately reopening that stage |
| `audit_<date>/**` | a dated one-off audit workspace (`audit_2026-07-19/`, `pin_audit_fresh_<date>/`) — a snapshot of a re-gate, kept until its findings are dispositioned into `08_reviews/` | regenerate |
| `easyeda_cache/**` | easyeda2kicad model cache (tool drops it in CWD — keep it HERE, not project root; usb-hub-3s 2026-07-21) | regenerate |
| `reads_outside_root.log` | clean-room runs: every out-of-root read, path + reason (toolchain-only at the end) | keep for the run's audit |
| `rebuild.sh` `policy_audit.md` `policy_erc.json` `policy_drc.json` | orchestration + audit outputs at build root | regenerate |
| `render/**` | render outputs (either spelling; boards have used both) | regenerate |
| `*.log` `*.rpt` `*.csv` `*.json` `*.md` `*.net` `*.step` `*.png` `*.svg` `*.sh` | loose build-root artifacts — the tree is DISPOSABLE; structure lives in the subdirs above | regenerate |
| `build_provenance.json` | canon **M-FRESH**: the per-run build witness written by `build_provenance.py stamp` and completed by `verify` (`run_id`, `started_ns`, `src_fingerprint` + the file LIST behind it, `board`/`tsx`, then `artifact`/`artifact_sha256`/`producer`). It lives HERE, and that placement is load-bearing: `rm -rf 06_build/` is always legal, so "no record" means exactly "no evidence this board was built", which `audit` reports as `F-NORUN` rather than as a pass | regenerate (rerun `03_src/rebuild_all.sh`) |
| `contracts.md` | this file | |

## Why `cache/` matters

Volatile lookups (JLC stock, LCSC attributes, distributor pricing) are cheap
per call but add up: one session fetched attributes for 287 parts at ~1.2s
each and left them in a SESSION-scratch directory, so the next session would
pay all ~6 minutes again. Cache them here, keyed by query, with a
`fetched_at` — and **re-fetch before ordering regardless**, because stock
moves and a stale number is worse than no number.

Never promote anything from `cache/` into `02_parts/`. Facts are permanent;
market data is not.

## Forbidden

- Anything unregenerable. If `rm -rf 06_build/` would lose information, that
  information is in the wrong folder.
- Committing anything here except this contract and `checkpoints/*.json`.
- Treating a cached stock number as truth at order time.

## Validate

- `.gitignore` covers `06_build/` and only re-includes `contracts.md` plus
  `checkpoints/*.json`
- every `cache/` entry carries a `fetched_at`
- deleting `06_build/` and re-running the generators + exports reproduces it

## Repair

- Tracked file in `06_build/` → decide: regenerable (delete + gitignore) or not
  (move to `03_src/`, `01_docs/`, `02_parts/`, or `07_releases/`).
- Cache entry with no timestamp → delete; unknown age is unusable.
