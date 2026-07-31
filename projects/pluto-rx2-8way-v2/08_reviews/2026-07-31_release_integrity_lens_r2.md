# pluto-rx2-8way-v2 v1.0 — RELEASE INTEGRITY LENS, ROUND 2

Subject: the **re-staged** archive at `06_build/staging/`, git sha `2a65b60b`.
Lens: release integrity only — bijection, provenance, gate honesty, contamination.
Fresh context. Round 1's findings were **not** inherited; every number below was
re-measured against the archive that exists now.

```
design_verdict: DEFECTIVE
order_verdict:  DO-NOT-ORDER
```

**The copper is clean and I could not fault it.** DRC 0/0/0 raw exit 0 on my own
out-of-repo copy; all 13 fab files reproduce COMMAND-FOR-COMMAND from the shipped
board; the MANIFEST is bijective both ways with 0 hash mismatches. The verdict is
`DEFECTIVE` for two reasons, neither of them copper:

1. **The instrument allowed to say `SOUND` has not run against this board.**
   A-EVID FAILs on exactly the four review documents, and `M-REV`'s denominator
   is **zero** — so the freshness gate prints `DESIGN: PASS` while grading no
   verdict at all. Absence, not disagreement.
2. **The MANIFEST and ORDER_README both assert something MEASURABLY FALSE about
   their own git state** — see finding R2-1. Small in substance, exactly the
   self-report class that `policy_audit`'s own M-REL comment calls "a gate that
   validates its subject's self-report proves nothing".

`order_verdict: DO-NOT-ORDER` follows from the design key and from the four owed
human gates. It is **not** `BLOCKED-SOURCING`: I re-ran the sourcing claim and it
measures `SOURCING: CLEAR` over 11 coded+placed lines.

**Nothing here asks for the archive to be changed.** The A-EVID FAIL is the
correct state and I am not re-arguing it. What I am reporting is (a) one false
sentence in the paperwork, (b) four gate-shape defects that let a *future* seal
of this or any board go green on nothing, and (c) a contamination artifact
already inside an immutable directory.

---

## 0. VERDICT SUMMARY TABLE

| claim under test | my measurement | verdict |
|---|---|---|
| 69 files / 68 MANIFEST rows | 69 / 68, my own walker | **CONFIRMED** |
| bijective BOTH ways | 0 rows-without-file, 0 files-without-row | **CONFIRMED** |
| 0 hash / size mismatches | 0 over 68 files, 7 150 264 B | **CONFIRMED** |
| fab set from the fixed exporter, nothing renamed | 13/13 reproduce; only names `bom.csv`/`cpl.csv` | **CONFIRMED** |
| standalone DRC outside the repo 0/0/0 raw exit 0 | 0/0/0, raw exit 0, my copy | **CONFIRMED** |
| A-EVID FAIL = 4, 29 present | 4 missing, 29 present, raw exit 1 | **CONFIRMED** |
| `git_dirty: true`, honestly scoped | true, raw exit 1 — but see R2-1 and R2-2 | **PARTIAL** |
| freshness re-run clean | DESIGN PASS / SOURCING CLEAR / FRESHNESS PASS, raw exit 0 | **CONFIRMED, and hollow — R2-3** |
| my run contaminated nothing | 0 drift over 69 files; 0 new `.kicad_prl` in the repo | **CONFIRMED** |

Every row above is **MEASURED** by me in this session unless marked otherwise.

---

## 1. BIJECTION — MY OWN WALKER, BOTH DIRECTIONS (canon M1)

**MEASURED.** I did not use `sha256sum -c`. I wrote a walker that (a) enumerates
the tree with `os.walk`, (b) parses the MANIFEST with my own row regex, and (c)
re-hashes every file with `hashlib`. Run against a copy of the archive taken
**out of the repo** before anything opened it.

