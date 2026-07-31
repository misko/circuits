# pluto-rx2-8way-v2 — RELEASE-ARCHIVE INTEGRITY LENS (2026-07-31)

lens:            release-archive integrity — "does this archive stand alone and tell the truth?"
scope:           `06_build/staging/` (82 files on disk, 81 MANIFEST rows)
graded_at:       repo HEAD `9af663f0`, 2026-07-31
archive_git_sha: `c0e21fa7` (stamped in MANIFEST; verified present and an ancestor of HEAD)

design_verdict: DEFECTIVE
order_verdict:  DO-NOT-ORDER

**Not a copper defect.** The board's copper, netlist and DRC are clean and I
re-measured them myself. The archive is DEFECTIVE because it is a **coherent
snapshot of a design state the project has already left**: it ships the
schematic that fails S-OCCL with 13 occlusions, and declares that failure open,
**91 minutes after commit `9af663f0` fixed it to 0**. Every hash in it is
correct; what is wrong is the *tense*. A rebuild clears this — no design work
is owed.

## The one blocking finding, in one line

| | archive `source/` (would be sealed) | project `04_kicad/` (current) |
|---|---|---|
| `.kicad_sch` S-OCCL | **FAIL, 13 occlusions, RAW EXIT 1** | **PASS, 0 occlusions, RAW EXIT 0** |
| schematic population | wires 35, junctions 0 | wires 39, junctions 5 |
| `.kicad_pcb` electrical | — | **identical**, pad-for-pad (verified) |
| netlist | 40 nets / 130 nodes | **identical**, node-set for node-set |

The PCB and netlist did **not** move; only the schematic's de-collision pass
did. So the archive's **fab set is still electrically valid** — but its
`source/`, its `pdf/schematic.pdf`, its MANIFEST `policy_audit FAIL=2` line and
its ORDER_README §7 item 1 all now state something untrue about the design.

## Verdict basis (this lens only)

`DO-NOT-ORDER` because an order is placed from a *sealed* release, and this
archive **cannot seal as-is**: M-REL fails, the freshness gate fails, and the
archive is stale against its own project. `DEFECTIVE` is scoped to the archive,
not the copper. Neither key is inherited — both are re-measured below.

---

## 1. Bijection — BOTH directions. MEASURED, own walker.

Canon M1: I did not use `sha256sum -c`, and did not reuse any release script.
The walker is `os.walk` + `hashlib` + a text parse of the MANIFEST, written for
this review.

| property | result |
|---|---|
| files on disk | **82** |
| MANIFEST hash rows parsed | **81** |
| MANIFEST `files:` footer claim | **81** |
| duplicate rows | **0** |
| direction A — row with no file | **0** |
| direction B — file with no row | **1**, and it is `MANIFEST.txt` |
| hash mismatches | **0 / 81** |
| size mismatches | **0 / 81** |

**Direction B is the unguarded one and it is clean here.** The single unlisted
file is `MANIFEST.txt`, and the MANIFEST *declares* that exclusion in its own
table header ("MANIFEST.txt is the ONE exclusion — it cannot hash itself").
That is the difference from the `crow-recorder-central-v2` v1.5 precedent, where
a `.kicad_prl` sat in the archive unlisted while the header claimed to cover
"every file in this archive". Here the claim and the tree agree.

I re-ran the walker after all my own tooling had touched the tree; the result
was byte-identical, so nothing I did contaminated the archive.

## 2. `.kicad_prl` / `.lck` — CLEAN, and the strip-last ordering is PROVEN

| class | on disk | in MANIFEST |
|---|---|---|
| `*.kicad_prl` | **0** | **0** |
| `*.lck` | **0** | **0** |
| `*-backups/`, `_autosave-*`, `*.bak`, `*~`, dotfiles, `.DS_Store` | **0** | **0** |

