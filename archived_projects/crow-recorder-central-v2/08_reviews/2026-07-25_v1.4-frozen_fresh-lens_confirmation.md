subject: crow-recorder-central-v2 v1.4-2026-07-25 (FROZEN + STAMPED, pre-seal-commit)
date: 2026-07-25
reviewer: redteam-agent (zero-context adversarial second-pass confirmation lens)
context-given: zero-context (frozen release archive + predecessor v1.3 read-only + 01_docs design docs + 02_parts + 03_src + 04_kicad + the release contract + the gate scripts; journals/learnings/STATUS/08_reviews withheld)
verdict: ORDER

Second pass over the FROZEN, STAMPED directory, tasked with verifying every
claimed closure of the first pass (2026-07-25_v1.4-staging_fresh-lens_integrated.md,
DO-NOT-ORDER) with its own instruments, and re-running the core acceptance
checks from scratch. Archived VERBATIM below. Dispositions for its five new
findings: DISPOSITIONS.md rows FL4-NF1..NF5 and the release's
verification/review_dispositions.md.

---

I have completed all checks. Here is the review.

---

# SECOND-PASS ZERO-CONTEXT RELEASE REVIEW — crow-recorder-central-v2 v1.4-2026-07-25 (FROZEN/STAMPED)

**Reviewer stance:** adversarial, read-only, no stake in shipping.
**Anchor:** all measurements taken against the frozen bytes at
`/home/mouse9911/gits/circuits/projects/crow-recorder-central-v2/07_releases/crow-recorder-central-v2-v1.4-2026-07-25/`.
**Directory stability:** the 61-entry sha256 table verified at the start of this pass and still verified at the end — the directory did not move under me (this closes F10 in a way the first pass could not).

**Disclosure of side effects.** Re-running `policy_audit.py` regenerated the *gitignored* build artifact `projects/crow-recorder-central-v2/06_build/policy_audit.md` (`.gitignore:1:06_build/*`). Nothing in the release, in `04_kicad/`, in `skills/`, or in git was written. `projects/smc0985-cooksense/` was not touched.

---

## (a) The 17 dispositions, verified against the frozen bytes

