# learnings: verify/seal — interposer v1.1 (harvest source, canon M9)

Written 2026-07-27 at the v1.1 re-seal. Each entry is a candidate for the
shared canon (`skills/kicad-pcb/references/design-policies.md`) or for a
generic script; `candidate-canon:` says whether I think it should be promoted.
No skill file is edited from here — two other agents are in `skills/` and
`tests/` concurrently.

---

## 1. A SHARED FOLDER IN A MULTI-BOARD PROJECT IS AN UNGRADED GATE INPUT

Four separate gates on this board were reading the OTHER board's artifact and
reporting a verdict about it. All four were invisible: none FAILED, they just
graded the wrong thing, and two of them graded the wrong thing while printing
PASS.

| gate | what it globbed | what it actually got |
|---|---|---|
| `export_jlc_package` / `bom_source_check` / `M-BOM` | `03_tscircuit/build/circuit.json` | COOKSENSE's 222-component circuit |
| `count_parity` | same | one leg silently absent (3 legs, not 4) |
| `net_label_survival` | `03_tscircuit/kicad/*.kicad_sch` sorted, first | cooksense's 100+ global labels |
| `assembly_coverage` (A-POP) | `release.resolve().parent.parent/03_src/rules/assembly.yaml` | cooksense's assembly.yaml |

**The most instructive one is the fab export.** v1.0's BOM has the RIGHT LCSC
for `J_KEY_MATRIX` — and it got there by reading the wrong board's circuit.json,
which happens to carry the same refdes for the same part. A correct output from
a wrong input is the worst possible outcome, because it looks like evidence the
input is right. The two 10FDZ-BT resolved blank for the same reason and that was
read as "these parts are uncoded" (true, but not for that reason).

**candidate-canon: YES.** ADR-0007's two-strike rule is now met — this is the
second multi-board project. The generic scripts should take an explicit
`--board` and resolve `03_tscircuit/build/<board>.circuit.json`,
`03_tscircuit/kicad/<board>.kicad_sch`, `06_build/netlists/<board>.net` and
`03_src/<board>/rules/` rather than globbing the first match. The
shadow-root workaround is a per-project hand-built symlink farm that every
multi-board project now has to reinvent, and it is 60 lines of `rebuild_all.sh`.

## 2. A SYMLINKED RELEASE DOES NOT SURVIVE `Path(...).resolve()`

Exposing `07_releases/interposer-*` into the shadow root as symlinks looked
correct and produced **18 spurious A-POP findings**, because
`assembly_coverage.discover()` does `t = Path(target).resolve()` and then
`root = t.parent.parent`. `resolve()` follows the symlink straight back out to
the shared project, so `root` became the real tree and the interposer release
was graded against cooksense's `assembly.yaml`.

Fix: each release in the shadow is a REAL directory whose CHILDREN are symlinks.
The bytes still come from the one real archive — nothing is copied, so there is
no second copy to drift — but the release PATH stays inside the shadow.

**candidate-canon: the general rule.** *A tool that resolves its input path
cannot be scoped by a symlink to that input.* Scope it one level deeper, or give
the tool an explicit flag. Worth a line in the project-structure reference.

## 3. "THE COPPER DID NOT MOVE" NEEDS A COMPARATOR, NOT A HASH

`generate_board_generic` mints fresh UUIDs on every run and emits footprints in
a different order, so the plotter numbers apertures differently and flashes them
in a different sequence. After a rebuild that changed only two footprint
ATTRIBUTES and one silk character, **every one of the eleven payload files
differed textually and the board's md5 changed.** `sha256`, `diff` and
`cmp` all say "changed" and none of them says WHAT.

