subject: crow-recorder-central-v2 v1.4-2026-07-25 (STAGED, pre-stamp)
date: 2026-07-25
reviewer: redteam-agent (zero-context adversarial release lens, integrated — fix-pass scoping)
context-given: zero-context (staging archive + predecessor v1.3 read-only + 01_docs design docs + 02_parts + 03_src + 04_kicad + the release contract + the gate scripts; journals/learnings/STATUS/08_reviews withheld)
verdict: DO-NOT-ORDER

Reviewed the STAGING directory before the seal's stamp step. Archived VERBATIM
below, unedited (including the reviewer's own typographical artifacts).
Dispositions: 08_reviews/DISPOSITIONS.md rows FL4-* and the release's
verification/review_dispositions.md.

---

I have everything measured. Writing the review.

# ADVERSARIAL RELEASE REVIEW — crow-recorder-central-v2 v1.4-2026-07-25 (STAGED)

**Reviewer posture:** zero-context, adversarial. Every number below was measured by me against the staged bytes, not read out of the release's own prose.
**Measurement anchor:** `2026-07-25T15:53:15-07:00`. Anchored sha256 of the artifacts my findings quote:

| file | sha256 |
|---|---|
| `MANIFEST.txt` | `1268facfcd5ffce39cffd01a0dcfe4406d518dc120085cfaf9a75ad191d1b49a` |
| `verification/policy_audit.md` | `8677ef6740defed9a18db75ff337cf6767a848336307e71df42da8bf1b81e7eb` |
| `verification/release_freshness.txt` | `5b8fd17e1da220c21a462f9b3cf1eb2f3730de5363694fe75040c443665bb65f` |
| `fab/cpl.csv` | `eb2cdf7c6bc0f21c2e07e4d0ce3ded75adeb7de1e36178d3967f2095ee0ece19` |

**Headline:** the fab payload is clean and the rotation fix is real and well-evidenced. The *release* is not. The MANIFEST asserts a gate result that the release's own shipped evidence contradicts, has no provenance and no integrity table, and cites a review file that does not exist. Four P0s, all in paperwork, none requiring a fab byte to change.

---

## (a) Findings table

| # | Finding | Sev | Evidence I measured | Disposition |
|---|---|---|---|---|
| F1 | **MANIFEST contradicts its own shipped audit.** MANIFEST line 72 states `policy_audit 0 FAIL`. The bundled `verification/policy_audit.md` states `\| M-REL \| FAIL \| git_sha not an exact commit: 'PENDING'; git_dirty not false \|` and `Summary: FAIL=1, HUMAN=6, N-A=3, PASS=27, WAIVED=2`. | **P0** | I re-ran the gate: `release_freshness_check.py <rel>` → `AUDIT/MANIFEST DISAGREEMENT: shipped policy_audit.md reports FAIL=1 [M-REL] … but MANIFEST claims policy_audit FAIL=0` → `FRESHNESS: FAIL (1 finding(s))`, **exit 1**. | BLOCK. Complete the stamp (step 2 of the seal procedure), re-run policy_audit, then re-run freshness. Do not hand-edit the MANIFEST claim to match. |
| F2 | **MANIFEST sha256 table is EMPTY.** Line 113 reads `sha256:` and the file ends. | **P0** | `find … -type f ! -name MANIFEST.txt \| wc -l` = **58 files**; table entries = **0**. Predecessor v1.3 for comparison: **53 entries / 53 hashable files** (54 minus `SUPERSEDED.md`, legally added post-seal). Contract *Validate*: every file in the table and every table entry has a file — **both directions**. Coverage here is 0/58 and 0/58. | BLOCK. Integrity is unverifiable in either direction; the archive cannot be shown to still be what was sent. |
| F3 | **No provenance.** `git_sha: PENDING`, `git_dirty: PENDING`. | **P0** | `git cat-file -e PENDING` → `fatal: Not a valid object name PENDING`. `git status --porcelain -- projects/crow-recorder-central-v2/ skills/` = **11 entries at anchor**, including **untracked `03_src/rules/assembly.yaml`** — the file A-POP grades against. The release's population declaration exists only in a working tree. | BLOCK. Source-commit the inputs, then stamp. |
| F4 | **The shipped freshness evidence does not describe the shipped bytes.** `verification/release_freshness.txt` ends `MISSING: verification/policy_audit.md (cannot verify the manifest's claimed audit result)` / `FRESHNESS: FAIL (1 finding(s))`. But `verification/policy_audit.md` **is present** (mtime 15:43:38, three seconds *after* the freshness run at 15:43:10). | **P0** | Re-running the gate now yields a *different* finding (F1), not this one. So the archived verdict is stale in content, not just in time. Evidence that disagrees with its own artifact is not evidence. | BLOCK. Regenerate after the stamp so the shipped file grades the shipped bundle. |
| F5 | **MANIFEST cites a review file that does not exist.** Lines 73–74: `Fresh-context zero-knowledge lens over these STAGED bytes: ORDER (verification/fresh_lens_v1.4.md)`. | P1 | Scripted every `verification/…` path in MANIFEST against the filesystem: exactly one真 miss — `verification/fresh_lens_v1.4.md`. Not in the 59-file tree. | Ship the review or delete the claim. An asserted ORDER verdict with no document is the strongest single reason to distrust this MANIFEST. |
| F6 | **v1.4 has no release-level review evidence of its own.** `redteam_topology.md` and `redteam_layout.md` are **sha256-identical to v1.3's** and name only v1.1/v1.2 internally. | P1 | Version tokens inside: topology → `v1.1`×11, `v1.2`×6, zero v1.3/v1.4. Layout → `v1.1`×7, `v1.2`×4. Both read `verdict: ORDER`. Combined with F5, **no lens has graded v1.3's or v1.4's bytes** — and v1.3 is the release that shipped seven wrong rotations. | Contract requires both lenses = ORDER *for this release*. Re-run at least one integrated lens (fix-pass scoping) and archive it. |
| F7 | **`01_docs/CHANGELOG.md` has no v1.4 entry.** | P1 | Latest `Released:` line is `crow-recorder-central-v2-v1.3-2026-07-24` (line 18). No line names the v1.4 directory. Contract *Validate* requires one. | Add with the seal commit. |
| F8 | **v1.3 carries no `SUPERSEDED.md` at anchor.** v1.4's MANIFEST and ORDER_README both declare v1.3 **DO-NOT-ORDER FOR PCBA**, but nothing inside v1.3's directory says so. | P1 | `ls v1.3/SUPERSEDED.md` → *No such file*. It **existed** at the start of this review (my first `find` and my sha-tree diff both listed it) and was deleted by 15:51. Anyone opening `07_releases/` today sees a defective release with no marker. | Restore before/with the seal commit. Contract: "Every superseded sibling carries `SUPERSEDED.md`." |
| F9 | **The method behind the release's most important fix claim is not archived and not even in git.** V14-F2 (the independent rotation re-derivation) was produced by `06_build/tmp/rot_remeasure.py`. | P1 | `git check-ignore -v` → `projects/crow-recorder-central-v2/.gitignore:1:06_build/*` — **gitignored**. Not among the 59 release files. The *output* (`rotation_remeasure.txt`) is archived; the *method* survives only as an untracked temp file. | Promote to `skills/jlcpcb-fab/scripts/` (with the RED-verified operator test) or vendor into `verification/`. Contract completeness test: a future reader must be able to re-run this. |
| F10 | **The staging directory was mutated during this review.** | P1 | `MANIFEST.txt` mtime **15:50:18** — mid-review; the `policy_audit 0 FAIL` line moved from line 70 to line 72 between my two reads. `v1.3/SUPERSEDED.md` deleted. `01_docs/CHANGELOG.md` went from ` M` to clean. | Any verdict — mine included — is against a moving target. Freeze the directory, then re-gate, then review. |
| F11 | No `msl:` line in the MANIFEST. Contract: *"The `msl:` line is REQUIRED for every consigned part and every exposed-pad package."* | P2 | MANIFEST has `consigned:` with MSL-3/168h prose embedded, and ORDER_README §3b is genuinely thorough (5 numbered steps, datasheet §14.5 p.33 cited). But `grep -rn "msl" skills/jlcpcb-fab/scripts/*.py` → **zero hits**: no gate enforces this contract clause anywhere in the fleet. | Add the line; separately, the unenforced clause is a gate gap worth its own work item. |
| F12 | **Two different numbers for the same measurement.** `jlc_lcsc_rotations.csv` row C6938291 evidence: *"rms 0.2047mm @270 vs 11.98mm next best (58x)"*. Shipped `rotation_remeasure.txt` for U1: **rms 0.0025 @270, next 11.9812, 4811x**. MANIFEST quotes the 4811x figure. | P2 | Ratios: 11.9812/0.2047 = 58.5; 11.9812/0.0025 = 4792. Same part, same day, two residuals differing 80×. | Reconcile (likely a differing pad-inclusion set) and state which run is authoritative. Both point to 270, so the *conclusion* is unaffected. |
| F13 | `fab/bom.csv` MPN column is blank on **49/49** rows; the `Comment` column carries the LCSC code for ICs (e.g. `C6938291,U1,TQFP-128…,,C6938291`). | P2 | Parsed the CSV directly. Orderable — JLC sources from the LCSC column — but ORDER_README §3a instructs the operator to record "final supplier + MPN for every manually-sourced line" from a BOM that contains no MPNs. | Note only; byte-identical to v1.2/v1.3 and M-BOM PASS. |
| F14 | J3–J10 ship as 8 coded `C9900035627` BOM lines at **stock 0** while deliberately off the CPL. ORDER_README says confirm they're absent from the placement preview, but never says what to do when JLC's quote engine flags the zero-stock BOM line. | P2 | `stock_check.json`: `C9900035627, qty 8, LOW_STOCK(0)`. CPL cross-check: none of J3–J10 on the CPL. | Add one sentence to §3: "if JLC flags C9900035627 as unavailable, that is expected — the line is not placed." Saves a support round-trip. |
| F15 | ORDER_README §0 analyzes only PoE **"mode B (4/5 = +, 7/8 = −)"** and calls it an *endspan* injector. Alternative A (1/2, 3/6) is the more common endspan mode and would inject onto **AUDIO±** and the **beeper pair** — a different damage path the section never analyzes. | P2 | Read against the stated pinout `1,2=AUDIO±; 3,6=+5V_BEEP/RTN; 4,7=+5V_AUDIO; 5,8=GND`. | Conclusion ("never plug into Ethernet") is unaffected; the *analysis* is half-complete. Broaden the sentence. |
| F16 | `twin_report.txt` trailer: `TRANSIENT FETCH FAILURES (1): ['C9900035627'] … these parts were never checked, so this run does NOT constitute twin verification for them.` MANIFEST summarizes as `twin exit 0`. | P2 | The part is adjudicated with a dated 8-attempt measurement and is off the CPL, so impact is nil — but the MANIFEST's one-liner is rosier than the report it summarizes. | Note only. |
| F17 | `stock_check.json` `"bom"` field names `06_build/fab_v14/bom_jlc.csv` — outside the archive. | P2 | Content reconciles exactly with `fab/bom.csv` (49 lines / 47 coded / 2 uncoded), so the grading is correct. But the evidence points at a path a future reader won't have. | Note only. |

**No P0 exists in `fab/`, `source/`, `pdf/` or `3d/`.** Every P0 is in the release paperwork.

---

## (b) The ten mandated checks, measured

### 1. CPL diff — **PASS**
Parsed both CSVs, compared every field of every row keyed by Designator.

```
v1.3 rows 177   v1.4 rows 177     added 0   removed 0
header identical: True            designator order identical: True
CHANGED CELLS: 7   — all in column index 6 (Rotation), all '90.0' -> '270.0'
   D_USB, U1, U2, U3, U5, U7, U8
CONTROLS: Q1 / Q2 / U9 whole row byte-identical = True / True / True
```
Exactly 7, all Rotation, all 90.0→270.0. No eighth row. Q1/Q2/U9 untouched. Re-confirmed at anchor after the directory moved. **The claim holds exactly.**

CPL rotation histogram (v1.4): `0.0`×162, `270.0`×10, `180.0`×5, all `top`, 177 rows. The extra 270s (`C_c10`,`C_c11`,`C_c13`) and 180s (`C_c9`,`U10`) are board-rotated parts with offset 0 — correctly not part of the per-LCSC set.

### 2. Payload identity — **PASS (20/20)**
sha256 of every file in both trees:

```
common files 50   identical 30   differing 20
PAYLOAD (fab+pdf+source+3d) common 21   identical 20   differing 1
  the 1: fab/cpl.csv
```
The 20 identical: gerber zip, both `.drl`, `bom.csv`, all 3 PDFs, the STEP, and all 12 `source/` files. `fab/cpl.csv` is genuinely the only differing payload file. The other 19 differences are all under `verification/` (new gate outputs + re-rendered PNGs), which is expected and correct.

I also independently confirmed the copper-identity story is checkable: the gerber zip carries **15 members** (6 copper + F/B mask/paste/silk + Edge_Cuts + 2 drills), and **no BOM or CPL is inside the zip** — correct for JLC's separate upload.

### 3. MANIFEST integrity — **FAIL (F2, F3)**
- sha256 table: **0 entries for 58 files.** Both directions fail trivially.
- `git cat-file -e PENDING` → not a valid object name.
- `git_dirty: PENDING`; scoped status shows 11 dirty entries in the board subtree, including untracked `03_src/rules/assembly.yaml`.
- Dangling MANIFEST citation: `verification/fresh_lens_v1.4.md` (F5).

For contrast, the predecessor v1.3 passes this check cleanly (`git_sha: 1495a8a` → exists, `Fri Jul 24 21:50:09 2026`; `git_dirty: false`; 53/53 table entries). v1.4 is strictly *behind* the release it supersedes on provenance.

### 4. MANIFEST vs evidence — **MIXED: counts PASS, the audit claim FAILS**

| MANIFEST states | I measured | verdict |
|---|---|---|
| ERC 0 errors / 1211 warnings | `erc.json`: severity histogram `{'warning': 1211}`, **0 errors** | ✅ |
| (same) | `policy_audit.md` S-ERC row: `PASS \| 0 errors (1211 warnings)` | ✅ 3-way agreement |
| bom_source_check 49 lines: 47 coded, 2 uncoded | `fab/bom.csv`: **49 data rows**, **2 blank-LCSC** (`JP_INJ`, `J_DBG`) → 47 coded | ✅ |
| CPL 177 placements, top=177, bottom=0 | `fab/cpl.csv`: 177 rows, layer histogram `{'top': 177}` | ✅ |
| A-POP board 203 / cpl 177 / unpop 26 = 10 declared + 16 exempt | pcbnew: **203 footprints**, **26** `exclude_from_pos_files`, **16** `exclude_from_bom`; A-POP re-run reproduces it | ✅ |
| count_parity 199 ×4 | 203 footprints − 4 mounting holes = 199 | ✅ consistent |
| DRC 0/0/0 + standalone 0/0/0 | `drc.json` and `standalone_archive_drc.json`: `violations: []`, `unconnected_items: []`, `schematic_parity: []` | ✅ |
| **policy_audit 0 FAIL** | **`policy_audit.md`: `Summary: FAIL=1` (M-REL)** | ❌ **F1, P0** |

Everything numeric reconciles. The one disagreement is the one that matters.

### 5. The rotation independence claim — **REAL, with one disclosed residual oracle. This is the strongest part of the release.**

**What is genuinely independent.** The defect was `jlc_twin.xform()` applying the wrong-handed rotation operator. `rot_remeasure.py` derives its *own* operator and **proves it against pcbnew before using it** — `max |pcbnew − operator| = 0.000000000 mm at 0/90/180/270`. Critically, it then runs the **pre-fix negated form through the same proof and shows it failing**: `0.000000000 / 35.560000000 / 0.000000000 / 0.960000000 mm`. That is the incident's exact signature — sign-invariant at 0/180, wrong at 90/270 — reproduced as a *falsification test*. Had the new operator shared the old handedness, this proof would have failed loudly. **This is precisely the test v1.3 did not have**, and it is why v1.3 sealed green with seven wrong rows.

The two inputs are also separately sourced: our pads from `pcbnew`, JLC's from a plain text parse of JLC's cached `.kicad_mod` — no reuse of the twin's parser, resolver, or exporter.

**What is NOT independent — state it plainly.** Both `jlc_twin` and `rot_remeasure` read the **same cached JLC `.kicad_mod` files**, produced by the twin's own EasyEDA fetch/convert path. Re-parsing them as text defeats a *parser* bug but not a *conversion* bug. And the whole answer hinges on JLC's **pad numbering** being faithful, because pad numbering is the only thing that breaks the 180° symmetry of a TQFP/TSSOP/SOIC land. A mirrored or renumbered conversion would fool both methods identically. The release does not claim otherwise, but the MANIFEST's phrase "sharing no code with jlc_twin" describes the *code*, not the *data*.

**Corroboration that partly covers the residual:** 270° for these seven is exactly what v1.0, v1.1 and v1.2 shipped — three releases cut *before* the per-LCSC table existed, i.e. by a different code path. Independent agreement across a code-path change is meaningful support.

**And the residual is correctly mitigated, not hidden:** ORDER_README §3a makes a human pin-1-dot check against JLC's own placement preview **MANDATORY and BLOCKING** for U1 — the only oracle genuinely outside this toolchain. That is the right call and it is written in the right register.

**Calibration note (not a finding):** the separations are not uniform. The seven corrected parts are decisive (15× to 4811×; worst residual 0.0725 mm on the SOT-563 bucks). The *weakest* fits in the table are Q1 (9×, rms 0.2003) and U9 (13×, rms 0.1592) — 3- and 5-pad SOT-23 packages, where a pad fit carries the least information. Those are the rows that did **not** move, so they also carry the least *new* evidence. They agree with v1.0–v1.3 and with fleet cross-verification, so I am not calling it a finding — but if any single row in this table deserves the preview eyeball beyond U1, it is Q1.

**Judgement: the independence claim is REAL for the defect that caused v1.3.** It is not absolute, the gap is the shared footprint cache, and the gap is gated by a blocking human check.

### 6. Population set (A-POP) — **PASS**
Re-ran `assembly_coverage.py` against the staged bytes: **exit 0**.
```
board=203 footprints, cpl=177 placements, unpopulated=26
  (declared=10, consigned=1, exempt_prefixes=['H','TP'])
placement histogram: top=177
A-POP: PASS
```
My own independent cross-check of CPL × BOM × assembly.yaml:
- declared not-assembled refs **on** the CPL: **`[]`** ✅
- CPL rows whose BOM line has a **blank LCSC**: **`[]`** ✅ (the 2 blank lines are `JP_INJ`/`J_DBG`, both off the CPL)
- CPL rows with no BOM line at all: **`[]`** ✅
- **U1 is ON the CPL** (`U1 … 270.0`, LCSC `C6938291`) and appears under `consigned:`, **not** `not_assembled:` ✅ — the exact v1.3 defect is corrected
- BOM refs not on CPL: exactly the 10 declared (`J3–J10, JP_INJ, J_DBG`) ✅
- MANIFEST `not_assembled: J3-J10, JP_INJ, J_DBG` — **refdes only, no prose** ✅. `assembly_coverage.py` expands the range form (line 269) and reports no `MANIFEST-PROSE` / `MANIFEST-DRIFT`.
- Shipped `verification/assembly.yaml` is **byte-identical** to `03_src/rules/assembly.yaml` ✅
- Arithmetic closes: 203 footprints − 16 exempt (H1–H4, TP1–TP12) = 187 BOM refs; 187 − 10 declared = 177 CPL. pcbnew confirms 26 `exclude_from_pos_files` / 16 `exclude_from_bom`.

This is the cleanest part of the release. One caveat: `assembly.yaml` is **untracked in git** (F3).

### 7. Sourcing (A-STOCK) — **PASS, honestly stated**
`stock_check.json` verdict line: **`"verdict": "FAIL"`, failures 2, uncoded_lines 2, min_stock_per_board 5.** The two problem lines:

| LCSC | refs | qty | need (×5) | stock | placed? | covered? |
|---|---|---|---|---|---|---|
| `C6938291` | U1 | 1 | 5 | **0** | **yes** | `sourcing_plan:` entry with `measured_stock: 0`, `measured_on: 2026-07-25` ✅ |
| `C9900035627` | J3–J10 | 8 | 40 | **0** | **no** (off CPL) | `not_assembled: not_in_catalog` with dated query ✅ |

I scanned all 47 graded lines: **exactly those two** fall below `qty × 5`. Every other coded+placed line clears it; the tightest are `C5224055` (383 vs 10, 38×) and `C882626` (496 vs 5, 99×) — both match the MANIFEST and ORDER_README §5 watch-list. The `sourcing_plan:` entry carries a measured number *and* a date, as the contract requires.

The MANIFEST's handling here is exemplary and worth naming: it does **not** claim a clean verdict line. It states "jlc_stock_check's own verdict line reads FAIL on TWO lines and neither accuses this release" and then names both. That is the correct way to report a FAIL you have adjudicated — and it is the direct fix for the fleet defect where five sealed releases shipped a `FAIL:` line nobody parsed.

### 8. Order paperwork — **substantively good; two gaps and one dangling claim**
I read ORDER_README as the person about to upload. It is unusually strong: the ⛔ supersede banner is unmissable, the seven corrected rows are tabulated with package and pitch, the MSL-3 procedure (§3b) is five concrete numbered steps sourced to datasheet §14.5 p.33, and the consignment logic is stated correctly and emphatically — **"U1 is CONSIGNED — which means POPULATED … any paperwork that says otherwise is wrong"**, explicitly naming v1.3's mistake.

I tested its two most falsifiable technical claims against the actual fab bytes, expecting to catch it:

- *"The board file ships `capping yes` / `filling yes`"* → `source/…kicad_pcb` lines 55–56: **`(capping yes)` `(filling yes)`** ✅
- *"the PTH drill file emits [the EP vias] under the **ViaDrill** tool (T1, 0.150 mm) … there is no 0.15 mm ComponentDrill tool in the file"* → PTH tool table: `ViaDrill T1C0.150`, `ViaDrill T2C0.200`, then `ComponentDrill` T3C0.600 / T4C0.890 / T5C1.000 / T6C1.570. **No 0.15 ComponentDrill.** ✅ Exactly as described.

Board geometry also checks out against the order form: pcbnew reports **170.100 × 120.100 mm, 6 copper layers, 203 footprints** — matching §1 exactly.

Draft-marker sweep (`TODO|TBD|FIXME|XXX|PENDING|placeholder|DRAFT|WIP`): **ORDER_README is clean**; the only hits repo-wide are `MANIFEST.txt:4` and `:5` — the two `PENDING` stamps of F3.

Gaps: F14 (no guidance when JLC flags the zero-stock `C9900035627` BOM line), F15 (PoE Alternative A unanalyzed), F13 (BOM has no MPNs though §3a asks the operator to record them).

### 9. Archive self-containment — **PASS**
`source/fp-lib-table` declares 14 libraries. **12** resolve to `${KICAD10_FOOTPRINT_DIR}` (the system KiCad library — permitted). **2** resolve to `${KIPRJMOD}`:
- `Sensor_Humidity` → `source/Sensor_Humidity.pretty/` — **present**, 1 `.kicad_mod`
- `crow_recorder_central_v2` → `source/crow_recorder_central_v2.pretty/` — **present**, 4 `.kicad_mod`

**Zero URIs point outside the release directory.** Corroborated by `standalone_archive_drc.json`: 0 violations / 0 unconnected / 0 parity on a copy of `source/` alone. This release does **not** have the out-of-archive-pointer defect the contract records against usb-hub-3s-v3.

### 10. Anything else
F6 (no v1.4-era review), F8 (missing `SUPERSEDED.md`), F9 (fix-claim method gitignored), F10 (live mutation), F11 (no `msl:` line + no gate enforcing it fleet-wide), F12 (irreconcilable U1 residuals), F16, F17. All above.

---

## What I checked hardest, and what I could not break

I went after the CPL diff hardest, because an eighth changed cell or a moved Q1/Q2/U9 would have been the killer finding — I parsed both files independently rather than trusting the shipped `diff`, keyed every row by Designator, compared all 7 fields, checked row order, and re-ran it after the directory moved under me. It is exactly 7 cells. I could not break it.

Second hardest: the independence claim. The pre-fix operator being run through the same proof and *failing* (35.560 mm at 90°, 0.960 mm at 270°) is a real falsification test, not a self-consistency check. I found the residual — both methods read the same JLC footprint cache — but the release gates it behind a blocking human preview check rather than papering over it.

Third: the two ORDER_README fab claims that a fab house will actually verify (via fill/cap, ViaDrill tool table). Both true against the bytes.

**The defect class that killed v1.3 is fixed, and fixed with evidence that could have caught it.** What is broken is the seal: a MANIFEST that claims a gate result its own bundle refutes, no hashes, no commit, and a cited review that does not exist. This release family has now shipped two wrong seals; the paperwork state here is exactly how a third would happen.

**Path to ORDER** — no fab byte changes: (1) commit the inputs including `assembly.yaml`; (2) stamp `git_sha`/`git_dirty` and compute the 58-entry sha256 table; (3) re-run `policy_audit` (M-REL should clear) and `release_freshness_check` (must exit 0); (4) ship or delete `fresh_lens_v1.4.md` and run one v1.4-era lens; (5) add the CHANGELOG entry and restore v1.3's `SUPERSEDED.md`; (6) archive `rot_remeasure.py`. Then re-review — against a frozen directory.

---

**VERDICT: DO-NOT-ORDER**
