# Changelog — usb-hub-3s-v3

Board internal name `usb_hub_3s_v2`; project directory `usb-hub-3s-v3`.

## v1.10 — 2026-07-27

Released: `07_releases/v1.10-2026-07-27/`. **BOM-LEGIBILITY supersede of v1.9.
NO COPPER CHANGE.** v1.9 gains `SUPERSEDED.md`; it is otherwise immutable and it
is **not** DO-NOT-ORDER — its board is this board.

### Why

Canon **F-LEGIBLE** (ADR-0006): a fab artifact is graded as its RECIPIENT will
parse it, not as we wrote it. v1.9's `fab/bom.csv` carries **26 findings**:

| check | findings | what JLC saw |
|---|---|---|
| F-WORDS | 21 | the Comment is an LCSC code — 21 of 46 rows unreviewable by a human on either side |
| F-MPN | 4 | `C25757`/R42, `C2296`/D8, `C2297`/D9–D12 ship a **blank MPN** despite having `02_parts` dossiers (JLC: *No Part Selected*); and **SW1 ships `SS12D07VG6 087` with a SPACE** where `02_parts/SS12D07VG6-087` says a HYPHEN |
| F-ENCODE | 1 | `Ω` with no UTF-8 byte-order-mark — a cp936 reader sees `惟` |

v1.10 ships **0 findings**: 46/46 coded rows carry an MPN from the dossier or the
vetted passives ledger, 46/46 Comments read, byte-order-mark present.

The SW1 space-vs-hyphen is the one that matters most and is unique to this
board: usb-hub-3s-v3 is the **only** project that ever created the retired
`lcsc_mpn_map.csv` side-file, so it is the only one where a second home for the
MPN could drift from the first. This is why F-MPN requires the two match paths to
AGREE and not merely to be non-empty — a blank-only check passes that row.

### What did NOT change, measured

* `source/usb_hub_3s_v2.kicad_pcb` md5 `83af8e5a5596a51cf139dd06e8903d47` —
  identical to v1.9's **and** to `04_kicad/`'s.
* Gerbers + drills **re-plotted** from this release's own source: **15/15
  byte-identical** to v1.9's sealed zip after stripping the plot timestamp
  comments — the restored pour (36 zones / 106 filled outlines) included.
* `fab/cpl.csv` byte-identical; every A-ROT rotation and A-POS coordinate
  carried forward unchanged. 21 of 22 payload files sha256-identical.
* Asserted mechanically by `release_freshness_check.py --legible-bom-supersede`,
  a mode added for this class: only `Comment` and `MPN` may move, and a changed
  `LCSC` (a substitution) or `Footprint` FAILs.

No source change was needed on this board — all 29 dossiers already declared
their code under `sourcing:`, so the MPN column is filled entirely from
artifacts already in the tree.

### Still open, unchanged by this release

The A-POL single-channel JLC order-preview human gate (C130056, C13755, C473910,
C7519, C98732), the order-day stock recheck, the In1_Cu/In2_Cu gerber-viewer
check — and now **F-ECHO**: after uploading, diff JLC's own resolved part table
back against ours (`verification/bom_echo_gate.txt`, 46 lines).

## v1.9 — 2026-07-27

Released: `07_releases/v1.9-2026-07-27/`. **DO-NOT-ORDER supersede of v1.8, v1.7
AND v1.6.** All three gain `SUPERSEDED.md`; they are otherwise immutable.

### The defect: three sealed releases with NO COPPER POUR

v1.6, v1.7 and v1.8 shipped gerbers carrying **zero copper pour on all four
layers — 44287.91 mm2 of missing copper**. No GND plane, no VIN plane, no
5VA/5VC/VBUS/switch-node islands. On such a board the 7 A battery trunk and the
6 A rails exist only as the thin routed stubs that were never meant to carry
them, and the return path does not exist at all.

**Root cause:** `03_src/post_stitch_fixes.py` section 6, added in v1.6, unfills
the zones so it can place vias and never refills before its own save. That script
holds the **LAST** save in the pipeline, so the refill guard inside the stitch
driver guarded nothing.

**Why every gate stayed green:** `kicad-cli pcb drc --refill-zones` refills the
zones **IN MEMORY**. It reports 0/0/0 on a board whose saved file has no fill.
DRC, parity, twin, renders, ERC and the policy audit were all measuring an
in-memory board that was correct while the bytes on disk were not.

**The signature was in the shipped payload the whole time.** v1.8's `In1_Cu` and
`In2_Cu` gerbers are BYTE-IDENTICAL at 18921 bytes — a GND plane and a VIN plane
cannot be the same file unless neither contains a plane.

### The fix, and the two gates that make the class impossible

* **M-SHIP read-back** (`route_and_stitch_generic.py verify-fill`): reopens the
  saved `.kicad_pcb` AS TEXT and counts `filled_polygon` blocks. Text rather than
  pcbnew deliberately — pcbnew is the tool whose save behaviour is under test
  (canon M1). Wired into `rebuild_fast.sh` and `rebuild_all.sh`.
* **F-PAYLOAD** (`fab_payload_census.py`, canon F-POUR/F-IDENT): opens the
  shipped **zip** and grades it against the board. The only gate downstream of
  the export, and the one that closes the loop.

MEASURED, both releases graded side by side in
`verification/fab_payload_census.txt`:

| | v1.8 | v1.9 |
|---|---|---|
| F-PAYLOAD | **FAIL: 5 findings, 0 ok** | **OK: 5 checks passed** |
| G36 regions B.Cu / F.Cu / In1.Cu / In2.Cu | 0 / 0 / 0 / 0 | **17 / 87 / 1 / 1** |
| F-IDENT | inner layers byte-identical at 18921 B | all 4 copper gerbers distinct |
| saved-board read-back | 0 `filled_polygon` | **36 zones, 106 `filled_polygon`** |
| gerber zip | 88 692 B | **394 534 B** |

**Nothing electrical changed.** Netlist parity vs v1.8 is **0 differences**
(122 components, 73 nets, 372 nodes) and `fab/cpl.csv` is byte-identical.

### Also in v1.9 — four gates that did not exist when v1.8 sealed

* **A-AMP now grades 10/10 net-class currents** (was 3/10: the parser could not
  read any declaration carrying a qualifier, so "7 A worst case", "6 A / 5 A" and
  "7 A pulsed" were silently unchecked). PWR_IN, PWR_RAIL and SWITCH_NODE are now
  declared `pour_fed:` with cross-sections MEASURED on this board with pcbnew:
  narrowest 8.750 mm (VBAT), 9.300 mm (PMID) and 6.050 mm (SW_A) against
  IPC-2221 requirements of 4.399 / 2.765 / 4.399 mm. **VBUS and GATE are NOT
  pour-fed and are not declared so** — VBUS reaches its port pour through one
  0.800 mm B.Cu track per port (8.810 mm of it standalone copper), redeclared at
  the design's own 2 A continuous (dT 9.6 C; the 2.5 A burst is dT 16.0 C, stated
  and handed to bench gate Q4b); GATE is 100 % track and was failing only because
  a 2 A switching peak was being read as continuous — I_rms is 0.276 A.
* **S-COUNT parity restored 4-way.** The v1.6 status-LED cell was never added to
  `03_tscircuit/manifest.yaml`: **12** refs (Q8, R37-R42, D8-D12), not the 8 the
  audit reported — `count_parity.py` prints `extra[:8]` and truncates.
* **A-RENDER** (`twin_overlay.py`) run for the first time, both sides. 29 refs
  flagged, **0 board defects**; the bottom side correctly REFUSED (no populated
  bottom). Per-class adjudication with the crops examined:
  `verification/gate_adjudications_v1.9.md`.