```
MANIFEST hash rows parsed  : 68
files on disk (ex MANIFEST): 68
duplicate rows             : 0
ROWS WITH NO FILE   (A->B) : 0
FILES WITH NO ROW   (B->A) : 0        <-- the direction sha256sum -c cannot see
HASH MISMATCHES            : 0
total bytes hashed         : 7 150 264  (6.82 MiB)
```

**The walker is proven able to FAIL.** Positive control, same code, run against
`crow-recorder-central-v2` v1.5 (read-only): **68 files on disk, 66 MANIFEST
rows, 2 files with no row** — `SUPERSEDED.md` (legitimate, added post-seal) and
`source/crow_recorder_central_v2.kicad_prl` (**the #58 defect**, confirmed: that
MANIFEST contains zero occurrences of the string `kicad_prl` while its own
footer claims the table is bijective). A checker that cannot fail is worthless;
this one failed where a defect exists and passed where none does.

**Layout note.** This MANIFEST uses `sha256sum` order (`<hash>  <path>`), not the
path-first layout three other boards write.

---

## 2. `M-REL` — HOW MANY OF THE 68 ROWS DOES IT ACTUALLY VERIFY?

**MEASURED, and the answer has two parts.**

**Part 1 — right now, ZERO, because M-REL does not grade this board at all.**
`policy_audit.py projects/pluto-rx2-8way-v2` reports:

```
| M-REL | N-A | no releases yet |
```

M-REL resolves its subject from `07_releases/` (via `release_index.releases_for_board`).
That directory holds only `contracts.md`. **The 68-row MANIFEST is currently
graded by no M-REL run whatsoever** — so a green M-REL on this project today
would be a green over an empty set, and it correctly reports `N-A` instead.

**Part 2 — at seal time it will verify 68 of 68. DERIVED by executing M-REL's
own regex** against this MANIFEST, extracted verbatim from `policy_audit.py`:

```
^(?:\s+(?P<p1>[\w./-]+)\s+(?P<h1>[0-9a-f]{16,64})
 |(?P<h2>[0-9a-f]{16,64})\s+(?P<p2>[\w./-]+))\s*$
```

```
M-REL regex matches : 68
my parser rows      : 68
in mine, not M-REL  : []      in M-REL, not mine : []
```

The two layouts both parse and the path charset `[\w./-]+` covers every path here,
including `source/pluto_rx2_8way_v2.pretty/QFN-24_4x4_P0.5_EP2.7_PE42482.kicad_mod`.
**No silent zero-denominator.** This number is the one the brief asked for: do
not accept a green M-REL on this board without it, and note that today's green
is `N-A`, not a pass.

---

## 3. FINDINGS

### R2-1 — the MANIFEST states its own git scope is EMPTY. It is not. (MEASURED)

`MANIFEST.txt` line 10-11, inside the `git_dirty:` block:

> *"Every input THIS BOARD owns is committed at the sha above and
> `git status projects/pluto-rx2-8way-v2/` is EMPTY."*

`ORDER_README.md` §7 item 2 repeats it: *"Every input this board owns is
committed and its working tree is clean."*

**Measured, unpiped:**

```
$ git status --porcelain projects/pluto-rx2-8way-v2/
 M projects/pluto-rx2-8way-v2/03_src/route.yaml
```

It is not empty, and it was not empty when the stamp was written: `route.yaml`
mtime **14:52:24**, `MANIFEST.txt` mtime **15:13:41**. The false sentence was
written 21 minutes after the fact it denies.

**The SUBSTANCE survives, and I proved it rather than assuming it.** The diff is
`+56/-26` and **comment-only**:

```
committed non-comment lines : 146      sha of stripped content : 2afcfda2f52523c6
worktree  non-comment lines : 146      sha of stripped content : 2afcfda2f52523c6
SEMANTIC DIFF LINES         : 0
stitch.via.spacing          : 0.75 in BOTH
```

