subject: usb-controlled-debug-hub-v1 v0.1.0-2026-08-17 release staging
date: 2026-08-17
reviewer: redteam-agent (fresh-context topology/protection/ratings lens)
context-given: full-tree
source_commit: 39c50d9517d05c3315d6411c1b3512db09d62975
board_sha256: 4c69a2dfbc7bd6c78fdfa4675316d42e5028249984b4bf455bdab4a733e7cd28
design_verdict: DEFECTIVE
order_verdict: DO-NOT-ORDER

# Final routed-release topology, protection, and ratings red-team review

## Scope and exact subject

This is a clean-room review of the exact mutable staging archive at
`06_build/release_staging/v0.1.0-2026-08-17`, supplemented by the project
architecture, decisions, rules, authoritative part dossiers, and the PCB/JLC
release contracts. It does not adopt an earlier review's verdict. The working
tree was dirty and the staged manifest says `git_sha: pending release seal` and
`git_dirty: true`; therefore the commit above is repository context, not proof
that it contains the reviewed bytes.

| artifact | SHA-256 |
|---|---|
| staged PCB | `4c69a2dfbc7bd6c78fdfa4675316d42e5028249984b4bf455bdab4a733e7cd28` |
| staged schematic | `dccfa2feb7949225e7c789175cffab569fb4d7fa510cc194b872d6ae4c7d5f48` |
| staged TSX | `595bc3d60fc781ae08d1de825c273f23db3a66a9261904425baf251da3176590` |
| staged netlist | `0d3fbddb082f4e1772205914cc65cbb9c8241c96a6e5152c5e32c68bb4e53087` |
| staged `.kicad_dru` | `fd21d98c2fa11183ba914013bcf21c8732ec8fe7fee5ff0641ec2a97e7323802` |
| Gerber ZIP | `fb7a5ba8508a639a08c53577f67e408db4a0c394339c87e43d341f4d011deca7` |
| BOM / CPL | `88c9070e733cf3ae7363a88b19d5b63270c28105296c6dfd09e692454ecfd35d` / `209a3dad517a0ac8bbc6c5d161b7707dcd8d969ccce03bda92a2217982055a0d` |
| staged DRC JSON | `4d2a2fb227e2ae6197bee24fd446f01a8b7c46842a4f00b3a07acdc7a2b9973e` |
| staged policy audit | `765b887c1c745f545377b6f8aea61a45982310ae527c6ad257c517d46e0c9533` |
| staged integrated audit | `b78abdc3c63e04824995cf9e9e63c2b437a7fce34079e964ad56356a2a796148` |
| draft manifest | `e47a25fdcba01cdde390e3f08a7a470924b844407d5bca8e73fd644c120f46c8` |

The architecture/rules hashes reviewed were: `ARCHITECTURE.md`
`9dce11f55c04b7cadf5e396db224eab49131d643b8ddea7c4ddfd8eb811c03f7`;
`requirements.yaml` `a1d575599b65a2ea98c200e47cdee089b2983a2a12318511633fd8c184b5c459`;
`electrical_invariants.yaml` `beb901b27866360189324789beb7a2972f9446cb3517e2b38bf015d29dcca038`;
`power_tree.yaml` `ae34fda05059d3e73ec18ae3ae0f302b616febdf2c7cf36c59d2b0397b049cd0`;
`power_stages.yaml` `20437f393c670a2964878ccfb3915757d63a047673f2818e6cf0a009dc82aef1`;
`protection_paths.yaml` `8ea1797da3ea7bb25122a923d3105e111b2eead3ed5b7fc0cf1c77928588da6b`;
`nets.yaml` `a89398ad61b2ad2d5864df2540356761612608f06f8479bf5ecf610edb64dea4`;
and `assembly.yaml` `08f59c4e9a367fc95879db41e8ff260a01ad51b87694636c59877b1fe4364d37`.

## Prioritized findings

### P0 — realized 0.15 mm drills exceed the declared plated-through aspect-ratio ceiling

The exact PCB and `via_process.txt` contain 27 ordinary `0.410/0.150 mm`
vias. The source stackup is nominally 1.6 mm, so these realize
`1.6 / 0.15 = 10.67:1`. The governing `jlc_4layer_advanced` tier caps PTH
aspect ratio at 10:1. The route preflight reports 0 FAIL only because its
aspect-ratio inventory grades the common 0.20 mm and selected 0.35 mm
configuration entries; it does not enumerate the realized wave-specific
0.15 mm family. DRC and the via-process family audit cannot prove drill
fabricability.