* **`pdf/schematic.pdf` is tscircuit's own render again** (ADR-0002). v1.6-v1.8
  regressed to an Eeschema re-render (`Creator: Eeschema-PDF`) and A-EVID passed
  it because A-EVID checks the FILENAME, not the producer.
* **`verification/rules_audit.txt` ships** — v1.8 shipped none while A-AMP failed.
* **`verification/bom_source_check.txt` PASSES again** after the 10 mOhm shunt
  C127692 was catalog-verified into the fleet passives ledger; leg C had started
  grading milliohms and read the row as UNVERIFIABLE-VALUE.

### The three pre-seal lenses, and what they cost in EDITS

Three zero-context reviews were run against the STAGED archive before the seal —
pin review **PASS-WITH-NOTES**, render review **PASS**, integrated red-team
**ORDER**, **no P0 in any of them**. That timing is the whole point: `07_releases/`
becomes immutable at the seal commit, so **a finding here costs an edit and the
same finding afterwards costs a supersede**. Every item below was fixed at
SOURCE (canon M3) and propagated. **The board did not change** —
`source/usb_hub_3s_v2.kicad_pcb` is md5 `83af8e5a5596a51cf139dd06e8903d47`,
identical to `04_kicad/`; DRC 0/0/0; 106 `filled_polygon` blocks in the saved
text.

**P1 — the OFF-state budget was 2.6× low, and the bench gate it fed COULD NOT
PASS.** `power_tree.yaml` declared `quiescent_ua: 271`. It omitted the two
LM5116 **UVLO dividers** — `R6+R7` and `R15+R16`, each 49.9 k + 6.98 k =
**56.88 kΩ**, sitting **permanently across VIN**. SW1 gates ENABLE, not power
(pad 1 = T1→GND, pad 2 = COM→ENKILL, pad 3 unconnected; no pole touches
VBAT/VBAT_F/VIN), so both conduct for the whole of storage:
`12.6 V / 56 880 Ω = 221.5 µA` each = **443.0 µA** that was never counted.
Corrected to **714 µA typ / 744 µA countable worst**; storage life on a 3S
5000 mAh pack is **292 days to flat / 233 to the 20 % LiPo floor**, not 769/615.

**The serious part is the gate, not the number.** ORDER_README bench **Q6**
declared *"PASS ≤ 300 µA"* — a threshold a correctly-built board **cannot
meet**. A gate that cannot pass is the same defect class as a gate that cannot
fail, and this one would have condemned a good board. Q6 is re-based to
**≤ 1.00 mA**, derived rather than picked: worst-case-good 744 µA;
weakest-possible-bad 1461 µA (Q8 failed, pack LED lit, at the *weakest* corner
VIN 9.0 V / Vf 2.4 V); `sqrt(744 × 1461) = 1042` → 1.00 mA sits **1.34× above
good and 1.46× below bad**. It carries a **1.00–1.45 mA INDETERMINATE band with
a discrimination step** (lift D8 and re-measure), because two terms — the D2/R1
zener leg and **C1/C2 polymer leakage, which has no entry in its `part.yaml` at
all** — are unbounded in the record and are NAMED rather than silently zeroed.
Root cause reported upstream: `power_topology.py grade_off_control()` checks
only that `quiescent_ua` is *declared*, never that it reconciles with the
netlist.

**Five shipped documents were asserting things that are not true, and all five
are corrected:**

* **The CS/CSG pair is not a Kelvin connection.** sec.2.5 said *"no shared trunk
  copper enters the sense loop"*. Re-measured with pcbnew: `R10.1` taps the
  **GND plane 3.73 mm** from `RS1.2`, putting **0.359 mΩ** (buck-A) / 0.381 mΩ
  (buck-C) of shared trunk copper inside the loop; with the CS side, 0.483 /
  0.555 mΩ → **+4.8 % / +5.6 %** sense error → **the 11.0 A current limit is
  really ≈10.5 A**. The claim is withdrawn verbatim and the corrected limit is
  in a new sec.2.5a. Still 1.75× the rail load; no design change.
* **The R-THERM waiver described a board that no longer exists.** It said
  *"U11.21 … 1 direct via (vs 3 on U2.21)"* and carried a next-rev work order
  that is **already done**. Measured here: **U2.21 = 7 GND vias, U11.21 = 7**.
  Its dissipation figures were still the superseded 15.5 A Q1 / 5 A Q6 envelope.
  Rewritten, and the three TPS2557 EPs (1 via each) are **named for the first
  time** with the numbers that make them acceptable. *A stale waiver is an
  inherited defect* — this one had outlived four releases, having been raised
  and DEFERRED once already at v1.5 (RL-11).
* **The port ceiling nobody had written down: 2.72 A, not 2.5 A.** `R20/R21/R22
  = 36.5 kΩ` → `I_OS(min) = 2717 mA`, and the TPS2557 is guaranteed not to limit
  below it, so **nothing enforces 2 A or 2.5 A**. Three ports at the ceiling is
  8.16 A on a 6 A rail, still under the valley limit, so **nothing intervenes**
  — checked survivable term by term (L1, RS1 0.67 W in a 1 W part, F1) at a cost
  of **ΔT 19.4 °C** on the feed. A-AMP still grades 2.0 A and that choice is now
  written down beside the number instead of hidden by it.
* **`DETAIL_DESIGN` had no line for DEMB.** `U2.11`/`U11.11` are tied to GND
  (R_DEMB = 0 Ω), so **both bucks run in permanent diode emulation** — a
  deliberate departure from the TI worked design this project declares it
  adopts, against that file's own rule that *"a value in the schematic with no
  line here is UNJUSTIFIED"*. Now derived (DCM below ≈0.9 A/rail) and recorded
  as the CHOICE it is.
* **A datasheet citation belonged to a different device variant.** The
  "unused channel-2 pins may float" claim quoted SLVSBY8D's **TPS2514x** pin
  table, where pins 3/4 are genuine N/C; the fitted **TPS2513A** has real
  DP2/DM2 there. Restated as an engineering judgement, not a datasheet
  permission.

**Also corrected before the seal:** 5VA's **E-MARGIN had never been computed**
although it feeds three known 2 A loads — now derived (**+151.8 mV** at the
receptacle, +7.8 mV with the mating contacts charged) and **wired into the
machine gate**, which now grades 2 rails instead of 1; the rail's declared
window went from the bare nominal 5/5 to the tolerance-inclusive 5.032/5.273.
The **stackup is declared for the first time** (JLC 4-layer STANDARD, 1 oz outer
/ 0.5 oz inner) — the board file carries none, so every ampacity figure's copper
weight was an unnamed fab default; it is now an **order-form obligation** in
ORDER_README, which is where it binds, since gerbers do not carry it. Two
gate-reporting defects the render review caught were fixed: `A-POP` shipped a
**FAIL** that was purely an ordering artifact (it grades the MANIFEST, and ran
21 minutes before the MANIFEST existed — re-run **PASS**, and it now runs after
the stamp), and the MANIFEST's `twin:` line repeated `missing_models.txt`'s
`122/122` without the caveat that **R12 (C2984354) has no JLC model at all**.
And the gerber zip size stated in six documents was **394 530 B**; the file on
disk is **394 534 B**, corrected everywhere.

**RECORDED, DEFERRED, WITH THEIR MEASUREMENTS** — both are copper, and v1.9
exists to fix the pour; re-routing would void every verdict just collected.
Buck-A's pour is **2.7× (SW) and 3.2× (CS) more resistive than the
geometrically MIRRORED buck-C cell**, from a 0.300 mm neck ~0.8 mm long — and
SW_A is 1.38× of IPC-2221 by summed cross-section but **0.96× by
resistance-equivalent width**, a 44 % disagreement between two methods, so
`nets.yaml` now states the method with the number. High-side gate loops measure
**25–34 nH** (Q ≈ 1, so switching-loss/EMI, not shoot-through) — the
uncomfortable part being that the GATE class justifies its 0.300 mm width on
dI/dt loop area and **nobody had ever measured the loop**.

