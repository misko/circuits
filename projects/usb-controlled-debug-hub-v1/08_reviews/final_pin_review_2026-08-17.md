# Final routed-release pin/connectivity review — 2026-08-17

subject: usb-controlled-debug-hub-v1 v0.1.0-2026-08-17 mutable release staging
date: 2026-08-17
reviewer: independent-agent (fresh routed-release pin/connectivity lens)
context-given: full-tree authority, exact staged source treated as the immutable review subject
source_commit: 39c50d9517d05c3315d6411c1b3512db09d62975
board_sha256: 4c69a2dfbc7bd6c78fdfa4675316d42e5028249984b4bf455bdab4a733e7cd28
design_verdict: DEFECTIVE
order_verdict: DO-NOT-ORDER

## Verdict

The routed board has no discovered node-level functional miswire: an
independent parse of the staged exported netlist and staged PCB found **508/508
nodes and 105/105 nets identical**, with zero missing nodes, extra nodes, or
net-name mismatches. The staged DRC independently reports zero violations,
zero unconnected items, and zero schematic-parity findings. Hub USB polarity,
management-port swapping, per-port PRTPWR/OCS association, command interlocks,
safe-state biasing, power-tree pin functions, and all intentional NCs are
electrically coherent on the exact staged bytes.

The release review nevertheless cannot grade the design `SOUND`. One accepted
ADR contradicts the exact TSX, executable invariant, netlist, and board on four
connector ESD channel assignments; the required digest-selected fresh-pin
authority is incomplete; and the only human connector-orientation approval is
not bound to the current routed subject. These are evidence/source-of-truth
defects rather than a demonstrated D+/D- reversal, but the review contract is
fail-closed. Do not seal or order this staging package.

Findings: **P0/P1/P2 = 0/3/0**.

## Findings

### P1-1 — ADR-0006 contradicts the exact downstream ESD pin/net assignment

ADR-0006 explicitly requires `U_ESD1..4.1=P*_PORT_N`,
`.2=P*_PORT_P`, `.3=GND`. The exact staged TSX, current
`electrical_invariants.yaml`, exported netlist, and PCB instead realize all
four instances as `.1=P*_PORT_P`, `.2=P*_PORT_N`, `.3=GND`.

This is not evidence of a USB polarity reversal: the exact Nexperia dossier
identifies IO1 and IO2 as equivalent bidirectional shunt channels, and each
connector still maps pad 2 to D- and pad 3 to D+. It is, however, a direct
conflict between accepted decision authority and executable/source artifacts.
Resolve which per-instance map is intended, update the owning authority rather
than rationalizing both, regenerate, and renew the exact-artifact pin/topology
reviews. The present review cannot certify that routed changes preserved a
single unambiguous authored intent.

Evidence:

- ADR-0006 SHA-256:
  `882808e5d1c18647d766e97433dd42de8c6885a7863631bfa1b4e7d11d247a9b`.
- Staged TSX SHA-256:
  `595bc3d60fc781ae08d1de825c273f23db3a66a9261904425baf251da3176590`.
- Electrical-invariants SHA-256:
  `beb901b27866360189324789beb7a2972f9446cb3517e2b38bf015d29dcca038`.
- Exact board observations: `U_ESD1..4` each have pin 1 on their
  `P*_PORT_P` net, pin 2 on `P*_PORT_N`, and pin 3 on GND.

### P1-2 — no exact-current human connector-orientation approval

The current machine receipt is internally consistent and board-bound, but it
does not replace the required directional human review. It binds board
`4c69a2...` to orientation subject
`8a7f766c33855e7c9b325d1f792f928b0fd38197eb61d7f13969415eaea65f97`.
The tracked human approval instead names subject
`43a74ee2ddf76192c25f8e51529cdcbc9aad010cefd2362d2d4bf2945d7d553d`
and different image hashes. Therefore it is not exact-current approval.

I do **not** approve connector mouth direction, mounting side, keying, cable
approach, or J_PWR operator polarity in this review. Obtain user/human approval
of every current staged directional view and bind it to the current subject.

Evidence:

- Current machine receipt SHA-256:
  `675264bcfd6272c83d2fe2a300777bd7486143ae06aaf71277282e837cc902c9`.
- Current human-instruction document SHA-256:
  `08204a4ae8d4903e354880b083e0385b95d240dede8ef21c6c2a4c7437e8fa4b`.
- Tracked prior approval SHA-256:
  `84e0858fff5f5acc2f22fece6dfdcc9d0a5c7b7cc9a11f2df3c83e453ce29a62`.

### P1-3 — fresh-pin datasheet authority/dossier generation is incomplete

The mandatory pre-seal protocol requires a dossier generated from the exact
board plus a local PDF selected by the SHA-256 declared in each `part.yaml`.
That battery is not reproducible over the exact staged BOM:

- `TPS259474LRPWR/part.yaml` declares neither a datasheet SHA-256 nor a local
  PDF; `PESD2USB3UX-TR/part.yaml` likewise has no SHA-selected local PDF.
