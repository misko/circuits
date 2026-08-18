# Review, release, and publication procedure

Use this procedure after the first judgeable schematic, before routing, and
for every release/publication claim. Fabrication mechanics remain owned by the
JLCPCB skill; KiCad geometry mechanics remain owned by the KiCad skill.

## Contents

1. Review at first judgeable artifacts
2. Scope the verification battery
3. Build the pre-seal staging archive
4. Admit independent review evidence
5. Seal immutably
6. Publish fail-closed
7. Report and order-day status

Policy IDs owned by this procedure: `M-REV`, `PR-REVIEW`, and `P-PUBLISH`.

## 1. Review at first judgeable artifacts

Run human-readable review before expensive downstream work:

- At schematic: bind topology and schematic-readability reviews to the exact
  PDF, normalized netlist, parts bytes, and adopted rules.
- At placement: bind pin, layout, and render reviews to the exact track-free
  board and deterministic route-prep subject. Run same-camera render
  registration before asking a human to judge the render.
- At routed release: repeat fresh independent lenses against the exact staged
  source/fab artifacts.

Missing, stale, defective, interrupted, or unadopted evidence blocks. A
review-budget deadline produces an `INCOMPLETE` witness rather than extending
indefinitely. Resume after review through the checkpoint-aware driver; do not
rerun a nondeterministic producer solely to continue.

## 2. Scope the verification battery

Run the full battery once per material design state. For an initial release:

1. Run cheap deterministic gates first.
2. Run exact-source/fab identity and completeness gates.
3. Generate trustworthy twin/render evidence.
4. Launch independent pin, render, topology/ratings, and layout/power-integrity
   lenses where applicable.
5. Run the integrated policy audit after the witnesses exist.

For a fix-pass release, still run all cheap mechanical gates but limit human
review to every changed item plus one integrated fresh-context lens. A material
electrical, placement, routing, assembly, or mechanical change invalidates the
relevant previous witnesses.

Perform verification against a pre-seal staging archive. Do not review an
immutable release and then modify it; findings must cost an edit and rerun, not
a superseding release.

## 3. Build the pre-seal staging archive

The staged archive must be self-contained and include:

- `fab/`: exact manufacturer upload payload;
- `pdf/`: human schematic, PCB layers, and assembly drawing;
- `source/`: exact KiCad schematic/board, TSX, netlist, project libraries, and
  rule files needed to reopen/replot;
- `3d/`: STEP/GLTF where available, with absence stated;
- `verification/`: ERC/DRC/parity, policy, sourcing, assembly, rotation,
  model/twin, RF, review, and first-article evidence required by applicability;
- `ORDER_README.md`: manufacturing options, human uploader checks, assembly
  exceptions, sourcing state, and first-power procedure;
- `MANIFEST.txt`: SHA-256 for every archive file plus source commit and clean
  scoped input state.

Copy files; never symlink. Run a standalone-archive open/replot/DRC rehearsal
before sealing so absolute model/library paths and mutated archive source are
caught while the release is still staging.

Initialize the declaration before staging gates consume it:

```text
release_rehearsal.py init 07_releases/<version>-<date>
```

The command refuses to overwrite a manifest and writes a loud DRAFT,
DO-NOT-ORDER skeleton from the staged board and authoritative assembly
disposition. It is not a seal.

The definitive required file set and two-commit seal procedure live only in
`skills/pcb-design/templates/contracts/07_releases/contracts.md`. Do not create
a second seal algorithm here.

## 4. Admit independent review evidence

Each review commission names one immutable subject, one lens, exclusions,
checklist, output path, and deadline. The launcher enforces time. The witness
must contain parseable data:

```text
design_verdict: SOUND | DEFECTIVE | INCOMPLETE
order_verdict: ORDER | FIRST-ARTICLE-ONLY | DO-NOT-ORDER | BLOCKED-SOURCING
```

The seal reads `design_verdict`; order paperwork reads `order_verdict` and
cross-checks it against a fresh, exact-BOM JLCPCB `ALLOCATED` receipt. Catalog
stock is advisory and cannot support `ORDER`. Prose is not a verdict.
Archive accepted witnesses verbatim under `08_reviews/` with subject hashes and
copy the contract-named witnesses into staged verification.

A P0 blocks. Fix and re-gate. Record P1 items in the order/next-revision work
order and P2 items in the disposition ledger. An external review is evidence,
not permission to waive machine failures.

## 5. Seal immutably

Immediately before the normative two-commit procedure, run the same
publication-internal contract against mutable staging:

```text
release_rehearsal.py rehearse 07_releases/<version>-<date>
release_rehearsal.py seal 06_build/release_rehearsal/<release>.json \
  --output 06_build/release_rehearsal/<release>-seal-admission.json
```

Rehearsal composes required-release content, design/sourcing freshness and the
publication contract using `pcb_publication_gate.py --release`. Its receipt is
stored outside staging to avoid a self-referential manifest. Seal admission
refuses a rejected, incomplete, or byte-stale rehearsal and never commits or
publishes on the operator's behalf.

Follow the release contract's normative two-commit procedure:

1. Complete and verify staging.
2. Commit the exact live source state (`S`).
3. Stamp `MANIFEST.txt` with `git_sha: S` and clean scoped inputs.
4. Re-run release freshness and required gates on the stamped archive.
5. Create a seal commit that adds only the release directory.
6. Refresh the board status beacon to name the new live release.
7. Run the beacon checker after the seal commit.

A release is immutable. Corrections create a new version and mark the previous
release superseded. Select the contract-owned supersede mode matching the exact
delta; never substitute hand-written allow-identical waivers for a mechanical
assertion.

## 6. Publish fail-closed

Treat publish, merge-to-main, release, ship, and ready claims as sealed-state
requests unless the user explicitly asks for an unreviewed WIP. A WIP must say
so in its branch/PR and first-screen status and must not be merged into the
publication branch.

Immediately before a publication-branch push or merge, run:

```text
python3 skills/pcb-design/scripts/pcb_publication_gate.py \
  --base <publication-base-sha> --head <candidate-head-sha>
```

Require `P-PUBLISH PASS`. The gate must find every materially changed project,
its latest complete sealed release, existing gates, exact live/sealed board
identity, no material drift after the manifest source commit, and all required
accepted reviews. Zero required reviews is zero coverage and fails.

Repository protection should require this check and a pull request. A workflow
that runs only after an unprotected push can report a violation but cannot undo
publication.

## 7. Report and order-day status

Report:

- architecture/protection decisions and user assumptions;
- gate scoreboard with denominators;
- design and order verdicts;
- release path and source/seal commits;
- measured vs inherited claims;
- unresolved first-article, sourcing, uploader-preview, stackup/impedance,
  via-process, THT-assembly, BOM, and rotation items.

Use precise readiness language. `DRC 0/0/0`, a generated board, a fab export,
or a manifest proves only its own stage. If uploader previews, stackup values,
final allocation, or first-article evidence remain, state `DO-NOT-ORDER`,
`FIRST-ARTICLE-ONLY`, or `BLOCKED-SOURCING` as appropriate rather than calling
the board production-ready.
