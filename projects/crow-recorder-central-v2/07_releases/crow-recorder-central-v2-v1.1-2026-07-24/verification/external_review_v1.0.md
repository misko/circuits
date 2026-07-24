subject: crow-recorder-central-v2 v1.0 (sealed 07_releases/crow-recorder-central-v2-v1.0-2026-07-23, seal 496b4bb)
date: 2026-07-24
reviewer: external (user-supplied LLM review; file/evidence-level — reviewer did not rerun KiCad or test hardware)
context-given: unknown (external) — reviewed released source, KiCad config/rules, custom footprints, drill output, BOM/CPL, DRC/ERC/parity evidence, twin reports, review provenance
verdict: DO-NOT-ORDER

Transmission path: received via user chat 2026-07-24, AFTER the v1.0 seal
(496b4bb, 2026-07-23 19:44 PT). Relayed by the orchestrator, who independently
VERIFIED every concrete claim against the sealed bytes before handing it to
this board lead: F1 (U1 EP holes emit as ComponentDrill T2; KiCad
capping/filling disabled), F2 (diff_pair_dimensions []; R-LEN N-A), and all of
F4 (M-REL N-A; manifest ERC 1409 vs policy report 1215; manifest BOM 48 lines
vs actual 49; bom_source path "07_releases/v1.0-2026-07-23" != sealed dir
name) — all confirmed TRUE. Root cause of F4: the seal predated the M-REL glob
fix (af30b54, 21:41 PT) by ~2h. Body below is VERBATIM.

---


Review verdict
HOLD — I would not approve fabrication, assembly, or a reorder from this exact v1.0 archive unchanged.
The release is substantially better than a typical first hardware drop: the source, fabrication outputs, and verification evidence are unusually complete, and the two previously discovered P0 net-merges appear to have been repaired and re-gated. However, I found two unresolved order-critical issues:

1. The XU316 exposed-pad thermal-hole construction does not unambiguously request a filled-and-capped via-in-pad process.
2. USB 2.0 High-Speed routing is neither constrained nor demonstrated to meet the required 90 ohm differential impedance.

After those are resolved, I would consider it suitable for a limited engineering first article. I would still not approve deployment where ordinary Ethernet cables or PoE equipment can reach the RJ45 ports.

1. High — U1's exposed-pad thermal holes are not safely defined for fabrication and assembly
The order instructions describe U1 as using 0.30/0.15 mm via-in-pad and require JLC's advanced small-via option, but they do not explicitly order epoxy filling, copper filling, capping, or plated-over via-in-pad processing.
More importantly, the footprint does not model the sixteen exposed-pad holes as ordinary vias. It defines them as sixteen duplicate-numbered through-hole pads numbered 129, each with a 0.15 mm drill, 0.30 mm outer diameter, and openings on all copper and mask layers. They sit directly beneath the exposed-pad paste pattern.
That distinction survives into the manufacturing data. The PTH file defines two separate 0.15 mm tools: T1 as ViaDrill and T2 as ComponentDrill. The sixteen U1 exposed-pad holes are emitted under T2, at the expected 4x4 coordinates around U1 — not under the via-drill tool. The KiCad board setup also has plugging, capping, and filling disabled.
As packaged, JLC may therefore interpret these as open plated component holes under a pasted thermal pad. That creates several risks: solder can wick into or through the holes during reflow; the exposed-pad joint can lose solder volume or develop excessive voiding; solder can protrude or collect on the reverse side; the assembler may reject the consigned XU316 placement or process the board differently from the design intent; the central ground/thermal joint is difficult to inspect after assembly.
JLC's own guidance distinguishes open/tented holes from epoxy- or copper-filled and capped via-in-pad construction, and says Gerber-based orders should include an annotated image or note and be confirmed in the production files.
Required closure — The next release should do one of the following: remodel these as actual thermal vias and explicitly order epoxy-filled or copper-filled, capped via-in-pad processing; or obtain written JLC engineering approval for the existing component-pad construction, including how the holes will be filled/capped and how the stencil will be handled. In either case, add an annotated U1 image and explicit fabrication note, inspect the generated production files before approval, and obtain X-ray or equivalent inspection on the first assembled board. This is especially important because U1 is an expensive, out-of-stock consigned component rather than a readily replaceable JLC stock part.