**MEASURED, not inherited:** when I copied `source/` out of the repo and ran
`kicad-cli pcb drc` on it, kicad-cli **created**
`pluto_rx2_8way_v2.kicad_prl` (2304 bytes) in my copy — one file, from one
read-only-intent DRC invocation. The regeneration hazard is real and I
reproduced it. The archive carrying zero therefore proves the strip ran **after**
the last kicad-cli invocation, which is the ordering `cooksense` v1.7 got wrong
(its `MANIFEST.txt:445` hashes a `.kicad_prl` its `source/` lacks).

Worth naming for whoever seals: the board `.gitignore` carries `*.kicad_prl`, so
a stray would be **invisible to `git status`** while still sitting in the
archive. Archive cleanliness here cannot be delegated to git — it was achieved
by ordering, and only a walker like §1 can confirm it.

**Operational hazard, unresolved by anything in this archive:** verifying a
*sealed* release in place would contaminate it, because DRC writes a `.kicad_prl`
next to the board. Verification must always be done on a copy. That is what I
did and what `standalone_archive_drc.json` implies was done.

## 3. Standalone — the archive really does stand alone. MEASURED.

`source/` copied to `/tmp/rx2v2_standalone/source` (outside the repo, `git
rev-parse` there returns "not a git repository"), then:

```
kicad-cli pcb drc --severity-all --refill-zones --schematic-parity
```

**RAW EXIT 0** — unpiped.

**CLASSIFIED, both halves, from the JSON rather than the summary line:**

| class | count | key present in JSON? |
|---|---|---|
| `violations` | **0** | yes — empty array, not an absent key |
| `unconnected_items` | **0** | yes — empty array, not an absent key |
| `schematic_parity` | **0** | yes — empty array, not an absent key |

The "key present" column matters: a 0 read off an absent key is the M-COVER
shape and would be worth nothing. All three keys exist and hold genuinely empty
arrays, in my run and in the two shipped JSONs (`drc.json` 09:07:27,
`standalone_archive_drc.json` 10:27:15, mine 11:47:28 — three independent runs,
same result).

**The mechanism is verified, not assumed.** ORDER_README §6 claims the archive
stands alone because `source/fp-lib-table` is repointed and the `.pretty` is
vendored. Confirmed by diff:

- archive: `(uri "${KIPRJMOD}/pluto_rx2_8way_v2.pretty")` — self-contained
- in-repo `04_kicad/`: `(uri "${KIPRJMOD}/../03_src/lib/pluto_rx2_8way_v2.pretty")` — escapes the archive

§6's counterfactual ("a standalone copy carrying *that* table raises 12
`lib_footprint_issues`") is about the **in-repo** table, not the shipped one. My
run used the shipped table and got 0. The two statements are consistent and I
corroborate the claim.

## 4. M-REL — ungraded, but NOT for the reason the MANIFEST gives

The MANIFEST devotes a paragraph to why M-REL is ungraded. Two of its four
claims are wrong, and both errors are in the *safe* direction.

| MANIFEST claim | measured | verdict |
|---|---|---|
| "M-REL IS UNGRADED ON THIS ARCHIVE" | true | **TRUE, wrong reason** |
| regex admits two layouts, this ships a third, so it verifies ZERO rows | **0 of 81 rows match** | **TRUE** |
| "the backstop tests for `sha256:`, which this banner does not contain" | the string **IS** present | **FALSE** |
| "a green M-REL here would be evidence of nothing" | M-REL goes **RED**, not green | **FALSE** |

**Why it is ungraded right now** is simpler than the MANIFEST says: `07_releases`
is empty, so `policy_audit.py:1692` takes the `else` branch and emits
`M-REL N-A "no releases yet"`. The hash-verification block at :1641–1665 is
**never reached**. The whole regex discussion is a statement about seal time,
not about the present grade.

**The regex claim is correct and I measured it:** running the exact pattern from
`policy_audit.py:1643-1646` against this MANIFEST yields **0 matches** across
81 rows. The layout `<hash>  <size>  <path>` defeats both admitted alternatives —
the size field sits where the path-first branch expects whitespace, and the
hash-first branch's `[\w./-]+` cannot span the gap to the path.

**The backstop claim is false, self-referentially.** The MANIFEST says its banner
does not contain the literal `sha256:`. It does — at **`MANIFEST.txt:81`**, inside
the very sentence denying it:

```
literal substring "sha256:", which this banner does not contain. So M-REL
```

`policy_audit.py` tests `"sha256:" in mt` where `mt` is the **whole MANIFEST
text**, not "the banner". So the condition holds and the backstop fires. The
document's disclosure of the vulnerability is the thing that closes it.

**Verified end-to-end, not merely reasoned.** I copied the project to a scratch
tree, promoted `staging/` into a release directory, and ran the real
`policy_audit.py --skip-drc`:

```
FAIL M-REL: git_sha c0e21fa7... not in repo; sha256 table yielded ZERO readable entries again
```

The second clause is the M-COVER backstop firing. (The `git_sha ... not in repo`
clause and a separate `E-INV` failure are **artifacts of my simulation** — the
scratch tree is not a git repo and I did not copy `06_build/netlists/`. In the
real repo the sha resolves and the netlist exists. I discount both; neither is a
finding against the board.)

**So the operational conclusion is the opposite of the MANIFEST's:** at seal
time M-REL does not go silently green — it goes **RED and blocks**, correctly,
because it can verify nothing. The seal is blocked until either the MANIFEST
adopts one of the two admitted layouts or the regex learns this one. That is a
`skills/` change; **proposed below, not applied.**

## 5. Freshness — re-run, unchanged, and the shortcut is still refused

```
/usr/bin/python3 skills/jlcpcb-fab/scripts/release_freshness_check.py \
    projects/pluto-rx2-8way-v2/06_build/staging \
    --releases-root projects/pluto-rx2-8way-v2/07_releases --claim both
```

**RAW EXIT 1** — `DESIGN: FAIL (10)`, `SOURCING: CLEAR`.

Confirmed: **all 10 findings are in review documents. Zero concern the board,
the fab set, or any machine evidence.**

| class | n | which files |
|---|---|---|
| `EVIDENCE PATH MISMATCH` | **8** | archive-integrity review (**3 on its own**), fab-manufacturability, `pin_review.md`, `redteam_layout.md`, `redteam_topology.md`, `render_review.md` |
| `REVIEW-NO-VERDICT` | **2** | `redteam_topology.md`, `redteam_layout.md` |

Both `REVIEW-NO-VERDICT` files **do** state `design_verdict: DEFECTIVE` — at
lines 211 and 77, below the 40-line window `_REVIEW_HEADER_LINES = 40` reads.
M-REV gives a false *reason* for a true *refusal*. **This review states its keys
at line 9-10 for exactly that reason.**

**The fictitious-name shortcut is still refused, and should stay refused.**
Sealing under the never-created name `v1.0-2026-07-30` would turn 8 of the 10
findings green without making one word of the evidence truer. Confirmed the
previous agent's refusal stands. Two notes for whoever seals:

- The fleet's actual naming convention is **board-prefixed** — the five sealed
  boards use e.g. `crow-mic-pod-v2-v1.0-2026-07-23`. So `v1.0-2026-07-30` was
  never a plausible directory name here regardless; the correct one would be
  `pluto-rx2-8way-v2-v1.0-<date>`.
- The gate's regex is `07_releases/(<segment containing v\d>)/`. A review that
  *quotes* such a path **becomes a finding** — which is why the previous
  archive-integrity review contributes 3 of the 8 by itself. **This review
  writes every directory name bare, without the prefix, to avoid adding to the
  count it is reporting.**

## 6. MANIFEST truthfulness — independently re-derived. It is honest.

I re-derived the MANIFEST's headline numbers from the artifacts themselves
rather than trusting its summary. **Every one matched exactly.**

