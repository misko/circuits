# pin_review — zero-context review (fable-medium, 2026-07-26)

> **SCOPE AND INDEPENDENCE.** Reviewer was given the release archive, the 02_parts
> dossiers, the netlist and the design docs, and was NOT part of the design session.
> Brief: find pin-level defects, not confirm the design. 122 components, 73 nets,
> all 372 connected pins walked; board pads cross-checked pad-by-pad against the
> netlist via pcbnew.
>
> **VERDICT: PASS, with one CONCERN and one documentation defect — both acted on.**
>
> * **CONCERN (U12):** as shipped, with R42 unpopulated, the USBLC6-2SC6 sits ~100-230 mV
>   above its 5.25 V V_RWM continuously. Below breakdown, so leakage not damage — but it
>   is operation above a datasheet rating on the released configuration, and no earlier
>   document said so directly. NOW STATED PLAINLY in ORDER_README at bench gate Q9.
>   The reviewer's recommendation (populate R42 by default, or a 6 V-V_RWM array next
>   spin) is a DESIGN DECISION for v-next: populating R42 would put it on the CPL and
>   change the fab payload, which this verification-completeness supersede must not do.
> * **DOC DEFECT (SW1):** the tsx comment at SW1 described the deleted eFuse-era
>   D6 / EN_C enable scheme as if current, contradicting the same file's own v1.2
>   header. Copper was never wrong (E-INV asserts both EN pins on ENKILL). FIXED in
>   03_tscircuit/src/usb_hub_3s_v2.tsx and the v1.1 revision note marked SUPERSEDED.
>
> Dated copy: `08_reviews/2026-07-26_v1.8_pin-review.md`.

--- VERBATIM REVIEWER REPORT ---

# Zero-context pin review — usb-hub-3s-v3, release v1.7-2026-07-26

Method: parsed all 73 nets / 122 components / 372 connected pins out of
`07_releases/v1.7-2026-07-26/source/usb_hub_3s_v2.net`, then cross-checked **every pad of every
footprint** in `usb_hub_3s_v2.kicad_pcb` (pcbnew) against the netlist: **0 pad/net mismatches**
(merged drain paddles and duplicate SH pads included). IC pinouts were verified against the cached
manufacturer PDFs in `02_parts/` (SNVS499I.pdf, SLVS931B.pdf, SLVSBY8D.pdf), not against the
part.yaml claims. Discrete/connector pinouts were verified against part.yaml only where no PDF is
cached (noted at the end).

