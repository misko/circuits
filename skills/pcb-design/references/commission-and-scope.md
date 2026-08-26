# Commission and scope procedure

Use this procedure at project intake and whenever a backtrack reaches the
brief, architecture, fabrication tier, or part-selection boundary. Keep
project-specific facts in the project; never copy them from another board.

## Contents

1. Commission the project
2. Lock capabilities and exclusions
3. Lock electrical and mechanical facts
4. Resolve specification tensions
5. Prove sourcing feasibility
6. Choose modules, packages, and precedents
7. Exit criteria

## 1. Commission the project

1. Choose a short kebab-case project slug.
2. Seed the numbered folders and their `contracts.md` files from
   `skills/pcb-design/templates/`. Read the copied contracts before adding
   artifacts. Never seed a project from a sibling board.
3. Keep TSX authoring in `03_tscircuit/`, generator/routing configuration in
   `03_src/`, generated KiCad output in `04_kicad/`, disposable evidence in
   `06_build/`, immutable archives in `07_releases/`, and accepted review
   witnesses in `08_reviews/`.
4. Write `01_docs/BRIEF.md` with the user's prompt verbatim between the prompt
   markers and record its SHA-256. Append parsed requirements `P#`, questions
   `Q#`, answers `A#`, and decisions `D#`. Only a user statement may relax a
   requirement.
5. Ask only questions whose answers change architecture, safety, fabrication,
   assembly, mechanical fit, or verification. Ask two to four at a time. When
   the user is unavailable, select the simplest conservative interpretation
   that satisfies the stated requirement, record a `D#`, and surface it in the
   final report.

Use the template schemas for `floorplan.yaml`, `route.yaml`, and every adopted
rules file. A declared schema key must name the checker that consumes it; a
field with no reader is a defect, not documentation.

## 2. Lock capabilities and exclusions

Record a capability profile before architecture. At minimum resolve:

- delivery target: design, fabricated prototype, sealed release, publication,
  first article, or production;
- signal-integrity class: ordinary, high-speed digital, or RF/microwave;
- assembly provider and whether the target is a populated PCBA;
- power-source and output envelopes;
- foreign mating hardware;
- fabrication cost ceiling;
- firmware posture.

Apply these rules:

- Treat JLCPCB assembly as the default for `/pcb-design` unless the brief names
  another assembly path.
- Start at the cheapest plausible fabrication tier. Raise it only through a
  `D-TIER` decision that states why the cheaper tier fails and carries the
  corresponding order instruction.
- Treat firmware as **forbidden by default**. Do not create, modify, build, or
  release firmware unless the user explicitly requests firmware. An onboard
  programmable device does not imply firmware authorization. When requested,
  record firmware as a separate workstream; PCB design gates may define the
  hardware programming interface but do not silently expand scope.
- Do not load the conditional signal-integrity procedures for an ordinary
  board. Load them for `high_speed_digital` or `rf`, when the deliverable
  depends on impedance, phase, isolation, RF loss, or microwave behavior.
- Do not select an advanced flow merely because it exists. Use it only when
  package escape, stackup, impedance, via, or clearance evidence shows the
  simpler tier cannot meet the locked requirements.

Use `skill_reference_router.py` in shadow/plan mode to turn the capability
profile into typed stages and owning references. The router is a procedure
selector; project drivers and their gates remain execution authority.

## 3. Lock electrical and mechanical facts

Fill the commission fact lock before architecture:

- each output voltage minimum/maximum and continuous/peak current;
- connector and simultaneous-load counts;
- continuous/peak duty assumptions;
- exact measurement plane for every delivered capability;
- included and excluded delivery-path elements;
- input voltage/current envelope;
- protection posture and downstream absolute maxima;
- off-control and stored quiescent draw for self-powered boards;
- load brownout threshold and end-to-end resistance budget when relevant;
- hard-cell or constrained sourcing class.

Each row must be user-confirmed or linked to a `D#`. Emit machine-readable
electrical facts into the appropriate rules files rather than leaving them only
in prose.

### Foreign mating facts (`D-MATE` / `M-IMPORT`)

If the board plugs into, bolts to, or aligns with hardware this repository did
not design:

1. Put each external fact once under `spf/<device>/facts.yaml`, with a human
   method record in `spf/<device>/README.md`.
2. Grade each fact `MEASURED`, `CITED`, `ESTIMATED`, or `OWED`.
3. Give every estimated dimension an error bar. Do not spend an owed fact.
4. Reference fact IDs from `03_src/rules/mates.yaml`; never restate values in
   the board project.
5. Measure the feature that establishes the required location, not a nearby
   proxy. Machine-readable design files and direct measurements outrank an
   undimensioned render.
6. Run the import-provenance gate before a foreign fact becomes placement or
   copper.

If the board mates to nothing foreign, state that explicitly and omit an empty
`mates.yaml`.

## 4. Resolve specification tensions

Run `D-SPEC` before architecture:

