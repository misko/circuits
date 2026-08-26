# pluto-rx2-8way-v2 — release-integrity lens, round 3

    board:      pluto-rx2-8way-v2
    archive:    06_build/staging  (re-staged 2026-07-31 16:07-16:23)
    repo HEAD:  083dc488   (MANIFEST stamps git_sha fe5fade5 — see F-1)
    lens:       release integrity / archive bijection / gate denominators
    round:      3   (round 2 = DEFECTIVE / DO-NOT-ORDER; nothing inherited)

design_verdict: SOUND
order_verdict: DO-NOT-ORDER

**Why those two.** Every round-2 design finding I was asked to re-check is
FIXED, and I re-measured each from the bytes rather than reading the claim: the
two false git-status sentences are withdrawn and what replaced them is true, the
PTH<->PTH row is right to the last digit, and the copper provably did not move
across the BOM fix. I found no defect in the board. The order is blocked on
STATE, not on the design and not on sourcing: the archive says of itself
`ordered: no — *** STAGED, NOT SEALED ***`, its release root holds zero release
directories, A-EVID FAILs on four contract-required review documents that are
genuinely absent, and the archive's own declared seal precondition
(`git_dirty: false`) is not met. `BLOCKED-SOURCING` would be a false statement —
sourcing MEASURES CLEAR, 11/11 coded+placed lines OK — and the freshness gate
would rightly contradict it.

**Nothing here is blocking that the archive does not already declare itself.**
The four findings below are all ARCHIVE/GATE findings, not board findings. Two
are gates that report green over a zero denominator.

---

## 0. Method, and what I did not trust

Everything below is MEASURED unless labelled otherwise. INHERITED means I took a
number from a document without re-deriving it — I have tried to leave none.

- I wrote my own tree walker, my own Excellon parser, and my own s-expression
  set-comparator rather than reuse the archive's instruments (canon M1). Scripts
  are in this session's scratchpad, not in the repo.
- `kicad-cli pcb drc` is **never** invoked here with `--exit-code-violations`,
  so its exit 0 is exit-0-by-construction and is not cited as evidence anywhere
  in this document. Only PARSED counts are.
- Gerbers are compared as command MULTISETS, never as bytes.
- `04_kicad/` and the release root were opened READ-ONLY. Everything I ran
  kicad-cli against was a copy outside the repository.

### Contamination report — MY RUN CONTAMINATED NOTHING (MEASURED)