**U2, U11 LM5116 (HTSSOP-20 PWP) — PASS.** All 21 pins checked against SNVS499I (Nov 2023) Figure
4-1 + Table 4-1, read directly from the cached PDF. Netlist pin order matches the datasheet
exactly for both instances: 1 VIN→VIN, 2 UVLO→UVLO_A/C (divider R6/R7 = R15/R16 = 49.9k/6.98k from
VIN, ≈9.65 V rising per the 5 µA pin pull-up — matches DETAIL_DESIGN sec.2), 3 RT/SYNC→RT_A/C
(12.4k to GND), 4 EN→ENKILL (datasheet: >3.3 V required, abs max 100 V — 9–12.6 V pull-up via
R8/R17 100k is legal), 5 RAMP→RAMP_A/C (330 pF to GND, per DS "capacitor between this pin and
AGND"), 6 AGND→GND, 7 SS→SS_A/C (10 nF), 8 FB→FB_A/C, 9 COMP→COMP_A/C (R5/C4/C5 resp. R14/C19/C20
type-II network between COMP and FB per DS), 10 VOUT→5VA/5VC ("connect directly to the output
voltage" — buck-C senses LOCAL 5VC, pre-Q6, correct), 11 DEMB→GND (DS: "For start-up into a
pre-biased load, tie this pin to ground at the CSG connection" — grounded is the documented diode
emulation configuration), 12 CS→CSF_A/C via 0Ω R9/R18 from the shunt top CS_A/C (DS: "connect to
the top of the current sense resistor"), 13 CSG→CSGF_A/C via 0Ω R10/R19 from GND (DS: "bottom of
the sense resistor"), 14 PGND→GND, 15 LO→LO_A/C = Q3/Q5 gates, 16 VCC→VCC_A/C (1 µF C8/C23),
17 VCCX→GND (DS: "If VCCX is unused, VCCX must be connected to ground" — done), 18 HB→BOOT_A/C
(boot cap C7/C22 to SW; external boot diode D3/D4 anode=VCC cathode=HB — the LM5116 has no
internal boot diode, so its presence and direction were checked and are correct), 19 HO→HO_A/C =
Q2/Q4 gates, 20 SW→SW_A/C, EP(21)→GND (DS: "solder to ground plane"; verified GND in the board
file). FB dividers: buck-A R3/R4 3.92k/1.21k → 5.15 V; buck-C R12/R13 4.12k/1.21k → 5.35 V
(Vref 1.215 V per DS FB description). Snubbers R34+C53 / R35+C54 SW→GND. Nothing floats, nothing
is on the wrong rail.

**Q1 AON6403 (P-ch, PowerPAK SO-8, merged drain) — PASS.** Reverse-polarity input pass element.
Board pads verified: 1/2/3 (S) = VIN, 4 (G) = RPP_G, all five drain pads named "5" = VBAT_F.
PowerPAK SO-8 single convention (S=1-3, G=4, D=5-8+paddle) per the AON6403 sheet. P-FET body diode
anode=drain, cathode=source, so here it points **VBAT_F → VIN** (battery → load): conducts on
first pack contact, then R1 100k pulls RPP_G low to enhance the FET; with a reversed pack the
diode is reverse-biased and Vgs≈0, so the path is open — correct RPP orientation. D2 BZT52C12
gate clamp: K=VIN(source), A=RPP_G(gate) — clamps |Vgs| to 12 V < ±20 V rating. Correct.

**Q6 AON6403 — PASS.** USB-C reverse-block: S1-3=PMID, G=QG, D=5VC. Body diode points
**5VC → PMID** (anode=D=5VC, cathode=S=PMID), i.e. forward with the power flow and **blocking
PMID→5VC back-feed** when Q6 is off — the correct orientation for a reverse-block element whose
downstream (Pi via USB-C) may be externally powered. Gate chain: R30 100k PMID→QG holds it off;
Q7 pulls QG to GND when ENKILL is high (Vgs ≈ −5.35 V, no clamp needed, < ±20 V). Correct.

**Q2/Q4 AON6354 (N-ch high-side) — PASS.** D(5)=VIN, S(1-3)=SW_A/C, G(4)=HO_A/C. Body diode
S→D = SW→VIN, the normal intrinsic diode of a buck high-side switch. **Q3/Q5 AON6354 (N-ch
low-side) — PASS.** D(5)=SW_A/C, S(1-3)=CS_A/C (top of the 10 mΩ shunt RS1/RS2, whose pad 2 is
GND), G(4)=LO_A/C. Body diode S→D = shunt→SW: correct freewheel direction. Source-side shunt
placement matches LM5116 low-side sensing (SNVS499I CS/CSG pin table).

**Q7, Q8 BSS138 (SOT-23) — PASS.** Universal SOT-23 order G=1, S=2, D=3 (per every vendor sheet;
dossier gotcha explicitly asked pin review to confirm). Netlist: Q7 1=ENKILL, 2=GND, 3=QG;
Q8 1=ENKILL, 2=GND, 3=LEDPKK. Both are low-side switches with source on GND — correct. ENKILL
swings 0–12.6 V < ±20 V Vgs rating.

**D1 SMBJ15A (SMB) — PASS.** K(pad1)=VIN, A(pad2)=GND. Unidirectional TVS cathode to the
protected positive rail, and it sits on VIN *behind* Q1's reverse block (the part.yaml records why
it must not be on VBAT_F). KiCad D_SMB pad1=cathode convention confirmed by the dossier assert.

**D2 BZT52C12 (SOD-123) — PASS.** K(pad1)=VIN, A(pad2)=RPP_G — see Q1.

**D3, D4 1N4148WS (SOD-323) — PASS.** Boot diodes: A=VCC_A/C, K=BOOT_A/C. Current flows VCC→HB
to charge the boot cap; cathode on pad 1 at the HB node. Correct, and required (no internal boot
diode in the LM5116).

**D5 SMBJ6.0A (SMB) — PASS.** K(pad1)=VBUSC, A=GND. Unidirectional (C113976 — the v1.3 fix away
from the bidirectional C140903 is in effect in this netlist), 6.0 V standoff clears the 5.43 V
no-load VBUSC corner.

**C1, C2 KNM2 100 µF 35 V polymer (CP_Elec_6.3x7.7) — PASS.** POS(pad1)=VIN, NEG(pad2)=GND on
both. KiCad CP_Elec pad1=positive; the dossier carries a P-FACT assert with the v1.4
reversed-rotation post-mortem. Pin-level polarity is correct in netlist and board. (CPL rotation
is out of scope of this review but is the historical failure mode — keep the A-ROT gate on it.)