So the board is not built from undeclared source. **But the claim is what a
future reviewer checks, and this one is checkable and wrong.** The correct stamp
is one sentence longer: *"`03_src/route.yaml` is modified — comment-only, 0
semantic diff lines, `spacing: 0.75` unchanged."* Classified, this is a CLAIM
defect, not a copper defect — the same class the archive itself carries in §8a
and §8b, and it belongs beside them.

### R2-2 — the `git_dirty` stamp's mtimes are already stale (MEASURED)

The stamp names four backend scripts with mtimes. Re-measured now:

| script | MANIFEST says | measured now | |
|---|---|---|---|
| `generate_board_generic.py` | 14:23 | 14:23:58 | agrees |
| `generate_rules_generic.py` | 12:11 | 12:11:51 | agrees |
| `pcb_toolkit.py` | **13:51** | **15:27:44** | **moved again** |
| `route_and_stitch_generic.py` | 14:44 | 14:44:59 | agrees |

`pcb_toolkit.py` changed **14 minutes after the MANIFEST was stamped**, while
this archive sat staged. This does not weaken the stamp's conclusion — it
strengthens it: the tree is even further from reproducible than the stamp says.
I re-hashed all three at the start and end of my own review and they did **not**
move during it, so a peer agent's edit landed between staging and my run.

The stamp also under-reports the dirty set. `release_git_dirty.py
pluto-rx2-8way-v2` (RAW EXIT 1) lists **eleven** paths, not four+one:
the four backend scripts, plus `design-policies.md`, `routing-pipeline.md`,
`skills/kicad-pcb/scripts/contracts.md`, `gate_contract_audit.py`, the
`03_src` contracts template, `03_src/route.yaml`, and an untracked
`skills/kicad-pcb/scripts/dru_subject.py`. The four named are the four that
matter for reproducibility and naming them is the right editorial choice — but
"the dirty paths are all in the SHARED skills/ tree" is false in the same
sentence as R2-1, for the same file.

**The stamp must NOT be used to move a gate, and it is not.** `git_dirty: true`
is recorded, `M-REL` would fail on it (`git_dirty is 'true', not false`), and no
one has stamped `false`. That restraint is correct and I am confirming it, not
requesting it.

### R2-3 — `M-REV` grades ZERO documents and the gate prints PASS (MEASURED)

Re-run of `release_freshness_check.py` on the staging tree, unpiped:

```
note: M-REV: 0 graded / 0 redteam*.md present in verification/
DESIGN: PASS
SOURCING: CLEAR
FRESHNESS: PASS
RAW EXIT 0
```

Compare with A-EVID on the same tree, same moment:

```
MISSING required artifact: verification/pin_review.md
MISSING required artifact: verification/render_review.md
MISSING required artifact: verification/redteam_topology.md
MISSING required artifact: verification/redteam_layout.md
A-EVID FAIL: 4 required artifact(s) missing, 0 unparsed, 29 present
RAW EXIT 1
```

**Two gates, same fact, opposite exit codes.** The cause is one line in
`check_reviews()`:

```python
graded = [n for n in _REVIEW_LENS_FILES if (ver / n).is_file()]
...
if not graded:
    return dfails, sfails, notes        # <-- zero denominator, silent pass
```

**I proved M-REV is not simply dead** — two known-bad fixtures, built out of
repo on a copy at a real seal path, both go RED:

| fixture | result |
|---|---|
| control (archive as-is, 0 lens files) | DESIGN PASS / FRESHNESS PASS, **raw exit 0** |
| `redteam_layout.md` present, no verdict key | `REVIEW-NO-VERDICT`, FRESHNESS FAIL, **raw exit 1** |
| `redteam_layout.md` with `design_verdict: DEFECTIVE` | `REVIEW-DESIGN-DEFECTIVE` + `REVIEW-DO-NOT-ORDER`, **raw exit 1** |