| # | Disposition claim | My verdict | What I measured |
|---|---|---|---|
| **F1** | shipped `policy_audit.md` says M-REL PASS / FAIL=0 | **CLOSED** | Fresh `policy_audit.py projects/crow-recorder-central-v2 --skip-drc` → **exit 0**, `HUMAN=6, N-A=7, PASS=24, WAIVED=2`, **zero FAIL rows**. Diff vs shipped file: **exactly 4 rows + the summary line** differ (S-ERC, S-NC, P-CRT, R-DRC → N-A, which is what `--skip-drc` does); `\| M-REL \| PASS \|` byte-identical in both. Caveat: the shipped summary literally reads `Summary: HUMAN=6, N-A=3, PASS=28, WAIVED=2` — the string `FAIL=0` the disposition quotes does not appear. `policy_audit.py:814` emits only non-zero grade counts, so absent-FAIL ≡ FAIL=0 and `sys.exit(1 if counts.get("FAIL"))` returns 0. True in substance, misquoted. |
| **F2** | every file in the table, every entry has a file, every hash matches | **CLOSED** | Recomputed both directions myself: **62 files on disk**, **61 table entries** (MANIFEST excluded, correctly), **0 duplicate keys**, **on-disk-not-in-table = 0**, **in-table-not-on-disk = 0**, **sha256 mismatches = 0/61**. |
| **F3** | git_sha exists; scoped status empty apart from the release dir | **PARTIALLY CLOSED** | `git cat-file -e 47eca68` → exists = `47eca686655f31f2be97d38cdb2918c760f18162`, dated 2026-07-25 16:13:00 -0700, **and is HEAD**. But `git status --porcelain -- projects/crow-recorder-central-v2/ skills/` returns **3 entries, not 1**: the release dir, plus ` M 01_docs/CHANGELOG.md` and `?? .../v1.3-2026-07-24/SUPERSEDED.md`. Those are exactly the other two items the 07_releases contract's step-3 seal commit is *defined* to carry, and F7/F8 declare them deliberately parked — so the **state is contract-correct; F3's stated measurement is wrong by two entries.** See NF-2. |
| **F4** | shipped `release_freshness.txt` = FRESHNESS: PASS, exit 0 | **CLOSED** | Fresh `release_freshness_check.py <release_dir>` → **exit 0**, `FRESHNESS: PASS`, and the output is **byte-identical to the shipped file** (all 18 lines, including both A-STOCK adjudication notes). No AUDIT/MANIFEST DISAGREEMENT. |
| **F5** | the lens is archived verbatim with its DO-NOT-ORDER verdict | **CLOSED** | `verification/fresh_lens_v1.4.md` present (24 071 B), hash `e0484d73…` matches the table. `verdict: DO-NOT-ORDER` at line 5 and `**VERDICT: DO-NOT-ORDER**` at line 197. All 17 findings F1–F17 present in full, not summarised. MANIFEST line 82 says so plainly. |
| **F6** | MANIFEST REVIEWS paragraph + two v1.4-era lenses | **PARTIALLY CLOSED** | The disclosure is real and precise (MANIFEST 73–91). Verified: `redteam_topology.md`/`redteam_layout.md` are **sha256-identical to v1.3's copies**, each reads `verdict: ORDER`, and contain **zero v1.3/v1.4 tokens**. One v1.4-era lens file exists; the second is this document (its absence is the known, expected one). |
| **F7** | CHANGELOG v1.4 entry written, parked for the seal commit | **CLOSED** | `01_docs/CHANGELOG.md` carries `## v1.4 — 2026-07-25` (+47 lines) ending `Released: crow-recorder-central-v2-v1.4-2026-07-25`. Uncommitted, as declared. **M-REL PASS in my own fresh audit run** confirms the gate sees it. |
| **F8** | v1.3 carries SUPERSEDED.md naming v1.4 | **CLOSED** | Present, untracked (parked). Names v1.4, tables all seven 90.0→270.0 rows, identifies U1 as the CONSIGNED XU316, and states the bare PCB is fine. |
| **F9** | method promoted to `03_src/`, vendored into `verification/`, output regenerated from the tracked copy | **CLOSED — and independently reproduced** | `verification/rot_remeasure.py` present and **`cmp`-identical to `03_src/rot_remeasure.py`**, which **exists in commit 47eca68**. Imports: `math, re, sys, pathlib, pcbnew` only — **zero** imports from `jlc_twin` / `jlc_rotation_resolve` / `export_jlc_package`. I re-ran it against the archive's own `source/` board + `fab/cpl.csv`: output **reproduces the shipped `rotation_remeasure.txt` line for line**, exit 0, `mismatches vs shipped fab/cpl.csv: 0`. **The operator proof genuinely falsifies the pre-fix form:** correct operator `0.000000000 mm` at 0/90/180/270; NEGATED form `0.000000000 / 35.560000000 / 0.000000000 / 0.960000000 mm` — exact at 0/180, wrong at 90/270. This is a real falsification test, not a restatement. |
| **F10** | answered by a second pass on frozen bytes | **CLOSED by this document** | 61/61 hashes verified at pass start and pass end. |
| **F11** | MANIFEST `msl:` line; assembly.yaml `consigned: msl:`; part.yaml `limits.msl` | **CLOSED; the gate gap is real** | MANIFEST lines 129–137 carry the top-level `msl:` for U1 with the XM-014532-PC v2.0.0 §14.5 p33 citation and the "no other placed part is consigned or exposed-pad" statement. `assembly.yaml consigned[0].msl` present. `02_parts/XU316-1024-TQ128-I24/part.yaml:168 msl:` present. Independently confirmed the disclosed gap: **`grep -rn msl skills/jlcpcb-fab/scripts/*.py` = 0 hits.** |
| **F12** | §2a four-angle rms/mean/max table | **CLOSED (reconciled, not papered over)** | §2a present: `ang=0 rms 11.9812 · 90 16.9439 · 180 11.9812 · **270 rms=max=mean=0.0025**`. The uniformity argument is sound — no pad subset can yield 0.2047 under this alignment. My independent re-run reproduces `0.0025 @270 / 11.9812 next / 4811x`. The upstream table row was correctly left untouched. |
| **F13** | ORDER_README §3a redirects MPNs | **CLOSED** | §3a: *"…`fab/bom.csv`'s MPN column is blank on all 49 rows (JLC sources from the LCSC column) — take the MPNs from `02_parts/` or from §2 above, not from the BOM."* I measured **MPN blank on 49/49 rows**. |
| **F14** | ORDER_README §3 block quote on the zero-stock line | **CLOSED** | Present immediately after the J3–J10 paragraph: flag is EXPECTED, `C464587` must not be accepted (does not fit the land), and the remove-the-row fallback with "the CPL is unaffected either way". |
| **F15** | ORDER_README §0 works both PoE alternatives | **CLOSED** | §0 now carries both bullets. Alternative A explicitly reaches AUDIO± → the PCM1865 front end through the per-port 100 Ω + TPD2E2U06, plus the **unfused** beeper pair, and "bypasses the input PTC entirely… if anything the worse of the two". Conclusion unchanged. |
| **F16** | adjudicated FETCH-FAILED, off the CPL | **NOTED — accurate** | `twin_report.txt:394` `ADJUDICATED-FETCH-FAILED` with the dated 8-attempt measurement (45 other codes fetched in the same run). My own BOM↔CPL cross-check: the 10 BOM designators absent from the CPL are exactly J3–J10, JP_INJ, J_DBG. The trailer is standing tool text. |
| **F17** | provenance field is honest; content reconciles | **NOTED — accurate** | `"bom": "projects/…/06_build/fab_v14/bom_jlc.csv"`. Reconciles exactly: 47 JSON line entries + `uncoded_lines: 2` = 49 = `fab/bom.csv` data rows (47 coded / 2 uncoded, measured by me). |

