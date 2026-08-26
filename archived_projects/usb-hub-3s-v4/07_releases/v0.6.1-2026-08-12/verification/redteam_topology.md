subject: usb-hub-3s-v4 routed r9 topology publication reseal
date: 2026-08-12
reviewer: Codex independent topology/protection/ratings publication reviewer
context-given: exact routed board, exact netlist, current rules/parts, and sealed publication evidence
source_commit: ca9cc5785781820239bf513a43cbfc8db4d1eed7
board_sha256: 9888b1267744b8f659ce3f57dd0cbdd037e208440781bd1c80da88b2b1966dfb
netlist_sha256: ed689c7d75719a3c7955511a2b1311fb0438443cb2ef6da58280ed97a4461763
exact_netlist_sha256: 222667931a0147368cac49ea1b0799e78826ef64f0282dc33907a8287af2612f
design_rules_sha256: ef3693aae5be7dfbb29e762e15203d6e86db57164f31176238be1657b35dfb62
parts_sha256: 8e3d14083528ee127709753251ab2f8f4349a34203d73b93f0dd49a5f5dffb2e
layout_seal_sha256: e7e197cd0bf6b4e71a55ce04c716e3d6d3c9d2e817138c7e866611ca348719f3
release_manifest_sha256: b7cfd591fb95c74516e843b0c44bb6605833eb6c327f43d3a521c8b5c809bcc3
design_verdict: SOUND
order_verdict: DO-NOT-ORDER

# Routed r9 topology publication reseal

## Exact evidence binding

I independently re-reviewed the unchanged canonical routed board
`04_kicad/usb_hub_3s_v4.kicad_pcb`, its exact electrical netlist, current
topology/protection/rating rules and the sealed `v0.6.0-2026-08-12`
publication evidence. The board SHA-256 is exactly the assigned
`9888b1267744b8f659ce3f57dd0cbdd037e208440781bd1c80da88b2b1966dfb`.
The release copy `source/usb_hub_3s_v4.kicad_pcb` and release netlist are
byte-identical to their live counterparts. Neither board nor netlist differs
from the archive's recorded source commit
`9b0bfd4bd6b2bd3b99d8ab485defc8fad80b317d`; the `source_commit` header binds
this publication reseal to current HEAD.

The normalized netlist hash above removes only KiCad export-clock/path/UUID
presentation churn; the exact-byte hash is bound separately. The current
canonical rule digest covers all authored rule YAMLs plus the design projection
of `route.yaml`; the parts digest covers all 25 sorted part dossiers. The
release manifest, current layout seal and the hashes above provide independent
publication, routed-board and electrical-policy witnesses. Current
`power_tree.yaml` and `FIRST_ARTICLE_TEST_PLAN.md` are byte-identical to the
copies in the sealed archive.

Fresh read-only checks returned 91/91 electrical invariants, 4/4 converter
topology rails, 12/12 rail-margin cases, a declared OFF path, 5/5 early-design
gate families, 192/192 declared physical pin identities and 324/324 board
nodes. The live and standalone-archive DRC JSON each contain zero violations,
zero unconnected items and zero schematic-parity findings. The exact board
census is 95 footprints, 446 routed segments, 183 vias and 54 zones.

## Bounded topology and protection observations

- The input path remains `J1.1 BAT_POS -> F1 -> VBAT_FUSED -> Q1.D(5..8) ->
  Q1.S(1..3) -> VIN`. Q1 is oriented for reverse-battery blocking; D5 clamps
  its gate-to-source stress. D1 SMBJ15A is cathode-to-protected-VIN and
  anode-to-GND after Q1, so reverse battery does not forward-bias the rail TVS.
  The TVS is a hot-plug/wiring-transient clamp only. There is deliberately no
  active sustained-input or converter-fail-high OVP.
- SW1 OFF grounds `EN_BUS`; ON releases it to the sole VIN pull-up. Both buck
  modules and every downstream source switch are therefore disabled in OFF,
  but this is enable-controlled shutdown rather than galvanic battery
  isolation. A protected 3S pack and external disconnect at or above 9.0 V
  remain mandatory.