So the gate enforces *"a missing verdict is a FAIL, never a skip"* for a missing
**KEY** and not for a missing **FILE** — and the module's own docstring states
that doctrine without the distinction. The archive's decision to ship no stale
reviews is right; the consequence is that the ONLY gate standing between this
tree and a seal on this point is A-EVID.

### R2-4 — A-EVID is the sole detector, and `policy_audit` does not run it (MEASURED)

```
occurrences of "A-EVID" in policy_audit.py                : 0
occurrences of "A-EVID" in the generated 06_build/policy_audit.md : 0
```

`release_required_check.py` is invoked only by `fleet_regrade.py` and
`tests/t1_release_required.py`. **A seal driven off `policy_audit` +
`release_freshness_check` alone would not notice that the four review documents
are absent** — policy_audit reports one unrelated FAIL (R2-5) and freshness
reports PASS. The seal procedure must run A-EVID explicitly, and this review is
the record that it currently must be run by hand.

### R2-5 — the `A-POP` FAIL is a path-resolution artifact, and I proved it (MEASURED)

`policy_audit` reports `FAIL=1, HUMAN=6, N-A=7, PASS=31`, the single FAIL being:

```
A-POP: MANIFEST-UNDECLARED: the release MANIFEST carries no `not_assembled:`
       line while the board has unpopulated parts
```

The ORDER_README §7 item 1 calls this an artefact of not sealing. **That is
correct, and it is worse than stated.** `assembly_coverage.py` resolves its
manifest as:

```python
man_p = Path(args.target) / "MANIFEST.txt"
```

and `policy_audit` passes `_asm_target = str(latest) if latest else str(proj)`.
With no sealed release the target is the project root, so it looks for
`<project>/MANIFEST.txt`.

```
$ ls projects/*/MANIFEST.txt
No such file or directory        <-- that path exists in ZERO of 10 projects
```

The MANIFEST half of A-POP is **structurally unreadable in project mode for
every board in the fleet**, not just this one. Pointed at the real staged
manifest it is clean:

```
$ assembly_coverage.py projects/pluto-rx2-8way-v2 \
    --manifest projects/pluto-rx2-8way-v2/06_build/staging/MANIFEST.txt
A-POP: PASS (every unpopulated part is declared with evidence)
RAW EXIT 0
```

And the declaration itself is verified by a **different method** (canon M1) — I
regenerated the line from `03_src/rules/assembly.yaml` and compared:

```
generated from assembly.yaml : not_assembled: H1, H2, H3, H4, U_MCU
stated in the MANIFEST       : not_assembled: H1, H2, H3, H4, U_MCU
```

Byte-identical, no MANIFEST-DRIFT. **Classified: 1 FAIL, 0 of it a defect in this
archive.** Proposal in §6.

---

## 4. THE FAB SET DESCRIBES THE SHIPPED COPPER — COMMAND MULTISETS (MEASURED)

This is the check round 1's failure mode demanded: *the archive said the copper
did not move, and then the copper moved.* I re-ran the exporter **out of the
repo** against the archive's own `source/*.kicad_pcb` and compared **command
multisets**, never bytes.

```
files compared : 13
pluto_rx2_8way_v2-F_Cu.gtl          MULTISET DIFF 4   (bytes_equal=False)
    only in MINE : %TF.CreationDate,2026-07-31T15:37:09-07:00*%
    only in MINE : G04 Created by KiCad (PCBNEW 10.0.4-...) date 2026-07-31 15:37:09*
    only in SHIP : %TF.CreationDate,2026-07-31T14:30:07-07:00*%
    only in SHIP : G04 Created by KiCad (PCBNEW 10.0.4-...) date 2026-07-31 14:30:07*
    ... identical shape on all 13 files ...
TOTAL multiset-differing lines across all files: 52
```

**52 = 13 files x 4 lines, and all 52 are timestamps.** Every aperture
definition, every draw command, every drill coordinate is reproduced exactly.
**The shipped gerbers and drills are the shipped board.** DERIVED corollary: an
agent comparing these files byte-wise would see 13/13 "differ" and learn nothing.