**No disposition merely asserts a fix that is absent from the bytes.** Every claimed artefact I looked for was present. Two claims are *imprecisely worded* (F1's quoted string, F3's "empty") — recorded below as P2, not as the P0-class "asserted-but-absent" defect.

---

## (b) Part 2 — the six core acceptance checks, re-run from scratch

### 1. CPL diff v1.3 → v1.4 — **PASS**
Both files parsed as CSV, keyed by Designator, all 7 fields compared per row.
```
rows (excl header): 177 vs 177   added: []   removed: []
header identical: True           designator ORDER identical: True
CHANGED CELLS: 7   — all in the Rotation column, all '90.0' -> '270.0'
   D_USB, U1, U2, U3, U5, U7, U8
CONTROLS  Q1 whole-row identical=True  Q2=True  U9=True   (all 180.0)
raw byte-diff: 7 differing lines (idx 98,167,169,170,172,174,175); no other line differs
```
Exactly 7. No eighth row. Q1/Q2/U9 byte-identical.

### 2. Payload identity — **PASS**
sha256 over all of `fab/ pdf/ source/ 3d/`: **21 files both sides, 20 IDENTICAL, 1 DIFFERING = `fab/cpl.csv`**, 0 added, 0 removed. `fab/cpl.csv` is genuinely the only differing payload file.

I also independently re-verified the copper-identity claim rather than trusting `replot_identity.txt`: extracted all **15** shipped zip members and compared each to the corresponding freshly-plotted file in `06_build/fab_v14/` with only the plot's own timestamp comment lines stripped → **15/15 identical, 0 mismatched, 0 missing.** And a further cross-check: the CPL's Mid X/Mid Y agree with the *archive board's own* footprint positions (`cpl_y == -board_y`) on **177/177 rows, worst error 0.000001 mm** — the CPL is not stale relative to the board it ships with.

### 3. A-POP — **PASS**
Fresh `assembly_coverage.py <release_dir>` → **exit 0**, output byte-identical to the shipped `assembly_coverage.txt`:
`board=203 footprints, cpl=177 placements, unpopulated=26 (declared=10, consigned=1, exempt_prefixes=['H','TP']); histogram top=177`.
My own independent arithmetic: board 203 (pcbnew, **0 flipped footprints**); BOM references 187 designators; 187 − 177 = 10 unplaced-and-coded/uncoded = J3–J10 + JP_INJ + J_DBG; 203 − 187 = 16 = H1–H4 + TP1–TP12. **Zero CPL designators missing from the BOM.** No blank-LCSC ref on the CPL (the 2 uncoded BOM lines, JP_INJ and J_DBG, are both off the CPL). Board bbox measured **170.100 × 120.100 mm**, matching ORDER_README.

