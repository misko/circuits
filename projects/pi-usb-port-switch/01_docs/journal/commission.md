# Commission journal

## 2026-08-14 21:30 — start
- did: scaffolded a new project from the pcb-design skill's canonical templates and recorded the user prompt verbatim.
- result: MEASURED prompt sha256 is `2a83e1ad13bd5a004709e4315fe4a609d37e2d6371a84c065b3f6b7aa74f1c59`; all nine numbered stage directories and their contracts exist.
- next: resolve design-changing USB, connector, power, and safe-state questions before architecture.

## 2026-08-14 21:30 — iterate 1
- did: compared the commission identity with the existing `programmable-usb2-hub` project without importing its design.
- result: MEASURED that the existing project is a self-powered 12-24 V seven-port USB hub with onboard MCU and firmware, while this commission requests a four-channel Pi-GPIO inline pass-through; it is not a valid project continuation.
- next: wait for Q1-Q4 and keep the source configuration fail-closed.

## 2026-08-14 21:51 — iterate 2
- did: recorded D3, translated it into a USB 3 Gen 1 target with USB 2 fallback, external 5 V, Pi 4/5 compatibility, and fail-safe interlock; began official-source D-SPEC research.
- result: MEASURED from Raspberry Pi product documentation that both supported hosts have two USB 3 and two USB 2 ports; official USB-IF drop/droop material uses 900 mA at 4.75 V for a USB 3.2 self-powered downstream port. Q5 remains open because D3 selected the source but not the current.
- next: obtain the per-port current, then close the external-input and protection envelope.

## 2026-08-14 22:27 — iterate 3
- did: converted the unanswered current into explicit conservative assumption A5, completed the D-SPEC tension table, and ran the commission sourcing spike for the three data/power switch classes plus USB 3 connectors.
- result: MEASURED a 0.9 A x4 continuous output contract, 5.0-5.25 V / >=5 A input envelope, three surfaced spec tensions, and stocked LCSC candidates for redriver, USB 2 switch, current-limited power switch, ESD and both connector classes on 2026-08-14.
- next: validate commission records and enter `02_parts/`; exact MPN, pin-map, footprint and JLC assembly evidence remain gated there.

## 2026-08-14 22:29 — iterate 4
- did: ran the machine D-SPEC/E-PATH requirements gate on the newly locked measurement boundary.
- result: MEASURED 0/1 on the first run because `downstream_usb_a_mated_test_plug` was more specific than the schema vocabulary; corrected it to the permitted `mated_test_plug` while retaining the exact downstream USB-A boundary in `boundary_evidence` and BRIEF A5.
- next: rerun the gate; no electrical requirement changed.

## 2026-08-14 22:30 — iterate 5
- did: reran D-SPEC/E-PATH after correcting the measurement-plane enum.
- result: MEASURED 0/1 because the schema also requires canonical included-element tokens; mapped the already-locked path to `protection_switch`, `pcb_copper_vias_joints`, and `mated_power_contacts`.
- next: rerun the gate; no path element was added or removed.

## 2026-08-14 22:31 — iterate 6
- did: reran D-SPEC/E-PATH after mapping included path elements.
- result: MEASURED 0/1 because excluded elements likewise require canonical `cable` and `appliance` tokens; mapped the external/downstream cables and device to those tokens while BRIEF A5 retains the exact boundary wording.
- next: rerun the gate.

## 2026-08-14 22:32 — iterate 7
- did: reran D-SPEC/E-PATH with canonical boundary tokens.
- result: MEASURED 0/1 because the four claimed output rails were not yet mirrored into `power_tree.yaml`; authored four identical 5.0-5.25 V / 0.9 A rail envelopes with a conservative 200 mOhm delivery-path allocation.
- next: rerun D-SPEC/E-PATH; replace each budgeted maximum with selected-part and layout evidence before schematic approval.

## 2026-08-14 22:34 — iterate 8
- did: reran D-SPEC/E-PATH and declared the cheapest plausible controlled-impedance fabrication tier.
- result: MEASURED D-SPEC/E-PATH PASS 1/1 for 4 x 0.9 A, 4 simultaneous, 4.75-5.25 V at the mated test plug; `jlc_4layer_standard` is now the cost ceiling and exact footprints still owe P-ESC evidence.
- next: close commission journal/learnings and enter the parts contract.

## 2026-08-14 22:35 — finish
- did: completed the commission fact-lock, mating declaration, spec-tension ADRs, timeboxed sourceability spike, requirements gate and fabrication-tier decision.
- result: MEASURED prompt hash matches `2a83e1ad13bd5a004709e4315fe4a609d37e2d6371a84c065b3f6b7aa74f1c59`; M-BEACON passes 1/1; D-SPEC/E-PATH passes 1/1; no firmware is authorized.
- next: enter `02_parts/` and verify exact orderable identities, datasheet digests, pin maps, footprints, sourceability and escape tiers.