**D8 KT-0805Y, D9–D12 KT-0805G (LED 0805) — PASS.** All five: pad1=K, pad2=A per KiCad
LED_0805_2012Metric (cathode band at pad 1, per the tsx's verified note against
Device.kicad_sym). D8: K=LEDPKK (→Q8 drain→GND), A=LEDPK (←R37 6.98k←VIN) — lights only when
ENKILL is high. D9/D10/D11: K=GND, A=LEDVA1/2/3 ←R38/39/40← VBUSA1/2/3 (post-TPS2557, so a
tripped port goes dark — intended). D12: K=GND, A=LEDVC ←R41← VBUSC (post-Q6/F2). All anodes fed
through ballast, all cathodes to the low side. Correct.

**U3, U4, U5 TPS2557DRBR (VSON-8) — PASS.** Verified against SLVS931B p.3 pin drawing read from
the cached PDF: 1 GND, 2/3 IN, 4 EN (active-HIGH on the 2557 — the datasheet prints the 2556/2557
distinction on the same page), 5 ILIM, 6/7 OUT, 8 FAULT̄, PowerPAD→GND. Netlist: 1=GND,
2/3=5VA, 4=5VA (permanently enabled, active-high — correct polarity for this part), 5=ILIM1/2/3
(36.5k to GND; within the DS 20k–187k RILIM window), 6/7=VBUSA1/2/3, 8 floating (open-drain,
unused — legal), EP(9)=GND (verified in board). IN at 5.15 V is inside 2.5–6.5 V rec / 7 V abs.

**U6, U7 TPS2513ADBVR (SOT-23-6) — PASS.** Verified against SLVSBY8D p.4 (cached PDF): 1 DP1,
2 GND, 3 DP2, 4 DM2, 5 IN, 6 DM1. U6: DP1/DM1=DP_A1/DM_A1 (J2), DP2/DM2=DP_A2/DM_A2 (J3),
IN=5VA with C33/C34 100 nF at the pin (DS requirement). U7: DP1/DM1=DP_A3/DM_A3 (J4), DP2/DM2
floating — the unused-channel disposition recorded in the dossier; the sibling TPS2514 datasheet
page confirms those pins may float. D+/D− are not swapped anywhere: J pin3(DP)→DPx→DP1,
J pin2(DM)→DMx→DM1.

**U8, U9, U10, U12 USBLC6-2SC6 (SOT-23-6) — U8/U9/U10 PASS, U12 CONCERN.** Pinout 1 IO1, 2 GND,
3 IO2, 4 IO2, 5 VBUS, 6 IO1 (pass-through pairs 1–6 and 3–4, ST DS p.1). All four instances wire
D+ through IO1/IO1b, D− through IO2/IO2b, pin2 to GND, pin5 to the port VBUS — correct.
CONCERN on U12 only: its VBUS pin sits on VBUSC, which is regulated to 5.35 V nominal (netlist FB
divider 4.12k/1.21k; the tsx computes 5.352 V, no-load max 5.43 V) — above the USBLC6-2SC6 VRWM
of 5.25 V. Below breakdown (VBR ≈ 6 V) so the failure mode is elevated leakage, not damage, and
populating the R42 strap (drops the rail to 5.25 V) removes most of the exceedance — but as
released (R42 not placed) the part is operated ~100–180 mV above its rated standoff,
continuously. The project's own earlier dossier note ("usable on USB-A ports ONLY") shows the
rating was known. Recommend either populating R42 by default or swapping U12 for a 6 V-VRWM array
on the next spin.

**J1 XT60PW-M — PASS.** Pad1 = "−" per the AMASS drawing (dossier polarity fact) → GND; pad2 =
"+" → VBAT. Correct.

**J2, J3, J4 KH-AF90DIP-112 (USB-A receptacle, THT) — PASS.** USB-A standard contact order
1 VBUS, 2 D−, 3 D+, 4 GND (vendor drawing / Stewart SS-52100 template per dossier). Netlist:
1=VBUSAk, 2=DM_Ak, 3=DP_Ak, 4=GND, SH(×2)=GND on all three. Correct.

