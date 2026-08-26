# Review dispositions — v1.4-2026-07-25

Every finding of the zero-context adversarial lens run against this release's
STAGED bytes (`verification/fresh_lens_v1.4.md`, verdict DO-NOT-ORDER on the
PRE-STAMP directory), with the MEASUREMENT that closes it. Mirrored into
`08_reviews/DISPOSITIONS.md`.

The reviewer's four P0s are all the same thing: **it reviewed the staging
directory between step 0 and step 2 of the seal procedure**, i.e. before the
stamp. That is where the procedure puts the review — a finding at staging costs
an edit, the same finding after the seal costs a supersede — and the stamp is
what closes them. The reviewer was right to block on them: an unstamped MANIFEST
is exactly what a bad seal looks like, and it correctly refused to grade intent.

| # | Sev | Finding | Closed by | Closing measurement |
|---|---|---|---|---|
| F1 | P0 | MANIFEST claims `policy_audit 0 FAIL` while the bundled `policy_audit.md` says `Summary: FAIL=1 (M-REL: git_sha not an exact commit: 'PENDING')` | **CLOSED by the stamp.** M-REL failed *only* because `git_sha` was the literal string `PENDING`. Source commit S landed, MANIFEST stamped, `policy_audit.py` re-run, the re-run copy shipped. | shipped `verification/policy_audit.md`: row `\| M-REL \| PASS \|` and `Summary: HUMAN=6, N-A=3, PASS=28, WAIVED=2` — **no FAIL row and no FAIL count**, which is how `policy_audit.py` reports zero (it emits only non-zero grade counts and exits 0 on `FAIL==0`; corrected wording per second-pass NF-4, which caught this disposition quoting a literal `FAIL=0` string that is not in the file). `verification/release_freshness.txt` exits 0 with no AUDIT/MANIFEST DISAGREEMENT |
| F2 | P0 | sha256 table EMPTY — 0 entries for 58 files, both Validate directions fail | **CLOSED by the stamp.** Table computed over every file in the release except `MANIFEST.txt` itself. | shipped `MANIFEST.txt` sha256 table, entry count == file count, verified both directions by `policy_audit` M-REL (which re-hashes every listed file) — see the gate table in this release's MANIFEST |
| F3 | P0 | `git_sha: PENDING`, `git_dirty: PENDING`; 11 dirty entries including **untracked `03_src/rules/assembly.yaml`** — the file A-POP grades against | **CLOSED.** All inputs committed in source commit S (assembly.yaml, the msl backfill in the XU316 part.yaml, `03_src/rot_remeasure.py`, the re-synced contracts, journal/learnings/STATUS, the archived reviews). `release_git_dirty.py` gated the commit. | `git cat-file -e <S>` succeeds and `<S>` is HEAD. Scoped `git status --porcelain -- projects/crow-recorder-central-v2/ skills/` at this instant returns **exactly THREE entries and no others**: the staged release dir, ` M 01_docs/CHANGELOG.md`, and `?? .../v1.3-2026-07-24/SUPERSEDED.md` — which is precisely the set the 07_releases contract's step-3 seal commit is DEFINED to carry, and nothing else. (Corrected per second-pass NF-2: the earlier wording said "empty apart from the release dir", which under-counted by two and would have read as a discrepancy to anyone checking it.) `git_dirty: false` is truthful for commit S: at `<S>` every INPUT is committed |
| F4 | P0 | shipped `release_freshness.txt` reports `MISSING: verification/policy_audit.md` while that file is present — stale evidence | **CLOSED.** Regenerated after the stamp so the shipped file grades the shipped bundle. | shipped `verification/release_freshness.txt`: `FRESHNESS: PASS`, exit 0 |
| F5 | P1 | MANIFEST cites `verification/fresh_lens_v1.4.md`, which did not exist | **CLOSED.** The review is archived verbatim at that exact path (and in `08_reviews/2026-07-25_v1.4-staging_fresh-lens_integrated.md`), including its DO-NOT-ORDER verdict — not a summary of it. | the file exists and is in the sha256 table; its verdict line reads `DO-NOT-ORDER` and the MANIFEST now says so plainly rather than claiming ORDER |
| F6 | P1 | `redteam_topology.md` / `redteam_layout.md` are v1.3's bytes and name only v1.1/v1.2 — no lens had graded v1.3's or v1.4's bytes | **CLOSED by disclosure + a real v1.4-era lens.** The MANIFEST now states exactly what those two files are: the **v1.2 MATERIAL-STATE** lenses, which grade the DESIGN (unchanged since v1.2 — same copper, schematic, netlist, BOM) and do NOT grade v1.3's or v1.4's assembly data. The release-level review of THESE bytes is `fresh_lens_v1.4.md` + `fresh_lens_v1.4_final.md`. Fix-pass scoping (canon "Verification scoping") calls for a diff-verified delta + targeted confirms + ONE integrated fresh-context lens; that is what ran. | MANIFEST `gates:` REVIEWS paragraph; two v1.4-era lens files in `verification/` |
| F7 | P1 | `01_docs/CHANGELOG.md` has no v1.4 entry | **CLOSED.** Written; carried by the seal commit per the 2-commit procedure (it was deliberately parked out of commit S so that S's only dirt was the release dir — which is why the reviewer saw it absent). | `policy_audit` M-REL checks every release dir has a CHANGELOG entry and now PASSes |
| F8 | P1 | v1.3 has no `SUPERSEDED.md`; it vanished mid-review | **CLOSED, and the reviewer caught a real transient.** It was written, then deliberately parked (same reason as F7) so commit S would be clean, then restored. It ships with the seal commit. | `07_releases/crow-recorder-central-v2-v1.3-2026-07-24/SUPERSEDED.md` exists and names v1.4, the 7 rotations and the consigned CPU; `policy_audit` M-REL checks every superseded sibling carries one |
| F9 | P1 | the method behind the release's central fix claim (`rot_remeasure.py`) lived only in gitignored `06_build/tmp/` | **CLOSED — this was the best finding in the review.** Promoted to `03_src/rot_remeasure.py` (git-tracked, with a canon-M8 STOPGAP docstring naming the gap it fills: the HELD A-ROT gate, and the `assembly.yaml`-driven config schema that would replace it) and VENDORED into `verification/rot_remeasure.py` so the archive stands alone. The shipped `rotation_remeasure.txt` was regenerated by running the tracked copy. | `03_src/rot_remeasure.py` in commit S; `verification/rot_remeasure.py` in the sha256 table; re-run from the tracked path exits 0 with `mismatches vs shipped fab/cpl.csv: 0` |
| F10 | P1 | the staging directory mutated during the review | **ACKNOWLEDGED — inherent to reviewing staging, and answered by a second pass.** The same reviewer re-reviewed the FROZEN, STAMPED directory; that re-review is `verification/fresh_lens_v1.4_final.md`. | the final lens's own anchor + verdict |
| F11 | P2 | no `msl:` line in the MANIFEST (contract requires one for consigned/exposed-pad parts); no gate enforces it fleet-wide | **CLOSED for this release; the gate gap is recorded.** MANIFEST now carries a top-level `msl:` line for U1 with the datasheet citation, and states that no other placed part is consigned or exposed-pad. The unenforced contract clause (no `msl` handling anywhere in `skills/jlcpcb-fab/scripts/`) is a real fleet gap and belongs to the assembly-gate work, not to this board. | MANIFEST `msl:` line; `03_src/rules/assembly.yaml` `consigned: msl:`; `02_parts/XU316-1024-TQ128-I24/part.yaml` `limits.msl` |
| F12 | P2 | two residuals for the same U1 measurement: 0.2047 mm (rotation table's evidence prose) vs 0.0025 mm (this release's re-derivation), 80x apart | **RECONCILED, not papered over.** Re-measured all four angles with both inclusion rules: at 270 the residual is UNIFORM (rms = mean = max = 0.0025 mm over 129 pads), and zipping the duplicate-numbered pads in returns identical numbers — so no pad subset can produce 0.2047 under this alignment. The difference is an ALIGNMENT difference (a translation not taken from the centroid), not a pad-set difference; this run could not reproduce the other. Both agree on 270 and on the 11.98 runner-up, which is what the release depends on. The rotation table is owned outside this board and was left untouched. | `verification/cpl_acceptance_gate.md` section 2a, with the four-angle rms/mean/max table |
| F13 | P2 | `fab/bom.csv` MPN column blank on 49/49 rows while ORDER_README §3a asks the operator to record MPNs | **CLOSED (docs).** §3a now says where the MPNs actually are (`02_parts/` or §2), instead of implying the BOM carries them. The BOM itself is byte-identical to v1.2/v1.3 and M-BOM PASSes; changing it would break the copper-identity claim for no gain. | ORDER_README §3a |
| F14 | P2 | no guidance for when JLC's quote engine flags the zero-stock `C9900035627` BOM line | **CLOSED (docs).** ORDER_README §3 now says the flag is EXPECTED, that `C464587` must not be accepted as a substitute (it does not fit the land), and what to do if the form refuses a zero-stock line. | ORDER_README §3, block quote after the J3-J10 paragraph |
| F15 | P2 | §0 analyses only PoE Alternative B; Alternative A would inject onto AUDIO± and the unfused beeper pair — a different, arguably worse damage path | **CLOSED (docs), and it is a genuine gap in the analysis.** §0 now works BOTH alternatives explicitly and states that A reaches the PCM1865 front end through the per-port 100R + ESD parts and bypasses the input PTC entirely. The conclusion (never plug into Ethernet; bench-only deployment) is unchanged — the reasoning is now complete. | ORDER_README §0 |
| F16 | P2 | `twin_report.txt` trailer says the FETCH-FAILED code "was never checked" while the MANIFEST summarises `twin exit 0` | **NOTED, no change.** C9900035627 is adjudicated with a dated 8-attempt measurement (`03_src/rules/twin_adjudications.yaml`) and is OFF the CPL, so it is not assembly data. The trailer is the tool's standing warning text, printed whenever any code fails to fetch; the adjudication is what makes exit 0 legitimate. | `verification/twin_report.txt` `ADJUDICATED-FETCH-FAILED` row; `assembly_coverage.txt` confirms J3-J10 absent from the CPL |
| F17 | P2 | `stock_check.json`'s `bom` field names `06_build/fab_v14/bom_jlc.csv`, a path outside the archive | **NOTED, no change.** The field records where the tool was pointed, which is the honest provenance; its content reconciles exactly with `fab/bom.csv` (49 lines / 47 coded / 2 uncoded — the reviewer verified this). Rewriting a tool's own provenance field to look tidier would make the evidence less true, not more. | the reviewer's own reconciliation in `fresh_lens_v1.4.md` §7 |

## Second pass — the same lens over the FROZEN, STAMPED bytes

`verification/fresh_lens_v1.4_final.md`. **VERDICT: ORDER, zero P0.** It did not
take the closures above on trust: it re-ran `policy_audit --skip-drc` (exit 0,
zero FAIL rows, M-REL PASS), re-ran `release_freshness_check` (exit 0, output
BYTE-IDENTICAL to the shipped file), recomputed the whole 61/61 sha256 table in
both directions (0 discrepancies), confirmed `47eca68` exists and is HEAD, and
**re-ran `rot_remeasure.py` itself** — reproducing the shipped
`rotation_remeasure.txt` line for line and confirming the operator proof
genuinely falsifies the pre-fix form. It re-derived the acceptance gate from
scratch (7 cells, Q1/Q2/U9 byte-identical), re-verified 20/20 payload identity
AND re-extracted all 15 gerber members for its own timestamp-stripped compare
(15/15), and cross-checked the CPL's X/Y against the archive's own board on
177/177 rows at a worst error of 0.000001 mm. It also confirmed the directory
did not move under it (61/61 verified at pass start and pass end), which is the
answer to F10 the first pass could not give. Its five new P2s:

| # | Sev | Finding | Disposition |
|---|---|---|---|
| NF-1 | P2 | `cpl_acceptance_gate.md` still named the gitignored `06_build/tmp/rot_remeasure.py` as the method's home — self-inconsistent with the same document's own later reference to the archived copy | **FIXED** — the line now names `verification/rot_remeasure.py` (canonical tracked copy `03_src/rot_remeasure.py`). A dead path in the release's central fix-claim artefact is exactly the kind of thing a future reader hits first |
| NF-2 | P2 | F3's closing measurement said the scoped git status was "empty apart from the release dir"; it is THREE entries (release dir + CHANGELOG + v1.3 SUPERSEDED.md) | **FIXED** — F3's row above now states all three and why they are contract-correct rather than dirt. The bytes were never wrong; the disposition's wording was |
| NF-3 | P2 | MANIFEST states `count_parity 199 x4` and `check_port_nets 115/115 + 8/8` with NO shipped machine artefact behind either — unfalsifiable from inside the archive, the exact property the completeness test exists to prevent | **FIXED** — both re-run for this seal and shipped: `verification/count_parity.txt` (4x `ok … 199 components`) and `verification/check_port_nets.txt` (`PASS — 115 labels all survive; 8 ports pin-for-pin`), the latter run against THIS release's own `source/<board>.net`. Every MANIFEST gate number now resolves to a shipped machine artefact |
| NF-4 | P2 | F1's closing measurement quoted `Summary: FAIL=0`, a string not present in `policy_audit.md` | **FIXED** — F1's row above now quotes the actual summary line and explains that `policy_audit.py` emits only non-zero grade counts |
| NF-5 | P2 | J2 (USB-C) is the one PLACED part no pad-fit method can grade — our vendored footprint numbers pads 1..17 while JLC names them A1–A12/B1–B12, so zero pad names are shared and an independent re-fit separates 90° from 180° by a factor of **1.0** (rms 4.4723 vs 4.8841). It was not on the preview-eyeball list | **FIXED, and it is the best catch of the second pass** — ORDER_README §3a now names J2 as a second BLOCKING preview check with that measurement stated, plus Q1 as the weakest of the fitted rows (9×). A part that no machine can orient is precisely the part a human must |

Its one informational note — that five non-zero-rotation CPL rows (U10, C_c9,
C_c10, C_c11, C_c13) were graded by nothing independent — it closed itself by
re-fitting all five: all agree with the shipped CPL, notably **U10 at 180, rms
0.1500 vs next-best 3.2882 (22x)**, which matters because U10's angle comes from
the footprint-NAME DB rather than a per-LCSC measurement. Recorded in
`cpl_acceptance_gate.md` §2c. It is NOT folded into `rot_remeasure.py`: amending
a committed INPUT after the source commit makes that commit stale, and grading
every CPL row is the held A-ROT gate's job, not this board's.

Its one standing CONDITION, which the seal honours: *if the seal commit adds
anything under `projects/crow-recorder-central-v2/` or `skills/` beyond the
release directory, the CHANGELOG entry and v1.3's `SUPERSEDED.md`, then
`git_dirty: false` becomes retroactively false.* `release_git_dirty.py` was
re-run immediately before the seal commit and the commit's own file list is the
check.

**What the review did NOT break, having tried hardest:** the 7-cell CPL diff
(re-parsed independently, keyed by Designator, all 7 fields per row, re-run
after the directory moved — exactly 7 cells, Q1/Q2/U9 untouched), the payload
identity (20/20, `fab/cpl.csv` the only differing payload file), every numeric
claim in the MANIFEST except the one that the stamp fixes, A-POP, A-STOCK, the
archive's self-containment, and both falsifiable ORDER_README fab claims (via
fill/cap, and the ViaDrill-not-ComponentDrill tool table).