**Left OPEN and written down rather than papered over:** the fix lens's own SOR
reads **3.009 mΩ** for the three 5VC delivery segments against RL-2's 9.32 mΩ
and the 12 mΩ carried in the budget — **a 3× disagreement between two mesh
solves on identical copper that neither side could reconcile**. It is in the
safe direction (the shipped budget is the pessimistic one), which is the only
reason it is not a finding. Bench gates Q2/Q5 settle it, not whichever number
reached the file first.

## v1.8 — 2026-07-26

Released: `07_releases/v1.8-2026-07-26/`. **VERIFICATION-COMPLETENESS supersede of
v1.7-2026-07-26.** v1.7 gains `SUPERSEDED.md`; it is otherwise immutable.
**Fab payload BYTE-IDENTICAL to v1.7** (`diff -r` clean) — the board is not changed.

### Why: a new gate found what no tool had ever checked

`release_required_check.py` (canon **A-EVID**) enforces the **REQUIRED** direction of
`07_releases/contracts.md`. Nothing ever did: `contracts_audit` iterates files that
EXIST and asks whether they are permitted, which cannot see an absence. Run against
v1.7 it reported **5 missing**. Two were real evidence gaps, three were naming.

**usb-hub had never shipped a `pin_review.md` or a `render_review.md`** — absent from
v1.5, v1.6 *and* v1.7. A predecessor-diff check could not see it, because the
predecessor was missing them too.

### The two reviews, and what they found

Both **PASS**. Both found something.

**Pin review** (122 components, 73 nets, all 372 connected pins walked; board pads
cross-checked pad-by-pad against the netlist, 0 mismatches):

* **CONCERN — U12.** As shipped, with R42 unpopulated, the USBLC6-2SC6 sits on VBUSC
  at 5.352 V nominal / 5.479 V no-load — **~100-230 mV above its 5.25 V V_RWM,
  continuously**. Below breakdown (6.0 V), so leakage not damage. Every earlier
  document framed R42 as landing *on* 5.25 V **if fitted** and never wrote down the
  corollary. **Now stated plainly in ORDER_README at gate Q9.** The reviewer's
  recommendation — populate R42 by default, or a 6 V-V_RWM array — is a **v-next
  design decision**: populating R42 puts it on the CPL and changes the fab payload,
  which this supersede must not do.
* **DOC DEFECT — SW1.** The tsx comment described the deleted eFuse-era **D6 / EN_C**
  enable scheme as if current, contradicting the same file's own v1.2 header. The
  copper was never wrong (E-INV asserts both EN pins on ENKILL), which is exactly why
  nothing machine-checkable caught it. **Fixed**, and the v1.1 revision note marked
  SUPERSEDED.

**Render review** — no blocking defect, no render-vs-CPL or render-vs-netlist
disagreement. It did the **bare-vs-twin discrimination on Q1-Q6 explicitly**, the test
an earlier review generation failed when two of four lenses read the bare copper drain
paddle as a moulded package: bare shows the paddle, twin shows solid bodies with pin-1
dots in the netlist-correct corners. It recomputed the **CPL datum** from pad geometry
and matched all five connectors, each 1.5-4.7 mm off the KiCad anchor — the v1.6 fix
holds. It states plainly that the LED and C1/C2 3D models are polarity-symmetric so a
render **cannot** decide physical orientation; both stay on the order-preview gate.
One cosmetic nit carried to v-next: refdes "D1" runs into the "LEDS DARK = SWITCH OFF"
legend (silk is copper — not touched here).

### Also