Supporting measurements, all MEASURED:

- `fab/pluto_rx2_8way_v2_gerbers.zip` — 13 entries, **every one byte-identical**
  to its loose twin, no entry without a twin, no loose gerber missing from the
  zip. The thing that gets uploaded and the thing that gets reviewed are the
  same bytes.
- `06_build/fab/` vs `staging/fab/` — **18 of 18 files byte-identical**. No
  legacy `bom_jlc.csv` / `cpl_jlc.csv` anywhere, so the contract names came from
  the exporter and not from a hand-copy.
- `628ee3d4` is an **ancestor of HEAD**, it touches `export_jlc_package.py`, and
  that file is **clean in `git status`**. The exporter writes `bom.csv` /
  `cpl.csv` at lines 340-341. The claim *"nothing here was hand-copied or
  renamed"* is supported.
- `staging/source/` vs the project source of truth: `.kicad_pcb`, `.kicad_sch`,
  `.kicad_dru`, `.kicad_pro`, `.net`, `.tsx`, `refdes_waiver.json` and all three
  `.pretty/*.kicad_mod` — **byte-identical**. The single difference is
  `fp-lib-table`, and it is the intended standalone rewrite:
  `${KIPRJMOD}/../03_src/lib/…pretty` -> `${KIPRJMOD}/pluto_rx2_8way_v2.pretty`.
  That one edit is what makes the archive openable on its own.

### Standalone DRC, my own run, outside the repo

```
$ kicad-cli pcb drc --severity-all --refill-zones --schematic-parity ...
Found 0 violations
Found 0 unconnected items
Found 0 schematic parity issues
RAW EXIT 0
```

**Both halves, classified: zero violations in zero classes, zero unconnected in
zero classes, zero parity.** This agrees with the shipped
`verification/standalone_archive_drc.json` and with `verification/drc.json`
(dated 14:35:32), all three at 0/0/0.

---

## 5. CONTAMINATION (#64) — I REPRODUCED IT, AND I CONFINED IT

**Method.** I fingerprinted all 69 staging files (path, size, mtime_ns, sha256)
**before** touching anything, copied the tree out of the repo, and opened only
the copy. Final re-fingerprint:

```
STAGING: 0 drift across my entire run (69 files, path+size+mtime_ns+sha256)
new .kicad_prl anywhere under projects/ after my run started: NONE
git status --porcelain | wc -l : 19  (unchanged)
```

**My run contaminated nothing in the repo.** In my out-of-repo copy it
contaminated exactly what #64 predicts: `kicad-cli pcb drc` wrote
`pluto_rx2_8way_v2.kicad_prl`, **2304 bytes**, at 15:32:17. Merely opening the
board created it.

**A 2304-byte `.kicad_prl` was ALREADY sitting in `04_kicad/` before I arrived**
— mtime 12:32:01, i.e. three hours before this session, sharing an
identical-to-the-nanosecond mtime with `fp-lib-table` and `refdes_waiver.json`,
so it was written by the build, not by a reviewer. `04_kicad/` is IMMUTABLE; I
did not touch it and I am not asking anyone to. Fleet census, MEASURED:
**15 `.kicad_prl` files under `projects/`**, of which **8 are in `04_kicad/`**
and **3 are inside sealed release trees**.

**Why three detectors miss it, verified here:**

```
$ git check-ignore -v <project>/04_kicad/pluto_rx2_8way_v2.kicad_prl
projects/pluto-rx2-8way-v2/.gitignore:11:*.kicad_prl     ...
RAW EXIT 0
```

Gitignored, so invisible to `git status`; untracked *and* ignored, so
`contracts_audit --present` (tracked ∪ untracked-not-ignored) sees it in
neither; and the purge glob targets the DOUBLE extension `*.kicad_pcb.kicad_prl`
while this is the single-extension name. **My bijection walker is the only one of
the four that catches it** — which is exactly how it caught the crow-recorder
instance in §1.

