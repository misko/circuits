---
schema: 1
kind: pcb-human-report
report_id: 2026-08-27-closed-loop-permutation-pcb-findings
title: Closed-loop calibration findings for the fabricated Pluto eight-way PCB
subtitle: What the conducted permutation experiment establishes, what it does not, and how v6 should respond
project: pluto-rx2-8way-v5
date: 2026-08-27
status: REVIEWED
evidence_status: INCOMPLETE
---

## Executive conclusion

The conducted closed-loop permutation experiment is strong evidence that the
fabricated v5 selector has stable, separable board paths across 2.400–2.480 GHz.
Five frequencies passed the experiment's board-calibration gates with only
0.033–0.064 dB RMS amplitude residual and 0.411–0.538 degrees RMS phase
residual. Returning the fixture to its original mapping changed the relative
eight-path shape by only 0.026–0.038 dB RMS and 0.498–0.575 degrees RMS.
**CITED:** this does not look like an intermittent switch, incorrect state map,
or gross assembly fault.

The experiment does expose two design concerns:

1. **CITED:** the unequal PCB routes produce large but highly deterministic
   relative phase terms. At 2.400 GHz the route-length pairs ANT1/ANT8,
   ANT2/ANT7, ANT3/ANT6 and ANT4/ANT5 also form matching phase-correction
   pairs. This is calibratable, but an uncalibrated direction-finding system
   cannot treat the eight ports as phase-equivalent.
2. **CITED:** near 2.480 GHz the middle six board paths require approximately
   6.2–7.7 dB gain correction while the short ANT1/ANT8 pair remains within
   0.05 dB of the reference. Software can normalize amplitude but cannot
   recover the lost per-path SNR. The frequency-localized loss needs a
   board-only VNA sweep before a v6 layout is frozen.

The present Pluto-plus-selector assembly is **not qualified at 5.8 GHz**.
Its worst raw selected-to-ALL_OFF contrast is -8.76 dB, so the additive leakage
term can exceed the selected signal. After ALL_OFF subtraction the three-
permutation model is still repeatable and separable at 0.158 dB and 0.812
degrees RMS. **INFERRED:** that combination points to a stable desired path
hidden under a dominant common/bypass leakage term. It does not identify
whether that term originates in the Pluto, RX2 cable/common launch, selector
PCB, switch IC, fixture, or coupling between them.

There is therefore no evidence-based reason to respin the PCB immediately.
First measure the board by itself. If the 2.480 GHz loss or 5.8 GHz leakage
remains at the board SMA planes, v6 should shorten and geometrically equalize
the RF branches, add a bonded shield-can boundary, and compare the existing
absorptive switch against a controlled higher-isolation coupon. If the board
passes alone, the corrective work belongs at the Pluto/cable/enclosure system
boundary instead.

## Question and scope

This report asks what the Smateway closed-loop experiment teaches about the
fabricated Pluto RX2 eight-way v5 PCB, whether it reveals a PCB design defect,
and which next measurements or design changes are justified.