* **Red-team naming** (crow-mic-pod's pattern): dated history stays in `08_reviews/`;
  the release ships the current review under the contract name. `redteam_layout.md`
  (from `2026-07-25_v1.5_redteam_layout.md`) and `redteam_topology.md` (from
  `2026-07-22_v1.0_redteam_topology_rereview.md`) are **copies**, with provenance
  headers naming the source and the lineage. The v1.2 protection red-team is a
  different document, not this one's successor — said explicitly, because
  "re-review" is otherwise ambiguous.
* **Assembly PDF** — the stricter option: the board moves to the contract, not the
  contract to the board. `assembly_front.pdf` + `assembly_back.pdf` are replaced by a
  single **2-page `pdf/assembly.pdf`**, front then back.
  *Correction to the brief for the record:* the named exemplar
  (crow-recorder-central-v2 v1.5) is **1 page**, not 2 — its 254137 bytes match but its
  page count does not. The genuine 2-page exemplar is **crow-mic-pod-v2 v1.2**
  (2 pages, 73472 B). v1.8 ships the 2-page form the user chose.
* **Archive still stands alone** — re-proved, not assumed: `source/` extracted to a
  bare temp dir, DRC **0/0/0** and ERC `footprint_link_issues` **0**. That is v1.6's
  defect, which cost a release; cooksense shipped the same one today.

## v1.7 — 2026-07-26

Released: `07_releases/v1.7-2026-07-26/`. **VERIFICATION-COMPLETE supersede of
v1.6-2026-07-26.** v1.6 gains `SUPERSEDED.md`; it is otherwise immutable.

**THE FAB PAYLOAD IS BYTE-IDENTICAL to v1.6** — `fab/bom.csv`, `fab/cpl.csv`, the
13-file gerber zip and both drill files are the same bytes, verified by `diff -r`.
**The board is not changed and v1.6's board was not wrong.** This is an
evidence-completeness supersede, not a fab defect.

### What was wrong

v1.6 shipped **13** verification files where v1.5 shipped **34**. The MANIFEST
asserted DRC 0/0/0, twin 119/119, passives 26/26, A-STOCK and freshness — while
the release carried no `drc.json`, no `erc.json`, no `bom_source_check.txt`, no
stock check, and no **`manifest_selfcheck.txt`**, the artifact whose entire job is
proving the manifest's PROSE matches its MACHINE EVIDENCE. The release asserted
its own gate results with the evidence stripped out.

**Two distinct causes, diagnosed rather than papered over:**

1. **Generated, never staged.** All six `twin_*.png` existed in `06_build/twin/`
   dated 01:02 the same day. The staging step did not carry them. A copy miss.
2. **Never produced at all.** `render_top_bare.png` / `render_bottom_bare.png`
   existed nowhere outside v1.5 — a **skipped stage**. And the nine machine-
   evidence files (`drc.json`, `erc.json`, `audit.txt`, `bom_source_check.txt`,
   `stock_check.{json,txt}`, `release_freshness.txt`, `manifest_selfcheck.txt`,
   `standalone_archive_drc.json`) existed nowhere under `06_build`: the gates ran
   and their output went to **stdout**, never to an artifact. A number in a chat
   message is not evidence.

### And the missing evidence hid a real defect

v1.6's `source/fp-lib-table` was copied raw from `04_kicad/` and points at
`${KIPRJMOD}/../03_src/lib/...`, which **does not exist inside the archive**.
Extracted on its own, v1.6's archive yields **12 `lib_footprint_issues`** (DRC)
and **12 `footprint_link_issues`** (ERC). v1.5 rewrote that table to
`${KIPRJMOD}/`; v1.6 did not. The gate that catches exactly this is
`standalone_archive_drc.json` — **one of the 21 files v1.6 was missing**. v1.7
fixes the table and ships the proof: standalone archive DRC **0/0/0**, extracted
to a bare directory with no project around it.

### Why no gate caught it

**M-REL requires only that `verification/` exist and be non-empty.** Thirteen
files satisfied it. A directory-presence check cannot see a missing artifact —
the same shape as `jlc_twin` exiting 0 on 11 parts it never verified. A
required-artifact-list check is proposed (not landed) in the seal commit.

### v1.7 verification set

34 files, matching v1.5's list exactly (`comm -23` empty), plus the gates re-run
against the **shipped artifact** rather than the working tree.

## v1.6 — 2026-07-26

### THE TARGET IS A RASPBERRY PI 4, NOT A PI 5 (ADR-0004)

Every power document on this board rested on one sentence recorded at
commission: that the Pi can be told to skip PD negotiation and assume a 5 A
supply via `PSU_MAX_CURRENT=5000`. **That is a Pi 5 bootloader-EEPROM feature.
The user has confirmed the load is a Pi 4, which has no such setting.**

The conclusion — no PD source controller — survives. The reason does not, and
the difference is not cosmetic. A Pi 5 *is* a PD sink and the old story was
"talk it out of negotiating". A **Pi 4 does not negotiate PD for its power input
at all**: its USB-C input is a plain 5 V sink with CC pull-downs, officially
**5 V / 3 A (15 W)**. A plain regulated rail is not a workaround for a Pi 4, it
is the only interface it has. ADR-0001 is marked `superseded-by: 0004`
(reasoning only); the BRIEF keeps the old paragraph struck, not deleted.

**The margin improves 16.5x.** Same hardware, same 97 mOhm budget, same 1.2
derating, same 5.227 V worst-case rail, same 4.63 V threshold — only the load
changed, because we now know what it is:

| | IR drop | delivered | slack |
|---|---|---|---|
| Pi 5 premise @ 5 A | 582.0 mV | 4.645 V | **+15.0 mV** |
| Pi 4 actual @ 3 A | 349.2 mV | 4.878 V | **+247.8 mV** |

E-MARGIN re-graded PASS at 3 A. *"15 mV of paper slack is not a margin you ship
on"* was a true statement about the wrong load, and it is retired. The bench
gates are not — Q2/Q5 are now judged against the 3 A number.

`load_uv_threshold: 4.63` is unchanged: it was always the **Pi 4** figure, until
now applied to a Pi 5 by inference. And one number is upgraded from inference to
specification — the **Pi 4 absolute maximum input is +6.0 V** (Pi 4 datasheet
p.8, Absolute Maximum Ratings, *"a stress rating only"*).

`power_tree.yaml` USB-C `iout_max_A: 5 -> 3`. **The board stays provisioned for
5 A** — buck-C, the F2 7 A polyfuse, the VBUSC via count and the delivery-corner
pours — and that is now stated as deliberate over-provisioning rather than left
as an unexplained mismatch.

### D5 / U12 — RESOLVED by the Pi 4 numbers; do not reselect

| V | what | source |
|---|---|---|
| 5.479 | worst-case operating VBUSC | power_tree.yaml |
| 6.00 | **Pi 4 ABSOLUTE MAXIMUM input** | Pi 4 datasheet p.8 |
| 6.00 | U12 guaranteed non-conduction floor (V_BR min; no typ, no max) | ST 11265 rev 5 Table 2 |
| 6.67 | D5 breakdown **minimum** | Littelfuse SMBJ rev 06/03/20 |

**D5 cannot protect the Pi** — by the time it conducts, the rail is already
670 mV above the Pi's absolute maximum. It never could have, at any breakdown
that also clears a 5.479 V operating rail. The TVS protects the **board** against
**transients**. So the "inverted hierarchy" is a non-issue for the Pi and the
empty TVS window does not matter. **Stated plainly: nothing on this board
protects the Pi from a SUSTAINED over-voltage** — a TVS clamps transients, not a
stuck regulator — which is the fail-high posture the BRIEF already accepts as
best-effort for a supervised prototype. Escalation, if that ever changes, is an
**active OVP at ~5.6-5.7 V (a disconnect/crowbar), NOT a different TVS**.

### R42 — a DNP setpoint-trim strap, and the series-resistor trap

The user asked for an optional way to drop the rail if the bench says U12 is
stressed; the instinct was a **series resistor in the 5 V line**. Recorded as
rejected because it is genuinely attractive and wrong: over-voltage is a
**light-load** phenomenon and IR drop is a **heavy-load** one, so they are
anti-correlated. At 0 A a series part drops 0 mV — nothing in the exact case it
was added for; at full load it removes voltage when the rail is already lowest.
It costs 72 mV and 0.18 W at 3 A, and does nothing about a fail-high
(20 mOhm x 3 A = 60 mV of a multi-volt excursion).

Instead **trim the setpoint**: `R42 = 160k, 0402, DNP, in PARALLEL with R12`
(the buck-C FB top). Rtop 4.12k -> 4.12k||160k = 4.017k, rail **5.352 -> 5.249 V**,
landing on U12's 5.25 V V_RWM — load-independent, zero heat, zero delivery cost.
Fitted, worst-case vout_min 5.227 -> 5.125 V, minus 349 mV = 4.776 V, still
**+146 mV**. *The trim is only affordable because the load is a Pi 4;* at 5 A it
would have eaten the whole margin. Ships **unpopulated**, declared
`dnp_by_design` with dated evidence, deliberately uncoded, and its value pinned
by an E-INV `part_value` assert — the parallel combination is nonlinear in the
strap, so a 16k slip gives 4.500 V and a board that browns out at no load.

New bench gate: measure VBUSC at no load and at 3 A, and U12 leakage at the
measured voltage over temperature. **PASS = fit nothing if U12 leakage is
acceptable at 5.352 V; fit R42 if not.** Record the numbers either way.


**COPPER revision.** `07_releases/v1.6-2026-07-26/`. **v1.5 and every earlier
release are DO-NOT-ORDER.** v1.5 gains `SUPERSEDED.md`; it is otherwise
immutable.

### Why v1.5 became DO-NOT-ORDER: a datum defect in the CPL exporter

A new **A-POS** gate measured every CPL row against JLC's own convention and
found **11 of v1.5's 108 rows off-datum**. JLC positions a part from the
bounding box of its **PAD CENTRES**; the exporter had been emitting
`fp.GetPosition()`, the footprint **anchor**, which is only the same point when
the land happens to be symmetric about it. Measured error, per ref:

| ref | offset from JLC's datum |
|---|---|
| J1 (XT60, the pack inlet) | **4.6861 mm** |
| J2 / J3 / J4 (USB-A) | **3.7346 mm** each |
| J5 (USB-C, 0.5 mm pitch) | **1.4975 mm** |
| Q4 / Q5 / Q6 | 0.0625 mm each |

Every external connector on the board, and the worst of them by nearly 5 mm.
This is not a rotation question and no render would ever have shown it. The
exporter fix is in the tree; v1.6 re-exports from scratch and every row lands
on-datum.

### What changed in the copper

- **H3 mounting hole — a short of the 6 A rail to GND through a screw.**
  MEASURED on sealed v1.5, on FILLED copper: H3 (106.0, 24.0) is a 1.600 mm-radius
  NPTH carrying **`5VA` at 1.850 mm AND `GND` at 1.850 mm on BOTH outer layers** —
  0.250 mm of bare laminate and ~20 um of solder mask between them. Every M3
  fastener bridges it, including the smallest cap head (r 2.75). v1.5's only
  mitigation was a sentence in `ORDER_README` about nylon standoffs. v1.6 states
  a rule instead — **within r <= 4.00 mm of any mounting hole all outer copper is
  one net and that net is GND** — and enforces it by notching the 5VA pour (5VA
  now stops 4.50 mm from H3) and by raising the router's hole keepout 3.0 -> 4.2 mm
  so a signal wave cannot re-create it on a different net.
- **H4** — `VBUSA3` reached 4.152 mm, inside a DIN 9021 washer (r 4.50). The pour's
  SE corner is chamfered; it now stops at 5.00 mm.
- **In2 VIN plane vs every mounting drill** — the 9-12.6 V plane sat 1.850 mm from
  a 1.600 mm drill on all four holes (0.250 mm, against a +-0.13 mm NPTH position
  tolerance). A 12-gon rule area per hole pushes VIN to >= 2.077 mm. In1 GND is
  deliberately left alone: a grounded fastener touching GND is the benign case.
- **VBUS ampacity 0.5 -> 0.8 mm.** "Pour-fed" was true of the connector end and
  false of the feed: each of VBUSA1/2/3 ran **13.554 mm of 0.500 mm B.Cu at
  exactly the class floor** carrying ~2 A. One 0.650 mm segment per port cannot be
  widened (TPS2557 VSON-8 is a 0.650 mm pitch and an 0.8 mm track is wider than
  the pitch), so it takes a `scoped_floors` relaxation pinned to three 2x3 mm rule
  areas over those pin pairs, with the measured geometry as its evidence.
- **PowerPAK EP paste, all six power FETs.** Each carried **ONE 100%-area aperture
  over a 3.810 x 3.910 mm exposed pad = 14.897 mm2**; IPC-7093 asks 50-80% as an
  array. A vendored footprint (`03_src/lib/usb_hub_3s.pretty/
  PowerPAK_SO-8_Single_Paste65`) replaces it with a 2x2 window-pane at **65.0%**
  (4 x 1.5359 x 1.5762 = 9.683 mm2), webs 0.369/0.379 mm. The ratio is not
  invented: KiCad's own HTSSOP-20-1EP_...\_Mask2.75x3.43mm uses 4 x 1.11 x 1.38
  over 2.75 x 3.43 = **65.0%** for this same package family. Copper and mask are
  unchanged.
- **USB-C delivery corner.** PMID crossed F.Cu<->B.Cu on 2 vias and F2 had ZERO
  vias on either pad at 0.775 W. Now 4 per F2 pad, 6 across the PMID pour, and 3
  per J5 VBUS contact pair, all sites derived from live pad geometry.
- **Three fiducials (FID1-3).** v1.0-v1.5 shipped with none, on a board whose
  smallest machine-placed pitch is 0.500 mm (J5, which IS on the CPL). Nearly
  free during a spin, impossible afterwards.

### Status LEDs (user decisions D2/D3/D4)

Five indicators, **+11 placements and exactly +2 BOM lines**:

| ref | part | taps | current |
|---|---|---|---|
| D8 | C2296 amber | VIN via R37, returned through **Q8** | 1.504 mA typ (0.946-1.547) |
| D9/D10/D11 | C2297 green | **VBUSA1/2/3** — per port | 0.282-0.377 mA |
| D12 | C2297 green | **VBUSC** — post Q6 + F2 | 0.275-0.405 mA |

- **The pack LED had to be FET-gated.** There is no switched power node on this
  board: SW1's pads are GND / ENKILL / NC, and neither `VBAT` nor `VBAT_F` reaches
  a switch pole — it switches ENABLE. Ungated, D8 would add **1.504 mA to a
  271 uA OFF-state budget (6.6x) and flatten a 3S 5000 mAh pack in ~117 days**.
  Q8 (BSS138, the same feeder as Q7) gates it off ENKILL; the adder is Q8's
  I_DSS, <= 0.5 uA. `power_tree.yaml` quiescent 270 -> **271 uA**.
- **Per-port, not one rail LED**: with a single 5VA indicator a port that had
  latched off into current limit looks identical to a working one.
- **The C indicator taps VBUSC, not 5VC**, so a dark C LED with the A LEDs lit
  means the ADR-0002 protection chain opened. Cost to the 15 mV E-MARGIN slack:
  0.346 mA x 42.4 mOhm = **14.7 uV = 0.098%**.
- Silk: `PACK ON`, `USB-A1/2/3 5V`, `USB-C 5V OK`, and — because the pack LED is
  enable-gated and the XT60 stays hot — `LEDS DARK = SWITCH OFF` /
  `PACK STILL LIVE AT XT60`.
- **CPL rotation for C2296/C2297 is 0, NOT 180.** The pad-NUMBER fit returns 180
  at a 17.7x margin and is wrong: JLC numbers pad 1 = ANODE, KiCad's `Device:LED`
  is pin 1 = K, and both libraries draw the cathode WEST, so the parts already
  align. A 180 row would ship every indicator dark — indistinguishable from a
  dry joint. See the release notes for the two numbering-free channels.

### D5 / U12 protection ordering — the sourcing half of the story

*(Superseded in framing by "D5 / U12 — RESOLVED by the Pi 4 numbers" above, which
is the conclusion. This subsection is retained because the SOURCING result stands
on its own and saves the next person a day of catalog searching.)*

The finding is real and **the requested fix cannot be bought.** ST's USBLC6-2SC6
(U12) specifies VBUS-GND breakdown as **MIN 6.0 V @ 1 mA with no typ and no max**
(doc ID 11265 rev 5, Table 2); D5's breakdown MINIMUM is 6.67 V, so the small ESD
array conducts first. A replacement would need Vwm >= 5.479 V **and** Vbr(max)
< 6.00 V at once; that window is **empty** — the SMBJ family has no step between
Vwm 5.0 V and 6.0 V, and the tightest SMB part found at any qualifying Vwm
(SM6T6V8A) still breaks down 450 mV above U12's floor and is not JLC-stocked.
v1.6 therefore **records the accepted residual** with its numbers, corrects the
part.yaml (VBR window was `6.67-8.15 V @1mA`; it is **6.67-7.37 V @ 10 mA**, and
Ppk is 10/1000us not 8/20us), and names the escalation as an ACTIVE OVP rather
than a better TVS. Lowering 5VC is refused: it would spend the 15 mV margin.

### Two budget corrections, neither of them a hardware change

**The GND return was ABSENT, not negligible.** RL-2's 12 mOhm board-copper figure
named three segments — 5VC L2.2→Q6 tab 2.198, PMID Q6.S→F2.1 4.914, VBUSC F2.2→J5
2.209 — and all three are FORWARD path. The return from J5 back to the buck was
simply missing, and in a budget a missing term looks exactly like a zero one. Solved
2026-07-26 by the same method as the forward path (SOR on filled copper, 0.8 mm
cells, all four layers, 178 GND vias coupling them, converged on the one-port
resistance over 10350 sweeps): **0.956 mOhm**. It is small for the reason you would
hope — In1.Cu carries 17520 of 18908 GND cells, with B.Cu (12105) and F.Cu (9438) in
parallel — but at 5 A it is 4.78 mV, a third of the old 15 mV slack, so it had to be
counted rather than called negligible. `ir_budget_mohm: 97 → 98`; slack at 3 A
+247.8 → **+244.2 mV**.

**A Pi 5 at 5 A is now a DECLARED NON-GOAL**, not an implicit one, because the
margin is contingent on the load and not on the hardware — the copper is
bit-identical to the copper that measured +15.0 mV. The 5 A arithmetic is preserved
in `power_tree.yaml` so anyone retargeting finds it waiting: at 5 A the board still
PASSES E-MARGIN (588.0 mV vs 597 mV headroom = +9.0 mV) but is back on paper-thin
slack, and both the 4.63 V undervoltage threshold and ADR-0003's 6.00 V
absolute-maximum chain are **Pi 4 figures** that would need re-deriving.

### Gates and bench

- New bench gate (user decision D7): LEDs fitted, SW1 OFF, **measure pack current
  with a uA meter and record it with the ambient. PASS <= 300 uA.** That
  measurement, not the BSS138 datasheet's 25 C maximum, is what qualifies
  `quiescent_ua`.
- P-FACT `pad1_net_polarity` declared for both LEDs and for every polarized 2-pad
  part on the board (C1/C2 polymer, D1, D2, D3/D4, D5) — coverage was zero.
- E-INV gains `part_value` on all five 6.98 k ballasts plus the LED-cell topology
  asserts: 36 invariants, all holding.
- Two tier-preflight FAILs that predate v1.6 and were invisible when it sealed:
  the Default netclass rode a hardcoded 0.2 mm clearance while the router used
  0.18, and `island_rescue` scanned only the outer layers on a board with two
  inner planes.

## v1.5 — 2026-07-25

Released: `07_releases/v1.5-2026-07-25/`. **CPL-CORRECTION supersede of
v1.4-2026-07-23** (v1.4 gains `SUPERSEDED.md`, otherwise immutable).
**v1.4 and every earlier release are DO-NOT-ORDER. Order from v1.5.**

**Why: a P0 in the CPL, not in the copper.** Sealed v1.4 places **C1 and C2 —
100 uF / 35 V POLARIZED polymer electrolytics — at CPL 270.0 where the measured
correct value is 90.0**: 180 degrees reversed, directly across the 9.0-12.6 V 3S
LiPo input behind a 10 A fuse. A reverse-biased polymer electrolytic on a
near-zero-impedance pack heats, gasses and **vents**, at first power-up, before
any bench gate can run. Found by a pre-order PCBA audit
(`08_reviews/2026-07-25_v1.4_pcba-audit_assembly.md`, 15 findings, dispositions
PCBA-1..15) — the earlier reviews had audited the board, not what the machine
would build.

- **fab/cpl.csv — EXACTLY FOUR changed cells, and nothing else:**
  `C1 270.0->90.0`, `C2 270.0->90.0`, `Q7 270.0->180.0`, `J1 90.0->0.0`.
  108 placements both sides, 0 rows added or removed.
  - **C1/C2** (PCBA-1, P0): no per-LCSC rotation row existed for C2982822, so the
    exporter fell through to the footprint-NAME DB, which a per-part fact cannot
    live in. Polarity re-verified independently of the pad fit: JLC's own library
    silk draws a crossed **"+" over its pad 1** and a bar **"-" over pad 2**, and
    our pad 1 is on VIN.
  - **J1** (PCBA-2, P1): the name-DB pattern `^AMASS_XT60PW-M` is START-ANCHORED
    and this board uses a vendored `XT60PW-M_EdgeTrim`, so **no rule fired at
    all** and the offset silently defaulted to 0. Four-pad fit (2 blades + 2
    anchors) gives rms **0.0000 mm @270**, 12.0 mm out at 90.
  - **Q7** (PCBA-3, P1): `^SOT-23` = -90 is wrong for C78284. 3-pad asymmetric
    fit, rms 0.062 mm @180 vs 1.95 mm @270. Would have left Q6 un-gated — a dead
    or silently unprotected Pi rail.
  - Root cause behind all three, fixed at source before this release: a
    **handedness bug in `jlc_twin.xform()`** that NEGATED every rotation offset
    the tool ever reported (repo `e0d735c`, `9078ad9`, `95a8180`, `1b69760`).
- **NO COPPER CHANGE.** Gerbers, both drill files, `source/`, `3d/` and `pdf/`
  are **sha256-IDENTICAL to v1.4** — 20 files. Proven by RE-EXPORT from the
  unchanged board: 13/13 zip members identical once the plot's own timestamp
  comments are stripped (`verification/cpl_acceptance_gate.md`).
- **fab/bom.csv**: identical to v1.4 row-for-row except the **MPN column is now
  populated on all 43 lines** (was 0/43). Cross-checked against the
  independently datasheet-authored `02_parts/` directory names: **26/26 hard-part
  MPNs matched, 0 directories unaccounted for** (PCBA-10).
- **NEW `03_src/rules/assembly.yaml`** (PCBA-5) — the population set finally has a
  machine-readable home: `service` (incl. **THROUGH-HOLE assembly**, 4 refdes /
  22 plated holes, J1-J4), `sides: [top]` (measured 108/108), `fiducials: none`
  (deliberate: the smallest centre-to-centre distance between two distinct
  pads is a measured **0.500 mm** at J5, > 0.4 mm),
  `build_quantity: 5`, and F1/SW1 as the only `not_assembled` refdes with dated
  evidence. The MANIFEST `not_assembled:` line is GENERATED from it.
- **NEW `01_docs/DETAIL_DESIGN.md`** (PCBA-7) — it did not exist, although three
  sealed `part.yaml` files have cited sec.1/2/5 as authority since 2026-07-21.
  Derivations from the datasheets directly (LM5116 SNVS499I eq. 7-24; USBLC6-2
  Doc ID 11265 Rev 5). The sec.5 citation was wrong three ways and is corrected.
- **ORDER-PREVIEW HUMAN GATE** in ORDER_README (PCBA-8). v1.4 mentioned the JLC
  preview **zero times** while **12** twin findings are waived on exactly that
  gate — **C1/C2 among them**. P1-P7 now say what to look for and what rejects.
- **U12 over-voltage: ACCEPTED + MEASURED** (user decision; MANIFEST waiver
  **W-U12**). 5.352 V nominal / 5.479 V worst corner vs the 5.25 V at which ST
  characterizes leakage — but ST's absolute-ratings table carries **no V_BUS
  limit** and V_BR is **6.0 V minimum**, cleared by 521 mV. R12 deliberately NOT
  changed. Bench gate Q1 now RECORDS measured VBUSC/VBUSA.
- **Stock, at build_quantity 5:** PASS, 43/43 lines OK, 0 uncoded. Split **12
  Basic / 31 Extended** (~31 feeder setups, priced before the order). Tightest
  ceilings: C473910 = **37 boards**, C5337088 = 90, C408523 = 225. Table rebuilt
  sorted by tightness with a named alternate per row (PCBA-13/14).
- **Panel-rail policy, measured:** three of the four edges cannot take a rail —
  J1 (-6.82 mm), J2-J4 (-4.29 mm) and J5 (-2.90 mm) physically OVERHANG the
  outline. Only the edge opposite the USB-C connector is usable (+1.43 mm).
- **TWO fresh review lenses, both ORDER**, both archived in `verification/`:
  a zero-context lens over the STAGED release (0 P0 / 3 P1 / 9 P2 — it
  re-derived the four CPL cells five ways and got **107/107 parts agreeing with
  the shipped CPL to <1°**, and it found real defects in this release's own
  paperwork, all fixed), and the **FIRST layout/thermal/power-integrity lens
  ever run against THIS copper** (0 P0 / 5 P1 / 7 P2). The prior layout lens was
  written against the **v1.0** board; 10 footprints were added afterwards
  (C53, C54, D5, F2, Q6, Q7, R30, R34, R35, SW1; tracks 642→1061), so the whole
  discrete VBUS protection chain had never been layout-reviewed — v1.3 and v1.4
  both sealed carrying that claim.
- **Build note that changes what you do (RL-3):** H3's mounting hole has **5VA
  and GND copper both starting at r = 1.80 mm, on BOTH outer layers**. A metal
  M3 screw head bridges the 6 A USB-A rail to GND through solder mask alone.
  **Fit a nylon screw, or leave H3 unfitted.** ORDER_README section 3a, B1.
- **The Pi-rail margin is thinner than any previous release said.** The board
  copper on the 5 A path was a **~3 mΩ estimate** carried since v1.3; the layout
  lens MEASURED it at **≥9.32 mΩ** (mesh solve; true ≈10.4-11.6). Three figures
  have now been published for this one margin — **157 mV → 69 mV → 15 mV** —
  each step removing an optimistic assumption without the hardware changing.
  `power_tree.yaml` synced (`vout_min` 5.27→5.227, `vout_max` 5.43→5.479,
  `ir_budget_mohm` 88→97); E-MARGIN re-run **PASS**. 15 mV of paper slack is not
  a margin to ship on — bench gates Q2/Q5 measure the delivered voltage.
- **The archive is self-contained for the first time (PCBA-16).** `source/
  fp-lib-table` pointed at `${KIPRJMOD}/../03_src/lib/` — OUT of the release —
  so a standalone re-measure of v1.3/v1.4 raises **6 `lib_footprint_issues`**
  despite the vendored `.pretty` folders being shipped, and their MANIFESTs
  claim the path they do not have. v1.5 points it at the vendored copies:
  standalone `kicad-cli pcb drc` from inside the archive now reads **0
  violations / 0 unconnected**. Cost: `fp-lib-table` is the ONE payload file not
  byte-identical to v1.4 (19, not 20) — a library-path line, not copper.

## v1.4 — 2026-07-23

Released: `07_releases/v1.4-2026-07-23/`. **DOCS-ONLY supersede of
v1.3-2026-07-23** (v1.3 gains `SUPERSEDED.md`, otherwise immutable — the one
allowed addition). **Board, BOM, CPL, gerbers, source and PDFs are
byte-identical to v1.3** (22/22 files sha256-verified; the freshness gate's
9 identical-artifact findings are the release's declared purpose, waived with
evidence in `verification/freshness_waiver.md`). v1.3's electrical state and
verification battery stand unchanged. **Order from v1.4.**

Driven by a post-seal user-supplied external review
(`08_reviews/2026-07-23_v1.3_external-user_full.md`, dispositions EXT13-1..8):

- **SW1 fallback-header shunt polarity was REVERSED in the v1.3 README.**
  The tsx wires SW1 pin1=T1→GND, pin2=COM→ENKILL; grounding ENKILL shuts both
  bucks down and opens Q6. Correct: **COM-T1 shunted = OFF; shunt removed =
  ON.**
- **F1 was misdescribed as "KH-AF90DIP-112"** (the USB-A connector family).
  F1 = **Keystone 3568 MINI-blade fuse holder, C5249699** (BOM row 38).
- **Tolerance-inclusive worst-case rail table** replaces the Vref-only
  numbers: R13/R4 = C5126242 = FRC0603F1211TS **±1 %** (ledger row 150) was
  omitted. 5VC static range **5.227-5.479 V** (was 5.272-5.432); low-corner
  headroom **597 mV vs the 440 mV IR budget — E-MARGIN still PASS** (157 mV
  slack); 5VA top corner 5.273 V slightly above the 5.25 V USB-A intent
  (accepted, no-data charge ports; 0.1 % R13/R4 recorded as next-rev option).
- **Packaging note:** F1 (C5249699) + SW1 (C2939728) are on `fab/bom.csv` but
  intentionally off `fab/cpl.csv` (hand-solder) — JLC upload shows 2 unmatched
  designators; README instructs marking both DNP + a hand-fit purchasing list
  (incl. the off-BOM 10 A MINI blade fuse element).
- **Bench qualification TIGHTENED** (Q0-Q7, adopted from the review): R12 AND
  R30 ohmmeter pre-power; no-load rails with a **5.45 V firm ceiling**;
  VBUSC@5A ≥5.00 V at the board; 5 A→0 A load-release overshoot capture;
  cable-end hot ≥4.80-4.85 V; SW1/header continuity logic; `vcgencmd
  get_throttled` through the Pi stress test. OV posture (Option 2) carried
  VERBATIM.

Verification scoping (canon): docs-only fix-pass — targeted source-evidence
confirmations (`verification/2026-07-23_v1.4_docfix_confirmation.md`), M-BOM
re-run PASS, policy_audit re-run 0 FAIL; no fresh review lens (no new
electrical state).

## v1.3 — 2026-07-23

Released: `07_releases/v1.3-2026-07-23/`. **Supersedes v1.2-2026-07-23**
(v1.2 was found **DO-NOT-ORDER** by an external human review after seal; it gains
`SUPERSEDED.md`, otherwise immutable). v1.3 is the FIX PASS for the confirmed
blockers — a BOM + docs + artifact-regen revision; the netlist topology and
routing are unchanged (same promoted KRT chain).

**R12 catalog-verified (THE order blocker).** v1.2's BOM resolved R12 to
**C2933210 = 3.74 kΩ** (tscircuit value-resolution; the tsx left R12 uncoded),
driving the buck-C setpoint to ~4.97 V undervoltage. v1.3 bakes the LIVE-catalog-
verified **C2984354** (AR03BTCX4121, Viking **4.12 kΩ ±0.1 % ±25 ppm** 0603,
stock 15 353 on 2026-07-23) into the tsx (`fbtopMpn`); verified alternate
C861436 (Yageo RT0603BRD074K12L). The buck-C setpoint is RE-DERIVED against the
ACTUAL Q6+F2 delivery path (Q6 AON6403 ~4.3 mΩ + F2 SMD2920-700 R1max 18 mΩ
catalog-verified — NOT the removed eFuse 34-48 mΩ model): 5VC 5.352 V nom /
5.27 V worst-case; **E-MARGIN PASS** (640 mV headroom vs 528 mV need at
ir_budget 88 mΩ).

**D5 directionality fixed.** v1.2's C140903 is listed **BIDIRECTIONAL** by the
JLC catalog (LRC SMB-FL) — the design's uni-directional cathode-on-VBUSC
assumption was unverifiable against it. v1.3 uses **C113976** (SMBJ6.0A
**UNIDIRECTIONAL** DO-214AA/SMB, catalog-verified, stock 74 758).

**R30 catalog-verified (2nd wrong-part, caught by the semantic M-BOM gate).**
v1.2's BOM resolved R30 (Q6 gate pull-up, QG→PMID) to **C2933195 =
FRC0603F3091TS = 3.09 kΩ** while labeled 100 kΩ (v1.2 SUPERSEDED addendum,
`688a8af`) — functional but burning ~1.7 mA through Q7 whenever the port FET was
ON. v1.3 bakes **C25803** (UNI-ROYAL 0603WAF1003T5E, **100 kΩ ±1 %** 0603, JLC
Basic, ledger-verified; MPN E96 decode `1003` = 100×10³) — the same code the
board's other 100 k 0603s (R1/R8/R17) resolve to, so the BOM row merges (43
grouped lines). Q6 margins re-derived at 100 k from the AON6403 STATIC table:
OFF/back-feed |Vgs| ≈ 60 mV (Q7 Idss 0.5 µA + Q6 IGSS 0.1 µA × 100 k), 20×
below |Vgs(th)|min 1.2 V → blocks; ON Vgs = −5.35 V (fully enhanced); pull-up
waste 54 µA vs ~1.7 mA at 3.09 k.