| MANIFEST claim | my independent measurement | |
|---|---|---|
| 3446 vias, every one 0.2500/0.1500 mm | 3446 vias, histogram `{(0.25,0.15): 3446}` — single bin | ✓ |
| 50 PTH pads at 1.400 mm | 50, all 1.4 mm | ✓ |
| 4 NPTH at 3.200 mm | 4, all 3.2 mm | ✓ |
| 3500 holes total | 3446 + 50 + 4 = 3500 | ✓ |
| "3446 of the 3496 PLATED holes under process minimum" | plated = 3446 + 50 = 3496 | ✓ |
| ERC 0 errors (209 warnings) | `erc.json`: 0 errors, 209 warnings | ✓ |
| bom_source_check over 11 BOM lines | `fab/bom.csv`: 11 data rows | ✓ |
| CPL histogram top=27, bottom=0 | `fab/cpl.csv`: 27 rows, all `top` | ✓ |
| DRC 0/0/0 | reproduced standalone, §3 | ✓ |

The freshness gate's `check_manifest_consistency` also raised **no**
`MANIFEST/EVIDENCE MISMATCH` finding, independently corroborating the DRC/ERC/BOM
figures against the shipped evidence.

**Conclusion: the archive does not overstate a single measured number.** Its only
false statement is the `sha256:` self-description at line 81 (§4), and its only
systemic problem is tense (§8).

## 7. `git_sha` / `git_dirty` stamping — HONEST, and it is what caught §8

| field | stamped | verified |
|---|---|---|
| `git_sha` | `c0e21fa7ac2ab25cce718eaedf49ee84e3fae284` | **exists**, `git cat-file -t` = commit; **ancestor of HEAD** (RAW EXIT 0) |
| `git_dirty` | `true` | **true**, with the reason named rather than rounded off |

The stamp declares its scope (`projects/pluto-rx2-8way-v2/` + `skills/`) and
names the single dirty path — a sibling workflow's uncommitted edit to
`route_and_stitch_generic.py`, still dirty now. It explicitly refuses to stamp
`false` to make a gate green. **That is the honest form**, and it earned its
keep: the stamp is precisely the instrument that let me detect §8. Had it been
absent or falsified, the staleness would have been invisible.

## 8. THE BLOCKING FINDING — the archive is stale against its own project

The MANIFEST stamps `c0e21fa7`. HEAD is `9af663f0`. **Two commits landed after
the archive was assembled**, and one of them is a regeneration of this board:

```
9af663f0 rx2-v2 regenerated through its own driver: S-OCCL 13 -> 0, and the netlist did not move a node
a0e6fe60 the de-collider had never seen a wire, and nine of the thirteen findings were not even labels
```

| artifact | archive (10:06) | project (11:35–11:37) | |
|---|---|---|---|
| `.kicad_sch` | `aa25160b…`, 109 793 B | `cdb9232e…`, 110 879 B | **DIFFERENT** |
| `.kicad_pcb` | `74c60be4…`, 881 150 B | `ae25fcb9…`, 881 150 B | **DIFFERENT** |
| `.kicad_pro`, `.kicad_dru` | — | — | identical |

**What actually changed — measured, not assumed:**

- **Schematic: a real change.** S-OCCL **13 → 0** (RAW EXIT 1 → 0). Population
  went wires 35 → 39, junctions 0 → 5: the de-collision pass added four wires
  and five junction dots to route conductors clear of text.
- **PCB: reserialization only.** Despite a 14 852-line diff, the boards are
  electrically identical — footprints 32, tracks 199, arcs 0, vias 3446, zones
  6, nets 40, pads 143, track copper 390.434 mm, **all equal**, and the full
  `(refdes, pad, net)` map, the net-name set and the refdes set are **identical**.
- **Netlist: identical.** 40 nets, 130 nodes, net-name sets equal, **zero** nets
  with a differing node set. The commit message's "did not move a node" is
  corroborated independently.

**Why this blocks the seal.** The archive is internally perfect (§1) and honest
about what it measured (§6) — but it would seal:

1. a `.kicad_sch` and a `pdf/schematic.pdf` carrying **13 occlusions that are
   already fixed upstream**;
2. a MANIFEST reading `policy_audit FAIL=2` and an ORDER_README §7 item 1
   itemising those 13 occlusions as an **open, unwaived defect** — a statement
   that is **no longer true of this design**;
3. a permanent, immutable record understating the board.

This is the inverse of the usual failure. The archive does not overclaim; it
**underclaims**, preserving a defect the project has already retired. Sealing it
would make the fleet's record of this board worse than the board.