- USB-A remains `VIN -> U1 TPSM63610 -> 5VA_RAW -> U9 TPS259827O -> 5VA ->
  U4/U5/U6 TPS2559 -> VBUSA1/2/3 -> J2/J3/J4`. U9 is the no-OVLO latch-off
  circuit-breaker option. Each receptacle has its own downstream limiter,
  charge-signature cell and local ESD clamp; no USB-A data net reaches another
  receptacle, upstream connector, hub or PHY.
- Type-C remains `VIN -> U2 TPSM63604 -> 5VC_RAW -> U3 TPS25810 -> VBUSC ->
  J5`. U3's IN/AUX/EN/CHG/CHG_HI strapping selects an attach-controlled fixed
  5 V source with 3 A advertisement. CC1/CC2 remain separate through D6; all
  four J5 VBUS pins are VBUSC, all GND pins and shell are GND, and USB2/SBU
  contacts are explicit no-connects. There is no USB-PD or USB data path.
- The routed evidence preserves full-board ground planes, poured high-current
  nets and the declared forced layer transfers. Fresh via-ampacity grading
  passes 4/4 banks: U9's 5VA distributor has 11.76 A credited against 8 A,
  and each TPS2559 input bank has 3.91 A against 2.849 A. Process evidence
  grades all 183 vias as 65 protected 0.50/0.20 mm filled/capped sites and 118
  ordinary 0.30 mm-drill sites, with no partial family. These checks do not
  replace complete-path resistance or thermal measurement.

## Bounded rating observations

- Three USB-A ports require 6 A continuous and permit 7.5 A for no more than
  10 ms. U1 is rated 8 A continuous/10 A peak. Exact R26 programs U9 to
  6.160253--8.066419 A, and C29 gives an 11.129--45.962 ms modeled persistent
  overload interval. Each exact 43.2-kohm TPS2559 setting gives
  2.554--2.849 A, clearing the short peak while staying below the 3 A USB1130
  contact rating. This is proprietary charge-only service, not a USB-IF BC1.2
  current-compliance claim.
- The input calculation is approximately 5.8 A at 9 V for the simultaneous
  47.058 W load, below the 7.2 A VIN routing contract. The 10 A fuse remains
  catastrophic wiring/trunk protection; pack prospective fault current,
  interrupt rating, clearing behavior, holder/Q1 thermal withstand and BMS
  behavior require system-level acceptance.
- U1's effective ceramic bank is 80.784 uF versus 75 uF required. U2's ceramic
  bank is 40.392 uF versus 30 uF. Panasonic C23 contributes 115.2 uF at the
  independently charged initial/life corner, so U3 sees 155.592 uF versus its
  120 uF cold-socket minimum. The mixed ceramic/polymer banks remain subject
  to first-article loop, startup, load-step and thermal validation.
- The U1 rail computes to 5.015--5.228 V and retains its declared 15 mV
  high-side variation reserve below 5.25 V. The revised U2 divider computes to
  5.064--5.227 V with its conservative 0--500 nA engineering FB-current
  screen and likewise retains 15 mV below 5.25 V. That U2 current bound is not
  a manufacturer maximum; exact populated-board voltage remains a release
  measurement.
- The Type-C delivery proof is conditional on the complete J5-to-Raspberry-Pi
  interconnect measuring no more than 39 milliohm hot. The 98-milliohm total
  path budget and 5% residual margin are valid only after that exact cable/Pi
  path and the board's 4-milliohm allocation pass hot four-wire testing.

## Publication and order boundary

The sealed archive is internally inspectable: its exact live and standalone
DRC witnesses are clean; required release evidence reports 35 required
artifacts present; its BOM/CPL and local process records exist; and its source
board/netlist match the live design. This reseal does not manufacture external
evidence. The JLC uploader preview has not been accepted, the item-specific
Type-VII fill/cap instruction has not been acknowledged by the fabricator, and
physical first-article electrical, resistance, stability, fault, backfeed,
thermal and interconnect results do not exist. The archive itself explicitly
states that it has not been ordered.

## Closed verdict

The exact routed board is `SOUND` for the commissioned supervised,
protected-3S-input, power-only, fixed-5-V, no-PD, no-active-OVP prototype
boundary. No topology, protection-network or component-rating defect was found
in this publication reseal. `SOUND` does not assert fabrication acceptance,
USB-IF compliance, production qualification, bare-pack safety or successful
first-article testing. Because the JLC uploader/process gates and physical
first-article evidence remain absent, the closed order verdict is
`DO-NOT-ORDER`.
