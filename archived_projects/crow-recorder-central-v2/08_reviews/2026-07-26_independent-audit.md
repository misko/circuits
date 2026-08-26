# Independent audit — crow-recorder-central-v2 v1.5-2026-07-25 (SEALED)

reviewer: independent-audit-agent (zero-context; formed findings before reading
STATUS/journal/08_reviews/DISPOSITIONS)
date: 2026-07-26
target: `07_releases/crow-recorder-central-v2-v1.5-2026-07-25/` — the fleet's
only orderable release.

## Verdict

**NO DO-NOT-ORDER FINDING.** The fab payload, CPL geometry and rotations were
independently re-measured and agree with the release's claims. Findings below
are P1/P2/NOTE — mostly claims that overstate what their evidence proves, and
gate-coverage holes that happened not to contain a defect this time.

## Pass 1 — contract REQUIRED-direction (retasked priority)

Checked BY HAND against `07_releases/contracts.md` (this board carries the
current template revision). Every REQUIRED item in the tree diagram is present
by its contract name:

| required item | present |
|---|---|
| MANIFEST.txt, ORDER_README.md | yes |
| fab/ (zip, PTH+NPTH drl loose, bom.csv, cpl.csv) | yes — zip contains 15 files, 6 copper layers matching the declared 6-layer stackup |
| pdf/ schematic+pcb_layers+assembly | yes |
| source/ sch+pcb+tsx+net (+fp-lib-table, 2 vendored .pretty) | yes |
| 3d/ step (gltf absence stated in MANIFEST) | yes |
| verification/: drc.json, erc.json, audit.txt, assembly_coverage.txt, stock_check.json, stock_check.{txt,csv}, bom_source_check.txt, twin_report.{csv,txt}, six twin_*.png, render_{top,bottom}_bare.png, missing_models.txt (generated, `bodies mounted: 174/174`), pin_review.md, render_review.md, redteam_topology.md, redteam_layout.md, policy_audit.md, parity.md | all present |

Contract-drift noted (state, not resolve): the contract's own Validate bullet
requires directory names matching `^v[0-9]...`; the actual directory is
board-prefixed (`crow-recorder-central-v2-v1.5-...`), which the same file's
seal-procedure text elsewhere accepts. The contract disagrees with itself
(contracts.md:390 vs the M-CONS paragraph at :287-290).

Project-level contracts: all REQUIRED files exist (03_src/rebuild_all.sh;
03_src/rules/{nets,power_tree,assembly,electrical_invariants,policy_waivers,
twin_adjudications}.yaml; part.yaml for every vendored part sampled). Gap:
`01_docs/journal/` has 02_parts/03_schematic/routing/verify but **no
placement journal** (M9 says every stage; sibling crow-mic-pod has one). NOTE.