2. High — USB High-Speed impedance is explicitly waived but not demonstrated
The order README says impedance control is "not required" because the USB FS/HS pair is short. That is not sufficient evidence for USB 2.0 High-Speed operation.
The final source connects the XU316 USB PHY to the USB-C receptacle through USB_DP and USB_DM, with the ESD device attached to the same nets. But the released KiCad configuration contains: no defined differential-pair dimensions; no USB-specific netclass or pattern assignment; no USB-specific width, gap, skew, or reference-plane rule; no impedance tuning profile; no declared timing-critical nets — the policy audit records R-LEN as not applicable.
XMOS's XU316 routing guidance requires the USB D+/D- traces to be coupled and impedance-controlled, identifies 90 ohm differential impedance, and gives a maximum pair skew target of 1 mm.
The existing route might happen to be acceptable because it is short, but that cannot be established without the actual six-layer stackup and geometry. A short impedance discontinuity is less harmful than a long one; it is not automatically harmless. Possible symptoms include host- or cable-dependent enumeration, fallback behavior, intermittent operation, reduced eye margin, and excess emissions.
Required closure — Before release approval: 1. Obtain the exact JLC six-layer stackup for the selected fabrication option. 2. Calculate or field-solve the D+/D- width and spacing for 90 ohm differential impedance. 3. Add a USB differential-pair netclass and enforce width, gap, skew, coupling, and uninterrupted reference-plane requirements. 4. Regenerate DRC evidence showing those rules are active. 5. Either order controlled impedance or document a stackup-specific calculation and validate a first article with at least a robust High-Speed USB host/cable matrix; an eye/compliance measurement is preferable.

3. High for deployment — the RJ45 interface is electrically hazardous by design
This risk is disclosed very clearly, which is a strength of the release rather than a documentation failure. All eight RJ45 connectors carry custom 5 V audio and beeper wiring, not Ethernet. The release states that a Mode-B PoE source can place approximately 48 V through a port PTC onto the shared 5 V rail, exceeding the buck converters' 6.5 V absolute maximum and the ratings of the other 5 V circuitry. It also states there is no per-port overvoltage protection and that the mitigations are administrative — silkscreen warnings, custom cables, and a closed installation.
The beeper conductors also lack per-port fusing. A short on a beeper leg can open the common 2 A input fuse and take down the entire recorder.
My deployment judgment is therefore: Controlled engineering bench, owner-built cables, restricted physical access: conditionally acceptable after the two order blockers above are closed. Shared lab, field installation, equipment rack, classroom, venue, or any location where ordinary patch cables are present: no-go. Product or unattended deployment: no-go without connector error-proofing and electrical protection.
The durable fix is a keyed connector that cannot accept Ethernet patch cables. If RJ45 must remain, the next revision needs rail-side overvoltage protection, fault isolation, and beeper-bus protection — not only silkscreen warnings.

4. Medium — the independent review did not clearly cover the exact final sealed bytes
The release's review history is candid but weaker than the manifest wording suggests.
The first integrated review was a DO-NOT-ORDER review that found the P5VA_4/AUDIO4M net merge. Its original report was lost when the review session ended, and the archived document is explicitly a reconstruction from contemporaneous records rather than the reviewer's verbatim report.
The later "fresh lens" reviewed a staging archive. That session exhausted its context before producing a formal report, and the archive preserves its final message and session summary. Crucially, its findings still describe CL1/CL2 as 22 pF and Cout_U10 as 1 uF — values that were changed after the review and before the final seal. The disposition ledger shows that those two values were subsequently corrected and the machine gates rerun.
I therefore infer that the final component-value changes received machine re-verification but not a new, independent, zero-context integrated review of the exact final release bytes.
Several smaller inconsistencies support that conclusion: The archived policy report still says M-REL: N-A — no releases yet and says its BOM check targeted 06_build/fab/bom.csv, not the sealed release BOM. The manifest says ERC had 1,409 baselined warnings, while the archived policy report says 1,215. The manifest describes a 48-line BOM-source check, while the stock report says the BOM has 49 lines. The BOM-source evidence names a shortened release path that does not match the sealed directory's actual name.
None of these proves an electrical error, but they prevent the evidence bundle from being a clean, snapshot-consistent attestation.
Required closure — Create a superseding immutable release, such as v1.0.1, and run the full release checks against the staged directory itself: archive-relative BOM and CPL checks; manifest hash verification; release-provenance checks; exact warning-count capture; one independent integrated review against the final SHA; preservation of the reviewer's original output, not a reconstruction.

