# usb-power-3s — full independent review + audit (2026-07-19)

Fresh-eyes audit of the released project against the CURRENT canon
(`design-policies.md` incl. S-DSL, I10b, R-THERM, P-SILK-FN, small-via/fab
lessons). Live release under audit: **07_releases/v1.3-2026-07-17**
(SUPERSEDED chain v1.0 → v1.1 → v1.2 → v1.3 verified closed; v1.3 has no
SUPERSEDED.md). Policy: adopted-forward — releases predating a policy are
graded honestly, gaps tracked, sealed artifacts untouched.

Everything below was re-measured on 2026-07-19 (fresh ERC + DRC, fresh
policy_audit, fresh stock check, fresh-context pin reviews, fresh renders)
— nothing is copied forward from the release's own verification bundle
without re-verification.

## 1. Graded scoreboard (every canon ID)

| ID | Grade | Evidence (re-measured 2026-07-19) |
|---|---|---|
| S1 / S-ERC | PASS | fresh `kicad-cli sch erc --severity-all`: 0 errors, 1 warning = documented baseline (isolated_pin_label PGOOD_B, max 1 in erc_warning_baseline.yaml) |
| S2 / S-NET | PASS | 54 routed nets all deliberately named; only legitimate `unconnected-(…)` autonames on sanctioned NC pins |
| S3 / S-VER + pin review | PASS | 6/6 part.yaml `verified:` cite figure+page; THREE fresh-context re-derivations run today (§3): LM5145, CSD18543Q3A, LM74800+XT60 — no mirror, no swapped pin, all verdicts PASS |
| S4 / S-NC | PASS | all floats carry generator-emitted no_connect flags; ERC pin_not_connected = 0 |
| S5 | PASS | 3 derivations re-computed exactly: Vout = 0.8·(1+20k/3.74k) = 5.078 V; UVLO/OV ladder 9.33 V / 15.25 V (T = 1021.8k); TPS2557 IOS = 61050/24.3 = 2.51 A — all match DETAIL_DESIGN.md and the BOM values |
| S6 | PASS (graded EFFORTFUL) | schematic has 7 titled section boxes + 25 drawn story wires (UVLO ladder chain, gate networks, FB/ILIM chains) + GND power icons (v1.3); the majority of connectivity is still label-pairs (J1→F1, decoupler banks) — readable with effort, debt visible and tracked |
| S7 | PASS (adequate) | decouplers drawn inside their IC's section with purpose comments ("100n at U1.A", "100n CAP-VS"), not pin-attached; acceptable, same debt class as S6 |
| S-DSL | PASS | schematic compiled by schwriter2 to native .kicad_sch; every gate runs on artifacts (ERC/parity/S-OCCL on the .kicad_sch itself) |
| S-OCCL | PASS | fresh policy_audit: 0 text occlusions |
| P1 / P-CRT | PASS | fresh full-severity DRC: 0 courtyard findings |
| P2 / P-POL | PASS | machine check present AND independently re-derived this audit (§4): D1–D3 TVS pad1(cathode)=rail, D4/D5 LED pad1(cathode)=GND, CE1 pad1(+)=VSW, J1 pad1('−')=GND with '+/−' silk paired to the correct pads — all correct vs footprint conventions, not just vs part.yaml |
| P3 / P-KEEP | PASS | mate/edge/screw-keepout checks present in audit_board.py; fresh audit.txt: PASS 0 fails 0 warns |
| P4 / P-SILK-REF | WAIVED-valid | re-measured: 0 refdes on silk, 96 on F.Fab — exactly the waiver's claim; policy adopted 1 day after v1.1; fab sealed; next-spin remediation named |
| I10b (refdes occlusion) | N-A | no refdes on silk to occlude (subsumed by the P4 waiver); F.Fab copies legible except the front-end cluster (finding F6) |
| P5 / P-SILK-FN | WAIVED-valid | re-measured: silk text = exactly 2 items ('+','−' at J1, correctly placed); no functional words near F1/J2–J5 — matches waiver; functions live in ORDER_README + assembly PDF; next-spin labels named |
| P6 / P-PLANE | PASS | In1 carries only the GND plane (0 tracks) |
| R1 / R-RULES | WAIVED-valid | r0.kicad_pro still shows classes=['Default'] (historical route input, deliberately as-shipped); remediation landed (03_src/route_prep.py builds rule-carrying route inputs); waiver expires at the next routing campaign |
| R2 / R-POUR | WAIVED-valid (= tracked defect) | re-measured on the board: VBUS1–3 are 0.8 mm F.Cu runs (~15 mm each, all segments 0.8 mm), 2 vias/net feed only the B.Cu port-cap spur (1.2 mm) — exactly the waiver's numbers; 2.51 A ILIM-bounded, ~16 °C rise, margin bar honestly NOT met; carried as a NEXT-SPIN DEFECT, not evidence-of-adequacy |
| R3 / R-PLANE | N-A | no plane_regions configured; no sensitive analog on this board — acceptable |
| R4 | PASS | escape feasibility proven empirically: 0.5 mm-pitch VQFN fanned out with 0.25/0.15 vias at the JLC ADVANCED tier, DRC 0/0/0 |
| R5 / R-LEN | N-A | no timing-critical nets on a power-only board |
| R6 / R-THERM | PASS | fresh check: all pads ≥4 mm² on power nets have ≥2 nearby same-net vias (TPS2557 EPs, FET tabs included) |
| R7 / R-DRC | PASS | FRESH `kicad-cli pcb drc --severity-all --refill-zones --schematic-parity` today: 0 violations / 0 unconnected / 0 parity — identical to the release's verification/drc.json |
| M1 | PASS | independent-reference battery demonstrably ran: JLC twin (caught the v1.0 mirror), fresh-agent pin review, and THIS audit re-ran all of it from outside the project's assumptions |
| M2 | PASS | canon IDs machine-enforced via policy_audit.py; project-level audit_board.py present |
| M3 / M-REPRO | PASS (one gap → F5) | all rebuild inputs git-tracked incl. promoted chain 03_src/route/r5.kicad_pcb; GAP: no MANIFEST records the chain file's sha (canon M3 letter) |
| M4 / M-WAIV | PASS | all 4 waivers + 3 twin adjudications carry measurements; every waiver's evidence RE-VERIFIED true on current artifacts today (see WAIVED rows above) |
| M5 / M-REL | PASS | v1.3: full sha256 table verifies file-by-file (6/6); git_sha d8992b8 exists, tree board sha 81a01c2e matches the release claim byte-for-byte; DRC regenerated from that board = 0/0/0; CHANGELOG names the dir; chain closed; fix-claims (parity 0, S-OCCL 0, GND-icon change) evidenced in verification/render_review.md + policy_audit.md; v1.0/v1.1/v1.2 git_shas all exist (b69807f, 522d61c, 5d45e54) |
| M6 | FINDING (F1) | authoritative-source discipline mostly honored, EXCEPT: three ROT-DB-SUGGEST twin findings on POLARIZED electrolytics left with no disposition (see findings) |

