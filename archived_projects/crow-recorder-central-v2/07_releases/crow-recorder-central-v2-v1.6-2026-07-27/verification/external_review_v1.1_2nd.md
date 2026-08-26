subject: crow-recorder-central-v2 v1.1 (crow-recorder-central-v2-v1.1-2026-07-24, seal d9d5ae1, source b08f182)
date: 2026-07-24
reviewer: external (second external LLM full review, user-supplied; transmission path: user -> orchestrator -> board lead, received post-seal)
context-given: release-archive-only (file/evidence-level; reviewer did not run KiCad or test hardware)
verdict: DO-NOT-ORDER (reviewer wording: "HOLD for ordering the exact v1.1 archive"; conditional first-article defensible under written waiver; preferred disposition = v1.2 spin)

Body below VERBATIM (including the orchestrator provenance/verification note it arrived with).

---

# External review of crow-recorder-central-v2 v1.1 (user-supplied, received 2026-07-24)

NOTE (orchestrator): received AFTER the v1.1 seal (d9d5ae1, source b08f182).
File/evidence-level review; reviewer did not run KiCad or test hardware.
Orchestrator VERIFIED finding 1 against the sealed bytes: BOM ships exactly
C_c1..C_c8 (8x 100nF, C1525) with C_c1 on net 0V9; our own independent v1.1 pin
review measured 0V9 landing on 15 core-VDD pins {5,11,14,18,39,45,50,54,68,85,
95,104,105,106,113}; the reviewer's 8-core / 6-on-3V3 (C_d*) / 2-on-1V8 (C_e*)
breakdown matches the BOM groupings exactly. CONFIRMED: 8 local core bypass caps
for 15 core-VDD pins. The exact XMOS ">=12" threshold is to be confirmed from
the datasheet during the v1.2 fix. Findings 2-4 assessed correct but previously
known/dispositioned. Verbatim below.

---

Review verdict

HOLD for ordering the exact v1.1 archive as a release candidate.

The update genuinely closes the principal v1.0 findings: the XU316 thermal holes are now real filled-and-capped vias, the USB High-Speed pair is constrained and stackup-solved, the unsafe XU316 1.8 V-bank straps are corrected, and the release evidence is substantially more internally consistent. The sealed release points to source commit b08f182... and is sealed by d9d5ae....

However, I found one new hardware issue that I would correct before paying for boards:

The XU316 0.9 V core rail has only eight local 100 nF bypass capacitors, while XMOS specifies at least twelve.

I found no new net-merge, pin-map, or gross fabrication P0. With a documented engineering waiver, v1.1 could be used for a minimum-quantity, controlled-bench first article. My preferred disposition is a small v1.2 spin adding the missing bypass capacitors before fabrication.

1. High - XU316 core decoupling is below the manufacturer's minimum

The final v1.1 source creates exactly eight C_c1...C_c8 100 nF capacitors from N0V9 to ground. It separately provides six 100 nF capacitors for the 3.3 V I/O rail, two for the 1.8 V I/O rail, and one 10 uF bulk capacitor on each rail. Therefore, the I/O-bank decoupling count looks sensible, but the core VDD rail has only eight local high-frequency capacitors.

XMOS's XU316 package guidance calls for at least twelve 100 nF multilayer capacitors close to the VDD pins, together with bulk capacitance. The bulk 10 uF and the buck converter's remote output capacitors do not replace the high-frequency function of local 100 nF parts.

This is not detectable by ERC or DRC. In my judgment, it creates avoidable core-rail transient, jitter, EMI, startup, and high-load operating margin risk. The fact that the design is expected to run USB High-Speed and eight-channel audio makes following the processor vendor's bypass guidance particularly worthwhile.

Required correction: add at least four more 100 nF 0402 capacitors on 0V9, distributed around currently under-served XU316 VDD pins. Each should have a short connection to the pin or local core pour and a very short ground path into the EP/ground-via field. Then rerun DRC, parity, the thermal/PDN audit, and the final-byte review, and seal a superseding release.