**OV honesty (BRIEF A3/D3, Option 2 — user decision).** The discrete Q6/Q7/F2/D5
chain is kept as **SECONDARY** protection; no active OVP added. Docs now state
plainly: protected against shorts / overload / reverse-feed-off; **NOT guaranteed
against a buck high-side short** (D5+F2 = best-effort crowbar). Context:
supervised prototype, replaceable Pi. Escalation boundary (verbatim): "add active
OVP if the system becomes unattended, hard-access, carries valuable storage, or
powers expensive SDR".

**Assembly:** SW1 (SS12D07) moved **off automated assembly** (hand-solder;
VG4-vs-VG6 pitch unconfirmed; header+shunt fallback documented). F1 holder's CPL
status corrected to match its documented hand-solder plan (was erroneously
machine-placed in v1.1/v1.2 CPLs). CPL 108 placements.

**ORDER_README:** bench-qualification plan baked as a REQUIRED pre-Pi-connection
deployment gate (Q1-Q5: assembled-R12 measurement, 8-24 h electronic-load soak,
switch-node scoping at 12.6 V, thermal soak, end-of-cable VBUSC verification).

All release artifacts regenerated fresh from v1.3 source and sha256-distinct from
v1.2 (the v1.2 stale-artifact defect class is machine-checked by
`release_freshness_check.py` this release).

