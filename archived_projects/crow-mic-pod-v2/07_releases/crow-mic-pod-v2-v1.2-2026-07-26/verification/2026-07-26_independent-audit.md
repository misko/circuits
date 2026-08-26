# Independent audit — crow-mic-pod-v2 v1.1-2026-07-25 (STAGED, seal imminent)

reviewer: independent-audit-agent (zero-context; findings formed before
reading STATUS/journal/DISPOSITIONS)
date: 2026-07-26
target: `07_releases/crow-mic-pod-v2-v1.1-2026-07-25/` (staged, untracked;
another agent owns the seal — nothing here was modified).

## Verdict

No DO-NOT-ORDER on the fab payload: copper, CPL geometry (re-measured 0.000mm
worst datum residual over 26 rows), rotations and BOM/CPL consistency all
check out. **But the release should NOT seal as currently staged**: its three
rotation/polarity documents contradict each other about which part needs the
human order-preview gate (P1 below), and against its OWN 07_releases contract
the verification/ tree is missing or mis-names 9 REQUIRED items (P1/P2).
These are paperwork fixes, cheap pre-seal and expensive after.

## P1 — the A-POL human gate points at the WRONG parts (three shipped documents disagree)

Which placements are SINGLE-CHANNEL (pad-number fit uncorroborated, requiring
the JLC order-preview eyeball)?

| document | says single-channel | says two-channel |
|---|---|---|
| MANIFEST.txt (A-POL line) | **D2 + D3** | U1 + LS1 |
| verification/rotation_human_gate.txt (the machine-readable gate) | **C2480/D2 + C559105/D3** | — (hand-authored; provenance block admits the exporter could not run) |
| verification/rotation_measurements.txt | D2 + D3 | U1 (pin-1-mark 1.0508 vs 3.4742), LS1 ('+' silk) |
| ORDER_README §3b (table + bold instruction) | **U1 (C192421)** — "confirm U1's pin-1 dot... names exactly C192421/U1" | D2 (JLC silk cathode glyph), D3 (cathode band line), LS1 |
| fleet table rows as landed (commit f9eee3f, 2026-07-26) | **U1 (C192421)** | D2 (C2480), D3 (C559105), LS1 (C22359707) |

The measurement history explains the flip: the D2/D3 "no numbering-free
channel" verdict in rotation_measurements.txt was superseded by a by-hand
re-measure (the JLC cathode-mark shapes DO resolve — recorded in the f9eee3f
table rows), and U1's "pin-1 marking" channel is the same F.Fab-shape channel
the release itself proved to be a false positive on LS1 (fixed upstream
848833b) — a SOIC-8 pin-1 dot follows numbering, so it is not numbering-free,
hence U1 is single-channel. ORDER_README §3b carries the CURRENT truth; the
MANIFEST and the machine-readable gate file carry the STALE one.

Consequences if sealed as-is: (a) an operator following the machine-readable
gate (or the MANIFEST) eyeballs D2/D3 and **skips U1 — the one 270-rotation
part whose fit could be confidently wrong**; (b) ORDER_README §3b claims
"rotation_human_gate.txt (regenerated at seal: names exactly C192421/U1)"
— a claim the shipped file falsifies (it names C2480/C559105 and its own
provenance says hand-authored, never regenerated); (c) the MANIFEST A-ROT
note "As of this release no C22359707 row exists in that table. Keep it that
way..." is stale — all four rows landed in f9eee3f today; (d) §3b even
contradicts ITSELF: its closing paragraph calls U1 "two-channel... the pin-1
marking independently agrees" two paragraphs after its own table declares U1
the single-channel row.

Pre-seal action (owner: the sealing agent): re-run
`export_jlc_package.py` so `rotation_human_gate.txt` is GENERATED (the four
rows now exist so A-ROT no longer blocks), and bring the MANIFEST A-POL/A-ROT
lines and §3b's last paragraph in line with the f9eee3f classification. Check
IDs: A-POL, M-CONS (M10), and the "fix-claim evidence" rule (a claim of a
regenerated file that was not regenerated).

## P1/P2 — contract REQUIRED-direction: 9 items missing or mis-named vs this board's own 07_releases/contracts.md

(The retasked first pass. `contracts_audit.py` cannot see any of this — its
three checks all iterate existing files; the REQUIRED direction is unchecked
by any tool.)

| required by contract | on disk | status |
|---|---|---|
| verification/drc.json | drc.json | OK (0/0/0 re-read) |
| verification/erc.json | erc.json | OK (0 err / 176 warn re-counted) |
| verification/audit.txt | audit.txt | OK |
| verification/stock_check.{txt,csv} | **neither** — only stock_check.json | **MISSING** (the .json the release ships is the CURRENT template's requirement, but this board's contract revision names {txt,csv} and does not list .json) |
| verification/twin_report.{csv,txt} | csv only | **twin_report.txt MISSING** |
| verification/twin_{six}.png | all six | OK |
| verification/render_{top,bottom}_bare.png | shipped as **bare_top.png / bare_bottom.png** | content present, contract NAMES absent |
| verification/missing_models.txt | present, generated | OK (but see NOTE on --cpl) |
| verification/pin_review.md | **pin-review.md** | name mismatch |
| verification/render_review.md | **render-twin-review.md** | name mismatch |
| verification/redteam_topology.md | **redteam-topology-protection.md** | name mismatch (byte-identical to 08_reviews copy — verbatim rule holds) |
| verification/redteam_layout.md | **redteam-layout-thermal.md** | name mismatch (verbatim rule holds) |
| verification/parity.md | **ABSENT under any name** | **MISSING** — netlist parity evidence exists only as drc.json's parity=0 count and MANIFEST prose |
| MANIFEST/ORDER_README/fab/pdf/source/3d | all present | OK (2 copper layers in the zip == the declared 2-layer tier; drills loose + in zip; BOM 26 designators == CPL 26, zero blank LCSC) |

