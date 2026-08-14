# Revision checklist

## v0.2.1 bench-power / rounded-RF hardware archive — release sealed 2026-08-14

- [x] J12 is exact CJT `A2541WV-2P` / LCSC `C225477`, vertical 1x2 THT at
      2.54-mm pitch; manufacturer drawing, dossier and project-local 3D model
      are retained
- [x] J12.1 is `VBUS_RAW` (+5 V) and J12.2 is GND; square pad, `+5V`, `GND`,
      `BENCH 5V` and `USB OR J12 - NOT BOTH` markings are visible
- [x] either J1 or J12 traverses the common F1, D1 and U3 protection/regulation
      path; the two non-isolated inputs are explicitly limited to one energized
      4.75--5.5 V source at a time
- [x] generated schematic/board/Circuit JSON/manifest agree 30/30; label/pin
      assertions pass 133/133, electrical invariants 34/34 and ERC has zero
      error-severity findings
- [x] placement passes 42 assertions, zero pad/courtyard collisions, P-PADSEP,
      30/30 model coverage and pre-route reviews; blocking P-MODEL-REG passes
      9/9 SMA instances and 45/45 drilled attachment centres
- [x] exact JLC twin includes J12; 30/30 bodies mount and J12 measures 0.172-mm
      centre delta / 0.176-mm outward excursion against the 1.00-mm limit
- [x] the promoted route preserves all earlier tracks/vias and adds only two
      0.30-mm `VBUS_RAW` segments; final saved-board DRC is 0/0/0
- [x] seven RF paths use 14 tangent arcs and two remain direct/straight; all
      nine remain branch-free with zero RF vias, route fence passes 18/18
      flanks and via process grades 9 filled/capped + 615 ordinary vias
- [x] fresh layout seal and release evidence bind board SHA-256
      `e2d1deaf4052b18b84df02d1b5cab48e131c6debbd70a03678c3ed918b24c2d5`
- [x] firmware was not generated or modified
- [x] commit the exact source/layout/review snapshot
- [x] generate and independently review a distinct v0.2.1 fabrication,
      BOM/CPL, STEP and high-resolution final-render release package
- [ ] obtain JLC controlled-impedance, selective-via, C429844/C225477 THT,
      BOM-allocation, rotation and placement-preview echoes before ordering

Current order verdict: **DO-NOT-ORDER**. The local hardware archive is sealed;
JLC uploader/process acknowledgement and first-article evidence are still open.

## Layout-sealed candidate — 2026-08-13

- [x] architecture ADRs accepted and exact part codes selected
- [x] exact-code manufacturer facts and dated two-source/JLC checks recorded
- [x] current official ST DS13866 Rev 5 is retained and digest-selected; the
      prior misnamed Rev 3 is historical only, with consumed facts rechecked
- [x] power, surge/capacitor, module-first, package-escape and source-rule gates pass
- [x] fail-safe RF truth table and framed dwell decoder contract are executable
- [x] JLC four-layer stackup and live-calculator RF source geometry retained: 0.295-mm width / 0.200-mm CPWG gap / 49.972 ohm
- [x] generated four-page schematic agrees 29/29 across source and exports
- [x] source pin-map 131/131, electrical invariants 32/32, ERC errors 0 and checkpoint 7/7 pass
- [x] exact-PDF topology/readability reviews and independent RF schematic review are SOUND
- [x] schematic pause completed before any PCB artifact was generated
- [x] D12 confirms all nine SMA connectors as Amphenol RF 901-143-6RFX female right-angle THT
- [x] exact Amphenol Rev-C drawing and no-form/fit-change PCN retained; stale drawing association and wrong ground-hole diameter corrected
- [x] exact Amphenol, pSemi and GCT footprints realized and compared with fresh exact-code JLC CAD
- [x] D14 90 x 65 mm outline, four M3 holes, three fiducials and cyclic
      non-crossing open-U RF edge order commissioned
- [x] all nine SMA mating-face datums and the USB PCB-edge datum measure exactly on the outline
- [x] generated board places 29/29 parts and nine selective U1 EP POFV vias; P-COLLIDE and P-PADSEP pass
- [x] placement DRC: 0 violations, 39 expected track-free unconnected items, 0 schematic-parity findings
- [x] physical pin-map gate passes 127 declared identities across 15 multi-pin refs
- [x] critical-pair gate explicitly grades 0 differential pairs with a single-ended RF reason
- [x] D15 compact top, oblique and edge placement review renders generated;
      the five-top/two-per-side SMA arrangement is visibly clear and U2, U3,
      U4, D1, F1 and every fitted R/C package are now visibly populated
- [x] `model_coverage_check.py` independently reopens the saved board and
      resolves 29/29 fitted bodies from project-owned paths