## v1.2 — 2026-07-23

Released: `07_releases/v1.2-2026-07-23/`. **Supersedes v1.1-2026-07-23**
(v1.1 gains `SUPERSEDED.md`, otherwise immutable).

**Discrete VBUS protection — the eFuse is DROPPED (ADR-0002; BRIEF A2/D2 user
decision).** The v1.1 TPS26631 eFuse was over-built for a 5 V/5 A Pi rail and was
the root cause of BOTH the board routing wall (its 20-pin HTSSOP IN_SYS pin boxed
in a fine-pitch escape) AND v1.1's two electrical order-blockers. −9 parts / +1 =
**110 total**. New USB-C protection chain: `5VC → Q6 (AON6403 P-FET,
ENKILL-gated reverse-block via Q7 BSS138) → F2 (PPTC polyfuse 2920, 7 A/16 V) →
VBUSC → J5`, with **D5 (SMBJ6.0A TVS)** over-voltage clamp. buck-C FB stays on
**LOCAL 5VC** (R12 4.12k → 5.352 V; the v1.1 runaway fix). buck-C EN re-merged to
ENKILL. Removed: U13, R31/R32, R33/R36, C51/C52, D6, D7.

Gates at seal (git_sha in `MANIFEST.txt`, `git_dirty: false`):
- DRC **0/0/0** (severity-all, refill-zones, schematic-parity); source/ standalone
  re-measure **0/0** (V-REL-FPLIB).