Fresh policy_audit.py summary (FULL mode, 2026-07-19): **zero FAIL** — 14 PASS,
4 WAIVED (all evidence-verified), 6 HUMAN (graded above), 2 N-A.

## 2. Release integrity (M-REL detail)

- v1.3 MANIFEST sha256: all 6 files re-hashed, all match.
- `git_sha d8992b8` exists; `04_kicad/usb_power_3s.kicad_pcb` at HEAD ==
  d8992b8 == release claim (sha256 81a01c2e…). Fresh DRC from that board:
  0/0/0 — matches verification/drc.json (2026-07-17).
- Fab byte-identity claim verified: gerbers.zip/bom.csv/cpl.csv sha-identical
  across v1.1, v1.2, v1.3 (v1.0 differs — the superseded mirror-footprint
  build, correctly quarantined by SUPERSEDED.md "DO NOT ORDER").
- CHANGELOG has an entry naming every release dir; SUPERSEDED chain closed.
- BRIEF prompt_sha256 verifies by its documented command.
- Stock re-verified TODAY: all 37 coded BOM lines in stock (PASS), 1 line
  intentionally uncoded (USB-A CNCTech, hand-solder per A5/MANIFEST).

## 3. Fresh-context pin reviews (S3 bar: derived from datasheet FIGURES first)

Three independent fresh agents, conclusion-free dossiers (pad geometry +
nets only, no part.yaml):