`kicad-cli` writes a `.kicad_prl` merely by opening a board (#64). I censused
before and after:

| census (scope `projects/`) | baseline, session start | after my run |
|---|---|---|
| `.kicad_prl` total | 100 | **100** |
| under `04_kicad/` or a release root | 15 | **15** |
| under a release root only | 3 | **3** |
| inside `06_build/staging` | 0 | **0** |

No file under `projects/` was written in the 40 minutes of this review; the
staging tree's newest mtime is still `MANIFEST.txt` at 16:23, which predates my
session; `04_kicad/` has nothing newer than 16:21. The one `.kicad_prl` my DRC
and gerber runs produced is in the out-of-repo copy in the scratchpad.

The prompt's fleet numbers are CONFIRMED with their scoping made explicit: **15**
is `.kicad_prl` under `04_kicad/` **or** a release root within `projects/`;
**3** is the release-root subset (`crow-recorder-central-v2-v1.5-2026-07-25`,
`cooksense-v1.7-2026-07-30`, and `interposer-v1.1-2026-07-27` — that last one
written 2026-07-31 02:38, by review activity, into a SEALED tree). Repo-wide the
count is much larger (100 under `projects/`, more again under
`archived_projects/`); the 15/3 figures are the sealed-tree ones.

---

## 1. Bijection BOTH ways, with my own walker — CLEAN (MEASURED)

My walker parses the hash table with its own regex, walks the tree with
`os.walk`, and set-differences in both directions. It does not shell out to
`sha256sum -c`, which structurally cannot see a file present in the archive and
absent from the table.

```
MANIFEST rows parsed            68      duplicate path rows      0
files on disk (all)             69      malformed hash lines     0
files on disk (excl MANIFEST)   68
ON DISK NOT IN TABLE            0  []
IN TABLE NOT ON DISK            0  []
HASH MISMATCHES                 0
symlinks / zero-byte files      0
```

**68 / 68, both directions, 0 mismatches.** The archive's claim is exact.

### Directory census — no empty directory, and none uncovered

An empty directory is invisible to a file table, so it gets its own census:

| directory | files | subdirs | covered by >=1 table row |
|---|---|---|---|
| `.` (archive root) | 2 | 5 | yes |
| `3d/` | 1 | 0 | yes |
| `fab/` | 18 | 0 | yes |
| `pdf/` | 3 | 0 | yes |
| `source/` | 8 | 1 | yes |
| `source/pluto_rx2_8way_v2.pretty/` | 3 | 0 | yes |
| `verification/` | 34 | 0 | yes |

7 directories including the root, 6 excluding it — which is the archive's own
figure. **EMPTY DIRECTORIES: none.** Every directory carries at least one hashed
row, so there is no dark corner the table cannot see.

For completeness the archive's own method also passes: `sha256sum -c` over the
68 extracted rows, RAW EXIT 0. That agreement is expected and is not the point —
the reverse direction is, and it is clean.

### Zip integrity — a direction neither the table nor `sha256sum -c` covers

`fab/pluto_rx2_8way_v2_gerbers.zip` is hashed as one opaque blob. Its 13 members
are not. I extracted and compared each against its loose sibling:

- **13 / 13 members BYTE-IDENTICAL** to the loose file that the MANIFEST hashes
  individually.
- **0 zip-only members** — nothing rides into the vendor's uploader that the
  hash table has not seen.
- loose-only files are exactly `bom.csv`, `cpl.csv`, `bom_echo_gate.txt`,
  `rotation_human_gate.txt` and the zip itself, which is the exporter's
  documented contract (the upload zip carries gerbers + drills only).

---

## 2. The two withdrawn sentences — VERIFIED TRUE NOW, and the named set is complete

**The false sentence is gone and its replacement is true.** MEASURED:
`git status --porcelain projects/pluto-rx2-8way-v2/` returns exactly one line,
` M projects/pluto-rx2-8way-v2/03_src/route.yaml`. The MANIFEST now says the
subtree is NOT clean and that the previous claim "was FALSE when it was written
and it is false now". Both halves check out.

**The comment-only claim, re-derived from scratch** (I stripped comments and
blank lines myself and hashed both sides):

| | worktree | HEAD `083dc488` |
|---|---|---|
| total lines | 848 | 818 |
| non-comment lines | **146** | **146** |
| stripped sha256 (first 32) | `744327e1bf0330bb3a13e10fd9e1d577` | `744327e1bf0330bb3a13e10fd9e1d577` |
| semantic diff lines | 0 | |
| `stitch.via.spacing` | `0.75` (line 386) | `0.75` (line 366) |

CONFIRMED. The board is not built from undeclared source.

**Is the dirty set the MANIFEST names COMPLETE? YES — and I can date it.** The
MANIFEST enumerates NINETEEN dirty paths at write time, broken out as 9 of this
board's own plus 10 in `skills/` + templates. Commit `04e9b8eb` landed at
16:24:34, **90 seconds after the MANIFEST was written at 16:23**, and carried
exactly EIGHT board paths:

```
A  01_docs/decisions/0006-...md          M  03_tscircuit/src/pluto_rx2_8way_v2.tsx
M  03_src/rules/nets.yaml                M  04_kicad/pluto_rx2_8way_v2.kicad_pcb
M  03_tscircuit/build/circuit.json       M  04_kicad/pluto_rx2_8way_v2.kicad_sch
M  03_tscircuit/build/schematic.pdf      M  03_tscircuit/dist/src/.../circuit.json
```

Those eight plus `03_src/route.yaml` (which stayed dirty) are the MANIFEST's
nine, **name for name, with nothing missing and nothing extra**. The
enumeration was exact.

`release_git_dirty.py pluto-rx2-8way-v2` NOW, unpiped, **RAW EXIT 1**, lists
ELEVEN paths: `03_src/route.yaml`, the four shared backend scripts
(`generate_board_generic.py`, `generate_rules_generic.py`, `pcb_toolkit.py`,
`route_and_stitch_generic.py`), `design-policies.md`, `routing-pipeline.md`,
`skills/kicad-pcb/scripts/contracts.md`, `gate_contract_audit.py`, the `03_src`
contracts template, and untracked `dru_subject.py`. That is **exactly** the
eleven ORDER_README section 7 item 2 enumerates — see F-2 for the one
timestamping wrinkle.

**The flag is not used to move any gate.** `git_dirty: true` in the MANIFEST,
RAW EXIT 1 from the tool, and the archive states in two places that
`git_dirty: false` is a SEAL PRECONDITION which stays unmet. M-REL is the gate
that reads this field and it is N-A here (section 5), so no gate is being
carried by the flag in either direction. The characterisation as a COMMIT
dependency rather than a rebuild dependency is corroborated independently in
section 4.

---

## 3. The PTH<->PTH correction — CONFIRMED to the last digit, by my own parser

I parsed the shipped Excellon files directly (tool table + coordinate blocks,
no pcbnew), and derived footprint ownership independently from the
`.kicad_pcb` by transforming each `thru_hole` pad into board coordinates.

**Hole census — every figure matches:**

| class | archive says | I measure |
|---|---|---|
| `PCB_VIA`, T1 C0.15 | 3446 | **3446** |
| PTH pads, T2 C1.4 | 50 | **50** (10 SMA jacks x 5; 50 `thru_hole` pads found in the board, exactly) |
| NPTH, T1 C3.2 | 4 | **4** |
| plated / all holes | 3496 / 3500 | **3496 / 3500** |
| duplicate coordinates | — | **0** |

**Minimum hole-to-hole, edge to edge (nominal -> max material):**

| pair class | archive | I measure | at |
|---|---|---|---|
| VIA <-> PTH | 0.3265 -> 0.2615 | **0.3265 -> 0.2615** | (43.000, -23.000) / (43.960, -22.460) |
| VIA <-> VIA | 0.3785 -> 0.3785 | **0.3785 -> 0.3785** | (48.060, -30.200) / (48.584, -30.131) |
| NPTH <-> VIA | 0.3768 -> 0.3118 | **0.3768** -> 0.3768 or 0.3118 | (36.500, -89.200) / (35.000, -87.800) |
| PTH <-> PTH | **1.6934 -> 1.5634** | **1.6934 -> 1.5634** | `J_RX2.5` <-> `J_ANT8.3` |

The NPTH row is the one place we differ, and the archive is the CONSERVATIVE
side: it grows the NPTH hole's radius by the 0.065 mm pad tolerance, I did not.
Its own stated rule ("max material grows a PAD hole's radius by 0.065 and a
via's by ZERO") is silent on whether an NPTH counts as a pad hole; taking the
larger growth is the safe reading and I endorse it. Neither reading is near a
floor. **Pairs under the 0.25 mm tier floor at max material: 0** — CONFIRMED,
the tightest is 0.2615.

**The population claim, re-derived.** Of PTH<->PTH pairs under 2.6 mm there are
**41**; exactly **ONE is INTER-footprint** (the 1.6934 minimum, `J_RX2.5`
centre pin to `J_ANT8.3` ground post) and the other **40 are INTRA-footprint**,
every one a jack's own centre pin to its own ground post. **CONFIRMED — the old
row's label really was wider than its number.**

One refinement, sub-quantum and cosmetic: the archive says the forty "all sit
at exactly 2.1921 mm". Measured, they split **16 at 2.1920 and 24 at 2.1921**,
because the drill file quantises coordinates to 3 decimals and the two
orientations of the same 2.54*sqrt(2) - 1.4 geometry land on opposite sides of
the 0.1 um rounding. Same family as the 2.2152/2.2142 sample-grid artefact
`fe5fade5` resolved. **Zero manufacturing consequence**; recorded so the next
reader who measures 2.1920 does not think they have found a discrepancy.

---

## 4. "The copper did not move" — CONFIRMED, and by a stronger method than claimed

The archive compares this staging against the previous staging, which no longer
exists on disk. I did not have to take that on faith: the pre-fix board is in
git. `04_kicad/*.kicad_pcb` at `fe5fade5` **is** the pre-rebuild board (the
rebuild ran at 15:57-15:58, after that commit at 15:52:08), and the post-rebuild
board is at HEAD.

**First, the mechanism.** MEASURED — the LCSC code cannot reach the copper:

| file | `C25744` | `C60490` | any `LCSC` token |
|---|---|---|---|
| `source/*.kicad_pcb` | 0 | 0 | 0 |
| `source/*.kicad_sch` | 0 | 0 | 0 |
| `fab/cpl.csv` | 0 | 0 | 0 |
| `fab/bom.csv` | 0 | **1** | 1 |

The code appears in the BOM and nowhere else. That is an independent
corroboration of the archive's "it appears in neither file".

**Second, the measurement.** My own s-expression walker splits each board into
top-level elements, masks UUIDs and tstamps, and compares MULTISETS per class:

| element class | pre-fix (`fe5fade5`) | archive | symmetric difference |
|---|---|---|---|
| `via` | 3446 | 3446 | **0** |
| `segment` | 199 | 199 | **0** |
| `footprint` | 32 | 32 | **0** |
| `gr_text` | 51 | 51 | **0** |
| `zone` (top level) | 6 | 6 | **0** |
| `zone` (tokens at any depth) | 64 | 64 | **0** |
| `gr_line`, `setup`, `layers`, `general`, ... | — | — | **0** |
| `filled_polygon` | 13 | 13 | equal |
| `pad` | 143 | 143 | equal |

**TOTAL symmetric difference across every class: 0.** The raw bytes differ
(7290 diff lines) and the difference is UUID churn plus ordering, exactly as
claimed. The archive's "zones 64" counts `(zone` tokens at any depth, not
top-level zone objects — both counts are equal on both sides, so the figure is
right under either reading; noted only so a future reader is not confused by
finding 6.

**Third, DRC on the archive's own bytes, out of the repo** — copy first, parsed
counts, both halves:

```
kicad-cli pcb drc --severity-all --refill-zones --schematic-parity
  PARSED violations        0
  PARSED unconnected_items 0
  PARSED schematic_parity  0            kicad 10.0.4
```

(The command exited 0. That is NOT evidence — `--exit-code-violations` was not
passed. The three parsed counts are the evidence.) These agree with both shipped
DRC artefacts, `verification/drc.json` and
`verification/standalone_archive_drc.json`, which each carry 0 / 0 / 0.

**Fourth, the gerbers — and one thing worth writing down.** I re-exported
gerbers and drills from the out-of-repo copy with `kicad-cli` and compared
command MULTISETS against the shipped set. Seven of thirteen files match
exactly (both silkscreens, both pastes, Edge_Cuts, both drill files —
PTH 3510 / 3510 commands, NPTH 15 / 15, symdiff 0). Six differ, and the
difference is **entirely mine**, fully classified:

- each shipped copper layer carries **3500 extra flashes**: 3446 at `C,0.150`
  (the via drill) and 54 at `C,0.350`;
- each shipped mask layer carries the same **54 at `C,0.350`**;
- the 54 are the 50 PTH pad centres and the 4 NPTH centres.

These are KiCad **drill marks** — `PLOT_CONTROLLER` defaults to
`SMALL_DRILL_SHAPE`, `kicad-cli` defaults to none, and the archive is exported
through `PLOT_CONTROLLER`. Every mark is strictly inside the aperture it sits
in (0.150 inside a 0.250 via pad; 0.350 inside a 1.900 PTH pad) or inside a
3.2 mm NPTH that removes it. **Net copper and mask geometry: unchanged.**
Non-blocking, and recorded because it is the reason a naive `kicad-cli`
re-export does not reproduce the shipped copper — the next reviewer who tries
this will otherwise open a finding that is not there.

**Verdict on the section: the copper did not move. CONFIRMED, independently.**

---

## 5. Gate denominators — the numbers the greens are hiding

I ran both gates unpiped and read the raw exit from the process itself, not
through a pipe.

### `release_freshness_check.py` — RAW EXIT 0

```
== release-freshness: staging ==
  note: A-STOCK: grading verification/stock_check.json (11 graded line(s),
        verdict=PASS) against 11 coded+placed BOM line(s) x 5 boards
  note: A-BUY: measured SOURCING: CLEAR over 11 coded+placed line(s)
  note: M-REV: 0 graded / 0 redteam*.md present in verification/
DESIGN: PASS
SOURCING: CLEAR
FRESHNESS: PASS
```

**`DESIGN: PASS` is printed over a denominator of ZERO.** `check_reviews`
grades `_REVIEW_LENS_FILES = ("redteam_topology.md", "redteam_layout.md")`;
neither exists in `verification/`, `graded` is empty, and `if not graded:
return` short-circuits before a single verdict is read. The note prints the
zero honestly — but the three-line summary underneath does not, and the summary
is what travels. This is the M-COVER shape that M-REL was hardened against at
`policy_audit.py:1658`.

Sub-check denominators inside the same green, all MEASURED by calling the
module's own helpers:

| sub-check | comparands actually used | of possible | outcome |
|---|---|---|---|
| ERC error count | MANIFEST `0`, `erc.json` `0` | 2 of 3 | agree |
| ERC warning count | MANIFEST `213`, `erc.json` `213` | 2 of 3 | agree |
| BOM line count | `_manifest_bom_lines` -> **None** | **0 comparisons** | vacuous |
| embedded release path | **0 matches** over 16 `.txt`/`.md` files | — | clean, see section 6 |

The missing third ERC comparand and the vacuous BOM comparison are both caused
by F-3 below. I independently parsed `erc.json`: **0 errors, 213 warnings**
(124 `endpoint_off_grid`, 89 `lib_symbol_issues`), which matches the MANIFEST.
`fab/bom.csv` carries **11 data rows**, matching the "all 11 lines" MOQ claim.

### `release_required_check.py` (A-EVID)

Run as the pipeline would (contract defaulting to the release root's
`contracts.md`), **RAW EXIT 1**:

```
  CONDITIONAL absent (contract states a condition): 3d/<board>.gltf
  MISSING required artifact: verification/pin_review.md
  MISSING required artifact: verification/render_review.md
  MISSING required artifact: verification/redteam_topology.md
  MISSING required artifact: verification/redteam_layout.md
A-EVID FAIL: 4 required artifact(s) missing, 0 contract line(s) unparsed,
             29 present
```

**Denominator 33: 29 present, 4 missing, 0 unparsed.** The four missing are
exactly the review documents, which is the honest state — the reviews in
`08_reviews/` graded copper this board has left, and promoting one version's
review as another version's verdict is the adjacent-property error. ORDER_README
section 7 item 3 says this in as many words and declines to close it by copying.
**I agree, and this document is not to be copied in either.**

**A-EVID is never invoked by `policy_audit.py`.** MEASURED: the string `A-EVID`
does not occur in `policy_audit.py`; its only production caller in the tree is
`fleet_regrade.py:95`. So a seal driven off `policy_audit` + `release_freshness_check`
sees `DESIGN: PASS` over zero reviews and never learns that four are missing.
Both halves of #75 are live on this archive right now.

### M-REL — **verifies 0 of the 68 rows**

The prompt asked for the number and it is zero. `policy_audit.py:1579` builds
`_all_reldirs` from subdirectories of the board's release root; that directory
contains `contracts.md` and **nothing else — 0 subdirectories**, so control
reaches `rows.append(("M-REL", "N-A", "no releases yet"))` at line 1692. M-REL
never opens the MANIFEST, never re-hashes a file, and never reads `git_dirty`.

Two more denominators worth having, DERIVED by reading the code that would run
if a release directory existed:

- M-REL's hash-table regex admits `<hash>  <path>` and `  <path>  <hash>`. The
  archive writes sha256sum order, so all 68 rows **would** match — this archive
  is not exposed to the usb-hub-3s-v3 zero-match failure. The M-COVER backstop
  at line 1658 would catch it if it were.
- M-REL would FAIL this archive on `git_dirty is 'true', not false` — correctly.
  It is N-A instead, so that judgement is not being made at all.

The shipped `verification/policy_audit.md` self-reports `FAIL=1, HUMAN=6,
N-A=7, PASS=31` — 45 rows, of which the 7 N-A include M-REL.

---

## 6. The freshness rename hole (#66) — NOT taken, and structurally unavailable here

The hole: keep every evidence byte identical, rename the release directory to
the fiction the evidence quotes, and `check_manifest_consistency` stops firing.

MEASURED with `_RELPATH_RE` applied by hand to every `.txt`/`.md` file in
`verification/` (16 files): **0 matches, total, across all of them.** No
evidence file names a versioned release directory at all. Nor does any evidence
file quote a `06_build/staging` path — the one raw mention of the release root
anywhere in the archive is a sentence in `audit.txt` describing what the
contract requires, which carries no directory component and cannot match.

There is no evidence path for a rename to be made to agree with, so the
shortcut has not been taken and cannot be. **CONFIRMED CLEAN.**

---

## 7. The two `git check-ignore` traps — both reproduced, both avoided

The corrected rule is: map each staged path to the location it will occupy when
sealed, and ask git THERE — from the repository root, because `git check-ignore`
resolves relative paths against CWD.

| what was run | result |
|---|---|
| **correct rule**, seal path, CWD = repo root | **0 of 69 ignored** |
| non-vacuity probe: a `.kicad_prl` at the same seal path | **IGNORED**, by `projects/pluto-rx2-8way-v2/.gitignore:11:*.kicad_prl` |
| **trap A**, blanket sweep at the staging path | **69 of 69 ignored**, via `.gitignore:1:06_build/*` |
| **trap B**, the CORRECT rule with CWD inside `06_build/staging` | **69 of 69 ignored** — byte-identical to trap A |

**0 of 69 are ignored at the seal path, and the rule is demonstrably not
vacuous.** Trap B is the nastier of the two precisely because the rule is right
and the answer is still wrong; the only thing separating the correct result from
the catastrophic one is the working directory. Nothing was deleted.

---

## 8. Findings — CLASSIFIED

None of these blocks the DESIGN. F-1 and F-2 are archive-text findings; F-3 and
F-4 are gate findings that will outlive this board.

### F-1 — the stamped `git_sha` does not name the commit that holds this copper (MEASURED)

`git_sha: fe5fade5`, qualified as "HEAD at staging time", which is literally
true. But the board was rebuilt AFTER that commit and the rebuild landed in
`04e9b8eb`:

| board `.kicad_pcb` | sha256 (first 16) |
|---|---|
| `04_kicad` at `fe5fade5` — the stamped sha | `670fd9421f11ffb0` |
| `04_kicad` at HEAD `083dc488` | `cb8faaeb23924ede` |
| **the archive's `source/`** | **`cb8faaeb23924ede`** |

A reproducer who checks out the stamped sha gets the PRE-fix board — C25744, the
old copper. The archive matches HEAD. `source/*.kicad_pcb`, `.kicad_sch`,
`.kicad_pro` and `.kicad_dru` are all byte-identical to `04_kicad` at HEAD, so
the archive IS reproducible from committed state for its own files; the stamp
just points one commit too early. **Fix is one field** — restamp `git_sha` to
the commit that contains `04_kicad`, or add the sentence "the board in this
archive is `04e9b8eb`, not the stamped HEAD". Not order-blocking; it is a
provenance pointer, and M-REL (the gate that would read it) is N-A.

### F-2 — ELEVEN and NINETEEN are both in the archive, and only one is dated (MEASURED)

`MANIFEST.txt:26` says "NINETEEN paths are dirty **as this archive is
written**". ORDER_README section 7 item 2 says the tool "lists **eleven**
paths" in the present tense, under the heading "What is actually dirty". Both
numbers are true measurements of the same tool; they differ by the eight board
paths, and only the MANIFEST timestamps its own.

- At ORDER_README's mtime (16:21) the tool would have returned 19.
- At the previous stamp's moment it returned 11 — which the MANIFEST states
  explicitly at line 29 ("it was ELEVEN then"), so the two documents are
  consistent in intent.
- Right now it returns 11, and **the eleven names ORDER_README lists are exactly
  the eleven the tool prints**, name for name. I checked.

So the eleven is a correct measurement that is not anchored to a moment. This is
the mildest possible version of the defect class the section exists to
criticise, and it is worth one clause on the next revision: say *when*.

### F-3 — `verification/policy_audit.md` is a 5-line stdout dump, and two cross-checks go vacuous on it (MEASURED)

The shipped file is not the audit table. It is five lines: three wxWidgets
`PROPERTY_ENUM` assertion messages, the summary line, and **one FAIL line
truncated mid-word** — `...while the board has u`. It contains **zero** `|`
table rows.

Consequences, both inside the green above:

- `check_manifest_consistency` searches it for `^\s*\|\s*S-ERC\s*\|`. There is
  nothing to find, so the ERC agreement check runs on **2 comparands instead of
  3**. The two it has agree (0/213 both), so nothing is wrong today — but the
  three-way check is a two-way check and no one is told.
- The single FAIL the audit found (A-POP `MANIFEST-UNDECLARED`) is not legible
  in the shipped evidence. Its resolution is written up in ORDER_README, so the
  information is not lost, but the ARTEFACT does not carry it.
- A-EVID counts the file PRESENT because it exists. Nothing grades its content.

Separately and in the same check, `_manifest_bom_lines` returns **None** — it
needs the shape `bom_source_check ... (N lines`, and the MANIFEST writes
`bom_source_check     M-BOM PASS, every BOM LCSC == source`. So the BOM-line
cross-check performs **0 comparisons** against a `fab/bom.csv` that carries 11
data rows. Absence is not a mismatch by design, which is defensible; it is still
a denominator the reader is never shown.

### F-4 — `DESIGN: PASS` over zero documents, and the only gate that would notice is never run (MEASURED, = #75)

Restating with the numbers attached, because this is the finding with fleet
reach: `check_reviews` returns before grading anything when no contract-named
lens file is present, and the caller then prints `DESIGN: PASS`. A-EVID — the
one instrument that detects an ABSENT required review — is called by
`fleet_regrade.py` and by nothing else in the pipeline. On this archive the two
together produce: freshness RAW EXIT 0, `DESIGN: PASS`, four contract-required
reviews missing.

This board is not at risk from it, because the archive declares the gap in
ORDER_README section 7 item 3 in plain language. A board whose author did not
would sail through.

---

## 9. What I did NOT find

Stated explicitly, because a lens that only lists problems misrepresents its
denominator.

- No bijection defect, in either direction, including the directory census and
  the zip interior.
- No hash mismatch, no duplicate row, no malformed row, no symlink, no
  zero-byte file, no empty directory.
- No false checkable sentence surviving in MANIFEST or ORDER_README. I went
  looking specifically for the round-2 class and found none.
- No copper movement across the BOM fix — symdiff 0 on every element class,
  against the pre-fix board recovered from git rather than from a document.
- No DRC or unconnected or parity finding: 0 / 0 / 0, parsed, on the archive's
  own bytes, re-measured out of the repo. Both halves.
- No embedded foreign release path; the rename hole is not available here.
- No path ignored at its seal location; no repository file touched by this
  review.
- Sourcing measures CLEAR: 11 graded lines, all `OK`, verdict `PASS`, against
  11 coded+placed BOM lines at 5 boards. The evidence file carries its own
  correct caveat that a PASS is necessary and not sufficient.

Two order-time unknowns are open and both are already documented by the archive
rather than found by me: the possible mutual exclusivity of the ADVANCED
small-via option and impedance control (ADR-0006 deliberately does not pick a
reading), and the unpublished vendor rule for the mixed via<->pad hole class.
They belong to the fab-orderability lens; they contribute to DO-NOT-ORDER but
they are not integrity findings.

One observation with no finding attached: `export_jlc_package.py` sets
`SetCreateGerberJobFile(True)` but no `.gbrjob` exists anywhere under this board
(0 found). It is not contract-required, JLC's uploader does not need it, and
A-EVID does not miss it. Recorded only so it is not rediscovered as a mystery.

---

## 10. Owed, and what would move the order verdict

Nothing here is a `skills/` change I have applied — all three are PROPOSED.

1. **`check_reviews` must FAIL, not return, on `graded == 0`** when the archive
   claims a design verdict. The M-COVER precedent already exists eleven hundred
   lines away in `policy_audit.py`. Needs a known-bad fixture: a release with an
   empty `verification/` that goes RED.
2. **Wire A-EVID into the seal path**, or have `release_freshness_check` refuse
   to print `DESIGN: PASS` when the contract's required review set is not
   satisfied. Today the two gates cover each other's blind spot only if a human
   runs both and reads both.
3. **`policy_audit.md` should be captured as the audit TABLE**, not as stdout.
   The truncation is the visible symptom; the invisible one is that a
   cross-check silently loses a third of its comparands.

**To turn `order_verdict` to ORDER**, in the order they gate: land the four
contract-required reviews against THIS copper; commit `03_src/route.yaml` and
the four shared backend scripts so `git_dirty` can go false; restamp `git_sha`
(F-1); seal into a real release directory so M-REL stops being N-A; and get the
vendor's answer on the two open fab questions. The design does not need to
change for any of that — which is what `design_verdict: SOUND` means.