This is a design and order blocker. Increase those drills, reduce the finished
thickness under an approved stackup, or obtain and bind a manufacturer-approved
construction that satisfies the actual finished-hole aspect ratio. Then
regenerate and rerun the realized-board tier check. An uploader note is not a
waiver for an out-of-tier drilled geometry.

### P0 — the contract-required policy gate is red, including human-interface and power-copper defects

The staged `policy_audit.md` reports `FAIL=6`, while the release contract
requires zero FAIL. Its material findings include:

- `P-SILK-FN`: 7/7 human-facing connector/fuse references lack a nearby
  functional label (`J_PWR`, `F_IN`, `J_UP`, `J_PORT1..4`). In particular,
  absence of a durable 5 V polarity/function marking at the input defeats the
  stated protection posture by making operator reversal more likely.
- `R-POUR`: the reported high-current rails have no zones. Independent
  inspection of the exact PCB found zero zones on `P5V_RAW`, `P5V_FUSED`,
  `P5V_PROTECTED`, `VBUS1_SW..VBUS4_SW`, and `VBUS_CTRL`; the design instead
  depends on tracks and package-local necks. DRC width floors do not prove the
  claimed 3 A continuous/5 A transient common path, the 25 mOhm copper/via/
  joint budget, or temperature rise.
- `P-PLANE`: three signal tracks occupy In1 (`HUB_PRTPWR4` and `I2C_SCL`), so
  the asserted continuous-reference-plane posture has no passing region-based
  continuity proof. The exact board also uses In2 for control/VBUS-sense
  routing. These may be spatially benign, but the release supplies no passing
  machine evidence delimiting the USB reference corridors.
- `S-VER` and `S-OCCL`: two dossier citation records are weak and the staged
  schematic has four text/wire occlusions. These undermine the independent
  human audit trail even though netlist connectivity is unaffected.
- `R-THERM` flags the USB2517 exposed pad. Inspection shows sixteen 0.20 mm
  drilled pad-65 lands embedded in the footprint, so this looks like a checker/
  footprint-representation mismatch rather than an absent physical via array.
  It nevertheless remains an unresolved hard-gate contradiction; resolve it
  with a corrected gate or evidence-backed adjudication rather than silently
  crediting the geometry.

The routed board cannot receive `design_verdict: SOUND` while its governing
integrated policy gate is red.

### P0 — staged archive is not a self-contained or sealable release subject

The staged integrated `audit.txt` is explicitly `overall: BLOCKED`: only
121/139 fitted footprint models resolve when the copied source is opened in
the archive layout. Eighteen `${KIPRJMOD}/../03_src/lib/3d/...` paths point to
a location inconsistent with the archive's copied model directory. The
archive also lacks contract-required `verification/design_math.md`, pin,
render, layout-red-team, and final freshness evidence; its manifest contains
no file hashes or source commit and explicitly records a dirty pending seal.
This prevents offline reopen/replot/model review and blocks release admission
independently of the circuit findings.

### P1 — aggregate protection has narrow transient coordination and must be tested as a system

The five TPS2557 worst-high limits plus the 3.3 V input allowance total
4.45 A. The TPS259474L can trip as low as 2.990 A and its charged timer can
expire in 1.608 ms, while the declared allowable service peak is 3.0 A for
1.5 ms. That leaves only 0.108 ms between the source contract and the
fastest calculated latch-off corner. Four external outputs each include
22 uF after their switches, and an MCP23017 register write can command four
ports together. TPS2557 controlled rise helps, but no staged waveform proves
that concurrent output-capacitor/device charging plus operating load stays
below the aggregate trip-time integral across voltage, temperature, and part
corners.

This is a first-article limitation, not permission to ignore the global
latch-off behavior. Exercise simultaneous four-port enable, loaded hot-plug,
short, recovery, and upstream-host sequencing at the worst-low eFuse threshold;
verify that a single downstream fault produces the intended hub OCS response
before or without an unacceptable whole-board latch, and verify that removing
external power is an acceptable recovery mechanism.

### P1 — USB data disconnect is logically fail-off but not a physical-state interlock

The topology is internally consistent: `PWR_EN = PRTPWR AND PWR_CMD`,
`DATA_OK = PWR_EN AND DATA_CMD`, the 2N7002 pulls active-high-disconnect `OE`
low only for data-on, and pull-down/pull-up defaults force full-off during
reset or loss of management power. Upstream VBUS reaches only the 100k/100k
sense path, so no board-power backfeed path was found.

The limitation is correctly admitted but remains operationally important:
data-on follows the commanded enable, not `VBUS_SW`, power-good, or TPS2557
fault state. FSUSB42 provides no connection-status output. Software readback
therefore cannot be represented as proof of VBUS presence, physical data
connection, attach, or enumeration. First article must test brownout, reset,
MCP23017 default-input state, control-rail collapse, TPS2557 fault, aggregate
latch-off, and command transitions with real devices.