The PCB subject is immutable release
[`v0.2.1-2026-08-14`](../../07_releases/v0.2.1-2026-08-14/MANIFEST.txt).
The external evidence subject is Smateway commit
[`c0d8751654c5b869724a6b3666141de68a92789e`](https://github.com/misko/smateway/tree/c0d8751654c5b869724a6b3666141de68a92789e/docs/closed_loop_permutation_calibration).
The captured signal chain includes Pluto TX1, a two-way reference splitter,
an eight-way feed splitter, three physical feed-to-board permutations, the v5
selector, the common RX connection and Pluto RX2. It is not a board-only VNA
measurement.

This report does not qualify OTA direction finding, absolute antenna phase
centres, the unknown splitter/attenuator absolute transfer, 5.8 GHz operation,
production readiness, or a v6 design. It does not copy the external raw
captures into this repository.

## Evidence boundary

| Evidence | Grade | What it establishes | What it does not establish |
|---|---|---|---|
| [Closed-loop experiment report at exact commit](https://github.com/misko/smateway/blob/c0d8751654c5b869724a6b3666141de68a92789e/docs/closed_loop_permutation_calibration/README.md), SHA-256 `94c842ef03401f9c7e4b7dff179d726ec88a636e45d49a18c78ddf21a444e964` | **CITED** | Fixture, capture contract, model, qualification thresholds, conclusions and safety handoff | Locally retained raw SigMF captures or board-only S-parameters |
| [Machine-readable results](https://github.com/misko/smateway/blob/c0d8751654c5b869724a6b3666141de68a92789e/docs/closed_loop_permutation_calibration/data/closed-loop-calibration-results.json), SHA-256 `1b5fb00488085a634b7ed89d27f901b320d36bcb6a571fe901825c89e2822c55` | **CITED** | Per-frequency corrections, fit residuals, closure, raw-isolation contrast and artifact hashes | Independent reopening of each raw artifact from this repository |
| [Frozen permutation manifest](https://github.com/misko/smateway/blob/c0d8751654c5b869724a6b3666141de68a92789e/docs/closed_loop_permutation_calibration/data/closed-loop-permutation-manifest.json), SHA-256 `28470a30f7a3f14aca3bc407cf39e0b5d3295db2203c700780ed01e54efd7e53` | **CITED** | Board/firmware/Pluto identities, mappings, capture IDs and analysis provenance | Instrument calibration traceability outside the retained manifest |
| [Sealed realized-RF report](../../07_releases/v0.2.1-2026-08-14/verification/rf/realized/report.json) | **MEASURED** on CAD artifact | Exact route lengths, branch-free geometry, reference/fence realization | Physical loss, delay or isolation |
| [Sealed RF PCB review](../../07_releases/v0.2.1-2026-08-14/verification/rf_pcb.md) | **MEASURED** on CAD artifact | 0/0/0 DRC/parity, nine branch-free top routes, zero RF vias, continuous reference and return fencing | S-parameters or manufactured stackup conformance |
| [Prior isolation and v6 mitigation report](2026-08-27-rf-isolation-and-v6-mitigation.md) | **INFERRED** synthesis | Device-level leakage matrix, bypass-path analysis and enclosure options | Measured isolation of this article |

The external analyzer binds its accepted artifacts and reports that every
admitted capture passed metadata continuity, ADC headroom, schedule alignment,
coherent-reference, per-state transfer-SNR and cycle-repeatability gates.
**CITED:** those checks make the summary suitable for engineering decisions,
but the absence of a release-local raw capture package keeps this report's
overall evidence status `INCOMPLETE`.

## Findings

### Conducted calibration result

| Centre frequency (GHz) | Model residual, amplitude / phase RMS | Minimum raw selected-to-ALL_OFF contrast (dB) | Worst coherent leakage phase bound | Decision |
|---:|---:|---:|---:|---|
| 2.400 | 0.056 dB / 0.538° | 32.12 | 1.42° | Qualified, isolation-limited |
| 2.420 | 0.064 dB / 0.525° | 32.23 | 1.40° | Qualified, isolation-limited |
| 2.440 | 0.056 dB / 0.495° | 31.85 | 1.46° | Qualified, isolation-limited |
| 2.460 | 0.045 dB / 0.438° | 31.66 | 1.50° | Qualified, isolation-limited |
| 2.480 | 0.033 dB / 0.411° | 29.32 | 1.96° | Qualified, isolation-limited |
| 5.800 | 0.158 dB / 0.812° after ALL_OFF subtraction | **-8.76** | Unbounded | Experimental; do not deploy |

**CITED:** the five 2.4 GHz conditions clear the experiment's 20 dB
operational contrast gate. None clears the conservative 35.16 dB contrast
needed to bound worst-case coherent leakage below one degree. “Qualified” is
therefore a measured 1.4–2.0 degree isolation floor, not one-degree absolute
phase metrology.

At 5.8 GHz, a low residual after baseline subtraction does not rescue the raw
measurement. A model can fit the desired component even while a larger
uncontrolled phasor dominates the receiver. Any calibration coefficient from
that condition is diagnostic only.

### No port subset is currently qualified near 6 GHz

The experiment measured 5.800 GHz, not exactly 6.000 GHz. **CITED:** the
maximum raw selected-to-ALL_OFF contrast across every admitted 5.8 GHz
observation was only 9.19 dB. Therefore even the best observed state misses the
20 dB experiment operating gate, the project's 25 dB first-article criterion
at 5.9 GHz, and the 35.16 dB one-degree phase target. No single port, pair or
larger subset can be called safe from these captures, and the result must not
be extrapolated to 6.0 GHz.

The fitted board-path gain terms do identify a sensible order for a reduced-
port diagnostic experiment:

| Diagnostic order | Candidate ports | 5.8 GHz gain correction (dB) | Why test them first |
|---:|---|---:|---|
| 1 | ANT1 / ANT8 | 0.000 / 0.369 | Shortest equal routes and strongest fitted selected response |
| 2 | ANT4 / ANT5 | 1.629 / 1.552 | Matched pair with relatively strong fitted response |
| 3 | ANT2 / ANT7 | 2.449 / 2.589 | Matched pair, but weaker than ANT4/ANT5 |
| 4 | ANT3 / ANT6 | 9.887 / 8.310 | Large selected-path sensitivity penalty; defer initially |

**INFERRED:** this is a sensitivity ranking, not an isolation ranking. The
released summary records only the global minimum and maximum raw contrast, not
the per-port contrast census, so it cannot prove that ANT1/ANT8 have the best
isolation.

**PROPOSED:** begin with ANT1 and ANT8, terminate the other six inputs in
characterized 50-ohm loads, and sweep raw selected-to-ALL_OFF contrast from
5.7–6.1 GHz. Admit the pair only if every used state meets at least the current
25 dB project criterion across the intended band. Require approximately 35 dB
if the application needs a one-degree worst-case coherent-leakage bound. Then
add candidate pairs one at a time; do not assume a passing pair remains passing
when more cables or antennas are attached.

### The phase pairs correspond to the routed PCB geometry

The sealed CAD gives the following route lengths. The correction terms are the
2.400 GHz closed-loop board-path corrections, normalized to ANT1.

| Physical pair | Sealed route length (mm) | Gain correction pair (dB) | Phase correction pair (deg) |
|---|---:|---:|---:|
| ANT1 / ANT8 | 22.195 / 22.195 | 0.000 / 0.125 | 0.000 / 0.606 |
| ANT2 / ANT7 | 34.931 / 34.931 | 1.900 / 2.092 | 79.524 / 79.863 |
| ANT3 / ANT6 | 31.501 / 31.501 | 1.444 / 1.513 | 65.738 / 65.245 |
| ANT4 / ANT5 | 36.557 / 36.557 | 2.858 / 2.907 | 95.818 / 96.221 |

**INFERRED:** the exact pair symmetry and phase ordering are strong evidence
that the solver has recovered a real, deterministic board-topology term rather
than random reconnect error. The absolute value also contains switch and launch
phase, so this table is not a dielectric-constant measurement.

This is not automatically a PCB defect. A calibrated phased system can remove
stable complex offsets. It is nevertheless a PCB design characteristic that
must be explicit: without correction, the channels are not phase-equivalent;
with correction, the longest paths still pay their real insertion-loss and
noise penalty.

### The 2.480 GHz amplitude change deserves a board-level investigation

At 2.480 GHz the middle six board paths require 6.220–7.725 dB gain correction,
while ANT1 is the reference and ANT8 requires only 0.049 dB. **CITED:** the
physical permutations separate the eight-way feed-arm terms from the fitted
board-path terms, so the effect cannot be dismissed as one bad splitter arm.

**INFERRED:** the symmetry again points toward a repeatable selector/launch/
route response. Possible causes include an impedance discontinuity, connector
or switch-state mismatch, a frequency-localized standing-wave interaction, or
coupling tied to the longer fanout paths. Copper loss alone is unlikely to
explain such a sharp change over 20 MHz. The experiment does not resolve those
possibilities.

Amplitude equalization is not a complete fix. Multiplying a weak channel by a
larger coefficient also multiplies its receiver noise. Direction-finding code
should retain per-port SNR/noise weights and reject a port or dwell that falls
below the qualified transfer-SNR envelope.

### Does this show a PCB design problem?

| Observation | Assessment | Confidence | Required disposition |
|---|---|---|---|
| Stable three-permutation fit and reconnect closure at 2.4 GHz | No evidence of an intermittent switch, wrong state map or gross assembly defect | High within the cited fixture | Preserve the calibration and normal mapping |
| Large paired phase offsets | Real consequence of unequal electrical paths; acceptable only with calibration or a locked uncalibrated-error budget | High | Make calibration mandatory, or physically shorten/equalize v6 paths |
| Sharp long-path amplitude penalty near 2.480 GHz | Potential PCB/switch/launch resonance or mismatch; not yet localized | Medium | Dense board-only VNA sweep and time-domain/gating analysis |
| 29.32–32.23 dB raw contrast at 2.4 GHz | Meets the experiment's operational gate but not its one-degree precision gate | High | Report the 1.4–2.0° floor; do not claim one-degree metrology |
| -8.76 dB worst raw contrast at 5.8 GHz | System-level failure; selected signal may be below coherent leakage | High | Block 5.8 GHz deployment until the boundary ladder identifies and removes the bypass |
| Good 5.8 GHz fit after ALL_OFF subtraction | Desired path is repeatable, but the dominant additive leakage source remains unidentified | Medium-high | Do not assign the failure to the PCB without board-only evidence |

### Calibration-model limitation

The three cyclic mappings overdetermine amplitude and the relative complex
board/feed terms, but retain an exact eight-way 45-degree phase-ramp ambiguity.
The released result chooses the minimum reconnect-common-phase branch, supported
by the continuous RX1 reference and 1.12–1.91 degree common reconnect phase.
**CITED:** further cyclic rotations cannot remove the ambiguity.

If absolute spatial phase matters, use one deliberately non-cyclic mapping,
such as swapping only F1 and F2, as a held-out validation. This is a fixture and
calibration requirement, not a PCB change.

## Recommendations

### Immediate operational controls

1. Load only the qualified 2.400–2.480 GHz complex corrections and preserve
   their exact frequency/configuration identity.
2. Interpolate complex response or fit a delay/dispersion model; never linearly
   interpolate wrapped phase angles.
3. Keep ALL_OFF samples as a live leakage/noise monitor and reject any dwell
   whose raw contrast, metadata continuity or transfer SNR falls below the
   qualified envelope.
4. Carry per-port SNR/noise weights into direction finding. Do not describe
   amplitude normalization as recovered sensitivity.
5. Keep 5.8 GHz coefficients diagnostic-only.

### Measurements before a PCB respin

| Priority | Measurement | Decision it enables |
|---:|---|---|
| 1 | Calibrated board-only VNA measurement at all nine SMA reference planes, with unused ports in characterized 50-ohm loads | Separates selector PCB/switch isolation from Pluto, cable and fixture leakage |
| 2 | Dense 2.350–2.550 GHz insertion/return/isolation sweep, with particular resolution around 2.460–2.500 GHz | Confirms whether the long-path amplitude change is a board resonance/mismatch and locates its bandwidth |
| 3 | Dense 5.4–6.2 GHz board-only sweep, followed by Pluto + cable + board boundary additions | Locates the -8.76 dB system leak without changing several boundaries at once |
| 4 | One held-out non-cyclic feed permutation | Removes the cyclic phase-ramp ambiguity and tests absolute phase transportability |
| 5 | Repeat the qualified mapping after cable reroute, enclosure change, temperature soak and reconnection | Establishes which correction terms are portable and when recalibration is mandatory |

For the VNA matrix, record every selected common-to-active path, all 56
common-to-off cells, ALL_OFF common-to-each-input behavior, return loss at all
ports, Touchstone files, calibration-kit identity, cable identity, state
evidence and photographs. The existing 25 dB common-to-off first-article
criterion at 5.9 GHz remains the project authority until an ADR changes it.

### Conditional v6 PCB direction

If board-only measurements reproduce the paired loss or isolation problem:

1. **PROPOSED:** reposition the switch and connectors so the longest branches
   become shorter and the eight routes become more equal by geometry. Do not
   add serpentine delay merely to make the short paths lossy; minimize the
   worst path first.
2. **PROPOSED:** retain branch-free top-layer routing, continuous adjacent
   ground and route-following fences, but add a grounded shield-can footprint
   over the switch and central fanout with a via-stitched perimeter designed
   as one RF boundary.
3. **PROPOSED:** keep the absorptive PE42482 for the first A/B coupon so switch
   topology and mechanical shielding are not changed simultaneously. Compare a
   higher-isolation part only with identical launches, stackup and loads.
4. **PROPOSED:** preserve full SMA access for calibration and avoid unterminated
   diagnostic stubs. If a calibration injection feature is added, it needs a
   characterized coupler/switch path and its own ALL_OFF leakage budget.
5. **PROPOSED:** provide a chassis-bond/shield-can ground land independent of
   case fasteners, then compare bare, shield-can and bonded-metal-enclosure
   matrices.

If the board passes alone, do not churn its controlled RF geometry. Apply the
prior report's v6A system-boundary changes instead: short double-shielded coax,
bulkhead SMAs bonded to a conductive RF cassette, controlled cable routing,
and antenna separation/orientation trials.

## Validation plan

### Phase 1 — reproduce and bind the cited result

1. Preserve the exact external report/result/manifest identities recorded in
   the evidence table.
2. Reopen the raw capture set from a durable artifact package and reproduce the
   machine-readable result byte-for-byte or explain every deterministic
   difference.
3. Repeat the final normal mapping once to confirm that the present hardware
   remains inside the reported closure envelope.

### Phase 2 — separate board, cable and Pluto boundaries

1. Measure the selector alone at its SMA planes with a VNA.
2. Add only the RX2 cable and characterized terminations.
3. Add Pluto RX2 with TX muted and verify its receiver baseline.
4. Add the bounded TX1/reference stimulus.
5. Add the plastic enclosure, then a shield can and bonded RF cassette.
6. Add antenna cables and antennas last.

At each step retain raw isolation and selected transfer, not only
ALL_OFF-subtracted data. The first boundary that collapses raw contrast owns
the next corrective experiment.

### Phase 3 — test a v6 candidate

1. Compare v5 and v6 on the same fixture, loads, cables and calibration.
2. Require no regression in selected-path insertion loss or return loss.
3. Re-run all 56 off-path cells and the ALL_OFF census over both frequency
   bands.
4. Verify the non-cyclic held-out mapping and reconnect closure.
5. Repeat after the intended enclosure, cable routing and antenna panel are
   installed.

A v6 release must report the worst cell and its state/frequency, not only an
average isolation. Any one-degree phase claim additionally needs at least
35.16 dB raw contrast or a tighter directly validated coherent-leakage model.

## Source register

| Source | Type | Use in this report |
|---|---|---|
| [Smateway closed-loop permutation report at exact commit](https://github.com/misko/smateway/tree/c0d8751654c5b869724a6b3666141de68a92789e/docs/closed_loop_permutation_calibration) | Cross-project experimental report | Fixture, qualification outcome, phase-branch caveat, findings and operating guidance |
| [Closed-loop result JSON](https://github.com/misko/smateway/blob/c0d8751654c5b869724a6b3666141de68a92789e/docs/closed_loop_permutation_calibration/data/closed-loop-calibration-results.json) | Machine-readable experimental summary | Per-frequency corrections, residuals, closure, raw contrast and source hashes |
| [Closed-loop permutation manifest](https://github.com/misko/smateway/blob/c0d8751654c5b869724a6b3666141de68a92789e/docs/closed_loop_permutation_calibration/data/closed-loop-permutation-manifest.json) | Frozen experiment manifest | Hardware/firmware identities, physical mappings, capture IDs and provenance |
| [Sealed v5 realized-RF report](../../07_releases/v0.2.1-2026-08-14/verification/rf/realized/report.json) | Immutable PCB CAD evidence | Exact paired route lengths and RF geometry |
| [Sealed v5 RF PCB review](../../07_releases/v0.2.1-2026-08-14/verification/rf_pcb.md) | Immutable PCB review | Routing/reference/fence quality and physical VNA evidence boundary |
| [Sealed first-article test plan](../../07_releases/v0.2.1-2026-08-14/verification/FIRST_ARTICLE_TEST_PLAN.md) | Immutable measurement procedure | Existing isolation target, reference planes, terminations and state census |
| [RF isolation, leakage paths, and v6 mitigation strategy](2026-08-27-rf-isolation-and-v6-mitigation.md) | Prior project report | Device isolation matrix, bypass paths, enclosure and alternative-switch analysis |

## Disposition

Report synthesis: **REVIEWED**. PCB and product evidence: **INCOMPLETE**.

The 2.4 GHz calibration is usable within its measured isolation floor and exact
configuration. The 5.8 GHz system is not deployable on this evidence. No PCB
source change is authorized by this report alone: first close the board-only
VNA matrix and boundary ladder. If they implicate the PCB, open a v6 ADR that
locks the path-equalization objective, shield boundary and measured isolation/
insertion-loss acceptance criteria before changing placement or routing.