A prototype-only waiver is possible, but it should explicitly record the deviation and make 0.9 V ripple, droop, boot-cycle, USB-load, and thermal testing mandatory. Given that the fix is small before fabrication and difficult after assembly, I would spin the board instead.

2. Medium - the required 1.8 V-before-core sequence is plausible, but not explicitly interlocked

The current topology powers U9, the 1.8 V LDO, directly from 3.3 V. U8, the 0.9 V core buck, is enabled by PG_3V3. Thus the intended behavior is that 1.8 V begins rising as soon as 3.3 V appears, while 0.9 V waits until the 3.3 V rail asserts power-good.

That will probably produce the correct ordering, but the circuit does not actually sense that 1.8 V is valid before enabling 0.9 V. XMOS requires the 1.8 V VDDIOB18 domain not to be the last XU316 supply to rise; XMOS's multichannel reference design deliberately establishes 3.3 V and 1.8 V before starting the core supply.

The reset pull-up being referenced to 1.8 V is helpful because reset remains low while 1.8 V is absent, but reset does not itself enforce the supply ordering.

The release already makes rail/reset oscilloscope captures a first-article gate. That requirement should cover:

cold, room-temperature, and warm starts;
fast disconnect/reconnect;
slow 5 V input ramps;
brief brownouts;
repeated power cycling;
both lightly and heavily loaded USB conditions.

The pass condition should explicitly state that 1.8 V is valid before the 0.9 V core rail reaches its valid threshold, and that reset remains asserted until all required I/O rails are stable.

A failure at any corner requires an interlock-such as gating U8 from a 1.8 V supervisor or combined rail-good signal-rather than merely increasing a delay empirically.

3. Medium - USB impedance is fixed, but the ESD device remains on a branch stub

The prior USB blocker is convincingly closed. The release now specifies the exact JLC06161H-3313 stackup and calculates a 0.125 mm trace width with a 0.150 mm edge gap at approximately 89.7-90.5 ohms differential. The routed pair is approximately 23.6 mm long with 0.110 mm skew, and the KiCad USB differential-pair rules are active.

The remaining concern is the recorded approximately 7 mm branch from the main pair to D_USB. The release itself carries this as a nonblocking P2. XMOS's USB layout guidance recommends avoiding stubs on the High-Speed pair.

For a limited engineering build, the mandatory multi-host, multi-cable High-Speed test matrix is a reasonable signal-integrity screen. It is not an ESD qualification, however. Before production or field use, I would:

place the protector directly in-line with D+/D- at the connector;
minimize connector-to-protector distance and the protector's ground inductance;
conduct contact and air-discharge ESD testing while monitoring resets, USB disconnects, data corruption, and permanent damage.

Also note that the order deliberately does not buy measured controlled impedance. The geometry is calculated rather than coupon- or TDR-verified, so an eye measurement or production impedance coupon remains preferable before a larger batch. The README appropriately acknowledges that distinction.

4. High for deployment - the custom RJ45 and overvoltage risks remain

The eight RJ45 ports are still custom 5 V audio/power connectors, not Ethernet. The release correctly warns that a PoE source can place roughly 48 V through a port PTC onto circuitry designed around 5 V, and that there is no rail-side per-port overvoltage shutdown in this revision. The beeper conductors also remain unfused per port, so a beeper-cable short can take down the whole recorder through the main fuse.

The DC-input protection also remains an accepted-risk rather than robust overvoltage protection. The design brief explicitly notes that the AP61102 path has very little voltage margin above the regulated 5 V input. The AP61102's specified input range ends at 5.5 V, while the selected SMAJ5.0A does not begin breakdown until roughly 6.4-7.0 V and has a rated clamp around 9.2 V. Therefore, the TVS cannot hold the buck input within its normal operating range during a substantial surge; the design depends on the correct regulated brick and a fuse/crowbar-style response to severe wrong-adapter faults.

My deployment classification remains:

Environment / Status
Owner-controlled engineering bench, custom cables, no Ethernet/PoE access - Conditional
Shared laboratory or equipment rack containing ordinary patch cables - No-go
Unattended, public, outdoor field, commercial, or product deployment - No-go
Larger production batch - No-go until connector error-proofing and electrical OVP are added

A keyed connector remains the strongest solution. If RJ45 is retained, the next revision needs active rail-side overvoltage disconnection and beeper-bus protection, not only warnings and PTCs.

Previous v1.0 blockers: closure assessment

U1 exposed-pad construction - closed at the file level

The PTH output now classifies the 0.15 mm holes as ViaDrill, with component drills starting under separate tools. The sixteen U1 coordinates occur under the via tool, rather than being emitted as exposed-pad component holes.

The board source also enables filling and capping, and the order instructions explicitly require epoxy-filled, copper-capped/Type-VII-style processing, production-file confirmation, and first-article X-ray inspection.

This is a strong correction. Actual closure still depends on JLC confirming the process before manufacture and the X-ray result after assembly.

USB 90 ohm constraint - closed for a prototype

The stackup, solver assumptions, width, gap, layer, route length, and skew are all documented. The active KiCad rules match the calculation, and the audit independently reports the expected geometry, no vias, and small pair skew.

Production approval still requires physical High-Speed validation because impedance is calculated rather than measured.

XU316 low-voltage bank straps - closed

The unsafe 3.3 V ties on the fixed 1.8 V I/O bank have been removed. The final source leaves the relevant mode pins unconnected as required, and the archived diff documents both the netlist change and the associated copper surgery.

Snapshot consistency and verification provenance - substantially closed

The v1.1 policy report now shows release provenance passing, the BOM check targets the sealed archive, the warning and BOM counts are consistent, and the final staged bytes received a fresh independent review with an ORDER verdict.

Final DRC includes errors, warnings, exclusions, refill, and schematic parity and reports no violations, no unconnected items, and no parity differences. The separate parity report gives zero discrepancies across 116 nets.

Manufacturing and bring-up conditions

This remains a skilled, human-controlled assembly:

U1 and the eight RJ45 connectors require consignment or manual sourcing/placement.
JLC's placement preview must be checked for all polarity and rotation-sensitive parts.
JLC must confirm the filled-and-capped U1 via process.
The first assembled U1 joint needs X-ray or equivalent inspection.
USB, rail sequencing, eight-channel recording, inter-ADC synchronization, noise, crosstalk, cable length, thermal behavior, and port-short recovery all remain first-article tests.

The stock report still marks the XU316 and RJ45 placeholder lines as zero-stock/consignment items, and the two headers remain uncoded manual parts.

Recommended disposition

Preferred: produce a v1.2 source commit adding four or more local 100 nF XU316 core capacitors, regenerate all outputs, rerun the release gates, and seal a new immutable archive. Keep the existing v1.1 directory unchanged.

Conditional alternative: order only the minimum engineering quantity from v1.1 under a written decoupling waiver. In that case, the following become blocking before any additional units:

Scope 0.9 V at U1 during repeated boot, sustained USB High-Speed traffic, and maximum audio processing load.
Prove 1.8 V precedes 0.9 V across startup corners.
Obtain JLC confirmation of the filled-and-capped U1 via construction and X-ray the assembled joint.
Pass the USB High-Speed host/cable matrix and perform ESD testing.
Demonstrate eight-channel capture, TDM synchronization, noise/crosstalk performance, cable-length operation, thermal margin, and fault recovery.
Restrict the hardware to a physically controlled, non-Ethernet environment.

The old v1.0 archive is now correctly marked DO NOT ORDER and explicitly identifies all four superseded defects.

Final status: v1.1 is a major improvement and closes the prior review, but the exact sealed archive remains on HOLD because its XU316 core bypass count is below XMOS's stated minimum. Conditional first-article fabrication is defensible; production approval is not.

This was a file- and evidence-level review of the sealed source, KiCad rules, drill outputs, BOM/CPL, audit reports, review records, and manufacturer documentation. I did not independently run KiCad's generators or physically test an assembled board.