- ERC 0; parity **110 ×5 sources**; E-INV **24/24**; E-ADR/E-TOPO/E-MARGIN/E-OFF PASS.
- policy_audit **0 FAIL** (PASS=27, WAIVED=2: R-THERM + R-POUR); M-BOM (BOM==source) PASS.
- jlc_twin **GREEN** — F2 (C6165170), D5 (C140903), Q6 (C2760089/AON6403) fetched +
  fit; all PAD-GEOM/PAD-MISMATCH/POLARITY-CHECK adjudicated.
- Fresh zero-context red-team: **ORDER** (architecture approved, no design P0; Q6
  5 A / 0.11 W OK, reverse-block correct). Report in `verification/`.
- 2 Extended-tier parts (F2, D5) carry a MANDATORY order-day `jlc_stock` recheck
  (ORDER_README); first-power OV caution documented (ADR-0002 tradeoff).

## v1.1 — 2026-07-23

Released: `07_releases/v1.1-2026-07-23/`. **Supersedes v1.0-2026-07-22**
(review-driven revision; v1.0 gains `SUPERSEDED.md`, otherwise immutable).

Protected-VBUS revision. +15 parts (115 total). Adds a **TPS26631 eFuse** (U13)
with a **two-FET reverse-current block** (Q6 AON6354 + Q7 BSS138) on the USB-C
rail — **5.83 A current-limit, 5.91 V input-OV cutoff, soft-start, auto-retry**;
moves the USB-C setpoint to **5.151 V sensed at the connector** (buck-C FB → VBUSC,
resolving the Blocker-2 4.97 V finding); adds a **master-off slide switch (SW1)**
on the merged EN bus; raises buck caps to **50 V input / 10 V output** (RT-T2/T5);
adds optional (DNP) SW-node snubbers; relabels silk/docs to the honest framing
(Pi-dedicated 5 A, NOT USB-PD; power-distribution board, not a USB hub).