The name mismatches are not cosmetic: this is precisely the hole the usb-hub
13-of-34 defect walked through — any future REQUIRED-direction checker keyed
to contract names reads this release as missing 9 artifacts, and M-REL today
only checks "verification/ exists and is non-empty" (policy_audit.py:818-820).
Renames cost nothing pre-seal.

## P2 — contract drift: this board's contracts are a stale template revision, and v1.1 is the revision that should have re-synced them

`07_releases/contracts.md` here lacks the current template's REQUIRED entries
(assembly_coverage.txt, stock_check.json, bom_source_check.txt, the
missing_models provenance/N==M rule, the not_assembled/msl MANIFEST blocks,
the scoped git_dirty and the seal-procedure + supersede modes) — the release
USES those mechanisms (`--bom-only-supersede`, generated not_assembled line,
stock_check.json) while its governing contract does not define them.
`03_src/rules/contracts.md` predates `assembly.yaml`, so `contracts_audit
--projects` FAILs this board's own `03_src/rules/assembly.yaml` (C-ALLOW)
today. Governance rule: project copies re-sync from
`skills/pcb-design/templates/contracts/` on their next revision — v1.1 IS a
revision and did not re-sync. State-not-resolve: the template moved; the
board copies did not.

Measured `contracts_audit.py --projects` C-ALLOW violations in this board's
tree (all but STATUS.md present at seal-input sha de94df7):
`01_docs/STATUS.md` (not permitted by this board's 01_docs contract),
`03_src/rules/assembly.yaml`, five 08_reviews files (naming pattern),
`RESUME.md` and `crow_mic_pod_v2-drc.rpt` at project root (root contract
forbids loose docs / generated artifacts at root).

## P2 — M-CONS: MANIFEST "payload identity vs v1.0: 37/38 files byte-identical"

The cited artifact (`verification/payload_identity.txt`) states **19 payload
files, 18 byte-identical, 1 differing (fab/bom.csv)** and contains no 37/38
figure anywhere. The claim is directionally true but its number is
substantiated by nothing shipped. Fix the number or ship the count it came
from.

## NOTEs

- **A-ROT process deviation, honestly documented:** at staging none of the
  four codes (C192421, C22359707, C2480, C559105) had fleet-table rows, so
  the exporter BLOCKED and fab/bom.csv was produced by editing v1.0's
  (sanctioned and shape-asserted by `--bom-only-supersede`: 2 whole rows
  removed, 0 added, 0 edited — verified in payload_identity.txt, and the
  claim is proven by RE-PLOT, canon-M1-clean). The rows have since landed
  (f9eee3f), which is what makes the P1 regeneration fix cheap now.
- **A-BODY ran in its weaker mode:** missing_models.txt header reads "26
  checked refs (no --cpl given...)". On this board the denominators coincide
  (26 checked == 26 CPL rows) so there is no coverage gap, but the canon asks
  for `--cpl fab/cpl.csv` so the denominator is the population, not the check
  count. Regenerate with --cpl at seal if the twin is re-run at all.
- **LS1 stock:** 69 units against need 8 (build_quantity 8 x qty 1), but
  single-source Extended with a 182->104->69 seven-day trend, correctly named
  as an order-day re-check in the MANIFEST.
- **sha256: 51/51 both directions, all hashes re-verified. 0 mismatches.**
  Evidence-completeness diff vs v1.0: nothing dropped, 12 files added.
- **Rotations independently traced:** 21 placements are 2-pad chip R/C at
  CPL 0 (measured-symmetric exemption); 5 placements on measured rows (D1
  C1972959 table 0; D2/D3/LS1/U1 per the f9eee3f rows, all equal to the
  shipped CPL values). LS1's quarantined machine `ROW: C22359707,90` was NOT
  pasted into the fleet table — verified: the landed row is 0.
- **policy_audit:** 0 FAIL; WAIVED S-OCCL (converter artifact) and R-RULES
  (2 dead DRU rules, measured harmless: worst under-floor segment 0.2498mm vs
  the dead rule's 0.25 floor, actual tier floor 0.127 holds at 1.97x) — both
  evidence-backed, R-RULES correctly marked REQUIRED-at-next-respin. Cosmetic
  gate bug: the E-TOPO row prints status `PASS` while its own text says
  "N-A: power_tree.yaml has no rails" — a label/status mismatch in the
  audit writer, harmless here.
- The PoE P0 (RJ45 power injection would destroy U1) is an ACCEPTED USER
  WAIVER (ADR-0005, "NEVER plug into PoE/Ethernet", ORDER_README §0) — noted
  as a live deployment-discipline dependency, not re-litigated.

## Not audited, and why

- Electrical re-derivation beyond spot-checks (opamp bias chain, VMID
  headroom): the release documents the U1 common-mode ceiling (~103-109 dB
  SPL) with datasheet-cited numbers; not re-derived at this tier.
- Gerber replot identity: shipped payload_identity.txt proves it by re-plot
  (11/11); method is M1-clean, not repeated.
- The v1.0 sealed release (superseded, carries SUPERSEDED.md — chain intact);
  retro-auditing a superseded seal is scoped out.
- git_dirty at the eventual seal: the working tree currently has uncommitted
  skills/ edits (rotation table + audit/resolve scripts + t1 test) — those
  are IN SCOPE for this board's seal per the git_dirty rule, so the sealing
  agent must land or revert them before stamping `git_dirty: false`.