| Part group | Verdict | Key derivation |
|---|---|---|
| U2/U3 LM5145 (VQFN-20 RGY) | **PASS** | SNVSAI4 Fig 6-1: pin1 top-left, CCW, 2/8/2/8 per side; board = same package rotated 180°, rotation-only, NOT mirrored (the v1.0 defect class is absent); all 21 pads sane incl. SYNCIN→GND (diode emulation), EP→GND, NC/EP-pin floats; U3.EN-from-PGOOD_A question resolved on-board: R21 20k pullup to 5V_C + R33/R34 divider → EN = 2.30 V > 1.2 V |
| Q1,Q2,QA1,QA2,QB1,QB2 CSD18543Q3A (VSON-8) | **PASS** | SLPS432 top view: pads 1-3 = S, 4 = G, tab = D; body diode A=S→K=D. Q1/Q2 = common-drain back-to-back at FE_MID: blocks both directions off, no sneak path, reverse-battery safe. Buck pairs: QA1/QB1 D=VSW S=SW_x, QA2/QB2 D=SW_x S=GND — correct high/low-side orientation, freewheel diode right way |
| U1 LM74800-Q1 (WSON-12 DRR) + J1 XT60PW-M | **PASS** (see below) | re-verified this audit against SNOSD95C Table 6-1 (now committed to 02_parts): all 12 pins match (DGATE=DG_FE, A=VSNS=VBATT_F, SW=FE_LAD ladder-top via internal disconnect switch, OV/EN ladder taps, GND, HGATE=HG_FE, OUT=VSW, VS=FE_MID common-drain +100n, CAP=FE_CAP, C=FE_MID); EP: datasheet demands "Leave exposed pad floating. Do Not connect to GND plane" — board EP has NO net ✓. J1: pad1='−'=GND, pad2='+'=VBATT_RAW, silk marks paired to the correct pads |

Third fresh agent (independent of my table check above) also returned
**PASS/PASS**: LM74800 winding = datasheet Fig 6-1 at rotation 0, no
mirror, all 12 pins match, EP-float mandatory per Table 6-1 ("RTN — leave
floating, do NOT connect to GND plane") and board complies (note: EP still
gets soldered to its isolated island — fine, pad exists netless). XT60
polarity derived through TWO independent chains — EasyEDA CAD JSON for
C98732 (pin1='−' south blade, mouth west) AND the Amass mounting drawing +
the XT60 shape convention (chamfered side = negative) — both agree with
the board: pad1(GND) = the physical '−' blade. Explicitly NOT a repeat of
the sister-board XT60 reversal.

## 4. Independent polarized-part re-derivation (Q9-class hunt)

Board pad-1 nets vs the FOOTPRINT's own convention (not part.yaml — the
class of doc errors that cancel):

| Ref | Footprint (pad1 meaning) | pad1 net | Verdict |
|---|---|---|---|
| D1 SMBJ16A | D_SMB (pad1=cathode) | VBATT_F | ✓ cathode to rail |
| D2/D3 SMBJ5.0A | D_SMB (pad1=cathode) | 5V_A / 5V_C | ✓ |
| D4/D5 LED | LED_0805 (pad1=cathode) | GND | ✓ (anode fed via 1k from rail) |
| CE1 100u hybrid | CP_Elec (pad1=+) | VSW | ✓ |
| CA7/CB7 220u poly | CP_Elec (pad1=+) | 5V_C / 5V_A | ✓ |
| J1 XT60PW-M | pad1='−' blade | GND | ✓, '+/−' silk on correct sides |

No self-consistent-wrong-together pair found. Wide-vs-narrow SOIC trap: N-A
(no SOIC packages on this board).

## 5. History coherence

- ARCHITECTURE.md power tree, net classes, interfaces == shipped board
  (spot-verified: J1→F1→U1/Q1/Q2→bucks→TPS2557/USB-C, ILIM values, Rp 10k).
- DETAIL_DESIGN math re-derives (§ S5). Note: the ladder-top shorthand
  "VBATT_F ─ R1 887k…" is realized through LM74800 pin 4 (SW, internal
  VSNS disconnect switch) — functionally identical, per SNOSD95C Table 6-1.
- ADR-0001…0005 all still describe the board. BRIEF criteria G1–G7 met.
- Drift found & FIXED this audit: BRIEF `current_release` pointed at
  v1.1 (two releases stale) → now v1.3-2026-07-17.

## 6. Findings table