### 4. A-STOCK — **PASS**
`stock_check.json`: 47 graded lines, `verdict: FAIL`, `failures: 2`. Both problem lines checked by hand:
- **C6938291** (U1) — PLACED, stock **0**, covered by `sourcing_plan[0]` with `measured_stock: 0` **and** `measured_on: 2026-07-25` **and** a plan naming consignment. Compliant with the contract's "measured number and its date".
- **C9900035627** (J3–J10) — stock 0, **NOT placed** (verified absent from the CPL myself).

Every other coded+placed line clears 5× its per-board quantity; I walked the whole table and the two tightest are **C5224055 383 vs 10** and **C882626 496 vs 5** — exactly what the MANIFEST and ORDER_README §5 state.

### 5. ORDER_README read as the uploader — **PASS, with one suggestion**
Draft-marker sweep over the whole release (`TODO|TBD|FIXME|XXX|PENDING|PLACEHOLDER|DRAFT|WIP`): **zero live markers.** Every hit is either the word "placeholder" describing JLC's C99* consign-only codes, or a *quotation of the old PENDING stamps* inside the archived lens/dispositions — the MANIFEST itself carries no PENDING.

Everything falsifiable checks out: 6 layers ✓, 170.1 × 120.1 mm ✓ (measured), 177 placements / all top / 0 bottom ✓, BOM 49 lines / 47 coded / 2 uncoded ✓, stackup + advanced-small-via + filled-and-capped-via requirement consistent with `kicad_pro` and §1a, C464587 land delta (11.74 − 3.67 = 8.07 mm) consistent with `02_parts/RJHSE-5384/part.yaml`'s `d8.07mm`, all cited commits exist (`1b69760`, `e0d735c`, `95a8180`, `9078ad9`), all cited ADRs 0002–0007 exist. §2's "row 168" for U1 is the *file* line including the header (data row 167) — accurate, if terse. The MANDATORY blocking U1 pin-1 preview gate in §3a is present and correctly framed as the only oracle outside the toolchain. No self-contradictions found.

### 6. Anything that would make me refuse to send this to a fab house — **No.**
Independently re-verified from the archive: DRC **0 violations / 0 unconnected / 0 schematic-parity** (`drc.json`, parsed by me); standalone-archive DRC on `source/` alone **0/0/0** (`standalone_archive_drc.json`) — the archive is self-contained; ERC **0 errors / 1211 warnings**, all warnings (`endpoint_off_grid` 862 + `lib_symbol_issues` 349), parsed by me from `erc.json`; parity 0 (116/116 nets, 598/598 nodes, 146/146 NCs); twin `175 OK / 369 checked`, **0 ROT-DB-SUGGEST** (grep-confirmed); `missing_models 177/177/0`; `source/` `.kicad_pcb`/`.kicad_sch`/`.kicad_pro`/`.kicad_dru` byte-identical to sealed `04_kicad/`, `.tsx` byte-identical to `03_tscircuit/src/`; exactly one gerber zip, 15 members, **no BOM/CPL inside it**.

---

## (c) New findings

**P0: none.**

**NF-1 (P2) — stale internal path in a shipped fix-claim document.**
`verification/cpl_acceptance_gate.md:103` still names **`06_build/tmp/rot_remeasure.py`** — the gitignored path F9 blocked on — as the method's home, while lines 152–153 of the *same document* correctly name `verification/rot_remeasure.py` and `03_src/rot_remeasure.py`. Self-inconsistent provenance inside the release's central fix-claim artefact. The method itself is present and I re-ran it successfully, so nothing is lost — but a future reader hits the dead path first.

**NF-2 (P2) — F3's closing measurement is not what the repo shows.**
Claimed: *"`git status --porcelain -- projects/crow-recorder-central-v2/ skills/` empty apart from the staged release dir."* Measured: **3 entries** — the release dir, ` M 01_docs/CHANGELOG.md`, `?? …/v1.3-2026-07-24/SUPERSEDED.md`. The 07_releases contract step 3 defines the seal commit as *"a commit that adds ONLY the release directory, the `01_docs/CHANGELOG.md` entry, and `SUPERSEDED.md` on the predecessor"* — so the working tree is in exactly the state the procedure prescribes, and the MANIFEST's `git_dirty: false` is truthful for commit S. The disposition's *wording* is what is wrong, not the release. **This does create one procedural condition on my verdict — see below.**

