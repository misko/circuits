# Future improvements

This is the repository-wide ledger for design-pipeline and process
improvements discovered while building boards. A project journal records what
happened during one stage; this file keeps the resulting work visible across
projects until it is implemented or deliberately rejected.

Status vocabulary: `proposed`, `accepted`, `implementing`, `completed`,
`rejected`. Entries are never deleted. A completed item must link to its
canonical implementation and executable tests; a rejected item must retain the
rationale.

## Active forward roadmap

This small table is the working queue. The long historical index and retained
incident narratives below explain prior changes but do not set current
priority. New work enters here with one owner, one landing point, and executable
completion evidence.

| ID | Improvement | Status | Landing point |
|---|---|---|---|
| IMP-229 | Make PCB documentation navigable, executable, and graph-checked | completed | root README, `pcb-design` skill, execution graph, docs index, documentation tests |
| IMP-230 | Reduce `kicad-pcb` policy prose to terse normative rules with linked evidence | accepted | `kicad-pcb/SKILL.md`, `design-policies.md`, dated evidence pages |
| IMP-231 | Version and shrink project contract templates to structural membership and schema | accepted | `pcb-design/templates/contracts/`, contract-version migration tooling |
| IMP-232 | Split this ledger into a machine-checked active registry and archived completed narratives | accepted | `improvements.md`, generated/history archive, ledger test |
| IMP-233 | Generate the active-project catalog from STATUS/release metadata | accepted | `projects/README.md`, catalog generator and freshness test |
| IMP-234 | Add an independent firmware release stream bound to exact PCB releases | accepted | firmware release contract, staging/reopen tooling, product-lock composition |
| IMP-235 | Add an executable commission-admission compositor | accepted | commission receipt, fact-lock/architecture/sourcing gates, hold removal check |
| IMP-236 | Compose prompt-to-device releases and a product-level digital twin | accepted | exact product manifest, cross-stream replay, device bundle and system twin |
| IMP-237 | Make enclosure first-article load-path feedback explicit and reusable | completed | `pcb-enclosure` first-article reference, typed support-clearance evidence, v2 test |
| IMP-238 | Compose mixed-authority supplemental obstruction solids without overstating STEP coverage | accepted | pcb-enclosure composite subject schema, per-solid authority ceilings, collision receipts |
| IMP-239 | Distinguish intended endpoint bearing contacts from motion collisions | accepted | pcb-enclosure v2 contact-region schema, endpoint/contact verifier, known-bad motion fixtures |

## IMP-229 — executable PCB documentation and graph

- status: completed
- observed: the repository front door described a retired schematic path and
  stale tool counts; three different execution layers were all called “the
  pipeline”; the template README's claimed exact copy list omitted current
  source and enclosure authorities.
- landing point: one five-minute root quick start; a lean `pcb-design` entry;
  one catalog-derived execution graph; an indexed normative/evidence/history
  taxonomy; an executable fail-closed commissioner; and a documentation
  contract test.
- completion evidence: `tests/t1_pcb_commission.py` commissions ordinary and
  conditional projects without overwriting data and audits the exact scaffold;
  `tests/t1_pcb_documentation.py` checks runnable starts, graph/catalog equality,
  local links, DRC/resume/seal semantics, and forward terminology;
  `tests/t1_skill_progressive_disclosure.py` plus
  `skill_authority_check.py` preserve authority and selective disclosure.
- authority boundary: documentation may expose implementation but may not
  promote the disclosure router into an executor or make a release imply an
  order/physical result.

## IMP-230 — terse policy canon with separated evidence

- status: accepted
- problem: `skills/kicad-pcb/references/design-policies.md` carries normative
  rows and extensive incident prose in the same very long lines, while the
  owning skill duplicates parts of both.
- intended landing point: retain each stable policy ID and concise predicate in
  the canon; move measured incidents, derivations, and dated examples to linked
  evidence documents; slim the skill to invariants and selective routing.
- completion evidence required: every policy ID remains uniquely owned and
  reachable; known-bad gate fixtures remain green; no procedure has two live
  authorities; fresh-user retrieval uses fewer documents without losing a
  required gate.

## IMP-231 — versioned structural project contracts

- status: accepted
- problem: copied contract prose has diverged across active projects, turning
  generic procedure and incident history into many competing live texts.
- intended landing point: contracts retain allowed artifacts, mutability,
  schema version, and runnable validation; generic procedure moves to the
  owning skill; projects declare a contract version and only local deltas.
- completion evidence required: a migration tool reports exact versions and
  deltas, every active artifact remains governed, sealed release contracts stay
  byte-immutable, and template/commission tests reject drift.

## IMP-232 — active improvement registry

- status: accepted
- problem: the retained ledger has missing index entries and incompatible
  status spellings, so an operator cannot reliably distinguish current work
  from completed history.
- intended landing point: keep a compact, schema-checked active registry at
  this path and move completed narrative bodies to a generated or explicitly
  historical archive with stable backlinks.
- completion evidence required: exact ID census, closed status vocabulary,
  index/body equality, owner and completion-evidence fields, and zero loss of
  historical entries.

## IMP-233 — generated active-project catalog

- status: accepted
- problem: most active boards have a STATUS beacon but no consistent root
  landing page, and the repository README cannot safely hand-maintain fleet
  status.
- intended landing point: generate `projects/README.md` from governed project
  identity, `01_docs/STATUS.md`, and release metadata; keep it navigation-only.
- completion evidence required: every active project appears exactly once,
  archived projects never appear, stale/missing status is explicit, and a
  freshness test rejects a hand-edited catalog.

## IMP-234 — firmware release stream

- status: accepted
- problem: firmware is presently a requested/forbidden handoff in the PCB
  capability profile, but the repository has no immutable firmware release
  stream, replay contract, or exact PCB-parent binding. Documentation must not
  describe that future policy as a current capability.
- intended landing point: an independent firmware artifact identity and SemVer
  stream whose manifest binds one exact immutable PCB release, with no PCB
  reseal for firmware-only changes; add an optional product lock that composes
  exact PCB, firmware, and enclosure identities.
- completion evidence required: staging and independent reopen tools; wrong or
  mutated PCB-parent fixtures; firmware-only update proving the PCB tree and
  release identity unchanged; exact product-lock mismatch tests; and explicit
  separation between firmware release and device update/first-article claims.

## IMP-235 — executable commission admission

- status: accepted
- problem: the commissioner can safely create a held scaffold, but no single
  executable currently validates the agreed brief, closed fact locks,
  architecture, applicability, sourced parts, and adopted source schemas to
  produce the lifecycle's `commissioned_brief` evidence. Manual hold removal is
  intentionally not a gate.
- intended landing point: one fail-closed compositor that reopens the exact
  brief/profile/source subjects, invokes the existing owning checks, emits a
  typed commission receipt, and permits hold removal only against that receipt.
- completion evidence required: incomplete fact locks, unchanged schema
  examples, missing/ambiguous applicability, unsourced parts, stale receipt,
  transient input mutation, and premature hold-removal known-bads; a clean-room
  ordinary-board fixture must reach the first green boundary without copper.

## IMP-236 — prompt-to-device product composition and digital twin

- status: accepted
- problem: PCB fabrication, enclosure, board-level JLC twin, and physical
  evidence currently have separate identities and readiness claims. There is
  no single replayable device identity that starts at the exact user brief and
  composes those outputs with a future firmware release or behavioral model.
- intended landing point: add an exact product manifest that binds the source
  brief, PCB release, optional enclosure release, future firmware release, and
  an executable product-level digital twin without forcing unchanged streams
  to be resealed. Export one user-facing device bundle while retaining each
  domain's independent status and evidence authority.
- completion evidence required: a clean prompt-to-device fixture reopens its
  schematic, fab package, renders, STEP, and enclosure meshes from the product
  bundle; wrong-parent and mutated-stream fixtures fail; omitted optional
  firmware/twin scopes remain visibly `INCOMPLETE`; and no component scope can
  inflate the composed device's physical or production readiness.

## IMP-237 — enclosure first-article load-path feedback

- status: completed
- observed: final-pose collision and board drop-in checks did not state whether
  a printed PCB actually bears on every intended boss or instead rests on an
  edge connector, solder tail, wall, panel, or case-closure post.
- landing point: `skills/pcb-enclosure/references/first-article-iteration.md`,
  the built-in `board_support_clearance` physical-test type, template guidance,
  and the v2 acceptance test.
- completion evidence: `tests/t1_pcb_enclosure_v2.py` accepts the typed test
  while the existing unknown-type canary still rejects misspellings; the
  reference also preserves independent fasteners, whole-body motion,
  authority, fit coupon, selector, scoped-status, and replay lessons.
- authority boundary: this is physical load-path evidence, not a substitute
  for exact collision, dimensional authority, or thermal qualification.

## IMP-238 — mixed-authority supplemental obstruction composition

- status: accepted
- problem: schema v1 binds one sealed STEP for collision, while some immutable
  releases contain useful exact solids plus missing bodies for which only
  conservative footprint-, dossier-, or measured bounds exist. Replacing the
  STEP with a mixed candidate launders partial authority; checking only present
  STEP solids is non-authoritative.
- intended landing point: a schema-v2 composite obstruction subject whose
  solids each bind exact provenance, transform, authority grade, excluded
  claims, and affected scope ceiling; collision receipts must preserve that
  census and reject omission.
- completion evidence required: exact+candidate mixed fixtures, missing-solid
  and transform mutations, per-scope ceiling tests, release-root replay, and a
  known-bad proving a partial sealed-STEP collision cannot produce CAD-ready
  status.

## IMP-239 — contact-aware enclosure motion verification

- status: accepted
- problem: a whole-part linear sweep treats the complete destination assembly
  as one obstacle census. A strictly positive minimum clearance is impossible
  when the intended endpoint contains legitimate PCB-to-boss or lid-to-post
  bearing contact, while reducing the whole operation to zero does not express
  the required positive clearance from every non-bearing feature.
- intended landing point: extend schema v2 clearance cases with exact,
  feature-bound contact regions that name the moving and obstacle faces,
  permit contact only at the terminal pose, bind a tolerance/load-path role,
  and retain a separate positive minimum for every other obstacle feature.
- completion evidence required: PCB seating and lid-post bearing clean fixtures;
  early-contact, wrong-face, excessive-gap, penetration, missing-contact, and
  non-bearing-clearance known-bads; exact collision receipts must retain both
  the allowed-contact census and the independently graded swept free space.

## Index

| ID | Improvement | Status | Discovered |
|---|---|---|---|
| IMP-001 | Validate rule/config schemas before expensive TSX generation | implementing | USB Hub 3S v4, Stage 2 schematic |
| IMP-002 | Require early and exact rendered-schematic readability gates | implementing | USB Hub 3S v4, Stages 2 and 5 schematic |
| IMP-003 | Resolve every frozen footprint/library alias before board generation | proposed | USB Hub 3S v4, Stage 3 placement |
| IMP-004 | Emit a directional pad-side and critical-adjacency report before placement freeze | proposed | USB Hub 3S v4, Stage 3 placement |
| IMP-005 | Replay configured power/sense taps in the full rebuild driver | completed | USB Hub 3S v4, Stage 4 routing |
| IMP-006 | Make hole-to-copper screening tier-aware for every via emitter | completed | USB Hub 3S v4, Stage 4 routing |
| IMP-007 | Emit parity-safe real fabrication primitives for thermal via-in-pad | completed | USB Hub 3S v4, Stage 4 pre-route DRC |
| IMP-008 | Bind layout provenance to generator, footprint-library and tool inputs | proposed | USB Hub 3S v4, Stage 4 regeneration |
| IMP-009 | Refuse to promote a route race when every candidate is dirty | completed | USB Hub 3S v4, Stage 4 routing |
| IMP-010 | Require a fresh-reload, post-fill connectivity gate | completed | USB Hub 3S v4, Stage 4 full DRC |
| IMP-011 | Reject self-intersecting zone and keepout polygons before board generation | completed | USB Hub 3S v4, Stage 4 fill diagnosis |
| IMP-012 | Use the KiCad 10 layer-aware via-width API | completed | USB Hub 3S v4, Stage 4 routing |
| IMP-013 | Bound every quiet external producer with heartbeat and timeout | completed | USB Hub 3S v4, Stage 4 replay |
| IMP-014 | Keep verbose foreign-producer diagnostics out of the progress channel | proposed | USB Hub 3S v4, Stage 4 replay |
| IMP-015 | Bind topology reviews to a stable electrical netlist projection | implementing | USB Hub 3S v4, Stage 4 replay |
| IMP-016 | Exclude orchestration-only fields from the adopted-design-rules digest | completed | USB Hub 3S v4, Stages 4 and 8 replay |
| IMP-017 | Require RF review provenance only when `rf.enabled` is true | completed | USB Hub 3S v4, Stage 5 recovery audit |
| IMP-018 | Make effective-capacitance evidence a machine-readable schematic gate | completed | USB Hub 3S v4, Stage 5 topology review |
| IMP-019 | Separate fuse-holder identity from exact fuse-element coordination | proposed | USB Hub 3S v4, Stage 5 topology review |
| IMP-020 | Prefer functional schematic partitioning and pin grouping over broad absolute placement | implementing | USB Hub 3S v4, Stage 5 schematic repair |
| IMP-021 | Machine-check aggregate fault/current-limit envelopes | implementing | USB Hub 3S v4, Stage 5 topology review |
| IMP-022 | Validate authored board net/pin references against the exact netlist before human review | proposed | USB Hub 3S v4, Stage 5 schematic checkpoint |
| IMP-023 | Pin and provenance-bind TSX producer dependencies | implementing | USB Hub 3S v4, Stage 5 schematic rebuild |
| IMP-024 | Give the regression-suite runner per-suite heartbeats and hard deadlines | implementing | USB Hub 3S v4, Stage 5 verification |
| IMP-025 | Treat a mixed output bank and fitted CFF as one control-loop decision | proposed | USB Hub 3S v4, Stage 5 topology review |
| IMP-026 | Time-box fresh-context reviews and convert unresolved checks into findings | implementing | USB Hub 3S v4, Stage 5 topology re-review |
| IMP-027 | Lint standards-defined terminology and evidence identifiers before review | proposed | USB Hub 3S v4, Stage 5 topology re-review |
| IMP-028 | Validate part layout-precedent closure before hash-bound schematic review | completed | USB Hub 3S v4, Stage 6 placement entry |
| IMP-029 | Prefetch and provenance-bind JLC catalog models before A-RENDER | proposed | USB Hub 3S v4, Stage 6 placement review |
| IMP-030 | Make thermal-via transforms ownership-safe and run exact placement DRC | implementing | USB Hub 3S v4, Stage 6 placement review |
| IMP-031 | Add a published-legibility silk class for operational markings | proposed | USB Hub 3S v4, Stage 6 placement render review |
| IMP-032 | Promote the reviewed schematic at its stage boundary | completed | USB Hub 3S v4, Stage 6 placement replay |
| IMP-033 | Require machine-checked evidence for per-reference P-OUT exceptions | proposed | USB Hub 3S v4, Stage 6 edge-connector review |
| IMP-034 | Validate deterministic route copper against exact placement before review | proposed | USB Hub 3S v4, Stage 7 route preparation |
| IMP-035 | Prove pour-service coverage for every net excluded from routing | proposed | USB Hub 3S v4, Stage 7 authoritative DRC |
| IMP-036 | Let layout sealing resume an exact reviewed schematic checkpoint | completed | USB Hub 3S v4, Stage 8 layout seal |
| IMP-037 | Keep track-free review checks typed to the pre-route artifact | completed | USB Hub 3S v4, Stage 8 layout seal |
| IMP-038 | Make ampacity audit a canonical stage gate | completed | USB Hub 3S v4, routed review |
| IMP-039 | Select via treatment per process family, not board-wide | completed | USB Hub 3S v4, manufacturing review |
| IMP-040 | Validate promoted-route compatibility before placement review | completed | USB Hub 3S v4, corrected-process replay |
| IMP-041 | Grade series-transition via ampacity non-vacuously | completed | USB Hub 3S v4, routed review |
| IMP-042 | Bind fresh pin review to an exact local datasheet digest | completed | USB Hub 3S v4, routed pin review |
| IMP-043 | Propagate typical-only and accessory-qualified bounds into release blockers | implementing | USB Hub 3S v4, routed topology review |
| IMP-044 | Prove rendered symbol terminals coincide with authoritative trace endpoints | completed | USB Hub 3S v4, schematic readability re-review |
| IMP-045 | Run repository schema and bound-provenance ratchets before producer or reviewer spend | completed | USB Hub 3S v4, schematic regression replay |
| IMP-046 | Preflight rendered reference/value occlusion before human review | proposed | USB Hub 3S v4, schematic readability review |
| IMP-047 | Give IR-budget terms non-overlapping measurement endpoints | implementing | USB Hub 3S v4, Type-C topology review |
| IMP-048 | Compare visible schematic paths with authoritative electrical nets | proposed | USB Hub 3S v4, schematic readability review |
| IMP-049 | Bound independent-review briefs and enforce closure deadlines | implementing | USB Hub 3S v4, exact placement review |
| IMP-050 | Prove fresh generated outputs instead of trusting exit zero | implementing | USB Hub 3S v4, routed-review export |
| IMP-051 | Give long external stages progress and bounded retry budgets | implementing | USB Hub 3S v4, JLC digital-twin fetch |
| IMP-052 | Preflight mutable catalog clients and distinguish compatibility from throttling | implementing | USB Hub 3S v4, JLC digital-twin fetch |
| IMP-053 | Prefer explicit catalog facts over MPN-shape heuristics | completed | USB Hub 3S v4, C23 source substitution |
| IMP-054 | Persist the final adjudicated state in generated reports | completed | USB Hub 3S v4, JLC digital twin |
| IMP-055 | Register exact 3D model attachment geometry before placement freeze | implementing | USB Hub 3S v4 and Pluto RX2 8-way v5 twins |
| IMP-056 | Separate automated and manual population denominators | completed | USB Hub 3S v4, release audit |
| IMP-057 | Validate relocated release archives in their own dependency context | implementing | USB Hub 3S v4, release staging |
| IMP-058 | Treat multi-format evidence as one atomic result | proposed | USB Hub 3S v4, release staging |
| IMP-059 | Preflight publication review identity before immutable seal | implementing | USB Hub 3S v4, publication gate |
| IMP-060 | Replay a release's declared freshness mode at publication | completed | USB Hub 3S v4, docs-only publication correction |
| IMP-061 | Close exact-code manufacturing readiness before part freeze | partially implemented | USB Hub 3S v4, nine-hour pipeline retrospective |
| IMP-062 | Provide one transactional primitive for generated artifact bundles | implementing | USB Hub 3S v4, nine-hour pipeline retrospective |
| IMP-063 | Rehearse the complete release and publication-internal contract before seal | partially implemented | USB Hub 3S v4, nine-hour pipeline retrospective |
| IMP-064 | Pair early warning gates with late authoritative rechecks | partially implemented | USB Hub 3S v4, nine-hour pipeline retrospective |
| IMP-065 | Measure pipeline critical path by work class and order cheap gates first | implementing | USB Hub 3S v4, nine-hour pipeline retrospective |
| IMP-066 | Confirm broad-phase geometry findings with native transformed polygons | completed | Pluto RX2 8-way legacy canary replay |
| IMP-067 | Prevent executable example values from entering new-project scaffolds | proposed | Pluto RX2 8-way v5 commission |
| IMP-068 | Coordinate protection before freezing downstream voltage ratings | proposed | Pluto RX2 8-way v5 exact-parts stage |
| IMP-069 | Derive stage readiness from canonical gate receipts | implemented; project adoption opt-in | Pluto RX2 8-way v5 pre-schematic audit |
| IMP-070 | Mechanically scope clean-room filesystem discovery | proposed | Pluto RX2 8-way v5 clean-room audit |
| IMP-071 | Derive observable timing from executable state schedules | implementing | Pluto RX2 8-way v5 control-protocol audit |
| IMP-072 | Classify committed binary evidence in the canonical scaffold | proposed | Pluto RX2 8-way v5 checkpoint commit |
| IMP-073 | Grade human symbol pin functions, including unused pins | proposed | Pluto RX2 8-way v5 schematic readability review |
| IMP-074 | Type ADR gate applicability instead of inferring it from prose | proposed | Pluto RX2 8-way v5 schematic gate |
| IMP-075 | Bind mechanical dimensions to exact document identity and feature role | proposed | Pluto RX2 8-way v5 connector review |
| IMP-076 | Reconcile exact package geometry and logical pin identity in the first-board preflight | proposed | Pluto RX2 8-way v5 placement grind |
| IMP-077 | Reconcile footprint and symbol metadata before schematic-parity DRC | proposed | Pluto RX2 8-way v5 keyed-SWD placement |
| IMP-078 | Run the source-resolvable tier/routing preflight before schematic and placement spend | proposed | Pluto RX2 8-way v5 keyed-SWD placement |
| IMP-079 | Derive compact floorplans from topology and operational connector envelopes before placement freeze | proposed | Pluto RX2 8-way v5 compact placement |
| IMP-080 | Emit and measure RF fences from routed centrelines, not a rectangular lattice declaration | completed | Pluto RX2 8-way v5 route preparation |
| IMP-081 | Seed route-prep UUID generation so identical source yields byte-identical r0 | completed | Pluto RX2 8-way v5 route preparation |
| IMP-082 | Require executable budgets for datasheet `short`/`close` layout obligations before placement review | proposed | Pluto RX2 8-way v5 pre-route placement renewal |
| IMP-083 | Make no-via-in-pad intent executable at every routing wave | completed | Pluto RX2 8-way v5 first control/power route |
| IMP-084 | Make geometry admission consume pad-local copper and mask rules | completed | Pluto RX2 8-way v5 first post-stitch DRC |
| IMP-085 | Normalize overlap-only track/via joints before deleting barrels | completed | Pluto RX2 8-way v5 route cleanup |
| IMP-086 | Run external mating-fact provenance before PCB generation | proposed | Pluto RX2 8-way v5 post-stitch gate |
| IMP-087 | Grade rerunnable density gates against realized saved geometry | completed | Pluto RX2 8-way v5 RF-fence rerun |
| IMP-088 | Seed deterministic identities across import and stitch, not only route prep | proposed | Pluto RX2 8-way v5 layout-seal entry |
| IMP-089 | Treat same-net via-in-pad as a fabrication process, not a DRC clearance | completed | Pluto RX2 8-way v5 final layout red team |
| IMP-090 | Bind review freshness to declared stage dependencies, not monolithic source bags | proposed | Pluto RX2 8-way v5 corrected layout seal |
| IMP-091 | Freeze executable assembly-process ownership before placement export | proposed | Pluto RX2 8-way v5 layout-seal entry |
| IMP-092 | Make provenance source discovery honor declared source boundaries and ignore policy | proposed | Pluto RX2 8-way v5 layout seal |
| IMP-093 | Compare repeated-pad catalog lands as geometry, not merged labels | implementing | Pluto RX2 8-way v5 final JLC twin |
| IMP-094 | Bind review contracts to the exporter artifact index | partially implemented | Pluto RX2 8-way v5 fabrication entry |
| IMP-095 | Dispatch exact-artifact reviews from a machine-written envelope | proposed | Pluto RX2 8-way v5 RF fabrication review |
| IMP-096 | Derive release PDF pages from populated sides and document purpose | proposed | Pluto RX2 8-way v5 release-asset export |
| IMP-097 | Preserve schematic-sheet coordinate domains in native conversion | completed | Pluto RX2 8-way v5 schematic archive |
| IMP-098 | Make clean replay produce every ignored review prerequisite it consumes | proposed | Pluto RX2 8-way v5 clean replay |
| IMP-099 | Seed every late KiCad writer, not only board and route preparation | completed | Pluto RX2 8-way v5 release reproducibility |
| IMP-100 | Validate assembly semantics before release staging | proposed | Pluto RX2 8-way v5 release staging |
| IMP-101 | Make local PCB ECO routing preserve the validated copper baseline | proposed | Pluto RX2 8-way v5 J12 bench-power renewal |
| IMP-102 | Make RF expertise a conditional, bounded evidence module | completed | Pluto RX2 8-way v5 RF module audit |
| IMP-103 | Model protected distribution rails explicitly | completed | Raspberry Pi USB port switch power preflight |
| IMP-104 | Retain per-row JLC evidence in mixed-source BOMs | completed | Raspberry Pi USB port switch sourcing |
| IMP-105 | Separate early high-speed authority from placed route primitives | completed | Raspberry Pi USB 3 source preflight |
| IMP-106 | Refactor PCB skills around progressive disclosure without moving execution authority | completed | Cross-board skill/pipeline review |
| IMP-107 | Make footprint side a first-class floorplan property | completed | USB-controlled debug hub placement |
| IMP-108 | Scope physical adjacency budgets to the electrical path they protect | completed | USB-controlled debug hub ESD placement |
| IMP-109 | Preserve every actionable finding in durable gate reports | completed | USB-controlled debug hub placement iteration |
| IMP-110 | Measure every disconnected body island in native-model registration coupons | completed | USB-controlled debug hub connector registration |
| IMP-111 | Canonicalize producer-private repeated-pad identities before physical pin comparison | completed | USB-controlled debug hub pin-map preflight |
| IMP-112 | Give headless rendering the same model environment as body coverage | completed | USB-controlled debug hub placement render |
| IMP-113 | Exercise refactored skill authority with a real release-target canary | completed | USB-controlled debug hub canonical schematic rebuild |
| IMP-114 | Close aggregate fault, effective-capacitance and device-specific startup envelopes before placement | completed | USB-controlled debug hub independent pre-route review |
| IMP-115 | Scope executable part authority to the live design | proposed | USB-controlled debug hub placement entry |
| IMP-116 | Make generated annotation and fabrication text follow footprint side | completed | USB-controlled debug hub placement DRC |
| IMP-117 | Compare catalog and board lands in an unflipped footprint frame | completed | USB-controlled debug hub JLC twin |
| IMP-118 | Separate presentation rendering from shadow-free pixel evidence | implementing | USB-controlled debug hub A-RENDER |
| IMP-119 | Resolve part dossiers by declared identity, not raw MPN path spelling | proposed | USB-controlled debug hub pre-route pin review |
| IMP-120 | Make route-wave pauses authenticated and non-promotable | completed | USB-controlled debug hub first USB route wave |
| IMP-121 | Grade differential-pair fanout against pair gap, not foreign-net clearance | completed | USB-controlled debug hub first USB route wave |
| IMP-122 | Grade realised functional pad-bank direction before routing | completed | USB-controlled debug hub USB routing backtrack |
| IMP-123 | Preflight differential endpoint topology and tangent compatibility | partially implemented | USB-controlled debug hub USB routing retry |
| IMP-124 | Classify high-speed protection parts as shunt or series before placement | implemented | USB-controlled debug hub deterministic USB-bottom routing |
| IMP-179 | Require an absolute public-stock surplus before footprint freeze | completed | USB-controlled debug hub 2A v1 pre-layout sourcing |
| IMP-180 | Reject shadowed schematic-placement authority before TSX generation | proposed | USB-controlled debug hub 2A v1 power-sheet readability |
| IMP-181 | Compile one canonical critical-signal contract for routing and verification | proposed | USB-controlled debug hub 2A v1 release review |
| IMP-182 | Make required-check applicability and coverage fail closed | proposed | USB-controlled debug hub 2A v1 release review |
| IMP-183 | Reconstruct release evidence against the complete staged archive | proposed | USB-controlled debug hub 2A v1 release review |
| IMP-184 | Replace global DRC suppressions with scoped, measured exceptions | proposed | USB-controlled debug hub 2A v1 release review |
| IMP-185 | Ratchet ERC warnings by category and stable object identity | proposed | USB-controlled debug hub 2A v1 release review |
| IMP-186 | Generate review claims and scoreboards from admitted receipts | proposed | USB-controlled debug hub 2A v1 release review |
| IMP-187 | Require known-bad promotion-boundary canaries for every fail-closed gate | proposed | USB-controlled debug hub 2A v1 release review |
| IMP-188 | Treat native post-stitch DRC as an independent mandatory acceptance predicate | proposed | USB-controlled debug hub 2A v1 route repair |
| IMP-189 | Type route-seed and manufacturing-board artifacts and reject role confusion | proposed | USB-controlled debug hub 2A v1 route repair |
| IMP-190 | Preflight filled-zone islands and inner-plane obstacles before stitching | proposed | USB-controlled debug hub 2A v1 route repair |
| IMP-191 | Prefer semantic connector approval identities over nondeterministic render bytes | proposed | USB-controlled debug hub 2A v1 route repair |
| IMP-125 | Make generated evidence bundles relocatable across atomic promotion | completed | USB-controlled debug hub evidence promotion |
| IMP-126 | Grade connector mating direction against the board edge | completed | USB-controlled debug hub connector review |
| IMP-127 | Bind package-local rule areas to realised footprints | completed | USB-controlled debug hub connector review |
| IMP-128 | Authenticate camera semantics in directional render evidence | completed | USB-controlled debug hub connector review |
| IMP-129 | Separate geometric render resolution from ray-tracing quality | proposed | USB-controlled debug hub connector review |
| IMP-130 | Grade the signed mounting side independently of XY registration | implementing | USB-controlled debug hub connector review |
| IMP-131 | Derive intermediate power floors in their own current domain | implementing | USB-controlled debug hub schematic renewal |
| IMP-132 | Make schematic-review hashes phase-semantic | proposed | USB-controlled debug hub schematic renewal |
| IMP-133 | Grade deterministic critical-copper length before review and routing | proposed | USB-controlled debug hub route preparation |
| IMP-134 | Replay downstream corridor capacity after deterministic route growth | proposed | USB-controlled debug hub route preparation |
| IMP-135 | Authenticate a reviewed critical route as a reusable wave prefix | implementing | USB-controlled debug hub route recovery |
| IMP-136 | Classify wide multi-pad power distribution before autorouting | completed | USB-controlled debug hub route recovery |
| IMP-137 | Make incomplete structured router results fail the wave directly | completed | USB-controlled debug hub route recovery |
| IMP-138 | Measure plated-pad layer transitions as real conductor length | implementing | USB-controlled debug hub route review |
| IMP-139 | Order route waves by geometric flexibility and physical ownership | implementing | USB-controlled debug hub route recovery |
| IMP-140 | Bound routing exploration by stagnation and novelty | completed | USB-controlled debug hub routing retrospective |
| IMP-141 | Grade every route candidate in an authoritative immutable workspace | completed | USB-controlled debug hub routing retrospective |
| IMP-142 | Make first-article power-up a staged, measurable contract | completed | USB Hub 3S v3 bring-up failure |
| IMP-143 | Make route experiments transactional and retention-bounded | completed | USB-controlled debug hub routing retrospective |
| IMP-144 | Keep one canonical pause-state authority | completed | USB-controlled debug hub routing retrospective |
| IMP-145 | Schedule user interaction only at high-leverage physical boundaries | implementing | USB-controlled debug hub and USB Hub 3S v3 reviews |
| IMP-146 | Make copper-layer roles and low-speed escape eligibility executable | partially implemented | USB-controlled debug hub final control routing |
| IMP-147 | Route against pairwise authoritative clearances, not one global clearance | proposed | USB-controlled debug hub final control routing |
| IMP-148 | Prove placement and complete routability together before floorplan promotion | partially implemented | USB-controlled debug hub VBUS-divider relocation |
| IMP-149 | Author deterministic geometry with explicit numeric margin above hard floors | proposed | USB-controlled debug hub sense routing |
| IMP-150 | Isolate repeated KiCad board mutations per candidate process | proposed | USB-controlled debug hub placement scan |
| IMP-151 | Require complete displaced-net closure and source rebase before ECO promotion | proposed | USB-controlled debug hub VBUS-divider relocation |
| IMP-152 | Make generated-copper cleanup ownership-scoped and width-aware | partially implemented | USB-controlled debug hub final stitch replay |
| IMP-153 | Preflight stitching sites against final filled geometry | proposed | USB-controlled debug hub final ground stitching |
| IMP-154 | Distinguish byte provenance from semantic 3D-model identity | proposed | USB-controlled debug hub model registration |
| IMP-155 | Generate the release manifest skeleton before release gates | partially implemented | USB-controlled debug hub release staging |
| IMP-156 | Use multiscale render evidence for small bodies | proposed | USB-controlled debug hub JLC twin overlay |
| IMP-157 | Reject same-net branches, cycles, and duplicate copper before route promotion | implemented | USB-controlled debug hub Port 4 release audit |
| IMP-158 | Grade every realized via against the actual stackup aspect-ratio ceiling | implemented | USB-controlled debug hub topology red team |
| IMP-159 | Make route replay regenerate or select an immutable segment-free base | proposed | USB-controlled debug hub route repair replay |
| IMP-160 | Grade projected reference-plane interruptions on every declared adjacent plane | implemented | USB-controlled debug hub final electrical review |
| IMP-161 | Separate catalog stock, PCBA availability and final allocation | implemented | USB-controlled debug hub sourcing backtrack |
| IMP-162 | Grade MOQ exposure by gross surplus cost and cash outlay before layout | implemented | USB-controlled debug hub JLC preorder review |

## IMP-001 — pre-build rule/config schema validation

- status: completed
- observed: `projects/usb-hub-3s-v4/01_docs/journal/03_schematic.md`,
  2026-08-11 08:34 entry
- evidence: A malformed `label_survival` row was knowable from YAML alone, but
  was not rejected until after an approximately 25-second TSX build/render.
  Existing `tsx_preflight.py` runs before generation but currently grades
  alphanumeric pad mapping, not all adopted rule schemas.
- additional evidence: the Stage 4 full replay completed routing and DRC before
  `project_state.py` found that a gate marked `pass` had no evidence list. The
  findings ledger is source-only and could have failed before TSX generation.
- intended landing point: a cheap canonical pre-build schema gate, invoked by
  both PCB rebuild templates before `build_provenance.py stamp` and before any
  `tsci build`. It should validate every rule block whose schema does not depend
  on generated circuit/netlist/board bytes, including `label_survival`.
- completion evidence required: clean and known-bad executable fixtures; both
  canonical rebuild templates prove the gate precedes TSX generation; the USB
  Hub v4 rule set passes; the original malformed label-survival shape fails
  without invoking the producer.
- implementation progress: the full-build template now runs
  `net_label_survival.py --schema-only` and the source-only portion of
  `early_design_check.py` before the provenance stamp and `tsci build`;
  executable ordering and malformed-label fixtures pass in
  `tests/t1_net_label_survival.py` and `tests/t1_rebuild_templates.py`. The
  broader all-rule schema inventory and source-only findings-ledger validation
  remain outstanding, so this item is not complete.
- follow-up evidence: Pluto RX2 8-way v5 parsed 25/25 YAML files and passed the
  selected package, topology, netclass and surge checks, yet four canonical
  readers disagreed at the same pre-schematic boundary on 2026-08-13:
  `electrical_invariants.py` rejected the prose-only invariant shape;
  `rf_contract_check.py` rejected `rf.ports[0]` without a `nets` list;
  `assembly_coverage.py --emit-manifest-line` raised an `AttributeError` on
  scalar `not_assembled` rows instead of issuing a bounded schema failure; and
  `net_label_survival.py --schema-only` reported PASS while interpreting zero
  of the thirteen intended pin-map rows. Parse success and a zero-row schema
  pass are both M-COVER failures when authored declarations were expected.
- completion evidence extension: the canonical pre-build command must invoke
  every source-readable rule-family reader, require an expected non-zero
  denominator when that family is authored, convert malformed input to a
  concise failure rather than a traceback, and refuse TSX when any family is
  ungraded. The four v5 shapes above become executable known-bads.
- implementation progress: the electrical-invariant reader now has an
  explicit source-only mode and configurable non-zero minimum; label survival
  rejects unknown keys and empty pin-map declarations; assembly projection
  shape failures are bounded diagnostics rather than tracebacks; and the RF
  reader accepts an explicitly evidenced `pending_solver` cross-section before
  PCB work while refusing it at PCB/fab review. The canonical full-build
  template invokes the new source checks before TSX. Focused clean/known-bad
  regressions for these readers and control timing pass 108 tests. Assembly,
  control-protocol and RF now have canonical key/reader tables; the repository
  ratchet reports 604/604 declared keys, 508 proven, zero orphan and zero
  unread. `mates.yaml`, `twin_adjudications.yaml`, a complete stage registry
  and preflight of the findings ledger remain open.
- history:
  - 2026-08-11 — proposed and promoted from the schematic journal.
  - 2026-08-11 — implementation started with pre-producer label-survival and
    electrical schema gates; V4 passed before its 9.1-second TSX invocation.
  - 2026-08-13 — v5's four source-reader failures were converted into bounded,
    non-vacuous pre-TSX checks and executable regression fixtures.

## IMP-003 — pre-generation footprint resolution

- status: proposed
- observed: `projects/usb-hub-3s-v4/01_docs/journal/placement.md`,
  2026-08-11 Stage 3 closeout
- evidence: The first board-generation attempt stopped immediately because the
  frozen schematic named `Package_TO_SOT_SMD:SOT-9X3`, while the installed
  KiCad library now names the exact TI land `Texas_DRT-3`. The local project
  alias was then vendored and generation completed. The failure was cheap and
  loud, but the mismatch was knowable before starting the board producer.
- intended landing point: extend the pre-build/pre-board schema gate so every
  manifest footprint resolves through the project `fp-lib-table`, including
  frozen aliases, before invoking either TSX or PCB generation. The resolver
  must report the unresolved refdes, requested library identifier, and the
  exact library search order.
- completion evidence required: fixtures for a missing library, missing
  footprint, stale renamed alias and valid project-local alias; the canonical
  pipeline proves the resolver runs before the producer; USB Hub v4 passes
  without relying on the generator to discover the problem.
- history: 2026-08-11 — proposed after the Stage 3 first-generation stop.

## IMP-004 — directional pad-side and adjacency report

- status: proposed
- observed: `projects/usb-hub-3s-v4/01_docs/journal/placement.md`,
  2026-08-11 Stage 3 closeout
- evidence: Collision, outline, capacity and pad-separation gates all accepted
  the first legal placement. A direct physical-pad report then showed the two
  power modules rotated with VIN and VOUT on the opposite sides from the
  authored comment, and the human render exposed BOOT/RT/feedback parts that
  were legally separated but electrically too remote. The corrected board
  measures U1 BOOT 2.70 mm, RT 1.99 mm and nearest FB 2.06 mm; U2 VIN bypasses
  are 1.60 mm and RT is 2.07 mm from their actual lands.
- intended landing point: before placement review, emit a small report from
  the exact board listing the global coordinates and side/order of named
  directional pads plus the minimum pad-to-pad distances for every structured
  `layout:` adjacency obligation. Comments such as “VIN west” must be checked
  against board bytes, never accepted as evidence.
- completion evidence required: rotated/mirrored and far-but-nonoverlapping
  known-bad fixtures; a clean report for USB Hub v4; the canonical placement
  stage runs it before render review and before routing.
- history: 2026-08-11 — proposed after two defects escaped geometry-only gates.

## IMP-002 — early and exact rendered-schematic readability gates

- status: implementing
- observed: `projects/usb-hub-3s-v4/01_docs/journal/03_schematic.md`, the Stage
  5 exact-replay backtrack, and the rejected USB Hub v4 schematic-render
  review.
- evidence: Connectivity, parity, ERC, freshness and source-level section
  metadata all passed, but an independent review of the delivered PDF found
  approximately 2.1--2.5 pt native text, weak functional grouping, no visible
  block headings or important active-part identities, excessive label hopping
  through critical circuits, unexplained intentional NCs, and poor page use.
  The source described sections, but the rendered artifact did not communicate
  them. Because the first explicit picture review occurred after detailed
  electrical and PCB work, a cheap presentation defect caused a late
  backtrack.
- required process:
  1. Render a small "first picture" as soon as the functional schematic
     skeleton exists. Require a human-readable left-to-right flow, visible
     functional headings, local critical support circuits, explained NCs and
     useful page occupancy before detailed sourcing or PCB work begins.
  2. At schematic freeze, repeat the review against the exact delivered PDF
     and bind the closed verdict to the PDF SHA-256, canonical electrical
     netlist, adopted design rules and exact parts manifest.
  3. Review the artifact itself at normal viewing size; source metadata and a
     zoom-readable drawing are not substitutes.
- implement now: keep the hash-bound `schematic_render` review as a mandatory
  schematic-phase prerequisite to placement, repair USB Hub v4 until that
  independent review is SOUND, and make the first-picture checkpoint explicit
  in the PCB design/review contract. This is required now because the current
  v4 artifact has already failed the gate; deferring it would knowingly carry
  an unreadable schematic into release.
- implement later: add deterministic, cheap render heuristics for minimum text
  size, drawing bounds/page occupancy, required headings and identities, and
  unexplained NCs; add a reusable skeleton-render template and cached stage
  telemetry. These checks reduce review load but do not replace the human
  verdict, and they do not need to block completion of the present electrical
  design once its actual PDF is readable.
- completion evidence required: canonical review schema and checker; the PCB
  design instructions and `08_reviews` contract name both checkpoints; clean
  and stale/missing/defective fixtures; a future project proves the
  first-picture gate runs before detailed generation; and the USB Hub v4 PDF
  receives an explicit SOUND verdict bound to its exact SHA-256 and electrical
  inputs.
- partial implementation: `skills/kicad-pcb/scripts/render_schematic_pdf.mjs`
  renders each declared sheet independently from the exact Circuit JSON;
  it now applies the same leading-`N` digit convention and explicit
  `net_aliases.txt` mapping as the KiCad bridge to display canonical net names
  without mutating Circuit JSON. USB Hub v4's exact review also proved that
  polarity, user-fitted safety consumables and manufacturer-required open-pin
  dispositions are part of schematic readability, not merely BOM/dossier
  facts; the repaired source renders all three visibly. Alias behavior and
  exact-input immutability have executable coverage in
  `tests/t1_schematic_render.py`;
  `skills/pcb-design/scripts/pre_route_review_check.py` and the USB Hub v4
  `03_src/route.yaml` require independent topology and `schematic_render`
  reviews bound to exact schematic/electrical inputs; the PCB-design and
  `08_reviews` contracts now require the earlier first-picture checkpoint.
  `stage_checkpoint.py` plus `rebuild_all.sh
  --resume-after-schematic-review` preserve the reviewed bytes across the
  deliberate pause instead of rerunning nondeterministic TSX. Executable
  coverage is in `tests/t1_schematic_render.py`,
  `tests/t1_pre_route_review.py`, `tests/t1_stage_checkpoint.py`, and
  `tests/t1_rebuild_templates.py`.
- history:
  - 2026-08-11 — proposed and promoted from the schematic journal.
  - 2026-08-11 — expanded after the first exact-artifact review rejected USB
    Hub v4; split into a mandatory present repair/contract change and later
    automated presentation heuristics.
  - 2026-08-11 — implemented the exact multi-sheet renderer, explicit
    first-picture contract, hash-bound freeze review, and content-preserving
    review-pause resume; remains `implementing` until USB Hub v4 receives the
    exact SOUND readability verdict.
  - 2026-08-12 — the next exact-PDF review found authoring-only net aliases,
    invisible C22/C23 polarity, an unnamed user-fitted fuse element and
    unexplained module SW/VCC opens. Canonical-name rendering was repaired in
    the shared renderer/template; the board source now exposes the remaining
    assembly and intentional-open facts before a fresh review.

## IMP-005 — deterministic tap replay in the full rebuild

- status: completed
- observed: USB Hub 3S v4 Stage 4 routing preflight, 2026-08-11
- evidence: `route.yaml` configured five explicit 5VA F.Cu-to-B.Cu bonds, and
  both the project contract and `rebuild_reuse.sh` require the standard `taps`
  command between route import and stitch. The canonical `rebuild_all.sh`
  omitted that command, so a full rebuild would silently skip source-owned
  copper that an iterative rebuild correctly replayed.
- intended landing point: invoke `route_and_stitch_generic.py taps` after
  promoted-chain import and before stitch/fill in the canonical full driver;
  keep project copies aligned.
- completion evidence required: an executable template test requires
  `import < taps < stitch` in both full and reuse drivers; USB Hub v4 completes
  the same route from its source contract under the full ordering.
- implementation: `skills/pcb-design/templates/03_src/rebuild_all.sh` and the
  USB Hub v4 copy now invoke `taps` strictly between import and stitch.
  `tests/t1_rebuild_templates.py` pins the full and reuse order.
- history: 2026-08-11 — implementation started after comparing the v4 driver,
  its contract, the reuse driver and USB Hub v3; completed in Stage 4.

## IMP-006 — tier-aware hole-to-copper screening for every via emitter

- status: completed
- observed: USB Hub 3S v4 Stage 4 `tier_preflight.py`, 2026-08-11
- evidence: the board declares the JLCPCB four-layer advanced 0.25 mm
  hole-to-copper floor. Configured stitch tiers carry the correct 0.255 mm
  collision-screening value, but the generic `taps` path still calls
  `via_site_ok` with its 0.205 mm default and offers no project knob. The A*
  fallback can already inherit a matching stitch-tier value, but the preflight
  currently reports it as knobless too. An under-strict screen is caught by
  final DRC, but only after copper generation; an over-strict default can
  create a false routing wall.
- intended landing point: every via emitter resolves one effective
  `hole_to_copper` value from an explicit pin or the matching fab-tier entry,
  passes it to every site check and A* layer change, and reports that resolved
  value accurately in `tier_preflight.py`.
- completion evidence required: clean tests for taps and A* on a non-default
  hole floor, known-bad under-floor/false-wall fixtures, and zero PF-HTC
  warnings on USB Hub v4 without relying on final DRC.
- implementation: `route_and_stitch_generic.py` forwards the configured
  value through tap via-site checks and verified A* layer changes;
  `tier_preflight.py` resolves and grades both paths. Clean/non-default and
  under-floor fixtures live in `tests/t2_route_stitch.py` and
  `tests/t2_tier_preflight.py`. USB Hub v4 preflight is 0 FAIL / 0 WARN at
  0.255 mm versus the declared 0.25 mm floor.
- history: 2026-08-11 — proposed and completed during the bounded Stage 4
  preflight loop.

## IMP-007 — parity-safe fabrication primitives for thermal via-in-pad

- status: completed
- observed: USB Hub 3S v4 Stage 4 pre-route DRC, 2026-08-11
- evidence: 40 exposed-land thermal holes were represented by duplicated
  footprint PTH pads carrying KiCad's `pad_prop_heatsink` marker. They are
  electrically valid, but JLC's official via-covering guidance distinguishes
  vias from component pad holes and says via finishing does not apply to pads.
  A Gerber/fab order must not rely on the fabricator reinterpreting the
  primitive. The same cheap DRC also exposed the 0.20/0.30 mm board-floor
  contradiction before KRT ran.
- intended landing point: explicit, config-gated board-level via declarations
  resolve named footprint pads, inherit their live nets and preserve the
  library-linked footprint identity used by schematic parity. The legacy
  marker-promotion path remains supported but fails closed on an empty match.
- implementation: `generate_board_generic.py` emits 40 explicit true vias for
  U1-U6 while retaining all six library FPIDs. `tests/t1_generate_board.py`
  covers count/geometry, unknown refs and legacy empty matches. USB Hub v4's
  refill/full-severity pre-route DRC has no drill-floor or schematic-parity
  finding; its manufacturing contract still requires resin fill and copper cap.
- history: 2026-08-11 — implemented after the pre-route quick check prevented
  routing over a fabrication-primitive mismatch.

## IMP-008 — complete generated-layout provenance inputs

- status: proposed
- observed: USB Hub 3S v4 Stage 4 regeneration, 2026-08-11
- evidence: the board/review hashes bind the generated artifact and authored
  rule bytes, but a generator implementation or vendored footprint change can
  alter board bytes without appearing as a named producer input in the pending
  layout provenance record.
- intended landing point: bind the board generator, resolved footprint files,
  project library tables, KiCad version and any post-generator transformer to
  the layout provenance record, with a report explaining which input changed.
- completion evidence required: clean rebuild plus stale generator/library/tool
  fixtures that invalidate provenance before routing.
- history: 2026-08-11 — proposed during parity-safe footprint regeneration.

## IMP-009 — fail-closed route-race promotion

- status: completed
- observed: USB Hub 3S v4 Stage 4 route race, 2026-08-11
- evidence: an early race returned success and selected the least-bad candidate
  even though every candidate's cheap verdict still contained routed-net opens.
  The failure then surfaced only after import, taps, fill and full DRC.
- implementation: `_cmd_route_race` now considers only `CLEAN` candidates,
  clears any stale `FINAL` marker before a run, records an all-dirty
  `race_log.json` with `chosen: null`, and exits nonzero. Clean selection,
  all-failed and all-dirty fixtures live in `tests/t2_route_stitch.py`.
- history: 2026-08-11 — completed before rerunning USB Hub v4's route race.

## IMP-010 — fresh post-fill connectivity gate

- status: completed
- observed: USB Hub 3S v4 Stage 4 full DRC, 2026-08-11
- evidence: an in-process stitch gate reported clean while a fresh authoritative
  KiCad CLI refill found 35 unconnected items and one dangling via. Fill state,
  island healing and connectivity must cross the same serialization boundary as
  the release DRC.
- intended landing point: force save/fresh reload after fill, heal split same-net
  islands, prune stitch-created dangling copper, then gate; retain full CLI DRC
  with refill and schematic parity as the authority.
- completion evidence required: USB Hub v4 reaches fresh 0/0/0 and a fixture
  proves a stale in-memory connectivity result cannot pass.
- implementation: `route_and_stitch_generic.py` provides an unconditional
  `fresh_reload` process barrier, collision-checked `heal_islands`, and
  ownership-scoped `prune_stitch_dangling`; USB Hub v4 runs all three before
  `gate` and then independently runs KiCad CLI DRC with refill and schematic
  parity. `tests/t2_route_stitch.py` proves the fresh barrier always re-execs,
  split same-net pours heal and re-verify, a dangling emitted via is pruned,
  and an unbridgeable split is still found by the independent DRC backstop.
- history: 2026-08-11 — completed after USB Hub v4 reproduced the stale
  in-memory result and then reached serialized 0/0/0.

## IMP-011 — simple-polygon validation before generation

- status: completed
- observed: USB Hub 3S v4 Stage 4 fill diagnosis, 2026-08-11
- evidence: the authored VIN polygon crossed/overlapped itself. KiCad accepted
  the zone but filled only its downstream tail, silently omitting the protected
  input region even on the segment-free board.
- implementation: `generate_board_generic.py` rejects repeated closure points,
  zero-length edges, zero area and non-adjacent crossing/collinear-overlapping
  edges for every zone and keepout. `tests/t1_generate_board.py` carries the
  original self-intersection as a known-bad fixture.
- history: 2026-08-11 — completed while tracing the missing VIN fill.

## IMP-012 — KiCad 10 layer-aware via-width API

- status: completed
- observed: USB Hub 3S v4 Stage 4 routing, 2026-08-11
- evidence: calling the legacy no-argument via `GetWidth()` under KiCad 10
  emitted assertion noise during otherwise bounded search loops, obscuring real
  progress and making the pipeline appear stuck.
- implementation: the importer/router now obtains via width through the
  layer-aware API. Focused route/import tests run without the assertion flood.
- history: 2026-08-11 — completed during Stage 4 diagnostics.

## IMP-013 — bounded external-producer progress

- status: completed
- observed: `projects/usb-hub-3s-v4/01_docs/journal/routing.md`,
  2026-08-11 12:17 entry
- evidence: a from-source replay appeared to stop at `Generating circuit
  JSON...` while the host was under global OOM and I/O pressure. The process
  was still alive and ultimately continued, but the direct `tsci build` call
  had no pipeline heartbeat, state file or process-group deadline. Routing and
  DRC already used the bounded runner, so progress observability depended on
  which child happened to be active.
- implementation: the canonical full rebuild template and USB Hub v4 invoke
  `tsci build` as the `tscircuit_build` stage through `pcb_flow.py`; the v4
  config budgets and times out at 60 seconds and emits a heartbeat every 10
  seconds. The canonical route template now names a 60-second budget and a
  conservative 180-second starting deadline for projects without measured
  history. `tests/t1_rebuild_templates.py` rejects a return to the former
  unbounded direct call.
- history: 2026-08-11 — completed during Stage 4 deterministic replay.

## IMP-014 — bounded console detail for foreign-producer diagnostics

- status: proposed
- observed: USB Hub 3S v4 Stage 4 from-source replay, 2026-08-11
- evidence: `tsci build` emits hundreds of unnamed-trace and supplier-model
  advisories before the repository's diagnostic gate prints the useful
  classified summary (`367 advisory`, zero embedded errors). The volume hides
  stage transitions and makes a healthy build hard to scan even though the
  complete detail remains useful for diagnosis.
- intended landing point: retain the complete producer stream in a timestamped
  build log while the interactive channel prints stage start/heartbeat/end,
  hard errors and a warning-class summary. Failure must automatically include
  a bounded tail and the log path; suppression may never discard evidence.
- completion evidence required: clean/chatty/failing producer fixtures prove
  bounded console output, lossless retained logs and visible failure context.
- history: 2026-08-11 — proposed after the first full routed replay.
- additional evidence: the 2026-08-12 exact placement resume completed all
  useful machine work in seconds, but its live stream repeated KiCad's empty
  enum assertion three times at nearly every pcbnew load, repeated image-
  handler registration diagnostics during prep/review checks, and printed ten
  non-blocking silk-ownership lines. The same class also affects KiCad render
  progress. The retained log should preserve every line, while the live view
  groups known warning signatures by class/count and keeps stage timing,
  heartbeat, failure context and artifact paths prominent.

## IMP-015 — stable electrical topology-review digest

- status: implementing
- observed: USB Hub 3S v4 Stage 4 from-source replay, 2026-08-11
- evidence: a fresh TSX-to-KiCad reconstruction invalidated the pre-route
  normalized-netlist hash while all independent semantic gates and a direct
  60-net/270-node traversal reported the same electrical graph. The current
  digest deliberately normalizes only export time and instance UUIDs, leaving
  other non-electrical serialization/presentation churn capable of forcing a
  manual re-review.
- intended landing point: parse KiCad's legacy netlist and hash a canonical
  projection containing every component identity, value, footprint, property,
  net name, physical pin identity and no-connect, with unordered collections
  sorted and presentation paths/timestamps excluded. Keep the raw-byte hash in
  the review for forensic provenance.
- completion evidence required: permutations of ordering, UUIDs, timestamps
  and source paths retain one semantic digest; a one-pin, value, footprint,
  property, net or no-connect change produces a different digest; existing
  reviewed boards migrate through explicit fresh reviews.
- implementation progress: `pre_route_review_check.py` now normalizes the
  export date, instance UUIDs, schematic source path, generated Sheetname/
  Sheetfile properties and project-derived netclass labels. This makes full
  and pinned exports of the byte-identical v4 schematic agree while a
  component-value change remains a known-bad failure in
  `tests/t1_pre_route_review.py`. Collection-order canonicalization and the
  complete mutation matrix remain outstanding, so this item is not complete.
- additional evidence: the final v4 full-source proof produced a new
  normalized digest (`2bb964f6...` versus pinned `be5c7573...`) and correctly
  stopped for review, even though an independent structural parse found exact
  equality over all 88 `(ref, footprint, value)` records, all 324 physical
  pin-to-net identities and all 69 net names. This isolates the remaining
  false invalidation to collection/serialization ordering and makes sorted
  structural projection the next implementation step, not a speculative
  optimization.
- history: 2026-08-11 — implementation started after the Stage 4 deterministic
  replay proved the full/reuse contradiction.

## IMP-016 — adopted-rule digest should not include orchestration metadata

- status: completed
- observed: USB Hub 3S v4 Stage 4 replay, 2026-08-11
- evidence: adding only `flow.budgets_s.tscircuit_build` and
  `flow.timeouts_s.tscircuit_build` invalidated all four hash-bound electrical,
  pin, layout and render reviews because `design_rules_digest()` hashes the
  whole `route.yaml`. The review files had to be rebound even though board,
  copper, parts and every design/fabrication rule were unchanged.
- additional evidence: adding U9's placement-local taper rule and moving J5's
  deterministic CC seed coordinates invalidated both schematic reviews even
  though the normalized electrical netlist and delivered schematic PDF did
  not change. The fail-closed stop was correct under the present contract, but
  it forced electrical/readability review work for a layout-only mutation.
- intended landing point: hash a versioned canonical projection of adopted
  electrical, fabrication, placement and routing semantics. Exclude progress,
  timeout, budget, path, owner, blocker and other orchestration-only fields;
  retain a separate raw config/provenance hash for forensic replay.
- completion evidence required: timeout/heartbeat/log-path mutations leave the
  adopted-rules digest stable; width, clearance, via, layer, route-wave, tap,
  zone, placement and fabrication mutations invalidate it; existing projects
  migrate via fresh reviews.
- implementation: `pre_route_review_check.py` now hashes canonical parsed YAML
  under a versioned `design-v1` projection. All `03_src/rules/*.yaml` and the
  design-bearing keepout, seed, wave, critical-route, tap and stitch sections
  remain bound. Project paths, the whole `flow` block, intermediate/output
  filenames, KRT checkout/import selection and race count are excluded as
  orchestration. `tests/t1_pre_route_review.py` independently reproduces the
  projection and proves both process-only stability and deterministic-copper
  invalidation; the fast-flow reference defines the boundary.
- history: 2026-08-11 — proposed after bounded TSX execution caused a vacuous
  four-review rebind.
- history: 2026-08-12 — implemented when the new checkpoint-resume argument
  reproduced the same false invalidation immediately before v4 layout seal.

## IMP-017 — conditional RF review provenance

- status: completed
- observed: USB Hub 3S v4 Stage 5 recovery-path audit, 2026-08-11
- evidence: `reviewed_commit_provenance()` requires exact SOUND RF schematic
  and PCB review files even when `03_src/rules/rf.yaml` explicitly declares
  `rf.enabled: false`. The ordinary RF contract correctly supports a negative
  applicability decision, but the immutable-commit recovery path hard-codes
  six review lenses and contradicts it.
- intended landing point: always require pin, render, topology and layout
  review provenance; add the two RF review witnesses only when the parsed RF
  contract enables RF. Malformed or missing applicability must fail closed.
- implementation: `pcb_flow.py` parses the schema-1 RF applicability contract
  for reviewed-commit provenance. Non-RF boards require the four general
  review lenses; RF-enabled boards additionally require both exact RF reviews;
  missing/malformed applicability fails closed. `tests/t2_pcb_flow.py` covers
  both branches and the complete 34-test file passes.
- history: 2026-08-11 — implemented and regression-tested during the v4 Stage
  5 backtrack.

## IMP-018 — effective-capacitance evidence gate

- status: completed
- observed: USB Hub 3S v4 Stage 5 independent topology review, 2026-08-11
- evidence: U1 named three 47uF MLCCs and TPS25810 shared another three, so
  nameplate totals appeared to clear 75uF and 120uF requirements. The exact HRE
  manufacturer sheet has no DC-bias curve; none of the existing semantic gates
  rejected crediting unproved nameplate capacitance at 5V bias.
- intended landing point: a machine-readable capacitance obligation names the
  required effective minimum, operating bias, temperature and stability/ESR
  boundary. Each credited capacitor supplies an exact tolerance/DC-bias curve
  or an independent guaranteed minimum; uncredited high-frequency bypass parts
  remain allowed but cannot satisfy the sum.
- implementation: `early_design_check.py` now grades `effective_capacitance_banks`
  from exact component refs and identities. Every contributor must declare
  initial negative tolerance, DC-bias, temperature and lifecycle derating;
  accepted dielectric types and requirement evidence are mandatory. The terms
  are applied multiplicatively and a deficient bank fails before placement.
  `tests/t1_early_design.py` contains clean, DC-bias-shortfall and omitted-term
  fixtures. USB Hub v4 passes at 80.784/75uF for U1, 40.392/30uF for U2 and
  155.592/120uF for the TPS25810 cold-socket bank.
- history: 2026-08-11 — proposed after the independent review rejected
  nameplate MLCC credit; completed during the Stage 5 backtrack.

## IMP-019 — fuse element and coordination contract

- status: proposed
- observed: USB Hub 3S v4 Stage 5 independent topology review, 2026-08-11
- evidence: the schematic and BOM exactly identified the Keystone 3568 holder
  and said “fit 10A MINI fuse”, but did not identify the replaceable fuse whose
  voltage, interrupt, time-current, I2t and ambient-derating properties carry
  the protection claim.
- intended landing point: model holder and fuse element as distinct identities.
  A user-fit/consigned element must name its exact MPN, ratings, installation
  instruction, normal-current/ambient margin, protected-device coordination
  and maximum admitted prospective fault current.
- completion evidence required: holder-only and generic-rating known-bad
  fixtures; exact-element clean fixture; release assembly output names the
  element even though it is absent from the JLC placement file.
- history: 2026-08-11 — proposed after selecting Littelfuse 0297010.WXNV.

## IMP-020 — bounded, function-first schematic layout

- status: implementing
- observed: USB Hub 3S v4 Stage 5 schematic repair, 2026-08-11
- evidence: adding `schX`/`schY` to nearly every component changed a normal
  9--13 second TSX build into a 100% CPU run that had not completed after two
  minutes. The bounded runner's heartbeats proved it was alive, but the broad
  placement graph made the autorouter combinatorial. Reverting those
  coordinates, splitting the drawing by functional responsibility, arranging
  only U9's pins by electrical role, and fitting tall sheets to portrait pages
  restored 9--13 second builds and produced a materially clearer PDF.
- intended landing point: author schematic readability in this order: (1)
  functional sheets with explicit titles, (2) functional pin arrangement for
  dense mixed-role ICs, (3) adaptive page orientation, and only then (4) a
  small, measured set of absolute component constraints. Any step that adds
  constraints must run under the stage deadline and be reverted if it exceeds
  the established performance envelope.
- implementation progress: `render_schematic_pdf.mjs` chooses portrait or
  landscape A-series fit from exact component bounds without transforming the
  Circuit JSON; USB Hub v4 separates input enable, USB-A regulation and
  aggregate protection, and gives U9 a functional schematic pin arrangement.
  The renderer has clean landscape/portrait, exact-input immutability and
  fail-closed ownership fixtures in `tests/t1_schematic_render.py`.
- completion evidence required: USB Hub v4 receives an exact SOUND schematic
  readability verdict; the PCB-design authoring guidance names the ordering
  above; a fixture or static check rejects broad all-component absolute
  placement without an explicit waiver and tighter measured deadline.
- history: 2026-08-11 — proposed and implementation started after the bounded
  all-component placement experiment was stopped at two minutes.

## IMP-021 — aggregate fault/current-limit envelope

- status: implementing
- observed: USB Hub 3S v4 Stage 5 topology review, 2026-08-11
- evidence: three TPS2559 output switches each have a worst-high current limit
  of about 2.849 A, so their independent maxima sum to 8.547 A while U1 is
  rated for 8 A continuous. Per-port current checks and total normal-load
  power checks both passed because neither represented simultaneous downstream
  fault limits. The independent review found the missing envelope. A later
  primary-datasheet audit also found that the initial nominal 33 nF U9 timer
  did not guarantee 10 ms at the joint C/threshold/current corner and violated
  the startup relation while DVDT was open; the generic gate did not model
  either multi-parameter timing envelope.
  A later exact-hash review found a third escape: the authored U9 limits
  omitted TPS25982 Equation 4's `+0.11A` affine term. Because E-FAULT trusted
  copied threshold scalars instead of deriving them from R26 and the equation,
  the wrong pair remained internally consistent and passed every machine gate.
- present disposition: USB Hub v4 adds U9, a no-OVLO TPS259827 aggregate
  circuit breaker, between `5VA_RAW` and `5VA`. Its documented resistor and
  timer corners admit the stated short peak but disconnect persistent
  aggregate overload before U1 must carry the downstream worst-high sum. C29
  is now a 47 nF +/-5% C0G part. Including the 30ppm/C class bound over the
  100C design excursion gives 44.516 nF minimum and guarantees 11.129 ms at
  0.7 V and 2.8 uA. C30 is a 3.3 nF +/-2% C0G part; its 3.224 nF full-corner
  minimum gives a 4.388 ms capacitor term at the documented VIN and DVDT-current
  corner, permitting 82.795 nF while C29's full-corner maximum is 49.498 nF.
  This exact design still requires the topology review and first-article
  transient qualification. The review's second timer escape demonstrated that
  the generic gate is required now, before the present schematic can freeze.
- intended landing point: add a machine-readable fault-envelope contract that
  lists every downstream limiter's full-tolerance maximum, simultaneity rule,
  upstream continuous/peak ratings, aggregate limiter threshold and timer,
  reset behavior, post-timer device response, legitimate-pulse recurrence or
  minimum recovery interval, and evidence. Derived corners must retain enough
  precision or round outward. Fail if an unbounded simultaneous sum exceeds an
  upstream rating, if the interrupting device/timing is absent, or if repeated
  admissible peaks can accumulate without an explicit qualification boundary.
- completion evidence required: clean aggregate-breaker and mutually-exclusive
  fixtures; known-bad independent-limit sum and missing-timer fixtures; USB Hub
  v4 passes from exact U9/R26/C29/C30 values and cited TPS25982 limits.
- implementation progress: `early_design_check.py` now adopts `E-FAULT` when
  `power_tree.yaml` declares `fault_envelopes`. It calculates the simultaneous
  downstream worst-high sum, coordinates breaker threshold corners with
  normal load and upstream continuous/peak ratings, calculates minimum and
  maximum fault time, and checks the maximum timer capacitor against the
  minimum dV/dt startup ramp. Capacitor nominal/tolerance and all programmer
  refs must resolve to exact `electrical_invariants.yaml` `part_value` rows so
  duplicated proof data cannot silently drift. Breaker thresholds are now
  recomputed from the exact programmer, tolerance, TCR, temperature excursion,
  inverse-resistance coefficients and affine current offset; a separately
  published corner lock must match. Explicit normal/fault margins and any
  timer-bounded interval above an upstream continuous rating are also graded.
  Executable clean,
  mutually-exclusive, escaped-X7R, over-threshold, startup-relation and
  missing-timer fixtures live in `tests/t1_early_design.py`.
- measured result: the focused suite is 34/34 green, including 27 known-bad
  discriminators. USB Hub v4's exact authored contract passes at
  normal/peak/fault = 6/7.5/8.547625 A, breaker threshold =
  6.160253--8.066419 A, timer = 11.129--45.962 ms, and startup allowance =
  82.795 nF. The independent exact-hash topology review is SOUND and adds
  TI's maximum 270 us post-timer response for an approximately 46.232 ms
  total worst-case response, still inside the 50 ms physical qualification.
  That review also exposed the remaining generic obligations: outward-rounded
  aggregate precision and an explicit recovery/recurrence condition for the
  legitimate <=10 ms peaks. First-article transient qualification remains;
  the machine proof does not replace it.
- history:
  - 2026-08-11 — proposed after the independent review found a fault
    combination that normal operating-load checks could not represent.
  - 2026-08-11 — implementation started immediately after a second independent
    review reproduced the timer-temperature escape in the revised design.
  - 2026-08-11 — expanded after a fresh exact-hash review found that copied
    threshold scalars omitted the datasheet equation's affine current offset.
  - 2026-08-11 — the corrected exact-hash review closed SOUND and extended the
    future gate scope to outward rounding, post-timer response and repeated-
    peak recovery.

## IMP-022 — pre-review authored-board reference validation

- status: proposed
- observed: USB Hub 3S v4 Stage 5 schematic checkpoint, 2026-08-11
- evidence: the refreshed schematic and electrical rules correctly split the
  USB-A supply into `5VA_RAW -> U9 -> 5VA`, but `route.yaml` and
  `floorplan.yaml` still assigned the U1 output, output bulk and distributor
  geometry to the old unsplit `5VA` rail. The schematic gates passed and two
  expensive human reviews were about to start; a manual frozen-input scan
  caught the contradiction and the reviews had to be stopped. A scratch board
  generation also immediately exposed stale anchored overlaps introduced by
  the added capacitors and breaker.
- intended landing point: before requesting pre-route human review, parse the
  exact canonical netlist and statically resolve every net and `REF.PAD`
  mentioned by floorplan zones/assertions/thermal fields and routing excludes,
  waves, stubs and taps. Require the authored pin's net to equal the declared
  net, reject unknown/superseded names, and optionally run deterministic board
  generation plus collision/placement gates as a disposable preflight.
- completion evidence required: known-bad stale-net, wrong-pad-net, missing
  ref/pad and anchored-overlap fixtures; a clean split-rail fixture; driver
  ordering proves the cheap semantic pass and disposable placement preflight
  happen before either independent review is commissioned.
- present disposition: USB Hub v4's raw/protected zones, taps, assertions and
  placement were corrected manually; disposable board generation now reports
  91/91 anchored parts, zero pad/courtyard collisions, placement PASS and
  pad-separation PASS. The generic checker should be implemented after the
  current board reaches a stable release checkpoint so this repair does not
  expand into another pipeline rewrite mid-stage.
- history: 2026-08-11 — proposed after the review freeze caught a stale
  downstream topology contract before reviewer time was wasted.

## IMP-023 — pinned and provenance-bound TSX dependencies

- status: implementing
- observed: USB Hub 3S v4 Stage 5 schematic rebuild, 2026-08-11
- evidence: the project declared `tscircuit: "*"`, carried no lockfile and had
  no local dependency graph. Two bounded rebuilds failed in 3.983 s and 1.247 s
  because a newly cached `@tscircuit/core@0.0.1658` imported
  `@tscircuit/copper-pour-solver` from a dependency class the package exposed
  only as a development dependency. The missing module existed in another
  global graph, so the same electrical sources could pass or fail according to
  ambient cache/global state.
- intended landing point: every TSX project pins an exact `tscircuit` producer,
  commits its package-manager lock, installs from that graph, and includes the
  manifest plus lock bytes in M-FRESH. A dependency update is an intentional
  producer change that requires rebuild and re-review, not an ambient event.
- implementation progress: USB Hub v4 now pins `tscircuit@0.0.2300` and commits
  `03_tscircuit/bun.lock`; its local graph was installed without lifecycle
  scripts. `build_provenance.py` now fingerprints Bun/npm/pnpm/Yarn lockfiles
  alongside the TSX and package manifest. The project/template contracts and
  PCB-design instructions state the exact-version/committed-lock rule, and
  `tests/t1_rebuild_templates.py` carries a known-bad lock-mutation fixture.
  The canonical driver now runs a bounded
  `bun install --frozen-lockfile --ignore-scripts` before `tsci build`, so a
  clean checkout restores the graph instead of inheriting ambient modules, and
  invokes `./node_modules/.bin/tsci` rather than a PATH-resolved executable.
  The pinned producer also changed capacitor footprinter tokens from `0603`
  to `cap0603`; the bridge now accepts both producer dialects, with a regression
  assertion across 0402/0603/0805/1206/1210.
- measured result: the PATH-resolved executable was independently checked and
  found to be global tscircuit 0.0.2112 even after the local 0.0.2300 graph was
  restored. After binding the executable itself, project-local 0.0.2300
  generation completes in 7.981 s and the whole schematic checkpoint reaches
  the intentional exact-review stop in 12.01 s. The bridge emits 91/91
  non-empty FPIDs; the converter suite is
  43/43 green and the template/provenance suite is 52/52 green, including 24
  known-bad discriminators and one declared provenance blind spot.
- completion evidence required: the focused provenance suite passes, USB Hub
  v4 builds from its local locked graph, and the full schematic checkpoint is
  regenerated and reviewed from that producer identity.
- history: 2026-08-11 — proposed and implementation started when the first
  post-review rebuild exposed an ambient mixed dependency graph.

## IMP-024 — bounded, observable regression-suite execution

- status: implementing
- observed: USB Hub 3S v4 Stage 5 verification, 2026-08-11
- evidence: `tests/run_tests.sh` captures each suite's complete stdout in a
  shell variable and emits nothing until that suite exits. Real default-tier
  suites such as `t1_generate_board.py` and `t1_escape_tier.py` can therefore
  run for more than a minute with no visible progress, no per-suite heartbeat
  and no hard deadline. Process inspection showed the suite was alive, but the
  user-visible behavior was indistinguishable from the historical pipeline
  lockups this work is meant to eliminate.
- intended landing point: execute every suite through the existing
  process-group runner (or an equivalent small wrapper) with periodic
  heartbeat, elapsed time, last-output summary and a declared hard deadline;
  preserve the current independent exit-status/stdout-verdict reconciliation
  and aggregate counts.
- completion evidence required: a quiet-child fixture produces heartbeats and
  is killed with a distinct timeout verdict; a chatty suite streams bounded
  progress; a suite that prints failures but exits zero still trips the harness
  disagreement guard; the ordinary fast tier retains its exact aggregate
  verdict.
- implementation progress: `tests/run_tests.sh` now streams each suite through
  `tee`, emits periodic elapsed-time heartbeats and terminates the suite's
  process group at a declared hard deadline while preserving the suite exit
  status separately from `tee`. `tests/t1_pipeline_reliability.py` exercises
  the shared bounded runner's quiet-child heartbeat/deadline/process-group
  behavior. Direct runner fixtures for chatty-output bounding and the
  exit-zero/printed-failure reconciliation path remain before completion.
- history:
  - 2026-08-11 — proposed after the live fast-tier sweep reproduced the same
    silent-wait experience despite the PCB pipeline stages themselves being
    bounded and observable.
  - 2026-08-11 — implementation started after the schematic checkpoint was
    stable; the default runner now exposes progress and enforces deadlines.

## IMP-025 — mixed output-bank and CFF control-loop contract

- status: proposed
- observed: USB Hub 3S v4 fresh pre-route topology review, 2026-08-11
- evidence: U1 populated TI's table-value 22pF CFF plus required 4.99k series
  RFF while also fitting a 100uF polymer output capacitor. The exact APAQ part
  permits 24mohm ESR, placing its nominal ESR zero near 66kHz; TPSM63610
  section 8.2.1.2.6 explicitly forbids CFF when an output-capacitor ESR zero is
  below 200kHz. E-CAP correctly proved the ceramic minimum but did not treat
  added polymer bulk and CFF as one control-loop decision.
- intended landing point: extend the machine-readable output-bank contract to
  enumerate additional ceramic/polymer capacitance, ESR corners, switching
  frequency, any CFF/RFF population, vendor zero/pole placement requirements
  and explicit CFF prohibitions. Reject a fitted CFF at any admitted prohibited
  corner and require a first-article frequency-response/load-step obligation
  when a mixed bank cannot be closed analytically.
- present disposition: v4 removes R25/C27 and also removes U2's C28 because its
  mixed ceramic/polymer bank is not close to the minimum for which TI recommends
  CFF. ADR-0008 and the PCB-design checklist now require the complete-bank
  review. Implement the general gate after the schematic checkpoint is stable;
  the fresh topology lens currently supplies the independent backstop.
- completion evidence required: known-bad low-ESR-polymer-plus-CFF and
  prohibited ESR-zero fixtures; clean ceramic-minimum+CFF and mixed-bank/no-CFF
  fixtures; exact fitted refs/values bind to the schematic rather than prose.
- history: 2026-08-11 — proposed and the immediate design/instruction repair
  applied after fresh review caught the TPSM63610 prohibition before routing.

## IMP-026 — bounded fresh-context review execution

- status: implementing
- observed: USB Hub 3S v4 Stage 5 topology re-review, 2026-08-11
- evidence: a fresh topology reviewer remained active well beyond the useful
  review window without returning a verdict or a bounded list of unresolved
  checks. From the pipeline's point of view this was the same silent-lockup
  failure class as an unbounded producer, even though the work was reasoning
  rather than a child process. Interrupting it also meant its partial work was
  not admissible as exact review evidence.
- intended landing point: every commissioned fresh-context lens declares an
  elapsed-time or turn budget, verifies exact artifact hashes at entry and
  exit, and returns a closed verdict by the deadline. Any check that cannot be
  resolved inside the budget becomes an explicit material unresolved finding;
  it must not keep the pipeline apparently busy forever. Orchestration should
  expose reviewer age/status and allow a clean replacement without crediting
  partial prose.
- implementation progress: the PCB-design review instructions now require a
  declared review budget and deadline behavior. USB Hub v4's replacement
  topology and PDF lenses were commissioned with exact hashes, 10--12 minute
  budgets, start/end freshness checks and the unresolved-as-finding rule.
  A reusable machine-enforced reviewer watchdog/evidence fixture remains
  outstanding, so this item is not complete.
- follow-up evidence: during the r8 placement re-review, reviewers again ran
  beyond the useful evidence-gathering window despite receiving the written
  budget and despite the machine gates already supplying a complete bounded
  dossier. The operator had to interrupt them and close the evidence manually.
  This proves that a prompt-level deadline is advisory, not enforcement. The
  landing point must therefore own the reviewer process/turn externally: emit
  visible age/last-progress, interrupt at the declared wall time, reject any
  partial witness, and immediately convert the unfinished checklist into a
  named unresolved finding or launch one bounded replacement.
- completion evidence required: a canonical review launcher or protocol test
  proves that a quiet reviewer cannot exceed its declared budget unnoticed;
  a timed-out reviewer produces no admissible witness; and a bounded reviewer
  either returns a current closed verdict or names every unresolved check.
- history: 2026-08-11 — proposed and implementation started after an unbounded
  topology re-review was interrupted without admissible evidence.
- history: 2026-08-12 — r8 reproduced the overrun under an explicit written
  budget; machine-enforced interruption and evidence closure are now required
  for completion, not optional hardening.

## IMP-027 — standards terminology and evidence-identifier lint

- status: proposed
- observed: USB Hub 3S v4 Stage 5 fresh topology review, 2026-08-11
- evidence: the electrical design was SOUND, but review found two forms of
  documentation drift that can change the apparent claim: some prose cites
  TPS2559 document `SLVSCP1C` rather than the exact `SLVSCL5A`, and the local
  token `usb_type_c_receptacle_power_only` can be confused with USB Type-C
  Release 2.5's standardized Power-Only receptacle construction even though
  this board uses a normal 16-contact receptacle with data/SBU lands left NC.
  The same review also caught a parameter-direction error: a capacitor's
  maximum ESR proves the lowest possible ESR-zero frequency, not its highest.
- intended landing point: validate datasheet document identifiers against the
  exact part dossiers; maintain a small glossary of standards-defined terms
  that require an explicit claim/no-claim qualifier; and require prose that
  derives a bound from min/max source data to state which direction that source
  can prove. Run these cheap checks before commissioning exact human reviews.
- completion evidence required: fixtures reject a wrong-but-plausible document
  identifier, an unqualified collision with a governed standards term, and a
  maximum value used to prove a maximum for an inverse relationship; correct
  citations, qualified functional terminology and bound direction pass.
- history: 2026-08-11 — proposed from the final v4 topology lens; the exact
  design review records all three P2 findings so they remain visible meanwhile.

## IMP-028 — pre-review layout-precedent closure

- status: completed
- observed: USB Hub 3S v4 Stage 6 placement entry, 2026-08-11
- evidence: the first real-board build completed footprint placement before
  `P-PREC` found two source-only `part.yaml` records whose precedent ladders
  stopped at tier 1. Correcting those records changes the parts digest and
  therefore invalidates otherwise-current, hash-bound topology and schematic
  render reviews, even though no electrical topology or rendered sheet changed.
- intended landing point: run `P-LAYOUT` and `P-PREC` over the frozen part
  dossiers before schematic generation and before commissioning any review
  bound to the parts digest. Placement should rerun the same checks as a guard,
  but should never be their first execution on a new board.
- completion evidence required: a rebuild-order fixture proves malformed or
  unclosed `layout_refs` fails before TSX generation and before review
  commissioning; a corrected dossier reaches the schematic checkpoint without
  a later placement-stage invalidation; and the placement gate retains an
  independent defense-in-depth check.
- implementation: `policy_audit.py --phase source` now emits only the shared
  P-LAYOUT/P-PREC rows and deliberately ignores any stale realized board.
  `rebuild_all.sh` runs it after the other source-schema checks and before the
  M-FRESH stamp/TSX producer. The existing placement phase still reruns the
  same implementation and adds P-ADJ geometry. Clean and known-bad source-phase
  fixtures prove a project with no board can pass an honest ladder and an
  unclosed tier-1 stop fails; the rebuild-order fixture pins this phase before
  both TSX and review consumption. USB Hub v4's corrected 24-dossier source
  phase passes 2/2 and the subsequent schematic checkpoint reaches only the
  expected stale-review stop.
- history:
  - 2026-08-11 — proposed after the v4 placement policy gate exposed two
    omissions that were knowable before the exact schematic reviews.
  - 2026-08-11 — implemented before recommissioning the invalidated reviews;
    the full v4 driver demonstrated the new early stop/order on real inputs.

## IMP-029 — bounded, cached JLC model preparation for A-RENDER

- status: proposed
- observed: USB Hub 3S v4 Stage 6 placement review, 2026-08-11
- evidence: the native exact-board orthographic and isometric renders each
  completed in 8.6--8.8 seconds, but the first cold-cache `jlc_twin.py` run
  timed out at 180 seconds and a cache-reusing retry timed out at 360 seconds
  after exceeding its 240-second budget. The process was healthy and emitted
  ten-second heartbeats while resolving EasyEDA/JLC models, so this was not a
  deadlock; network/model preparation was incorrectly placed on the exact-
  review critical path. The early JLC export also correctly found 22
  placements without measured per-LCSC rotation evidence.
- intended landing point: after BOM/LCSC identities freeze, prefetch every
  catalog model through a bounded parallel/cache-preparation stage. Record a
  content digest and resolver/tool identity for every successful model and
  make the populated-twin renderer consume only that pinned local cache.
  Missing/failed models must produce a named coverage worklist without
  repeatedly spending the whole review window. The A-RENDER witness schema
  should distinguish `native_geometry`, `catalog_body` and `rotation` coverage
  and machine-verify how it was produced, so a manually authored PASS cannot
  masquerade as a successful `twin_overlay.py` run.
- completion evidence required: cold/warm/missing-model fixtures with bounded
  progress; the warm render performs no network access; a cache or resolver
  mutation invalidates the witness; the placement checker refuses a
  geometry-only PASS where catalog-body coverage is claimed; and USB Hub v4's
  38-code population reaches a complete twin without an indefinite wait.
- present disposition: placement review may use the exact native board render
  for geometry and routing feasibility, but it grants no body-registration,
  height, polarity, CPL-rotation or order credit. The full catalog twin and all
  22 rotation measurements remain explicit DO-NOT-ORDER release blockers.
- history: 2026-08-11 — proposed after two bounded cold-cache twin attempts
  exposed a network/cache stage on the placement-review critical path.

## IMP-030 — rotation-safe thermal-via ownership and exact placement DRC

- status: implementing
- observed: USB Hub 3S v4 Stage 6 placement review, 2026-08-11
- evidence: U9's split exposed pad contains adjacent `5VA_RAW` and GND lands.
  The generic board generator transformed explicit footprint-local thermal-via
  offsets with the wrong KiCad rotation handedness, so a 90-degree placement
  could put a via into the neighbouring net while still assigning it the
  declared source net. U1/U2 had the same coordinate permutation but all
  affected lands were GND, hiding the defect. The original placement battery
  ran overlap and pad-separation checks but did not run exact refilled KiCad
  DRC before commissioning human reviews; the independent pin lens found the
  short and zero-clearance findings instead.
- intended landing point: use one tested footprint-local-to-board transform;
  require every explicit via centre to lie inside its named owner pad and its
  copper shape to avoid every different-net pad; then run full-severity,
  refilled, schematic-parity JSON DRC immediately after placement policy and
  before human review. At this stage only unrouted ratsnest and KiCad's
  `isolated_copper` preliminary-zone class may remain, with no caller-defined
  defect allowlist.
- implementation progress: `generate_board_generic.py` now uses KiCad's
  measured coordinate operator and enforces both owner-pad containment and
  foreign-pad non-collision for each explicit via. The v4 floorplan declares
  48 vias across eight footprints, including independent U9 input/GND fields
  and two cold-socket C23 return vias. `placement_drc_check.py` plus both
  canonical rebuild templates now place P-DRC before PR-REVIEW; clean and
  known-bad fixtures cover shorts, library/clearance defects, parity,
  incomplete reports and attempted generic suppression.
- completion evidence required: the focused generator, placement-DRC,
  template-order and gate-contract suites pass; a clean v4 regeneration has
  zero pad/courtyard collisions; exact pre-route DRC has zero non-island
  violations and zero schematic-parity findings; and fresh pin/layout/render
  reviews bind that exact board hash.
- history: 2026-08-11 — proposed and implementation started immediately after
  the exact placement pin review found the rotated split-pad short.

## IMP-031 — published-legibility silk class for operational markings

- status: proposed
- observed: USB Hub 3S v4 Stage 6 placement render review, 2026-08-11
- evidence: the generated board and DRC accepted 24 functional legends at
  0.60--0.75 mm text height / 0.13 mm stroke and refdes as small as
  0.45 mm / 0.1125 mm. The tier ledger intentionally permits those values
  from boards that were observed to print, while JLCPCB's current official
  capability table says legend below 1.0 mm height or 0.15 mm line width may
  be unidentifiable. The first exact render lens correctly distinguished
  on-screen readability from manufactured readability and rejected safety,
  polarity, switch and port markings below the published envelope.
- intended landing point: model two explicit silk assurance classes rather
  than one ambiguous minimum: `empirical_printed` for noncritical density and
  `published_legible` for polarity, voltage/current, fuse, switch, connector
  and other operational markings. The generic generator should derive both
  height and emitted stroke from the selected class, fail an operational
  caption below the published class, and report coverage by class. Reference
  designators should default to the published class where space permits and
  any smaller fallback must remain visible debt, not a silent success.
- present disposition: v4 now uses 1.0 mm text and 0.16 mm emitted stroke for
  all retained functional captions and every refdes; redundant internal-net
  captions were removed rather than crowded below the limit. Exact P-DRC
  passes with zero silk-overlap or silk-over-copper findings. The fleet-wide
  two-class schema and gate remain future work.
- completion evidence required: clean and known-bad fixtures distinguish the
  two classes; every operational caption is independently inventoried and
  constrained; the emitted-stroke coupling is tested; and a board cannot earn
  a render/release PASS by citing merely `printed before` for a safety label.
- history: 2026-08-11 — proposed after the fresh v4 render review compared the
  exact produced geometry with JLCPCB's official legend table.

## IMP-032 — promote the reviewed schematic at its stage boundary

- status: completed
- observed: USB Hub 3S v4 Stage 6 placement replay, 2026-08-11
- evidence: the full driver deliberately pauses after schematic review and
  again after placement review, while the deterministic reuse driver consumes
  `03_tscircuit/kicad/<board>.kicad_sch`. The full driver copied its newly
  generated schematic into that pinned path only after final PCB DRC. During
  the intended placement iteration, `rebuild_reuse.sh` therefore exported the
  previous schematic topology and failed its review hash before board
  generation. The two schematic files had different SHA-256 digests and the
  normalized netlist changed from the reviewed `be5c7573...` to stale
  `56259186...`; this was a loud stop, but deterministic replay could not be
  used at the stage where it is explicitly needed.
- intended landing point: promote the exact generated schematic immediately
  after its semantic/ERC/checkpoint gates and both hash-bound schematic reviews
  pass, before board generation. A later PCB-stage failure must not revoke a
  completed schematic stage. Verify the pin immediately and again after the
  PCB stages; never promote a producer output that failed its own review.
- implementation: both canonical full-build drivers now copy and compare the
  schematic at the reviewed Stage-2 boundary, and the final stage only compares
  it again. `tests/t1_rebuild_templates.py` proves there is exactly one copy,
  that it follows schematic review, precedes board generation/DRC, and is
  verified both immediately and after PCB work.
- completion evidence: the focused rebuild-template suite passes, a fresh v4
  schematic replay promotes byte-identical `04_kicad` and pinned schematics at
  the review boundary, and `rebuild_reuse.sh` subsequently exports the reviewed
  normalized netlist rather than the superseded one.
- history: 2026-08-11 — found and fixed during the U9/J5 placement correction;
  the stale replay stopped in 0.4 seconds rather than wasting a routing run.

## IMP-033 — evidence-backed per-reference P-OUT exceptions

- status: proposed
- observed: USB Hub 3S v4 Stage 6 edge-connector review, 2026-08-11
- evidence: strict courtyard-to-outline checking correctly reports J5's
  mechanical courtyard 0.500 mm beyond Edge.Cuts after its manufacturer `PCB
  Edge` datum is aligned exactly. That overhang is intentional for the GCT
  USB4105 edge receptacle, while its tightest copper remains 1.700 mm inside.
  `placement_gates.py` supports `out_ok: ["J5"]`, and the contracts call such
  exceptions evidence-backed, but the checker accepts a bare ref string and
  neither requires nor prints the reason. V4 therefore carries a separate
  `out_ok_evidence` map that is human-readable but not yet machine-graded.
- intended landing point: replace or extend bare `out_ok` entries with
  structured `{ref, why, expected_excursion_mm, datum}` records. The gate must
  fail an exception without evidence, print the measured excursion and reason,
  continue checking all copper pads, and invalidate the exception when the
  measured overhang exceeds its declared bound.
- completion evidence required: edge-connector/castellated clean fixtures plus
  missing-reason, wrong-ref and over-excursion known-bads; migration of the
  existing bare-list test; v4 passes at the measured 0.500 mm J5 courtyard
  excursion and still fails if any J5 copper leaves the board.
- present disposition: keep strict courtyard mode enabled for v4 and retain the
  explicit human-readable J5 evidence. Implement the shared schema before a
  second board copies the ungraded map; this is not a routing blocker.
- history: 2026-08-11 — proposed while closing J5's manufacturer edge-datum P1.

## IMP-034 — pre-review exact validation of deterministic route copper

- status: proposed
- observed: USB Hub 3S v4 Stage 7 route preparation, 2026-08-11
- evidence: the canonical routing preflight passed, but `route prep` then
  refused four explicit U5/U6 output via-in-pad drops in 0.70 seconds. Their
  0.50/0.20 mm geometry was copied from the superseded placement. On the exact
  TPS2559 0.50 mm-pitch row, the 0.50 mm via left only 0.13 mm to an adjacent
  0.24 mm foreign-net land, below the adopted 0.18 mm clearance. The route
  emitter behaved correctly and no stochastic routing time was spent, but the
  deterministic copper had not been part of the placement-stage machine gate.
- intended landing point: add a read-only `prep --validate` mode, or equivalent
  exact-board gate, that resolves every authored seed segment/via and tap,
  checks pin/net identity, pad contact, foreign copper, holes, outline and rule
  areas, and emits no board artifact. Run it after placement DRC and before
  hash-bound pin/layout/render review so a moved footprint cannot leave stale
  absolute route coordinates for the routing stage to discover.
- completion evidence required: clean and known-bad fixtures cover moved pads,
  wrong nets, foreign-pad clearance, hole spacing, board-edge/rule-area
  conflicts and idempotency; the full rebuild order pins the validation before
  placement reviews; the tier preflight also grades every prep/stitch seed-via
  declaration against the exact board-setup via and annular constraints. USB
  Hub v4's exact off-pad 0.50/0.20 mm U5/U6 drops pass while the former in-pad
  configuration fails with the measured 0.13 mm foreign-copper gap.
- present disposition: fix v4 now because these four drops are the declared
  current path to the B.Cu output pours and block routing. A rejected interim
  0.40/0.20 mm attempt cleared the neighboring pads but exact DRC found four
  `via_diameter` plus four `annular_width` violations against the board's
  conservative 0.50 mm / 0.15 mm setup; the tier preflight had not compared
  this seed-via block with those board constraints. Keep the shared pre-review
  validation as future work; bounded prep plus exact DRC remain safe backstops.
- history: 2026-08-11 — proposed after the first corrected-placement prep run
  stopped before KRT and exposed stale, electrically impossible via geometry.
- follow-up evidence: Pluto RX2 8-way v5's D15 floorplan proved zero proper
  straight-corridor/courtyard intersections, but the first exact seed attempt
  still refused 7/9 RF centreline segments in 0.41 s: each hit an adjacent U1
  or SMA ground pad at an oblique endpoint. Package-normal and launch-normal
  escape sections made all nine polylines collision-clean. A read-only exact
  seed validation before the D15 human review would have exposed the distinction
  between a body-clear floorplan proof and legal copper without regenerating a
  review checkpoint.
- follow-up evidence: USB-controlled debug hub v1's exact seed emitter accepted
  all 38 reviewed primitives, but a raw KiCad DRC on r0 found four
  `diff_pair_uncoupled_length_too_long` errors. The USB-A-to-ESD branches were
  2.0626 mm against the retained 2.0 mm class ceiling. This was not a collision,
  off-pad endpoint or net-identity failure, so the existing prep checks could
  not see it. A 0.10 mm source placement backtrack reduces all eight branches
  to 1.963 mm without weakening the class rule. Extend the intended
  pre-review validation to run the exact emitted r0 through a raw, unfilled
  DRC and classify only expected partial-route findings (dangling vias/tracks
  and unconnected items); any constraint finding such as uncoupled length,
  width, clearance, via geometry or edge distance must block human review.

## IMP-035 — static pour-service coverage for router-excluded nets

- status: proposed
- observed: USB Hub 3S v4 Stage 7 authoritative post-stitch DRC, 2026-08-11
- evidence: both KRT race candidates were CLEAN and the in-process stitch gate
  also said clean, but fresh KiCad CLI refill found ten opens on nets excluded
  from stochastic routing plus one dangling 5VC_RAW via. All were deterministic
  coverage omissions knowable from the track-free placement: five inter-pad
  gaps in U9's parallel OUT bank, R22 and TP3 outside their named pours, C6/C9
  surface islands without explicit plane drops, and R11 incorrectly declared
  as a drop even though no plane existed under its pad. KRT correctly reported
  zero routed-net opens because these nets were deliberately outside its scope.
- intended landing point: before route search, enumerate every pad on every
  `prep.waves.exclude` net. For each, require exact geometric evidence that it
  is served by a filled zone on a flashed layer, a same-net plated land, or a
  named deterministic seed/tap whose endpoint reaches the intended pour. A
  `plane: true, drop: true` declaration must prove that the named plane
  actually overlaps the selected via site; prose or same-net copper beneath an
  SMD pad is not connectivity. Report the uncovered refs/pins and the owning
  remedy before KRT runs.
- completion evidence required: fixtures reject a pad just outside a pour, a
  split same-net pin bank, a drop over no plane, and a surface island cut by
  later routing; valid direct-pour, plane-drop, plane-tap and seed-stub cases
  pass. USB Hub v4's excluded nets grade every physical landing and the first
  authoritative post-stitch refill reaches zero deferred opens without a
  discovery/rebuild cycle.
- present disposition: repair v4 now in declarative taps and one scoped U9
  output-bank bridge. Keep fresh CLI refill/parity as the authority (IMP-010
  is working as intended); add the static coverage gate before another board
  spends a route/review cycle discovering deterministic opens at the end.
- history: 2026-08-11 — proposed when the first corrected route was clean for
  every routed net but failed 0/0/0 exclusively on excluded pour-net service.
- follow-up evidence: Pluto RX2 8-way v5's first successful RF prep served only
  26/32 SMD GND pads. The six uncovered pads were precisely U1's interleaved
  RF-ground perimeter lands; adding short deterministic links into the exposed
  pad and its existing filled/capped field made the next pre-route denominator
  32/32 before KRT. Coverage must be evaluated after deterministic critical
  copper exists, because that copper both supplies connections and consumes
  legal rescue space.

## IMP-036 — checkpoint-aware canonical rebuild at layout seal

- status: completed
- observed: USB Hub 3S v4 Stage 8 layout-seal preparation, 2026-08-12
- evidence: the full producer deliberately pins and pauses on exact schematic,
  PDF and netlist bytes for independent review. Its safe continuation is
  `rebuild_all.sh --resume-after-schematic-review`, which verifies that
  checkpoint and regenerates the complete board. `pcb_flow.py layout-seal`
  could only call `rebuild_all.sh` without arguments, so it would rerun the
  nondeterministic TSX producer, replace the approved bytes and correctly stop
  for another review instead of ever reaching its seal checks.
- implementation: `flow.rebuild_args` declares optional, source-hashed
  arguments to the canonical rebuild driver. Layout sealing passes them to the
  driver but still performs the fresh board build; malformed values fail
  before seal mutation. USB Hub v4 declares its content-addressed resume arm.
  `tests/t2_pcb_flow.py` covers the exact command and malformed configuration;
  `skills/kicad-pcb/references/fast-pcb-flow.md` defines the contract.
- history: 2026-08-12 — implemented before v4's first layout-seal attempt so
  the orchestration defect could not cause a redundant review loop.

## IMP-037 — stage-typed placement-review validation

- status: completed
- observed: USB Hub 3S v4 Stage 8 layout seal, 2026-08-12
- evidence: the canonical rebuild correctly graded four independent placement
  reviews against the exact track-free board, imported the promoted route,
  applied 29 deterministic services and reached DRC 0/0/0. The seal conductor
  then invoked the same pre-route checker against the routed board. Its hash
  differed by design, so a clean layout could never acquire a seal witness.
- implementation: `pcb_flow.py layout-seal` leaves the track-free review in
  the canonical rebuild at its true lifecycle boundary. After routing it still
  repeats body/outline clearance, critical-route, landability, pad-separation,
  placement-policy and full DRC checks. Reviewed-commit recovery remains bound
  to exact final pin/render/topology/layout review provenance. Hermetic tests
  prove no post-route plan contains `pre_route_placement` and that geometry,
  connectivity and DRC remain present.
- history: 2026-08-12 — implemented after the first fully clean v4 seal replay
  exposed the impossible cross-stage comparison in 0.094 seconds.

## IMP-038 — make ampacity audit a canonical stage gate

- status: completed
- observed: USB Hub 3S v4 routed-evidence review, 2026-08-12
- evidence: `rules_audit.py` correctly rejected four high-current classes and
  an unreadable switching-node declaration when run manually. Neither
  canonical rebuild driver invoked it: source policy read only its A-FIRE
  helper, while layout seal reached DRC 0/0/0 and acquired a witness despite a
  0.30 mm U9 output-bank collector and one plane-transfer via carrying the
  protected aggregate rail. A capable checker outside the execution stack is
  documentation, not a gate.
- implementation: full and deterministic canonical drivers, plus both
  skill-owned templates, now run `rules_audit --phase source` before producer
  spend and the full board-bound audit immediately after the final rules
  generation and before final DRC. High-current pour classes carry explicit
  geometry evidence; signal exemptions are parseable. Template tests reject a
  driver with either stage missing or misordered.
- completion evidence: generator/router suites pass, rebuild-template tests
  prove source-before-producer and full-rules-before-final-DRC ordering, and
  USB Hub v4's exact regenerated board must pass A-CLASS/A-AGREE/A-AMP/A-FIRE/
  A-ORDER before reacquiring layout seal.
- history: 2026-08-12 — implemented immediately after the first routed copper
  extraction found the checker had teeth but no call site.

## IMP-039 — selective, fabricator-compatible via treatment

- status: completed
- observed: USB Hub 3S v4 manufacturing-evidence review, 2026-08-12
- evidence: the board source declared `capping: yes, filling: yes` as a KiCad
  board default. KiCad 10 documents “From rules” vias as inheriting that
  default, so every ordinary 0.60/0.30 mm routing/stitch via appeared to request
  IPC-4761 Type VII even though only via-in-pad holes need the process. JLC's
  current capability table limits its via-in-pad family and its order guide
  requires the selected hole family in order remarks. The blanket declaration
  was ambiguous, unnecessarily expensive and not an exact manufacturing
  instruction.
- implementation: the shared generator and tap emitter now support item-level
  capping/filling overrides through KiCad's per-via API. USB Hub v4 marks only
  its 0.50/0.20 mm via-in-pad fields and exact SMD-pad drops Type VII; ordinary
  0.60/0.30 and 0.70/0.30 mm transfers inherit the tented board default. The
  machine-readable assembly contract requests copper-paste fill, names the
  exact geometry/source and retains a mandatory uploader confirmation.
- completion evidence: clean tests prove item-level flags and geometry survive
  a KiCad save; known-bads reject malformed protection and misuse of exact via
  placement; the regenerated board/fab package must census protected versus
  ordinary vias and reproduce the order remark before release seal.
- history: 2026-08-12 — implemented while comparing the exact v4 board against
  KiCad 10 IPC-4761 behavior and JLCPCB's current via-covering guidance.

- follow-up: the first selective implementation still assigned four ordinary
  off-pad seed vias the protected family's 0.50/0.20 mm geometry. Native KiCad
  flags were correct, but Gerber order instructions cannot address them by
  per-item metadata. USB Hub v4 now makes the process families disjoint by
  drill: every 0.20 mm drill is Type VII and all ordinary vias use 0.30 mm.
  The r7 source and fully stitched censuses prove no cross-family exception.

## IMP-040 — promoted-route compatibility before placement review

- status: completed
- observed: USB Hub 3S v4 corrected-process replay, 2026-08-12
- evidence: the track-free board and its schematic/placement geometry were
  independently sound, but `route.final` still selected r5. Exact import then
  failed in under one second because 18 of the 48 inherited source-owned vias
  were 0.60/0.30 mm in r5 and 0.50/0.20 mm in the current source. All 48 r5
  copies also predated the item-level Type-VII flags. The human layout lens
  correctly refused to grant route permission to a canonical command that
  could not execute, forcing a review round to discover a static derivative
  incompatibility.
- implementation: `promoted_route_check.py` runs inside the placement phase of
  `pre_route_review_check.py`, immediately after exact track-free generation
  and before any human review is credited. For an explicitly selected existing
  `route.final`, P-ROUTEBASE independently compares footprint placement/layer,
  pad geometry/net identity, and every inherited source-via identity
  `(net, x, y)`, geometry and IPC-4761 process bits. Missing/new source vias and
  stale placement fail with exact evidence. An absent artifact is explicit
  N-A only for a first route. The importer's independent geometry refusal
  remains in place as defence in depth.
- completion evidence: seven focused fixtures cover compatible inheritance,
  a first route, geometry drift, process drift, added and removed source vias,
  and moved placement. USB Hub v4's freshly regenerated exact base passes
  95-footprint / 48-source-via coverage against promoted r7; the stale r5 case
  is the measured incident this gate now prevents before review spend.
- present disposition: v4 was repaired by a fresh bounded route from corrected
  r0 and promotion of r7 after the process families were made drill-disjoint.
  P-ROUTEBASE is now a mandatory canonical placement-review prerequisite.
- history: 2026-08-12 — proposed after the exact v4 review found the stale
  promoted artifact before any routing or fabrication spend.
- history: 2026-08-12 — implemented and regression-tested before v4's first
  layout seal; the exact corrected r0/r7 pair passes 95/48 comparisons.

- follow-up: deterministic route-prep copper is now part of the same identity
  boundary, not merely the generated placement. The canonical drivers run
  prep before placement review, and P-ROUTEBASE compares every prepared
  segment and via with the promoted route. Focused coverage is 9/9, including
  a missing prepared segment and a missing prepared via. USB Hub v4's exact
  corrected r0/r8 pair passes 95 footprints / 64 base-or-prepared vias / 12
  prepared segments; the earlier r7 correctly fails on all twelve newly
  declared U4-U6 input-bank vias.

## IMP-041 — series-transition via ampacity as a non-vacuous gate

- status: completed
- observed: USB Hub 3S v4 routed-copper review, 2026-08-12
- evidence: connectivity, full DRC and netclass ampacity all passed while the
  exact board forced the aggregate protected rail through four 0.30 mm drill
  barrels and each 2.849 A USB-A input island through one 0.20 mm drill barrel.
  Those banks credited only 3.36 A versus 8 A and 0.55 A versus 2.849 A under
  TI SLVA959B Table 3-1's IPC-2152 10 C-rise screening values. Same-net vias
  elsewhere cannot repair this: they may be geometrically countable without
  carrying the series current at all.
- implementation: `via_ampacity_check.py` grades named, tight series-boundary
  rectangles from `route.yaml`, sums only declared finished-hole capacities,
  gives fill material zero electrical credit, and requires a source, method,
  temperature rise, continuous-current requirement, minimum via count and
  physical reason. A-VIA runs after the final saved-board construction and
  rules audit but before authoritative DRC in both canonical drivers and in
  layout seal. Its explicit vacuity fixture proves the geometric limitation;
  independent topology/path review and loaded first-article testing remain
  mandatory.
- completion evidence: clean, insufficient, explicit-N-A and vacuity fixtures
  pass 4/4; gate-contract adoption rises with the new declared blind spot. The
  exact r8 board passes all four banks: U9 has fourteen 0.70/0.30 mm transfers
  crediting 11.76 A for 8 A, and each U4-U6 input has four ordinary 0.60/0.30
  mm transfers plus one protected 0.50/0.20 mm pad drop, crediting 3.91 A for
  2.849 A. V-PROCESS independently counts 65 protected and 118 ordinary vias
  with drill-disjoint process families; DRC is 0/0/0.
- history: 2026-08-12 — implemented before routed review was allowed to resume;
  the checker first failed the previously clean r7 board, then passed the
  declaratively repaired and freshly routed r8 board.

## IMP-042 — exact local datasheet authority before pin review

- status: completed
- observed: USB Hub 3S v4 routed pin review, 2026-08-12
- evidence: the first exact-board pin lens reached a conclusion while the
  selected TPS2559, TPS259827O and SMBJ15A dossiers had no hash-selected local
  datasheet bytes. A mutable URL or a neighboring family PDF can look plausible
  and still make the review non-reproducible. This was discovered only after
  the independent reviewer had spent its full pass.
- implementation: `pin_audit.py` now fail-closes as P-AUTH unless
  `datasheet.sha256` is a valid digest matching exactly one of the local PDF
  candidates. It never falls back to directory order, a sole unbound PDF or a
  URL. The parts contract now calls the URL human retrieval provenance and the
  digest-selected bytes review authority. Exact vendor-authored PDFs were
  archived for TPS2559, TPS259827O, SMBJ15A and the Phoenix 1715022 terminal;
  the latter two retain exact distributor-mirror provenance because their
  manufacturers' delivery endpoints block automation.
- completion evidence: `tests/t1_pin_audit.py` passes one clean selector and
  three known-bad authority cases; schema governance proves the digest reader
  and the pin-review canon names P-AUTH. The exact v4 dossiers are regenerated
  from the sealed-board hash before the confirmation lens is commissioned.
- history: 2026-08-12 — implemented immediately after the routed pin lens
  exposed the late authority gap; focused pin, contract, schema and gate-on-gate
  suites passed before review resumed.

## IMP-043 — non-guaranteed bounds must remain release obligations

- status: implementing
- observed: USB Hub 3S v4 routed topology review, 2026-08-12
- evidence: the first sealed-board topology review found that TPSM63604 lists
  FB input current as 10nA typical without a maximum, while the project treated
  a 50nA engineering allowance like a closed component corner. The same review
  found that the Pi delivery calculation named neither an exact cable nor the
  GCT connector's 50mOhm post-test limit. Correct arithmetic cannot promote an
  unguaranteed typical value or an unnamed accessory into production evidence.
- implementation: v4 lowers the Type-C divider impedance by ten, screens FB
  current at 500nA and names Amphenol 10165794-Z0030YBLF. GCT's
  post-environment contact limit remains plausibility evidence, while the
  binding qualified term is a hot four-wire J5-land-to-Pi-load-plane bound that
  includes both mated pairs and cable/sink internals. Complete-path voltage and
  resistance remain explicit first-article findings. The paper gate may permit
  a controlled engineering article after independent review, but it may not
  close the physical qualification or production-release state.
- additional evidence: the first repaired-PDF review found the selected U2
  dossier still described the superseded 50nA screen while ADR-0009 and the
  executable rule used 500nA. The exact-bound human comparison caught the
  contradiction, but a typed shared qualification obligation would give this
  fact one machine-readable owner instead of duplicating it across prose.
- additional evidence: Pluto RX2 8-way v5 set the TPS7A2433 dossier's
  `pdiss_max_mw` to 66 and explicitly described it as a 30mA analysis ceiling,
  while the field contract defines it as a package rating or board/ambient
  derating. `power_topology.py` correctly proved 44.825mW < 66mW but could not
  detect that the compared ceiling had the wrong semantic authority. Correct
  arithmetic over a self-selected design budget is not a component-rating
  proof.
- intended landing point: extend the shared design/release schema so every
  `engineering_qualification_bound`, `qualified_max`, or other non-datasheet
  basis creates a typed validation obligation with an owner, acceptance test
  and latest release stage it blocks. A gate must reject a production claim if
  any such obligation is open, and report distinctly whether it blocks design,
  first-article ordering, first-article acceptance or production.
  Numeric rating fields additionally need a typed `{value, basis, source,
  conditions}` record; a package rating, board/ambient derating, engineering
  screen and design operating budget are distinct closed-vocabulary bases and
  may not substitute for one another merely because their units match.
- completion evidence required: clean fixtures for a controlled prototype and
  a fully qualified production release; known-bads for a typical-only maximum,
  unnamed interconnect and missing acceptance test; USB Hub v4 reports its
  FB/interconnect obligations without misclassifying them as guaranteed
  limits.
- history: 2026-08-12 — project-level implementation started while repairing
  the routed topology review; shared schema/release enforcement remains open.
- history: 2026-08-12 — corrected the stale U2 dossier before commissioning a
  fresh review; no review hash was carried across the changed parts digest.
- implementation progress: `power_topology.py` now reads and reports the
  optional delivery `margin_basis`/`margin_evidence` pair and rejects partial
  declarations; USB Hub v4's 5% residual is therefore no longer an orphan
  schema field. This closes field propagation into the design gate, but the
  generic release-obligation schema and production-claim refusal remain open.
- history: 2026-08-12 — USB-IF's normative LLCR measurement boundary showed
  that the first contact/cable split did not account unambiguously for two
  mated pairs and excluded plug internals; IMP-047 records the endpoint-level
  generalization and v4 now qualifies the complete interconnect instead.

## IMP-044 — rendered-symbol endpoint coincidence

- status: completed
- observed: USB Hub 3S v4 schematic readability re-review, 2026-08-12
- evidence: Circuit JSON connected C22/C23 and their traces at identical
  schematic-port coordinates, but the delivered PDF visibly separated each
  polarized-capacitor body from both wires. The installed `circuit-to-svg`
  renderer composes a terminal translation with a non-unit symbol scale in an
  order that leaves a scale-dependent offset. Electrical parity and ERC could
  not detect this presentation defect.
- implementation: `render_schematic_pdf.mjs` now corrects only a display copy
  of scaled two-port symbols and their display ports before SVG conversion;
  traces and the authoritative Circuit JSON remain unchanged. It recreates
  the installed renderer's transform, fail-closes above 1 micrometre residual,
  and reports the correction count and maximum residual. The correction is
  deliberately presentation-only and remains subordinate to normal-scale
  human readability review.
- completion evidence: `tests/t1_schematic_render.py` proves both symbol
  terminals land on their original endpoints, the input object and exact JSON
  file stay unchanged, aliases remain canonical, and malformed/unowned inputs
  fail closed. The exact v4 PDF applies two corrections with a measured
  0.000168 mm maximum residual; pages 3 and 9 visibly join C22/C23 to both
  rails.
- history: 2026-08-12 — implemented immediately after the second independent
  PDF review exposed the gap; ineffective source-size hints were removed.

## IMP-045 — pre-spend schema and bound governance

- status: completed
- observed: USB Hub 3S v4 schematic regression replay, 2026-08-12
- evidence: the canonical schematic rebuild passed and two fresh human
  reviews were already in progress when the full repository suite found that
  new `margin_basis`/`margin_evidence` fields had no declared reader and that
  ADR-0009 published `<=14mOhm` without an executable bound block. Both facts
  were knowable from authored bytes before the 8.143-second producer or any
  reviewer time.
- implementation: the full rebuild template and v4 driver now run
  `schema_reader_audit.py` and `adr_bound_provenance.py` as bounded,
  heartbeat-emitting source stages before the provenance stamp and TSX build.
  ADR commands have a 30-second per-command limit and both wrapper stages a
  60-second process-group deadline. The v4 delivery-margin pair is read and
  reported by E-MARGIN; ADR-0009's cable limit regenerates from the exact
  98mOhm path decomposition. The fleet ratchets are now 502/502 declared
  schema keys, 424 proven readers, and 13 cited ADR bounds with 37 owed.
- completion evidence: `tests/t1_rebuild_templates.py` proves ordering and a
  post-TSX known-bad; `tests/t1_power_topology.py` covers complete and partial
  margin provenance; `t1_schema_reader.py` and `t1_adr_bounds.py` pin the
  raised monotone floors. The two prematurely commissioned reviews were
  interrupted and cannot become accepted evidence.
- history: 2026-08-12 — implemented in the same stage that exposed the gap.

## IMP-047 — IR-budget terms need non-overlapping measurement endpoints

- status: implementing
- observed: USB Hub 3S v4 Type-C topology review, 2026-08-12
- evidence: a 25mOhm contact term applied USB-IF/GCT's 50mOhm post-stress LLCR
  as four parallel VBUS plus four parallel GND contacts, and a separate
  14mOhm cable term named an exact assembly. USB Type-C Release 2.0 section
  3.7.8.1 defines LLCR across one plug/receptacle pair and excludes internal
  paddle cards/substrates. The real board-to-Pi path has two mated pairs. Each
  scalar was plausible, their sum was machine-checked, and the boundary still
  omitted or ambiguously assigned physical segments.
- implementation progress: USB Hub v4 now uses one <=39mOhm hot four-wire
  qualified term from J5 PCB-side VBUS/GND lands to Pi load-plane sense points,
  explicitly including both mated pairs, cable plug internals/conductors and
  Pi entry path. `early_design_check.py` accepts that complete-interconnect
  alternative for a load-plane claim and rejects mixing it with decomposed
  contact/cable terms; the template contract documents the choice.
- intended landing point: give every IR component structured `from`/`to`
  endpoints and a path-order/coverage gate that detects gaps and overlap,
  rather than relying on evidence prose. Measurement planes should identify
  Kelvin points, not only device classes.
- completion evidence required: clean fixtures for fully decomposed and
  end-to-end-qualified paths; known-bads for a missing sink connector, double
  counted interface, overlapping complete/decomposed terms and unjoined
  endpoints; the real v4 report prints one continuous regulator-to-load path.
- history: 2026-08-12 — project correction and mutual-exclusion guard landed;
  structured endpoint continuity remains open.

## IMP-046 — rendered reference/value occlusion preflight

- status: proposed
- observed: USB Hub 3S v4 schematic readability review, 2026-08-12
- evidence: the exact PDF was electrically correct and its scaled-symbol
  terminals passed the endpoint check, but BOOT_C_C/BOOT_C_R/GND label ink
  covered C4's reference designator on page 9. The independent normal-scale
  review blocked placement; moving only C4's schematic coordinate made its
  reference, value and terminals plainly readable. Existing electrical, ERC
  and terminal-coincidence gates cannot grade text occlusion.
- intended landing point: before commissioning human readability review,
  compare rendered ink or PDF text boxes for every component reference and
  value against label, conductor and symbol ink. Report the exact page/ref and
  refuse a zero-denominator run. Keep the human review: collision-free text is
  necessary but does not prove page flow, explanatory adequacy or correct
  visual interpretation.
- completion evidence required: a clean multi-page fixture with every
  reference/value measured; known-bads for label-over-reference,
  wire-through-value and missing/unmeasurable text; a discriminator proving
  the fixed C4 page changes verdict while an adjacent clear component does not.
- history: 2026-08-12 — recorded after the third fresh PDF review caught the
  defect before any placement or routing work was allowed to resume.

## IMP-048 — compare visible schematic paths with electrical nets

- status: proposed
- observed: USB Hub 3S v4 schematic readability review, 2026-08-12
- evidence: page 3 visibly presented C2 as VIN-to-VIN while the exact netlist
  correctly placed it between VIN and GND. Netlist parity, invariants and ERC
  could prove only the electrical artifact; terminal-coincidence could prove
  only that a symbol met the lines drawn at it. None could prove those visible
  lines communicated the same endpoint nets. The independent human lens did.
- near-term implementation: retain exact-PDF human review and replay the full
  net-survival/parity gates after every presentation edit. USB Hub v4 now uses
  explicit per-pin VIN/GND labels for C2, avoiding an ambiguous shared auto-
  routed trunk. It also names the formerly isolated U1 `5VA_RAW`, U4-U6
  `VBUSA1/2/3` and U2 `VIN` pin groups at their visible endpoints. A broader
  attempted move was rejected when net-survival caught an unrelated SW1
  open-pin merge, demonstrating why a local-looking layout edit cannot skip
  the electrical replay.
- intended landing point: derive a display graph from each rendered sheet,
  associate symbol terminals and net-label anchors with visible conductors,
  and compare the reached endpoint labels with the exact netlist. Report each
  checked terminal and refuse missing, multiply-labelled or zero-denominator
  paths. Treat explicit disconnected net labels as valid named endpoints.
- completion evidence required: a clean VIN-to-GND capacitor; a known-bad
  rendering of the same netlist as VIN-to-VIN; a misleading junction; a valid
  explicit-label endpoint; and a discriminator proving that endpoint
  coincidence alone still passes the VIN-to-VIN fixture.
- history: 2026-08-12 — recorded after the fourth fresh schematic review;
  project-level explicit endpoints landed, generic visible-path comparison is
  still open.

## IMP-049 — bounded independent-review briefs and closure deadlines

- status: implementing
- observed: USB Hub 3S v4 exact placement review, 2026-08-12
- evidence: pin, layout and render reviews began on the same frozen board.
  Render and layout closed normally, but the first pin reviewer kept widening
  an already-complete physical-land investigation despite repeated requests to
  write a verdict. It produced no review file and was discarded. A replacement
  brief limited to six named failure classes closed promptly, passed all
  192 physical identities and wrote the required exact-hash witness. No design
  bytes changed in either attempt.
- intended landing point: every independent review commission names its exact
  immutable inputs, one allowed output, bounded checklist, explicit exclusions,
  verdict vocabulary and a wall-clock closure budget. At the deadline the
  reviewer must write a closed verdict from evidence already collected or
  return `INCOMPLETE`; it may not silently broaden scope. An incomplete attempt
  is never review evidence and is replaced, with its elapsed time recorded.
- completion evidence required: orchestration tests for on-time SOUND,
  on-time DEFECTIVE, deadline INCOMPLETE and forbidden-file mutation; review
  journals separate machine-stage duration from human-review duration and
  report discarded attempts without treating them as design failures.
- history: 2026-08-12 — proposed after the placement pin lens became the only
  long-running activity despite all producer and gate commands being bounded.
- history: 2026-08-12 — the strict schema-1 commission/witness core landed in
  shadow form. It binds one lens, exact subject/commit/artifacts, a non-zero
  checklist, explicit exclusions, one output and a UTC deadline; durable
  output/input hashes are independently supplied at admission. Late and
  partial witnesses remain inadmissible, while a complete DEFECTIVE witness
  remains valid blocking evidence. A launcher/legacy-Markdown adapter and
  real-review adoption remain open, so this entry is not complete.
- history: 2026-08-12 — USB Hub 3S v4 now exercises a project-local real
  placement commission at the exact route-prep boundary. It emits either an
  atomic `ALREADY_ADMISSIBLE` pointer or an immutable content-addressed
  `INCOMPLETE` request with top/isometric renders; it never writes the human
  witnesses or acceptance token. The unchanged review gate still reported all
  eight stale findings. First preparation measured 19.77--21.15 seconds and a
  semantic rerun 1.06--1.07 seconds, so no placement-resume flag was added.
  Promotion of the adapter and direct schema-1 review-service integration
  remain open.

## IMP-050 — generated evidence must prove fresh output, not exit zero

- status: implementing
- observed: USB Hub 3S v4 routed-review export, 2026-08-12
- evidence: `kicad-cli pcb render` rejected a negative-first rotation argument,
  printed its usage page, returned exit code zero and wrote no file. Because
  the output directory already held an isometric PNG from 02:29, `set -e` let
  the script continue and its final checksum table presented that stale image
  beside fresh 05:23 evidence. Only explicit timestamp inspection exposed it.
- implementation progress: the v4 exporter now removes each exact expected
  target before starting, requires a non-empty file immediately after every
  producer/conversion, and uses the proven positive-first `35,0,-35` rotation
  syntax. A complete rerun regenerated all nine outputs, including a fresh
  isometric view. No exit status can preserve an adjacent old artifact now.
- intended landing point: make delete-before-produce plus postcondition
  verification the shared rule for every generated review/release artifact.
  Where practical also stamp input hash, producer command and finish time in a
  machine manifest; consumers should bind that manifest rather than infer
  freshness from directory presence.
- completion evidence required: a fixture whose fake producer prints usage,
  exits zero and leaves an old file must fail; clean and zero-byte outputs must
  discriminate; project exporters/templates adopt the same helper or shared
  wrapper.
- history: 2026-08-12 — project repair landed immediately; shared helper and
  executable known-bad coverage remain open.

## IMP-051 — long external stages must expose progress and a bounded retry budget

- status: implementing
- observed: USB Hub 3S v4 JLC digital-twin fetch, 2026-08-12
- evidence: after its one setup line, `jlc_twin.py` produced no console output
  for more than 90 seconds while fetching and retrying catalog CAD. The process
  was alive and measurable only by inspecting its cache: 16/40 unique codes had
  completed at roughly two minutes, then 19 code directories existed with eight
  still empty during backoff. To an operator this is indistinguishable from the
  historical pipeline lock-up unless they know how to inspect processes and
  cache timestamps.
- intended landing point: every network or otherwise long-running stage prints
  a periodic machine-readable heartbeat containing `completed/total`, current
  item, attempt/max-attempts, retry/backoff seconds, elapsed time and a rolling
  ETA. The orchestrator must declare a wall-clock budget before launch and end
  with a distinct `TIMED-OUT` result plus a resumable command; completed
  content-addressed cache entries must survive the stop. Silence longer than a
  configured heartbeat interval is itself a process finding, not permission to
  wait indefinitely. Consumers such as `jlc_rotation_measure.py` should index
  the cache tree once, not run a recursive repository-wide glob independently
  for every requested code, and should emit a per-code progress/result line.
- implementation progress: `jlc_twin.py` now fetches each unique LCSC code only
  once per run, prints `completed/total`, current code, state, attempt budget,
  elapsed time, rolling ETA, backoff and whole-run budget, heartbeats while a
  child is silent, bounds every child and the complete batch, preserves the
  per-code cache, and prints a distinct resumable `TIMED-OUT` result. The live
  v4 rerun is the first production exercise; rotation-measure cache indexing
  and shared orchestration remain open.
- completion evidence required: deterministic fixtures for steady progress,
  transient retry recovery, a permanently failing item, a silent child process
  and resume from partial cache; journals report productive fetch time,
  backoff time and final coverage separately.
- history: 2026-08-12 — recorded during the first v4 manufacturing-twin run;
  the active process was left unchanged because its cache showed forward
  progress, but the missing telemetry was visible immediately. The first
  16-code rotation batch then spent 36 seconds CPU-searching cache roots in
  silence before reporting that only two requested models were available,
  confirming the same observability problem outside the network fetcher.
- history: 2026-08-12 — the JLC twin implementation and deterministic silent-
  child/cache-replay tests landed; 33/33 twin tests pass, including a fixture
  that heartbeats, times out in 0.25 seconds and emits the resumable command.
- history: 2026-08-12 — the Pluto RX2 8-way v4 canary isolated the same
  symptom in local compute: `cpwg_field_solver.py` used about 24 CPU cores but
  emitted no progress for its measured 35.724-second solve. The design result
  was clean; the observability contract was not. The stage is now assigned a
  measured 45-second performance budget and a 60-second process-group deadline
  through the bounded runner so silence produces heartbeats instead of an
  indefinite-looking shell.

## IMP-052 — preflight mutable catalog clients and distinguish compatibility from rate limits

- status: implementing
- observed: USB Hub 3S v4 JLC digital-twin fetch, 2026-08-12
- evidence: installed `easyeda2kicad` 1.0.1 sent its pinned Chrome/120
  User-Agent and EasyEDA's CloudFront returned HTTP 403. The same exact product
  endpoint returned HTTP 200 with Chrome/146. After twelve successful model
  fetches the newer identity also received 403, demonstrating a second state:
  burst/rate enforcement. Treating both as a generic retry consumed minutes
  and could never tell the operator whether waiting or upgrading was useful.
- intended landing point: before a batch, issue one bounded capability probe
  against the exact endpoint/client headers and classify incompatible client,
  transient service failure and mid-batch throttling separately. Keep the
  User-Agent/configuration repository-owned and overrideable; print the tested
  client identity. Apply a rate budget and adaptive backoff after a successful
  preflight rather than mistaking the first burst 403 for a permanent client
  failure. Never relabel any 403 as `NO-CAD`.
- implementation progress: a repository-owned compatibility wrapper patches
  only the upstream HTTP User-Agent (default Chrome/146, configurable through
  `JLC_TWIN_USER_AGENT`) without editing the installed package; `jlc_twin.py`
  selects it only for the real `easyeda2kicad` entry point, leaving test stubs
  untouched. Hermetic tests prove both behaviors. The separate one-request
  capability probe and explicit throttle classification remain open.
- completion evidence required: mocked old-UA 403/new-UA 200, mid-batch 403
  after successful fetches, recovery after declared cooldown, permanent 403
  and cache-only replay; production journal reports compatibility failures,
  throttled time and useful fetch time separately.
- history: 2026-08-12 — compatibility wrapper and selection tests landed after
  upstream issue #191/PR #190 identified the same User-Agent failure class;
  live C124196 then fetched successfully through the wrapper before burst
  throttling reappeared.

## IMP-053 — explicit catalog values outrank MPN-shape heuristics

- status: completed
- observed: USB Hub 3S v4 C23 source substitution, 2026-08-12
- evidence: the cheap source gate interpreted Panasonic MPN `16SVPF180M` as
  18 pF before consulting the repository's exact LCSC-code ledger, which
  correctly records C136277 as 180 uF. The rebuild stopped safely in 16.6
  seconds before TSX/KiCad generation, but the finding was false: a generic
  ceramic-value decoder had claimed authority over an electrolytic family.
- implemented: `bom_source_check.py` now gives an exact LCSC-code ledger value
  precedence over a value guessed from an MPN. Its ceramic decoder explicitly
  refuses Panasonic OS-CON `SVP*`/`SEP*` families rather than inventing a
  capacitance. A regression fixture proves `16SVPF180M` resolves to 180 uF and
  not 18 pF; the focused source suite passes 29/29 with two environment skips.
- general rule: measured, part-specific and code-specific records outrank
  syntax heuristics. A heuristic may fill an otherwise unknown field; it may
  never override an explicit authority, and an unrecognized family must be
  `UNKNOWN` rather than a plausible-looking number.
- history: 2026-08-12 — fixed at the first false pre-generation stop and
  replayed through the complete v4 source/electrical gate set.

## IMP-054 — generated reports must persist the final adjudicated state

- status: completed
- observed: USB Hub 3S v4 JLC digital twin, 2026-08-12
- evidence: `jlc_twin.py` correctly applied two evidence-backed library-absence
  adjudications in memory and exited zero, but had already written
  `twin_report.csv`. The durable CSV therefore retained transient
  `FETCH-FAILED` rows while the console reported success, and its footer still
  told the operator to retry absences already proven genuine.
- implemented: the report is now written only after adjudications have been
  applied. Its rows carry `ADJUDICATED-FETCH-FAILED`; resumable/retry guidance
  is printed only for still-unresolved statuses, while genuine library
  absences receive a distinct non-retry explanation. A regression fixture
  reads the emitted CSV, not merely the process exit code; the twin suite
  passes 34/34.
- general rule: every durable artifact is a serialization of the final state
  consumed by the verdict. If normalization, waivers or adjudication happen
  after collection, report generation must be the last pure step and tests
  must reopen the report from disk.
- history: 2026-08-12 — fixed before release staging; the v4 twin report was
  regenerated and now agrees with its successful console verdict.

## IMP-055 — register exact 3D model attachment geometry before placement freeze

- status: implementing
- observed: USB Hub 3S v4 and Pluto RX2 8-way v5 JLC digital twins,
  2026-08-12 through 2026-08-14
- evidence: the final twin mounts 71 of 75 placed bodies. JLC's current library
  has no usable exact 3D body for four deliberately hand-soldered connectors:
  the upstream USB-C power input and three USB-A outputs. Their footprints,
  mechanical drawings, pin identities and courtyards are independently
  reviewed, but the digital twin cannot prove their shell height or enclosure
  interference. Discovering this only after routing makes a package swap
  disproportionately expensive.
- follow-up evidence: Pluto RX2 8-way v5 named KiCad 10's exact GCT USB4105
  STEP in J1's footprint and `kicad-cli pcb render` exited successfully, yet the
  resulting image contained bare J1 lands because `${KICAD10_3DMODEL_DIR}` did
  not resolve in that headless process. Visual inspection caught the missing
  body before routing; a project-local hash-bound copy referenced through
  `${KIPRJMOD}` rendered correctly. Availability on disk and a plausible model
  path therefore do not prove render-time body coverage.
- follow-up evidence: Pluto RX2 8-way v5's first SMA render showed complete
  plated holes beside every connector even though the exact Amphenol footprint
  and all nine mating-face datums were dimensionally correct. The converted
  EasyEDA WRL had lost the native model's XY registration; swapping only to the
  native exact-code STEP put all four legs under the body without changing one
  pad or anchor. A rendered body count would still have passed this defect: the
  body existed, but it was in the wrong coordinate frame.
- decisive evidence: the v0.1.2 Pluto twin then produced a visually plausible
  green/magenta overlay after `mount_anchor` removed the 1.796-mm repeated-pad
  centroid error. That result was still not physical registration evidence:
  the renderer drew the internally misregistered converted JLC WRL and the
  analytic expectation was derived from that same WRL. They agreed with each
  other while disagreeing with the footprint and native exact-code STEP. An
  independent native-STEP render disagreed with the WRL-derived expectation by
  about 4.05--4.10 mm in body centre and 1.54 mm in outward extent. For J2,
  the converted-WRL body also missed the signal-pad centre and protruded about
  3.4 mm beyond two non-mating courtyard edges. The current v0.1.2 overlay is
  therefore a renderer self-consistency witness, not an approved mechanical-
  registration witness, and must be superseded before release evidence relies
  on it.
- root cause: the pipeline treated three distinct claims as one. `P-MODEL`
  proves that a model token resolves and produces a non-empty body.
  `A-RENDER` proves that final pixels agree with the mounted model and camera.
  Neither proves that the model's internal mechanical frame agrees with the
  footprint, physical attachment field or manufacturer datum. The existing
  catalog `MODEL-REG` bounding-box comparison is not sufficient for
  asymmetric or edge-mounted bodies, and a subjective asymmetry waiver can
  hide an origin error.
- refactor decision: retain `P-MODEL` as the model-availability gate and
  narrow `A-RENDER` to renderer fidelity. Add an independent
  `P-MODEL-REG` gate for physical model-to-footprint registration. The
  authority used to form the registration expectation must not be the same
  converted mesh under test. A pass in one gate must not be described as a
  pass in either of the other two.
- registration authority order: prefer the exact manufacturer's native STEP
  plus mechanical drawing; then a provenance-bound, previously registered
  package model; then a datasheet-derived body envelope and attachment datums.
  A catalog or converted WRL is a candidate/comparator, not the authority when
  it conflicts with native CAD or the drawing. Native STEP and converted WRL
  must receive separate hashes and separate receipts because conversion may
  change the internal origin while preserving a plausible body.
- intended landing point: after exact part selection and before placement,
  create one disposable origin-centred coupon for every unique
  `(footprint hash, model hash, transform)` tuple. Render bare top, populated
  top, front, side and isometric views with standardized scale and colours.
  Overlay pad copper, drill centres, courtyard/fabrication outline, model
  silhouette and declared physical landmarks. Emit numerical residuals and a
  human-readable registration card; approve it once and cache it by the tuple
  hash. Repeated instances on a board reuse that receipt, while any footprint,
  model or transform change invalidates it automatically.
- landmark contract: mechanically significant parts declare semantic anchors
  appropriate to the package, such as unique signal/reference pad, required
  attachment holes or lead centres, mating axis, body datum, polarity marker
  and permitted mating-edge overhang. Courtyard containment is the default;
  exceptions name the permitted edge and limit rather than waiving the whole
  comparison. Simple SMD packages may use body/lead overlap defaults, while
  asymmetric connectors require explicit drawing- or native-CAD-derived
  landmarks.
- diagnostic contract: every failure prints the complete transform stack
  (`model internal -> model scale/rotation/offset -> footprint local -> board
  -> camera`), the first failing landmark and its signed delta. Classify the
  result as `MODEL-MISSING`, `MODEL-WRONG-SOURCE`, `MODEL-INTERNAL-ORIGIN`,
  `MODEL-TRANSFORM`, `FOOTPRINT-DRAWING-MISMATCH` or `RENDER-CAMERA`; produce
  one focused coupon image and report instead of repeatedly rerendering the
  complete board.
- pipeline ownership: part freeze resolves and registers each unique critical
  model; placement permits only approved registration tuples; whole-board
  rendering checks instance rotation, mating direction and camera fidelity;
  the JLC twin compares manufacturing catalog geometry without overriding the
  approved mechanical model. Release requires registration receipts for all
  height-, polarity-, mating- or enclosure-critical references in addition to
  `P-MODEL` and `A-RENDER` receipts.
- relation to other improvements: IMP-093 remains responsible for retaining
  repeated physical pads and comparing their numbering-free geometry. Its
  `mount_anchor` can establish a rigid catalog-to-footprint transform, but it
  cannot certify a mesh's internal model origin. IMP-029 remains responsible
  for bounded catalog-model acquisition and caching; it must feed, not close,
  `P-MODEL-REG`.
- minimal implementation: a `pcb_model_register`-style command may initially
  use 2D silhouettes plus explicit human-authored attachment landmarks; full
  STEP feature recognition is not required. It writes a Markdown/HTML index
  with one row per unique tuple, source and hashes, transform, landmark/body/
  courtyard deltas, verdict and links to the standardized images. A single
  human approval is reusable only while all tuple hashes remain unchanged.
- partial implementation: `model_coverage_check.py` now independently reopens
  the saved board before modeled placement review and requires a renderer-
  resolvable non-empty body for every fitted, non-DNP, non-board-only
  footprint. The canonical full/reuse rebuild templates run it and persist the
  deterministic `model_coverage.json` report. `floorplan.yaml` may source-bind
  a package-correct file through `placement.patterns[].model_override`; the
  generator preserves the library model transform and refuses missing or
  ambiguous overrides. The clean fixture passes 22/22 and the known-bad
  removes its model after generation and fails 0/22. Pluto RX2 8-way v5 passes
  29/29 with eight provenance- and digest-pinned official KiCad package-model
  files covering 17 fitted refs.
- implementation progress: `model_registration_gate.py` and
  `native_model_registration.py` now provide the first reusable blocking
  `P-MODEL-REG` channel. A schema-1 project contract binds critical refs to an
  exact native-model SHA and numeric tolerances. The gate renders the exact
  board and a same-camera bare board, measures native-model pixels, and
  independently compares them with F.Fab, F.CrtYd, and every drilled
  attachment-pad centre. Its diagnostic overlay makes the transform channels
  visually distinct: orange courtyard, green expected F.Fab, pink measured
  native pixels, cyan attachment field, and blue board edge. The canonical
  full/reuse drivers run it before placement review. Pluto J2-J10 pass 9/9
  instances and 45/45 drilled centres; the prior converted-WRL self-pass is no
  longer accepted as the placement A-RENDER receipt.
- implementation progress: 2026-08-15 — the gate now constructs a compact,
  origin-centred coupon for every unique declared registration group and
  caches its accepted evidence by canonical hashes of the footprint
  registration datums, exact native model, model transform, numeric contract
  and checker identity. A verdict-free `model_registration_receipt.json`
  records measurements and images; a strict `model_registration.stage.json`
  owns PASS/FAIL. Per-group tuple bundles preserve a prior accepted pass and
  retain failed diagnostics, while one aggregate transaction binds their
  manifest hashes to the outer stage run/subject for receipt-derived
  readiness. Tests cover clean/cache reuse, two distinct groups, duplicate-ref
  denominator inflation, transform invalidation, the historical 5-mm shift,
  and a custom output location. The full Pluto nine-SMA canary passes 45/45
  drilled centres.
- implementation progress: 2026-08-16 — the USB-controlled debug hub bound
  eight exact source-owned STEP files through structured
  `model_override: {file, offset, scale, rotate}` declarations and reached
  independent saved-board body coverage of 133/133. Its registration contract
  then graded the four USB-A receptacles, upstream USB-B receptacle and power
  terminal against manufacturer-derived F.Fab, courtyard and 32 drilled
  attachment centres before routing. That run caught a genuinely translated
  Phoenix terminal body, a too-small USB-B courtyard, and a detector that had
  reduced multipart STEP bodies to the connected pixel island nearest the
  expected centre. After correcting all three classes, P-MODEL-REG passes 3/3
  unique tuples; presence and registration remain separate claims.
- follow-up evidence: the same board's later TPS259474L aggregate-eFuse change
  introduced a new exact custom footprint whose courtyard ended at the 2.0 mm
  body while its HotRod lands reached about 2.42 mm. It also referenced a
  generic 0.50-mm-pitch stock QFN model and was absent from the registration
  denominator. Electrical gates stayed green; the independent pre-route lens
  stopped placement. The fix enlarged the courtyard around the actual copper,
  added an independent F.Fab outline, replaced the generic body with the exact
  C2864845 RPW 0.45-mm-pitch STEP, and enrolled U_AGG as the fourth measured
  registration group. This is direct evidence that registration coverage must
  follow newly introduced custom/model-bearing footprints, not remain a static
  list inherited from the first placement pass.
- implementation progress: 2026-08-16 — P-MODEL-REG now selects a closed,
  tuple-bound `registration_datum` per group: `drilled_centres` remains the
  connector default, while `all_pad_centres` gives SMD packages a non-vacuous
  physical denominator. The exact TPS259474L coupon measures 0.010 mm body/
  F.Fab centre delta, zero body excursion beyond F.Fab/courtyard, and 10/10
  pad centres inside the native body. `tests/t1_model_registration.py` passes
  7/7, including a red fixture proving that an SMD-only subject still fails
  under the undeclared/default drilled-centre policy.
- implementation progress: 2026-08-16 — the live USB-controlled debug hub now
  reaches placement review with 139/139 renderer-resolvable fitted bodies and
  P-MODEL-REG passing 4/4 exact registration groups: 24 USB-A drilled centres,
  6 USB-B drilled centres, 2 power-terminal drilled centres, and 10/10
  TPS259474L all-pad centres. The SMD tuple is therefore exercised in the
  canonical pipeline, not only in an isolated coupon.
- implementation progress: 2026-08-19 — connector representation closure now
  extends the existing orientation/twin flow as `P-MATE-REG`, without adding a
  lifecycle stage. `jlc_twin.py` automatically discovers every
  orientation-declared connector, preserves the approved native model on the
  source board, and writes a `connector-datum-receipt-v1` binding native and
  vendor model identities, vendor transform, access axis, F.Fab/vendor body
  envelopes and signed mating-side support delta. The typed failure is not in
  the generic adjudication allow-list. Replaying the exact debug-hub v2
  v0.1.1 twin produced the intended discrimination: all four USB-A connectors
  passed at +0.022 mm, while both USB-C representations failed at -2.000 mm
  against their 0.650-mm limit—the displacement visible in the user's image
  that pad fit, native P-ORIENT and an adjudicated bbox-centre warning had let
  through. A clean/known-bad regression pins both a datum-preserving swap and
  the recessed-model failure.
- remaining: polarity-marker projection, permitted-edge overhang schemas,
  native/drawing landmark classes beyond body/F.Fab/courtyard/drilled centres,
  repeated-pad-numbering geometry, wrong-drill, wrong-rotation and converted-
  origin fixtures, and a fail-closed coverage policy deciding which newly
  introduced project parts require a receipt. At minimum, a project-local
  custom footprint carrying a project-local model may not reach placement
  unless it is explicitly registered or has an evidenced non-critical
  disposition. Full semantic STEP feature recognition remains out of scope. Body
  coverage, `mount_anchor`, catalog bounding boxes and same-mesh pixel
  agreement must still never close physical registration by themselves, so
  this entry remains implementing.
- completion evidence required: known-present, genuine-absent and transient
  model-resolution fixtures; correct body with wrong internal XY origin; right
  XY with wrong rotation; correct body with wrong footprint drills; repeated
  pad labels; a symmetric body with wrong polarity; a conversion that changes
  origin; and the shared-source self-consistency false pass reproduced by the
  Pluto WRL/native-STEP pair. The clean fixture must prove the receipt is
  reused for repeated refs, and any footprint/model/transform hash change must
  invalidate it before placement or release.
- history:
  - 2026-08-12 — recorded after the v4 twin made exact model coverage
    measurable; project-level dossier review exists, shared preflight remains
    open.
  - 2026-08-13 — extended after v5 proved render exit zero can coexist with an
    unresolved exact-model token and a missing connector body.
  - 2026-08-13 — extended after the v5 SMA image proved body presence alone
    does not catch a format-conversion registration error.
  - 2026-08-13 — implemented the independent fitted-body resolver gate,
    source-bound override, canonical stage wiring and red fixture; retained
    `implementing` because automated model registration is still open.
  - 2026-08-14 — refactored availability, renderer fidelity and physical
    registration into separate claims after the corrected Pluto twin exposed
    a shared-source false pass. Defined an independent, hash-cached per-part
    registration receipt as the remaining implementation target.
  - 2026-08-14 — landed the first reusable blocking native-model registration
    gate and wired it before placement review; Pluto's nine SMAs now have
    independent F.Fab/courtyard/45-hole evidence instead of a same-WRL pass.
  - 2026-08-15 — added origin-centred coupons, exact tuple receipts/caching,
    automatic invalidation, atomic per-group evidence, and an aggregate
    StageResult-bound bundle that passes the generic readiness composer.
  - 2026-08-16 — added structured source transforms, registered the new USB
    hub's three critical connector families before routing, and made native
    coupon measurement include disconnected STEP body islands.

## IMP-056 — population evidence must separate automated and manual bodies

- status: completed
- observed: USB Hub 3S v4 release audit, 2026-08-12
- evidence: the twin correctly broadened its mechanical population from 70 JLC
  CPL placements to 75 total installed bodies by adding five declared manual-
  install parts. Four manual connector models were genuinely absent, so its
  honest aggregate was 71/75. `policy_audit.py` then called that aggregate
  "CPL placements" and failed A-BODY, even though the actual JLC population was
  70/70. The producer and consumer were each locally reasonable but disagreed
  about the denominator's meaning.
- implemented: `missing_models.txt` now persists three counters: aggregate
  bodies, `CPL bodies mounted`, and `manual bodies mounted`. A-BODY grades the
  contractual CPL counter when present while the aggregate/manual deficits
  stay visible for mechanical review and first-article disposition. Historical
  reports fall back to the old aggregate format. Twin and policy known-bad
  fixtures prove an empty-CPL/manual-body case and a 2/2-CPL plus 0/1-manual
  case independently.
- general rule: when a verification population is a union of sets owned by
  different processes, persist every constituent denominator. Never make a
  consumer infer "placed", "assembled" or "installed" from one aggregate.
- history: 2026-08-12 — completed before v4 release staging; current evidence
  states aggregate 71/75, JLC CPL 70/70, manual 1/5.

## IMP-057 — validate a relocated release archive in its own dependency context

- status: implementing
- observed: USB Hub 3S v4 release staging, 2026-08-12
- evidence: the live project passed exact KiCad DRC at 0 violations,
  0 unconnected items and 0 schematic-parity findings. The first DRC run over
  the copied `07_releases/.../source/` board instead reported three
  `lib_footprint_issues`: its release-only `fp-lib-table` shadowed KiCad's
  complete `Package_SON` library with an incomplete one-footprint directory,
  so U4-U6 could not resolve `Texas_DRC0010J`. A live-project validation could
  never expose that packaging defect because it resolved the system library.
- implementation progress: the v4 staging archive now maps `Package_SON` the
  same way as the live project and reruns DRC from the relocated source tree.
  The archived board passes 0/0/0 and its SHA-256 is byte-identical to the
  frozen routed board. The result is shipped as
  `verification/standalone_archive_drc.json`.
- intended landing point: promote relocated-source validation into the shared
  release gate. After copying source and rewriting any project-local library
  paths, run KiCad DRC/parity from inside the staged archive, reopen the JSON,
  require all three finding sets to be empty, and check the staged board hash
  against the live frozen board. Also enumerate every `lib_id` used by the
  board and prove its footprint resolves under the staged `fp-lib-table`;
  copied but unused libraries must not create false confidence.
- completion evidence required: known-bad fixtures for an absent library, an
  incomplete same-name library that shadows a valid system library, and a
  relocated custom-library path; a clean fixture must prove both exact board
  identity and zero standalone findings.
- history: 2026-08-12 — project-level read-back landed during v4 staging;
  shared release-contract promotion and hermetic fixtures remain open.

## IMP-058 — multi-format evidence is one atomic result, not adjacent files

- status: proposed
- observed: USB Hub 3S v4 release staging, 2026-08-12
- evidence: the staged `stock_check.json` and `stock_check.txt` carried the
  accepted C23 substitution C136277 / 16SVPF180M, but `stock_check.csv` still
  carried rejected C369910 / 160AV5K181M0606C. A-STOCK passed because release
  freshness correctly reads the canonical JSON; M-DEPEND then exposed that
  C136277 had no release-internal CSV resolver and was passing only through
  the mutable live `02_parts/16SVPF180M` dossier. Each file looked valid in
  isolation and all three shared a basename, which made adjacency appear to be
  provenance.
- project correction: reran `jlc_stock_check.py` once against the current
  strict 40-line BOM with `--out` and `--json` in the same process, capturing
  stdout as the text form. The new CSV/JSON/text set agrees on every code; live
  stock remains PASS 40/40 and C136277 reports 1052 catalog units.
- intended landing point: every producer that emits several representations
  writes them into a temporary result directory with one run ID and one input
  hash, validates pairwise key-field equality, then atomically promotes the
  complete set. Release staging copies the declared bundle, never three
  independent globs. A release gate must cross-check the exact LCSC set and
  core facts across BOM, stock JSON, stock CSV and text; a canonical form may
  decide the verdict, but disagreement in a secondary form still fails the
  archive.
- completion evidence required: known-bad mixed-generation JSON/CSV, missing
  member, duplicate code and current-code/old-MPN fixtures; a clean producer
  run must reopen all written files and prove the same input hash, row set and
  verdict before promotion.
- history: 2026-08-12 — v4 archive corrected before seal; shared atomic-bundle
  writer and cross-format release gate remain open.

## IMP-059 — preflight the publication parser's review identity before seal

- status: implementing
- observed: USB Hub 3S v4 publication gate after v0.6.0 seal, 2026-08-12
- evidence: all four routed reviews were exact-board/hash-bound and SOUND, and
  release freshness graded both required red-team verdicts. Publication still
  rejected three reviews because their `subject:` values said `USB Hub 3S v4`
  rather than containing the repository's exact slug `usb-hub-3s-v4`. The pin
  review happened to use the slug and passed. Review quality was not the
  defect; a machine identity field had been left encoded as human prose and no
  pre-seal gate exercised the downstream parser.
- project correction: preserve immutable v0.6.0 and obtain three append-only,
  independent exact-board publication reseals with canonical subjects. Seal a
  docs-only v0.6.1 successor whose fab/source/3d trees are byte-identical and
  whose named review files are verbatim copies of those append-only records.
- intended landing point: add a pre-seal review-header gate shared with
  `pcb_publication_gate.py`. Require a dedicated canonical `project:` slug or,
  until that schema lands, require the exact project slug inside `subject:`.
  It must also grade verdict vocabulary, full source-commit syntax, board hash,
  required lens coverage and archive byte identity against the staging release
  before immutability begins. Review commissions should receive the exact
  header block as structured input rather than translating a display name.
- completion evidence required: spaced-display-name/slug mismatch,
  wrong-neighbour project, missing subject, malformed commit, stale board hash
  and untracked-review fixtures; the pre-seal and publication readers must
  import one parser and return the same finding IDs.
- history: 2026-08-12 — narrow independent publication reseals commissioned;
  docs-only v0.6.1 correction in progress, shared pre-seal parser still open.
- history: 2026-08-14 — Pluto RX2 8-way v5 repeated the same exact-slug
  failure on two otherwise SOUND, hash-bound reviews because the mutable
  release staging path still did not call the publication parser. Preserve
  immutable v0.1.0 and correct the identity fields through a strict docs-only
  v0.1.1 successor; this is additional evidence that the shared pre-seal
  parser is required, not a project-specific convention.

## IMP-060 — publication must replay the release's declared freshness mode

- status: completed
- observed: USB Hub 3S v4 v0.6.1 docs-only staging, 2026-08-12
- evidence: `release_freshness_check.py` already had the correct strong mode
  for this correction: `--docs-only-supersede` asserts that every file under
  `fab/`, `source/` and `3d/` is byte-identical to the named predecessor while
  requiring release documents to differ. `pcb_publication_gate.py` discarded
  that release shape and always invoked ordinary freshness, where identical
  fabrication/PDF artifacts are deliberately treated as stale. Therefore a
  legitimate docs-only release could pass its normative seal gate and be
  structurally unable to pass publication.
- implemented: a superseding MANIFEST now declares `release_mode: docs-only`
  and an exact sibling directory in `supersedes:`. The publication wrapper
  parses those fields and composes the existing docs-only freshness mode. It
  fails closed on an unknown mode, a path-shaped predecessor, a missing
  predecessor or self-reference; a release with no mode retains ordinary
  freshness. The wrapper does not reimplement the identity comparison.
- completion evidence: `tests/t1_publication_gate.py` now proves the clean
  composition and the known-bad missing-predecessor refusal; 8/8 publication
  tests pass. V4's v0.6.1 gate additionally asserts the real 20-file fab,
  17-file source and one-file 3D trees against v0.6.0.
- general rule: an orchestration layer that composes a parameterized gate must
  preserve the subject's declared mode. Calling the same executable with
  weaker/default arguments is not composition; it is a different predicate.
- history: 2026-08-12 — completed before v0.6.1 seal.

## IMP-061 — exact-code manufacturing readiness before part freeze

- status: partially implemented
- observed: USB Hub 3S v4 nine-hour pipeline retrospective, 2026-08-12
- evidence: fabrication entry found four classes of fact after routing that
  were already properties of the selected exact LCSC codes. F1, J1-J4 and SW1
  were in the SMT CPL despite having drilled pads, no paste and catalog
  `assemblyComponentFlag=false`; C29 and C30 needed current-stock substitutes;
  C23's selected code had no usable supplier CAD record; and the first strict
  export lacked rotation authority for 22 placements over 16 codes. The board
  could remain copper-identical, but each late discovery forced source,
  evidence, schematic or review replay.
- intended landing point: after electrical qualification of a candidate and
  before the part is frozen into the schematic, run one bounded exact-code
  manufacturing-readiness gate. For every fitted ref/code it records:
  exact-code resolution and observation date; current stock evidence;
  JLC assembly eligibility; population class (`jlc_smt`, `manual`,
  `consigned`, or `dnp`) and its `assembly.yaml` disposition; supplier
  symbol/footprint/body state (`AVAILABLE`, `ABSENT`, or `TRANSIENT`);
  polarity; and rotation-authority readiness for every automatically placed
  package. No field may silently default from pad shape, package family or a
  neighbouring catalog code.
- pass semantics: mutable stock is a dated risk observation, not a permanent
  design fact. A genuine model absence or non-JLC part may pass only with an
  explicit mechanical envelope/local-model fallback and manual/first-article
  obligation. `TRANSIENT` never becomes `ABSENT`, and an automatically placed
  part without exact rotation authority remains unready.
- relationship: this composes the early portions of IMP-052 and IMP-055 with
  population and rotation readiness. It does not replace the final placed-
  board twin, same-day stock check or JLC uploader allocation check.
- completion evidence required: fixtures for stocked SMT/model-present,
  manual THT, genuine no-model with approved fallback, throttled catalog,
  missing rotation, and a code changed after preflight; both schematic and
  placement entry must refuse a stale or incomplete readiness record.
- history: 2026-08-12 — proposed from the nine-hour retrospective because the
  05:31-07:22 fabrication backtracks were cheaper to prevent at part freeze.
- follow-up evidence: Pluto RX2 8-way v5 independently checked all 13 JLC/LCSC
  codes and recorded distributor observations, but did not produce the
  contract-required composed Q-2SOURCE verdict before declaring exact-part
  closure. The 10V 4.7uF capacitor's recorded independent pool had zero local
  stock, and the 16V input capacitor recorded an exact listing without a
  qualifying stock count; neither prose entry can prove two active/orderable
  pools. The dossiers also committed `jlc_observed_stock` and second-source
  stock prose even though the parts contract assigns volatile stock/price only
  to TTL cache and dated generated sourcing evidence.
- completion evidence extension: schematic entry must consume one generated,
  parseable Q-2SOURCE/Q-COVER verdict for the exact candidate-BOM hash and
  board count. A dossier linter rejects volatile quantity/price fields, and a
  second-source identity with absent or insufficient stock remains a FAIL, not
  a narrative qualification. Candidate-BOM, assembly population and dossier
  code sets must be derived or checked for exact identity rather than maintained
  as three ungoverned lists.
- follow-up result: v5's first composed run failed 3/13. Removing the already
  rejected 10-V capacitor dossier, consolidating C1-C3 on the qualified 16-V
  code and adding current exact DigiKey product-page observations produced a
  parseable 12/12 Q-2SOURCE pass. Volatile stock prose was removed from all
  retained dossiers. This repairs v5 but does not yet implement the generic
  candidate-BOM hash/set-identity gate.
- diagnostic follow-up: in composed-pool mode the shopping tool still prints
  `FAIL NO-QUOTE` for non-required distributors (especially Amazon) before its
  final 12/12 PASS. Preserve each pool's coverage details, but label unavailable
  optional pools as diagnostics rather than gate failures so a successful
  composite verdict is not visually contradictory.
- implementation progress: 2026-08-17 —
  `manufacturing_readiness.py --phase selection` now composes exact per-ref
  JLC/manual disposition, exact-MPN dossier identity, dossier/source-code
  agreement and the existing source-value gate into one hash-bound receipt;
  the canonical rebuild calls it before board generation. `--phase order`
  separately composes population, strict realized part facts and order-time
  sourcing against release bytes. Stock/model/rotation/two-source readiness at
  initial part choice is still outside this receipt, so IMP-061 remains partial.
- implementation progress: 2026-08-20 — accepted `prelayout` readiness can now
  atomically publish a typed `S-PART-FREEZE` bundle/result, and both canonical
  drivers exercise it in shadow mode before placement. This closes the common
  lifecycle seam but not the remaining model/rotation/two-source predicates.

## IMP-062 — transactional generated-artifact bundles

- status: implementing
- observed: USB Hub 3S v4 nine-hour pipeline retrospective, 2026-08-12
- evidence: a KiCad render printed usage, exited zero and left an old PNG in
  place; stock JSON/TXT described C136277 while the adjacent CSV still
  described rejected C369910; and the twin CSV was initially written before
  adjudication even though the final in-memory verdict passed. These are one
  failure family: directory presence and process exit were mistaken for a
  coherent result.
- intended landing point: provide one shared producer transaction used by
  review exporters, catalog evidence, twins and release staging. It receives
  an input hash, producer command/version and declared expected outputs;
  writes into a new temporary result directory; requires every output to be
  newly created, non-empty and parseable; applies normalization/adjudication;
  reopens the durable files; compares key fields across representations; and
  atomically promotes the whole bundle with one run ID and completion time.
  Partial or failed attempts remain diagnostic workspaces and can never
  replace the current accepted bundle.
- relationship: this is the reusable mechanism needed to finish IMP-050 and
  IMP-058 and generalize IMP-054. Those incident-specific entries remain the
  acceptance cases; this entry owns the common transaction boundary.
- completion evidence required: known-bads for usage-plus-exit-zero with an
  old file, zero-byte output, missing bundle member, mixed-generation CSV/JSON,
  post-write adjudication and interrupted promotion; a clean fixture must
  prove atomic replacement and identical run/input identity in every member.
- history: 2026-08-12 — proposed from the nine-hour retrospective as the
  common fix for three apparently different release-evidence defects.
- history: 2026-08-12 — the shared schema-1 primitive and focused clean/bad
  fixtures landed in shadow form. It uses fresh sibling staging, a strict
  declared-output census, durable parse/read-back, manifest-last serialization
  and atomic directory promotion while preserving any accepted bundle on
  failure. Adoption by real producers and retained failed diagnostic
  workspaces remain open, so this entry is not complete.
- implementation progress: 2026-08-15 — `fab_payload_census.py` is the first
  real producer to adopt the primitive through an opt-in `--bundle` path. It
  declares the board, Gerber and rule inputs; publishes reopened JSON and
  human-text evidence with one manifest; cross-checks their durable verdict;
  preserves the prior accepted bundle; and retains failed bytes in a sibling
  workspace with no `bundle.json`. Legacy stdout and `--json` behavior remain
  unchanged. Stock evidence is the next bounded migration, followed by a
  shared routed-review exporter, then the JLC twin after its resumable cache is
  separated from accepted evidence, and finally release staging after its
  upstream producers are transactional. This entry remains implementing.
- implementation progress: 2026-08-20 —
  `pipeline_stage_evidence.py` is the small common adoption adapter for domain
  measurements. Manufacturing readiness, electrical closure, and placement
  feasibility now use the same fresh-bundle/reopen/atomic-promote/StageResult
  seam with focused clean and known-bad fixtures. Broader producer migration
  remains incremental, so the shared primitive is retained rather than copied.

## IMP-063 — complete pre-seal release rehearsal

- status: partially implemented
- observed: USB Hub 3S v4 nine-hour pipeline retrospective, 2026-08-12
- evidence: mutable staging exposed an incomplete `Package_SON` library only
  when DRC ran in the relocated archive; cross-format read-back then exposed a
  stale stock CSV; after v0.6.0 was immutable, publication rejected three
  human display-name subjects that did not carry the canonical project slug;
  and the v0.6.1 attempt showed that the publication wrapper discarded the
  declared docs-only freshness mode. The first two were caught before seal,
  while the latter two unnecessarily required a superseding release.
- intended landing point: add one canonical rehearsal command over the fully
  populated but still mutable release staging directory. It must run from the
  relocated `source/` dependency context; resolve every used footprint;
  reopen DRC/parity and every generated report; cross-check BOM, CPL,
  population and stock code sets; validate expected-output/hash manifests;
  parse review identity, verdict, commit, board hash, lens coverage and archive
  byte identity with the exact parser imported by publication; and replay
  freshness using the MANIFEST's declared release mode and predecessor.
- boundary: the rehearsal exercises every publication predicate that can be
  known from project and staging bytes. The final diff-aware repository
  publication gate still runs after the seal because source ancestry,
  candidate-head selection and branch protection are genuinely post-seal
  facts. Passing rehearsal is not permission to skip that boundary.
- relationship: this composes the shared completion work in IMP-057,
  IMP-058 and IMP-059 and consumes the mode preservation completed by
  IMP-060. It must reuse their readers rather than reimplement them.
- completion evidence required: replay the original v0.6.0 display-name
  mismatch as a pre-seal known-bad; fixtures for footprint-library shadowing,
  stale secondary evidence, malformed review identity, wrong board hash,
  missing predecessor and unsupported release mode; a clean staged initial
  release and docs-only successor must both pass before a seal commit exists.
- history: 2026-08-12 — proposed from the nine-hour retrospective to make
  inexpensive metadata and packaging findings cost a staging edit, not an
  immutable supersede.
- history: 2026-08-14 — Pluto RX2 8-way v5 passed its lower-level release and
  freshness gates but post-seal publication rejected a prose value in the
  reserved `release_mode` field, two non-canonical review subjects and a
  material BRIEF edit after the stamped source commit. All were knowable in
  mutable staging. This recurrence promotes the rehearsal from an efficiency
  improvement to a required release-safety control; implementation remains
  open.
- implementation progress: 2026-08-17 — `release_rehearsal.py` now creates a
  non-overwriting DRAFT/DO-NOT-ORDER manifest skeleton, grades required content,
  design/sourcing freshness and the publication contract against an explicit
  mutable staging directory, and emits seal admission only while every staged
  byte still matches the accepted receipt. Full clean initial/docs-only staging
  fixtures and final manifest-field replacement remain open, so IMP-063 is
  partial rather than complete.

## IMP-064 — early warning plus late authoritative recheck

- status: implementing
- observed: USB Hub 3S v4 nine-hour pipeline retrospective, 2026-08-12
- evidence: moving every check earlier would reduce rework but would be unsafe
  if the early observation were treated as permanent authority. Supplier
  stock and APIs change; placement changes body interactions; routing changes
  realized via/copper capacity; release copying changes dependency resolution;
  and publication depends on the final repository delta.
- intended landing point: declare lifecycle pairs for mutable or realized
  facts. The early member prevents expensive downstream work; the late member
  authorizes the final claim. At minimum:
  - exact-code stock at part selection, then same-day uploader/allocation check;
  - model availability before placement, then full placed-board twin;
  - declared via/process/current boundaries before routing, then exact-board
    process census and series-transition measurement;
  - generated-output postconditions at production, then release-bundle
    manifest/read-back;
  - canonical review headers at commission and staging, then the final
    repository publication gate;
  - live-project DRC during design, then relocated-archive DRC before seal.
- schema requirement: each pair names the fact owner, observation timestamp or
  immutable subject hash, maximum useful age where applicable, the stage it
  blocks and the later authoritative recheck. An early pass cannot satisfy a
  later claim; a late failure points back to the earliest causal stage.
- completion evidence required: orchestration fixtures prove all early checks
  precede expensive consumers and all late checks remain present; a stale
  stock observation, post-placement model mismatch, realized via shortfall and
  post-seal publication mismatch must each fail at their proper boundary.
- history: 2026-08-12 — proposed from the retrospective to codify "shift
  left, do not weaken the final gate."
- history: 2026-08-12 — the schema-1 fact-pair core landed with semantic/raw
  identities, exact invalidator census, optional early freshness and explicit
  prevention/authority roles. Early PASS is structurally unable to authorize
  a final claim; late evaluation accepts no early result and only the declared
  current authority can authorize. Real stock/model/via/release adapters and
  orchestration placement remain open, so this entry is not complete.
- follow-up evidence: Pluto RX2 8-way v5 had two honest source-authority
  exceptions at part freeze: Amphenol's current drawing endpoint returned HTTP
  403, and the locally cached STM32 data sheet was Rev 4 while current online
  facts were cross-checked against Rev 5. Prose correctly deferred footprint
  and release authority, but no typed lifecycle record made those precise
  future blockers visible to orchestration.
- lifecycle extension: manufacturer-document authority uses an early/late
  pair too. Part selection may record `CURRENT`, `STALE`, or `DEFERRED` with
  exact document identity, retry budget, fallback grade and first blocked
  stage; footprint approval and pin review require hash-bound local authority,
  and release rechecks the current revision. Repeated fetch failure is a
  visible bounded state, never an unbounded retry and never an implicit pass.
- implementation progress: 2026-08-17 — exact-code selection now has a
  separate order-phase authority; configured-via entry now has an exact
  saved-board aspect census; and mutable staging now has a separate final
  publication rehearsal. These are real early/late pairs. Stock age, model
  authority and all producer bundle pairs are not yet migrated, so IMP-064
  remains implementing.

## IMP-065 — critical-path telemetry and cheap-first scheduling

- status: implementing
- observed: USB Hub 3S v4 nine-hour pipeline retrospective, 2026-08-12
- evidence: measured route races took about 9-10 seconds, canonical layout
  seals about 33-39 seconds and strict JLC export about 0.3 seconds. Human
  review dominated elapsed time, one review broadened scope without producing
  a witness, and the first digital-twin fetch took roughly eleven mostly
  silent minutes. The pipeline felt locked even though routing and local
  producers were healthy.
- intended landing point: every orchestration stage emits machine-readable
  spans with stage/gate name, immutable subject, work class (`local`,
  `network`, `backoff`, `review_wait`, or `operator_wait`), start/finish,
  elapsed time, cache hit/miss, result and resumable command. A stage summary
  reports the actual critical path separately from aggregate subprocess time.
  Within dependency constraints, schedule cheap static and deterministic gates
  before network work and human review. Never reorder a weaker check to stand
  in for a later authoritative one.
- relationship: IMP-049 owns reviewer closure, IMP-051 owns heartbeat/retry
  behavior inside long external operations, and IMP-014 owns progress-channel
  noise. This entry owns cross-stage timing and gate-order feedback so future
  boards can see where time was actually spent.
- completion evidence required: a deterministic orchestration fixture with
  overlapping local/network/review spans computes the right critical path;
  summaries distinguish productive fetch from backoff and reviewer wait; a
  template-order test proves source-only gates precede TSX, external fetch and
  independent review where their inputs permit.
- history: 2026-08-12 — proposed from the retrospective after measured timing
  showed that optimizing the router would not address the experienced delay.
- history: 2026-08-12 — schema-1 shadow infrastructure now records bounded
  stage execution with work-class/start/finish/elapsed/log evidence, and a
  dependency registry recomputes after each choice so newly unblocked cheap
  work precedes already-runnable network/review work. Real-stage declarations,
  cross-stage critical-path aggregation and canary shadow equivalence remain
  open, so this entry is not complete.
- history: 2026-08-12 — cross-stage aggregation now distinguishes observed
  wall envelope, summed stage work, subprocess work and the deterministic
  dependency-duration critical path, with separate local/network/backoff/
  review/operator totals and cache/status counts. Real-stage span adapters and
  USB Hub/Pluto shadow traces remain open, so this entry is not complete.
- history: 2026-08-12 — the first real legacy adapters landed in
  non-authoritative form: exact-driver-hash-bound stage catalogs, a pure
  completion observer and a dedicated-channel xtrace mapper. A detached
  disposable-worktree exercise measured USB Hub 3S v4 reuse failing
  diagnostically at pre-route review after about 11.4 seconds (41 trace
  records) and legacy Pluto RX2 8-way reuse failing at seven anchored courtyard
  overlaps after about 2.0 seconds (20 records). Neither run hung, but neither
  completed, so equivalence and any authority migration remain open. This
  legacy Pluto observation is not the Pluto RX2 8-way v4 sealed canary required
  by ADR-0008.
- history: 2026-08-12 — a repeat with absolute Bash source identities exercised
  the strict source-line adapter itself. USB produced a fully mapped 23-stage
  failure prefix (36 top-level trace records, no unmapped executable command)
  at the same review gate after about 14.3 seconds; Pluto produced a fully
  mapped three-stage failure prefix (15 top-level records, no unmapped command)
  at the same board-generation collision after about 1.3 seconds. This closes
  trace-map plumbing, not canary equivalence: the not-reached tails and both
  design blockers remain explicit.
- history: 2026-08-12 — after replacing the legacy Pluto bbox-only courtyard
  false positive with native polygon confirmation (IMP-066), a disposable
  reuse run observed all 12 catalog stages in 7.29 seconds. Stitch/fill was the
  longest stage at 3.798 seconds; the first honest stop is now the final
  postcheck at 45 DRC violations / 15 unconnected / 0 parity. This closes the
  legacy trace tail but not a green canary or shadow equivalence.
- history: 2026-08-12 — the distinct sealed-project Pluto RX2 8-way v4 reuse
  canary first exposed two cheap source-contract debts (explicit zero
  differential-pair applicability and provenance on 26 non-pin seed-via
  banks), then completed all 22 declared stages green in 139.91 seconds:
  DRC 0/0/0, fence coverage 22/22 and RF length coverage 8/8. During that run,
  stitch/fill reported useful pass progress while the 35.724-second CPWG solve
  was silent despite about 24-core utilization; that measured stage now owns a
  budget, deadline and heartbeat. This establishes one complete v4 legacy
  observation, not shadow-plan/result equivalence or authority migration.
- history: 2026-08-12 — after the bounded solver adapter landed, a final
  disposable reuse run completed all 22 stages green in 94.94 seconds with no
  unmapped command. The solver recorded 6.579 seconds, the configured 45/60
  second budget/deadline and a durable terminal state; the earlier 35.724-
  second measurement remains the conservative sizing observation.

## IMP-066 — native geometry must confirm broad-phase findings

- status: completed
- observed: legacy Pluto RX2 8-way reuse-canary replay, 2026-08-12
- evidence: the generator's anchored-courtyard gate reported seven collisions,
  but KiCad DRC reported zero courtyard violations. All seven transformed
  courtyard polygons are disjoint: the six radial SMA pairs have about
  1.140 mm clearance and `R_T2`/`R_T1` has about 0.350 mm, even though their
  axis-aligned bounding boxes intersect. Moving these reviewed anchors would
  have damaged an electrically-derived RF floorplan to appease an
  approximation.
- general rule: bounding boxes, raster extents and convex envelopes are useful
  broad-phase filters, never final collision evidence. A geometry gate may
  reject only after the authoritative tool's transformed native shapes confirm
  overlap or touch; diagnostics may still report the bounding-box window for
  localization. The same principle applies to rotated bodies, board outlines,
  keepouts, apertures and model-registration checks.
- implementation: `skills/kicad-pcb/scripts/generate_board_generic.py` now
  filters anchored pairs by bounding box and then grades KiCad courtyard
  polygons with `SHAPE_POLY_SET.Collide`. The PCB-design authoring guidance
  makes exact confirmation normative.
- completion evidence: `tests/t1_generate_board.py` regenerates the real Pluto
  floorplan and proves the exact seven pairs have intersecting boxes but
  non-colliding polygons. Existing known-bad fixtures still prove that a true
  same-coordinate or anchored-courtyard overlap fails loudly.
- history: 2026-08-12 — completed during the legacy canary blocker-removal
  wave; fresh board generation and the 13-measurement project audit both pass
  without a Pluto source edit.

## IMP-067 — scaffolds must never copy executable example values

- status: proposed
- observed: Pluto RX2 8-way v5 clean-room commission, 2026-08-12
- evidence: before any schematic existed, the new project's live rule files
  contained plausible executable examples for another board: a 3S-LiPo/
  LM5116 power tree, cook/load-cell netclasses and route target, a five-board
  assembly declaration, and unrelated electrical invariants. YAML parsing
  could not distinguish these examples from project decisions. A downstream
  command could therefore grade or act on coherent but foreign intent.
- general rule: examples belong in contracts, references, fixtures or files
  explicitly marked non-executable. A project initializer must emit only
  project identity plus null/empty fail-closed sentinels until commission or
  part selection supplies each value. No copied example row may become a live
  project declaration merely because it parses.
- intended landing point: refactor project scaffolding so each generated live
  YAML is produced from a minimal sentinel template; add a cheap pre-TSX
  provenance/content gate that rejects foreign project names, example markers,
  undeclared non-null design values and active rows without a local decision
  source. Keep full annotated examples in skill-owned reference files.
- completion evidence required: initialize two unrelated fixture projects and
  prove their live rule files contain no example MPN, net, board path,
  population quantity or invariant; inject one foreign active row in each
  rule family and prove the pre-TSX gate names it and fails; prove an explicitly
  source-linked local decision passes.
- recommendation: fix the initializer/process before the next new board. The
  v5 instance was cleaned immediately because leaving it in place could have
  contaminated later generation; no TSX/KiCad artifact had yet been created.
- history: 2026-08-12 — v5 power, protection, invariant, netclass, assembly and
  route files were replaced with project-specific fail-closed sentinels. The
  reusable initializer and generic rejection gate remain open.

## 2026-08-12 nine-hour retrospective traceability

This table records the complete shift-left review so the recommendations are
not recoverable only from chat or one project's journal. “Early” is the first
stage with enough information to reject or disposition the issue; the final
authoritative recheck remains governed by IMP-064.

| Observed issue | Earliest useful boundary | Canonical improvement |
|---|---|---|
| Manual/THT parts entered the SMT CPL | exact-code part freeze | IMP-061, with population reporting in IMP-056 |
| C23/C29/C30 stock or CAD suitability was discovered after routing | exact-code part freeze | IMP-052, IMP-055, IMP-061 |
| Rotation authority was first demanded by strict export | exact-code part freeze, confirm after placement | IMP-061 |
| Exact connector bodies were unavailable after routing | before placement freeze | IMP-055, IMP-061 |
| A promoted route inherited stale placement/via-process geometry | before placement review | IMP-040 |
| DRC-clean forced via banks lacked current capacity | architecture declaration, then realized route | IMP-041, IMP-064 |
| Type-VII intent was board-wide or not Gerber-addressable | manufacturing architecture before routing | IMP-039 |
| A generic MPN decoder overruled exact catalog value | static source preflight | IMP-053 |
| A renderer exited zero but left a stale PNG | artifact producer transaction | IMP-050, IMP-062 |
| Stock CSV disagreed with JSON/TXT | atomic evidence production and staging read-back | IMP-058, IMP-062 |
| Twin CSV disagreed with the final adjudicated verdict | final-state serialization before exit | IMP-054, IMP-062 |
| An independent reviewer widened scope for hours and wrote nothing | externally bounded review commission | IMP-026, IMP-049 |
| Release-only footprint-table shadowing broke standalone resolution | mutable relocated staging | IMP-057, IMP-063 |
| Human display name failed canonical publication identity | review commission and mutable staging | IMP-059, IMP-063 |
| Publication discarded docs-only freshness semantics | orchestration mode tests before seal | IMP-060, IMP-063 |
| Healthy stages appeared locked because work class was invisible | every orchestration boundary | IMP-051, IMP-065 |
| Parseable rule files failed canonical readers or passed with zero graded rows | source-only preflight before generation | IMP-001, IMP-045, IMP-069 |
| Hand-maintained stage booleans claimed completion without fresh gate receipts | every stage transition | IMP-069 |
| Two-source proof was distributed across prose and volatile stock was committed in dossiers | exact-code part freeze | IMP-061, IMP-064 |
| A broad clean-room search surfaced explicitly excluded legacy design material | commission and every discovery command | IMP-070 |
| A 500 ms marker followed by the same state for 5 ms is observably 505 ms | control-protocol lock before firmware and analysis | IMP-071 |
| Generated PDF evidence was treated as text because it contained no NUL byte | project scaffold and staging preflight | IMP-072 |
| A regulator calculation passed against a locally chosen operating ceiling mislabeled as a package limit | source-bound capture before power analysis | IMP-043, IMP-045 |
| Manufacturer documents were inaccessible or a locally cached revision was stale | source authority at part freeze, then final recheck | IMP-042, IMP-051, IMP-064 |

Recommended execution order for future boards:

1. Commission the product, manufacturing, qualification and clean-room
   boundaries; enforce the allowed discovery scope mechanically (IMP-070).
2. Close exact-code manufacturing readiness—including the composed
   two-source gate—before part freeze (IMP-061, IMP-064).
3. Run every applicable canonical source-only schema, bound and authority
   gate before TSX or reviewers, then derive stage readiness from their fresh
   receipts (IMP-001, IMP-042, IMP-045, IMP-053, IMP-069).
4. Generate and electrically grade the schematic, then run presentation
   preflights before bounded human readability review (IMP-044, IMP-046,
   IMP-048, IMP-049).
5. Generate placement, prove promoted-route/model compatibility, then run
   bounded placement review (IMP-040, IMP-055).
6. Route and remeasure realized copper, via process and ampacity; generate
   review evidence transactionally (IMP-039, IMP-041, IMP-062).
7. Build complete mutable staging and run the pre-seal rehearsal (IMP-063).
8. Seal immutably, refresh the beacon, then run the final repository-level
   publication gate and retain the external JLC/first-article order holds.

## IMP-068 — coordinate protection before freezing downstream voltage ratings

- status: proposed
- observed: Pluto RX2 8-way v5 exact-parts stage, 2026-08-13
- evidence: the initially selected protected-input capacitor was rated 10 V,
  while the exact SMBJ6.0A maximum clamp is 10.3 V before the required 20%
  coordination margin. The source-stage surge gate rejected it before TSX or
  schematic generation; replacing it with the exact 16-V code made the path
  pass with unchanged topology.
- general rule: a TVS selection and every part exposed behind it form one
  interface proof. Before an exact-code freeze, compare the source envelope,
  admitted waveform, series impedance/current limiting, TVS standoff and
  maximum clamp, PCB overshoot allowance, and every downstream recommended/
  absolute voltage rating—including capacitors. Nominal source voltage and TVS
  part name alone are insufficient.
- intended landing point: make the early protection-path gate a mandatory
  dependency of exact-code freeze, before TSX/symbol/footprint work. Diagnostics
  should name the weakest exposed part and show `clamp x margin` against its
  rating, then rerun automatically when that exact code changes.
- completion evidence required: fixtures proving rejection of a capacitor
  below clamp, a regulator below clamp, a waveform mismatch, and an omitted
  exposed part; a coordinated 16-V-capacitor path must pass. The same proof must
  remain mandatory in the later authoritative schematic/release rechecks.
- recommendation: generic process change soon; no v5 repair is pending because
  the existing early gate caught and corrected this instance before schematic
  entry.

## IMP-069 — derive stage readiness from canonical gate receipts

- status: implemented; project adoption opt-in
- observed: Pluto RX2 8-way v5 pre-schematic audit, 2026-08-13
- evidence: `requirements.yaml` and the project status described architecture,
  interface and exact-parts work as complete, while the canonical electrical-
  invariant and RF-contract readers rejected their files, the assembly reader
  raised an exception, the label-survival check passed vacuously with zero
  graded pin-map rows, and the project-state reader could not find the required
  findings ledger. The selected commands that had been run were green, but the
  declared stage was not green under all applicable canonical consumers.
- general rule: a stage-complete boolean records desired state, not evidence.
  Readiness must be derived from fresh, subject-bound receipts for every
  applicable canonical gate. A pass with an unexpected zero denominator,
  an uninvoked rule family, a missing ledger, an exception or a stale subject
  leaves the stage ungraded and blocks its consumers.
- intended landing point: define a stage registry that enumerates applicable
  rule families, canonical reader commands and expected minimum coverage. Each
  reader emits a bounded result with the input hash, validator version,
  numerator/denominator, evidence paths and terminal state. `project_state.py`
  derives maturity only from those receipts, and generation refuses `FAIL`,
  `ERROR`, `STALE` and `UNGRADED` alike.
- completion evidence required: orchestration fixtures must reject an omitted
  reader, a manually true completion flag, a missing findings ledger, a stale
  receipt and a nominal pass with zero rows; a clean fixture with all expected
  families and nonzero coverage must advance exactly one declared boundary.
- recommendation: address before resuming v5 schematic generation. This is the
  umbrella fix that prevents several individually cheap contract mismatches
  from becoming a misleading stage-level green claim.
- implementation progress: v5 now has a canonical `findings.yaml`, a dated
  source-audit receipt with coverage and timing, a 50-file byte-identity
  checkpoint, and a derived `DRAFT` maturity
  instead of relying on the old completion booleans. Generic readers now emit
  bounded/non-vacuous source verdicts for the failures that exposed this gap,
  and the rebuild template invokes them before TSX. The generic stage registry,
  subject hashes, freshness checking and receipt-to-`project_state.py`
  composition remain outstanding; therefore this is not complete.
- implementation progress: 2026-08-15 — a strict schema-1 readiness registry
  and composer now validate the closed expected receipt set, exact
  applicability, semantic/raw subject identity, output symbols, accepted
  bundle run/subject/timing, file census, hashes, sizes and symlink safety.
  Every applicable stage declares a positive `minimum_total`; an unexpected
  low-but-nonzero denominator is inadmissible, and one accepted manifest may
  not be reused to satisfy two stage/output bindings.
  `project_state.py --receipt-registry ...` records deterministic receipt
  maturity and its exact comparison with the legacy ledger, but deliberately
  leaves the ledger and existing exit status authoritative. Clean, missing,
  unknown, stale, tampered, explicit-N/A and disagreement fixtures are wired
  into the default runner. Real project registries/receipts and representative
  canary observations remain required before any authority promotion, so this
  entry remains implementing.
- implementation note: source-phase policy currently imports PCB machinery and
  emits KiCad property assertions even though its two source rows pass. A stage
  registry should phase-lazy-load dependencies so source receipts are quiet,
  fast and free of irrelevant PCB initialization.
- history:
  - 2026-08-13 — proposed from the v5 false-green checkpoint.
  - 2026-08-13 — implementation began with bounded source readers, a v5
    findings ledger, a dated source receipt and a 50-file checkpoint; three
    rule families were promoted into the schema/reader ratchet.
- implementation completion: 2026-08-17 — `pipeline_readiness.py` supports an
  explicit `shadow` or `receipts` authority and `project_state.py` can make the
  closed registry authoritative while retaining the legacy projection;
  `agreement` refuses disagreement. Clean authority, missing receipt and
  disagreement fixtures are in the default suite. Project registries remain
  an opt-in migration decision, but the generic authority mechanism is no
  longer shadow-only.

## IMP-070 — mechanically scope clean-room filesystem discovery

- status: proposed
- observed: Pluto RX2 8-way v5 clean-room research, 2026-08-13
- evidence: a repository-wide search surfaced filenames and text snippets from
  explicitly excluded earlier Pluto projects. No legacy design artifact was
  intentionally opened or copied and the provenance record was corrected, but
  the breach showed that a prose instruction cannot constrain an otherwise
  broad discovery command.
- general rule: clean-room scope is a command-boundary property. Allowed roots,
  denied roots and permitted reusable process material must be machine-readable
  and enforced for filesystem discovery and reads; prompt wording and operator
  memory are not controls.
- intended landing point: commission an allowlist of new-project and generic
  skill/process roots plus explicit deny patterns for legacy subjects. Route
  searches through a wrapper that validates working directory and arguments,
  rejects repository-wide expansion and path traversal, and emits an auditable
  discovery receipt. Any breach stops the stage and records exactly what became
  visible before work continues.
- completion evidence required: fixtures must permit the commissioned project
  and reusable skills, reject an older project, a symlink escape, a traversal
  path and a broad repository search, and produce a stable incident record for
  each denied attempt.
- recommendation: implement before the next clean-room project; for v5, retain
  the disclosed provenance incident and avoid any further broad searches.

## IMP-071 — derive observable protocol timing from executable state schedules

- status: implementing
- observed: Pluto RX2 8-way v5 dwell-protocol review, 2026-08-13
- evidence: the declared 500 ms marker body was immediately followed by a 5 ms
  guard in the same switch state, so a downstream observer sees one contiguous
  505 ms interval. Cycle duration, capture requirements and distinguishability
  were then checked manually from prose and duplicated derived values.
- general rule: a receiver observes merged state runs, not semantic labels such
  as `marker`, `dwell` or `guard`. Observable windows, unique dwell signatures,
  cycle time and minimum capture must be derived from one atomic state schedule;
  the decoder must treat any unmatched or incomplete observation as unknown.
- intended landing point: add a conditional control-protocol checker for boards
  using timing-coded switching. It merges adjacent identical states, applies
  controller and estimator error bounds, computes observation windows and
  cycle/capture limits, and rejects handwritten derived-value drift, ambiguous
  merged intervals, overlapping windows and insufficient capture duration.
- completion evidence required: fixtures must cover the corrected v5 schedule,
  the original 500+5 ms adjacent-state ambiguity, overlapping tolerance
  windows, a truncated capture and a no-signal/reset interval; only the fully
  distinguishable schedule may pass.
- recommendation: land before firmware generation or downstream decoder work.
  It is conditional process machinery, not a burden for boards without an
  observable timing protocol.
- implementation progress: `control_protocol_check.py` now derives contiguous
  observable runs, active-state windows, marker duration, cycle time and
  guaranteed capture from the atomic schedule; it rejects derived-value drift,
  overlapping windows and decoder contracts without explicit unknown outcomes.
  The canonical rebuild template runs it before TSX and executable fixtures
  cover a clean v5 contract, the original 500+5 marker mismatch, overlap,
  derived drift and no-signal decoder behavior. Schema 2 now adds one versioned
  profile identity and project-confined consumer paths;
  `control_profile_codegen.py` generates the STM32 header and decoder JSON from
  that same contract and `--check` rejects either consumer when stale. The v5
  `fast20-v1` revision-1 profile proves disjoint 20/23/26/30/34/39/44/50 ms
  dwell windows, an 85 ms observable marker, a 386 ms frame and a 772 ms
  arbitrary-phase guaranteed-capture minimum. Actual firmware/decoder behavior
  and an explicit truncated-capture end-to-end fixture remain before closure.
- history:
  - 2026-08-13 — proposed from the adjacent ALL_OFF marker/guard ambiguity.
  - 2026-08-13 — implementation began with a generic source checker, template
    gate and regression suite; v5 passes at marker 505 ms/cycle 2160 ms.
  - 2026-08-13 — added versioned two-consumer code generation and moved v5 to
    the user-requested fast20-v1 profile; source, header and decoder now fail
    closed on any one-sided timing edit.

## IMP-072 — classify committed binary evidence in the canonical scaffold

- status: proposed
- observed: Pluto RX2 8-way v5 source-evidence staging, 2026-08-13
- evidence: two valid generated Yageo PDF files contained no NUL byte, so Git's
  heuristic treated them as text and `git diff --check` emitted thousands of
  whitespace diagnostics. A project-local `.gitattributes` entry declaring
  `*.pdf binary` restored bounded, useful review output.
- general rule: the repository must declare the representation of committed
  evidence formats whose bytes are not meaningfully line-reviewable. Tool
  heuristics are not a stable content contract.
- intended landing point: include a canonical `.gitattributes` file in the
  project scaffold and initializer copy list with `*.pdf binary`. Add other
  evidence types only when their review/merge behavior is explicitly known;
  continue to verify content with hashes and purpose-specific readers.
- completion evidence required: initialize a fixture, stage a valid PDF with no
  NUL byte and prove diff/check output remains bounded with no text-whitespace
  diagnostics; prove the file hash survives scaffold, copy and archive steps.
- recommendation: low-risk and inexpensive; land in the next scaffold update.

## IMP-073 — grade human symbol pin functions, including unused pins

- status: proposed
- observed: Pluto RX2 8-way v5 schematic readability review, 2026-08-13
- evidence: the first generated schematic connected every used STM32 pin to
  the correct net and passed 129/129 pin-map assertions, 30/30 electrical
  invariants, 33/33 component parity and zero-error ERC. It nevertheless gave
  several unused U2 pins the wrong human function names: PC14/PC15, PA8,
  PA11/PA9, PA12/PA10 and PB6 were mislabelled. The fresh visual/datasheet
  review caught the defect; the checkpoint was discarded, corrected against
  ST DS13866, regenerated and re-reviewed before PCB work.
- general rule: connectivity parity proves physical pad-to-net identity, not
  that the delivered schematic tells a human the truth about each pad. A pin-
  function check must cover connected and intentionally unused pins alike and
  compare the generated symbol's visible function to the exact part dossier or
  an explicit reviewed alias. Unconnected does not mean unimportant.
- intended landing point: before rendering and review, compare every generated
  symbol pin number/function with `02_parts/*/part.yaml pins:`. Require exact
  normalized identity or a board-local alias row that names its evidence and
  purpose suffix (`_NC`, role alias, alternate-function choice). Report the
  refdes, physical pin, visible text and dossier text for each mismatch.
- completion evidence required: a fixture with correct connected nets but the
  v5-style wrong unused labels must fail; correct exact labels must pass;
  intentional aliases and alternate-function abbreviations must fail unless
  explicitly declared and then pass without weakening physical-pin parity.
- recommendation: implement before the next new schematic. The v5 instance is
  repaired and hash-bound, so no current project fix remains.
- history: 2026-08-13 — proposed from the first v5 human-review rejection.

## IMP-074 — ADR gate applicability must be typed, not inferred from prose

- status: proposed
- observed: Pluto RX2 8-way v5 schematic gate, 2026-08-13
- evidence: `electrical_invariants.py --adr-coverage` reported `E-ADR OK: 0/0`
  even though ADR-0001 selects the complete RF topology, ADR-0002 selects the
  controller/control topology, ADR-0003 selects the protected power topology,
  and 30 executable invariants cite those decisions. The gate discovers
  protection/topology ADRs by keywords in titles/tags; the accepted v5 titles
  use descriptive names that do not match its regex.
- general rule: whether an ADR must emit executable assertions is schema, not
  natural-language classification. A zero denominator is meaningful only when
  the commissioned ADR set explicitly says that none is applicable.
- intended landing point: add closed front-matter metadata such as
  `assertion_domains: [topology, protection, control]` to the ADR contract and
  make E-ADR consume it. New ADRs must declare at least one domain or explicit
  `none` with a reason. Retain the title heuristic temporarily as a migration
  warning, never as the authoritative denominator.
- completion evidence required: fixtures must classify descriptive titles
  without keywords, reject a missing domain, reject an applicable ADR with no
  invariant, accept a cited applicable ADR, and accept explicit `none` only
  with substantive rationale. A migrated v5 run must report a nonzero cited
  denominator.
- recommendation: implement as a schema migration before relying on E-ADR for
  another newly commissioned board. V5's direct 30-invariant and independent
  topology reviews close the local risk, so changing accepted ADR metadata is
  not required inside this schematic checkpoint.
- history: 2026-08-13 — proposed from the v5 gate's misleading 0/0 coverage.

## IMP-075 — bind mechanical dimensions to exact document identity and feature role

- status: proposed
- observed: Pluto RX2 8-way v5 pre-placement connector review, 2026-08-13
- evidence: the `901-143-6RFX` dossier named a plausible Amphenol asset but the
  asset was drawing `901-40129`, not the selected MPN. The resulting draft
  geometry mixed a 1.50-mm RF-contact hole with a 1.52-mm value from the wrong
  part. The exact current drawing `SMA6252A2-3GT50G-50` Rev C instead requires
  one 1.50-mm centre hole and four 1.70-mm ground holes. This was caught before
  footprint or PCB generation; the dossier and evidence were corrected.
- general rule: an authoritative domain is not enough. Before any dimension is
  transcribed, resolve the exact product page to an exact document identity,
  verify visible MPN/document/revision, retain or explicitly qualify hash-bound
  bytes, and check current PCNs. Mechanical facts must be keyed by physical
  feature role and datum (`rf_contact_hole`, `ground_leg_holes`, mating face),
  never stored only as an unlabeled list of dimensions.
- intended landing point: add a pre-footprint document-identity gate that
  compares selected MPN, product-page drawing title, local PDF visible identity,
  dossier `doc_id`/revision/hash and applicable PCNs. Add a typed footprint
  contract whose role-labelled source dimensions are measured against realized
  pads, drills, courtyard, board-edge datum and mating direction before
  placement generation.
- completion evidence required: fixtures must reject a correct-vendor/wrong-
  part drawing, swapped centre/ground hole sizes, an unlabeled diameter list,
  an unmatched local hash, and a geometry-changing PCN without reapproval; an
  exact drawing plus no-form/fit-change origin PCN and matching realized
  footprint must pass with a nonzero feature count.
- recommendation: implement before the next custom connector footprint. The v5
  instance is corrected, but its realized-footprint measurement and render
  review remain mandatory before placement approval.
- history: 2026-08-13 — proposed after D12 triggered the exact drawing audit.

## IMP-076 — reconcile exact package geometry and logical pin identity in the first-board preflight

- status: proposed
- observed: Pluto RX2 8-way v5 first unrouted placement, 2026-08-13
- evidence: the first board generated in under one second and was mechanically
  collision-free, but the immediate placement DRC exposed four
  0.1944-mm GCT land-to-NPTH gaps against a provisional 0.200-mm generic hole
  rule, two 0.150-mm SOT-553 land gaps against a 0.200-mm default netclass, and
  decorative SMA silk crossing its own pads/edge. In the same cheap pass,
  P-PINMAP exposed that TSX's numeric USB logical ports had not yet been
  explicitly reconciled with GCT's alphanumeric physical contacts. All were
  source-only corrections; the next board passed 0 placement violations and
  117/117 declared physical identities before any routing work began.
- general rule: immediately after the first exact-footprint board exists, run
  one bounded preflight that (1) measures each package's own copper-to-copper,
  copper-to-hole and silk-to-mask/edge minima, (2) compares those minima with
  the adopted board/netclass rules, and (3) reconciles dossier logical pins,
  producer pins and realized pad identities. A manufacturer land below a
  generic rule must require an exact-package local override with evidence; it
  must not emerge later as unexplained route-grind noise.
- intended landing point: make the canonical placement stage run
  `pin_map_check.py`, exact intra-footprint geometry census and placement DRC
  as one first-board bundle before route config/rule preparation or human
  rendering. Emit a machine-readable report naming the package, exact feature
  pair, measured gap, controlling rule, local override and evidence path.
- completion evidence required: fixtures must reproduce the GCT NPTH gap, the
  SOT-553 0.150-mm land gap, an unjustified blanket rule relaxation, missing
  numeric-to-alphanumeric aliases, and self-clipping connector silk. The first
  four must fail with exact feature identities; evidence-backed package-local
  overrides and complete aliases must pass without weakening unrelated nets.
- recommendation: implement before the next custom-footprint project. V5 has
  already run the bundle manually and is clean, so no route-stage fix remains.
- history: 2026-08-13 — proposed from the bounded v5 placement grind.

## IMP-077 — reconcile footprint and symbol metadata before schematic-parity DRC

- status: proposed
- observed: Pluto RX2 8-way v5 keyed-SWD placement, 2026-08-13
- evidence: the exact J11 custom footprint initially carried non-empty KiCad
  `Datasheet` and `Description` properties while the generated schematic
  symbol carried empty values. Connectivity, physical-pin mapping, pad
  separation and placement geometry all passed, but immediate pre-route KiCad
  schematic-parity DRC correctly stopped first on `Datasheet` and then on
  `Description`. Two otherwise identical one-second placement regenerations
  were needed to expose the fields serially. The searchable human description
  remains in the footprint `descr` and the authoritative provenance remains in
  the part dossier, so clearing the duplicate instance properties repaired the
  exact board without losing evidence.
- general rule: symbol/footprint standard fields are parity-bearing design
  data, even when they are not electrical. A project footprint template must
  either inherit the exact generated-symbol value or leave the field empty;
  it must not independently author a second value that is expected to survive
  schematic-to-PCB parity.
- intended landing point: add a source/first-board lint that compares
  `Reference`, `Value`, `Datasheet`, `Description` and other parity-bearing
  footprint properties with the generated symbol contract before full DRC.
  Report every divergent field in one invocation. Keep descriptive search text
  in `descr`/`tags` and document authority in `part.yaml` unless the producer
  has one explicit, shared field source.
- completion evidence required: fixtures with two simultaneous divergent
  fields must report both at once; inherited-identical and deliberately empty
  properties must pass; the check must not erase or weaken dossier evidence.
- recommendation: low-cost lint before the next custom footprint. The v5
  instance is repaired and now reports zero schematic-parity findings.

## IMP-078 — run source-resolvable tier/routing preflight before expensive stages

- status: proposed
- observed: Pluto RX2 8-way v5 keyed-SWD placement, 2026-08-13
- evidence: after the exact schematic had been generated and reviewed and the
  placement had passed geometry, pin-map, landability and DRC checks,
  `tier_preflight.py` stopped before routing because
  the tier-derived effective `route.common.clearance=0.09 mm` was below the
  applicable 0.20 mm DRC floor and the tier-derived 0.15 mm drill through the
  declared 1.6 mm board gives 10.667:1, above
  the selected JLC advanced-tier 10:1 PTH aspect limit. It also warned that the
  0.50 mm legalization clearance is below the derived 0.53 mm rescue-via
  requirement. All three facts were derivable from already-authored
  `route.yaml`, net rules, stackup and fab-tier data before TSX generation or
  human schematic review.
- general rule: split routing preflight into a source-resolvable phase and an
  exact-board phase. Run the source phase with other cheap schema/electrical
  gates before foreign producers and reviewers; repeat the full phase after
  placement for facts that genuinely require realized pads and board setup.
- intended landing point: add `tier_preflight.py --phase source` (or an
  equivalent pure checker), invoke it before the TSX build in the canonical
  drivers, and retain the present pre-route invocation as the authoritative
  exact-board recheck. Diagnostics must distinguish source-known failures from
  placement-dependent checks and preserve the same effective-rule derivation.
- completion evidence required: the v5 clearance/aspect fixture must fail
  before a producer is called; a placement-dependent seed-via fixture must be
  deferred explicitly and fail at the exact-board recheck; clean designs must
  pass both phases without weakening the late authority.
- recommendation: implement early because it saves review cycles without
  changing any electrical or manufacturing rule. V5's local inputs are now
  corrected; this improvement changes when the conflict is discovered, not
  what values are acceptable.
- v5 disposition: explicitly selected the strictest adopted 0.20-mm class
  clearance for every router wave and JLC's preferred 0.45/0.20-mm ordinary
  via. Nominal aspect is 8:1 and remains 8.8:1 at JLC's published +10% board-
  thickness tolerance. Legalization clearance is 0.58 mm, derived from the
  actual 0.20-mm route drill plus twice the 0.19-mm hole clearance rather than
  merely accepting the checker's tier-minimum 0.53-mm warning threshold.
  R-PREFLIGHT now reports 0 FAIL / 0 WARN without changing the track-free
  board hash. The early source-phase implementation remains open.

## IMP-079 — derive compact floorplans from topology and operational connector envelopes

- status: proposed
- observed: Pluto RX2 8-way v5 compact placement, 2026-08-13
- evidence: the first board used a 100 x 100 mm four-edge ring because mapping
  the PE42482 cyclic pin order directly around the complete perimeter made
  crossing-free RF fan-out obvious. It passed every placement gate, but the
  square was not a component-density requirement. Before routing, the same
  cycle was cut between ANT4 and ANT5 and mapped onto a five-top/two-per-side
  open U. The resulting 90 x 65 mm board retains zero proper straight RF-
  corridor crossings, four M3 holes, three fiducials, keyed SWD and USB-C,
  while reducing area by 41.5%, the common straight span from 36.501 to
  14.502 mm and the maximum throw span from 46.580 to 35.676 mm. All exact-
  board placement, model, pad, DRC, escape and tier gates remain green.
- general rule: floorplanning must distinguish a topology proof, a geometric
  packing minimum and a comfortable operational target. Before freezing the
  first outline, test whether each cyclic/radial net order can be cut or folded
  onto an open boundary without crossings. Size connector banks from mating
  bodies, installed cable nuts, tool approach, mounting torque paths, RF
  launch/fence space and labelling—not courtyard non-overlap alone.
- intended landing point: add a pre-placement floorplan worksheet/checker that
  consumes exact connector body width/datum, requested edge grouping, minimum
  service/tool pitch, mounting-hole envelopes and ordered critical endpoints.
  It should emit at least two candidates: `geometric_minimum` and
  `comfortable_target`, plus board area, endpoint order, straight-corridor
  crossing count, connector/body gaps and any unmodelled service envelope.
  The human brief must select the target before detailed placement review.
- completion evidence required: a cyclic nine-port fixture must show the
  closed-ring and open-U embeddings, reject a smaller courtyard-clean layout
  whose declared tool envelope overlaps, and reproduce the v5 90 x 65 mm
  comfortable candidate with zero crossings. A non-cyclic connector bank and
  an enclosure-locked board must demonstrate that the checker reports no
  unjustified compaction opportunity.
- recommendation: implement before the next connector-heavy RF or power board.
  V5 is already compacted before routing, so no immediate corrective work is
  owed; the remaining exact-route and human placement reviews are unchanged.
- history: 2026-08-13 — proposed after the user challenged the conservative
  square and the open-U remap removed 41.5% of board area without weakening a
  placement gate.

## IMP-080 — emit and measure RF fences from routed centrelines

- status: completed
- observed: Pluto RX2 8-way v5 deterministic route preparation, 2026-08-13
- evidence: the generic stitch backend's `stitch_grid` accepts only orthogonal
  `x`/`y` lattice axes. It can provide ordinary plane stitching but cannot
  intentionally follow the nine straight/diagonal/bent RF polylines. The
  shared `fence_pitch.py` correctly measures saved geometry rather than
  trusting requested sites, but its RF net list is hard-coded to one legacy
  naming scheme and therefore cannot grade v5's `RF_COMMON`/`RF_ANT1..8`
  routes. Calling either mechanism an RF-fence proof would be a false green.
- general rule: an RF fence is a relationship to realized transmission-line
  geometry. The source must name the RF nets, flank band, lateral target,
  maximum along-route aperture, endpoint return structures and via geometry.
  Emission must sample the actual saved centreline, collision-check both
  flanks, and refuse uncovered apertures; an independent gate must then measure
  the surviving vias/PTH returns from the saved board.
- implementation: `route_and_stitch_generic.py` now has a generic
  `stitch.route_fence` pass. It reconstructs each exact saved straight-track
  chain, derives the net denominator/layer/maximum pitch from `rf.yaml`, grades
  explicit package/connector endpoint structures, reserves constrained bend
  sites before straight-span filling, collision-checks both flanks through the
  shared fabrication-aware via primitive, and refuses every unresolved
  aperture. A plated return beside a bend is credited to every adjacent finite
  route segment it physically serves; forcing it onto only one nearest
  projection created a fictitious corner opening.
- independent implementation: `fence_pitch.py` was generalized without
  sharing emitter state. It reopens the saved board, accepts a contract or
  explicit net list while retaining its legacy positional CLI, reconstructs
  and fail-closes each simple chain, counts realized GND vias/PTH posts, grades
  lead-in/interior/run-out apertures outside only geometry-proven endpoint
  spans, and writes a machine-readable report. `rf_contract_check.py` now
  reconciles the layout net denominator, route cross-section, via/stub policy,
  guided-wavelength pitch, lateral offset and endpoint evidence before layout.
- local-minimum evidence: the first disposable v5 emitter closed 3/18 flanks;
  endpoint structures raised that to 12/18 and the 0.50-mm same-net spacing
  policy to 16/18. Reducing spacing to 0.46 mm made the greedy result worse at
  14/18. Both survivors were symmetric 45-degree inner bends where legal vias
  placed just before and after the corner consumed its remaining placement
  window. Corner-first anchors plus multi-segment physical credit close the
  same saved geometry deterministically rather than retrying or rerouting it.
- completion evidence: focused clean/known-bad fixtures cover a bent chain,
  both flanks, endpoint-inclusive failure/pass, idempotence and saved-board
  measurement. V5 realizes 394 new 0.45/0.20-mm GND vias, including 22 corner
  anchors. The independent report grades 18/18 arm-sides PASS; worst aperture
  is 1.3979 mm against the 1.4000-mm guided-wavelength bound. KiCad DRC remains
  0 violations / 0 unconnected / 0 schematic-parity findings and all four
  filled zones survive the saved-file read-back.
- recommendation: make this contract mandatory before routing on every RF
  board that relies on a coplanar via fence. Define the exact route nets,
  stackup/reference plane, guided-wavelength pitch, lateral band, via geometry
  and endpoint return structures before copper, but emit and independently
  grade only after the actual centrelines exist. Keep ordinary plane stitching
  separate and never let an attempted-site count certify an RF fence.
- sources: Analog Devices' MMIC layout note recommends CPWG ground holes at
  `lambda/20` or less; its RF/mixed-signal PCB guidance recommends fences on
  both CPWG sides and an unbroken underlying plane. V5 derives a conservative
  1.40 mm maximum from its retained JLC effective dielectric constant at
  5.9 GHz and records the calculation in `03_src/rules/rf.yaml`.
- history: 2026-08-13 — completed before exact-board RF PCB review. The
  rejected 0.25/0.15-mm via fallback and RF reroute experiments were not
  carried into the board; the solution preserves the approved RF copper and
  the ordinary 0.45/0.20-mm JLC via geometry.

## IMP-081 — deterministic UUIDs for route preparation

- status: completed
- observed: Pluto RX2 8-way v5 D16 repeatability check, 2026-08-13
- evidence: two consecutive preparations from identical source reported the
  same 14 keepouts, 29 seed segments and 44 plane-rescue items, yet produced
  different r0 SHA-256 values. A text diff showed only fresh KiCad UUIDs. The
  route progress contract authenticates the exact r0 hash, so rerunning prep
  would make a valid bounded route unresumable even though no geometry moved.
- general rule: every deterministic stage that creates KiCad objects must seed
  KiCad's UUID generator from a stable artifact namespace before the first
  object is minted. Deterministic values with random identities are not a
  reproducible input to hash-bound downstream work.
- implementation: `route_and_stitch_generic.py cmd_prep` now seeds
  `pcbnew.KIID.SeedGenerator` from CRC32 of `<source-board>:route-prep` before
  creating keepouts, seed copper or rescue copper. Existing source objects
  retain their identities. `tests/t2_route_stitch.py` prepares a fixture with
  keepouts, deterministic seed copper and early pad rescue twice and requires
  byte equality.
- completion evidence: the focused regression passes; two v5 preparations
  complete in 0.56 s and 0.53 s and are byte-identical at SHA-256
  `d598d305f5d75dd5bcebdd8320ef0949ca787bd0f5c7e53a573c66c995e726de`.
- history: 2026-08-13 — discovered and completed at the D16 reflection pause,
  before KRT or route-progress provenance existed.

## IMP-082 — require executable budgets for datasheet short/close layout obligations

- status: proposed
- observed: Pluto RX2 8-way v5 exact pre-route placement renewal, 2026-08-13
- evidence: the TPD2E2U06 dossier said to place the clamp "immediately behind"
  J1 and the TPS7A24 dossier said to put both 4.7-uF capacitors "directly at"
  the LDO pins. The generated board passed collision, courtyard, pad-separation,
  escape and placement DRC, while `policy_audit --phase placement` reported
  P-ADJ N-A because neither prose sentence supplied a machine-readable
  denominator. A fresh layout reviewer then measured U4 about 8.33 mm from J1
  and C1/C2 about 4.24/4.61 mm from U3 and correctly blocked routing. After the
  source repair, four partner-specific budgets are all graded: U4.3→J1.A5
  1.922 mm of 4.0, U4.5→J1.B5 3.028 mm of 4.0, U3.1→C1.1 1.875 mm of 2.5,
  and U3.5→C2.1 1.875 mm of 2.5. Placement DRC remains 0 violations / 39
  expected unrouted items / 0 parity findings.
- general rule: a manufacturer layout statement containing `short`, `close`,
  `near`, `immediately`, `directly at`, or an equivalent critical-placement
  obligation must not be satisfied by `layout.notes` alone. Before board
  generation it must become a typed `keep_short` or `adjacency` budget with an
  explicit anchor pin, partner ref/role, numeric limit, measurement definition
  and source citation. If no defensible number exists, record an explicit
  HUMAN obligation that prevents the automated row from appearing applicable
  or complete; never let the constraint disappear into an N-A denominator.
- intended landing point: extend the part-schema/source preflight to classify
  critical-layout language and reject prose-only obligations unless paired
  with an executable budget or explicit human-gate record. Make the placement
  summary surface `declared/graded/unreached` counts prominently and treat an
  all-N-A P-ADJ result as a review warning whenever in-scope dossiers contain
  critical-layout language. Keep the exact-board P-ADJ evaluator as the late
  authoritative measurement.
- completion evidence required: fixtures must reject prose-only ESD-clamp and
  regulator-bypass instructions, a budget with no anchor, a broad-rail nearest-
  any-part false pass, and a partner name that resolves to nothing. They must
  accept the four v5 partner-specific budgets with a 4/4 denominator, accept a
  properly typed human-only obligation without claiming a machine pass, and
  preserve current boards whose layout notes contain no critical adjacency
  instruction.
- recommendation: implement before the next exact-placement project. The v5
  instance is repaired now, so the generic lint is not a blocker for its
  bounded control/power route; the fresh board-bound layout review remains the
  authority for this revision.
- history: 2026-08-13 — proposed after a fresh reviewer caught a real layout
  defect that every existing geometric gate passed because the datasheet intent
  existed only as prose.

## IMP-083 — make no-via-in-pad intent executable at every routing wave

- status: completed
- observed: Pluto RX2 8-way v5 first control/power routing attempt,
  2026-08-13
- evidence: one bounded five-wave KRT chain completed quickly but left the
  same `SW_V1` endpoint open that all three subsequent race candidates left
  open. The candidates also escaped boxed component lands with seven new
  ordinary vias directly in U1/U2/J1/C6 SMD pads, including 0.30/0.15-mm
  geometry below the board's authored 0.45/0.20-mm ordinary-via contract. The
  prepared route independently exposed a second form of the same semantic
  defect: with `via_in_pad: false`, plane-pad rescue for one J11 GND land put
  its adjacent same-net via in another long J11 GND land. KRT exited zero in
  every case; only the later quick/census work rejected the chain.
- general rule: `via_in_pad: false` is a geometry invariant, not a suggestion
  to an emitter. Each stochastic wave must compare its output with its exact
  input and refuse every newly-created via whose centre lies in any SMD land.
  Vias already present in the input remain source-owned, so a separately
  reviewed filled/capped exposed-pad field is allowed without weakening the
  rule. A deterministic adjacent-via placer must likewise reject all SMD-pad
  landing sites, including foreign pads on the same net. When a legal escape
  is topologically boxed, own the minimum package dogbone in source and leave
  only the unobstructed trunk to the router.
- implementation: `via_in_pad_guard.py` performs the exact input/output via
  comparison and records the offending via, pad, net, coordinate, size and
  drill. `route.forbid_new_via_in_pad: true` runs it after every successful
  KRT wave and before progress authentication or the next wave. The route
  driver now removes a stale `FINAL` marker before both single-chain and race
  attempts. `pad_rescue` rejects adjacent sites inside any SMD pad whenever
  `via_in_pad` is false. The schema contract names both new reader paths.
- completion evidence: the hermetic KRT fixture exits zero after creating a
  via in an SMD pad and the wave gate fails, records the exact finding and
  removes a planted stale `FINAL`; an independent review then found that an
  earlier preflight/config failure could still retain `FINAL`, so invalidation
  moved to the first `cmd_route` operation and a separate early-failure fixture
  now proves it. Fixtures also prove that source-owned vias already in the
  input are allowed, rejected waves do not enter authenticated progress, clean
  waves and both race lanes execute the guard, mask-only apertures are not
  mistaken for copper, and a two-pad same-net rescue emits an adjacent legal
  via without landing in either pad. The complete non-slow routing/stitch suite
  passes 108/108, including 47 known-bad fixtures. Schema-reader governance
  passes 616/616 with zero orphans and gate-contract audit passes 59/59.
  On v5, deterministic package/connector dogbones plus explicit J11 drops
  prepare byte-identically at SHA-256
  `cab54a0b9f9d304bdd9cf68c0d4ed756e8e93814dfe845db9de4e923756ca695`;
  the prep comparison reports zero newly-created via-in-pad and its DRC has
  zero copper/clearance/edge findings.
- recommendation: enable the wave guard on every new board whose assembly
  contract does not explicitly authorize router-created via-in-pad. Keep it
  opt-in for existing designs until their intentional source vias can be
  distinguished and reviewed; do not silently reinterpret legacy geometry.
- history: 2026-08-13 — completed before retrying v5 routing. The failed
  single chain and identical three-way race were retained as evidence rather
  than promoted or retried again.

## IMP-084 — site admission must honor realized pad-local copper and mask rules

- status: completed
- observed: Pluto RX2 8-way v5 first post-stitch full DRC, 2026-08-13
- evidence: two 0.45/0.20-mm GND grid vias were admitted 1.118 mm from 1-mm
  fiducials because `via_site_ok` used only the common 0.20-mm clearance. Each
  fiducial authored 0.60-mm local copper clearance and 0.50-mm solder-mask
  expansion. Full DRC reported two clearance, two hole-clearance and two
  solder-mask-bridge findings; the realized copper requirement was 1.325 mm.
- general rule: a geometry emitter's site predicate must evaluate the rules of
  every object it approaches, including per-pad copper clearance and mask
  expansion on each affected outer layer. Board/netclass defaults are only a
  floor, never permission to ignore an object's stricter local rule.
- implementation: `pcb_toolkit.py` caches each pad's local clearance and front/
  back realized mask expansion and applies them in copper, drill and via-mask
  collision probes. Bounding-box margins are per object rather than global.
- completion evidence: a known-bad fixture independently proves rejection by
  local copper clearance and by mask expansion. The final v5 lattice admits
  200 sites, rejects both fiducial-adjacent sites, and saved-board DRC is 0.
- recommendation: keep this in the shared toolkit and require every new via,
  tap, rescue and fence emitter to use the same predicate rather than a private
  board-default-only collision approximation.
- history: 2026-08-13 — completed before accepting the v5 post-stitch stage.

## IMP-085 — normalize overlap-only track/via joints before deleting barrels

- status: completed
- observed: Pluto RX2 8-way v5 R3.1 cleanup, 2026-08-13
- evidence: KRT stopped a 0.25-mm 3V3 track 0.100 mm from the centre of an
  existing 0.45-mm same-net via because the copper caps already overlapped.
  Removing that unused single-layer barrel would leave a cap-overlap-only
  joint rather than an explicit centreline node. A first endpoint-moving draft
  was rejected because pivoting a complete segment can change its whole copper
  envelope even when the moved cap stays contained.
- general rule: cleanup may remove an anchoring via only after every surviving
  connection is explicit. A normalizer may add a bridge only when the endpoint
  is otherwise free, net/layer agree, and the complete bridge capsule is
  contained inside copper that already exists. Do not pivot existing routes.
- implementation: `bridge_via_endpoints` adds a short same-net track from the
  free endpoint to the via centre under strict `distance + track_radius <=
  via_radius`; no geometric tolerance is allowed. `via_janitor` then removes
  only barrels attached on fewer than two copper layers.
- completion evidence: the focused fixture accepts a 0.100-mm exactly-contained
  bridge and refuses a 0.101-mm just-over-boundary bridge. Independent replay
  adds two bridges, removes 12 barrels and leaves R3.1 with two tracks sharing
  `(68.80,57.00)`, no via, zero opens and zero DRC findings. The routing/stitch
  suite passes 110/110 non-slow tests, including 48 known-bad fixtures.
- recommendation: retain this as a narrowly ordered pre-janitor normalization;
  do not generalize it into arbitrary endpoint snapping or gap healing.
- history: 2026-08-13 — completed and independently renewed P0/P1/P2=0/0/0.

## IMP-086 — run external mating-fact provenance before PCB generation

- status: proposed
- observed: Pluto RX2 8-way v5 post-stitch gate, 2026-08-13
- evidence: `BRIEF.md` had a `Mating fact-lock` describing the SMA cable
  boundary, but `03_src/rules/mates.yaml` was absent. `import_provenance_check`
  correctly failed D-MATE only after routing and stitch work had completed.
  The repaired machine copy references SMA gender, port order and RX absolute
  maximum from their single `external_hardware/plutoplus_hardware` home and passes 3/3; it
  consumes no Pluto dimension and changes no copper.
- general rule: when the brief declares a foreign-hardware mating boundary,
  D-MATE/M-IMPORT is source governance and must run before schematic freeze or
  PCB generation. A late gate is still useful, but it should verify an already
  pinned fact-lock rather than discover the first missing declaration.
- intended landing point: add `import_provenance_check.py PROJECT` to the early
  source-governance stage and include `mates.yaml` plus the referenced SPF fact
  index/record hashes in the schematic checkpoint whenever the denominator is
  nonzero. Retain the final rerun for drift detection.
- completion evidence required: a project with a Mating fact-lock and no
  machine copy must stop before TSX/PCB generation; a board explicitly saying
  it does not mate remains a visible zero-denominator N-A; a valid informational
  cable boundary passes early and again at final layout without restating data.
- recommendation: implement before the next board that interfaces with
  externally designed hardware. V5's instance is fixed and not blocked.
- history: 2026-08-13 — proposed after the right gate ran at the wrong stage.

## IMP-087 — grade rerunnable density gates against realized saved geometry

- status: completed
- observed: Pluto RX2 8-way v5 RF-fence disposable rerun, 2026-08-13
- evidence: the already-complete ordinary 5-mm GND stitch grid caused
  `stitch_grid` to emit zero duplicate vias, then falsely failed its own
  `min: 80` contract as `0 < 80`. The first run had safely realized 200 grid
  sites; the gate was measuring work performed in this invocation rather than
  the board property the minimum was meant to require.
- general rule: a rerunnable stage's acceptance criteria must grade the
  realized saved result, not its mutation delta. `added`, `removed`, cache-hit
  and retry counters are useful telemetry, but they cannot stand in for
  population, density, connectivity, fill or coverage requirements. This
  applies beyond vias to thermal arrays, test points, zones, labels, model
  coverage and any resumable generator.
- implementation: `stitch_grid` still reports newly added vias separately,
  but its minimum now counts declared lattice sites served by realized
  same-net plated returns inside the same spacing window that suppresses a
  duplicate. It records `grid_sites_total` and `grid_sites_served`; a foreign
  blocker earns no credit. The existing impossible-minimum known-bad remains
  red.
- completion evidence: a new fixture realizes a grid, reruns the complete
  stitch pass, proves zero new vias, and requires the saved served-site
  denominator to remain green. On the fenced v5 rerun, zero duplicate grid
  vias and 200/234 realized served sites pass the unchanged `min: 80`; the
  complete stitch gate is clean.
- recommendation: audit every resumable `min`/`require: all` gate for this
  distinction before the next board. Prefer three explicit values in reports:
  `attempted or added this run`, `realized subjects graded`, and `required
  denominator`. Run this cheap idempotence fixture when a new emitter is
  introduced, before using it in an expensive board replay.
- history: 2026-08-13 — completed during disposable RF-fence promotion, before
  touching the real board.

## IMP-088 — seed deterministic identities across import and stitch

- status: proposed
- observed: Pluto RX2 8-way v5 layout-seal entry, 2026-08-13
- evidence: IMP-081 seeded route preparation, so identical source produces a
  byte-identical r0. The later `import_krt.py` and stitch passes still construct
  PCB tracks/vias without a stable KiCad UUID seed. A canonical rebuild can
  therefore reproduce identical copper and clean DRC while changing the board
  SHA solely through fresh object identities, invalidating exact-artifact RF,
  pin, render, topology and layout reviews.
- general rule: reproducibility ends at the last artifact-producing stage, not
  the first deterministic one. Every process that creates identity-bearing
  objects must derive a stage-specific seed from immutable input identity and
  preserve deterministic creation order. A geometry-only comparison may be a
  useful diagnostic, but it must not silently replace exact-byte provenance.
- intended landing point: seed KiCad's UUID generator in `import_krt.py` from
  the exact base-board plus promoted-chain identity, and in `cmd_stitch` from
  the exact imported-board plus route/stitch-contract identity. Record those
  seeds and input hashes in provenance, then require two clean full replays to
  produce byte-identical imported and post-stitch boards.
- completion evidence required: fixtures must replay import and stitch twice
  from byte-identical inputs, including tracks, vias, corner anchors, filled
  zones and fresh-interpreter barriers, and require byte equality. Changing
  one source track or stitch parameter must change the identity namespace;
  an idempotent rerun on the finished board must still emit no duplicates.
- recommendation: implement before the next routed board and before using a
  full rebuild as an exact-review recovery path. V5 should use the existing
  reviewed-commit layout-seal path now; changing producer identity policy
  after its exact board was reviewed would create avoidable subject churn.
- history: 2026-08-13 — proposed when the layout-seal rehearsal showed that a
  canonical rebuild could be geometrically correct yet stale every exact-board
  review for identity-only reasons.

## IMP-089 — treat same-net via-in-pad as a fabrication process

- status: completed
- observed: Pluto RX2 8-way v5 final layout red team, 2026-08-13
- evidence: exact board `0b8ab1962ef7` was DRC 0/0/0, P-PADSEP clean and RF
  fence 18/18, yet an ordinary 0.45/0.20-mm GND stitch via at
  `(42.50,77.50)` was centred inside keyed SWD connector J11.3's
  0.74 x 2.79-mm F.Cu/F.Mask/F.Paste land. Same-net copper overlap is legal,
  so DRC had no reason to object. The via was neither filled nor capped and
  could wick paste/solder from the connector joint. A final-chain-to-board
  `via_in_pad_guard.py` comparison reported exactly this one post-route hole.
- general rule: via placement needs two independent meanings. Electrical DRC
  decides whether copper may touch; assembly policy decides whether a drilled
  barrel may occupy an SMT land. Every ordinary grid, fence, rescue and repair
  emitter must refuse exact SMD-pad hits at its shared admission seam. Only an
  explicitly owned via-in-pad operation may opt in, and every realized
  via-in-pad must be filled+capped and selectable by an unambiguous fabrication
  family that does not include ordinary vias.
- landed in: `route_and_stitch_generic.py` now rejects ordinary stitch sites
  whose centres hit exact KiCad SMD copper, with explicit opt-in only for
  `pad_rescue.via_in_pad: true`. `via_process_check.py` independently scans the
  final board, refuses any unprotected via in an SMT land, refuses native
  fill/cap intent without an assembly contract, and proves protected versus
  ordinary drill-family separation at layout/fab entry.
- regression: `t2_route_stitch.py` places a same-net J11-like land directly on
  a declared grid site and requires the site to remain barrel-free;
  `t1_via_process.py` requires both the unprotected-via-in-pad and
  native-flags-without-order-contract fixtures to fail.
- project correction: v5 replay removes the single J11 grid via. The nine
  intended U1 EP holes are 0.45/0.25-mm filled+capped vias; all 629 ordinary
  route/stitch/fence holes remain 0.45/0.20 mm. JLC's published POFV guidance
  lists a 0.25-mm hole with 0.40-mm via diameter, so the selected protected
  0.45/0.25-mm family is within that published geometry and drill-distinct.
- 2026-08-17 follow-up: the USB-controlled debug hub reached release staging
  with 87 realized via-in-pad sites even though only one source thermal via
  carried Type-VII flags. Most were legitimate route/prep transitions whose
  centres landed in same-net passive or IC lands, so electrical DRC remained
  0/0/0. The late process census correctly blocked fabrication. The repaired
  source now makes the complete 0.46/0.20-mm drill family filled+capped (470
  vias), leaves the 0.41/0.15 and 0.70/0.35-mm families ordinary, and splits
  one bulk-capacitor spur from its main power-via bank so current capacity is
  preserved. `protect_via_family` applies native intent to the exact complete
  family without resizing other vias; `via_process_check.py` now passes
  525/525 via flags/selectors and 87/87 via-in-pad sites while full DRC remains
  0/0/0.
- remaining lifecycle correction: run the final-style via-in-pad census after
  prep and after every promoted route wave, not for the first time during fab
  export. Before routing begins, require either an executable no-via-in-pad
  policy or a drill-disjoint fabrication family plus assembly/order contract.
  A wave that introduces a new barrel under paste must fail promotion unless
  its manufacturing disposition is already source-authenticated.
- history: 2026-08-13 — completed before layout seal after independent final
  pin and layout lenses both refused the otherwise-green exact board.

## IMP-090 — bind review freshness to declared stage dependencies

- status: proposed
- observed: Pluto RX2 8-way v5 corrected layout seal, 2026-08-13
- evidence: changing U1's final fabrication-via drill family in
  `floorplan.yaml`, its human dossier note, and `assembly.yaml` correctly
  invalidated layout/fabrication review. It also invalidated the pre-route
  schematic topology and PDF-readability witnesses solely because those
  witnesses hash the complete `02_parts` and design-rules bags. The schematic,
  netlist and PDF bytes were unchanged; the changed assembly/process fields
  are not inputs to either schematic lens. The gate failed loudly, which is
  safe, but required two unrelated review renewals and makes future users more
  likely to resent or bypass freshness checks.
- general rule: every review witness should declare the artifact and semantic
  source families its conclusion actually consumes. Freshness must fail on any
  consumed dependency change, but not on unrelated downstream fields. A broad
  whole-directory hash is a safe bootstrap, not a scalable final dependency
  model.
- intended landing point: add a versioned `review_dependencies` contract for
  each review kind. Build deterministic projections such as schematic
  topology = netlist + pin/electrical dossier fields + electrical/RF rules;
  schematic readability = PDF + net-label/pin-identity inputs; PCB layout =
  board + floorplan/routing/fab constraints; fabrication = exact outputs +
  assembly/process/source evidence. Store both the projection hash and its
  enumerated input list in the review.
- safety condition: unknown keys, an undeclared review kind, or a dependency
  extractor that cannot prove full coverage must fall back to the current
  broad hash, never silently narrow freshness. Regression fixtures must change
  one consumed and one unrelated field and require respectively STALE and
  STILL-CURRENT outcomes.
- recommendation: implement before the next board with frequent post-schematic
  sourcing/layout iterations. Do not refactor this during v5 final review; the
  bounded broad-hash renewal is safer than changing provenance semantics under
  an active seal.
- history: 2026-08-13 — proposed after the exact via-process correction made
  the stage-mismatch visible before layout seal.
- follow-up evidence: 2026-08-16 — the USB-controlled debug hub removed two
  retired, electrically unused part dossiers (DMP3007SPS-13 and USBLC6-2SC6)
  because their executable placement rules still entered P-ADJ. The normalized
  netlist remained semantically identical, yet each broad `02_parts` digest
  change required both topology and schematic-render renewal. A downstream-
  only eFuse launch-width rule then required another schematic-readability
  renewal even though the exact PDF bytes were unchanged. The fail-closed
  behavior is safe; the repeated unrelated renewals are the scaling cost this
  improvement is intended to remove.

## IMP-091 — freeze executable assembly-process ownership before placement export

- status: proposed
- observed: Pluto RX2 8-way v5 layout-seal entry, 2026-08-13
- evidence: `assembly.yaml` said J2-J10 would be wave-soldered by JLC *if* the
  uploader accepted C429844, otherwise hand-soldered. That advisory either/or
  left all nine paste-free THT connectors on the SMT CPL but declared neither
  the gate's executable `through_hole: {process, refs, evidence}` path nor a
  `not_assembled` hand-solder path. A-POP therefore found nine
  `CPL-NOT-SMT-PLACEABLE` defects only at final review, after routing and exact
  artifact reviews had already run.
- general rule: population ownership is a source decision, not an order-note
  afterthought. Before the first BOM/CPL export, every fitted paste-free drilled
  part must be assigned to a named purchased THT process, or declared
  `not_assembled` with its disposition and excluded from placement. Conditional
  prose must not allow one CPL to mean two mutually exclusive process plans.
- intended landing point: run A-POP/A-POS immediately after the first board and
  BOM/CPL candidate exist, before placement freeze and routing. Add an early
  source gate that rejects a drilled/paste-free fitted ref unless exactly one
  executable owner covers it. Treat an uploader-dependent fallback as a new
  release branch whose population set and CPL are regenerated, never as an
  in-place order-time edit.
- completion evidence required: a fixture with a THT connector on an SMT CPL
  and only conditional prose must stop before routing; the same fixture must
  pass with a complete purchased-process declaration, and independently pass
  when declared unassembled and absent from the CPL. A ref covered by both
  paths must fail as ambiguous.
- recommendation: implement before the next PCB. V5 now selects JLCPCB THT
  connector assembly as the required path; exact C429844 still needs the normal
  uploader allocation/process echo before payment, and refusal creates a
  separate hand-solder release.
- history: 2026-08-13 — proposed and corrected at v5 layout-seal entry, before
  the seal was minted.

## IMP-092 — make provenance source discovery honor declared source boundaries and ignore policy

- status: proposed
- observed: Pluto RX2 8-way v5 layout seal, 2026-08-13
- evidence: the first exact reviewed-commit seal attempt treated five generated
  two-byte files under `03_tscircuit/.tscircuit/cache/` as source inputs. The
  directory was already excluded by the project's `.gitignore`, its contents
  were tool cache rather than design authority, and the committed source was
  unchanged. Moving the ignored cache out of the project made the same sealed
  source pass without changing a design artifact.
- general rule: provenance must enumerate the declared authoritative inputs of
  a stage. Generated caches, editor state, lock files and build scratch must
  never silently join that authority merely because they appear below a broad
  source directory. A dirty or untracked *authoritative* input must still fail
  closed.
- intended landing point: centralize source discovery behind one policy-aware
  walker. It should consume explicit source roots, honor repository and
  project ignore rules for non-authoritative files, always exclude known tool
  cache/lock families such as `.tscircuit/`, and write the enumerated relative
  path list beside every source digest so unexpected membership is inspectable.
- safety condition: ignore rules must not be able to hide a path explicitly
  declared by a stage contract. Regression fixtures must prove that adding a
  cache file leaves the digest stable, adding an undeclared authoritative
  source fails discovery, and changing a declared-but-ignored source still
  changes the digest or fails loudly.
- recommendation: implement before the next layout seal. Until then, remove or
  relocate ignored generator caches before provenance generation and inspect
  the exact source-member list; do not weaken the reviewed-commit or clean-tree
  requirement.
- history: 2026-08-13 — proposed after the reviewed-commit seal was blocked by
  ignored tsCircuit cache bytes rather than a source or board delta.

## IMP-093 — compare repeated-pad catalog lands as geometry, not merged labels

- status: implementing
- observed: Pluto RX2 8-way v5 final JLC twin, 2026-08-13
- evidence: the exact C429844 catalog footprint and the manufacturer-derived
  901-143-6RFX footprint put all five holes at the same centres to 0.000 mm and
  use the same 2.40/2.80-mm copper diameters. The project preserves four
  distinct shell pins 2/3/4/5; JLC labels all four shell posts `2`.
  `jlc_twin.py` therefore compared one project pad 2 with the centroid of four
  JLC pad-2 instances, reporting a 1.796-mm `PAD-MISMATCH` and a false 3.59-mm
  `PAD-GEOM` delta. The tool correctly failed closed, but could not encode the
  one-to-many naming relationship and required 27 per-ref adjudicated finding
  rows for nine geometrically identical connectors.
- general rule: repeated pad numbers are a naming/multiplicity property, not a
  licence to collapse physical lands into one point. Land-pattern comparison
  must retain every physical instance and expose two independent results:
  numbering/pin-map agreement and numbering-free geometric agreement. A
  geometry pass must never be promoted into an electrical pin-map claim.
- intended landing point: add a deterministic multiset/assignment channel to
  `jlc_twin.py` for repeated labels. Compare complete pad clouds by position,
  shape, drill and layer after rigid transforms, report the winning residual
  and runner-up separation, and keep `PAD-MULTIPLICITY` visible. Permit an
  evidence-bound alias only for electrical identity; do not require an
  impossible one-to-many scalar `pad_alias` merely to measure geometry.
- completion evidence required: the C429844-shaped fixture must report five
  centres matched at 0.000 mm while separately naming the 2-versus-2/3/4/5
  convention and the real 0.10-mm drill delta. A fixture with one moved shell
  post must remain red, and a geometrically symmetric but electrically swapped
  polarized part must still require the independent polarity channel.
- recommendation: implement before the next board with multi-post connectors,
  exposed tabs or duplicated same-net pads. V5 is safely resolved by exact
  manufacturer evidence and retains its explicit uploader DFM gate; changing
  the matcher is not required for this board's release.
- history: 2026-08-13 — proposed after the strict final twin failed safely but
  represented a catalog numbering convention as two geometric failures.
- implementation progress: 2026-08-14 — the renderer and independent
  A-RENDER gate now consume an evidence-bound `mount_anchor` only after a
  whole-pattern fit fails. Each side's named pad must occur exactly once;
  invalid or duplicated datums refuse the run. A C429844-shaped known-bad
  fixture reproduces the old 1.796-mm centroid shift and proves the unique
  signal-hole 1-to-1 datum yields a zero-offset model while retaining the raw
  failed-fit evidence. This closes the false render displacement without
  claiming that numbering or full pad geometry agrees.
- remaining work: the numbering-free multiset/assignment channel described
  above is still open. It must match all five physical lands, report the real
  drill delta, stay red when one post moves and preserve the independent
  polarity channel before IMP-093 can be marked completed.

## IMP-094 — bind review contracts to the exporter artifact index

- status: partially implemented
- observed: Pluto RX2 8-way v5 fabrication entry, 2026-08-13
- evidence: `rf.yaml` named
  `06_build/fab/pluto_rx2_8way_v5-gerbers.zip`, while the strict exporter
  deterministically emitted
  `06_build/fab/pluto_rx2_8way_v5_gerbers.zip`. The PCB, plots and review intent
  were sound; one hand-typed hyphen made the exact-artifact RF review contract
  point at a nonexistent file. The mismatch was corrected before review and
  changed no fabrication bytes.
- general rule: a producer-generated artifact name is output metadata. A
  downstream exact-artifact contract should select it through one emitted
  index or an unambiguous role query, not restate the producer's filename
  convention. If a path is retained for human readability, post-export
  contract binding must run immediately and fail before review work begins.
- intended landing point: have `export_jlc_package.py` emit a versioned
  `artifact_index.json` with roles such as `gerber_archive`, `bom`, `cpl`,
  `pth_drill` and `npth_drill`, each carrying relative path and SHA-256.
  Extend `rf_contract_check.py` to resolve the fab artifact by role and compare
  any declared path/hash against that index at fabrication entry.
- completion evidence required: a filename-convention change must keep a
  role-bound review current, while a hand-declared stale path, two candidate
  Gerber archives, a missing role or a changed artifact hash must fail before
  the review is dispatched. The index itself must be regenerated and shipped
  with the release evidence.
- recommendation: implement before renaming another exporter or board stem.
  V5's source path is corrected now, so this is not a blocker for its current
  fabrication stage.
- history: 2026-08-13 — proposed after exact-artifact review setup found the
  hyphen-versus-underscore path mismatch before any release was sealed.
- implementation progress: 2026-08-17 — `export_jlc_package.py` now writes
  schema-1 `artifact_index.json` with the exact board and role-keyed hash/size
  records for Gerber archive, BOM, CPL, all drill files and the optional via
  note; the exporter regression requires the four core roles. RF/review
  contracts do not yet resolve their subject through the index, so IMP-094
  remains partial.

## IMP-095 — dispatch exact-artifact reviews from a machine-written envelope

- status: proposed
- observed: Pluto RX2 8-way v5 RF fabrication review dispatch, 2026-08-13
- evidence: after source commit `9706143a`, the coordinator sent the reviewer
  a manually expanded 40-character SHA that did not exist. The reviewer
  independently ran `git rev-parse HEAD`, found the disagreement, and refused
  to bind the review until the exact
  `9706143aea030b4e4ddddcd72e5e55293f3b19e8` value was confirmed. No review or
  release was misbound, but correctness depended on reviewer suspicion rather
  than a dispatch mechanism.
- general rule: exact commit IDs, artifact paths and digests are machine data.
  They must travel to a reviewer as one generated, immutable envelope; prose
  may explain the task but must not restate or expand identifiers by hand. The
  reviewer must verify the envelope against local bytes before writing a
  verdict.
- intended landing point: add a small review-dispatch producer that records
  schema version, project/board, exact `git rev-parse` commit, scoped dirty
  result, artifact path/role/SHA-256, contract path/SHA-256 and requested
  requirement IDs. Make review freshness validate the copied header against
  that envelope. Where IMP-094's exporter index exists, consume it rather than
  rediscovering the fab path.
- completion evidence required: a nonexistent expanded SHA, a one-character
  artifact digest error, a dirty consumed input and a path selecting a sibling
  artifact must all fail before review text is accepted. A clean envelope must
  round-trip its exact identifiers into the archived review without manual
  copy/paste.
- recommendation: implement with IMP-094, before the next exact-artifact review
  fan-out. V5's reviewer caught and corrected the dispatch before finalizing,
  so its present review can bind safely to the machine-read commit and is not
  blocked.
- history: 2026-08-13 — proposed after the independent reviewer detected the
  coordinator's invalid hand-expanded commit ID.

## IMP-096 — derive release PDF pages from populated sides and document purpose

- status: proposed
- observed: Pluto RX2 8-way v5 release-asset export, 2026-08-13
- evidence: the generic assembly command plotted
  `F.Silkscreen,B.Silkscreen,F.Fab,B.Fab,F.Courtyard,B.Courtyard,Edge.Cuts`
  as seven separate pages on a top-only board. Four pages were blank or only a
  title block/outline, while the F.Fab page overlaid values and catalog-like
  text densely enough to weaken its locator purpose. A purpose-derived export
  instead produced three nonblank pages: top silk, top fab with pad numbers and
  reference designators but values excluded, and top courtyard, each with the
  board edge as a common layer. The PCB layer packet similarly fell from nine
  pages to seven by dropping the empty bottom-silk page and making Edge.Cuts a
  common reference rather than a near-empty standalone page.
- general rule: a release PDF is a human verification artifact, not a dump of
  every possible layer name. Its page denominator must be derived from actual
  populated sides, nonempty layer content and the document's purpose. Edge
  geometry should appear as a common registration reference; assembly pages
  should prioritize refdes/pin/polarity legibility over repeating BOM values.
- intended landing point: replace ad-hoc `kicad-cli pcb export pdf` invocations
  with a shared release-PDF producer. It should inspect the board, select only
  meaningful top/bottom assembly layers, emit a page manifest naming each
  page's role, rasterize every page, and reject blank/near-blank pages or pages
  whose critical identifiers are missing/occluded. Preserve an explicit
  diagnostic mode that can still dump every layer when needed.
- completion evidence required: a top-only board produces no bottom assembly
  pages; a populated two-sided board produces both; Edge.Cuts is visible on
  every page; a known blank layer and a deliberately obscured polarity/refdes
  fixture both fail. The producer must prove fresh nonempty output rather than
  accepting a stale PDF after a CLI parse warning.
- recommendation: implement before the next release asset stage. V5's current
  generated 7-page PCB and 3-page assembly packets have been visually checked,
  so the shared producer is not a blocker for this board.
- history: 2026-08-13 — proposed after the first mechanically successful PDF
  export was visibly poor as a human assembly packet.

## IMP-097 — preserve schematic-sheet coordinate domains in native conversion

- status: completed
- observed: Pluto RX2 8-way v5 hardware-release audit, 2026-08-13
- evidence: the TSX human schematic contained four independently readable
  authored sheets, but `circuit_json_to_kicad_sch.py` treated every sheet's
  local coordinates as one global plane. The resulting native KiCad schematic
  superimposed J1/J2, U1/U2 and four value/reference fields. The rendered TSX
  PDF looked correct, so reviewing only that publication artifact hid the
  defective native source until full `S-OCCL` release grading found six exact
  overlaps.
- general rule: a schematic sheet identifier defines a coordinate domain.
  Geometry from separate domains must be emitted as separate native sheets or
  assigned deterministic non-overlapping regions before any global transform.
  A readable publication PDF does not prove the editable/native schematic is
  readable.
- landed at: the shared layout-preserving converter now computes bounds per
  `schematic_sheet_id`, orders pages by the authored `sheet_index`, stacks
  their unchanged local geometry into non-overlapping regions, and restricts
  port resolution to the trace's own sheet. The converter still proves the
  exported netlist independently against the board.
- completion evidence: a regression gives two authored sheets identical local
  component coordinates and requires different emitted KiCad coordinates,
  four exported nodes and zero native schematic occlusions. The full converter
  suite passes 44/44. Pluto v5's regenerated native schematic has 202/202
  drawable objects placed, zero text occlusions, zero two-net conductor events
  and exact 22-net/131-node parity with the unchanged routed board.
- recommendation: carry this fix immediately. Keep both human-render review
  and native `S-OCCL`/netlist parity as independent gates; neither subsumes the
  other.
- history: 2026-08-13 — found and fixed during hardware-only release audit;
  firmware was not read or invoked.

## IMP-098 — make clean replay produce every ignored review prerequisite it consumes

- status: proposed
- observed: Pluto RX2 8-way v5 hardware-release clean replay, 2026-08-13
- evidence: a fresh worktree at committed source stopped at placement review
  because `06_build/pre_route/twin_overlay.md` was absent. The replay driver
  requires and freshness-checks that derived report, but neither the driver nor
  an earlier declared stage produced it; the report is correctly ignored as a
  build artifact. Running the strict pre-route fab exporter, JLC twin producer
  and overlay grader created it, after which the unchanged replay passed all
  four placement-review bindings and continued to DRC 0/0/0.
- general rule: a clean-build driver may consume an ignored artifact only when
  its dependency graph contains a deterministic producer edge before the first
  consumer. A freshness check is not a producer, and a file left behind by a
  prior interactive run is not reproducibility evidence.
- intended landing point: express the pre-route twin and overlay as an explicit
  pipeline stage with declared source/config/model inputs, bounded execution,
  outputs and review invalidators. `rebuild_reuse.sh` should run that stage—or
  invoke one checkpoint-aware producer—before `pre_route_review_check.py`.
  Keep the review itself human-authored and committed; only its derived subject
  and machine report are regenerated.
- completion evidence required: delete or use a clean checkout with no
  `06_build/pre_route`; one command must reproduce the twin/report and reach
  the placement gate. A missing model, stale board hash, or failed overlay must
  still stop before route import. A stale ignored report must never satisfy the
  gate without its producer running or authenticating its inputs.
- recommendation: implement before the next board's placement-review replay.
  V5's exact prerequisite was regenerated and verified, so this is no longer a
  blocker for its hardware release.
- history: 2026-08-13 — proposed after the first genuinely clean v5 release
  replay exposed a hidden dependency on an ignored prior-run artifact.
- follow-up: the 2026-08-14 J12 renewal confirmed that this producer also needs
  a role-scoped output namespace. Writing a preliminary package under
  `06_build/pre_route/fab/` created valid `bom.csv`, `cpl.csv` and Gerber bytes,
  but the observation audit correctly reported an unresolved selection because
  canonical consumers select `06_build/fab/<basename>` while a second copy of
  the same basename existed elsewhere under the project. The temporary package
  was moved outside the subject and only uniquely named pre-route BOM/CPL
  witnesses were retained. The intended producer should emit a role-indexed
  artifact bundle (IMP-094), not introduce plausible same-basename alternatives
  into a tree whose consumers still resolve by path convention.

## IMP-099 — seed every late KiCad writer, not only board and route preparation

- status: completed
- observed: Pluto RX2 8-way v5 hardware-release reproducibility proof,
  2026-08-13
- evidence: the committed and first clean-replayed boards had identical
  electrical copper multisets (880/880 items), footprint placements (36/36)
  and pad geometry/net assignments (171/171), yet their PCB SHA-256 digests
  differed. Replotting showed 9/13 fabrication members identical after timestamp
  normalization; all four copper Gerbers differed. The cause was unseeded UUID
  creation in KRT import and multi-process stitch writers. KiCad save order
  changed, and F.Cu fill differed by six nanometre-scale tessellation vertices.
- general rule: deterministic generation ends at the last object-creating
  writer. Seeding only the base-board generator or route-prep stage is
  insufficient when import, taps, stitching, fencing, island healing, or
  barrier-resumed processes can mint tracks/vias. Each writer needs a stable,
  disjoint namespace; barrier resumptions must include the authenticated pass
  index so they neither randomize nor reuse a prior writer's UUID stream.
- landed at: `import_krt.py` now seeds a board-namespaced `route-import` UUID
  stream. `route_and_stitch_generic.py` provides phase-namespaced seeding for
  optional tap attempts and each stitch interpreter/resume index. A regression
  imports the same chain twice and requires byte-identical boards with no
  duplicate UUIDs.
- completion evidence: two complete v5 clean replays both passed DRC 0/0/0 and
  produced byte-identical PCB SHA-256
  `43689fe44daa2bd437979c573e78da39a51aacd9d4664a24e7e29bc1c22ea0b3`.
  The focused import regression passes. Final release export will recheck all
  Gerber/drill members from this canonical board.
- recommendation: carry immediately; implemented for the shared pipeline and
  exercised by v5 before sealing. Retain semantic copper comparison as a useful
  diagnostic, but do not treat it as a substitute for deterministic source and
  fabrication bytes.
- history: 2026-08-13 — found, generalized, fixed and double-replay verified
  before the v5 hardware release was assembled.

## IMP-100 — validate assembly semantics before release staging

- status: proposed
- observed: Pluto RX2 8-way v5 hardware-release staging, 2026-08-13
- evidence: `assembly.yaml` used the descriptive scalar
  `build_quantity: 5_first_articles`, which reached
  `release_freshness_check.py` and raised an uncaught integer-conversion
  exception instead of producing a gate result. The same file also used
  `sourcing_plan:` as a convenient complete BOM/function map. The release gate
  correctly interprets that field as an exception plan for a stock shortfall,
  so all 13 otherwise-stocked BOM lines became incomplete plans with no
  measured stock/date. The current board was repaired to numeric
  `build_quantity: 5` and `sourcing_plan: []`; exact BOM mapping remains in
  its proper circuit/dossier authorities.
- general rule: validate configuration by semantic role at the earliest
  schema boundary. `build_quantity` is a positive integer, not a display
  label. `sourcing_plan` contains only measured exception/disposition records,
  never the normal BOM population or a shopping list. A consumer must report a
  schema failure rather than crash on a malformed value.
- intended landing point: add an assembly-schema validator to commission/source
  preflight and reuse it from the exporter, stock gate and release gate. Give
  ordinary part mapping its existing authoritative homes rather than adding a
  second assembly-side map. Harden `release_freshness_check.py` so invalid
  types return a named fail-closed finding with path and field.
- completion evidence required: fixtures for a descriptive quantity, zero or
  negative quantity, a normal BOM row misfiled as `sourcing_plan`, and a valid
  measured stock-shortfall plan. Every malformed fixture must fail before PCB
  generation or market queries and none may raise a traceback.
- recommendation: implement before the next project reaches sourcing or
  release staging. Pluto v5's source and sealed copy are corrected, so this is
  not a blocker for its present hardware archive.
- history: 2026-08-13 — recorded after the first shipped-byte freshness run
  exposed both schema/semantic defects despite a passing live stock report.

## IMP-101 — make local PCB ECO routing preserve the validated copper baseline

- status: proposed
- observed: Pluto RX2 8-way v5 J12 bench-power renewal, 2026-08-14
- evidence: adding one two-pin connector outside the RF core required only two
  deterministic `VBUS_RAW` segments. A fresh whole-board stochastic route ran
  quickly but attempted a new via inside R6.1 and was correctly rejected by the
  via-in-pad guard. Importing the already validated promoted route onto the new
  exact base, then importing only the two J12 segments, produced a clean board.
  Exact comparison proved all 236 earlier tracks and 57 earlier vias unchanged
  to the nanometre limit; stitch, RF-fence, via-process and DRC gates then
  passed. The useful result came from treating the change as a bounded ECO, not
  from reopening a solved global search.
- general rule: when a placement-compatible promoted route exists and the
  design change has a small declared copper boundary, prefer an explicit ECO
  transaction: authenticate the old route against the new base, import it,
  add only declared deterministic delta copper, prove the protected baseline
  geometry is unchanged, then rerun every downstream connectivity, plane,
  process, RF and DRC gate. Never preserve old copper merely because it loads;
  P-ROUTEBASE and the post-import diff are both mandatory.
- intended landing point: extend the shared route orchestrator with an `eco`
  mode and a small YAML contract naming allowed added/removed refs, nets and
  copper-object budgets. Emit a machine-readable before/after geometry report
  and reject any undeclared track/via movement before stitch. If compatibility
  or the declared delta proof fails, fall back to a bounded fresh route rather
  than weakening the comparison.
- completion evidence required: fixtures for a clean one-connector/two-track
  ECO, a moved old track, an undeclared removed via, a changed pad/net, and a
  legitimate placement-incompatible change that must request a fresh route.
  The clean fixture must reproduce identical protected-baseline geometry across
  two runs and finish with the normal saved-board gates.
- recommendation: implement before the next local connector, test-point or
  protection-component PCB revision. The Pluto candidate itself is already
  covered by an exact manual migration/diff and full downstream replay, so this
  is a pipeline generalization rather than a blocker for the current board.
- relationship: IMP-040 proves that promoted copper is compatible with the new
  base before review; IMP-083 rejects unsafe router vias; this improvement adds
  an explicit minimal-change execution path between those two controls.

## IMP-102 — make RF expertise a conditional, bounded evidence module

- status: completed
- observed: Pluto RX2 8-way v5 RF routing/fence audit, 2026-08-14
- evidence: the board has nine declared 50-ohm CPWG paths and a passing
  18/18 saved-board fence result, but the retained invocation graded a default
  +/-2.5 mm lateral band while the route emitter actually searched +/-1.10 mm.
  Its authored RF polylines also contain 14 direction changes (12 above 20
  degrees, maximum 67.92 degrees), while the shared fence emitter and checker
  previously rejected native track arcs. Adding a generic RF reviewer or live
  research step would have added another quiet wait boundary; one earlier
  local field-solver run had already been silent for 35.724 seconds.
- general rule: RF specialization is conditional data and executable geometry
  inside the existing schematic/routing/seal lifecycle. It must not create a
  fourth pipeline owner, a new agent wait, or runtime web research. Separate
  normative/background/tool-capability/precedent voices; default clean-room
  context excludes prior-board results. Grade authored geometry before
  generation and independently reopen realized board bytes before PCB review.
- landed at: `references/rf/` contains validated local source cards and the
  bounded procedure. `rf_context.py` selects them offline. `rf_solver.py` runs
  only declared pending local jobs with direct argv, input/output manifests,
  streamed output, heartbeat, hard deadline, process-group termination and
  exact cache reuse. `rf_check.py` emits source/realized atomic bundles and
  binds the realized fence report to the exact board. `rf_contract_check.py`
  validates opt-in `rf-module-v1`, bend policy, one fence-band authority and
  review evidence hashes. `pcb_flow.py` and both rebuild templates place these
  operations in the existing bounded stages, without launching reviewers.
- geometry capability: deterministic seed routes and the independent fence
  gate now retain native KiCad `PCB_ARC` primitives and measure their true
  arclength. Bend policy begins advisory; blocking requires an explicit
  radius/width threshold and measured-site exceptions. This avoids requiring
  arcs before emission, collision checking, idempotency, fence projection and
  saved-board audit all understand them.
- Pluto result: the legacy board remains unchanged and passes source coverage
  9/9 plus realized coverage 9/9 and fence coverage 18/18 at the actual
  +/-1.10 mm band. It reports the 14 bends and route-only band authority as
  advisories. A future source revision can adopt `rf-module-v1`, promote
  `maximum_lateral_center_offset_mm: 1.10` into `rf.yaml`, choose which bends
  to round, and then request fresh exact-evidence reviews. Existing release
  bytes are not silently reclassified.
- completion evidence: focused clean/known-bad tests cover clean-room source
  selection, advisory versus blocking bends, exact stable bundle reuse,
  solver timeout termination, review-to-realized-board binding, contract/route
  band disagreement, missing bundle outputs, native arc emission/idempotency,
  independent arc fence measurement, YAML segment-boundary corners, and
  non-tangent line/arc joins. The Pluto v5 pipeline canaries pass 11/11 and
  7/7 for its two supported rebuild paths, the USB/non-RF canary passes 9/9,
  and the full `pcb_flow` regression passes 40/40. The non-RF source and
  realized gates also prove an immediate N-A path without loading a route
  contract or board.
- recommendation: carry immediately for new RF boards in advisory mode; adopt
  blocking geometry only after the board deliberately updates its source
  contract and reviews. Keep non-RF projects on the immediate N-A path.
- history: 2026-08-14 — audited, modularized and integrated after the Pluto
  board exposed both an authority gap and an end-to-end arc capability gap.

## IMP-103 — model protected distribution rails explicitly

- status: completed
- observed: Raspberry Pi USB port switch commission/source preflight,
  2026-08-14
- evidence: the board's four downstream VBUS paths are pass-through
  distribution rails fed through a shared fuse and reverse-polarity MOSFET,
  then one TPS2557 load switch per port. `power_tree.yaml` can express their
  load, voltage and resistance budgets, but the topology and margin validators
  previously required every external rail to name a buck, boost or linear
  `converter`. With no truthful converter to name, `power_topology.py --margin`
  reported load errors instead of checking the load-switch path. Inventing a
  converter would have made the artifact pass while corrupting its circuit
  model.
- general rule: a power contract must distinguish conversion rails from
  protected distribution rails. Both are real power stages, but distribution
  is governed by switch/pass-FET current, resistance, current limit,
  reverse-current behavior and voltage-drop budget rather than efficiency and
  regulator equations.
- landed at: `power_topology.py` accepts the explicit
  `stage: distribution` form and requires an exact non-empty series-device
  population, worst-case path resistance, a current-limit window covering the
  commissioned load, reverse-current policy and the normal Vin/Vout envelope.
  It resolves every device against `02_parts`, grades the distribution path
  without inventing a converter, includes its constant-current load in the
  input-trunk calculation, and gives E-MARGIN the same resistance authority.
- completion evidence: `tests/t1_power_topology.py` covers a valid protected
  distribution path and known-bad missing-device and under-current-limit
  fixtures while retaining the converter and linear-regulator regressions. The
  Pi USB fixture passes D-SPEC/E-PATH 3/3, E-TOPO 5/5 rails with one real
  converter, and E-MARGIN 4/4 external rails.
- recommendation: carry for every switched or pass-through power board; never
  express a load switch, eFuse or pass FET as a fictitious converter.
- history: 2026-08-14 — recorded when the four-channel USB fixture exposed the
  schema gap during the first complete loaded-plug voltage-drop audit.
- history: 2026-08-15 — implemented in the shared checker and contract with
  clean/known-bad regressions before this board began schematic capture.

## IMP-104 — retain per-row JLC evidence in mixed-source BOMs

- status: completed
- observed: Raspberry Pi USB port switch Q-2SOURCE composition, 2026-08-14
- evidence: its candidate BOM has exact JLC/LCSC codes alongside intentional
  global/user-fit rows. `jlc_stock_check.py` correctly graded the coded rows and
  explicitly reported uncoded rows, but `shopping_list.py` previously required
  `graded_lines == total_lines`. That discarded the entire JLC pool, so a
  fully stocked resistor or IC lost valid evidence merely because an unrelated
  connector had no LCSC code.
- general rule: source qualification is per exact row. An explicitly uncoded
  row is ineligible for the JLC pool and must clear two other authorized pools;
  it must not invalidate exact, fresh JLC evidence for coded rows.
- landed at: `shopping_list.py` validates the sidecar coverage identity
  `graded_lines + uncoded_lines == total_lines` and requires the line count to
  equal `graded_lines`. It preserves JLC grading for coded rows while returning
  `NO-LCSC` only on the uncoded row.
- completion evidence: `tests/t1_shopping_list.py` includes a mixed two-row
  fixture where the coded part qualifies through JLC plus DigiKey and the
  uncoded part independently qualifies through Mouser plus DigiKey. Corrupt
  counters and missing coded rows remain fail-closed through consistency
  checks.
- recommendation: carry immediately; this is required for any JLC assembly
  containing a hand-fit fuse, globally sourced connector, consigned part or
  other intentional non-LCSC line.
- history: 2026-08-14 — generalized, fixed and regression-tested at the first
  mixed-source Q-2SOURCE run for the four-channel USB fixture.

## IMP-105 — separate early high-speed authority from placed route primitives

- status: completed
- observed: Raspberry Pi four-channel USB 3 inline switch source preflight,
  2026-08-15
- evidence: after exact USB pin maps were locked, the project could truthfully
  declare its SuperSpeed and USB 2 pair inventory, named JLC stackup, 90-ohm
  intent, zero-via preference and first-article link tests. The conditional RF
  module previously presented an all-or-nothing source shape: a locked
  cross-section made `rf_check.py source` require coordinate-level route
  primitives before a floorplan or component coordinates existed. Inventing
  route primitives would have made the gate pass by corrupting its evidence.
- general rule: controlled-impedance applicability, exact pair inventory and
  stackup/cross-section authority are source-stage facts; coordinate-level
  route primitives are placement-stage facts. Microwave boards may choose to
  author geometry earlier, but ordinary high-speed digital boards should not
  be forced either to pre-place the board before schematic capture or to
  disable SI applicability.
- landed at: `rf.process.geometry_stage` is a closed `source|placement`
  lifecycle owner. Source still requires ports/pairs, risk tier, named stackup,
  target impedance, reference plane, allowed layers/vias/stubs, performance
  claims and either a locked cross-section or an honest bounded solver job. It
  may explicitly defer `layout_constraints` primitives to placement, where
  `rf_check.py source --require-geometry` requires the complete exact-net
  denominator before route preparation. Existing contracts default to source
  ownership, preserving stricter microwave behavior.
- completion evidence: a USB 3-style fixture passes source with locked
  pair/stackup authority and no invented coordinates, then fails placement if
  a critical pair lacks a planned route bank. The Pluto microwave canary keeps
  its source-level blocking behavior. Pending solver jobs, empty pair
  inventories and locked geometries with no later placement owner still fail
  closed through `tests/t1_rf_module.py` and `tests/t1_rf_contract.py`.
- recommendation: use placement ownership for ordinary high-speed digital
  boards and retain source ownership for microwave designs whose floorplan and
  route geometry are intentionally part of early architecture.
- history: 2026-08-15 — implemented and regression-tested before the Pi USB
  board began TSX capture; schema-reader governance covers the new authority.

## IMP-106 — refactor PCB skills around progressive disclosure without moving execution authority

- status: completed
- observed: repository-wide review after USB Hub 3S v4, Pluto RX2 8-way v5,
  and Raspberry Pi USB switch work, 2026-08-15
- evidence: `skills/pcb-design/SKILL.md` had grown to 1,470 lines / 14,601
  words and mixed lifecycle authority, incidents, JLC mechanics, layout
  mechanics, gate invocation detail, and reference routing. The duplication
  made it difficult to know which statement owned a decision and caused every
  board task to load procedures that did not apply. The JLC skill had the same
  smaller form at 593 lines / 5,601 words.
- general rule: progressive disclosure is an information-architecture change,
  not permission to alter board behavior. Keep a small entry kernel containing
  scope, lifecycle, decision rules, invariants, and a direct reference router.
  Give each domain one owner; move detailed procedure to that owner's named
  reference. Preserve current project drivers, scripts, gates, review pauses,
  seal rules, and publication rules until separate execution-equivalence
  canaries authorize a migration.
- landed at: `skills/pcb-design/SKILL.md` is a 260-line / 1,819-word
  orchestration kernel and `skills/jlcpcb-fab/SKILL.md` is a 134-line /
  861-word manufacturer adapter. `skill-authority-map.json` declares 14
  single-owner domains, 19 routed references, a typed capability-to-stage
  catalog, and the frozen pre-refactor source commit. The pure
  `skill_reference_router.py` selects stage-local authorities for ordinary,
  high-speed digital, RF, mating, JLC, and lifecycle target conditions; it
  cannot execute, retry, promote, review, seal, or publish anything.
- compatibility rule: `skill_authority_check.py` requires the PCB core to stay
  within 250--400 lines and 5,000 words, routes every long procedure directly,
  rejects duplicate authority, and proves all 109/109 pre-refactor policy/gate
  IDs remain reachable. Exact typed traces are pinned for a simple board, USB
  Hub v4, Raspberry Pi USB, and Pluto RF release. Firmware remains forbidden
  by default; an explicit request creates only a separate handoff, never a PCB
  pipeline stage.
- completion evidence: `tests/t1_skill_progressive_disclosure.py` passes nine
  clean, known-bad, and declared-vacuity cases, including an unregistered
  assembly adapter, duplicate A-ROT ownership, and the lexical limits of the
  router/authority audit. The existing USB and Pluto v4 catalog canaries,
  stage contract/registry, rebuild templates, and rotation-authority suites
  remain green. Both refactored skills pass the skill-creator schema validator.
  `tests/t1_contracts.py` now checks the routed Markdown corpus rather than
  assuming every policy appears in the monolithic entry file.
- recommendation: carry immediately for all new and resumed boards. Treat any
  future change to stage order, applicability, gate predicate, artifact,
  review pause, backtrack target, seal, or publication behavior as a separate
  migration requiring clean and known-bad tests plus USB and Pluto trace
  comparison. Preserve the old skill only through Git history; do not maintain
  a second live legacy manual.
- history: 2026-08-15 — implemented on a dedicated branch with a frozen legacy
  denominator and behavior-first compatibility fixtures before documentation
  or publication.

## IMP-107 — make footprint side a first-class floorplan property

- status: completed
- observed: USB-controlled debug hub placement, 2026-08-16
- evidence: keeping each USBLC6 ESD array and FSUSB42 data switch inside its
  electrical distance budget while four large THT USB-A bodies occupied the
  same top-side cells required nine deliberate bottom-side placements. The
  generic generator previously had no declarative side input; a project would
  have needed a board-specific postprocessor, and flipping a detached pcbnew
  footprint before it belonged to a board caused a native crash.
- general rule: side is authored placement intent, alongside coordinate and
  rotation. The generator must validate a closed `top|bottom` vocabulary,
  reject unknown references, add the footprint to its board before flipping,
  and grade body collisions only between parts on the same assembly side.
  Copper overlap and pad-short checks remain side-independent.
- landed at: `placement.sides` in `floorplan.yaml`, consumed by
  `generate_board_generic.py`; project and template contracts document the
  field. The generator reports its bottom-side denominator and the USB hub
  regenerates deterministically with nine B.Cu footprints.
- completion evidence: `tests/t1_generate_board.py` proves a named footprint
  flips while an undeclared control stays top, and that invalid side values or
  unknown references fail before board output. The existing pad-overlap and
  courtyard suites remain green.
- recommendation: use only where the electrical/mechanical floorplan benefits;
  keep ordinary single-sided assembly as the implicit top-side default.

## IMP-108 — scope physical adjacency budgets to the electrical path they protect

- status: completed
- observed: USB-controlled debug hub ESD placement, 2026-08-16
- evidence: each USBLC6 array shares D+, D-, VBUS and GND with its connector,
  but the 2 mm placement obligation exists to control the high-speed clamp
  path. Grading the pair over every shared net incorrectly selected the remote
  VBUS clamp-reference branch and made a correct in-line data placement look
  impossible.
- general rule: a physical adjacency row may name the exact shared net or net
  set whose path creates the distance requirement. Every named net must exist
  on both declared references; a typo or non-shared name is UNREACHED, never a
  fallback to some other shared connection. Omitting `nets` preserves the
  conservative all-shared-net behavior.
- landed at: optional `layout.adjacency[].nets` in `part.yaml`, consumed by
  `policy_audit.py` and documented in the project/template part contracts. The
  USB ESD rules scope the tight budget to D+/D- and the placed board closes all
  38/38 measurable layout budgets.
- completion evidence: `tests/t1_escape_tier.py` covers a valid scoped shared
  net and a non-shared name that fails P-ADJ-UNREACHED.
- recommendation: use for ESD, filters, current-sense and feedback structures
  where a part pair shares unrelated support nets; do not use it to hide a bad
  layout on another electrically critical shared path.

## IMP-109 — preserve every actionable finding in durable gate reports

- status: completed
- observed: USB-controlled debug hub placement iteration, 2026-08-16
- evidence: the placement policy console intentionally printed only the first
  five adjacency failures, but the same truncation reached the durable report.
  Fixing those five and rerunning exposed the next set, turning one bounded
  placement diagnosis into a serial whack-a-mole loop.
- general rule: console output may be bounded for readability; the persisted
  diagnostic artifact must enumerate the complete actionable denominator.
  Summary counts and representative samples are navigation aids, not a
  substitute for the full finding set needed to make one corrective pass.
- landed at: `policy_audit.py` retains bounded console presentation while its
  Markdown report writes every P-ADJ finding.
- completion evidence: `tests/t1_escape_tier.py` creates six independent
  violations and requires all six to appear in the durable report.
- recommendation: apply this pattern to every iterative geometry, sourcing and
  release gate; if a complete set is too large, write a structured sidecar and
  link it from the bounded summary rather than discarding rows.

## IMP-110 — measure every disconnected body island in native-model registration coupons

- status: completed
- observed: USB-controlled debug hub connector registration, 2026-08-16
- evidence: exact USB connector STEP files render as several disconnected
  shell, housing and retention-feature pixel islands. The registration gate's
  nearest-connected-component rule measured only one USB-B shell edge. That
  falsely reported all six drilled centres outside the body and, more
  importantly, hid body excursions visible elsewhere in the same model.
- general rule: same-camera populated-minus-bare coupons with exactly one
  provenance-bound model per search window own every surviving unblocked
  difference island. Their measurement must union those islands before
  comparing F.Fab, courtyard and attachment datums. Crowded whole-board twin
  images retain nearest-component behavior because unrelated neighboring
  bodies can occupy the search window.
- landed at: `extract_body(..., union_components=True)` is used only by
  `native_model_registration.py`; the default remains false for catalog-twin
  callers. This exposed and enabled correction of the terminal translation,
  USB-A registration and USB-B courtyard before routing.
- completion evidence: `tests/t1_twin_overlay.py` supplies two disconnected
  populated-minus-bare body islands and proves native coupon mode spans both
  while the default mode selects only the seeded component. The live project
  now passes P-MODEL-REG for 3/3 model tuples and 32/32 drilled centres.
- recommendation: carry immediately for all native STEP registration. Keep the
  one-model coupon invariant explicit; never enable union mode on a populated
  multi-part board without an independent pixel ownership partition.

## IMP-111 — canonicalize producer-private repeated-pad identities before physical pin comparison

- status: completed
- observed: USB-controlled debug hub pin-map preflight, 2026-08-16
- evidence: tscircuit represents the second occurrence of a repeated numeric
  connector pad with a private source-port hint such as
  `pin5_internal_1`, followed by the canonical `pin5` hint. P-PINMAP selected
  the first string and reported a fictitious sixth physical identity on every
  USB connector even though both shell stakes intentionally share pad 5 in the
  exact footprint and board.
- general rule: producer-private identifiers must not enter the physical pin
  denominator. When a source port has no explicit `pin_number`, ignore
  `_internal_N` hint suffixes and select its canonical pin hint. Do not add a
  fake dossier pin or alias merely to satisfy one producer's object identity.
- landed at: `pin_map_check.py` skips internal repeated-pad hints while
  retaining the canonical hint on the same source port. The live board passes
  293 declared identities over 27 multi-pin references.
- completion evidence: `tests/t1_pin_map.py` reproduces the extra internal
  source port and proves the physical denominator remains eight; missing pins,
  unevidenced aliases, unlike-function collapses and zero coverage still fail.
- recommendation: keep this normalization narrow to the documented suffix and
  require the canonical hint to exist; unrelated named pins must remain visible
  as extra identities.

## IMP-112 — give headless rendering the same model environment as body coverage

- status: completed
- observed: USB-controlled debug hub placement render, 2026-08-16
- evidence: P-MODEL passed 133/133 because it resolved stock KiCad STEP files
  under the user data tree, but a raw `kicad-cli pcb render` received no
  `KICAD10_3DMODEL_DIR` definition. It exited zero and drew the project-local
  exact connector bodies while silently omitting ordinary SOIC, SSOP, TSSOP,
  resistor, capacitor, fuse and crystal bodies. The image looked plausible
  until a high-resolution crop exposed empty IC outlines.
- general rule: a model-coverage resolver and the renderer must consume one
  explicit environment. A successful raw render is neither coverage nor proof
  that its variable table matches the preflight. The canonical invocation must
  pass every model-directory token used by the saved board and refuse any
  unresolved reference before image generation.
- landed at: `render_board.py` reuses `model_coverage_check.py` resolution,
  injects referenced variables through `kicad-cli -D`, verifies a fresh non-
  empty output, and supports a JSON `--dry-run` command receipt. Its use
  restored every stock package body in the placement render without changing
  the board.
- completion evidence: `tests/t1_render_board.py` proves the exact
  `KICAD10_3DMODEL_DIR` value reaches renderer argv and that an unresolved
  saved-board model blocks before rendering. The live corrected top view shows
  the previously absent controller, expander and two logic-package bodies.
- recommendation: use this wrapper for every placement, routed and release
  KiCad render; reserve raw `kicad-cli pcb render` for isolated diagnostics
  whose model environment is supplied explicitly.

## IMP-113 — exercise refactored skill authority with a real release-target canary

- status: completed
- observed: USB-controlled debug hub canonical schematic rebuild, 2026-08-16
- evidence: the progressive-disclosure router and its four normalized profile
  traces passed, but the first real `capability-profile: release` rebuild found
  twelve source keys without a central authority row. Six were real fields
  already consumed by board generation or length auditing; six were duplicate
  prose or distributor/power-envelope declarations with no reader. The gate
  stopped in 2.1 seconds before TSX generation, so no invalid review or routing
  work survived the discovery.
- general rule: a documentation/authority refactor needs both normalized trace
  equivalence and at least one complete real-project execution through every
  intentional pause. Static routing proves references are reachable; a live
  release-target canary proves the selected references, source schemas,
  ratchets, producers, hashes and resume boundaries compose in practice.
- landed at: exact child authority rows now cover corridor `layers`/`width_mm`,
  model-override `file`/transform vectors, and length-match `router_moves`.
  Unread duplicate fields were removed from the live project rather than
  legitimized as second authorities. `schema_reader_audit.py` advances its
  monotone floor to 18 governed families / 608 proven fields, and the live
  board reaches the intended hash-bound pre-route review stop.
- completion evidence: `tests/t1_skill_progressive_disclosure.py` passes 9/9,
  `tests/t1_schema_reader.py` passes 27/27, and
  `tests/t1_generate_board.py` passes 52/52 including known-bad corridor and
  model-override fixtures. The live rebuild now passes 59/59 electrical
  invariants, 4/4 ADR coverage, 139/139 component parity and zero ERC errors;
  the refactored lifecycle also reaches its placement-review stop with clean
  placement DRC and P-MODEL-REG 4/4.
- recommendation: after any future refactor that changes authority routing,
  schema ownership or lifecycle composition, run one ordinary and one
  conditional-domain project to their next intentional review pause before
  calling the migration complete.

## IMP-114 — close aggregate fault, effective-capacitance and device-specific startup envelopes before placement

- status: completed
- observed: USB-controlled debug hub independent pre-route review, 2026-08-16
- evidence: a readable, ERC-clean 133-part schematic still carried only
  32.6 uF of charged always-connected VBUS bulk against a 120 uF USB hub
  obligation, a 4.45 A simultaneous downstream fault envelope against a 3 A
  source contract, and an ESD-plus-switch capacitance combination that exceeded
  the hub vendor's channel budget. The review also found prose claiming actual
  VBUS/data interlock behavior when the circuit observed command state only.
  All four were source defects and would have made routing/placement rework
  inevitable if discovered later.
- general rule: before TSX rendering or placement, run inexpensive arithmetic
  over every standards-required effective capacitor bank and every shared path
  fed by independently limited outputs. Fixed converter/load rows must cite an
  exact part dossier; programmed limit rows must cite exact `part_value`
  invariants. Startup proof must dispatch by the selected device's real model
  rather than force unrelated parts through one timer/gate formula. Human
  review must separately challenge whether prose describes a command,
  measurement, fault indication, or physical state.
- landed at: E-FAULT accepts mutually exclusive `programmer_refs` or
  `evidence_refs` per downstream row and resolves the latter to exact part
  dossiers. Its startup subtree now has a closed model dispatch including
  `slew_limited_output_bank`, which independently recomputes maximum slew and
  inrush from dV/dt capacitance, equation coefficient and the full positive-
  corner output bank. Project contracts name every new field explicitly.
- completion evidence: `tests/t1_early_design.py` passes 38/38 including a
  fixed-load evidence row and a known-good slew-limited output-bank case. The
  live project passes E-CAP at 128.664/120 uF and E-FAULT with 2.58 A normal,
  3.0 A service peak, 4.45 A simultaneous fault, 2.990–3.680 A breaker,
  1.608–5.042 ms timing, 0.640 V/ms slew and 0.161 A inrush. Independent
  exact-hash topology and nine-page schematic-render reviews both returned
  SOUND with P0/P1/P2 = 0/0/0, and the board subsequently reached the clean
  placement-review boundary.
- recommendation: make this a mandatory source-stage check for hubs, powered
  distribution, multi-output load switches and any design whose downstream
  current limits can sum above the upstream continuous rating. Keep it
  inapplicable—with an evidenced declaration—for boards that have no such
  shared path; do not burden simple signal-only boards with invented envelopes.

## IMP-115 — executable part authority must be scoped to the live design

- status: proposed; live-project cleanup completed
- observed: USB-controlled debug hub placement entry, 2026-08-16
- evidence: the DMP3007SPS-13 reverse-polarity MOSFET and USBLC6-2SC6 ESD
  array had both been replaced in the live schematic, manifest and netlist.
  Their old `part.yaml` files remained under `02_parts`, so P-ADJ still treated
  their `layout.keep_short`/`layout.adjacency` rows as executable. Placement
  stopped twice with `P-ADJ-UNREACHED`, and each cleanup changed the broad
  parts hash and forced fresh reviews. Deleting both retired dossiers made the
  direct placement-policy audit pass all five rows, including 26/26 keep-short
  and 6/6 adjacency budgets, without changing the normalized netlist.
- general rule: a source directory is not automatically a live population.
  Any dossier that contributes executable pin, placement, sourcing or assembly
  policy must bind to at least one exact live component identity, or carry an
  explicit non-live state whose rules are excluded. Historical/superseded
  dossiers belong in version-control history or a typed archive, not in the
  active policy denominator.
- intended landing point: add an inexpensive pre-TSX `P-DOSSIER-SCOPE` audit
  that joins the manifest/declared parts to `02_parts`. Fail if an active
  dossier with executable policy has no live identity, if a live non-passive
  identity has no dossier, or if two active dossiers claim the same exact
  component role. Print live, shared-passive, retired and orphan denominators.
- safety condition: shared passive dossiers may legitimately serve many refs
  and must bind by exact catalog/value/footprint identity, not by directory
  name. Unknown status or an unresolved identity is a fail; it may not be
  silently treated as historical.
- recommendation: implement before routing this board. It is cheap, would have
  prevented both review-renewal loops, and generalizes to every project that
  replaces a component after initial sourcing.

## IMP-116 — generated annotation and fabrication text must follow footprint side

- status: completed
- observed: USB-controlled debug hub track-free placement DRC, 2026-08-16
- evidence: nine deliberately bottom-mounted USB ESD/data-switch footprints
  were correctly flipped, but `generate_board_generic.py` later forced every
  reference field onto `F.SilkS` without clearing the mirrored state created by
  `Flip()`. KiCad therefore reported nine `mirrored_text_on_front_layer`
  findings. The same generator also wrote every assembly copy on `F.Fab`, even
  for bottom-side parts.
- general rule: side, layer and mirroring are one placement fact. Any generated
  reference, polarity mark, assembly annotation or model-adjacent overlay must
  derive all three from the realized footprint side; changing only the layer
  preserves an invalid coordinate/text transform.
- landed at: the generator now emits top parts on unmirrored F.SilkS/F.Fab and
  bottom parts on mirrored B.SilkS/B.Fab. `tests/t1_generate_board.py` proves
  both sides and the bottom Fab copy in the saved board. The full 52-test
  generator suite passes, and the live placement DRC fell from nine mirrored-
  text findings to zero.
- recommendation: keep the saved-board regression, because source YAML side
  declarations alone cannot prove the serialized text layer/mirror state.

## IMP-117 — compare catalog and board lands in an unflipped footprint frame

- status: completed
- observed: USB-controlled debug hub JLC twin at the placement-review boundary,
  2026-08-16
- evidence: the first catalog twin reported all four bottom-side FSUSB42 data
  switches and all five bottom-side PESD2USB3UX arrays as `MIRRORED`, with
  mirror fits of 0.01/0.22 mm versus non-mirror fits of 2.00/1.90 mm. Every one
  was a correct asymmetric library land deliberately placed on `B.Cu`.
  `jlc_twin.py` zeroed footprint rotation but compared the resulting absolute
  board coordinates directly with JLC's top-side library coordinates; it did
  not undo KiCad's side flip. The detector therefore interpreted ordinary
  bottom-side placement state as mirror-numbered source CAD and would force
  nine false adjudications or block every such design.
- general rule: land-pattern identity is a library-to-library comparison.
  Before testing rotation or mirrored numbering, transform realized pad and
  polarity-mark coordinates back through both board rotation and the
  top/bottom side flip into the footprint's original unflipped local frame.
  Only a mirror that remains after this normalization is a package/library
  defect. Convert model registration, nudges and local/body transforms through
  the same inverse pair so the fitted and rendered frames cannot disagree.
- landed at: `jlc_twin.py` now owns explicit board-to-unflipped-footprint and
  footprint-to-board transforms. Pad fitting and local polarity graphics use
  the normalized frame; model registration and evidence-backed board nudges
  use its inverse. `twin_overlay.py` independently implements the same frame
  contract for expected image geometry instead of declaring every B.Cu body
  ungradeable. The live twin changed from nine false `MIRRORED` blockers and a
  vacuous 0/0 bottom-image gate to exact non-mirrored fits and 9/9 measured
  bottom bodies, while retaining the original top-side mirror-numbering
  detector.
- completion evidence: `tests/t1_jlc_twin.py` includes an asymmetric,
  quarter-turned bottom-side footprint whose identical supplier land must fit
  non-mirrored at offset zero. The existing 2026-07-16 known-bad mirrored
  SOIC-16 fixture remains blocking, so normalizing placement state does not
  weaken detection of a genuinely mirror-numbered library.
  `tests/t1_twin_overlay.py` independently flips an asymmetric connector,
  projects the exact side/rotation envelope through a mirrored bottom camera,
  and requires that body to enter the measured denominator. The live bottom
  A-RENDER passes 9 measured / 9 expected, with zero unmeasured or no-model
  exclusions.
- recommendation: carry immediately for every double-sided assembly. Never
  adjudicate a fleet of identical `MIRRORED` findings merely because every ref
  is on `B.Cu`; first prove the checker is comparing unflipped local frames.

## IMP-118 — separate presentation rendering from shadow-free pixel evidence

- status: implementing; live-project evidence corrected
- observed: USB-controlled debug hub placement-review A-RENDER, 2026-08-16
- evidence: populated and bare 4K renders made with the high-quality preset
  shared the same camera, yet model-cast shadows existed only in the populated
  image. The populated-minus-bare extractor therefore measured each connector
  plus its shadow as one body. Four geometrically identical USB-A receptacles
  all reported the same approximately 1.50 mm outward excursion, and the
  upstream USB-B reported 1.52 mm, despite direct visual and catalog-geometry
  agreement. Re-rendering the exact same board/camera at the shadow-free basic
  preset reduced the clean bodies below the 1.00 mm evidence tolerance and
  passed 30/30 measurable top bodies plus 9/9 bottom bodies.
- general rule: photorealistic presentation and metrology are different
  products. A populated-minus-bare body gate requires illumination effects to
  be invariant between observations; cast shadows, ambient occlusion,
  reflections and antialiasing halos are not component geometry. Generate a
  deterministic, shadow-free orthographic render pair for machine evidence,
  and a separate high-quality render for human review. Never tune a geometry
  tolerance to absorb a renderer's shadow extent.
- landed at: this project's canonical A-RENDER inputs are the 4K `*_gate.png`
  basic-preset populated/bare pairs. The high-quality `*_4k.png` files remain
  presentation-only and are not accepted as the machine measurement source.
- completion evidence: the exact-board top report passes 30 measured / 129
  expected (99 below the declared body resolvability floor, zero resolvable-
  unmeasured, zero no-model); the bottom report passes 9/9. Both calibrate at
  21.03 px/mm with 0.9999 anisotropy and preserve the 1.00 mm evidence
  tolerance. The repeated approximately 1.50 mm high-quality false failures
  disappear without a board, model, placement or tolerance change.
- recommendation: make the render wrapper expose named `evidence` and
  `presentation` profiles and have A-RENDER refuse a render receipt that does
  not declare the shadow-free evidence profile. Keep both outputs when useful,
  but bind review gates only to the evidence pair.

## IMP-119 — resolve part dossiers by declared identity, not raw MPN path spelling

- status: proposed; live pin map independently cleared
- observed: USB-controlled debug hub exact-board pre-route pin review,
  2026-08-16
- evidence: P-PINMAP graded 265 physical identities and an independent reviewer
  found no board pin defect, but the reproducible datasheet-backed `pin_audit`
  could not finish. One exact TPS259474LRPWR dossier has no digest-selected
  local PDF, while exact MPNs such as `MCP2221A-I/ST`, `MCP23017-E/SO` and the
  comma-qualified 74LVC08 identity are represented by path-safe directory names.
  The extractor attempted to use raw identity strings as filesystem paths, so
  `/` created fictitious subdirectories and `,`/variant spelling prevented
  resolution. This defeats IMP-042's exact-local-datasheet gate for correct
  dossiers whose storage name cannot literally equal the manufacturer string.
- general rule: a manufacturer part number is data, not a path. Dossier lookup
  must enumerate `part.yaml` files inside the declared parts root and match a
  normalized, schema-owned identity field. Directory names are opaque storage
  keys and may be path-safe slugs. Once resolved, the selected local PDF must
  still be bound by `datasheet.sha256`; path normalization must never weaken
  exact document authority or fall back to a neighboring family PDF.
- intended landing point: refactor `pin_audit.py` to build a one-to-one index
  from declared manufacturer identity and aliases to dossier path. Fail on
  zero or multiple matches, path traversal tokens and conflicting aliases.
  Add the exact TI TPS259474L PDF and digest to the live dossier, then regenerate
  the pin-audit report before release seal.
- completion evidence required: fixtures resolve slash- and comma-bearing MPNs
  through path-safe dossier directories; ambiguous and missing identities fail;
  a wrong or absent PDF digest still fails exactly as IMP-042 requires. The
  live board's pin audit must complete from repository-local bytes without
  network access.
- recommendation: implement before release sealing, not in the differential-
  routing critical path. The independently reviewed board mapping is SOUND and
  suitable to route, but the release must not claim reproducible pin authority
  until the gap is closed.

## IMP-120 — make route-wave pauses authenticated and non-promotable

- status: completed
- observed: USB-controlled debug hub first USB routing stage, 2026-08-16
- evidence: the first routing checkpoint needed to stop after three USB-only
  waves so their time, geometry and failure modes could be reviewed before
  power/control routing. The router previously offered only a complete chain
  or resume after interruption; a deliberate prefix required editing the
  config digest or killing a healthy process.
- general rule: a stage checkpoint must be an explicit successful state, not a
  simulated failure. It authenticates the exact config, r0 and per-wave chain,
  refuses races, writes no promotable `FINAL` while incomplete, and resumes
  only the untouched suffix.
- landed at: `route_and_stitch_generic.py route --through-wave NAME` records
  the digest-bound `route_progress.json`, prints an explicit pause receipt and
  omits `FINAL`. A later `route --resume` verifies the prefix before continuing.
- completion evidence: the complete `tests/t2_route_stitch.py` suite passes,
  including a fixture proving one-wave pause, non-promotion and suffix-only
  resume. The live board stopped at 3/7 waves with no `FINAL` marker.
- recommendation: use named pauses at critical/RF or high-speed, power and
  control boundaries when useful. Simple boards may run the full chain.

## IMP-121 — grade differential-pair fanout against pair gap, not foreign-net clearance

- status: completed
- observed: USB-controlled debug hub first USB routing stage, 2026-08-16
- evidence: all ten USB pairs used 0.2332 mm tracks, 0.15 mm intra-pair gap and
  0.30 mm clearance to unrelated copper. Their 0.50 mm-centre launch stubs have
  0.2668 mm copper-edge separation. KRT issue-242 preflight compared P/N with
  `config.clearance * 0.95` (0.285 mm), rejected all ten, and emitted identical
  r0/r1/r2/r3 boards. It ignored the declared `diff_pair_gap`.
- general rule: a differential router needs separate same-pair and foreign-net
  clearance domains. Launch validation compares P/N to the pair gap while
  obstacle construction retains full foreign clearance. Collapsing them either
  falsely rejects legal launches or encourages unsafe global relaxation.
- landed at: local KiCadRoutingTools commit `5a1bdc4` compares same-pair launch
  copper against `min(clearance, diff_pair_gap) * 0.95`, retains full clearance
  for foreign obstacles, and makes the CLI fail when any requested pair is
  skipped.  The circuits wrapper independently rejects skipped fanout and
  single-ended differential deferral.
- completion evidence: the focused KRT regression passes a legal 0.2668 mm
  edge gap for a 0.15 mm pair gap, rejects a known-bad pair gap, and retains
  0.30 mm foreign-copper clearance.  The circuits route/stitch suite passes
  121/121 applicable tests (two environment skips).  On the live retry all four
  bottom pairs reported `skipped_bad_fanout=[]`; a later, different endpoint
  topology failure was rejected in 9.031 s with no accepted route wave.
- recommendation: retain distinct same-pair and foreign-net clearance domains
  and the hard no-zero-work/no-single-ended guards.  Do not weaken foreign-net
  clearance to make a differential launch pass.

## IMP-122 — grade realised functional pad-bank direction before routing

- status: completed
- observed: USB-controlled debug hub USB-only routing backtrack, 2026-08-16
- evidence: ordinary adjacency, courtyard, pad-separation, 3D registration and
  human placement review all passed, yet two bottom-side FSUSB42 switches had
  their connector and hub channel banks facing the wrong cells.  After that
  correction, pad-level escape tracing found all four downstream SOT-23 ESD
  arrays still had their common GND land between the receptacle contacts and
  signal lands.  Both placements were close, collision-free and visually
  seated; neither was directionally routable without avoidable detours or a
  pair crossover.  The source-to-realised rotation change introduced by a
  bottom-side flip made visual inspection of authored angles especially
  unreliable.
- general rule: proximity is not direction.  For every mux, filter, shunt
  protector, edge connector or other part with functional pad banks, assert on
  the realised board that the named front bank is closer to its intended
  adjacent target bank than a named rear bank.  Bind the bank pads to their
  expected nets separately.  Run this before route preparation; 3D-body
  seating and body-to-body distance cannot substitute for copper-endpoint
  direction.
- landed at: `generate_board_generic.py` now consumes
  `asserts.pad_bank_faces[]` and compares exact realised pad-bank centroids
  after rotation and side flip.  The board declares connector-facing and
  hub-facing assertions for all four FSUSB42s plus connector-facing assertions
  for all five ESD arrays, and exact pad-net assertions for the four downstream
  ESD pairs.  The symmetric PESD2USB3UX channels are assigned IO1=D- and
  IO2=D+ downstream so the corrected orientation produces a straight,
  no-crossover launch.
- completion evidence: `tests/t1_generate_board.py` passes 53/53, including a
  known-bad fixture proving opposing pad-bank claims block generation.  The
  live generator must report all new orientation assertions before the next
  route-prep subject is reviewed.
- recommendation: add `pad_bank_faces` while the floorplan is authored for any
  multi-bank high-speed or protection part.  Require it for bottom-side signal
  parts and shunt devices by policy once fleet adoption data shows the required
  exceptions; do not infer it from rotation numbers or STEP geometry.

## IMP-123 — preflight differential endpoint topology and tangent compatibility

- status: partially implemented; live failure safely contained
- observed: USB-controlled debug hub USB-only routing retry, 2026-08-16
- evidence: after the same-pair fanout fix accepted all four bottom USB pairs,
  KRT found candidate centre lines but could not attach any coupled path between
  a horizontal PESD2USB3UX endpoint bank and its orthogonal FSUSB42 endpoint
  bank.  Each pair reported an unresolvable polarity mismatch, produced no
  coupled copper and was offered for single-ended deferral.  The wrapper
  rejected the wave after 9.031 s; r0 and r1 remained byte-identical.
- additional evidence: an attempted deterministic "through the ESD" route was
  collision-refused on all four pairs.  Exact pad shapes showed that the SOT23
  ground land is not a series endpoint: it separates the two signal exits and
  invalidates the two-ended coupled-router abstraction.  Recasting pins 1/2 as
  direct-through shunt lands produced 8/8 connected nets, no physical DRC
  finding and 0.305 mm realized skew per pair.
- further evidence: after the connector side was corrected, the independently
  bounded `usb_transition` wave rejected all five remaining pairs in 19.329 s.
  P1_HUB through P4_HUB exposed incompatible endpoint order/approach geometry
  on the opposite FSUSB42 banks, while UP_HUB exposed the same two-ended-router
  mismatch at a three-pad shunt and through-hole connector.  The reviewed
  connector-side path was valid, but the end-to-end path contract was
  incomplete.  The hard wrapper preserved byte-identical r0/r1, zero vias and
  zero authenticated waves.
- general rule: route feasibility depends on endpoint topology as well as open
  field geometry.  Before expensive search, inspect exact P/N ordering at both
  ends, allowed approach tangent, realised pad-bank orientation, multi-terminal
  shunt topology and declared seed direction.  Fail early and identify the end
  that requires a twist, relocation or compatible launch extension.
- configuration-aware extension: the endpoint table must also enumerate legal
  transformations supplied by the component itself, such as a hub's per-port
  polarity-swap strap or an FPGA's swappable pin assignment.  A transformation
  is usable only when its strap/register state and the corresponding physical
  pad-to-logical-net assignment are both explicit, executable invariants.
  Merely renaming or swapping D+/D- nets is not a remedy.
- intended landing point: add a read-only KRT/circuits differential endpoint
  preflight or dry-run report, plus a known-bad orthogonal-bank fixture.  The
  report should walk the complete critical path across both banks of every
  mux/switch and every series or shunt element.  It must expose physical P/N
  order, bank-facing direction, approach tangent and topology kind separately
  from obstacle-search feasibility, and it must detect when correcting one
  side merely transfers the twist to the other.
- board remedy: either author deterministic, source-owned coupled routes for
  the four short connector-to-switch spans with correct shunt topology or use
  a true flow-through protection package whose endpoints match the router's
  model.  Never remedy this by swapping D+/D- net identities, branching to the
  TVS, or accepting single-ended fallback.
- recommendation: implement the preflight before the next complex high-speed
  placement.  For this board, first trace one exact pair and choose the smaller
  source-owned geometry change before rerunning the bounded wave.
- completion evidence extension: USB2517I ports 2--5 now use the documented
  `PRT_SWP` straps with `CFG_SEL=000`; electrical invariants bind R_SWAP2--5
  high, R_SWAP1/6/7 low, and the four physical DM/DP pad assignments.  The
  exact 139-part schematic passed 30/30 pre-generation checks, 66/66 electrical
  invariants, zero ERC errors, and two independent hash-bound reviews.  Its
  canonical resume regenerated the board in under one minute and stopped at
  stale placement receipts before routing.  The reusable endpoint-transform
  report remains proposed; this board-specific instance is implemented.
- crossover evidence: the first upstream deterministic launches passed
  ordinary clearance, continuity and length-spread checks but still presented
  crossed terminal order to the coupled router.  A same-layer fanout cannot
  continuously transform opposite P/N order without an intersection.  The
  accepted source remedy keeps identity fixed, crosses the conductors on
  separate outer layers locally, gives each conductor exactly one B-to-F
  transition (P through the USB-B plated land, N through one signal via), and
  begins the stochastic field route as a straight coupled F.Cu runway.  KRT
  then routed the complete upstream pair with zero polarity swaps.
- intended implementation extension: the endpoint preflight should grade the
  terminal tangent and ordered signed normal of the *actual seed copper*, not
  only pad positions, length and clearance.  When the orders disagree it
  should require an explicit local-crossover architecture before routing and
  report its signal-via count, nearest same-reference GND return, prepared
  mismatch and prepared/realised uncoupled span.  This is conditional for an
  unavoidable order inversion, not a default licence to add layer changes.
- board completion evidence extension: the prepared crossover measures
  0.0010 mm P/N spread and 12.3854 mm uncoupled copper.  Its first complete
  coupled route measured 15.2335 mm including the package/runway terminal
  regions, so the non-spec design guard is calibrated to 15.50 mm rather than
  hiding the extra realised discontinuity.  A dedicated GND return via is now
  source-owned 0.87 mm from the N transition via.  First-article Hi-Speed
  enumeration, sustained traffic and eye testing remain mandatory.
- implementation progress: 2026-08-17 — the placement-routability compositor
  validates declared critical-pair endpoint instances, pad membership and
  dossier topology before placement promotion. Seed-copper tangent/signed-
  normal compatibility remains unimplemented, so this closes the topology
  classification portion but not all of IMP-123.

## IMP-124 — classify high-speed protection parts as shunt or series before placement

- status: implemented
- observed: USB-controlled debug hub deterministic USB-bottom routing,
  2026-08-16
- evidence: PESD2USB3UX is a three-pin shunt, but the placement/routing mental
  model treated its two signal lands like the input side of a series device.
  Ordinary topology, pad-net, directional-bank, body-registration and human
  placement reviews all passed.  The mistake surfaced only when four coupled
  routes collided with the central GND land.  Microchip's USB2517 checklist
  explicitly says never to branch USB signals to protection and to place the
  protection device directly on the differential traces.
- general rule: every high-speed protector, common-mode choke, filter, mux or
  retimer must declare whether it is `shunt`, `series_flow_through`, or
  `series_directional`.  A shunt's protected net is continuous through the
  placement and the protector is a land on that path; a series device divides
  the path into input/output nets.  Placement and route contracts must consume
  that distinction before directional pad-bank review.
- intended landing point: extend part layout metadata and early-design/route
  preflight to require the topology kind for protection parts on critical
  pairs.  Assert that shunts do not create new series nets or signal stubs,
  that their ground/return path is short, and that the realized continuous
  pair can clear every land before human placement review.
- board evidence: `P1_PORT` through `P4_PORT` are now deterministic direct-
  through B.Cu routes.  All eight nets connect connector, shunt land and data
  switch; raw r0 DRC has no physical-rule finding; every end-to-end group
  passes at 0.305 mm spread.  Only `USB_HS_PROTECTED` receives the measured
  7.50 mm SOT23/connector uncoupled ceiling; internal USB remains at 2.0 mm.
- recommendation: implement before the next high-speed protection placement.
  Prefer an actual flow-through package when its capacitance, protection,
  sourcing and assembly constraints are equally suitable; otherwise bind the
  unavoidable shunt-package discontinuity to a dedicated class and first-
  article eye/enumeration test.
- completion: 2026-08-17 — part dossiers now own
  `layout.route_topology.kind`; route instances own exact refs/pads/pairs; the
  generic placement-routability receipt refuses missing required rows,
  dossier/instance disagreement, unknown pads, invalid shunt returns and
  undeclared pairs. The current debug hub declares all five shunts and four
  directional series switches and passes 5/5 composed placement checks.

## IMP-125 — make generated evidence bundles relocatable across atomic promotion

- status: completed
- observed: USB-controlled debug hub placement-render renewal, 2026-08-16
- evidence: the pre-route fabrication exporter correctly staged and atomically
  promoted its output by copying the existing `pre_route` evidence tree through
  a temporary sibling.  Cached EasyEDA `.kicad_mod` files contained absolute
  3D-model paths to that temporary tree.  On the next twin run pad fitting still
  succeeded, but the independent terminal body gate reported 1/139 bodies and
  rejected the run because 138 paths named the vanished
  `pre_route_next.<id>` directory.  Reusing the older render would have hidden
  the defect behind a stale board hash.
- general rule: any generated bundle expected to survive rename, copy, atomic
  promotion or release staging must not persist an ephemeral absolute path.
  Cached third-party artifacts must be rebound to the current cache root when
  loaded, and generated references inside the bundle must be relative to the
  bundle root (for KiCad, `${KIPRJMOD}`) whenever possible.  Terminal coverage
  must run after rebinding and use the same project root the consumer will use.
- landed at: `jlc_twin.py` now rebases EasyEDA model entries by current
  per-code cache structure while preserving scale, offset and rotation; emitted
  twin-board paths use `${KIPRJMOD}/easyeda/...`; and NO-BODY resolves against
  the twin directory rather than the original design-board directory.
- completion evidence: `tests/t1_jlc_twin.py` adds an atomic-promotion fixture
  with a deliberately vanished absolute staging path and proves both rebinding
  and portable emission.  The complete suite passes 37/37.  The exact live
  rerun passes 139/139 mounted bodies, top A-RENDER 30/129 measurable with zero
  resolvable-unmeasured/no-model, and bottom A-RENDER 9/9.
- recommendation: apply the same relocatability audit to other staged evidence
  producers.  A promotion test should move the complete output directory before
  invoking its first independent consumer; string-scan generated manifests for
  the temporary directory name as an additional cheap guard.

## IMP-126 — grade connector mating direction against the board edge

- status: completed
- observed: USB-controlled debug hub USB-A placement review, 2026-08-16
- evidence: all four KH-AF90DIP-112 receptacles passed exact footprint/model
  registration (6/6 attachment centres each), model coverage and A-RENDER, yet
  their mating openings pointed into the board.  Native model and footprint
  were correctly registered to each other; source rotation `0` made the whole
  correctly registered assembly functionally backwards.  A perspective view
  from board centre showed all four mouths while the outside view showed only
  their rear shells.
- general rule: model registration, pad polarity, body presence and functional
  mating direction are independent claims.  Every edge-mounted connector must
  declare the semantic board edge through which it mates.  Its realised body-
  versus-pad displacement must point toward that edge, and its mating plane—not
  merely its contact-row origin or shell pads—must be checked against the board
  outline.  Human evidence should include one view from outside the edge and
  one from the board interior.
- landed at: `generate_board_generic.py` now consumes
  `asserts.edge_faces[] {ref, edge, min_offset_mm?}` for `x0/x1/y0/y1` edges;
  the contracts template documents every field; and
  `tests/t1_generate_board.py` contains a contradictory-edge known-bad fixture.
  The USB-controlled debug hub binds J_PORT1..4 to `y0` and J_UP to `x0`.
- completion evidence: the generator suite passes 56/56 including the new
  known-bad case, and fleet schema governance passes 717/717 declared keys with
  zero orphan fields.  The corrected board/r0 hashes are
  `f5be5f723e712cfb3f74797a39fbf79f78e2c7304433374f1669a2ff93f295c9` /
  `d006e5f09c7eaefdf304a506e275e1f95fe727d2a4e22ea8058d852f0277715a`.
  All four USB-A refs are realised at rotation 180 degrees, the exact native
  registration covers all 24 drilled centres, P-OUT measures 0.21 mm at the
  mating edge, the refreshed A-RENDER overlay binds the corrected board hash
  and passes, and independent exact-board pin/layout review confirms the
  mating direction is global -Y through the north edge.
- recommendation: make `edge_faces` required by project commissioning for
  every connector categorized as edge-mounted.  Later add a separate
  mating-plane-to-outline bound sourced from the part dossier; centroid
  direction reliably catches 180-degree reversal but does not alone prove
  flush depth or enclosure clearance.
- follow-up landed: IMP-128's `P-ORIENT` now consumes this single edge
  authority and adds the manufacturer-derived mating-plane-to-`Edge.Cuts`
  bound, independent model/footprint mouth axes, fixed camera semantics and
  hash-bound human review.  The original generator assertion remains the cheap
  first line; it no longer carries the entire orientation claim.

## IMP-127 — bind package-local rule areas to realised footprints

- status: completed
- observed: USB-controlled debug hub USB-A orientation correction, 2026-08-16
- evidence: moving U_DATA1--4 inward by 9.5 mm left four permissive
  package-launch rectangles at their former absolute board coordinates.  The
  regenerated board then produced 12 misleading field-clearance errors even
  though the package-local neck geometry had moved intact.  Relaxing the
  global 0.30 mm foreign-net clearance would have concealed the ownership
  error and weakened the rest of the board.
- general rule: a rule area that exists because of one realised package must
  be derived from that package, not duplicated as an absolute rectangle in
  the floorplan.  Absolute geometry remains appropriate for board/enclosure
  regions; package-local exceptions should follow ref, side and rotation.
- landed at: `generate_board_generic.py` accepts mutually exclusive
  `ref + margin_mm` package rule-area geometry in addition to explicit
  rectangles/polygons.  The four FSUSB42 launch areas now derive from
  U_DATA1--4 realised pad-copper bounds plus 0.4 mm.  Both contracts document
  the form and clean/known-bad fixtures cover it.
- completion evidence: the generator suite passes 56/56, fleet schema
  governance passes 717/717 with zero orphan fields, canonical pre-route DRC
  returns zero errors, and P-LAND grades all 281 pads with zero failures,
  including 39 package-scoped clearances.
- recommendation: prefer `ref + margin_mm` for package necks, exposed-pad
  escape regions and other footprint-owned exceptions.  Require an explicit
  rationale for absolute rule areas that overlap movable components.

## IMP-128 — authenticate camera semantics in directional render evidence

- status: completed; current USB-board human approval recorded
- observed: USB-controlled debug hub USB-A orientation verification,
  2026-08-16
- evidence: the two perspective images named `from_outside` and
  `from_board_center` showed opposite camera semantics.  The pixels were
  useful, but a reviewer trusting the filenames could invert the connector
  verdict.  The exact board hash was also absent from the image itself, while
  an earlier overlay receipt still named the rejected pre-fix board.
- general rule: directional render evidence needs an authenticated camera
  contract, not an informal filename.  Record source-board hash, viewed edge,
  camera side, target point and expected visible connector face.  For an
  edge-mounted receptacle, the outside view must expose the mating mouth and
  the interior view must expose the rear shell; contradictory metadata or a
  stale board hash must fail review.
- landed at: `connector_orientation_gate.py` closes reusable `P-ORIENT` after
  `P-MODEL-REG` and before route import.  It reuses `floorplan.yaml`
  `asserts.edge_faces[]` as the single intended-edge authority and extends the
  existing exact-SHA `model_registration.yaml` group only with manufacturer-
  derived local mouth/up axes, mounted side, mating-plane depth/range and one
  keyed pad.  Every realised `J*` ref is declared or explicitly exempted.
  The machine gate transforms model, footprint and board frames independently,
  traces the access ray through `Edge.Cuts`, and measures the signed mating-
  plane offset.  It refuses geometry before rendering and preserves the prior
  accepted bundle on a later failure.
- render refactor: five fixed exact-board cameras serve every connector.  Top
  selection uses exact projected footprint geometry; side crops use calibrated
  board-coordinate projection and intentionally draw no body bbox.  No image
  difference, colour threshold or removal of an overhanging model selects the
  connector.  Physical model-body bboxes remain solely `P-MODEL-REG`'s claim.
  Every image burns in `EDGE`, `CAMERA` and semantic `SUBJECT`; repeated exact
  tuples share one human representative while all instances remain in the
  machine and approval denominators.  Progress is visible as `n/5`, and both
  canonical drivers impose a 180-second process deadline.
- live correction: both diagnostic PNGs were regenerated from corrected
  `twin.kicad_pcb`; `from_outside` now uses the north-side camera and visibly
  shows all four mouths, while `from_board_center` shows their rear shells.
  The 4K populated/bare A-RENDER receipts were regenerated and now bind board
  SHA256 `f5be5f...295c9`.
- completion evidence: `tests/t1_connector_orientation.py` passes 4/4,
  including a 180-degree reversed known-bad, proof that machine PASS cannot
  self-approve, exact approval binding, repeated-tuple render compression and
  bounded full/reuse driver order.  Schema governance passes 27/27 with 634
  proven reader rows; progressive-disclosure governance passes 9/9; canonical
  rebuild wiring passes 62/62.  The live USB-controlled debug hub machine run
  passes 5/5 refs and renders the high-resolution five-camera bundle in about
  six seconds, then correctly returns `REVIEW REQUIRED` because no human has
  yet approved subject `55c6d776a55a922e...`.
- recommendation: keep `P-ORIENT` mandatory for future edge-mounted
  connectors.  Add an exemption only for a genuinely different service-access
  class, and close that class with its own mechanical review rather than
  borrowing the mouth-axis claim.
- approval-stability evidence: a renderer-only renewal changed a thin
  board-edge scanline and therefore the PNG bytes while the board, model,
  transforms, camera contract and semantic subject remained unchanged.  The
  gate correctly retained one semantic subject and the user's approval was
  rebound to that unchanged subject, but byte-level image freshness caused
  avoidable adjudication work.
- follow-up recommendation: bind human connector approval to a canonical
  semantic manifest (board/model/transform/camera/edge and keyed-pad facts),
  while retaining PNG hashes as evidence provenance rather than approval
  identity.  Add deterministic raster settings and a known-clean fixture where
  harmless antialiasing/edge-row variation refreshes evidence without staling
  the semantic approval; any camera, transform or geometry change must still
  produce a new subject and require approval.

## IMP-129 — separate geometric render resolution from ray-tracing quality

- status: proposed; bounded board-specific workaround implemented
- observed: USB-controlled debug hub exact pre-route A-RENDER renewal,
  2026-08-16
- evidence: a 4064x2832 KiCad `quality=high` populated render completed in
  23 seconds, while the same-camera bare board remained inside its second
  render for more than five minutes with no useful progress.  The bare board
  has fewer models, so input size did not predict cost.  Terminating that run
  and rendering the same four populated/bare top/bottom images at
  `quality=basic` completed in 7.6 seconds total.  The independent calibrated
  overlays then passed 30/30 measurable top bodies and 9/9 bottom bodies on
  the exact current board.
- general rule: pixel-verification resolution and photorealistic render
  quality are separate requirements.  Same-camera registration needs enough
  pixels and deterministic silhouettes, not expensive ray-traced lighting.
  Use bounded basic-quality orthographic populated/bare pairs for machine
  geometry.  Generate high-quality perspective images only for focused human
  review when they add judgeable information.
- intended landing point: give the render-pair producer one atomic command
  that emits progress per image, applies a per-image deadline, verifies both
  files were refreshed at identical dimensions/camera settings, and preserves
  the prior accepted pair on failure.  Record renderer mode and timing in the
  A-RENDER receipt.  A high-quality timeout may fall back to basic only for a
  gate whose contract explicitly accepts basic silhouettes; it must not
  silently weaken a human-review requirement.
- board workaround: exact 4064x2832 basic-quality populated and bare renders
  were regenerated for both sides under 60-second per-image deadlines.  Top
  and bottom `twin_overlay.py` reports bind board SHA256
  `8904921c...22746` and pass with zero resolvable-but-unmeasured or missing-
  model cases.
- recommendation: implement before making 4K A-RENDER generation a canonical
  stage on additional boards.  Keep connector directional review on its
  separate focused, authenticated camera bundle.

## IMP-130 — grade the signed mounting side independently of XY registration

- status: implemented; exact-board human connector approval still pending
- observed: USB-controlled debug hub J_UP profile review, 2026-08-16
- evidence: J_UP passed the earlier top-view model-registration and directional
  machinery while its connector shell was visibly below the PCB in
  `J_UP_profile_b.png`.  The original coupon selected the correct board
  coordinates but only graded projected XY overlap.  A reversed custom
  footprint body outline, an incorrect y-up 90/270-degree projection in the
  orientation checker, and an unsuitable model transform could therefore
  agree well enough to hide the physically impossible signed-Z result.
- general rule: footprint/pad registration in XY, mounting side in signed Z,
  and connector mating direction are three independent claims.  A top view
  cannot prove front-versus-back mounting.  Quarter-turn transforms must be
  compared with pcbnew's y-down board coordinates; 0/180-degree-only fixtures
  cannot expose the sign error.
- landed at: the J_UP footprint Fab/courtyard body is aligned to the exact JLC
  C86462 geometry; the source uses the SHA-bound JLC STEP and corrected edge
  placement; `connector_orientation_gate.py` uses pcbnew-compatible y-down
  footprint rotation; and `native_model_registration.py` / its wrapper render
  orthogonal coupons and grade the declared front/back solid-pixel fraction
  around the authored PCB strip.  Reports retain the side images and measured
  fractions.
- completion evidence: connector-orientation tests pass 5/5 including explicit
  90/270 coordinate fixtures.  Native model-registration tests pass 8/8,
  including an XY-aligned but vertically inverted known-bad.  The regenerated
  J_UP profile shows the shell above the PCB and leads below it; outside and
  inside cameras respectively show the mating mouth and rear shell.  Current
  machine evidence passes P-MODEL-REG 4/4 and P-ORIENT 5/5; explicit human
  approval remains intentionally absent after the rejected prior subject.
- recommendation: make signed mount-side evidence part of `P-MODEL-REG` for
  every new model, not only connectors.  Keep P-ORIENT focused on access/mating
  direction and require its exact current subject to be shown for user
  approval before routing.  When a body looks wrong, debug one reference across
  footprint local, board, model, and camera frames instead of nudging the real
  footprint to make pixels agree.

## IMP-131 — derive intermediate power floors in their own current domain

- status: implemented; exact schematic re-review pending
- observed: USB-controlled debug hub fresh pre-route topology review,
  2026-08-16
- evidence: E-MARGIN passed four USB outputs by starting each 0.5 A branch at
  an asserted `P5V_PROTECTED >= 4.89 V`.  The admitted 5.10 V input minus the
  fuse dossier's 121 mV allowance and the aggregate eFuse's 45 mOhm maximum at
  the 2.58 A shared load yielded no more than 4.863 V before holder/common
  copper.  The gate therefore proved a downstream inequality from an upstream
  premise it never derived, and also listed the aggregate eFuse again in each
  branch's 0.5 A resistance budget.
- general rule: a path containing shared and per-load elements must be split at
  the current-domain boundary.  Fixed drops and shared resistances are charged
  once at trunk current to derive an intermediate rail floor.  Branch switch,
  copper, via, connector and cable terms are then charged at that branch's
  current.  An intermediate voltage may not be both an author input and the
  conclusion the same gate claims to prove.
- landed at: `power_topology.py` accepts a structured top-level
  `upstream_delivery` proof with named source/destination nets, admitted source
  minimum, shared current, fixed-drop and resistance components, residual
  margin, destination floor, evidence and the complete consumer-rail set.  It
  derives the floor and fails when the declaration or any consumer `vin_min`
  exceeds it.  Clean and circular-floor known-bad fixtures are in
  `tests/t1_power_topology.py`; schema contracts and governance cover the new
  keys.
- board correction: commissioning now requires a regulated 5.20–5.25 V bench
  source.  The gate charges 121 mV fuse drop plus 45+18 mOhm aggregate
  eFuse/holder/common-copper at 2.58 A with 5% residual, deriving 4.902 V and
  conservatively declaring 4.890 V.  Each 0.5 A port then grades only its
  160 mOhm branch path, including 35 mOhm TPS2557, 25 mOhm copper/vias/joints
  and 100 mOhm mated contacts, with the existing 20% branch residual.
- completion evidence: the general E-MARGIN suite passes 59/59, including the
  exact 5.10 V circular-floor incident as a known-bad.  The board reports the
  shared derivation plus 4/4 branch passes; early-design is 5/5 and fleet
  schema governance is 743/743 with zero orphan keys.  The 18 mOhm
  holder/common-copper allocation remains an explicit hot four-wire
  first-article qualification, not an inferred manufacturer guarantee.
- recommendation: require `upstream_delivery` whenever an external output rail
  begins after a fuse, eFuse, ideal diode, reverse-polarity FET or other shared
  series path.  Print the current beside every loss term.  Review and test each
  assumed resistance at its declared temperature/current boundary before
  upgrading a first-article claim to production readiness.

## IMP-132 — make schematic-review hashes phase-semantic

- status: proposed; do not weaken the current fail-closed gate during this run
- observed: USB-controlled debug hub J_UP clearance repair, 2026-08-16
- evidence: moving U_ESD_UP by 0.2 mm, changing only the matching authored
  route endpoint coordinates, and trimming F.Silk made both exact schematic
  reviews stale through `design_rules_sha256`.  The PDF, normalized netlist,
  part dossiers, electrical rules and power proof were byte-identical.  Two
  independent reviewers therefore had to renew electrical/readability receipts
  for a downstream geometric delta that could not change either reviewed fact.
- general rule: a stage review should hash every upstream semantic input that
  can change its verdict, but not downstream implementation coordinates owned
  by a later review.  Over-broad freshness is safe but creates review churn;
  repeated low-value re-approval encourages rubber-stamping and hides the one
  re-review that genuinely matters.
- current mechanism: `pre_route_review_check.py::design_rules_digest` includes
  all rules YAML plus most of `route.yaml` for both schematic and placement
  reviews.  Route endpoint geometry therefore contaminates the schematic
  topology/readability subject even though placement review separately binds
  the exact board and route-prep subject.
- recommendation: split the digest by phase.  The schematic digest should keep
  requirements, electrical/power/protection rules and route-semantic ownership
  such as critical-pair names, layer/via policy and endpoint identities, while
  normalizing away seed coordinates, generated output paths and search knobs.
  The placement digest should retain exact authored geometry.  Add one
  known-bad proving a net/layer/via-policy edit stales schematic review and one
  clean fixture proving a coordinate-only seed nudge stales placement but not
  schematic review.  Land this only after fleet/canary comparison against the
  current conservative behavior.

## IMP-133 — grade deterministic critical-copper length before review and routing

- status: proposed; board-specific check applied manually
- observed: USB-controlled debug hub upstream USB crossover, 2026-08-16
- evidence: a deterministic launch was electrically continuous and physically
  DRC-clean, so it reached independent review and the bounded coupled router.
  Only the later realised-copper audit exposed a large P/N mismatch in an early
  candidate.  Correcting the source fanout first reduced the prepared spread to
  0.0010 mm and made the subsequent endpoint-order diagnosis unambiguous.
- general rule: any authored seed, escape, compensation bank or local
  crossover belonging to a declared length-critical group must be measured as
  soon as route preparation emits it.  Clearance and connectivity are
  orthogonal to propagation-length balance; a candidate that cannot meet its
  own prepared-stage spread should consume neither reviewer time nor router
  search.
- intended landing point: run `R-LEN` immediately after deterministic prep and
  before hash-bound placement receipts.  Grade every fully measurable prepared
  group, print partial coverage separately, and fail when a declared prepared
  group exceeds its stage ceiling.  Preserve the existing final realised-
  copper audit after routing; the early check is a spend/order gate, not a
  substitute for the final functional-link measurement.
- completion evidence required: a known-bad equal-clearance but mismatched seed
  pair must stop before review/router invocation; a corrected pair must report
  its exact spread and permit the next stage; and a route-time change must still
  be caught by the final audit.
- recommendation: implement in the generic prep/review boundary before the
  next high-speed or timing-critical board.  Keep it conditional on declared
  length groups so ordinary low-speed boards do not acquire irrelevant work.

## IMP-134 — replay downstream corridor capacity after deterministic route growth

- status: proposed; board-specific diagnostic applied
- observed: USB-controlled debug hub management-pair correction, 2026-08-16
- evidence: converting the short management USB path into a complete
  deterministic route produced zero DRC errors, zero skew, nominal width and a
  small measured uncoupled span.  Nevertheless, that new prep copper occupied
  the shared hub escape corridor and made the previously repeatable P2 coupled
  route impossible.  The failure appeared only when the earlier four-port
  wave was replayed; reviewing the new pair in isolation gave a false local
  optimum.
- general rule: deterministic copper is an obstacle for every later router.
  Any growth beyond a package-local escape must be checked against the capacity
  and reproducibility of all critical waves sharing its corridor, including
  waves that previously passed.  Local DRC, pair quality and connectivity do
  not prove global routability.
- intended landing point: let critical route contracts declare corridor or
  conflict groups.  After prep geometry changes, run a bounded dry replay of
  every affected earlier wave before renewing human receipts.  Report which
  new copper blocks which endpoint/frontier; do not spend the full remaining
  route chain once a prior authenticated wave becomes infeasible.
- board remedy: own only the management controller's boxed terminal escape,
  ending as a coupled runway in open space, and leave the shared field path to
  the ordered `usb_top` wave after the four port pairs.  Isolated diagnostics
  then routed MGMT in 278 iterations and replayed all four port pairs in their
  established 51,119-iteration pattern.
- recommendation: implement for boards with three or more critical pairs or
  an explicitly shared escape corridor.  For simpler boards, retain the
  ordinary placement-capacity and final route gates without adding a replay.

## IMP-135 — authenticate a reviewed critical route as a reusable wave prefix

- status: implemented and live-board exercised; final-route completion pending
- observed: USB-controlled debug hub critical USB replay, 2026-08-16
- evidence: ten critical pairs had a DRC-clean, length-checked solution, but a
  later full reroute repeatedly destroyed that solution while searching power
  and control copper. Loose `r2` files had no durable provenance, while
  expressing hundreds of successful stochastic segments as authored YAML
  would obscure design intent and invite transcription defects.
- general rule: a costly reviewed route may become a source artifact only at a
  named wave boundary, and only when both it and the exact prepared base are
  hash-bound. Reuse must re-prove base footprint/pad/prep-copper inheritance,
  physical DRC and connected critical contracts before skipping a wave.
- landed at: `route.prefix` in `route_and_stitch_generic.py` accepts exactly
  `board`, `through_wave`, `r0_sha256` and `board_sha256`; materializes current
  rule sidecars; runs P-ROUTEBASE, partial physical DRC and R-CRITESC; records
  provenance in `route_progress.json`; and reauthenticates on resume. Prefixes
  are deliberately incompatible with route races. Hermetic routing coverage is
  124/124, including post-review copper mutation refusal.
- live proof: the USB hub prefix retained 146 footprints, 120 prepared vias and
  200 deterministic segments; had zero hard physical findings; and passed
  10/10 connected critical pairs before the power-input wave began.
- recommendation: use only after an explicit stage review, not as automatic
  recovery from any router output. Keep the final promoted route and final DRC
  gates independent; a prefix is a continuation seam, not a release artifact.

## IMP-136 — classify wide multi-pad power distribution before autorouting

- status: implemented as an opt-in preflight and new-project template default;
  live project ownership migration remains
- observed: USB-controlled debug hub `power_input` wave, 2026-08-16
- evidence: `P5V_PROTECTED` is declared `pour_or_wide_track`, spans 22 pads and
  has five package-local 0.8 mm launch exceptions, but the generic wave asked a
  point-to-point router to connect the whole set as 1.5 mm tracks with power
  tap neckdown forbidden. It spent 28.14 s probing 17 boxed endpoints, left
  17 pads open, and attempted vias directly in U_AGG.5 and U_BUCK.2. The
  via-in-pad guard stopped promotion, but only after avoidable search.
- general rule: a high-current net with many load/decoupling pads is a topology
  decision before it is a search problem. Choose and declare one owner: a
  shaped pour/plane with graded necks and current bottlenecks, or a deliberate
  wide trunk with deterministic package launches and named short taps. A
  generic MST must not infer this from pad count.
- recommendation: add an early route-topology preflight that cross-checks
  multi-pad cardinality, `nets.yaml routing` intent, width-floor exceptions and
  `no_power_tap_neckdown`. Refuse contradictory track-only waves and print the
  missing ownership choice before KRT starts. For this board, design the
  protected 5 V trunk and local launches explicitly, then keep only genuinely
  point-to-point `P5V_RAW`/`P5V_FUSED` work in the stochastic wave.

## IMP-137 — a single-ended KRT JSON failure must fail the wave directly

- status: implemented and regression-tested
- observed: USB-controlled debug hub `power_input` wave, 2026-08-16
- evidence: KRT exited zero and wrote `r3` while its JSON summary reported a
  failed `P5V_FUSED` net and 17 failed `P5V_PROTECTED` pads. The wrapper already
  rejects deferred/failed pairs for the differential engine, but does not apply
  the analogous summary postcondition to the single-ended engine. This run
  failed only because the independent via-in-pad guard also found two defects.
- general rule: process exit and output-file existence prove execution, not
  routing success. Every engine-specific structured summary must be parsed and
  all requested nets/pads must close before width, DRC or progress promotion.
- landed at: `route_and_stitch_generic.py` now consumes every KRT
  `JSON_SUMMARY`, tracks failed single and failed multipoint nets across the
  initial and reconciliation passes, permits a later explicit success to clear
  an earlier failure, and refuses the wave while any requested net remains
  unresolved. `tests/t2_route_stitch.py` proves a zero-exit partial route
  cannot authenticate. Keep later physical/connectivity gates as independent
  defense.

## IMP-138 — measure plated-pad layer transitions as real conductor length

- status: implemented; broader length-policy cleanup pending
- observed: USB-controlled debug hub upstream USB route, 2026-08-16
- evidence: one upstream conductor changed layers through the plated J_UP
  through-hole pad while its mate used an explicit via. The length audit priced
  the via barrel but treated the plated-pad transition as disconnected, giving
  a false skew verdict despite continuous copper.
- general rule: cross-layer connectivity requires a physical barrel owner.
  Same-XY endpoints alone are not proof; an explicit via or a plated through
  pad is. When stackup Z is known, both mechanisms contribute vertical length.
- landed at: `copper_length_audit.py` recognizes plated `*.Cu` THT pads only
  when exact track endpoints occur on two or more copper layers, adds the pad
  barrel edge and reports its count/pricing status. A fixture proves an
  explicit via and plated-pad transition over the same stackup have zero skew.
- recommendation: retain the conservative exact-endpoint rule and never infer
  a layer transition through an SMD or mask-only aperture. Separately clarify
  the octilinear-floor policy for intentional three-pad ESD chains rather than
  weakening realized-length measurement.

## IMP-139 — order route waves by geometric flexibility and physical ownership

- status: implemented for explicitly shared corridors and constrained waves;
  broader automatic corridor inference remains deliberately out of scope
- observed: USB-controlled debug hub oscillator/control routing, 2026-08-16
- evidence: a 71-net catch-all control wave expanded from 71 to more than 177
  queued operations, repeatedly ripped the same hub exits and attempted a via
  in the crystal. Isolating XTAL1/XTAL2 showed the actual defect: the no-via
  oscillator was placed across already-promoted USB copper. After relocating
  the oscillator, giving pins 60/61 deterministic exits and routing it first,
  the result closed 8/8 pads in 1,753 iterations with zero vias and zero hard
  physical DRC findings.
- general rule: wave order is an ownership decision, not merely a net-class
  priority. Nets with no legal layer transition or a uniquely constrained
  local corridor—crystals, RF launches, switch nodes and comparable package
  escapes—must claim that corridor before flexible multi-layer or bulk nets.
  Catch-all `rest` waves should be partitioned by locality/owner so failure is
  bounded and reviewable.
- intended landing point: add a route preflight that classifies each wave's
  layer flexibility, via permission, endpoint density and shared-corridor
  dependencies. Warn or refuse when a less-flexible wave follows a wave that
  consumes its only corridor. Report queue expansion/rip-up amplification and
  stop early when the live operation count materially exceeds the requested
  net set without reducing unresolved endpoints.
- recommendation: implement first for boards declaring crystals, RF nets,
  strict no-via groups or three-or-more shared critical pairs. Preserve the
  ordinary simple order for low-density boards that have no constrained
  corridor; this should be progressive disclosure, not universal ceremony.

## 2026-08-17 eight-hour routing and bring-up retrospective

The 00:20--08:20 PDT review found 717 routing artifacts, including 155 PCB
variants. The first partial hour produced 49 PCB variants, 03:00--04:00
produced another 59, and the post-06:00 I2C investigation produced 93 PCB
candidates/recovery boards and 75 I2C-named artifacts. Counts are evidence of
work, not automatically waste, but repeated candidates with the same frontier
or collision signature show that the pipeline continued searching after the
problem had become one of topology, corridor ownership, or grading authority.

This table is the deduplicated action index. Existing improvements remain the
authority; the new entries below own only the gaps.

| Retrospective action | Owning improvement | Current disposition |
| --- | --- | --- |
| Require connector edge, cable direction, mounting side and mating-plane review before routing | IMP-126, IMP-128, IMP-130 | implemented; keep mandatory |
| Bind connector approval to semantic geometry/camera facts rather than harmless raster-byte variation | IMP-128 follow-up | proposed; P1 |
| Measure deterministic critical copper before review/router spend | IMP-133 | proposed; P1 |
| Replay affected critical corridors after deterministic copper grows | IMP-134 | proposed; P1 after preflight |
| Preserve reviewed expensive routing at an authenticated wave boundary | IMP-135 | implemented; use selectively |
| Classify multi-pad wide power as pour/trunk/star before point-to-point routing | IMP-136 | implemented; existing-board migration opt-in |
| Refuse a zero-exit router result whose structured summary is incomplete | IMP-137 | implemented |
| Route crystal/RF/no-via and uniquely constrained corridors before flexible signals | IMP-139 | implemented for declared shared corridors |
| Stop repeated search when no new routing fact is learned | IMP-140 | implemented; new-project default |
| Grade every candidate with immutable authoritative prepared-board sidecars | IMP-141 | implemented; new-project default |
| Require staged assembly, resistance and current-limited first-power evidence | IMP-142 | checker/template implemented; project card owed |
| Promote/reject/incomplete-label candidates transactionally and prune loose diagnostics | IMP-143 | implemented; pruning remains report-only by design |
| Keep one canonical pause-state authority and prevent STATUS/RESUME drift | IMP-144 | implemented; existing paused projects need migration |
| Ask users only at connector, operational-interface and first-power boundaries | IMP-145 | partial; connector and first-power landed, operational-interface gate open |

### Implemented priority sequence

1. **P0-1 — IMP-141 authoritative candidate workspace.** A false clean verdict
   is more dangerous than a slow route and currently blocks safe I2C promotion.
   This is a small, independently testable boundary with immediate fleet value.
2. **P0-2 — IMP-140 routing stagnation/novelty budget.** This directly caps the
   hours/tokens failure mode while retaining bounded diagnostic value. It can be
   developed independently of the grading workspace.
3. **P0-3 — IMP-136 + IMP-139 routing-ownership preflight.** Implement one
   preflight that classifies multi-pad power topology and wave geometric
   flexibility before KRT starts. Add IMP-134 corridor replay as the next
   increment rather than making the first landing unmanageably broad.

IMP-141 and IMP-140 can be implemented in parallel. The ownership preflight
should live in a separate producer/test surface and integrate with the route
driver only after its schema and verdicts are pinned, minimizing merge overlap.

## IMP-140 — bound routing exploration by stagnation and novelty

- status: implemented and regression-tested; enabled by the new-project route
  template and opt-in for existing boards
- observed: USB-controlled debug hub control/I2C routing, 2026-08-17
- evidence: the reviewed window produced 717 route artifacts and 155 PCB
  variants. Many permutations changed ordering, launch coordinates or search
  parameters while returning the same unresolved endpoints or collision
  cluster. The I2C investigation eventually learned the useful fact—SCL and
  SDA are individually legal but interact at three transition regions—but
  broad candidate generation continued after that problem had become a
  bounded two-net geometry repair.
- general rule: repeated execution is justified only while it can produce a
  new discriminating fact. A router loop must stop when unresolved endpoints,
  hard-finding signatures and owned-corridor frontiers remain unchanged across
  a bounded number of attempts, or when operation/rip-up growth materially
  exceeds the requested work without reducing the unresolved denominator.
- intended landing point: add a per-wave exploration budget and canonical
  signature to `route_and_stitch_generic.py`. The signature should include
  unresolved net/pad identities, normalized hard-finding types/locations and
  frontier ownership—not output hashes or stochastic coordinates. Emit
  `STAGNATED`, `BUDGET_EXHAUSTED` or `NOVEL_PROGRESS`; retain the best candidate
  and print the earliest owning stage to revisit.
- completion evidence required: a repeated-identical-frontier fixture stops
  before its process/time ceiling; a fixture that reduces opens is allowed to
  continue; coordinate-only stochastic variation cannot reset the budget; and
  a newly different hard-finding/owner signature counts as bounded diagnostic
  progress without authorizing promotion.
- recommendation: implement immediately. Default it on for routing waves, with
  a small simple-board budget and an explicit larger advanced-board profile.

## IMP-141 — grade every route candidate in an authoritative immutable workspace

- status: implemented and regression-tested; enabled by the new-project route
  template and opt-in for existing boards
- observed: USB-controlled debug hub I2C prefix promotion, 2026-08-17
- evidence: experimental prefix SHA256 `873001be...3fb8a` appeared clean beside
  router-generated sidecars whose USB-class clearance had been clamped to
  0.15 mm. Replaying the same PCB with the prepared `r0` project and custom-rule
  sidecars found 15 hard USB-class clearance violations. The normal prefix gate
  correctly caught the defect; isolated diagnostic DRC did not. Source was
  restored to accepted prefix `4c001688...257f`.
- general rule: a candidate verdict is a function of PCB bytes plus exact rule
  authority. A router-owned `.kicad_pro`/`.kicad_dru` is output evidence, never
  the authority by which that output may grade itself. No UI or script should
  print `clean`, `PASS` or `promotable` until the candidate has been checked in
  a workspace materialized from immutable prepared-board sidecars.
- intended landing point: create one candidate-workspace helper used by route
  waves, diagnostic scans and manual promotion. It copies/links the candidate
  under a fresh basename, installs exact hash-checked `r0` sidecars, runs
  P-ROUTEBASE, via-in-pad, physical DRC and requested connectivity, then writes
  a receipt with candidate/r0/rules hashes and `ACCEPTED|REJECTED|INCOMPLETE`.
  Consumers accept only that receipt; direct candidate-side DRC is labelled
  diagnostic and non-authoritative.
- completion evidence required: a clamped-sidecar known-bad must look locally
  clean yet be rejected by the helper; sidecar mutation after receipt creation
  invalidates it; accepted work survives relocation; and every promotion path
  is proven to consume the same helper rather than reimplementing sidecar copy.
- recommendation: highest priority. Land before resuming combined I2C
  promotion or trusting any new routing diagnostic.

## IMP-142 — make first-article power-up a staged, measurable contract

- status: implemented as a reusable staged first-article card/checker; existing
  physical projects still need board-specific cards authored before power
- observed: USB Hub 3S v3 first assembled board failure, 2026-08-16/17
- evidence: U5 burned after U2 was installed. U2 orientation was correct, but
  its required exposed ground pad had not been soldered. C17 measured about
  0 ohm before U5 removal and 35 ohm afterward; a replacement board with F1,
  U2 and U11 established about 1.5 kohm as the healthy unpowered reference and
  regulated 5VA to 5.17 V at 10.00--12.11 V input with 14--17 mA no-load draw.
  The initiating cause remains unproven, so the failed board correctly remains
  unpowered.
- general rule: fabrication readiness and first-power readiness are distinct.
  Before power, every exposed-pad device, polarity-critical part and staged-DNP
  assumption needs an assembly confirmation; every principal rail needs an
  expected resistance band, current limit, first probe point and stop condition.
- intended landing point: generate a project-specific first-article card from
  the power tree, assembly rules and footprints. It lists staged population,
  exposed pads, rail-to-ground measurements, initial supply/current limit,
  expected no-load voltages/current, temperature observation, dummy-load steps
  and explicit abort limits. Results append to `01_docs/journal/bringup.md`.
- completion evidence required: a fixture with an unsatisfied exposed pad
  blocks first-power authorization; a populated-stage record cannot silently
  claim an uninstalled part; resistance and voltage readings retain units and
  probe points; and an abnormal measurement produces HOLD, never advice to
  continue powering.
- recommendation: implement before the next physical first article. Keep
  firmware outside this contract unless explicitly requested.

## IMP-143 — make route experiments transactional and retention-bounded

- status: implemented as a content-addressed terminal experiment store with an
  exclusive accepted pointer and report-only pruning
- observed: USB-controlled debug hub routing pause, 2026-08-17
- evidence: 390 files totaling about 103 MB were moved into the project-local
  recovery archive, while loose `_candidate_*`, versioned TSX snapshots and
  checkpoints had to be separated from canonical source immediately before
  publication. The archive preserves useful diagnosis but its population is
  far larger than the accepted/rejected facts required to resume.
- general rule: an experiment has exactly one terminal state:
  `ACCEPTED`, `REJECTED` or `INCOMPLETE`. Canonical source contains accepted
  work only; a content-addressed recovery bundle contains the minimal rejected
  evidence needed to reproduce the diagnosis; disposable intermediates remain
  under the ignored build tree and expire by policy.
- intended landing point: wrap candidate production in a transaction manifest
  recording parent subject, command/config identity, outcome, receipt and
  retained files. Promotion atomically updates the canonical pointer; rejection
  keeps the smallest discriminating PCB/report/log set; pause bundles selected
  incomplete work. Add a dry-run pruning report before deletion.
- completion evidence required: interrupted work cannot overwrite an accepted
  checkpoint; two candidates cannot both become canonical; a recovery bundle
  recreates its terminal verdict without `/tmp`; and pruning never removes a
  manifest-referenced artifact.
- recommendation: implement after IMP-141 so receipts, rather than filenames,
  determine retention.

## IMP-144 — keep one canonical pause-state authority

- status: implemented as one hash-bound pause manifest with generated
  STATUS/RESUME views; existing paused projects require explicit migration
- observed: USB-controlled debug hub pause/publication, 2026-08-17
- evidence: root `RESUME.md` correctly identifies accepted prefix
  `4c001688...257f`, the rejected I2C experiment and exact restart procedure,
  while `01_docs/STATUS.md` still describes an earlier oscillator/USB
  reintegration boundary. Both are plausible prose, so a fresh operator can
  choose the stale one without a machine-detectable failure.
- general rule: a project has one current state record. Journals and historical
  resumes may explain prior states, but every status surface must resolve to
  the same state identity, accepted checkpoint hash, blocker and next command.
- intended landing point: define a small machine-readable pause manifest and
  render human STATUS/RESUME views from it, or make one canonical file and all
  others explicit pointers. Record state only after the referenced checkpoint
  and receipts exist; verify paths/hashes on read and before publication.
- completion evidence required: contradictory status fixtures fail; stale or
  missing checkpoint hashes fail; a clean pause can be resumed in a fresh clone
  without chat or `/tmp`; and publication refuses two competing current-state
  authorities.
- recommendation: implement alongside the next resume/pause refactor; manually
  treat `RESUME.md` as authoritative for the current board until then.

## IMP-145 — schedule user interaction only at high-leverage physical boundaries

- status: partially implemented: connector P-ORIENT, canonical pause state and
  staged first-power evidence exist; operational-interface approval is not yet
  an automatic lifecycle gate
- observed: USB-controlled debug hub connector review and USB Hub 3S v3
  first-power investigation, 2026-08-16/17
- evidence: explicit outside/inside/profile connector approval could decide
  cable access before routing, while router parameter choices did not benefit
  from user adjudication. On hardware, an exposed-pad confirmation, resistance
  baseline and current-limit authorization before first power would have been
  more valuable than tracing many individual pins after damage occurred.
- general rule: ask the user where human intent or physical observation is the
  missing authority, not where automation is merely uncertain. Standard
  checkpoints are: connector/cable access before routing; operational labels,
  bench access and service clearances before release; and assembly/resistance/
  current-limit confirmation before first power. Routing micro-decisions remain
  machine-owned and must stop with a compact diagnosis when blocked.
- intended landing point: add these conditional human gates to the lifecycle
  router. Each request presents bounded exact-subject evidence, one explicit
  decision and the consequence of approval. Semantic subject hashes prevent a
  harmless rerender from asking again; geometry, interface or assembly-state
  changes require renewal.
- completion evidence required: an edge-connector board pauses once before
  routing; an ordinary connector-free board incurs no new ceremony; a physical
  first article cannot inherit a design-review approval as power authorization;
  and a repeated router failure asks no user to choose search parameters.
- recommendation: implement the first-power and operational-interface gates
  after IMP-142; retain the already landed P-ORIENT connector gate.

### 2026-08-17 implementation landing

The public lifecycle remains one `KICAD-ROUTING` stage. Existing boards keep
their prior behavior unless they opt in; the skill-owned new-project
`route.yaml` enables enforcement. The modular landing points are:

| Improvement | Executable authority | Reference / evidence |
| --- | --- | --- |
| IMP-136 + IMP-139 | `route_ownership_preflight.py` | `route-ownership.md`; many-pad owner and constrained-corridor red fixtures |
| IMP-140 | `route_progress_guard.py` plus route-driver hook | `route-exploration.md`; coordinate-only plateau, denominator reduction and amplification fixtures |
| IMP-141 | `route_candidate_workspace.py` plus prefix/wave/race-winner hooks | `route-candidate-contract.md`; prepared-sidecar, relocation and tamper fixtures |
| IMP-142 | `first_article_check.py` and `first_article.yaml` template | `first-article-bringup.md`; exposed-pad, population and abnormal-reading fixtures |
| IMP-143 | `route_experiment_store.py` | `route-exploration.md`; exclusive accepted pointer, relocation and prune fixtures |
| IMP-144 | `pause_state.py` | `operator-checkpoints.md`; stale checkpoint/view and relocation fixtures |
| IMP-145 | lifecycle reference routing to operator/first-power boundaries | connector remains P-ORIENT; operational-interface automatic gate remains open |

Compatibility evidence at landing: skill authority preserved all 109 legacy
policies and one public `KICAD-ROUTING` stage; the USB reuse canary preserved
all 33 stages in order; Pluto v4 full/reuse traces remained distinct and
dependency-complete; 21 existing wave-routing tests passed; gate-contract
coverage was 73/73 with G-INPUT/G-COVER/G-RED satisfied.

## IMP-146 — make copper-layer roles and low-speed escape eligibility executable

- status: partially implemented
- observed: USB-controlled debug hub final control routing, 2026-08-17
- evidence: `HUB_VBUS_SENSE` was repeatedly infeasible or fragile when the
  router was restricted to F.Cu/B.Cu. The successful candidate used one short
  In2.Cu segment and one via, routed in 1,369 iterations / 0.06 seconds at
  0.30 mm clearance while preserving In1.Cu as an uninterrupted ground
  reference. The five-via outer-layer alternative crossed the occupied P4,
  OCS, management, reset and command field. Its proof receipt is
  `projects/usb-controlled-debug-hub-v1/06_build/route/candidate_grades/nearhub-x78y60-complete/receipt.json`.
- general rule: layer eligibility follows electrical role and stackup intent,
  not a blanket outer-layer default. A low-speed control or DC-sense net may
  use a declared internal signal-capable layer when an adjacent continuous
  reference plane remains, while USB/RF/differential and plane-owned nets keep
  their stricter layer contracts. An internal ground pour may clear locally
  around a signal only when another declared reference plane and the
  post-fill plane-continuity gates prove the return structure.
- intended landing point: extend route policy with source-owned layer roles
  such as `signal`, `reference_plane`, `mixed_signal_pour`, and
  `power_plane`, plus per-net-class layer eligibility and required reference
  planes. The routing preflight should report eligible escape layers before
  any rip-up escalation and require fill/return-path rechecks when a mixed
  layer is used.
- completion evidence required: a four-layer fixture with two plane layers
  permits a low-speed net on the declared mixed layer and proves the other
  plane continuous; the same fixture rejects USB/RF use of that layer; a
  two-layer board gains no fictitious escape; and post-fill loss of the
  declared reference path fails promotion.
- recommendation: high value. Integrate with IMP-139 ownership ordering and
  the existing stackup/plane gates before adding more handcrafted route
  repair logic.
- implementation progress: 2026-08-17 — `route.routability.layer_roles` and
  `class_layers` are now schema-checked against the exact board's enabled
  copper stack during placement promotion. Full effective-netclass/custom-rule
  projection into the router and post-fill class-to-reference enforcement are
  still open, so IMP-146 remains partial.

## IMP-147 — route against pairwise authoritative clearances, not one global clearance

- status: proposed
- observed: USB-controlled debug hub final control routing, 2026-08-17
- evidence: a global 0.15 mm search found a connected outer-layer sense route,
  but immutable authoritative DRC found four USB-class clearance defects
  (actual 0.1809--0.2964 mm against 0.30 mm). A global 0.30/0.32 mm search
  could not pass the fine-pitch control escape even though control-to-control
  spacing legally requires only 0.15 mm. The candidate was correctly rejected,
  but the router had no way to express both constraints in one search.
- general rule: route feasibility is governed by the clearance between the
  moving net and each obstacle, including scoped rule areas, not one clearance
  number for the entire wave. A low-speed control net may approach another
  control at its control floor while still maintaining the USB/RF/power rule
  against those classes.
- intended landing point: construct the router obstacle map from the prepared
  board's effective netclass and custom-rule authority. Expose a conservative
  per-pair clearance callback/table to search, including scoped-area overrides,
  and record the smallest effective clearance by obstacle class in the
  structured route summary. The immutable DRC remains authoritative.
- completion evidence required: a fixture with a narrow legal control-control
  neck and a nearby USB pair routes through the neck while holding the larger
  USB clearance; a deliberately incomplete rule projection is `INCOMPLETE`,
  not silently replaced by a global minimum; and the generated route passes
  the exact prepared-sidecar DRC under IMP-141.
- recommendation: high value for dense mixed-signal boards. Until implemented,
  use conservative layer changes or deterministic local geometry rather than
  accepting a globally clamped router sidecar.

## IMP-148 — prove placement and complete routability together before floorplan promotion

- status: partially implemented
- observed: USB-controlled debug hub VBUS-divider relocation, 2026-08-17
- evidence: the original divider at `(83,59)/(83,62)` was physically legal but
  enclosed by the P1/P2 route transitions. Several visually plausible new
  positions collided with accepted copper. A bounded 49-position native-DRC
  scan found exactly one zero-hard near-hub position, `(78,60)/(78,62)`. That
  position was not considered proven until `HUB_VBUS_SENSE`, `USB_UP_VBUS`,
  `HUB_NONREM0`, and the preserved `HUB_OCS1_N` all connected with zero hard
  findings.
- general rule: placement clearance is necessary but not sufficient. Before
  promoting a local floorplan ECO, prove the component's required ingress,
  egress and return/reference paths and restore every net temporarily removed
  to make the probe. Prefer a bounded native-geometry scan over visual guessing
  or unbounded router permutations.
- intended landing point: add a placement-feasibility probe that accepts a
  bounded candidate grid or explicit alternatives, runs exact physical DRC,
  performs declared route probes, restores displaced-net obligations, and
  emits a ranked receipt. It must remain diagnostic until the floorplan and
  source route policy are promoted transactionally.
- completion evidence required: a physically legal but unroutable placement is
  rejected; a placement that routes the target while stranding a displaced
  net is rejected; coordinate-only alternatives are bounded by the exploration
  budget; and the selected placement reproduces after source regeneration.
- recommendation: high value. Run at placement freeze for dense IC support
  networks and again before promoting any post-route footprint move.
- implementation progress: 2026-08-17 — placement promotion now has one
  receipt composing native physical gates, critical inventory, ownership,
  endpoint topology and layer eligibility. It rejects declared infeasibility
  before router spend. The bounded alternative-grid and actual route-probe
  portion of IMP-148 remains open; this is deliberately not described as proof
  of complete global routability.

## IMP-149 — author deterministic geometry with explicit numeric margin above hard floors

- status: proposed
- observed: USB-controlled debug hub sense routing, 2026-08-17
- evidence: a deterministic segment authored at the exact 0.180 mm CONTROL
  width floor serialized/reconstructed as 0.1798 mm and correctly failed the
  authoritative track-width rule. Re-authoring the intended geometry at
  0.19 mm removed that false-boundary dependence. This was not permission to
  weaken the 0.18 mm rule.
- general rule: an authored manufacturing or DRC value should not sit exactly
  on an integer-grid, unit-conversion or serialization boundary. Use a declared
  positive design margin for deterministic widths, clearances, drills and
  edge distances; report both the required floor and authored target.
- intended landing point: add a numeric-margin lint to route-prep and
  deterministic-copper emitters. The lint should understand KiCad's internal
  units and flag values whose serialized result can fall at/below the adopted
  floor. Default targets should come from fabrication policy, not an arbitrary
  universal epsilon.
- completion evidence required: the 0.180-to-0.1798 regression fails before
  board generation; a 0.19 mm control track passes; exact values explicitly
  mandated by a controlled-impedance solver are handled by that solver's own
  tolerance contract rather than blindly inflated.
- recommendation: small and inexpensive; implement alongside deterministic
  route-source cleanup.

## IMP-150 — isolate repeated KiCad board mutations per candidate process

- status: proposed
- observed: USB-controlled debug hub placement scan, 2026-08-17
- evidence: the first in-process placement scanner repeatedly loaded, mutated
  and discarded pcbnew boards. On its second iteration `LoadBoard` returned a
  `SwigPyObject` without `GetFootprints`, accompanied by numerous SWIG ownership
  warnings. Running each candidate mutation in a fresh subprocess completed all
  49 positions deterministically in about 28 seconds.
- general rule: long-lived SWIG object graphs are not a safe orchestration
  boundary for repeated destructive board mutations. Candidate isolation also
  prevents one failed mutation from contaminating the next candidate's board
  state.
- intended landing point: give batch geometry probes a shared subprocess worker
  protocol: one input board, one bounded mutation, one output/result, then
  process exit. Keep orchestration and ranking in the parent process; suppress
  known non-actionable SWIG diagnostics into the artifact log while surfacing
  crashes as `INCOMPLETE`.
- completion evidence required: a multi-candidate fixture completes without
  cross-candidate object reuse; a crashing worker leaves other candidates
  gradeable; inputs remain byte-identical; and worker stderr is retained but
  does not flood normal progress output.
- recommendation: medium priority, particularly for placement scans, model
  registration coupons and route-surgery experiments.

## IMP-151 — require complete displaced-net closure and source rebase before ECO promotion

- status: proposed
- observed: USB-controlled debug hub VBUS-divider relocation, 2026-08-17
- evidence: experimental candidates deliberately removed `USB_UP_VBUS`,
  `HUB_NONREM0`, and sometimes `HUB_OCS1_N` to expose the constrained sense
  route. Several intermediate boards had zero target-net clearance findings but
  were not complete designs. The final physical candidate connected all eight
  declared nets with zero hard findings yet still received `REJECTED`, correctly,
  because its moved footprints and replacement copper were not present in the
  prepared route base.
- general rule: an ECO has three distinct verdicts: local physical feasibility,
  complete electrical closure including displaced nets, and reproducible
  source promotion. None implies the next. A board is promotable only after the
  floorplan/config source regenerates the new prepared base and the reviewed
  copper is rebased and accepted against it.
- intended landing point: extend the route-experiment transaction with an
  explicit displacement set and promotion recipe. Candidate grading reports
  `PHYSICALLY_FEASIBLE`, `ELECTRICALLY_COMPLETE`, and `SOURCE_AUTHENTICATED`
  separately; only the conjunction may update the canonical route pointer.
  Generate the rebase plan from footprint/net deltas rather than ad hoc file
  copying.
- completion evidence required: target-only success cannot promote while a
  displaced net is open; a complete candidate against stale r0 remains
  rejected; regeneration plus semantic rebase produces an accepted receipt;
  and route-base failure text distinguishes expected ECO deltas from accidental
  loss of unrelated reviewed copper.
- recommendation: high value and the immediate next step for this board. Build
  on IMP-040, IMP-101, IMP-141 and IMP-143 instead of adding a parallel
  promotion authority.

### 2026-08-17 final-control routing synthesis

The complete learning record for this stage is also preserved in
`projects/usb-controlled-debug-hub-v1/01_docs/journal/07_routing_topology_reflection_2026-08-17.md`.
The priority order arising from the run is:

1. apply IMP-151 now so the physically proven board becomes reproducible rather
   than merely copying the candidate;
2. add IMP-146 and IMP-148 to the routing/placement preflight so future boards
   discover the legal internal-layer escape and routable placement before
   outer-layer congestion accumulates;
3. implement IMP-147 for dense mixed-rule routing; and
4. land the inexpensive IMP-149 lint and IMP-150 worker isolation as bounded
   tooling hardening.

Related existing items remain active rather than duplicated: IMP-134 covers
downstream corridor replay, IMP-139 owns constrained-wave ordering, IMP-140
caps non-novel search, IMP-141 owns authoritative candidate verdicts, and
IMP-143 owns experiment retention.

## IMP-152 — make generated-copper cleanup ownership-scoped and width-aware

- status: partially implemented on the USB-controlled debug hub; reusable
  contract and regression fixtures pending
- observed: USB-controlled debug hub final stitch replay, 2026-08-17
- evidence: an `all`-scope dangling cleanup removed an authenticated
  `DATA_OE4` route segment and valid protected-power via banks. The via test
  compared centre lines while the electrically valid contact came from the
  annular ring overlapping a wide track. The board regressed from an accepted
  route to 14 DRC violations and 7 unconnected items after a nominal cleanup.
- general rule: a downstream producer may delete only objects it emitted and
  can identify by receipt. Geometric connectivity tests must use copper
  extents (track half-width, via annulus and pad shape), not centre-line
  coincidence. Authenticated route copper is immutable input to stitching.
- landed locally: stitch pruning now uses `scope: emitted`; the redundant
  same-layer seed via was removed at source; the canonical replay returns DRC
  0/0/0 with all critical pairs connected.
- intended landing point: give every generated track/via an ownership receipt
  and require cleanup APIs to name the producer scope. Add a shared
  copper-contact predicate based on actual shapes. Run full connectivity and
  immutable DRC immediately after every destructive cleanup pass.
- completion evidence required: a fixture preserves a route-owned segment and
  a via whose annulus contacts a wide track while deleting a truly isolated
  stitch-owned via; an `all` scope is rejected in release mode; post-cleanup
  0/0/0 and critical-pair checks are mandatory.
- recommendation: P0. This can silently corrupt any densely routed board after
  routing has already passed and should be generalized before the next board.

## IMP-153 — preflight stitching sites against final filled geometry

- status: project workaround landed; general preflight proposed
- observed: USB-controlled debug hub final ground stitching, 2026-08-17
- evidence: two nominal grid sites at `(88,32)` and `(144,32)` landed in
  final-fill voids. They were legal in the early geometric grid but became
  dangling only after zone refill, creating late verification noise and
  tempting broad cleanup.
- general rule: a stitching site is valid only if the plated barrel/annulus
  contacts the intended copper on every required layer after authoritative
  zone fill. Grid regularity is not evidence of electrical attachment.
- landed locally: the two impossible sites are source-declared avoid boxes;
  129/129 ground SMD pads are served and all 86 emitted/retained stitch vias
  survive final verification.
- intended landing point: add a dry-run fill/contact probe before emitting the
  stitch grid, record accepted and rejected sites with reasons, and regenerate
  the same decision deterministically after routing changes.
- completion evidence required: a fixture containing a zone void rejects its
  visually regular grid point before mutation, accepts neighbouring connected
  points, and reports zero dangling stitch-owned copper after final refill.
- recommendation: P1, inexpensive and broadly useful on plane-heavy boards.

## IMP-154 — distinguish byte provenance from semantic 3D-model identity

- status: project hashes corrected; dual-hash model authority proposed
- observed: USB-controlled debug hub model registration, 2026-08-17
- evidence: vendored STEP files and cached JLC STEP sources had different raw
  SHA256 values solely because of line endings and trailing whitespace. After
  canonical text normalization their bytes were identical, yet the raw-hash
  gate initially reported a model-registration failure.
- general rule: release provenance and geometric/model identity are separate
  claims. The release must pin the exact repository bytes, while a model
  equivalence gate may additionally use a documented canonical or geometry
  digest. Neither digest may silently substitute for the other.
- landed locally: the registration rules now pin the exact vendored raw bytes
  and document canonical equality; all four model groups pass.
- intended landing point: model receipts should store `source_sha256`,
  `canonical_step_sha256`, normalization version and, where practical, a
  geometry digest. A raw-byte change invalidates provenance; semantic approval
  is reusable only when the canonical geometry/transform/camera subject is
  unchanged.
- completion evidence required: CRLF/whitespace-only variants share the
  canonical digest but retain different source hashes; a coordinate or solid
  change alters the semantic digest and invalidates approval.
- recommendation: P1. This prevents false regressions without weakening exact
  release provenance.

## IMP-155 — generate the release manifest skeleton before running release gates

- status: partially implemented
- observed: USB-controlled debug hub assembly coverage, 2026-08-17
- evidence: population identity, CPL datum and side counts were correct, but
  the release-local assembly gate failed solely because `MANIFEST.txt` did not
  yet contain the generated `not_assembled: F_IN` line. The manifest was being
  treated as a final seal artifact even though several gates consume its
  declarations earlier.
- general rule: separate a generated release declaration from its final
  cryptographic seal. Create the declaration skeleton at staging start from
  authoritative project rules; append hashes and clean-commit provenance only
  at seal time.
- intended landing point: a `release_stage init` command writes a clearly
  marked DRAFT manifest containing board/version/date, assembly disposition,
  process declarations and pending provenance fields. `release_stage seal`
  refuses pending fields, replaces the draft marker, hashes every payload file
  and proves no undeclared files exist.
- completion evidence required: assembly coverage passes against a generated
  draft; hand-edited population lines fail regeneration; the seal refuses
  dirty inputs, pending fields, missing files and stale hashes.
- recommendation: P1. This removes circular gate ordering and hand-copy risk.
- implementation progress: 2026-08-17 — `release_rehearsal.py init` writes a
  non-overwriting DRAFT manifest from the exact staged board, current commit,
  scoped dirty state and authoritative `not_assembled` refs. Rehearsal and seal
  admission refuse moved bytes. Final replacement of pending fields and a
  regeneration-equality check for hand edits remain open.

## IMP-156 — use multiscale render evidence instead of one whole-board resolution

- status: proposed
- observed: USB-controlled debug hub JLC twin overlay, 2026-08-17
- evidence: the same-camera populated-minus-bare overlays measured all 30
  resolvable top bodies and all 9 bottom bodies within 1 mm, but 99 small
  top-side passives were explicitly below the whole-board two-millimetre
  resolvability floor. Increasing the full-board image indefinitely is an
  inefficient way to inspect 0402/0603 bodies.
- general rule: whole-board renders prove global placement and connector
  context; deterministic local crops prove small-body presence and polarity.
  Both views must bind the same board hash, camera/projection contract and
  populated-minus-bare source.
- intended landing point: after the global overlay, automatically render tiled
  orthographic populated/bare crops only for unresolved refs, then merge their
  measurements into one coverage receipt. Keep symmetric/polarized parts as
  explicit human or pin-1 gates where pixels cannot prove orientation.
- completion evidence required: a mixed 0402/connector fixture achieves full
  resolvable coverage without an enormous whole-board raster; crop and global
  receipts bind the same board hash; a shifted small body fails locally.
- recommendation: P2. Valuable for evidence completeness, but it should not
  delay this release because every currently resolvable body passes and the
  unresolved set is named rather than silently accepted.

## IMP-157 — reject same-net branches, cycles, and duplicate copper before route promotion

- status: implemented
- observed: USB-controlled debug hub Port 4 release audit, 2026-08-17
- evidence: canonical DRC was 0/0/0 and all ten critical pair endpoint checks
  passed, yet strict realized-copper analysis refused `P4_HUB_P`: two launch
  segments existed twice at coordinates differing by only 1 nm. KiCad merged
  them visually and treated the overlapping same-net copper as connected, but
  the conductor graph correctly contained parallel edges, branch vertices and
  a cycle. Removing only the duplicate source pair made all 6/6 USB groups and
  12/12 members measurable; Port 4 then passed at 0.751 mm skew against its
  1.0 mm ceiling while DRC remained 0/0/0.
- general rule: endpoint connectivity and clearance DRC do not prove that a
  transmission line is a simple conductor. Before any critical-route wave is
  promoted, canonicalize geometrically coincident primitives at the board's
  integer-unit resolution and reject unexpected same-net branches, stubs,
  cycles, parallel edges, or disconnected components.
- intended landing point: make `copper_length_audit.py` (or a narrower shared
  topology precheck) part of immutable candidate grading for every declared
  differential/RF/clock group. Emit the exact primitive UUIDs and source owner
  for duplicate edges so repair happens in the producer, not in the final PCB.
- completion evidence required: fixtures covering exact duplicates, 1-nm
  near-duplicates, a legitimate declared tree, a real stub and a loop; only
  the declared topology may promote, and a 0/0/0 DRC cannot override failure.
- recommendation: P0 for high-speed/RF boards and P1 as a general route hygiene
  check. Run it immediately after each promoted critical-copper wave.
- completion: 2026-08-17 — `route_acceptance_gate.py` rejects branch or cycle
  topology on every declared critical net in quick and full promotion modes and
  composes strict declared copper-length grading in full mode. A planted
  branched conductor is a default-suite known-bad; the exact debug-hub board
  passes all 20 critical nets and the full 9/9 acceptance receipt.

## IMP-158 — grade every realized via against the actual stackup aspect-ratio ceiling

- status: implemented
- observed: USB-controlled debug hub topology red team, 2026-08-17
- evidence: 27 realized 0.410/0.150 mm signal vias satisfied the generic JLC
  advanced minimum-drill rule but reached 10.67:1 on the board's nominal
  1.6 mm stackup, beyond the project's adopted 10:1 ceiling. Tier preflight
  checked configured minima and missed the realized board/stackup combination.
  The source repair moved those transitions into the existing 0.460/0.200 mm
  protected family. Final census is 497 protected 0.46/0.20 mm vias and 28
  ordinary 0.70/0.35 mm vias; every drill is at or below 8:1 and DRC remains
  0/0/0.
- general rule: manufacturability belongs to each realized hole, not merely to
  the route configuration's nominal via. Compute board thickness / finished
  drill for every PTH and via after prep, after every promoted wave, after
  stitch, and from the final drill files. The smallest allowed catalog drill
  is not automatically legal at every selected thickness.
- intended landing point: extend tier/route/fab gates with one shared
  stackup-aware aspect-ratio census. It must compare native board vias, route
  vias, thermal/stitch vias and PTH footprints against the selected process,
  report the owning source, and reject an absent or ambiguous thickness.
- completion evidence required: a 0.15 mm drill passes on a qualified thin
  board but fails at 1.6 mm under a 10:1 ceiling; changing only the route common
  via cannot hide an old promoted via; final Excellon drill families reconcile
  exactly with the board census and order notes.
- recommendation: P0. Add this before the next fabrication release and before
  route-review spend on every multilayer board.
- completion: 2026-08-17 — `realized_via_aspect_check.py` inventories every
  saved-board `PCB_VIA`, uses KiCad's exact board thickness and the selected fab
  tier's aspect ceiling, and is mandatory in quick/full route acceptance. The
  1.6/0.15-mm >10:1 regression is pinned; the current debug hub grades 526/526
  vias PASS. Drill-file reconciliation remains a separate fabrication-stage
  census rather than a reason to weaken this route gate.

## IMP-159 — make route replay regenerate or select an immutable segment-free base

- status: proposed
- observed: USB-controlled debug hub route repair replay, 2026-08-17
- evidence: the route backend correctly refused `prep` when the canonical PCB
  still contained the previously imported 2,000+ copper items, and later
  refused a widened-via prefix against a cached old `r0`. The valid recovery
  required three separately remembered steps: regenerate the board from
  `floorplan.yaml`, regenerate rules, then regenerate `r0` before authenticating
  the prefix. Each refusal was safe, but the replay entrypoint did not explain
  or perform the full source lifecycle.
- general rule: the segment-free placed board and the final routed board are
  different lifecycle artifacts even when a legacy flow uses one pathname.
  A replay command must either regenerate the base transactionally or name an
  immutable base artifact explicitly; it must never infer readiness from a
  cached `r0` or ask an operator to hand-clear copper.
- intended landing point: add `route replay` orchestration that snapshots
  hashes, runs board generation and rule generation, creates fresh `r0`,
  authenticates/rebases the promoted prefix, imports, stitches and runs the
  complete final gate battery. Preserve the last good final board until the
  replacement passes, then promote atomically.
- completion evidence required: replay from a routed canonical board succeeds
  without manual file surgery; a stale prefix or stale `r0` fails before
  mutation; a failed replay leaves the previous canonical result recoverable;
  and successful output is reproducible from committed source alone.
- recommendation: P1. It reduces operator error and makes small source repairs
  cheap enough that defects are fixed rather than waived late in release.

## IMP-160 — grade projected reference-plane interruptions on every declared adjacent plane

- status: implemented as an opt-in board-measured gate
- observed: USB-controlled debug hub final electrical review, 2026-08-17
- evidence: exact DRC was 0/0/0, strict USB topology and realized-length gates
  passed, and the existing P-PLANE policy covered In1 only. Independent final
  review nevertheless found `USB_UP_VBUS` and `HUB_VBUS_SENSE` In2 tracks
  crossing directly beneath eight B.Cu USB conductors, cutting their nearest
  reference plane. Source-owned detours removed every crossing; the repaired
  board's nearest projected foreign-track copper edge is 0.4468 mm on
  B.Cu/In2 and 10.7108 mm on F.Cu/In1.
- general rule: a legal conductor on an inner mixed-signal layer can still be
  an SI defect for an outer high-speed route. Every high-speed/RF class must
  declare its signal layer, adjacent reference layer/net, and projected
  foreign-copper margins. Grade all declared adjacent planes, not just a
  globally preferred plane and not merely the presence of a GND zone.
- landed implementation: `reference_plane_check.py` reads opt-in
  `reference_plane_checks` from the project nets YAML, measures final-board
  foreign tracks and through-vias beneath each declared signal corridor, emits
  nearest-margin and exact-violation geometry, and fails below the source-owned
  track/via floors. The USB debug hub declares both B.Cu-over-In2 and
  F.Cu-over-In1 checks; existing boards are unchanged until they opt in.
- scope boundary: this is a projected interruption check, not a field solve or
  proof that filled GND polygons form a globally continuous return path. It
  complements, rather than replaces, impedance solving, zone/plane review,
  discontinuity review, DRC and first-article eye/traffic testing.
- completion evidence: the original crossing geometry is red; the exact
  repaired board passes both planes with named closest obstacles; absent
  declared nets/layers or an empty signal denominator fail configuration.
- recommendation: P0 for USB/RF/high-speed four-layer boards. Run after every
  promoted critical route, after fill/stitch, and again on the exact staged
  source before release sealing.

## IMP-161 — separate catalog stock, PCBA availability and final allocation

- status: implemented
- observed: USB-controlled debug hub sourcing backtrack, 2026-08-18
- evidence: nine exact LCSC codes reported substantial LCSC catalog
  `stockCount` while JLCPCB's assembly interface reported zero availability.
  The legacy freshness path could turn the catalog PASS into `SOURCING: CLEAR`,
  so the discrepancy was found only after a release and replacement pass.
- general rule: catalog identity/stock, JLCPCB PCBA availability, and final
  order allocation are three different facts. Catalog evidence is a cheap
  candidate filter; it can never authorize layout or an order. Preliminary
  `AVAILABLE` evidence prevents layout backtracking, while only exact final-BOM
  `ALLOCATED` evidence authorizes `ORDER`.
- landed implementation: `jlc_pcba_availability.py` emits a quantity-expanded
  request and grades exact resolved code, status, quantity, timestamp and saved
  evidence into a reproducible, hash-bound receipt. The full and reuse drivers
  require the prelayout receipt before placement. `manufacturing_readiness.py`
  composes prelayout/final receipts, and `release_freshness_check.py` has an
  explicit `jlc-pcba` authority whose catalog observations are advisory only.
  Historical releases retain an explicit `catalog-legacy` compatibility mode.
- completion evidence: `t1_pcba_availability.py` covers catalog-high/PCBA-zero,
  quantity shortfall, substitution, stale evidence, AVAILABLE-at-order,
  missing authority, post-grade evidence mutation, forged receipt verdict,
  manual-ref exclusion and self-contained bundle relocation. The focused
  release, assembly, template and progressive-disclosure suites remain green.
- recommendation: keep the operator checkpoint bounded: emit request/template,
  pause once, and resume from saved evidence. Recheck final allocation within
  24 hours of order rather than polling volatile inventory during design.

## IMP-162 — grade MOQ exposure by gross surplus cost and cash outlay before layout

- status: implemented
- observed: USB-controlled debug hub JLC preorder review, 2026-08-18
- evidence: JLC displayed `C25804` with public stock above seven million but a
  preorder MOQ of 1,195. Raw MOQ alone makes a cheap Basic resistor look risky,
  while a much smaller MOQ on an expensive IC can create materially greater
  exposure. The schema-v1 PCBA receipt recorded only exact code, status and
  quantity, so it could not distinguish public-stock use from a preorder or
  grade the money stranded by surplus inventory.
- general rule: distinguish public stock, My Parts, preorder, global sourcing
  and consignment. Grade preorder cash outlay, gross surplus part cost and
  nonrecoverable assembly-minimum excess cost independently. Raw surplus count
  and ratio are diagnostic only. Never credit speculative future reuse, and
  never infer a financial limit for the user.
- landed implementation: `jlc_pcba_availability.py` schema v2 binds one saved
  operator response to an explicit `procurement-policy.yaml`, uses decimal
  currency arithmetic, and emits independent availability/economics verdicts
  plus per-line and aggregate exposure. `manufacturing_readiness.py` composes
  both predicates at selection, prelayout and order phases. The project and
  template policies default every monetary limit to zero; public-stock/My
  Parts rows explicitly marked `NO_MINIMUM_COST` remain unaffected.
  `release_freshness_check.py` treats an aggregate cost rejection as blocked
  sourcing rather than allowing an empty failed-component set to read CLEAR.
  Historical schema-v1 receipts remain reproducible but cannot satisfy the new
  economics predicate.
- completion evidence: `t1_pcba_availability.py` covers stocked Basic parts
  with large irrelevant preorder MOQ, cheap and expensive high-MOQ preorders,
  aggregate cash limits, assembly excess cost, unknown economics, tampering,
  relocation, final sourcing authority and schema-v1 compatibility.
- recommendation: capture the actual cart/quote subtotal at the selected price
  break during critical-part selection and again over the full preliminary BOM
  before placement. Repeat against final order allocation and quote within the
  receipt freshness window.

## IMP-163 — corner-grade reference-design values before schematic freeze

- status: implementing
- observed: USB-controlled debug hub pre-order adversarial review, 2026-08-18
- evidence: the USB2517I hardware checklist's nominal 100 kOhm/100 kOhm
  `VBUS_DET` example was copied faithfully, yet the combined data-sheet limits
  show it can produce only 1.851 V at 4.75 V with 1% resistor corners and the
  specified 10 uA sinking leakage, below `VIH(min)=2.0 V`. The defect survived
  schematic, PCB, routing, DRC and sourcing gates because each checked
  conformance to the selected values rather than whether those values met the
  full electrical envelope.
- general rule: application-note and reference-design values are candidates,
  not proven requirements. Before schematic freeze, every threshold, divider,
  timing network, current limit, regulator setpoint and protection trip point
  must have a named worst-case equation using supply range, component
  tolerance, temperature/aging where relevant, and input/output leakage or
  bias. Both the must-trigger and must-not-trigger corners need positive
  margins.
- intended landing point: extend the pre-layout design-math contract with a
  small declarative `corner_checks` section. Bind each check to source refs,
  nets, exact values, authoritative min/max limits and an ADR. Fail schematic
  freeze when a threshold-class network has no check, a denominator is empty,
  a cited value is nominal-only, or either corner has non-positive margin.
  Re-evaluate automatically whenever a bound value or part identity changes.
- simple regression cases: the original 100 kOhm/100 kOhm USB2517I divider
  must fail the low-VBUS/leakage corner; the corrected 47 kOhm/100 kOhm divider
  must pass both `VIH(min)` and absolute input maximum; a nominally passing
  resistor divider with omitted leakage must fail coverage; changing either
  resistor in the source without updating the check must fail freshness.
- recommendation: P0 for power, reset, enable, UV/OV, current-limit and digital
  threshold networks. Run after part selection but before placement, then bind
  the exact result into final topology review and release evidence.
- implementation progress: `electrical_closure.py` now composes the existing
  design/corner, invariant, topology, margin, off-control, component-census and
  value-identity specialists into one non-vacuous `E-CLOSURE` receipt. Both
  rebuild templates exercise it through atomic shadow evidence. A general
  threshold-network coverage inventory remains open; equations stay with the
  specialist electrical gates, not the compositor.

## IMP-164 — recognize both lit faces of the board strip in directional crops

- status: implemented
- observed: USB-controlled debug hub v2 two-USB-C placement review,
  2026-08-18
- evidence: P-ORIENT geometrically graded all six connector instances PASS,
  but omitted the USB-C inside/rear image with `side render has no measurable
  board strip`. KiCad rendered the continuous reverse-camera board edge near
  RGB 107/111/125; the crop selector required blue below 105 and therefore
  rejected the real board while the outside/front camera passed.
- general rule: deterministic camera metadata does not make pixel calibration
  illumination-invariant. A side-crop selector must recognize the board's
  front and reverse rendered faces, while still deriving the connector window
  from board coordinates rather than target-model pixels.
- landed implementation: `connector_orientation_gate.py` retains the bounded
  three-channel background rejection and density/span checks but admits the
  cool grey-blue reverse face as well as the olive front face. The focused
  regression constructs an exact synthetic reverse-camera strip; the live v2
  rerun now produces top/outside/inside images and reaches `REVIEW REQUIRED`
  with machine 6/6 PASS.
- recommendation: retain this as part of P-ORIENT. Do not weaken the machine
  geometry checks or infer connector bodies from colours; this change affects
  only board-span calibration for the already coordinate-selected side crop.

## IMP-165 — decide duplicate-contact connector polarity order before routing

- status: partially implemented
- observed: USB-controlled debug hub v2 USB-only route checkpoint, 2026-08-18
- evidence: the USB-C receptacle exposes alternating A6/B6 D+ and A7/B7 D-
  contacts. All net identities and local clearances were correct, but the
  connector-side runway and hub fanout presented incompatible physical pair
  order to the coupled router. Two bounded attempts either entered rip-up or
  produced copper that the physical DRC correctly rejected. An explicit
  two-via crossover then connected 10/10 critical pairs with zero hard DRC.
- general rule: for reversible, duplicated or multi-row high-speed connectors,
  schematic connectivity is insufficient route input. Before placement
  approval, derive a small physical lane-order contract at the connector, the
  protection device and the destination. State whether the route is
  order-preserving, uses an allowed logical swap, or requires a physical layer
  crossover. Logical net identity must never be inferred from screen order.
- intended landing point: extend the connector-orientation/critical-pair
  pre-route evidence with ordered terminal tuples and an automatic parity
  comparison between both ends. A mismatch should require a source-owned
  crossover sketch plus via/uncoupled-length budget before KRT runs.
- simple regression cases: aligned single-row D+/D- passes without a
  crossover; TYPE-C A6/B6+A7/B7 merged contacts report a required physical
  crossover; a proposed D+/D- logical swap fails unless an ADR explicitly
  permits it; an authored crossover whose vias violate clearance fails raw r0
  DRC before routing.
- recommendation: P1 for USB-C and other reversible high-speed connectors.
  Run immediately after placement and before the first differential-pair wave.
- implementation progress: `placement_routability_preflight.py` now grades
  ordered connector `{pad, net}` tuples and rejects swapped physical lanes;
  accepted evidence can publish as `P-FEASIBILITY`. Automatic end-to-end
  parity and crossover/via-budget derivation remain open.

## IMP-166 — make switching-loop adjacency a placement contract, not a routing discovery

- status: proposed
- observed: USB-controlled debug hub v2 PD/power route, 2026-08-18
- evidence: the first TPS56637 power-prefix attempt exposed that the bootstrap
  capacitor was not loop-adjacent. Moving it during routing immediately caused
  an anchored courtyard overlap, which the existing placement gate correctly
  rejected; a second pose was required before any valid switching copper could
  be drawn.
- general rule: for every buck/boost/flyback cell, placement must explicitly
  contract the hot-loop capacitor, bootstrap capacitor, switch node/inductor,
  feedback divider and AGND/PGND join before routing begins. Generic nearest-
  component placement is not enough: each relationship needs a measured
  maximum span and a no-intervening-body/courtyard predicate.
- intended landing point: extend the part-dossier adjacency schema with named
  switching-loop roles and grade the complete loop immediately after placement.
  Emit a small pin-to-pin loop sketch and measured spans with the placement
  review, before connector approval or any route wave.
- simple regression cases: a bootstrap capacitor beside the IC body but far
  from the SW/BOOT pins must fail; a closer pose whose courtyard overlaps the
  IC must fail; the exact legal loop-adjacent pose must pass; changing the
  converter identity invalidates the role map and forces re-review.
- recommendation: P1 for every switching regulator. This prevents local-cell
  re-placement from invalidating already-reviewed high-speed or bulk routes.

## IMP-167 — split adjacent power-zone ownership at every series boundary

- status: proposed
- observed: USB-controlled debug hub v2 aggregate-eFuse route, 2026-08-18
- evidence: source zones for P5V_REG and P5V_PROTECTED overlapped around the
  TPS259474L. KiCad's equal-priority fill could not express which side owned
  the shared area, producing competing fill and making visual continuity look
  more authoritative than the actual series path. Splitting the rectangles at
  the package pin gap made the input/output boundary unambiguous.
- general rule: two different rail nets separated by a fuse, eFuse, shunt,
  ideal diode or load switch must never use overlapping equal-priority zones.
  Each side owns a disjoint source region, and the only permitted crossing is
  the exact series component (plus any explicitly reviewed Kelvin sense path).
- intended landing point: add a pre-route `series_boundaries` contract naming
  upstream net, device pins, downstream net and disjoint zone IDs. A geometry
  gate should fail overlap, wrong-side pad coverage, or any alternate copper
  path, then emit a compact current-flow diagram for human review.
- simple regression cases: overlapping VIN/VOUT zones fail; zones separated at
  the exact package gap pass; a same-net bypass track around the series device
  fails; a Kelvin sense trace crossing the boundary passes only when declared
  no-load-current and bound to the correct pin.
- recommendation: P1 for all protected/high-current paths, before filling
  zones or routing control signals through the power cell.

## IMP-168 — replay inherited copper only through exact pad signatures

- status: proposed
- observed: USB-controlled debug hub v2 control-route checkpoint, 2026-08-18
- evidence: 67 unchanged control nets could be replayed from the reviewed v1
  board after the v2 USB-C/power redesign. Comparing net names alone would
  have copied obsolete copper through moved parts; requiring the complete set
  of `(reference, pad, absolute position, layer, net)` signatures excluded
  every changed net and produced zero hard DRC before new local routes.
- general rule: reuse is a provenance operation, not a visual shortcut. A net
  is replayable only when every endpoint pad signature matches the reviewed
  reference, the destination has no existing copper for that net, and the net
  is not in a redesigned-domain deny list. Fresh physical DRC remains required.
- intended landing point: make pad-signature replay a shared, report-producing
  route primitive. Record accepted/rejected nets and reasons, both board
  hashes, replayed item counts and post-replay DRC in the route checkpoint.
- simple regression cases: identical endpoints pass; moving one resistor by
  0.01 mm rejects only its affected net; an added endpoint rejects the net;
  an explicitly redesigned net is rejected despite identical pads; any replay
  that creates a hard DRC finding fails atomically.
- recommendation: P1 for revisions derived from a reviewed board.

## IMP-169 — place low-speed service parts on the reachable side of route barriers

- status: proposed
- observed: USB-controlled debug hub v2 USB-C/control routing, 2026-08-18
- evidence: the inherited port-1 enable pull-down, one USB-C CC resistor and
  the upstream-VBUS divider were electrically correct and collision-free, but
  sat across the newly routed upstream D+/D- corridor from the pins they
  served. Moving them beside their owning pins produced bounded, DRC-clean
  routes without disturbing any USB pair.
- general rule: placement reachability must consider already committed route
  barriers. Pull resistors, divider networks, strap parts and local bypasses
  belong in the same reachable region as their owning pin; distance and
  courtyard legality alone do not prove routability.
- intended landing point: after critical-pair/power corridor planning,
  partition the board into reachable regions and grade each declared local
  service part against its owning pin. A mismatch pauses before copper and
  emits the blocking corridor plus a same-region placement window.
- simple regression cases: a pull resistor 4 mm away across a differential
  pair fails; an 8 mm route in the same open region passes; moving a divider
  changes only its two nets' replay eligibility; an overlapping correction
  still fails placement.
- recommendation: P1 after critical corridor planning and before control routing.

## IMP-170 — bind every intermediate board to its matching KiCad rule sidecar

- status: proposed
- observed: USB-controlled debug hub v2 staged routing, 2026-08-18
- evidence: a newly named `signal_prefix.kicad_pcb` was initially checked
  without same-basename `.kicad_dru/.kicad_pro` files. KiCad silently applied
  default constraints and emitted dozens of misleading USB findings; binding
  the generated sidecars reduced the report to the genuine new-route defects.
- general rule: an intermediate PCB is not independently reviewable unless its
  exact generated project/rule context is present and hash-bound. DRC wrappers
  must refuse rather than silently fall back to defaults.
- intended landing point: centralize intermediate-board creation in a helper
  that installs the authoritative sidecars, records their hashes, runs a
  sentinel rule probe and only then invokes DRC.
- simple regression cases: renamed board without sidecars fails preflight;
  stale sidecar hash fails; matching sidecars pass; a scoped-clearance sentinel
  proves the custom rules loaded.
- recommendation: P0 for trustworthy staged routing evidence; refactor the
  existing DRC wrapper rather than add a lifecycle stage.

## IMP-171 — prove load-current paths as source-to-load graphs before control routing

- status: partially implemented
- observed: USB-controlled debug hub v2 final power/ground stage, 2026-08-18
- evidence: both `VBUS_PD` pads appeared inside same-net filled zones and the
  ordinary ratsnest showed only one net-level island, yet the fuse-output lobe
  and buck-input lobe were separated by the PD-controller/CC field. A cheap
  endpoint graph would have exposed the missing series load path before
  control routing; visual zone membership did not.
- general rule: every protected or converted rail needs an explicit ordered
  current-path graph from source connector through fuse/switch/converter to
  each load. Every graph edge must be realized by a pad, track, filled-zone
  component or connectivity-graded via bank; same-net zone names alone are
  not continuity evidence. Kelvin/sense branches are declared no-load edges.
- intended landing point: extend the pre-control power-topology audit with
  source/load terminal sets and filled-copper connectivity components. Emit a
  small current-flow diagram and fail before control routing if any required
  load edge is absent or crosses an undeclared series boundary.
- simple regression cases: two disjoint same-net zone lobes fail; a full-width
  explicit neck passes; a fuse-bypass track fails; a declared no-load UVLO
  sense branch does not satisfy a load-current edge.
- recommendation: P0 for boards with fuses, eFuses, load switches or DC/DC
  conversion. Run after power fill and before low-speed/control routing.
- implementation progress: placement feasibility now accepts explicit
  `series_power_paths` and proves each copper/component transition against the
  exact placed board, catching wrong ordering and bypass intent before routing.
  Realized post-fill copper-component connectivity remains the completion
  still to land.

## IMP-172 — count only electrically participating vias in ampacity banks

- status: proposed
- observed: USB-controlled debug hub v2 PD input bank, 2026-08-18
- evidence: the first A-VIA rectangle counted eight correctly drilled
  `VBUS_PD` vias, but native DRC showed two touched copper on only one layer.
  Their holes existed geometrically yet they carried no layer-transfer
  current. Replacing the bank with eight fully attached barrels retained the
  4.4 A/10 C rating and removed every dangling-via warning.
- general rule: via-bank ampacity is a connectivity property, not a coordinate
  census. A credited barrel must touch the named upstream copper component on
  one required layer and the named downstream component on the other, have no
  dangling-via finding, and lie in the declared tight boundary.
- intended landing point: refactor `via_ampacity_check.py` so each transfer
  declares source layer/component and destination layer/component. Report
  total holes, participating holes, rejected holes with reasons, and capacity
  from participating holes only.
- simple regression cases: eight attached vias pass; six attached plus two
  one-layer vias credit only six; a same-net via outside the boundary earns no
  credit; a barrel touching the wrong filled island fails participation.
- recommendation: P0 because a geometric false pass can overstate current
  capacity. Refactor the existing A-VIA gate rather than add a lifecycle step.

## IMP-173 — replace broad ground A* fallback with fill-measure-explicit residuals

- status: partially implemented
- observed: USB-controlled debug hub v2 ground closure, 2026-08-18
- evidence: direct pad rescue served 136/154 isolated SMD GND pads in seconds.
  The subsequent 18-target A* fallback consumed more than five minutes at full
  CPU without intermediate output and was stopped. Skipping it, filling zones
  and measuring residuals reduced the real work to 18 named endpoints, then
  one filled-island bbox; explicit dogbones closed the board reproducibly.
- general rule: ground closure should use cheap direct rescue, fill, exact DRC
  residual extraction, and deterministic per-endpoint dogbones. Broad A* is a
  last resort for a small named denominator, with per-target timing/progress
  and a hard aggregate budget—not the default continuation after pad rescue.
- intended landing point: refactor the stitch pass order to checkpoint after
  pad rescue/fill, emit residual refs and island bboxes, and stop for an
  explicit residual contract. If A* is invoked, print each target/result and
  enforce both per-target and total deadlines.
- simple regression cases: directly serviceable pads never invoke A*; an
  18-pad residual emits a report immediately; a boxed endpoint times out by
  itself without blocking other targets; an explicit residual replay is
  byte-reproducible and leaves zero opens.
- recommendation: P0 for workflow latency and debuggability; this directly
  prevents the historical silent multi-minute stitch grind.
- implementation progress: `astar_fallback` now has an explicit residual-count
  admission ceiling, aggregate time budget, per-endpoint progress, and a loud
  explicit-dogbone stop when the denominator is too large. The canonical
  route template defaults to eight endpoints/30 seconds. Reordering fill and
  exact residual extraction ahead of A* remains open.

## IMP-174 — reject missing generated components by population identity, not appearance

- status: proposed
- observed: USB-controlled debug hub v2 PD-input generation, 2026-08-18
- evidence: a custom-footprint component with an unsupported supplier field
  disappeared from generated output while the surrounding circuit still
  looked plausible. Exact TSX-to-board reference-set parity exposed it.
- general rule: every generation stage must compare declared, emitted and
  assembled reference sets before placement or routing; visual completeness is
  not evidence that a generator retained every component.
- intended landing point: make component/ref identity a schema-level preflight
  immediately after TSX/circuit generation and before schematic/PCB generation.
- recommendation: P0; refactor the existing population/parity gate earlier.

## IMP-175 — clone contracts by semantic role, never by stale reference list

- status: proposed
- observed: USB-controlled debug hub v2 assembly and first-article contracts,
  2026-08-18
- evidence: v1-derived contract files initially retained obsolete connector and
  manual-population references despite a materially different v2 power input.
- general rule: a cloned project may inherit policy structure, but every
  reference-bearing assembly, first-article and orientation contract must be
  regenerated from the new design and fail on absent or undeclared references.
- intended landing point: add clone-time contract migration with strict board
  set validation before routing begins.
- recommendation: P0 for derivative designs.

## IMP-176 — run exact land-clearance gates immediately after footprint adjudication

- status: proposed
- observed: USB-controlled debug hub v2 manufacturer-footprint adjudication,
  2026-08-18
- evidence: choosing the manufacturer-authoritative inductor and TVS lands was
  correct, but their larger real pad envelopes invalidated nearby placement
  assumptions that had been made against generic library lands.
- general rule: every footprint-authority change must immediately re-run pad,
  courtyard, escape and local-adjacency clearance before downstream routing.
- intended landing point: attach a bounded placement-delta battery to the
  footprint adjudication gate.
- recommendation: P1; refactor existing placement checks into the adjudication
  transaction.

## IMP-177 — rebase routed candidates onto a clean generated board, not a routed baseline

- status: proposed
- observed: USB-controlled debug hub v2 canonical route promotion, 2026-08-18
- evidence: rebasing onto an already routed `r0` duplicated seed stubs and
  created false cycles; rebasing the accepted copper onto a clean generated
  board, then replaying against the declared baseline, was deterministic.
- general rule: route promotion must name separate clean-generation,
  route-baseline and accepted-candidate subjects. A board containing prior
  routing cannot silently serve as the clean destination.
- intended landing point: extend the promoted-route receipt with all three
  hashes and reject overlapping/duplicate seed identities before import.
- recommendation: P0 for deterministic route promotion.

## IMP-178 — treat split-pad copper as one terminal in physical-distance gates

- status: implemented
- observed: USB-controlled debug hub v2 PD-cell policy audit, 2026-08-18
- evidence: the audit measured a multi-shape exposed pad from the wrong copper
  shape and reported a false adjacency failure. The checker now groups shapes
  by footprint reference and pad number and measures the nearest physical shape.
- general rule: repeated copper primitives sharing one footprint/pad identity
  are one electrical terminal for adjacency and thermal checks.
- implementation: `skills/kicad-pcb/scripts/policy_audit.py` plus the split-pad
  regression in `test_policy_audit_partner_refs.py`.
- recommendation: retain as a regression-protected checker refactor.

## IMP-179 — require an absolute public-stock surplus before footprint freeze

- status: completed
- observed: USB-controlled debug hub 2A v1 pre-layout sourcing, 2026-08-20
- evidence: the first quantity-five public-catalog pass accepted every line
  because the legacy threshold was only `build_quantity * per_board_qty`.
  That classified a crystal with 8 units for 5 required, an ESD array with 66
  for 25 required, and an aggregate eFuse with 122 for 10 required as passing.
  These are technically sufficient for one snapshot but are not reasonable
  selections before footprint freeze: a small concurrent order can force a
  schematic, footprint, placement and routing backtrack.
- general rule: candidate selection must satisfy both quantity coverage and an
  absolute volatility buffer. For the present policy, every machine-assembled
  exact code must have public stock of at least
  `build_quantity * per_board_qty + 200`. The absolute surplus is evaluated
  per LCSC line after reference aggregation; it is not multiplied by board
  quantity and it is not weakened for low-cost parts.
- scope boundary: this is an early negative filter over volatile public
  catalogue stock. It never proves JLC PCBA allocation and does not replace
  the hash-bound pre-layout `AVAILABLE` response, MOQ/surplus-cash grading, or
  the exact order-time `ALLOCATED`/BOM-echo gates. Manual/consigned parts need
  an explicit disposition rather than silently bypassing the denominator.
- intended landing point: refactor the existing `jlc_stock_check.py` candidate
  gate to accept a named absolute-surplus policy alongside its existing
  quantity multiplier. Record required quantity, observed stock, absolute
  surplus, threshold and timestamp in the JSON receipt. Invoke it after the
  preliminary quantity-expanded BOM and before exact footprint promotion.
- substitution transaction: a failing line reopens exact MPN/datasheet,
  package and pin identity, electrical corners, sourcing economics, footprint
  authority and affected schematic invariants together. A same-package or
  similarly named catalogue hit is only a candidate until all of those close.
- simple regression cases: stock 205 for five required passes at `+200`;
  stock 204 fails; stock 225 for 25 required passes; two references collapsed
  into one BOM line use their aggregate required quantity; a public-stock pass
  with no JLC allocation receipt remains pre-layout blocked.
- recommendation: P0 for new boards because it spends seconds before layout
  and prevents high-churn sourcing substitutions after footprint freeze.
- implementation: `jlc_stock_check.py` now accepts the backward-
  compatible `--min-surplus` parameter, includes the absolute limit in its
  JSON receipt, records required quantity, threshold and observed surplus per
  line, and grades `stock >= min_stock * aggregate_line_qty + min_surplus`.
  The pure boundary regression covers 205/204 for five required, 225 for 25
  required, and reference aggregation without network access. The lifecycle
  router places the check inside S-PART-FREEZE while preserving separate MOQ,
  `AVAILABLE`, allocation and uploader authority. The USB-controlled debug
  hub 2A candidate BOM passes 50/50 at `--min-stock 5 --min-surplus 200`; the
  exact USB-A receptacles are outside that denominator only through an
  explicit manual/consigned disposition.

## IMP-180 — reject shadowed schematic-placement authority before TSX generation

- status: proposed
- observed: USB-controlled debug hub 2A v1 power-sheet readability,
  2026-08-20
- evidence: the schematic placement router contained an early exact-name map
  for `U_BUCK_A/B`, `L_BUCK_A/B` and `U_AGG_A/B` before a newer normalized
  bank-family map. The early return silently shadowed the comprehensive rule,
  so repeated attempts to move the aggregate eFuse appeared to have no effect.
  The converter correctly refused a cross-net wire/label merge, but diagnosis
  consumed several full TSX generations because the effective placement owner
  was not visible.
- general rule: one schematic reference must resolve to exactly one effective
  placement rule. Exact-name, regex/family and default rules may coexist only
  with an explicit priority contract; an earlier return that makes a later
  authored rule unreachable is a source error, not a layout preference.
- intended landing point: add a source-only schematic-placement lint before
  TSX generation. Enumerate the manifest reference set, evaluate every layout
  matcher, and fail on zero owners, multiple owners without declared priority,
  or a matcher whose complete reference set is shadowed. Emit an effective
  `ref -> rule id -> sheet/section/x/y` receipt for debugging and review.
- simple regression cases: an exact `U_AGG_A` row plus a matching `U_AGG_*`
  family row fails; two disjoint family rows pass; a documented exact override
  with higher priority passes and appears in the receipt; an unmatched
  reference falls through only to one named default owner.
- recommendation: P1. This is a cheap source-schema extension to the existing
  pre-TSX validation boundary, not a new pipeline phase.

## 2026-08-21 USB-controlled debug hub 2A v1 release-evidence retrospective

The adversarial review of sealed release `v0.1.0-2026-08-21` found no proven
wrong pin, short or architectural topology defect. It did find that the
evidence package made stronger claims than its executed checks supported. The
main process failure was therefore fail-open verification, not a missing PCB
lifecycle stage. The correct integration is to keep `pcb-design/SKILL.md` as
the lifecycle/router and strengthen the owning KiCad, JLC and release tools.

| Pipeline improvement | Durable owner | Disposition |
|---|---|---|
| One canonical USB/high-speed signal contract shared by router and auditors | IMP-181 | new P0 proposal |
| Required checks cannot become accepted `N-A`; report PASS/N-A/FAIL/INCOMPLETE separately | IMP-182 | new P0 proposal |
| Exact end-to-end copper path measurement, including plated transitions and topology | IMP-133, IMP-138, IMP-157 | existing work; IMP-133 remains P0 gap |
| Non-vacuous adjacent-plane declarations, filled-plane evidence and order-time impedance closure | IMP-160, IMP-182 | implemented leaf needs mandatory applicability/completeness |
| Release-local re-execution after BOM, CPL, twin and reviews exist | IMP-063, IMP-183 | partial rehearsal plus new exact-subject gap |
| Scoped DRC suppressions with an occurrence census | IMP-184 | new P1 proposal |
| ERC warning baseline by category and stable object identity | IMP-185 | new P1 proposal |
| Strict part facts over the exact active BOM, with inactive alternatives separated | IMP-115 | existing P1 proposal; use active population as denominator |
| Review scoreboards and prose derived from admitted machine receipts | IMP-186 | new P1 proposal |
| Fresh-context reviews receive an exact artifact packet without inherited verdicts | IMP-026, IMP-049, IMP-095 | existing implementing/proposed work; preserve bounded execution |
| Quantitative current/voltage/thermal headroom typed by first-article versus production maturity | IMP-043, IMP-142 | existing obligation and first-article mechanisms; generic margin policy remains open |
| One atomic staging/rehearsal/seal/publication transaction | IMP-062, IMP-063, IMP-155 | existing implementing/partial work; no new lifecycle stage |
| Known-bad canaries for every promotion boundary | IMP-187 | new P0 implementation discipline |
| Invalidate connector approval after any native/substitute model identity or transform change | IMP-055, IMP-126, IMP-130, IMP-154 | preserve current registration/mating-plane approach and add regression coverage |
| Preserve early PCBA availability, `+200` stock-surplus and MOQ-cost checks | IMP-161, IMP-162, IMP-179 | implemented; retain separate order-time allocation authority |
| Preserve routing heartbeat, stagnation and transactional experiment limits | IMP-013, IMP-140, IMP-143 | implemented; retain as workflow-speed controls |

### Concrete release-review evidence

- `route.yaml` declared `length_match_tolerance: 0.50` mm while the packaged
  copper-length audit searched `nets.yaml`, found no `length_match:` groups and
  measured zero paths. Independent frozen-board measurement found five USB
  P/N segment-length deltas above 0.50 mm. This is not proof of a USB failure;
  it is proof that authority, geometry and the reported verdict disagreed.
- the final route receipt contained six `PASS` and three `N-A` checks, but its
  coverage counted all nine as passing and admitted `ACCEPTED`. The two
  substantive `N-A` checks were critical copper length and reference plane.
- the staged policy audit said no release, BOM, CPL or twin existed even though
  those artifacts were present in the sealed archive. Earlier-phase evidence
  was cited as release evidence without exact-stage reconstruction.
- native DRC was clean only after five global ignores. A geometric census
  found 76 vias with same-net trace endpoints inside the via pad but away from
  its centre. None was a demonstrated open, but the suppression hid real
  occurrences and provided no bounded exception denominator.
- ERC reported zero errors but 1,107 warnings, including unconnected wire
  endpoints and unresolved symbol-library references. A new significant
  warning could disappear inside that undifferentiated total.
- order allocation and rotation remained explicitly incomplete and correctly
  blocked ordering. Those gates are examples to preserve: the problem was not
  that every gate was fail-open.

## IMP-181 — compile one canonical critical-signal contract for routing and verification

- status: proposed
- observed: USB-controlled debug hub 2A v1 release review, 2026-08-21
- evidence: the USB router consumed `length_match_tolerance: 0.50` mm from
  `route.yaml`, while `copper_length_audit.py` looked for a different
  `length_match:` schema in `nets.yaml`. With no matching block it measured
  0/0 paths and returned `N-A`; five independently measured frozen-board pair
  groups nevertheless exceeded 0.50 mm whole-net delta.
- general rule: one electrical intent must have one executable authority. A
  critical-signal group owns its ordered P/N net chains, endpoints, topology,
  signal layers, adjacent reference planes, differential engine, via policy,
  length/skew ceiling and impedance obligation in one normalized contract.
  Router recipes may own coordinate geometry but may not independently restate
  electrical limits.
- intended landing point: add a source-stage compiler that reads the authored
  critical-signal policy and emits one hash-bound `signal_contract.json`.
  Placement feasibility, the router, `copper_length_audit.py`,
  `reference_plane_check.py`, final-route acceptance and release review all
  consume that exact compiled identity. Conflicting duplicate declarations are
  source errors before routing begins.
- simple regression cases: a clean USB pair is consumed by both router and
  auditor with the same 0.50 mm ceiling; a tolerance present only in
  `route.yaml` fails compilation; an auditor reading a stale contract hash is
  inadmissible; a changed layer or ordered net chain invalidates every prior
  realized receipt.
- relationship: this completes the authority seam around IMP-105 and provides
  the non-vacuous source required by IMP-133, IMP-138, IMP-157 and IMP-160. It
  does not create a new lifecycle stage.
- recommendation: P0 before the next high-speed board or respin.

## IMP-182 — make required-check applicability and coverage fail closed

- status: proposed
- observed: USB-controlled debug hub 2A v1 release review, 2026-08-21
- evidence: `route_acceptance_gate.py` counted every `PASS` and `N-A` row in
  one `passing` numerator and allowed an `ACCEPTED` receipt containing three
  `N-A` checks. The resulting 9/9 headline concealed the actual result: six
  PASS, three N/A, zero FAIL. Copper length and reference plane were required
  by the board's declared high-speed role but had zero measured declarations.
- general rule: applicability is derived from the capability profile and the
  current stage, not from whether a checker happened to find configuration.
  `N-A` is legal only for a check proven not required; absent configuration for
  a required check is `INCOMPLETE`. Coverage always reports separate PASS,
  N-A, FAIL and INCOMPLETE denominators and never calls N-A passing.
- intended landing point: give every acceptance compositor an explicit
  `required_checks` set derived from commission/capability facts. Full
  high-speed route acceptance requires critical connectivity, conductor
  topology, copper length, adjacent reference-plane evidence, realized vias,
  ampacity where applicable and native DRC. Verification re-derives the set
  instead of trusting the receipt's verdict.
- simple regression cases: a high-speed board with zero length groups is
  INCOMPLETE; a signal-only board may record power ampacity N-A with a typed
  reason; six PASS plus three N-A prints exactly those counts; forging an
  accepted verdict or shrinking `required_checks` fails receipt verification.
- recommendation: P0 and the smallest high-value first implementation, because
  it prevents missing leaf checks from being laundered by the compositor.

## IMP-183 — reconstruct release evidence against the complete staged archive

- status: proposed
- observed: USB-controlled debug hub 2A v1 release review, 2026-08-21
- evidence: the packaged policy audit reported `M-REL`, `M-BOM`, `A-POP` and
  `A-BODY` as N-A because no release, BOM, CPL or twin existed at the earlier
  time it ran. The sealed archive contained all four artifact families, yet
  the stale audit was retained and cited in final review.
- general rule: evidence about a design-stage subject cannot authorize a
  release-stage claim merely because the board hash is unchanged. A release
  audit must run after the staged archive is complete, read only staged bytes,
  bind every input/config/tool identity and fail if its own applicability
  statements contradict the archive census.
- intended landing point: extend the existing release rehearsal so its last
  pre-seal action reconstructs policy, BOM/CPL/population, model/twin, routing
  and review admission evidence inside mutable staging. Then regenerate the
  manifest from reopened outputs. Seal admission names the complete staged-tree
  digest; adding or changing a review invalidates it.
- simple regression cases: an audit saying `no CPL` beside a staged CPL fails;
  evidence naming a prior release or `06_build` shadow fails; adding a review
  after rehearsal invalidates admission; a relocated complete archive passes
  without consulting mutable project evidence.
- relationship: this is the exact-stage completion seam for IMP-057, IMP-062,
  IMP-063, IMP-090, IMP-094 and IMP-155. Use their readers and transaction
  primitive rather than adding a second release path.
- recommendation: P0 before the next seal.

## IMP-184 — replace global DRC suppressions with scoped, measured exceptions

- status: proposed
- observed: USB-controlled debug hub 2A v1 release review, 2026-08-21
- evidence: native DRC reported 0/0/0 only after globally ignoring five rule
  classes, including track endpoints not centred on vias. Independent geometry
  found 76 affected vias; the worst trace endpoint remained connected by
  copper overlap, and none was on the ten USB pairs, but the release contained
  no occurrence census or bounded justification.
- general rule: a suppressed rule remains an ungraded population. Every
  suppression needs an occurrence census, stable object signature, technical
  justification, scope, owner and expiry/review trigger. Safety- or
  connectivity-relevant classes may not be disabled globally. Where generation
  owns the geometry, repair the producer first—for example, terminate emitted
  tracks at via centres.
- intended landing point: add a pre-DRC suppression audit and a source-owned
  exception registry. Final DRC reports enabled findings and suppressed
  occurrences separately. Any unmatched/new suppressed occurrence fails, and
  release headlines state the enabled and excepted denominators.
- simple regression cases: one signed intentional exception passes; a second
  occurrence fails; moving the object invalidates its signature; a global
  ignore with zero inventory fails; a router-created off-centre endpoint is
  repaired or explicitly rejected before promotion.
- recommendation: P1, promoted to P0 for high-speed, high-current or
  safety-relevant geometry classes.

## IMP-185 — ratchet ERC warnings by category and stable object identity

- status: proposed
- observed: USB-controlled debug hub 2A v1 release review, 2026-08-21
- evidence: ERC had zero errors but 1,107 warnings, dominated by generated
  off-grid endpoints and library issues while also containing unconnected wire
  endpoints. A total-count allowance cannot distinguish a known generator
  artifact from one new electrically meaningful warning.
- general rule: zero errors is necessary but not a complete ERC release claim.
  Baselined warnings are keyed by category and stable object identity with a
  reason. New warnings fail; disappeared warnings ratchet the baseline down;
  high-risk categories such as unconnected endpoints and missing exact symbol
  libraries fail regardless of the historic count.
- intended landing point: generate a versioned ERC baseline only after human
  adjudication, compare fresh clean-environment ERC JSON to it at schematic
  promotion and release staging, and repair library mappings so reproducibility
  does not depend on the author's workstation.
- simple regression cases: an unchanged approved off-grid warning passes; one
  new instance fails; deleting one warning reduces the accepted baseline; an
  unconnected endpoint or missing library fails even when total warnings fall.
- recommendation: P1. Start with blocking categories and identity ratcheting;
  do not require a one-shot cleanup of every generated-grid warning.

## IMP-186 — generate review claims and scoreboards from admitted receipts

- status: proposed
- observed: USB-controlled debug hub 2A v1 release review, 2026-08-21
- evidence: final prose stated route acceptance 9/9 and said copper-length and
  reference-plane contracts passed. The underlying receipt contained six PASS
  and three N-A, while the dedicated artifacts said 0/0 paths and zero plane
  declarations. Hash binding did not prevent the human summary from
  contradicting the evidence.
- general rule: a review may interpret measurements but may not manually
  reconstruct machine status. Counts, applicability and headline verdicts are
  rendered from admitted receipts. A contradiction between prose claims and
  structured evidence is itself a release failure.
- intended landing point: provide a small review-scoreboard composer that
  verifies receipt identities, emits exact PASS/N-A/FAIL/INCOMPLETE tables and
  supplies those blocks to review templates and the manifest. Add a claim lint
  for reserved phrases such as `all pass`, `N/N`, `clean` and `SOUND` when the
  referenced evidence contains non-pass or incomplete required checks.
- simple regression cases: six PASS plus three N-A cannot render `9/9 PASS`;
  prose claiming a plane pass beside zero declarations fails; a defective
  review remains admissible but blocks; changing a receipt invalidates the
  generated scoreboard and review admission.
- relationship: compose IMP-026, IMP-049 and IMP-095 review envelopes rather
  than creating a second review system.
- recommendation: P1 after IMP-182 defines the authoritative status grammar.

## IMP-187 — require known-bad promotion-boundary canaries for every fail-closed gate

- status: proposed
- observed: USB-controlled debug hub 2A v1 release review, 2026-08-21
- evidence: the skill already required nonzero denominators, exact identities
  and stale-evidence rejection, yet real compositors still admitted N-A checks
  as passing and sealed an earlier-stage policy audit. Positive fixtures proved
  that tools could pass clean inputs but did not prove that each promotion
  boundary rejected the defect it was meant to contain.
- general rule: every load-bearing gate needs at least one current clean canary
  and one minimal known-bad canary at the compositor boundary, not only at its
  leaf checker. The bad fixture must exercise status propagation through the
  same command used for promotion and prove the accepted bundle is preserved.
- intended landing point: maintain a small matrix mapping each mandatory
  promotion predicate to a planted defect, expected status and owning test.
  Initial cases are: missing signal contract, required N-A, stale release audit,
  off-centre-via suppressed occurrence, new ERC warning, inactive alternate
  part assertion, changed 3D-model transform and post-rehearsal archive change.
- simple regression cases: each planted defect turns only its expected boundary
  red; removing the defect returns green; a test that bypasses the compositor
  does not count; failure never overwrites the last admitted result.
- recommendation: P0 implementation discipline for IMP-181 through IMP-186 and
  for existing model-registration, sourcing and atomic-promotion gates.

## IMP-188 — treat native post-stitch DRC as an independent mandatory acceptance predicate

- status: proposed
- observed: USB-controlled debug hub 2A v1 route repair, 2026-08-21
- evidence: the deterministic stitcher reported its internal gate clean while
  a native KiCad DRC on the saved board still exposed geometry violations.
- general rule: router completion, connectivity and native CAD DRC answer
  different questions. Promotion requires all of them on the exact saved
  post-stitch board; no internal `clean` status may substitute for CAD DRC.
- intended landing point: keep native `kicad-cli pcb drc --severity-all
  --refill-zones --schematic-parity` as a separately produced, hash-bound
  receipt in atomic route acceptance.
- simple regression cases: an internally connected board with a clearance
  defect fails; a zero-DRC board with an open critical pair fails; changing the
  board after either receipt invalidates acceptance.
- recommendation: P0; compose into IMP-182 and IMP-187.

## IMP-189 — type route-seed and manufacturing-board artifacts and reject role confusion

- status: proposed
- observed: USB-controlled debug hub 2A v1 route repair, 2026-08-21
- evidence: a post-stitch board was temporarily used as the promoted route
  seed. A later prune/stitch pass could then remove source-owned seeds, and only
  the P-ROUTEBASE comparison made the lifecycle error visible.
- general rule: pre-stitch route authority and post-stitch manufacturing output
  are different artifact types even though both use `.kicad_pcb`. Each carries
  an explicit role, producer, input digest and permitted next stages.
- intended landing point: extend artifact provenance and route import to stamp
  `route_seed` versus `manufacturing_board`, refusing imports with the wrong
  role before any destructive prune or stitch action.
- simple regression cases: a route seed imports; a post-stitch board at the
  same path fails; changing only the role stamp fails; a rebuild from the
  admitted seed reproduces the manufacturing topology.
- recommendation: P0 before the next complex routed board.

## IMP-190 — preflight filled-zone islands and inner-plane obstacles before stitching

- status: proposed
- observed: USB-controlled debug hub 2A v1 route repair, 2026-08-21
- evidence: isolated same-net zone fragments and inner-layer foreign copper
  were discovered after expensive route/stitch iterations. The outer-layer
  router did not fully model those projected plane obstacles.
- general rule: before stitching, fill the exact zones and grade same-net island
  connectivity plus projected reference-plane obstacles for every declared
  high-speed corridor. A route candidate that cannot preserve its reference or
  join its intended power island stops early.
- intended landing point: add a cheap pre-stitch `zone_island_preflight` and
  reuse the reference-plane geometry engine in route preparation.
- simple regression cases: an unjoined filled island fails; an island joined by
  a declared via passes; foreign inner-plane copper under a USB corridor fails;
  a distant obstacle passes.
- recommendation: P1; run before the expensive stitch phase.

## IMP-191 — prefer semantic connector approval identities over nondeterministic render bytes

- status: proposed
- observed: USB-controlled debug hub 2A v1 route repair, 2026-08-21
- evidence: repeated KiCad side-view exports changed PNG bytes while connector
  placement, model transform, mouth direction, edge datum and keepout remained
  identical. A byte-bound approval would demand a false new human review.
- general rule: human connector approval binds to a canonical semantic subject
  containing footprint/model identity, transform, board-edge datum, mouth
  direction, body/courtyard bounds and keepout geometry. Images are evidence
  views of that subject, not its identity.
- intended landing point: make schema-2 semantic approval the default; render
  hashes remain recorded for traceability and visual regression but do not
  invalidate unchanged geometry.
- simple regression cases: PNG byte drift with unchanged subject passes;
  swapping a model, moving/rotating a connector, changing its edge, transform
  or keepout changes the subject and requires fresh approval.
- recommendation: P1; compose with the existing connector-orientation gate.