- [x] exact GCT USB, Samtec J11 and native exact-code SMA bodies resolve in the
      headless render; SMA legs align with the five-hole manufacturer pattern
      and all nine mating directions face outward at their board edges
- [x] R-PREFLIGHT source-known correction: common clearance 0.20 mm,
      ordinary via 0.45/0.20 mm (8:1 nominal aspect), and 0.58-mm legalizer
      pocket; 0 FAIL / 0 WARN and track-free board hash unchanged
- [x] user approval plus the fresh corrected-board renewals bind compact
      connector access, RF planning corridors and operational silk to board
      SHA-256 `bdb0df87886cc15ed8a3ae2aee53c97f4a4cfd49734558967240816c5c73a22e`
- [x] D16 route-wave/prep contract is complete; exact prep retains 23 RF
      segments with zero RF vias, six U1 ground-to-EP links, explicit boxed-
      endpoint dogbones and 29 automatic + 3 J11 explicit SMD GND drops
- [x] fresh pin/layout/render and A-RENDER placement witnesses are SOUND
      against the exact corrected board and deterministic prepared-route input
- [x] canonical placement checkpoint pins 24/24 exact inputs at SHA-256
      `f0fa1e83a1e00d020cced7f677a8ba198259f7e325278e18d273a8f5be496b39`;
      the superseded pre-D13 certificate is retained as
      `06_build/checkpoints/placement-pre-D13.json`
- [x] deterministic endpoint escapes own boxed U1/U2/J1/C6/R3--R6 lands;
      35/35 seed banks prepare collision-clean with no ordinary via-in-pad
- [x] shared per-wave no-new-via-in-pad gate is executable and all five
      promoted waves pass it; rejected attempts never entered progress/FINAL
- [x] promoted chain SHA-256 `ddb5b901d9d8b4666dc99df9d1de29e46f63315d4440e43af9dcc686668ad622`
      authenticates 5/5 waves and passes P-ROUTEBASE against exact r0
- [x] post-route quick verdict is CLEAN: zero routed-net opens and zero copper
      violations; 61 GND connections are explicitly deferred to plane fill
- [x] routing-stage checkpoint pins 19/19 source, prepared, intermediate,
      guard and quick-verdict artifacts at SHA-256
      `d7f828aad6b738290c8a324c5a7b15f0404ba4908b67cf7da2cf8c5929b032ca`
- [x] promoted import provenance binds exact chain `ddb5b901d9d8`; pre-fill
      quick is clean and the stitch gate serves 32/32 GND SMD pads
- [x] post-route cleanup adds two copper-contained endpoint bridges, removes
      twelve unused single-layer barrels, places 200 safe ordinary GND stitch
      vias and fills all four zones with no split island to heal
- [x] saved-board DRC is 0 violations / 0 unconnected / 0 schematic-parity;
      rules audit passes 20/20 and imported Pluto cable-boundary facts 3/3
- [x] post-stitch checkpoint pins 23/23 exact route, review, provenance, rule,
      DRC and saved-board artifacts at SHA-256
      `888c17bc703d324d18947fa704423eafe4054893497ee211c3b0f958a68d45c2`
- [x] route-following RF fence realizes 394 collision-clean 0.45/0.20-mm GND
      vias including 22 bend anchors; the independent saved-board report
      grades 18/18 flanks with worst aperture 1.3979 mm <= 1.4000 mm. The
      separate 5-mm rectangular lattice is not credited as RF fence
- [x] final-review P1 corrected before seal: the ordinary GND grid no longer
      lands in J11.3; exact final scan reports zero post-route via-in-pad,
      while V-PROCESS proves all 9 intentional U1 sites filled/capped in the
      drill-distinct 0.45/0.25-mm family and 629 ordinary 0.45/0.20-mm vias
- [x] paste-free J2-J10 have one executable assembly owner before seal: the
      required JLCPCB through-hole connector process names all nine refs and
      carries dated exact-code evidence; uploader refusal is a hard stop and a
      separately generated hand-solder release, never an in-place CPL edit
- [x] all six final exact-board lenses are SOUND against source commit
      `4cf5c818684e4c39f594b50a567fb086b9cf6f13` and board SHA-256
      `39251c24d4b3cc878824f26c48178cbc4a4d418fa528045c6c13f2308e017acd`
- [x] reviewed-commit layout seal minted; its scope is PCB layout only and it
      explicitly does not authorize fabrication, assembly or an order

Every revision passes this before it is tagged. A revision that will be
RELEASED must additionally pass the release gate at the bottom.

## Gates (mechanical — no judgement)
- [x] `kicad-cli pcb drc --severity-all --refill-zones --schematic-parity`
      → 0 violations, 0 unconnected, 0 missing footprints