Gates at seal (git_sha in `MANIFEST.txt`, `git_dirty: false`):
- DRC **0/0/0** (severity-all, refill-zones, schematic-parity); source/ standalone
  re-measures **0/0/0** (V-REL-FPLIB, with vendored `usb_hub_3s.pretty` +
  `Button_Switch_THT.pretty`).
- policy_audit **0 FAIL** (PASS=27, WAIVED=2 [R-THERM + R-POUR ev-backed], HUMAN=6,
  N-A=2). **E-INV 16/16, E-ADR, E-TOPO, E-MARGIN, E-OFF PASS**; P-LAYOUT/P-ADJ PASS.
- JLC twin **exit 0** (88 OK / 232 checked; U13 fit 0.01 mm, Q7 0.08 mm; Q6 reuses
  the AON6354 merged-drain adjudication; SW1 new — pitch confirm at order).
- Pin review PASS, render review PASS. Fix-confirmation review resolves each
  external-review finding (`08_reviews/2026-07-23_v1.1_fix_confirmation.md`).

Carried decisions / open items (none blocks the order):
- **SW1 (SS12D07VG6) footprint pitch = MANDATORY JLC order-preview confirm** — our
  2.5 mm (standard SS-12D07) vs JLC's mislabeled-VG4 model 2.0 mm; jumper fallback.
- **Snubbers R34/R35/C53/C54 = DNP-by-design** (bench-tune footprints; removed from
  fab BOM/CPL, pads remain in gerbers). Encoding `doNotPopulate` in the tsx is a
  next-rev item.
- Bench: loop-stability Bode with the eFuse in-loop; OVP no-false-trip at 5 A.
- **RT-T3** (LM5116 UVLO ~9.65 V cold-start > 9.0 V nominal) accepted as documented
  P2 (LiPo deep-discharge protective) — unchanged from v1.0.

## v1.0 — 2026-07-22

Released: `07_releases/v1.0-2026-07-22/`

First orderable release. 3S-LiPo powered 3-port USB hub (3× USB-A 5 V + 1×
Pi-dedicated USB-C 5 V/5 A), 4-layer, 130.1 × 92.1 mm, XT60 input →
10 A MINI-blade fuse → dual synchronous LM5116 bucks.

Gates at seal (git_sha in `MANIFEST.txt`, `git_dirty: false`):
- DRC 0/0/0 (severity-all, refill-zones, schematic-parity); source/ re-measures
  0/0/0 standalone (V-REL-FPLIB).
- policy_audit 0 FAIL (PASS=19, WAIVED=1 R-THERM evidence-backed, HUMAN=6, N-A=9).
- E-INV / E-ADR / E-TOPO PASS; P-LAYOUT / P-ADJ PASS.
- JLC digital twin exit 0 (80 OK / 209 checked; all criticals adjudicated).
- Pin review PASS, render review PASS.
- Red-team **topology: ORDER** — the original memo's DO-NOT-ORDER was a pre-fix
  snapshot driven solely by P1 RT-T1 (fuse 20 A→10 A, fixed `071fe56`); an
  independent zero-context re-review returned ORDER and re-confirmed the 10 A
  sizing (`verification/…_topology_rereview.md`, `verification/RT-T1_regate_note.md`).
- Red-team **layout: ORDER**, zero P0/P1.

Key decisions carried in this release:
- USB-C port is Pi-dedicated; needs `PSU_MAX_CURRENT=5000` on the Pi 5 EEPROM
  for 5 A (ADR-0001).
- F1 10 A MINI blade element is hand-fit (off-CPL); the Keystone-3568 holder
  (C5249699) is JLC-placed.
- F-2.1 (LM5116 UVLO ≈ 9.65 V cold-start > 9.0 V nominal) accepted as a
  documented P2 per user decision (doubles as LiPo deep-discharge protection).
- P2 next-rev work order (RT-T2/T4/T5, AON6354 doc hygiene, LM5116 EP via-arrays
  + VBAT_F B.Cu pour) recorded in `ORDER_README.md`; none blocks this order.