- Exact BOM MPNs `MCP2221A-I/SL`, `MCP23017T-E/SS`, and
  `74LVC08APW,118` do not directly resolve to their filesystem-safe dossier
  directory names in `pin_audit.py`.
- The staged policy audit independently reports `S-VER FAIL` for weak/missing
  figure citations on `2N7002K-7` and `PESD2USB3UX-TR`.

Manual comparison found the board pin functions coherent, and P-PINMAP passes
22 multi-pin references / 265 declared physical identities. That internal
consistency does not substitute for the protocol's world-facing,
digest-selected authority. Repair the authority/path mapping, generate the
complete dossiers against this exact board, and renew the fresh review.

Evidence: deterministic SHA-256 over the sorted `sha256sum` output for every
file below `02_parts/` is
`c1700a2ae76c61ec481b6ce9676a9e41613f20429ad437941bcb16b28c020899`.

## Node-for-node and routed-preservation evidence

Independent read-only extraction produced:

| Check | Result |
|---|---:|
| Staged netlist nodes | 508 |
| Staged PCB nodes | 508 |
| Staged netlist nets | 105 |
| Staged PCB nets | 105 |
| Missing / extra / mismatched node assignments | 0 / 0 / 0 |
| P-PINMAP | PASS, 265/265 declared identities across 22 multi-pin refs |
| E-INV | PASS, 82/82 invariants |
| E-ADR | PASS, 4/4 ADRs cited (citation coverage only) |
| DRC | 0 violations / 0 unconnected / 0 schematic-parity |
| ERC | 0 errors; 768 warnings as recorded by the staged policy audit |

The raw staged netlist SHA-256
`0d3fbddb082f4e1772205914cc65cbb9c8241c96a6e5152c5e32c68bb4e53087`
and TSX SHA-256
`595bc3d60fc781ae08d1de825c273f23db3a66a9261904425baf251da3176590`
are exactly the identities cited by the accepted pre-route pin witness. Thus
routing changed board geometry/copper but did not change the source netlist or
authoring TSX. The exact staged board also compares 508/508 node-for-node with
the live routed board in the staged parity evidence.

## Pin/function review

### USB upstream, hub, and management path

- `J_UP`: 1=`USB_UP_VBUS`, 2=`UP_HUB_N`/D-, 3=`UP_HUB_P`/D+,
  4=GND, fused shell pad 5=GND. Upstream VBUS reaches only the
  100k/100k `HUB_VBUS_SENSE` divider; it has no connection to
  `P5V_RAW`, `P5V_FUSED`, or `P5V_PROTECTED`.
- `U_HUB`: upstream DM/DP pins 58/59 remain N/P. Physical downstream port 1
  pins 1/2 carry `MGMT_P`/`MGMT_N`; `PRT_SWP1` pin 51 is strapped high,
  intentionally restoring logical D+/D-. `U_CTRL` pins 13/12 are D+/D- on
  those same nets. External hub ports 2..5 retain normal DM=N, DP=P and
  `PRT_SWP2..5` low.
- `U_PWR_CTRL` is associated only with hub `PRTPWR1`/`OCS1_N` and generates
  `VBUS_CTRL`, which powers `U_CTRL` and `U_EXP`. External ports 1..4 are
  associated respectively with physical hub ports 2..5, including matching
  PRTPWR and OCS nets.
- Ports 6 and 7 have both D-/D+ disable straps high. Their PRTPWR and OCS pins
  are intentionally NC with no routed copper. `NON_REM[1:0]=01`,
  `CFG_SEL[2:0]=000`, GANG=0, BOOST=00, and TEST is NC as documented.

### External data and power paths

For each external port 1..4:

- USB-A pin map is 1=switched VBUS, 2=D-, 3=D+, 4=GND, fused shell
  pad 5=GND.
- FSUSB42 D+ uses the complete symmetric 6-to-4 path and D- uses 7-to-3;
  SEL pin 2 is grounded. Unused throw pins 8/9 are explicit NCs and carry no
  track, via, or zone copper.
- TPS2557 pins 2/3 are `P5V_PROTECTED`, pins 6/7 are the matching switched
  VBUS, pin 4 is the matching active-high `PWR_EN`, pin 8 is the matching
  active-low OCS fault, pin 5 has the exact 165k current-limit network, and
  pin 1 plus exposed pad 9 are GND.
- `PWR_EN = HUB_PRTPWR AND PWR_CMD`; `DATA_OK = PWR_EN AND DATA_CMD`.
  The DATA_OK-driven 2N7002 has G/S/D=1/2/3 on DATA_OK/GND/OE. A 10k OE
  pull-up therefore disconnects data when the transistor is off.

### Safe states and NC census

- All eight MCP23017 commands have external 10k pull-downs. All four PWR_EN
  and DATA_OK nodes also have 10k pull-downs. All four FSUSB42 OE nodes have
  10k pull-ups. Reset, unpowered management, and default-input expander states
  therefore resolve to VBUS off and data disconnected.