| # | Sev | Finding | Falsifiable evidence | Remediation | New release? |
|---|---|---|---|---|---|
| F1 | **MAJOR** | Twin ROT-DB-SUGGEST on all three POLARIZED electrolytics (CE1 C454289, CA7/CB7 C128504) left UNDISPOSITIONED: pad-fit suggests CPL offset 0, shipped CPL applied the community-DB 180 (CE1/CB7 → 180, CA7 → 0 after board rot). JLC's EDA footprint has pad1(+) west like KiCad, so fit-vs-DB genuinely conflict and only JLC's ASSEMBLY-zero (order preview) can settle it. ORDER_README's preview-eyeball list omits exactly these three parts; twin render can't arbitrate (mounts at fitted angle; only ambiguous top-paint visible). A wrong call = reversed electrolytics on 5 V/12 V rails. | 07_releases/v1.3…/verification/twin_report.csv rows CE1/CA7/CB7; 06_build/twin/easyeda/C454289 & C128504 jlc.pretty pads (pad1 at −x); cpl.csv rotations 180/0/180; no entry in twin_adjudications.yaml; ORDER_README list | Disposition with authoritative evidence: JLC order-preview screenshot of the three caps (polarity stripe vs our + pads), or first-article photo if already ordered (MANIFEST says ordered 2026-07-17 → inspect BEFORE first power; a reversed polymer cap fails hot). Record as twin adjudication + add the 3 refs to the ORDER_README eyeball list in the NEXT release. | Not by itself (fab zip unaffected); a NEW release with corrected CPL ONLY IF the preview/first-article shows reversal |
| F2 | MINOR | BRIEF `current_release` stale (v1.1; live is v1.3) — history-coherence drift | 01_docs/BRIEF.md line 5 (pre-fix) | **FIXED this audit** (doc commit) | No |
| F3 | MINOR | LM74800 datasheet absent from 02_parts (sha256 "PENDING-FETCH") — violates CHECKLIST "every used part has a datasheet on file"; pin facts carried SPF provenance only | 02_parts/LM74800QDRRRQ1/part.yaml (pre-fix) | **FIXED this audit**: SNOSD95C fetched, committed, sha256 recorded, pins re-verified vs Table 6-1 | No |
| F4 | MINOR | XT60PW-M datasheet still "PENDING-FETCH" (vendor spec page only); polarity facts rest on footprint-silk + EasyEDA cross-check (which this audit independently re-confirmed) | 02_parts/XT60PW-M/part.yaml | Cache the Amass spec sheet when obtainable, or record a "no formal datasheet; facts from EasyEDA CAD + physical part" note with evidence | No |
| F5 | MINOR | Canon M3 letter unmet: promoted route chain 03_src/route/r5.kicad_pcb is git-tracked but its sha is recorded in NO MANIFEST | grep r5 07_releases/*/MANIFEST.txt → empty | Record the chain-file sha in the next release's MANIFEST (sealed releases stay untouched) | No |
| F6 | MINOR | Release PDF polish: pcb_layers.pdf / assembly_top.pdf title blocks empty (no title/rev/date; schematic.pdf has them), and assembly view has Fab-text collisions in the dense front-end region (values illegible → hand-solder aid degraded there) | 07_releases/v1.3…/pdf/*.pdf renders | export_pdfs.sh: set title block vars; Fab-text de-collision pass; next release | No (cosmetic) |
| F7 | NOTE | v1.1 MANIFEST used truncated sha256_16 hashes (v1.3 full table) — historical, superseded release, convention has already improved | v1.1 MANIFEST vs v1.3 | none (history not rewritten) | No |

## 7. Bottom line — orderability

**The live release v1.3-2026-07-17 is ORDERABLE AS-IS**, with one mandatory
order-time/arrival action:

- Fab package: DRC re-verified 0/0/0 TODAY from the exact release source;
  sha table verifies; gerber zip = the v1.1 copper that passed the mirror
  fix + twin + pin review; ADVANCED small-via option REQUIRED (0.25/0.15)
  — unchanged and clearly documented in ORDER_README.
- BOM/CPL: all 37 coded lines IN STOCK today; 1 intentional hand-solder
  line (USB-A). CPL rotations DB-corrected; VSON/VQFN corrections verified.
- **Mandatory (F1)**: before paying — or on first-article if the 2026-07-17
  order already went out — verify CE1/CA7/CB7 polarity (JLC preview
  stripe vs our '+' pads / physical bevel at arrival, BEFORE first power).
  Everything else in the protection chain (XT60 polarity, TVS, LED, FET
  body diodes, LM74800 pinout+EP-float) was independently re-derived
  clean today.
- All four waivers remain evidence-valid; VBUS 0.8 mm margin shortfall is
  an honest, ILIM-bounded next-spin defect (~16 °C rise worst case), not
  an orderability blocker.

Audit fixes committed (docs/parts only, no schematic/board/fab/release
artifacts touched): BRIEF current_release, LM74800 datasheet + part.yaml,
this report.