**The fix is a rebuild, not design work.** Re-run `03_src/rebuild_all.sh` at
current HEAD, re-export, re-stage, re-stamp. The copper is already correct — the
gerbers in this archive would produce the right board today. Nothing electrical
is owed.

## 9. ORDER_README — verdict keys and the retyped-number trap

| check | result |
|---|---|
| `design_verdict: DEFECTIVE` (line 7) | in `SOUND\|DEFECTIVE` ✓ |
| `order_verdict: DO-NOT-ORDER` (line 8) | in `ORDER\|DO-NOT-ORDER\|BLOCKED-SOURCING` ✓ |
| both inside the 40-line window | ✓ (lines 7–8) |
| gate table retypes a MANIFEST count | **no — and deliberately so** |

The 62-vs-63 defect is **fixed, and fixed at the right level**. ORDER_README §6
now says the count "is stated in the MANIFEST's own footer rather than retyped
here, because a hand-copied count is exactly what went wrong last revision".
Grepped: there is **no bare `81`** anywhere in ORDER_README. The document asserts
the *property* (bijective both ways) and defers the *number* to its single
source. That is the correct repair — it removes the class, not the instance.

## 10. Gitignore — a non-finding for the seal, but state it plainly

All **82** archive files are gitignored, by `projects/pluto-rx2-8way-v2/.gitignore:1:06_build/*`,
and **0 of 82** are tracked. This is by design — the archive lives under
`06_build/`, which is build output.

Probed the sealed location: a path under the `07_releases` tree is **not**
ignored, and the five sealed boards do track their MANIFESTs. So the "0
gitignored paths" requirement is satisfied at the destination and this is a
non-finding for the seal.

It is still worth stating: **right now this archive exists only on this disk.**
It is not preserved by git in any form. Until it is promoted, a lost working
tree loses it.

---

## Proposed `skills/` changes — PROPOSED, NOT APPLIED

1. **`policy_audit.py:1643-1646` — M-REL regex admits a third layout.** Add
   `<hash>  <size>  <path>`. Concretely, allow an optional numeric field between
   hash and path in the hash-first branch. Needs a KNOWN-BAD fixture per the
   testing contract: a MANIFEST in this layout with one corrupted hash must make
   M-REL **fail**, proving the branch can bite. Until then M-REL cannot pass on
   any archive using this layout.

2. **`policy_audit.py:1660` — the zero-coverage backstop keys on `"sha256:"`,
   a banner-formatting accident.** It happened to fire here only because the
   MANIFEST's prose quotes the string. Any archive whose banner says "sha256,
   size, path" — no colon — and whose rows the regex misses would get a silent
   green. The guard should key on **structure** (a hash table was expected
   because rows of 64-hex exist / the archive is non-empty), not on a substring.
   Suggested: fire whenever `_hashed == 0 and _n_files` and the text contains any
   64-hex-char token, dropping the `"sha256:"` conjunct entirely.

3. **`policy_audit.py:2023` — `print(f"  FAIL {cid}: {det[:110]}")` truncates
   mid-word with no ellipsis.** Measured here: the M-COVER message is cut inside
   the word "against", so the operator reads

   > `sha256 table yielded ZERO readable entries again`

   — a grammatical sentence that **silently loses the denominator (82 files) and
   the `(M-COVER)` tag**. A hard character cut that can produce a different valid
   sentence is the same failure class as the summarised-unconnected-items
   precedent. Suggest truncating on a word boundary and always appending `…`.

## What I did NOT verify (declared blind spots)

- **Fab-set correctness** (gerber/drill/BOM/CPL semantics) — another lens. I
  checked only that the fab files are hashed, present, bijective, and that the
  MANIFEST's counts about them re-derive.
- **RF/electrical and layout judgement** — other lenses.
- **`.step` geometry** — hashed and present; contents not inspected.
- **The 209 ERC warnings** — counted, not adjudicated.
- **Whether other lenses' findings this round change the design verdict.** My
  `DEFECTIVE` rests solely on §8.