**J5 TYPE-C-31-M-12 (16-pin USB-C receptacle) — PASS.** Per the HRO pinout table (dossier,
cross-checked with the KiCad pad names in the board): A1/B1/A12/B12=GND, A4/B4/A9/B9=VBUSC,
A5=CC1, B5=CC2, A6/B6=DPC, A7/B7=DMC, A8/B8=SBU floating (unused sideband — legal), SH=GND.
CC pull-ups R28/R29 = 10k from CC1/CC2 to VBUSC: Rp of 10 kΩ to 4.75–5.5 V advertises a 3 A
source per the Type-C spec table — the right value for a Pi 4 at 5 V/3 A, and pulling from the
*protected* VBUSC means the advertisement dies if the protection chain opens. R27 = 0Ω DPC–DMC is
the BC1.2 DCP short. No pin swaps.

**F1 (Keystone 3568 fuse holder) — PASS.** 1=VBAT, 2=VBAT_F, non-polarized; only J1 and F1 touch
VBAT, only F1 and Q1 drain touch VBAT_F — the fuse and RPP FET really are in series with
everything. **F2 SMD2920 PPTC — PASS.** 1=PMID, 2=VBUSC, non-polarized, in the Q6→F2→VBUSC chain.

**SW1 SS12D07 (SPDT slide) — PASS.** 1 T1=GND, 2 COM=ENKILL (center pin = pole per the SS-12D07
drawing), 3 T2 open. Slide one way shorts ENKILL to GND (both bucks' EN low, Q7/Q8 off); other
way lets R8/R17 pull ENKILL to VIN. It switches ENABLE, not power, as designed. Note: the tsx
comment block above SW1 still describes a v1.2 "EN_C + D6 coupling diode" scheme that no longer
exists (both EN pins are on ENKILL; there is no D6 in the netlist) — the later usbc-group comment
records the revert. Stale comment only; the copper is self-consistent.

**RS1, RS2 10 mΩ 2512 — PASS.** 1=CS_A/C (LS-FET source side), 2=GND. Non-polarized; value per
dossier (UNI-ROYAL 2512 1 W, r: 10 mΩ). **L1, L2 MWSA1206S-6R8 — PASS.** 1=SW_A/C, 2=5VA/5VC,
non-polarized.

**Resistors R1–R42 — PASS.** Every one walked; all sit between the two nets their function
requires (dividers, pull-ups/downs, ballasts, Kelvin 0Ω links, snubbers — enumerated above with
their ICs). **R42 (160k 0402, DNP)** specifically: pin1=5VC, pin2=FB_C — exactly parallel with
R12 (5VC→FB_C). Populated it lowers Rtop to 4.017k → 5VC = 5.25 V; the tsx documents the margin
arithmetic and the BOM-but-not-CPL disposition. Netlist agrees with the intent.

**Capacitors C3–C54 — PASS.** All 46 walked: VIN bulk/HF (C9–C13, C24–C28), 5VA/5VC bulk
(C14–C17, C29–C32), per-controller RAMP/SS/BOOT/VCC/comp networks (C3–C8, C18–C23), TPS2557
in/out (C33–C43), VBUSC bulk (C49/C50), snubber (C53/C54). All decouplers pin2=GND; the only
polarized caps are C1/C2 (see above). No cap sits on a wrong rail.

## VERDICT: PASS

(with one CONCERN: U12 USBLC6-2SC6 VBUS pin at 5.35 V nominal VBUSC exceeds its 5.25 V VRWM while
R42 is unpopulated — leakage-only exceedance, but it is operation above a datasheet rating on the
released configuration; plus one stale tsx comment at SW1 describing the deleted D6/EN_C scheme.)

## Not verified / limits of this review

- **LM5116, TPS2557, TPS2513A pinouts: verified from cached manufacturer PDFs.** Everything else
  (AON6403/AON6354/BSS138 S-G-D order, XT60 polarity, KH-AF90DIP contact order, TYPE-C-31-M-12
  pad map, SMB/SOD/LED pad-1=cathode conventions, RS 10 mΩ value) was verified against the
  hand-written part.yaml dossiers + KiCad library conventions; no vendor PDF is cached in the
  repo for those, so an independent datasheet fetch was not possible from this environment. The
  dossiers record explicit "verified from drawing" provenance for each, and the conventions are
  the universal ones, but they are one step removed from the manufacturer document.
- Footprint *geometry* (pad positions vs the physical part) and CPL rotations were out of scope;
  pad *names/nets* were fully cross-checked board-vs-netlist (0 mismatches across all 122
  footprints).
- Layout-level Kelvin quality of CS/CSG routing and the AGND/PGND single-point tie are physical
  properties the netlist cannot prove.