**Forward warning, DERIVED and measured:** the `*.kicad_prl` rule is unanchored,
so it applies at the seal location too. I confirmed by asking git at the mapped
path: a `.kicad_prl` inside a sealed `source/` **would be gitignored there**.
Anyone who opens a sealed board once puts a file in the sealed tree that is on
disk, absent from git, absent from the MANIFEST, and invisible to every
name-based check. That is #58, and the recipe is "open the board".

### The strip-gitignored trap — mapped, not tripped

I ran no deletion. I mapped every archive file to its seal location and asked
git **there**:

```
archive files mapped to the seal location : 69 ; gitignored there : 0
the SAME files at their current staging path : 69 of 69 gitignored
```

**All 69 are gitignored where they sit** (`06_build/*` blanket rule) — a naive
`git check-ignore` sweep would delete the entire archive again. **At the seal
location, 0 of 69 are ignored**, so every file is trackable once sealed. This is
the only safe form of that check and it is the form I used.

---

## 6. FRESHNESS RE-RUN, AND THE SHORTCUT THAT IS STILL OPEN

**Re-run, MEASURED:** `DESIGN: PASS / SOURCING: CLEAR / FRESHNESS: PASS`,
**RAW EXIT 0**. Round 1's `DESIGN FAIL (10)` is gone.

**Which of round 1's ten survive: ZERO — because the documents that produced
them are no longer in the archive**, not because anything about the board
changed. I confirmed the mechanism directly. Check (d) scans
`verification/*.{txt,md}` for embedded release paths with