5. Medium — this is not yet a blind-upload, turnkey JLC assembly package
The twin report contains rotation-database suggestions for Q1, U2, U3, Q2, U7, U8, U9, U5, and D_USB. The README therefore instructs the operator to verify every diode, SOT, and TSSOP orientation in JLC's order preview rather than trust the files without review.
U1 and all eight RJ45 connectors require consignment or manual placement, and the debug and injection headers are also manually installed. The stock report ends in FAIL because U1 and the RJ45 placeholder have zero stock and two lines remain uncoded, although the README treats those as intentional manual or consignment lines.
That makes the package orderable only with a skilled human-controlled workflow. It should not be represented operationally as "upload three files and pay."
Before assembly approval, archive: annotated screenshots of the approved JLC placement preview; a pin-1 and polarity checklist for every suggested rotation; the exact U1 consignment MPN and lot; confirmation that J3-J10 are absent from automated placement; the approved U1 exposed-pad fabrication process; the final supplier and MPN for every manually sourced line.

6. Medium — the release is pre-bring-up, not production-qualified
The README describes rail checks, USB enumeration, and eight-port power verification as a "first-power ritual" to perform when boards arrive. I did not find archived first-article measurements proving: startup sequencing and reset timing across 3.3 V, 0.9 V, 1.8 V, and 3.3 VA; USB High-Speed eye margin or stress enumeration; eight-channel simultaneous recording; shared-clock and inter-ADC synchronization; ADC noise, crosstalk, or channel matching; operation over intended Cat5e cable lengths; thermal behavior of U1 and the power converters; fault recovery after a port short.
The release should therefore be treated as a first-article manufacturing package, not a production validation package. Fabricate the minimum practical quantity, fully characterize at least one board, and preserve the measurements before authorizing further units.

What looks solid
Final DRC reports no violations, no unconnected items, and no schematic-parity discrepancies. The dedicated port-net gate reports all 115 expected labels surviving and all eight RJ45 ports matching the intended pin map; all four component representations agree at 194 components. The two severe converter/net-binding defects — P5VA_4 merged with AUDIO4M and MID2P merged with 5 V — are documented, repaired, and covered by a permanent regression gate. The final source contains the corrected 2.2 uF XC6227 output capacitor and 12 pF crystal capacitors. The custom RJ45 hazard is disclosed prominently rather than hidden. The CPL/twin workflow accounts for all 172 placed references with no missing modeled bodies. The review and disposition records preserve failed checks and accepted risks instead of presenting an artificially perfect history.

Minimum approval gate
Before fabrication approval or any reorder, I would require all five of these: 1. Written U1 fabrication closure: filled-and-capped exposed-pad construction, annotated order note, and production-file confirmation. 2. USB SI closure: actual JLC stackup, 90 ohm calculation, USB diff-pair rules, and regenerated DRC evidence. 3. Exact-byte release review: a new immutable archive with internally consistent manifest, counts, paths, and an independent review of the final SHA. 4. Assembly closure: approved JLC orientation preview and documented consignment/manual-placement plan. 5. First-article validation: rail/reset scope captures, USB HS testing, eight-channel audio and synchronization testing, noise/crosstalk measurements, and inspection of the U1 exposed-pad joint.
Final approval status: HOLD for the current archive; conditional engineering-prototype approval after items 1-4; production approval only after item 5 and resolution of the RJ45/PoE architecture.
I reviewed the released source, KiCad configuration and rules, custom footprints, drill output, BOM/CPL, DRC/ERC/parity evidence, twin reports, and review provenance. I did not independently rerun KiCad or electrically test assembled hardware, so this is a file- and evidence-level review rather than physical qualification.