- The freshness count of 10 will move as this round's lenses land; it is a
  measurement of the review set, which is still changing as I write.

## Bottom line

The archive **stands alone** — proven by an out-of-repo DRC at 0/0/0 with all
three JSON keys genuinely present and empty, on a vendored footprint library and
a repointed lib table. It is **bijective in both directions** with zero hash or
size mismatches, carries **no `.kicad_prl`**, and does **not overstate a single
measured number**.

It does not tell the truth about **when**. It preserves, as an open unwaived
defect, 13 schematic occlusions that commit `9af663f0` reduced to 0 ninety-one
minutes after the archive was built — and it would seal that as the permanent
record. The copper is untouched and correct; the netlist did not move a node.

**Rebuild at current HEAD and re-stage. Do not seal this snapshot, and do not
seal it under a name chosen to make a gate green.**

---

# ADDENDUM (same session, after the sections above were committed)

Verifying §2's strip-last claim against the *project* rather than the archive
turned up a live stray, and pulling that thread found a fleet-wide blind spot.
The verdict keys at the top are unchanged — none of this alters the pluto-rx2
archive, which is still clean (§1, §2) — but two sealed releases are affected.

## 11. A `.kicad_prl` is in this board's `04_kicad/` RIGHT NOW, invisible to every gate

```
projects/pluto-rx2-8way-v2/04_kicad/pluto_rx2_8way_v2.kicad_prl   2304 B   11:35:45
```

**I did not create it.** Its mtime is 11:35:45, before my session's first tool
call (~11:42) and before my only `pcbnew.LoadBoard` on that file (11:50:52). It
carries the same second as `fp-lib-table` and `refdes_waiver.json` — it is a
dropping of the 11:35 rebuild that produced commit `9af663f0`.

It is harmless as *content* — a `.kicad_prl` is never design data. It matters
because it sits in `04_kicad/`, which CLAUDE.md calls immutable and
generator-owned, and because **three independent mechanisms each fail to see it**:

| mechanism | why it misses this file | MEASURED |
|---|---|---|
| `generate_rules_generic.py:119` purge | globs `*.kicad_pcb.kicad_prl` — the **double** extension. The real file is plain `<board>.kicad_prl` | `glob('*.kicad_pcb.kicad_prl')` → `[]`; `glob('*.kicad_prl')` → `['pluto_rx2_8way_v2.kicad_prl']` |
| `git status` | `.gitignore:11:*.kicad_prl` | `git check-ignore` → IGNORED |
| `contracts_audit.py --present` | population is *tracked ∪ untracked-not-ignored*; a gitignored file is in **neither** | 26 `.kicad_prl` listed fleet-wide, **0** of them this one |

The double-extension restriction is deliberate and correct **for `.kicad_pro`** —
the code comment explains a genuine second `.kicad_pro` must still abort. But a
`.kicad_prl` is *never* content, so the same caution buys nothing there and
costs the purge its target.

**The gitignore rule is what blinds the detector.** The 26 strays the audit
*does* report all live under boards whose `.gitignore` lacks `*.kicad_prl`
(verified on two). Sixteen boards carry the rule; those are exactly the boards
where a stray cannot be seen. This is the "gate negation blindness" shape again:
the rule that keeps the tree tidy is the rule that hides the mess.

## 12. Two SEALED, IMMUTABLE releases contain a `.kicad_prl` — and one was written AFTER sealing

Swept the sixteen blind boards. Three sealed release trees hold one:

| sealed release (named bare, see §5) | file | in its MANIFEST? | file mtime vs seal date |
|---|---|---|---|
| `crow-recorder-central-v2-v1.5-2026-07-25` | `source/crow_recorder_central_v2.kicad_prl`, 2311 B | **NO** | 2026-07-26 — **1 day after** |
| `interposer-v1.1-2026-07-27` | `source/interposer.kicad_prl`, 2297 B | **NO** | 2026-07-31 02:38 — **4 days after** |
| `cooksense-v1.7-2026-07-30` | `source/cooksense.kicad_prl`, 2296 B | **YES**, line 445 | 2026-07-30 21:46 |