1. Compare every numeric requirement with its governing standard.
2. Compare it with the envelope of sourceable, compliant parts.
3. Record each disagreement in a spec-tension ADR and the BRIEF.
4. Ask the user when a different interpretation materially changes topology.
5. Never silently build an out-of-spec interpretation or silently lower the
   requirement.

For every regulated rail, derive buck, boost, or buck-boost topology from the
locked input/output envelopes. Over-capable topology fails as unnecessary
complexity unless an ADR justifies it. For known loads, bind setpoint margin to
the complete board/connector/cable resistance boundary. For self-powered
boards, prove how storage/shipping de-energizes the rail and estimate drain
time.

Protection analysis must compare the worst protected-rail waveform—not nominal
input—with every directly exposed component's recommended and absolute maximum.
Gate-drive analysis must use maximum or qualified-maximum gate charge, all
simultaneously driven FETs, minimum drive capability, switching frequency, and
thermal assumptions. Threshold and feedback math must include component and IC
corners, leakage, and temperature.

## 5. Prove sourcing feasibility

Perform a time-bounded sourcing spike during commission for every
specification-critical function:

1. Consult the proven-parts ledger.
2. If it has no fit, search the JLC/LCSC part universe and authorized supplier
   pools.
3. Classify the result: sourceable at the cost ceiling; sourceable only at a
   higher tier; or not sourceable as specified.
4. Resolve tier or specification tension before detailed engineering.

Treat LCSC catalog identity and `stockCount` as discovery evidence only.
Before freezing a critical or footprint-driving part, confirm its exact code
in JLCPCB's PCBA interface for the intended quantity. Once the preliminary BOM
is complete, run the full quantity-expanded JLC PCBA probe before placement.
Record a qualified alternate or a deliberate consign/manual disposition where
an unavailable line would otherwise force schematic or footprint backtracking.

At part selection, create `02_parts/<MPN>/part.yaml` with:

- exact MPN, manufacturer, LCSC code, and approved alternates;
- physical pin map from the datasheet figure with page/figure citation;
- pinned datasheet hash and package/land-pattern evidence;
- escape feasibility and required fab tier;
- layout/application guidance and partner-ref adjacency budgets;
- editable/open reference-layout precedents considered;
- asserted polarity, BOM value, MSL, or other part-owned facts.

Run the composed two-source gate (`Q-2SOURCE`) against a candidate BOM before
schematic completion. Count independent authorized supplier pools, not multiple
listings from one distributor. Require enough active stock for five board sets
at two pools and repeat on order day because stock is volatile.

Stock values and prices belong in TTL'd `06_build/cache/` evidence, not the
durable dossier. Removing or changing a dossier identity requires a sealed
dependency audit because immutable releases may still resolve through it.

## 6. Choose modules, packages, and precedents

Apply `D-MOD`: compare a proven module with a bare complex IC for programmable
compute/control, radio, interface, switching power, and precision sensing.
Optimize total engineering effort—support BOM, routing, bring-up,
verification, sourcing, and assembly—not unit cost or area alone. A bare IC
with a large support set requires an evidenced module comparison and ADR.

Apply `D-ESC` at part selection. Compute whether the chosen package can escape
at the declared tier. Fine-pitch impossibility is a package/tier decision, not
a router problem. For dense leaded packages, count escapes per side and reserve
legal staggered via corridors.

Apply `D-LAYOUT` and `D-ADJ` before placement:

- read the datasheet layout section and reference design;
- prefer editable reference-design files over raster pictures;
- record authority tier, artifact, whether it was reached, and why a stronger
  source was not used;
- compare the precedent's surrounding free space with this board's corridor;
- extract decisions into dossiers and floorplan config; never import precedent
  copper;
- keep bootstrap, feedback, decoupling, sense, pass-device, and hot-loop parts
  against the pins they serve.

Read the KiCad placement, routing, and RF references directly from the core
router for the selected capabilities. Those references own the geometry and
gate mechanics.

## 7. Exit criteria

Do not leave commission/architecture/sourcing until:

- the verbatim brief and fact locks are complete;
- capability profile and firmware posture are explicit;
- all specification tensions have a user answer or recorded decision;
- foreign mating facts are proven or the board declares none;
- the fabrication cost ceiling is declared;
- spec-critical functions have a sourcing classification;
- selected parts have exact dossiers, escape evidence, and required layout
  precedents;
- module-versus-bare-IC decisions are recorded;
- source-phase rules/schema and module-first gates pass;
- stage journal and live status beacon identify the next stage.

The bootstrap `COMMISSIONING-HOLD.md` starts at `PCB-COMMISSION` but spans this
combined admission boundary. Remove it only in the reviewed change that binds
the separately typed commission, architecture, and sourcing evidence. Manual
deletion is not an admission receipt; IMP-235 tracks the missing executable
compositor. Commit the green checkpoint before advancing. A later failure
reopens this stage only through the bounded backtrack protocol.
