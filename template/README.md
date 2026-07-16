# Board project template

Copy this directory to start a board:

```bash
cp -r circuits/template my-board && cd my-board
git init && git add -A && git commit -m "init from template"
```

Then read `contracts.md` at the root, and each folder's `contracts.md` as you
enter it.

## What the contracts are for

Every folder carries a `contracts.md` stating: its purpose, its mutability,
the file types it allows, the structure of each, and — the useful part —
**how to VALIDATE and REPAIR** what is there.

They exist because conventions that live only in a person's head do not
survive contact with a second person, a later session, or an agent. A
contract is checkable. An agent entering `parts/` can read one file and know
whether the folder is conformant, and how to fix it if not.

Each contract's rules are anchored to a real failure from a real board — not
taste. The `Forbidden` sections in particular are a list of things that
already went wrong once.

## The shape

```
docs/        human truth: architecture, math, decisions, changelog   [hand]
src/         THE source: generators, rules/nets.yaml, libs           [hand]
parts/       per-MPN datasheet + extracted facts                     [hand, once]
kicad/       the KiCad project — GENERATED, committed for diffs      [generated]
firmware/    code that runs on the board                             [hand]
build/       anything regenerable — gitignored, rm -rf safe          [tools]
releases/    one IMMUTABLE dir per fab order, with a MANIFEST        [write once]
```

Three ideas do the heavy lifting:

1. **Organize by who writes it and whether it may change.** Mixing source,
   derived, and release artifacts is the root cause of most structural pain.
2. **Iterations live in git, never in filenames.** `board_v2.kicad_pcb` beside
   `board.kicad_pcb` is a defect. Revisions are tags + a CHANGELOG line;
   only a *fab order* gets a folder.
3. **Intent and enforcement come from one file.** `src/rules/nets.yaml` says
   both "SW_A is a 6A hot loop, pour it" and "min 0.3mm" — and it generates
   the DRC rules. When those lived apart, a 6A node got routed at 0.15mm and
   DRC had no basis to object.