**Two corrections to the framing I was given:**

1. **`cooksense-v1.7` is no longer the defect it was described as.** The brief
   says its `MANIFEST.txt:445` hashes a `.kicad_prl` its `source/` *lacks*. That
   is **not true now**: the file is present, and its hash **matches the MANIFEST
   exactly** (`a2e8ca51…` both sides, re-derived with hashlib). That row is
   bijective. It still ships process state inside an immutable release, which is
   its own defect — but not the one on the ticket.

2. **`interposer-v1.1` is a third instance nobody has named**, and it is the
   clearest evidence of the mechanism: sealed 2026-07-27, and its `.kicad_prl`
   was written **2026-07-31 at 02:38** — today. Something opened that sealed
   board four days after it was sealed and wrote into it.

`crow-recorder-central-v2-v1.5` is confirmed exactly as described: present in
the archive, absent from its own MANIFEST, while that MANIFEST's header claims
to cover "every file in this archive". **This is the direction-B violation, and
it is still live.**

**The generalisation:** `kicad-cli` writes a `.kicad_prl` beside any board it
opens (§2, reproduced). Sealed releases get opened — for comparison, for
re-measurement, for exactly the kind of verification this review round performs.
Because `*.kicad_prl` is gitignored on all three boards, the write is invisible
to `git status` and to `contracts_audit --present`. **Immutability is being
violated by the act of inspection, silently, and the fleet's own stray detector
is structurally unable to report it.**

This is not hypothetical for the board in front of me: the archive I graded is
clean only because a strip ran after the last kicad-cli invocation. The `04_kicad/`
it was built from is **not** clean right now (§11). A re-stage that copies
`04_kicad/` wholesale, without re-running the strip last, reproduces
`crow-recorder-central-v2-v1.5` on this board.

## Additional proposed `skills/` changes — PROPOSED, NOT APPLIED

I did not delete any of these files. `04_kicad/` and `07_releases/` are
immutable; the sealed instances in particular must be dispositioned by whoever
owns those boards, not swept by a reviewer, and the correct repair for a sealed
release is a new version plus `SUPERSEDED.md`, never an edit.

4. **`generate_rules_generic.py:119` — purge plain `*.kicad_prl` too.** Keep the
   double-extension caution for `*.kicad_pcb.kicad_pro` (a genuine second
   `.kicad_pro` must still abort), but a `.kicad_prl` is never content and the
   plain form is the one that actually appears. Known-bad fixture: drop a
   `<board>.kicad_prl` in a fixture `04_kicad/`, assert the rebuild removes it,
   and RED-verify against the current glob — which leaves it.

5. **`contracts_audit.py --present` — a gitignored file must not be
   unauditable.** Its population (*tracked ∪ untracked-not-ignored*) means any
   pattern a board chooses to ignore becomes a hole in the stray detector, and
   the sixteen boards carrying `*.kicad_prl` are all holes. Suggest a
   forbidden-class sweep that runs over the raw filesystem regardless of ignore
   status, at minimum for `*.kicad_prl` / `*.lck` under `04_kicad/` and
   `07_releases/`. It would have found all four files in this addendum.

6. **A seal-time and inspection-time invariant.** `07_releases/**` should be
   asserted free of `*.kicad_prl` / `*.lck` *after* any tooling that opens a
   board, not only at seal. The `interposer-v1.1` timestamp shows seal-time-only
   checking is insufficient: the file arrived four days later.

## Revised bottom line

Everything in §1–§10 stands. The pluto-rx2-8way-v2 staging archive is bijective
both ways, carries no `.kicad_prl`, stands alone at DRC 0/0/0, and overstates
nothing. It is **stale**, by 91 minutes and one fixed schematic defect, and that
is why it must not be sealed as-is.

The addendum does not change that verdict. It adds a warning for whoever
performs the rebuild: **the `04_kicad/` you will re-stage from is not clean, and
neither `git status` nor the stray audit will tell you.** Strip last, then verify
with a walker that ignores `.gitignore` — the archive graded here proves that
ordering works, and §11–§12 show what happens on the boards where it did not run.