- [x] shared `placement_gates.py` → PASS (P-OUT/P-CAP/P-BODYCLR)
- [x] `model_coverage_check.py 04_kicad/<board>.kicad_pcb` → P-MODEL
      PASS: 29/29 fitted footprints have renderer-resolvable bodies
- [x] `pad_separation.py 04_kicad/<board>.kicad_pcb --project .` → P-PADSEP
      PASS: separate-footprint copper clears the fab-tier gap and paste does
      not intrude on foreign lands
- [x] `via_process_check.py 04_kicad/<board>.kicad_pcb` → V-PROCESS PASS:
      9/9 via-in-pad sites protected, protected/ordinary drill families
      disjoint, and the generated order remark complete
- [x] rules regenerate byte-identical from `03_src/rules/nets.yaml` (no hand-edits)
- [x] BOM ↔ `02_parts/` parity (every used part has a datasheet + facts on file)
- [x] `module_first_check.py .` → P-MOD PASS; every complex subsystem uses a
      proven module or carries an evidence-backed bare-IC exception ADR
- [x] placement-stage schematic parity → 0 findings

## Judgement (a human or a fresh-context agent)
- [x] every net >1A walked end-to-end for copper cross-section (none declared;
      routed power review instead grades the 100 mA VBUS and 20 mA 3V3 loads)
- [x] every 2-pad polarized part: pad 1's net checked against `02_parts/*/part.yaml`
      (diodes, LEDs, electrolytics, AND connectors — this is invisible to DRC)
- [x] targeted 3D/render review: J11 body/keying and SMA body/leg/edge alignment
- [x] complete placement review: RF spoke corridors, all body clearances and
      operational silk readability
- [x] `01_docs/CHANGELOG.md` entry written
- [x] anything surprising captured as an ADR or the stage journal/improvement
      ledger when it is process rather than architecture
- [x] `03_src/rules/rf.yaml` explicitly records RF applicability. If enabled:
      independent RF schematic review is SOUND before placement; independent
      exact-board RF PCB review was SOUND before the rejected first seal
- [x] all six final exact-board lenses renewed SOUND against corrected board
      SHA-256 `39251c24d4b3` and its source commit before layout seal
- [ ] order-stage JLC assembly DFM explicitly accepts the manufacturer-land
      SMA drills (1.50/1.70 mm) against JLC C429844 CAD (1.60/1.80 mm); do not
      silently replace the Amphenol Rev-C footprint
- [ ] uploader echoes exact C429844 for J2-J10 as wave/manual assembly before
      payment; a refusal stops this release rather than silently dropping them

## Release and publication gate