- `U_EXP` address pins 15/16/17 are GND, RESET_N is pulled to VBUS_CTRL,
  SCL/SDA share 4.7k pull-ups to VBUS_CTRL, and its true NC pins 11/14 are
  unconnected. Unused GPB and interrupt pins are also explicit NCs.
- `U_CTRL` VDD is VBUS_CTRL, VUSB has its dedicated 330nF capacitor, and
  unused GPIO/UART pins are explicit NCs.
- Across the exact board, 36 intentional unconnected pins on 8 references are
  represented as explicit unconnected nets; every one has zero routed copper.
  No NC pin was found tied to a functional net.

### Power/control support pins

- Input path is `J_PWR.1=P5V_RAW` -> fused holder -> `P5V_FUSED` ->
  TPS259474L pins 5/6 -> `P5V_PROTECTED`; `J_PWR.2=GND`. TPS259474L PG pin 3
  is intentionally NC, PGTH pin 4 and GND pin 8 are grounded, and UVLO/OVLO,
  DVDT, ILM, and ITIMER pins reach their named support networks.
- AP63203Q pins 1..6 are respectively 3V3 sense, enabled from protected 5 V,
  protected VIN, GND, SW, and BST. The 24 MHz crystal maps signal pins 1/3 to
  XTAL1/XTAL2 and case pins 2/4 to GND. USB2517I exposed pad 65 and every
  TPS2557 exposed pad 9 are GND.

## Connector map boundary

Electrical contact numbering and nets were reviewed as above. Mechanical
mouth direction and usability were deliberately not approved. In particular,
the machine receipt reports the USB-A access axes toward the north edge and
J_UP toward the west edge, but only a current human directional-view approval
can close that claim. J_PWR is physically non-polarized hardware; its electrical
assignment is pin 1 positive and pin 2 ground, while the staged policy audit's
functional-silk failure prevents this review from asserting operator-visible
polarity.

## Exact subject and authority hashes

| Artifact | SHA-256 |
|---|---|
| staged PCB | `4c69a2dfbc7bd6c78fdfa4675316d42e5028249984b4bf455bdab4a733e7cd28` |
| staged schematic | `dccfa2feb7949225e7c789175cffab569fb4d7fa510cc194b872d6ae4c7d5f48` |
| staged TSX | `595bc3d60fc781ae08d1de825c273f23db3a66a9261904425baf251da3176590` |
| staged exported netlist | `0d3fbddb082f4e1772205914cc65cbb9c8241c96a6e5152c5e32c68bb4e53087` |
| staged design rules | `fd21d98c2fa11183ba914013bcf21c8732ec8fe7fee5ff0641ec2a97e7323802` |
| electrical invariants | `beb901b27866360189324789beb7a2972f9446cb3517e2b38bf015d29dcca038` |
| net/routing rules | `a89398ad61b2ad2d5864df2540356761612608f06f8479bf5ecf610edb64dea4` |
| power tree | `ae34fda05059d3e73ec18ae3ae0f302b616febdf2c7cf36c59d2b0397b049cd0` |
| brief | `ff472db8015c293c5ad004a8076697396cdf0befa858d016af9f73d6a2a13063` |
| architecture | `9dce11f55c04b7cadf5e396db224eab49131d643b8ddea7c4ddfd8eb811c03f7` |
| staged parity evidence | `c0691b9e39c9c0ec406c8e84bb8f71815752a6810dd4b0e88925be03ea1fbac7` |
| staged DRC evidence | `4d2a2fb227e2ae6197bee24fd446f01a8b7c46842a4f00b3a07acdc7a2b9973e` |
| staged ERC evidence | `c30238cfb358106a02a293b57d580395d165e0565c272ea5b6bcc5eb40a1b5d8` |

`source_commit` above identifies repository HEAD only. It is **not** release
provenance: the staged MANIFEST says `git_sha: pending release seal` and
`git_dirty: true`. Exact hashes, not the commit, bind this review subject.

## Other observed release blockers (outside this lens)

These do not change the node-level conclusions but independently enforce
`DO-NOT-ORDER`:

- Staged `policy_audit.md` reports `FAIL=6`, including S-VER, S-OCCL,
  P-SILK-FN, P-PLANE, R-POUR, and R-THERM.
- Staged `audit.txt` is `BLOCKED`: standalone staged-source model coverage is
  121/139 because 18 project-local STEP paths do not resolve from the archive.
- The MANIFEST is explicitly draft, has no source commit, carries no final
  sha256 census, and declares `git_dirty: true`.
- Final release review witnesses, uploader confirmation, final controlled-
  impedance selection, selective via-process confirmation, and first-article
  USB/power measurements remain absent or held by the draft order instructions.

## Required disposition before renewed review

1. Resolve P1-1 in the owning ADR/source/rules and regenerate from source.
2. Make the complete exact-BOM pin dossier battery reproducible with
   digest-selected local manufacturer PDFs, then renew the fresh-context pin
   review against the resulting exact staged board.
3. Obtain explicit human connector-direction approval for the current subject;
   this reviewer supplies no such approval.
4. Close the independently failing release gates and rebuild staging before
   requesting a `SOUND`/`ORDER` verdict.