### P1 — the USB 2.0 margin is prototype evidence, not a production rating

The chosen shunt ESD part has a bounded 0.7 pF maximum, but FSUSB42 on
capacitance (3.7 pF), bandwidth, and 200 ps jitter are typical values, not
worst-case guarantees. The switch plus ESD nominal budget already reaches
4.4 pF before connector, package, vias, and PCB discontinuities. The routed
geometry is provisional and the upstream route contains long localized
uncoupled copper by the project's own measured contract. No final JLC
JLC04161H-7628 impedance solve/coupon selection or USB eye/compliance result is
present. Therefore enumeration alone is insufficient: require High-Speed eye,
traffic/error, attach/detach, and disconnect leakage/isolation tests across all
four paths, with production held until results cover representative boards.

### P1 — first power and production qualification remain HOLD

No release-bound `03_src/rules/first_article.yaml` or measured authorization
record exists. The following are not established by DRC or arithmetic and must
remain explicit holds: exact 5.20–5.25 V source qualification at 3 A continuous
and 5 A/6 ms, hot four-wire common/branch drop, four simultaneous 500 mA mated-
plug voltages, fuse-holder and connector-lot contact resistance, fuse/eFuse/
TPS2557/buck thermal rise, exposed-pad assembly, selective Type-VII via process,
and abnormal/reverse-input behavior. The sustained-input-OV boundary above
5.25 V is explicitly out of scope; the product must be labeled and operated as
a regulated-SELV-input fixture, not as a generic 5 V-tolerant appliance.

### P2 — architecture decisions that are sound but must not be overstated

- A seven-port hub is the correct way to obtain four external functions plus
  one internal management function on one upstream pair; ports 6–7 are
  hardware-disabled and port 1 is non-removable under the documented default
  strap mode.
- The MCP2221A/MCP23017 path meets the no-project-firmware requirement, but it
  still requires host-side use of the manufacturer's protocol. “Firmwareless”
  does not mean “no host integration.”
- The 180 uF polymer plus 22 uF X7R arithmetic provides 128.664 uF under the
  declared loss model, only 8.664 uF above the 120 uF floor. Exact population,
  polarity, and effective capacitance should be confirmed; no alternate is
  authorized.
- The exact Keystone holder and Littelfuse fuse are manual post-PCBA items.
  Their absence from JLC population is deliberate, but an assembled board is
  not power-ready until both exact parts are installed and inspected.

## Gate and evidence scoreboard

| item | result | denominator / observation |
|---|---|---|
| DRC / unconnected / schematic parity | PASS | 0 / 0 / 0 on the hash-bound PCB |
| ERC errors | PASS | 0 errors; 768 warnings |
| electrical invariants | PASS | 82/82, but staged report references live-tree netlist paths |
| power topology / margin | PASS as arithmetic | 6/6 topology rails; 5 graded external/load margins |
| BOM source / stock / assembly | PASS at staging time | 138 coded refs; 33/33 stock lines; 146 board footprints / 138 CPL placements |
| via-process family audit | PASS but incomplete for tier | 525/525 classified; does not catch 10.67:1 aspect ratio |
| integrated policy | FAIL | 6 FAIL, 6 HUMAN, 9 N-A, 25 PASS |
| standalone staged-source model coverage | BLOCKED | 121/139 in `audit.txt` |
| manifest/seal/freshness | INCOMPLETE | dirty, pending SHA, no manifest hash census |
| uploader BOM/rotation/THT/via/stackup evidence | ABSENT | human order gates remain open |
| first-article authorization | HOLD | no card and no measurements |

## Required disposition before another final review

1. Correct the realized 0.15 mm via aspect-ratio violation and close the
   realized-board tier-preflight coverage gap.
2. Regenerate the board/schematic until the exact staged policy audit has zero
   FAIL, including functional silk and an evidence-backed power/plane/thermal
   disposition.
3. Repair archive-relative model/library paths and prove standalone reopen,
   model coverage, DRC, replot, and payload identity from copied source only.
4. Add the contract-required design math and fresh pin, render, topology, and
   layout witnesses against one immutable staging subject.
5. Obtain and preserve the final JLC impedance/stackup, selective-via-process,
   BOM echo, placement/rotation, double-sided SMT, and six-connector THT
   previews; repeat stock at order time.
6. Create the first-article card and retain all electrical, thermal, transient,
   USB compliance, and connector-lot measurements as production holds.

Until items 1–4 are fixed and re-gated, the design is defective for release.
Until all applicable order-side items close and a clean immutable release is
sealed, the only safe purchase instruction is `DO-NOT-ORDER`.