What works: resolve every D-code to its aperture DEFINITION (shape +
parameters), every T-code to its diameter, and compare the MULTISET of
`(resolved-aperture, op, x, y)` tuples plus the G36..G37 region outlines.
Aperture numbering and statement order cancel out. On this respin that turned an
unreadable 11-file diff into:

    F_Cu 450 atoms, B_Cu 180, masks 84/52, pastes 12/0, PTH 55, NPTH 6
      -> ALL IDENTICAL
    Edge_Cuts  -> ONE segment's traversal direction reversed; identical as an
                  UNDIRECTED segment set
    F.Silk     -> 50 of 5368 atoms, ALL inside a 0.514 x 0.900 mm cell at
                  x 44.286-44.800, y 12.009-12.909 = the version digit

That last line is the one that matters: it does not just say "silk changed", it
says the change is one character in one place, which is a claim a reviewer can
falsify in ten seconds. The red-team lens then reproduced the whole table with
its OWN independently-written comparator.

**candidate-canon: YES.** `usb-hub-3s-v3 v1.10` and `crow-mic-pod-v2 v1.3` could
both assert byte-identity because their boards were md5-identical; a board that
must be REGENERATED (any source change touching the floorplan) cannot, and that
is the common case for a fix-pass. This belongs in `jlcpcb-fab/scripts/` beside
`fab_payload_census.py` as a `--against <other-release>` mode, and the F-PAYLOAD
family is exactly where it fits: it already parses gerber TEXT and shares no
method with the plotter.

## 4. THE AUDIT VIEW MUST BE REFRESHABLE WITHOUT REBUILDING THE SUBJECT

`rebuild_all.sh` built the single-board shadow root as step 0 of a full board
regeneration. So the only way to refresh the audit view — after staging the
release, which is exactly when you want to audit it — was to re-run
`generate_board_generic` and re-mint every UUID, invalidating the archive about
to be audited. `--shadow-only` splits the two.

**candidate-canon: mild.** Generic-script-level: any driver that builds a
scoping view as a side effect of a build should be able to build the view alone.

## 5. A MIS-NAMED REQUIRED ARTIFACT IS WORSE THAN A MISSING ONE

`release_required_check.py` (A-EVID) fails the SEALED v1.0 with 5 missing
artifacts, and two of them are not missing — they are mis-named:
`render_front_bare.png` / `render_back_bare.png` where the contract says
`render_top_bare.png` / `render_bottom_bare.png`, and `interposer.erc.json`
where it says `erc.json`. Both look present to a human reading the directory and
are invisible to every name-based check. A-EVID landed after that seal and would
have caught them.

**No canon change needed** — the gate already exists and works. Recorded because
it is the clearest example on this board of why the REQUIRED direction has to be
enforced separately from the ALLOWED direction.

## 6. A "FIX-PASS" ON THE ASSEMBLY PAYLOAD IS STILL A FULL MECHANICAL PASS

Canon "Verification scoping" scopes the REVIEW LENSES on a fix-pass, not the
mechanical gates — and the mechanical gates are what found everything here. The
one integrated adversarial lens returned 0 P0 and its most useful finding was a
RE-RATING: it recomputed the boss-fit margin from the datasheet NOMINAL boss
(ø1.70) instead of the measured one (ø1.60) and got INTERFERENCE where we got a
0.04 mm margin. Both numbers are right; the difference is which boss you assume.
That went straight into the order paperwork as "dry-fit EVERY connector", which
is a real behavioural change bought by one review.

**The transferable rule: when a fit margin depends on a MEASURED value that is
better than nominal, say so, and state what happens at nominal.** A margin that
only exists because this particular lot measured favourably is a per-lot margin,
not a design margin.

## 7. THE ROTATION FIX ITSELF NEEDED NO NEW WORK, AND THAT IS THE POINT

`export_jlc_package.py` re-exported this board's CPL at 270.0 with no
intervention: the A-ROT authority path (measured per-LCSC row only, name DB
advisory) had already landed, and the refuted `^JST_GH_SM,180` rule is annotated
in place in `jlc_rotations_db.csv` so it can inform a finding and never decide a
cell. **The defect was fixed at the gate level 2 days before this respin; the
respin only had to re-run it.** That is what a canon change is supposed to buy,
and it is worth recording that it did.