```
07_releases/((?=[^/\s`'")\]]*v\d)[^/\s`'")\]]+)/
```

and I ran that exact regex over the current evidence:

```
verification/*.{txt,md} scanned                       : 16
files embedding a 07_releases/<…v#…> path             : 0
MANIFEST.txt / ORDER_README.md (not scanned by (d))   : 0
```

So (d)'s evidence-path half will be **clean at seal**. (This review is written to
stay clean under that regex too — round 1's archive review generated 3 of its 8
findings by quoting the paths it was reporting on.)

### The fictitious-release-name shortcut is STILL OPEN, and has NOT been taken

**MEASURED, out of repo, on a copy.** Same evidence bytes in both runs; the
**only** thing that changed is the directory name:

| the seal directory is named | result |
|---|---|
| the honest name, evidence quoting a foreign one | `EVIDENCE PATH MISMATCH`, DESIGN FAIL, **raw exit 1** |
| renamed to match what the evidence quotes | DESIGN **PASS**, FRESHNESS **PASS**, **raw exit 0** |

Check (d) compares the embedded name against `release_dir.name`, so **naming the
release after the fiction turns the gate green without making one byte of
evidence truer.** `_release_date()` reads the date from the same directory name,
so a fictitious date also relaxes the A-BUY staleness window.

**This board has not taken it.** `07_releases/` holds only `contracts.md` — no
release directory of any name exists — and 0 of 16 evidence files embed a
release path to be matched. The shortcut is refused **in fact**; it is not
refused **by construction**, and that is a gate defect, not a board defect.

---

## 7. PROPOSED `skills/` CHANGES — PROPOSED, NOT APPLIED

Each needs a known-bad fixture that goes RED against the pre-fix code.

**P1 — `check_reviews()` must FAIL on an empty denominator** (M-COVER).
`release_freshness_check.py:2207`, `if not graded: return`. Make zero graded
lens files a `REVIEW-ABSENT` DESIGN fail. This is the same hardening `M-REL`
already received at `policy_audit.py:1658` ("a gate that verifies nothing must
not report that hashes verify"); M-REV has the identical hole and did not get
it. Fixture: a release dir with a populated `verification/` and no
`redteam_*.md` — today it exits 0.

**P2 — A-POP must find the staged MANIFEST in project mode.**
`assembly_coverage.py:778`, `man_p = Path(args.target)/"MANIFEST.txt"`. In
project mode fall back to `06_build/staging/MANIFEST.txt`, then
`06_build/MANIFEST_HEAD.txt`. Measured: `<project>/MANIFEST.txt` exists in
**0 of 10** projects, so today every pre-seal board with unpopulated parts eats
an unavoidable `MANIFEST-UNDECLARED`. A FAIL nobody can clear is a FAIL people
learn to skip. Fixture: this board — PASS with `--manifest`, FAIL without.

**P3 — check (d) must not accept the release name as authority over its own
evidence.** Anchor the comparison to something the evidence cannot rename:
compare against the MANIFEST's `board:` + `version:` fields, or require that any
embedded release name whose date is in the future be a FAIL regardless of match.
Fixture: §6's two-run demonstration, which is already scripted.

**P4 — the purge glob must catch the SINGLE-extension `.kicad_prl`.** The
current glob is `*.kicad_pcb.kicad_prl`; every file I measured is
`<board>.kicad_prl`. Add the single-extension form, and add a MANIFEST-vs-tree
bijection to the seal procedure so a gitignored intruder in a sealed `source/`
is caught by *something*. Fixture: crow-recorder-central-v2 v1.5, which carries
one today.

---

## 8. WHAT I DID NOT CHECK — so nobody reads this as broader than it is

- **RF, layout, schematic and DFM.** Out of lens. The 273.85 Ω / RL 21.45 dB
  restatement and the −20.26 dB qualifier are carried in §8a/§8b of the
  ORDER_README; I **confirmed they are present and internally consistent**
  (the 47x framing against the 5.80 Ω defect it replaced is stated) but I did
  **not** re-derive the impedance. **INHERITED, and flagged as such.**
- **The JLC mixed-class hole question.** Present in the MANIFEST `fab:` block
  and ORDER_README §7 item 4 as an unanswered DFM question put to the vendor.
  I verified it is stated as a question, not as a solved problem. Not re-derived.
- **Stock.** I read the A-BUY/A-STOCK verdicts out of the freshness run
  (11 graded lines, PASS, CLEAR). I did not re-query the catalog.
- **The reproducibility claim** that today's backend produces the same board
  (identical `.kicad_pcb` properties, UUID-masked `.kicad_sch` sha256, 28 gerber
  multisets, empty netlist symdiffs) is **INHERITED from the brief**. I did not
  re-run it; R2-2 shows the backend has moved again since, so it would need
  re-running anyway. What I *did* verify independently is the narrower and more
  load-bearing claim: the **shipped** fab set reproduces from the **shipped**
  board (§4).

---

## 9. WHAT WOULD MOVE MY VERDICT

`design_verdict: SOUND` needs a fresh red-team round against **this** copper,
landing `verification/redteam_topology.md` and `verification/redteam_layout.md`
with parseable keys, plus `pin_review.md` and `render_review.md` — which closes
A-EVID and gives M-REV a non-zero denominator at the same time. It also needs
R2-1's sentence corrected: the stamp should say `03_src/route.yaml` is modified
comment-only with 0 semantic diff lines, rather than that the scope is empty.

`order_verdict: ORDER` additionally needs the four §2/§7 human gates closed,
including JLC's written answer on the mixed-class hole floor.

Neither needs a byte of the fab set to change. **The copper, as far as this lens
can see it, is exactly what the paperwork says it is — and the paperwork is
where the two defects are.**

---

*Round 2, release-integrity lens. Fresh context; round 1 inherited nothing.
Gates run unpiped with raw exit codes recorded. `04_kicad/` and `07_releases/`
opened read-only; every board file was copied out of the repo before it was
opened. Staging tree verified 0-drift before and after. Only this file written.*