**P2 — MANIFEST claims "contracts_audit 0 violations"; measured 6 C-ALLOW
violations inside this board's own tree** (`/usr/bin/python3
scripts/contracts_audit.py --projects`, 2026-07-26):
`crow_recorder_central_v2-drc.rpt` at project root (root contract forbids
generated artifacts at root), `03_src/audit.json`, `03_src/drc_baseline.json`,
`03_src/fab_overrides.txt` (not in 03_src allowed table), and
`08_reviews/2026-07-24_v1.{1,2}-staging_{pin,render}-review.md` (4 files, name
pattern not permitted by the 08_reviews contract). All verified present at the
seal sha (`git ls-tree 375c0de`). The MANIFEST claim is true only in the
tool's default scope, which EXCLUDES projects/ — the claim's scope is not
stated, so a reader takes it as covering the board it seals. Check IDs:
M-CONS (M10) wording, C-ALLOW underneath.

Sixth-trap instance confirmed for the record: `contracts_audit.py` has only
C-COV/C-ALLOW/C-ISO, all iterating files that EXIST. Nothing machine-checks
the REQUIRED direction; the table above was built by hand and is currently the
only such check.

## Pass 2 — evidence completeness and claim-to-artifact

sha256: **66 table entries == 66 disk files, both directions, all 66 hashes
re-verified byte-for-byte. 0 mismatches.**

Diff vs predecessor v1.4 verification/ — dropped: `cpl_acceptance_gate.md`,
`freshness_exceptions.txt`, `payload_identity.txt`. Added: assembly_coverage
.json, electrical_invariants.{txt,yaml}, part_facts.txt, stock_check.csv.
`payload_identity` is replaced by `release_freshness.txt`'s cpl-only-supersede
byte-identity assertions (fab/source/3d asserted identical, CPL delta = 1
coordinate move J2 (90,-126)->(90,-124.698) + 3 rows removed) — explained.
`cpl_acceptance_gate.md` and `freshness_exceptions.txt` are dropped WITHOUT a
stated reason — NOTE, and see P2 finding on review scoping below.

Claim | artifact | present | agrees:

| MANIFEST claim | artifact | agrees? |
|---|---|---|
| DRC 0/0/0 (+ standalone archive) | drc.json, standalone_archive_drc.json | yes — 0/0/0 and 0/0/0 measured |
| ERC 0 err / 1211 warn | erc.json | yes — 0/1211 measured |
| count parity 199 x4 | count_parity.txt | yes |
| CPL top=174 / bottom=0 | fab/cpl.csv | yes — 174 rows, all `top` |
| A-POS worst 0.00050mm/174 | — | **independently re-measured with pcbnew on source/ in place: worst residual 0.0005 mm over 174 rows.** agrees |
| A-ROT all 174 sourced | jlc_lcsc_rotations.csv @375c0de | yes — 24 placements on 15 measured per-LCSC rows (all board-frame rotations 0, CPL rot == table offset), 150 on 2-pad chips (symmetric exemption; 4 of them at CPL 180/270, moot for 2-pad) |
| A-POL "all 15 orientable codes resolved two-channel" | same table @375c0de | **NO — see P2 below** |
| A-STOCK PASS | stock_check.json + assembly.yaml + release_freshness.txt | json's own `verdict: FAIL` (2 lines); freshness check (e) PASSes it via sourcing_plan (U1 consigned) + off-CPL (C9900035627). Sanctioned path, but see NOTE below |
| twin 176 OK, bodies 174/174 | twin_report.txt, missing_models.txt | yes — generated header `bodies mounted: 174/174` |
| E-INV 11 invariants | electrical_invariants.txt | yes — "E-INV OK: 11 invariants hold" |
| M-BOM PASS | bom_source_check.txt | verdict reproduced offline — but see P1 on coverage |
| policy_audit 0 FAIL | policy_audit.md | yes — PASS=29, WAIVED=2 (evidence-backed), HUMAN=6, N-A=3, FAIL=0 |
| MSL-3 stated in paperwork | ORDER_README §3b | yes (P-FACT graded it) |

## P1 — M-BOM/M6: the value-verification leg is blind to 12 of 25 passive BOM rows, and 2 codes (18 placements) had NO offline value source at seal

`bom_source_check.py row_kind()` (line 179) classifies by the ENTIRE
leading-alpha refdes prefix and returns None for anything not exactly {R} or
{C}; line 324-325 then `continue`s SILENTLY. This board's descriptive refdes
are exactly that class. Measured on the sealed `fab/bom.csv`: **49 rows, 13
value-graded, 12 passive rows skipped** — `C_5V2...` (44 placements of C1525
100nF), `Rs1M...` (16x C25076 100Ω), `Cd1-8` (C1523), `Cc*` (17x C377773
2.2uF), `CL1/CL2`, `Rf`, `Rd`, `RG1/R_cs/R_rst`, and 4 more — roughly 120 of
the 174 placements. The shipped `bom_source_check.txt` is a 3-line PASS with
no per-row output, so nothing discloses the coverage.

Of the skipped rows, I resolved every code offline (MPN column, part.yaml
dirs, `lcsc_passives_ledger.yaml`): 10 of 12 resolve and MATCH. Two resolve
NOWHERE offline — **C377773 (2.2uF, 17 placements: all Cc* ADC coupling caps
+ C_vb) and C25130 (680Ω, Rd)**: blank BOM MPN, no ledger row, and the
canon's own rule says an unresolvable row is UNVERIFIABLE-VALUE, "flagged for
review, never a silent pass". These were silently passed. This is the exact
channel of the 62k->6.2k and 510k->390k decade defects.

Defect check (independent channel): the release's own `stock_check.json`
records the live catalog MPN per line — C377773 = CL21A225KBQNNNE (225 code =
2.2uF, and `02_parts/CL21A225KBQNNNE/` exists), C25130 = 0402WGF6800TCE
(6800TCE = 680Ω, `02_parts/0402WGF6800TCE/` exists). **Both values are
CORRECT — no board defect.** The finding is the gate, not the board.

Reader action: (a) add C377773 and C25130 to the vetted ledger (verify once,
quiet forever); (b) fix `row_kind()` to classify descriptive refdes (or key
off the labeled value, which the function already has in hand) and add a
known-bad fixture with a `Cc1M`-style refdes that must FAIL — the current
gate cannot fail on this board's naming style; (c) have bom_source_check
print graded/skipped counts so a 3-line PASS can never again hide a 48%
coverage hole.

## P2 — M-CONS: MANIFEST A-POL line overstates its evidence

MANIFEST: "A-POL 0 single-channel refs (no human-gate file emitted; all 15
orientable codes resolved two-channel)". Measured at the seal commit
(`git show 375c0de:.../jlc_lcsc_rotations.csv`, polarity column of the 15
codes this board places): **two-channel = 7, n/a = 8, single-channel = 0.**
"0 single-channel" is true; "all 15 resolved two-channel" is false — the 8
n/a rows (C6938291, C181312, C82317, C5224055, C90627, C15127, C20917,
C79924) are declared NOT-POLARIZED, which is a different, weaker statement
than corroborated-two-channel. No coordinate or rotation is wrong (the 7
genuinely polarized/orientation-critical 2-pad and connector codes — D1
C87074, Dp1-8 C1972959, J2 C3020560, U4/U6/Y1/U10 — are two-channel). Reader
action: none for ordering; correct the wording pattern in the seal tooling so
the A-POL line quotes the channel histogram instead of a universal claim.

## P2 — review scoping: the one thing v1.5 changed has no fresh-context lens

v1.5 is a CPL correction (174-row datum rewrite + J2 move + 3 row removals).
The shipped red-team lenses are byte-identical copies of the **2026-07-24
v1.2-STAGING** reviews (sha256 match with 08_reviews files); the newest
fresh-context artifact is `fresh_lens_v1.4_final.md` (v1.4). 08_reviews has
no v1.5 entry, and v1.4's `cpl_acceptance_gate.md` (the CPL-specific gate
artifact) was dropped from v1.5. The scoped-verification amendment requires
targeted confirmation (present: A-POS machine evidence + rotation_remeasure)
PLUS one integrated fresh-context lens over the result (absent). The machine
gates are strong here and I re-verified A-POS independently, so this is P2
not P1 — but the release's review chain, read from its own archive, ends one
material change before its content.

## NOTEs

- **A-STOCK/A-POP shape, fleet-inconsistent standard:** the sealed BOM
  carries 13 refs that are not on the CPL: J3-J10 coded C9900035627 at
  measured stock 0, J1 coded C381116, R_inj1/R_inj2 (C11702), and JP_INJ +
  J_DBG with **blank LCSC**. crow-mic-pod-v2 superseded its v1.0 over exactly
  this shape ("a BOM row at stock 0 / uncoded, not on the CPL, stalls JLC's
  BOM/CPL matcher"). Here the same shape is retained and documented
  (ORDER_README §3 tells the operator to expect the flag and how to proceed;
  dispositioned F14 in review_dispositions.md). Both boards cannot be right
  about JLC's matcher. Residual risk: assembly-order upload friction, not a
  wrong board. Reader action: on order day, follow §3; fleet action: pick one
  standard for not-placed BOM rows and encode it in A-POP.
- **E-MARGIN never exercised:** power_tree.yaml declares no
  `load_uv_threshold` on 3V3_DIGITAL/0V9_CORE, so E-MARGIN self-graded N-A;
  the rails also declare zero-width vout windows (3.3-3.3, 0.9-0.9) with no
  `feedback:` block, so the computed-tolerance-corner check never ran either.
  The 4 AP61102 divider part_value E-INVs pin the resistors, not the
  worst-case Vout vs the XU316/PCM1865 brownout. A gate that is silenceable
  by omitting its config is the same class this campaign keeps finding.
- The 33pF C3-feedforward rework is declared BLOCKING in the MANIFEST and
  ORDER_README §3d — an honest, evidence-cited open item, not a finding.
- Positive re-measurements: gerber zip layer set matches the 6-layer
  stackup; In1/In4 same byte-length but different content (checked — not
  duplicated files); drills present loose + in zip; CPL/BOM designator sets
  consistent (CPL ⊆ BOM, 0 CPL refs uncoded); CHANGELOG `Released:` names
  this directory; SUPERSEDED.md chain closed on v1.0-v1.4; git_sha 375c0de
  exists.

## Not audited, and why

- Full electrical re-derivation (pin maps, divider thresholds vs downstream
  abs-max, open-circuit sensor nodes): out of tier for a 199-part board; I
  relied on the shipped E-INV (11 asserts), audit_board (21 polarity + 11
  keepout checks) and P-FACT outputs after verifying those tools' outputs are
  the artifacts claimed, not re-running their theory.
- JLC-side footprint re-reads for the 7 n/a-channel ICs (their pad clouds are
  asymmetric, so a pad-number fit is self-corroborating in a way 2-pad parts
  are not; the 2-pad polarized codes are all two-channel in the table).
- Replot identity of the gerbers (shipped replot_identity.txt asserts it;
  not re-plotted here).
- git_dirty:false at seal time (not reconstructable without checkout; the
  post-seal working tree is legitimately dirty with today's A-ROT work).