Any release, publication, ship/ready claim, or merge of material project
changes to the publication branch requires this section. An explicitly
unreviewed WIP may exist only on a clearly labelled branch/draft PR and is not
mergeable.
- [ ] release inputs clean (`git_dirty: false`, scope `projects/<board>/ + skills/` via `release_git_dirty.py <board>` — a dirty sibling board does not block)
- [ ] tagged
- [ ] stock re-verified TODAY (not from cache)
- [ ] `07_releases/<ver>-<date>/` written with MANIFEST + verification evidence
- [ ] fab options in ORDER_README match the board (layers, via tier)
- [ ] release freshness: `release_freshness_check.py 07_releases/<ver>-<date>` exits 0 —
      no pdf/ or fab/ artifact sha256-identical to an earlier release (a changed board
      must not ship a prior release's drawings), shipped policy_audit.md agrees with the
      MANIFEST's claimed result, no draft/placeholder markers in ORDER_README
      (usb-hub-3s-v3 v1.2 sealed with v1.1's PDFs + a FAIL audit under a 0-FAIL manifest,
      2026-07-23 — caught by external review, not by any gate)
- [ ] manifest-consistency (M-CONS): `release_freshness_check.py` exit 0 on the staged
      dir AFTER the MANIFEST stamp — every count the MANIFEST's gate summary states
      matches the shipped evidence (ERC errors/warnings vs policy_audit S-ERC and
      erc.json; bom_source_check line count vs fab/bom.csv rows), and evidence paths
      name the sealed dir, not a staging path (crow-recorder-central-v2 v1.0 sealed
      with three prose/evidence disagreements, 2026-07-23). The gate's version key
      handles board-prefixed dir names (`<board>-v1.x-<date>`) — before 2026-07-24
      those silently skipped the stale-artifact check

- [ ] A-POP (population set DECLARED): `assembly_coverage.py 07_releases/<ver>-<date>` exits 0 —
      `{board footprints} − {CPL designators}` EQUALS `03_src/rules/assembly.yaml`'s
      `not_assembled:` set (declared `exempt_prefixes:` honoured), no blank-LCSC BOM row
      whose refs are on the CPL, every declared-unpopulated ref carries
      `exclude_from_pos_files`, and the MANIFEST `not_assembled:` line agrees with
      assembly.yaml (it is GENERATED from it). cooksense v1.1 sealed 13 blank-LCSC parts
      onto its CPL while the MANIFEST declared 12 of them unassembled, 2026-07-24
- [ ] A-STOCK (seal only against evidence that PASSES): `release_freshness_check.py 07_releases/<ver>-<date>`
      exits 0 including check (e) — the shipped stock evidence carries a PARSEABLE PASS
      verdict and every coded, placed line clears `qty x build_quantity` or names an
      `assembly.yaml` `sourcing_plan:` entry with `measured_stock` + `measured_on`. Ship
      `verification/stock_check.json` (`jlc_stock_check.py --json`): a missing or
      unparseable verdict is a FAIL, not a skip (five sealed releases shipped a `FAIL:`
      last line, one with the board's own CPU at stock 0)

- [ ] BRIEF.md: every acceptance criterion `met` (with evidence link) or `dropped` citing a user D#/Q# — never release with an `unmet` criterion
- [ ] BRIEF.md prompt hash verifies — note `head -c -1`: the FINAL NEWLINE is `sed`'s terminator, not part of the prompt, and the commission hashes it stripped (`sed -n "/prompt-verbatim-begin/,/prompt-verbatim-end/p" 01_docs/BRIEF.md | sed "1d;\$d" | head -c -1 | sha256sum`)

- [ ] JLC twin gate: `jlc_twin.py` exits 0 with the project adjudications file — zero unadjudicated MIRRORED/PAD-MISMATCH findings; twin_report.csv copied into the release verification/

- [ ] semantic M-BOM on the STAGED fab set: `bom_source_check.py fab/bom.csv circuit.json --parts 02_parts` exits 0 — per-refdes LCSC == source AND decoded MPN catalog value == BOM label (the R12/R30 wrong-part class, 2 sealed escapes 2026-07-23)

- [ ] `policy_audit.py <project>` → zero FAIL; waivers evidence-backed; HUMAN items carry the fresh-context reviewers' verdicts

- [ ] REVIEW LENSES scoped by release type (canon "Verification scoping"): INITIAL release of a material state = full battery (both red-team lenses + fresh pin review + render review); FIX-PASS release = diff-verified delta + targeted confirmation of each changed item + ONE integrated fresh-context lens — never the full battery on a fix-pass
- [ ] all reviews ran against the PRE-SEAL staging dir (a finding costs an edit, not a supersede); red-team verdicts ORDER with ZERO open P0 BEFORE the seal commit
- [ ] when RF is enabled, exact-Gerber RF fab review reports
      `fab_package_verdict: READY`; prototype order is distinct from production,
      which remains HOLD until first-article VNA/TDR acceptance passes
- [ ] fresh-context pin review (per the scoping line above): `pin_audit.py` dossiers generated; independent agents (no session context) per `pin-review-protocol.md`; verdicts in verification/pin_review.md with ZERO unresolved FAILs

- [ ] seal follows the 2-commit procedure — 07_releases contract "Seal procedure (normative)": gates+reviews on staging → source commit S → MANIFEST stamped `git_sha: S` / `git_dirty: false` + M-REL/freshness re-run → seal commit adds ONLY the release dir (+ CHANGELOG, + SUPERSEDED.md on the predecessor)
- [ ] publication boundary: `python3 skills/pcb-design/scripts/pcb_publication_gate.py --base <publication-branch-base-sha> --head <candidate-head-sha>` exits 0; repository protection requires this check and a PR before material PCB changes can reach the publication branch
- [ ] docs-only supersede (when the release changes ONLY documentation): `release_freshness_check.py 07_releases/<ver>-<date> --docs-only-supersede 07_releases/<prior>` exits 0 — fab/source/3d byte-identical to the prior ASSERTED, ORDER_README + MANIFEST differ; never waive fab-identical files one-by-one
- [ ] a supersede that is NOT docs-only uses the mode matching the SHAPE of the fix, never a hand-written `--allow-identical` waiver set (usb-hub-3s-v3 v1.11 shipped seven, all machine-checkable): `--bom-only-supersede` (a row LEAVES, A-POP) · `--cpl-only-supersede` (a coordinate moves, A-POS) · `--legible-bom-supersede` (how the BOM READS, F-LEGIBLE) · `--sourcing-supersede` (WHICH PART is bought, M8) · `--value-change-supersede … --designators R4,R5` (a part's VALUE moves on already-placed parts: gerbers/drills identical after the plot-timestamp strip, CPL delta confined to `Val` cells, BOM delta confined to the DECLARED refs). Full statements: 07_releases contract