**NF-3 (P2) — two MANIFEST gate numbers have no shipped machine evidence.**
MANIFEST line 55–56 states `count_parity 199 x4` and `check_port_nets 115/115 labels + 8/8 ports`. No `verification/` artefact carries those as tool output; the only restatement inside the archive is prose in `cpl_acceptance_gate.md:281` by the same author. Every other MANIFEST gate number resolves to a shipped machine artefact (I traced them all). These two are unfalsifiable from inside the archive, which is the exact property the completeness test exists to prevent.

**NF-4 (P2) — F1's closing measurement quotes a string not present in the file.**
Shipped `policy_audit.md` ends `Summary: HUMAN=6, N-A=3, PASS=28, WAIVED=2`; the disposition quotes `Summary: FAIL=0`. Substantively correct (the script emits only non-zero counts and exits 0), but a reader checking the quote literally will not find it.

**NF-5 (P2, order-time) — J2 is the one placed part no pad-fit method can grade, and it is not on the preview eyeball list.**
Our vendored `USB4105_GCT_16P_TopMnt_num` and JLC's `TYPE-C-SMD_SBC-160S1A-20-S412` share **zero pad names**, so the twin's fit is `best=none` (adjudicated with independent schematic-stage evidence + MODEL-REG body-on-courtyard). I attempted my own independent fit and it is **degenerate — rms 4.4723 @90 vs 4.8841 @180, separation 1×** — i.e. no pad-based method has any discriminating power here. J2's CPL rotation is `0.0`, unchanged since v1.0, and the adjudication is well-evidenced, so this is not a defect. But ORDER_README §3a's per-row preview list names only the ten per-LCSC refs; **J2 deserves a line in that list** for the same reason U1 does.

**Informational — I closed the one rotation-coverage gap myself.**
`rot_remeasure.py` grades only its 10 hard-coded REFS. Five other CPL rows carry non-zero rotation and were graded by nothing independent: **U10 (180)**, **C_c9 (180)**, **C_c10/C_c11/C_c13 (270)**. I re-fitted all five with the same pcbnew-proven operator: **U10 fits 180 at rms 0.1500 vs next-best 3.2882 (22× separation) — agrees with the shipped CPL**, and it matters, because U10's 180 comes from the `^SOT-89 = 180` *name-DB* rule, not from a measurement (`C6035451` has no per-LCSC row). The four caps are non-polarised 0402s whose CPL rotation is simply their board orientation. **All five agree with the shipped CPL; no gap remains** — but the release did not measure them, and the script's own STOPGAP docstring correctly identifies grading *every* CPL row as the A-ROT gate's job.

---

## Verdict

The four P0s of the first pass are genuinely closed by the stamp, and I closed them with my own instruments rather than reading the closure evidence: I re-ran both gates (`policy_audit --skip-drc` exit 0 with zero FAIL rows and M-REL PASS; `release_freshness_check` exit 0 with output byte-identical to the shipped file), recomputed the full 61/61 sha256 table in both directions with zero discrepancies, confirmed `47eca68` exists and is HEAD, and re-ran `rot_remeasure.py` — whose operator proof is a real falsification test that the pre-fix form fails by 35.560 mm at 90° and 0.960 mm at 270°. The acceptance gate reproduces exactly: **7 changed cells, all Rotation, all 90.0 → 270.0, Q1/Q2/U9 byte-identical, 20/20 payload files identical, 15/15 gerber members identical on re-plot.** A-POP and A-STOCK both re-run clean. No draft markers, no P0.

**One condition, and it is procedural rather than a defect in the bytes:** at this instant the release is *not yet sealed*, and the scoped git status carries two extra entries beyond the release directory (`01_docs/CHANGELOG.md`, `v1.3/SUPERSEDED.md`). The contract defines the seal commit as carrying exactly those three things. **If the seal commit adds anything else under `projects/crow-recorder-central-v2/` or `skills/`, the MANIFEST's `git_dirty: false` becomes retroactively false and this verdict lapses.** Verify with `release_git_dirty.py` immediately before committing.

`VERDICT: ORDER`
