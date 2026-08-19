# Pre-route topology review — USB Controlled Debug Hub v2

review_stage: pre-route
review_kind: topology
design_verdict: SOUND
order_verdict: BLOCKED-SOURCING
netlist_sha256: e5999cc54248976423e736eab7e72b4fcb04b68170b4b8ad3903ba4a2af3ea59
parts_sha256: bef283a987f8cd38d20d424eae5cf1e0b212db89766aea22b666779ff1406a3e
design_rules_sha256: c1ce6821bbab53e5f83b884f60ac1d2491ab03365e0875b1eed2fd7870002d92
circuit_sha256: 3015d410603e89d1d3936f0b144b67deeb9997964589eff704fbfddbeb21c4e9
reviewed_at: 2026-08-19T12:53:42-07:00

## Scope and result

The exact regenerated 165-component circuit/netlist, 42 current part dossiers,
ADR-0015/0016, protection paths, power tree and 137 electrical invariants were
reviewed before PCB regeneration. No remaining source-topology or ratings
defect was found. This verdict does not authorize layout or ordering: the exact
53-code JLCPCB pre-layout response remains blank.

- USB-C POWER is a sink-only 15 V contract. Only the 1 uF / 50 V damping
  capacitor is directly exposed at attach; the two 10 uF buck-input capacitors
  stay behind the negotiated-voltage TPS259470A UVLO and dV/dt gate.
- `TVS1800DRVR` protects the post-fuse PD input. Its specified 24.7 V maximum
  35 A, 8/20 us, 125 C clamp is coordinated against `U_PD_IN`'s 28 V input
  absolute maximum. The 3.3 V tabulated margin is not used to waive the
  mandatory exact-pad transient capture on first article.
- TPS56637 uses 73.2 kOhm + 374 Ohm over 10 kOhm precision feedback. Reference,
  tolerance and TCR yield a machine-checked 4.92511–5.10424 V DC window. A
  separate 100 mV dynamic allocation leaves about 45.8 mV below 5.25 V and
  remains subject to no-load/load-release oscilloscope qualification.
- The TPS259804 aggregate stage has 5 mOhm guaranteed maximum RON. Its 300 Ohm
  characterized programmer charges to 4.27451–5.77551 A, and the 6.8 nF C0G
  timer bounds overload blanking to 1.610–6.650 ms. The exact input path must
  tolerate a qualified 5.78 A / 7 ms pulse.
- The protected-rail floor is 4.860 V at the 2.58 A simultaneous normal load.
  Each 500 mA mated-plug path clears its switch/copper/contact drop budget with
  the declared 20% margin.
- Every external TPS259470A uses TI's characterized 3.32 kOhm row, charged to
  0.84704–1.15404 A. Open `ITIMER` and `DVDT` are intentional minimum-delay and
  fastest-turn-on selections; capacitive startup and short behavior remain
  first-article gates rather than inferred guarantees.
- One worst-high port fault plus three 500 mA ports and normal internal demand
  is 3.23404 A, 1.04046 A below the aggregate worst-low threshold. Two such
  faults under normal internal demand remain 0.38642 A below it. The complete
  all-downstream worst-high sum is 5.80216 A, only 26.65 mA above the aggregate
  worst-high threshold; this narrow extreme-case interruption margin is
  explicit and must be stress-tested, not described as generous selectivity.
- Aggregate latch-off intentionally removes the management plane. Cycling
  USB-C POWER is the only recovery path; no software-clear claim is made.
- Source identity distinguishes all five TPS259470A instances from the
  TPS259804 aggregate stage. The generator synchronizes every hidden `LCSC
  Part` field and the BOM/source gate independently rejects per-reference PCB
  metadata drift.
- USB-C DATA remains VBUS-sense-only and cannot power or back-power the board.
  Hardware AND gates retain policy interlocks without project firmware.

## Exact machine corroboration

- E-INV schema and netlist: 137/137 PASS;
- E-ADR: 5/5 PASS;
- D-SPEC/E-PATH, E-SURGE, E-CAP and E-FAULT: 5/5 gate families PASS;
- E-TOPO: 7/7 rails and 2/2 converter dossiers PASS;
- E-MARGIN: 7 rails PASS, including the 100 mV regulator allocation;
- JLC pre-layout request reproducibility: PASS, 53/53 exact codes;
- public catalog negative filter: 53/53 PASS, not assembly allocation.

The release remains a bench instrument. Physical transient, thermal, drop,
reverse-current, overload and USB signal-integrity evidence is deferred only
to a quantity-five first article, never to unrestricted production.
