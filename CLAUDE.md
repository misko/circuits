# circuits — project instructions for Claude

This repo designs PCBs from a brief to an orderable, verified JLCPCB release.
These rules are BINDING. They exist because each one was learned by paying for it.

## Where the canon lives

- `skills/kicad-pcb/references/design-policies.md` — the policy canon (S/P/R/M
  check IDs and the meta-principles). Read it before changing any gate.
- `docs/decisions/` — ADR-0001 (tscircuit authoring boundary) and ADR-0002
  (tscircuit-native pipeline). These govern; do not contradict them silently.
- `tests/README.md` — the testing contract. Read before touching tests.
- `skills/pcb-design/SKILL.md` — pipeline orchestration, stage by stage.
- `docs/generic-generator-proof.md` — what the generic backend is proven on.

There is deliberately no `docs/learnings.md` here: the hard-won conclusions live
in `design-policies.md`, the ADRs, and the commit bodies (which are written as
post-mortems — `git log` is a primary source, not just history).

## Immutability

- **Sealed `04_kicad/` and `07_releases/` are IMMUTABLE.** Never write to them,
  never retro-fill a sealed release. Open them read-only for comparison. All
  regenerated output goes to `06_build/proof/` or a NEW release version.
- A fix means a NEW release plus `SUPERSEDED.md` on the old one — never an edit.
- Never hand-edit `04_kicad/`. Fix the generator and rerun. Everything must be
  regenerable from `03_src/` + `03_tscircuit/` (canon M3).

## Build order (violating it produces a board that passes DRC and is wrong)

- Netclasses and ampacity floors are generated BEFORE routing (canon R1), and
  `generate_rules` runs **LAST** again after stitch/fill — pcbnew saves clobber
  netclasses.
- KiCad has **no autorouter**. Route with KRT (`~/gits/KiCadRoutingTools`):
  fanout-first, track-free board, import once, then promote the final chain file
  to `03_src/route/` and commit it.
- Auto/AI placement is blind to electrical proximity. A routing failure is
  usually a PLACEMENT problem — check net span lengths before tuning the router.
- DRC violations are CLASSIFIED, never counted. Gate is `kicad-cli pcb drc
  --severity-all --refill-zones --schematic-parity` = 0 violations / 0
  unconnected / 0 parity.

## Testing

- **Test the checkers, not just with them.** Every checker needs a KNOWN-BAD
  fixture that makes it FAIL. A gate that cannot fail is worthless — `jlc_twin`
  exited 0 on 11 unverified parts because nothing ever proved it could block.
- Assert PROPERTIES, never file bytes: KRT routing is stochastic and silk
  de-collision is order-dependent, so golden files break permanently.
- When you fix a bug in a gate, verify the new test goes RED against the
  pre-fix code (swap it back in, confirm, restore) and say so in the test.
- `tests/run_tests.sh` (add `--slow` for e2e board rebuilds).

## Evidence

- Checker and checked must not share a method (canon M1). A gate that validates
  its own output proves nothing.
- Report measured numbers. A partial result honestly reported is worth more than
  a passing claim. If parity is not 0, give the node-level diff.
- Waivers need evidence, not rationale. A waiver copied from another board is not
  a judgement — it is an inherited defect (this happened to the refdes-on-silk
  rule across three boards).

## Structure governance

- **Every folder is governed by a `contracts.md`** (its own, or the nearest
  ancestor's via explicit patterns) stating permitted names, how to audit,
  and expected structure. Machine-checked: `/usr/bin/python3
  scripts/contracts_audit.py` (run by the test suite). Root `contracts.md`
  states the coverage rule.
- **Skills never reference `projects/` paths.** Worked evidence a skill
  cites lives in `examples/` (append-only snapshots with PROVENANCE.md);
  project templates live in `skills/pcb-design/templates/` — one home each,
  no drift. Enforced as C-ISO by the same audit.

## Mechanics

- Use `/usr/bin/python3` for anything importing `pcbnew`.
- `bun`/`tsci` come from `~/.bun/bin`.
- Stage folders are number-prefixed: `01_docs 02_parts 03_src 03_tscircuit
  04_kicad 05_firmware 06_build 07_releases`. `03_tscircuit` shares stage 3 with
  `03_src` because both are hand-written source.
- Commit at each green gate. Do not push unless asked.
