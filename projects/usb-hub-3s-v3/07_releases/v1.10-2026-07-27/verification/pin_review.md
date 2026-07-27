# pin_review — contract-named copy

> **PROVENANCE.** This is the CURRENT pin review for this board, shipped under the
name `07_releases/contracts.md` requires. It is a VERBATIM COPY of
`08_reviews/2026-07-27_v1.9_pin-review.md`, which remains in place — dated history
lives in `08_reviews/`, the contract name ships in the release, and the file is
COPIED rather than moved so the provenance survives in both places.
>
> **VERDICT: PASS-WITH-NOTES.** 0 P0, 1 P1, 8 P2. 122 components / 73 nets /
**372 pins, every one read and adjudicated**; PCB pads cross-checked pad-by-pad
against the netlist by an independently written comparator — **372/372 agree, 0
mismatches** (canon M1: checker and checked share no method).
>
> The single P1 (**PR-1**) is a defect in the REVIEW TOOL, not the board:
`pin_audit.py` resolves `02_parts/<MPN>/part.yaml`, and the LM5116's MPN contains
a `/`, so it silently produced an EMPTY dossier for U2 and U11 — the two
highest-consequence parts — and exited 0. The reviewer read SNVS499I directly
instead. Reported upstream; `skills/` is owned by concurrent agents.
>
> Four P2s were shipped-document defects and are **FIXED in this release**
(PR-4 DEMB derivation, PR-5 the USBLC6 pass-through claim, PR-8 a datasheet
citation belonging to a different device variant, and PR-6/PR-9 verified as
already human-gated). Per-finding disposition: `08_reviews/DISPOSITIONS.md`.

---

subject: usb-hub-3s-v3 release v1.9-2026-07-27 (board `usb_hub_3s_v2`), repo HEAD d0265ba
date: 2026-07-27
reviewer: pin-review (zero-context agent, Opus 5)
context-given: zero-context
verdict: PASS-WITH-NOTES

# Zero-context pin review — usb-hub-3s-v3 v1.9-2026-07-27

## Provenance — what was read, and what was deliberately NOT read

**Read (the only inputs used):**

| artifact | path |
|---|---|
| exported netlist (primary subject) | `07_releases/v1.9-2026-07-27/source/usb_hub_3s_v2.net` (sha256 `0ebdba19…`) |
| board, for the independent cross-check | `07_releases/v1.9-2026-07-27/source/usb_hub_3s_v2.kicad_pcb` |
| schematic, for DNP flags only | `07_releases/v1.9-2026-07-27/source/usb_hub_3s_v2.kicad_sch` |
| authoring source, for design intent on R42 | `07_releases/v1.9-2026-07-27/source/usb_hub_3s_v2.tsx` |
| fab BOM / CPL | `07_releases/v1.9-2026-07-27/fab/bom.csv`, `fab/cpl.csv` |
| part dossiers | `pin_audit.py` run over the release board + `fab/bom.csv` + `02_parts` |
| part pin tables + gotchas | `projects/usb-hub-3s-v3/02_parts/*/part.yaml` |
| design math | `projects/usb-hub-3s-v3/01_docs/DETAIL_DESIGN.md` |
| protocol | `skills/kicad-pcb/references/pin-review-protocol.md` |
| **vendor datasheets, read directly** | `02_parts/LM5116MHX-NOPB/SNVS499I.pdf` (Fig 4-1 pin config p.3, Table 4-1 pin functions pp.3-4, §5.1 abs-max, §6.3.2 Enable, §6.3.x diode emulation, Fig 7-1 + Table 7-1 pp.21-22, §7.2.2.2-7.2.2.4); `02_parts/TPS2557DRBR/SLVS931B.pdf` (§6 DRB pin config + pin functions, §7.1 abs-max); `02_parts/TPS2513ADBVR/SLVSBY8D.pdf` (§5 device options, §6 DBV pin config + pin functions); `02_parts/USBLC6-2SC6/USBLC6-2SC6_ST.pdf` (Fig 1 functional diagram, Table 1 abs ratings); `02_parts/AON6403/AON6403_rev.pdf` (DFN5X6 top view p.1); `02_parts/TYPE-C-31-M-12A/TYPE-C-31-M-12A_LCSC.pdf` (recommended PCB layout + pin/signal table, rendered at 130 dpi); `02_parts/KH-AF90DIP-112/KH-AF90DIP-112.pdf` (PCB pattern, rendered at 130 dpi) |

**NOT read** (independence, per the protocol): no journal, no `01_docs/learnings/`,
no `STATUS.md`, no `CHANGELOG.md`, no other `08_reviews/` file, no
`DISPOSITIONS.md`, no `07_releases/*/verification/` report. The scratchpad
contained artifacts from earlier sessions; none were opened.

## Coverage — the number, not a claim

| scope | count |
|---|---|
| component references in the netlist | **122** |
| **distinct component pins in the netlist, ALL of which were read and adjudicated** | **372** |
| — of those, in the part groups named in the brief (41 parts) | 210 |
| — of those, R/C passives (81 refs) | 162 |
| unconnected/no-connect pins, individually adjudicated | 8 |
| PCB pad ↔ netlist net assignments cross-checked pad-by-pad | **372 / 372 agree, 0 mismatches** |
| datasheet pin-configuration figures independently re-read | 6 (LM5116, TPS2557, TPS2513x, USBLC6-2, AON6403, TYPE-C-31-M-12A) + 1 PCB pattern (KH-AF90DIP-112) |

The PCB↔netlist cross-check was done with an independently written comparator
(pcbnew `Pads()` vs. an s-expression parse of the `.net`), i.e. checker and
checked do not share a method (canon M1). 7 PCB refs carry no netlist entry:
`FID1 FID2 FID3 H1 H2 H3 H4` — fiducials and mounting holes, expected.

## Per-part-group verdicts

| group | parts | pins checked | verdict | findings |
|---|---|---|---|---|
| **LM5116MHX/NOPB** buck controllers | U2, U11 | 42 (2 × 20 + EP) | PASS-WITH-NOTES | PR-4 (DEMB), PR-1 (dossier was empty for these two) |
| **TPS2557DRBR** USB-A switches | U3, U4, U5 | 27 (3 × 8 + EP) | PASS | — |
| **TPS2513ADBVR** DCP advertisers | U6, U7 | 12 | PASS-WITH-NOTES | PR-8 (U7 ch.2 float has no datasheet citation) |
| **USBLC6-2SC6** ESD arrays | U8, U9, U10, U12 | 24 | PASS-WITH-NOTES | PR-5 (pass-through collapsed to a net), PR-7 (U12 rail, already-recorded deviation) |
| **AON6403** P-FETs | Q1, Q6 | 10 | PASS | — |
| **AON6354** buck HS/LS FETs | Q2, Q3, Q4, Q5 | 20 | PASS | — |
| **BSS138** | Q7, Q8 | 6 | PASS | — |
| **Diodes / LEDs** | D1, D2, D3, D4, D5, D8–D12 | 20 | PASS | — |
| **Connectors** | J1, J2, J3, J4, J5 | 34 | PASS-WITH-NOTES | PR-9 (USB-A pin-1 side is inherited, not drawn) |
| **SW1, F1, F2, L1, L2, RS1, RS2** | 7 parts | 15 | PASS | — |
| **R/C passives** | 81 refs | 162 | PASS-WITH-NOTES | PR-6 (R42 BOM-without-CPL) |
| **whole netlist, pin-type audit** | — | 372 | FAIL (gate, not board) | PR-3 (every pin exported as `passive`) |

### Winding / mirror check (the failure this protocol exists for)

Every multi-pin part's pad geometry was compared against the datasheet's own
top-view pin figure. **No mirror anywhere.**

- **LM5116 U2/U11** — SNVS499I Fig 4-1 (PWP 20-pin HTSSOP, top view): 1 VIN
  top-left descending to 10 VOUT bottom-left, 11 DEMB bottom-right ascending to
  20 SW top-right. Board: pads 1-10 at x = −2.86 mm, y −2.92 → +2.92; pads 11-20
  at x = +2.86 mm, y +2.92 → −2.92. Exact, CCW top view. EP pad 21 present.
- **TPS2557 U3/U4/U5** — SLVS931B §6 (DRB, top view): 1 GND / 2 IN / 3 IN / 4 EN
  left, 8 FAULT / 7 OUT / 6 OUT / 5 ILIM right. Board matches pad-for-pad.
- **TPS2513A U6/U7** — SLVSBY8D §6 (DBV top view): 1 DP1 / 2 GND / 3 DP2 left;
  4 DM2 / 5 IN / 6 DM1 right. Board matches.
- **USBLC6-2 U8/U9/U10/U12** — ST doc 11265 Rev 5 Fig 1 (top view): 1 I/O1 /
  2 GND / 3 I/O2 left; 4 I/O2 / 5 VBUS / 6 I/O1 right. Board matches.
- **AON6403 / AON6354 Q1–Q6** — AON6403 DS p.1 DFN5X6 top view: S1/S2/S3 down
  the left with the pin-1 dot at top-left, G4 bottom-left, D 8/7/6/5 right.
  Board: pads 1,2,3 (S) at x = −2.67, pad 4 (G) at x = −2.67 y = +1.91, merged
  drain paddle + 4 lead pads at x = +0.69/+2.79. Exact.
- **J5 TYPE-C-31-M-12A** — the HRO drawing's *"RECOMMEND P.C.B LAYOUT
  (COMPONENT SIDE)"* labels the tails left→right as
  `A1/B12 · A4/B9 · B8 · A5 · B7 · A6 · A7 · B6 · A8 · B5 · B4/A9 · B1/A12`.
  The footprint's pads in ascending local x are
  `A1+B12(−3.25) · A4+B9(−2.45) · B8(−1.75) · A5(−1.25) · B7(−0.75) · A6(−0.25) ·
  A7(+0.25) · B6(+0.75) · A8(+1.25) · B5(+1.75) · B4+A9(+2.45) · B1+A12(+3.25)`.
  Identical order, identical merged pairs. Not mirrored. (A mirror here would
  have been live: it would land both 10 kΩ Rp resistors on SBU1/SBU2 and leave
  CC1/CC2 unterminated.)

## Item-by-item answers to the brief's specific questions

### (a) Every LM5116 pin with a `part.yaml` gotcha

Pin table re-derived from SNVS499I Table 4-1 (pp.3-4), not from `part.yaml`,
then compared. `part.yaml` `pins:` is **correct in all 21 entries**.

| pin | DS function | U2 net | U11 net | adjudication |
|---|---|---|---|---|
| 1 | VIN (chip supply + VCC-reg input) | VIN | VIN | ✓ |
| 2 | UVLO | UVLO_A | UVLO_C | ✓ R6/R7 = R15/R16 = 49.9 k / 6.98 k. Re-derived independently with the DS's fixed 5 µA pull-up: `(V−1.215)/49.9k + 5µA = 1.215/6.98k` → **V_rise = 9.65 V**, matching `part.yaml`. Separate divider per buck, so a 256-cycle hiccup on one rail cannot pull the other's UVLO down. |
| 3 | RT/SYNC | RT_A | RT_C | ✓ R2 = R11 = 12.4 kΩ to GND, one resistor only — DS eq.(7) gives 12.5 kΩ for 250 kHz, TI's own Table 7-1 uses 12.4 kΩ. |
| 4 | EN | ENKILL | ENKILL | ✓ see (d). Not floating (DS §6.3.2: *"It must not be left floating"*). |
| 5 | RAMP | RAMP_A | RAMP_C | ✓ C3 = C18 = 330 pF to GND only. Re-derived: `C_RAMP = 5 µA/V × L / (A × R_S) = 5e−6 × 6.8e−6 / (10 × 0.010) = 340 pF` → 330 pF. |
| 6 | AGND | GND | GND | ✓ |
| 7 | SS | SS_A | SS_C | ✓ C6 = C21 = 10 nF to GND only (TI Table 7-1 C3 = 0.01 µF). |
| 8 | FB | FB_A | FB_C | ✓ divider node, not a rail. R3 3.92 k / R4 1.21 k → 5.151 V; R12 4.12 k / R13 1.21 k → 5.352 V. Both re-derived from DS eq.(24). |
| 9 | COMP | COMP_A | COMP_C | ✓ R5/R14 18 k in series with C4/C19 3.3 nF to FB, plus C5/C20 100 pF direct to FB — matches TI Table 7-1 (R10 18 k, C6 3300 pF, C5 100 pF). |
| 10 | VOUT (*"connect directly to the output voltage"*) | 5VA | 5VC | ✓ on the rail, not on the FB node. |
| 11 | DEMB | GND | GND | **see PR-4** |
| 12 | CS | CSF_A | CSF_C | ✓ via R9/R18 = 0 Ω Kelvin link to CS_A/CS_C = the LS-FET source. Matches TI Fig 7-1's R6 = 0 Ω. |
| 13 | CSG | CSGF_A | CSGF_C | ✓ via R10/R19 = 0 Ω Kelvin link to GND = the shunt's PGND end. Matches TI Fig 7-1's R7 = 0 Ω. Shunt RS1/RS2 = 10 mΩ 2512, sitting LS-source → PGND, identical to TI's R11 = 0.010 Ω. Re-derived DS eq.(11)/(12) with V_CS(TH) = 110 mV (the **VCCX = 0 V** column, which is this board's case) → R_S ≤ 11 mΩ, 10 mΩ chosen. Consistent. |
| 14 | PGND | GND | GND | ✓ |
| 15 | LO | LO_A | LO_C | ✓ fans out to **exactly one** gate (Q3.4 / Q5.4). |
| 16 | VCC | VCC_A | VCC_C | ✓ C8/C23 = 1 µF at the pin (DS §7.2.2.8 wants ≥ 0.47 µF), plus the boot-diode anode. |
| 17 | VCCX | GND | GND | ✓ **exactly what the DS demands**: *"If VCCX is unused, VCCX must be connected to ground."* And it is VCCX = 0 that makes V_CS(TH) = 110 mV rather than 122 mV — the shunt sizing above depends on this being 0 and it is. |
| 18 | HB | BOOT_A | BOOT_C | ✓ D3/D4 1N4148WS cathode(pad 1) on HB, anode(pad 2) on VCC — the external VCC→HB diode the LM5116 does not contain. C7/C22 = 1 µF HB→SW (DS §7.2.2.9 wants ≥ 0.1 µF). |
| 19 | HO | HO_A | HO_C | ✓ fans out to **exactly one** gate (Q2.4 / Q4.4). |
| 20 | SW | SW_A | SW_C | ✓ HS source + LS drain + L1/L2 pin 1 + boot-cap low side + snubber. |
| 21 | EP | GND | GND | ✓ *"Exposed pad. Solder to ground plane."* |

Pairwise symmetry (protocol check 4): **U2 and U11 map identically, pin for pin,
onto their A/C equivalents. Zero structural divergence.**

### (b) The v1.6 status-LED cell — R37/D8/Q8 and R38-R41/D9-D12

KiCad `Device:LED` pin 1 = **K** (cathode); `LED_SMD:LED_0805_2012Metric` puts
pad 1 at x = −0.9375 with both the F.Fab chamfer and the F.SilkS cathode band at
that end. Both `02_parts/KT-0805Y/part.yaml` (D8) and `KT-0805G/part.yaml`
(D9-D12) carry a `pad1_net_polarity: negative` assert on the same basis.

| LED | pad 1 (K) net | pad 2 (A) net | ballast | verdict |
|---|---|---|---|---|
| D8 (amber, pack) | LEDPKK → **Q8 drain** | LEDPK → **R37 6.98 k → VIN** | anode side | ✓ ballast on the positive side, cathode on the FET-pulled low side |
| D9 | GND | LEDVA1 → **R38 6.98 k → VBUSA1** | anode side | ✓ |
| D10 | GND | LEDVA2 → **R39 6.98 k → VBUSA2** | anode side | ✓ |
| D11 | GND | LEDVA3 → **R40 6.98 k → VBUSA3** | anode side | ✓ |
| D12 | GND | LEDVC → **R41 6.98 k → VBUSC** | anode side | ✓ |

**All five ballasts are on the ANODE (positive) side and every cathode faces the
lower-potential node.** No LED is reversed and none is unballasted.

Gating chain re-derived: Q8 is a BSS138 with G(1) = ENKILL, S(2) = GND,
D(3) = LEDPKK. ENKILL high → Q8 on → D8 conducts VIN → R37 → A → K → drain →
GND. ENKILL low → Q8 off → D8 dark while VIN is still live. That is exactly the
"LEDS DARK = SWITCH OFF – PACK STILL LIVE" semantics. The four rail LEDs need no
gate because VBUSA1/2/3 and VBUSC collapse on master-off.

Currents re-derived independently: D8 `(12.6 − 2.4)/6.98 k = 1.46 mA` …
`(9.0 − 1.8)/6.98 k = 1.03 mA` (`part.yaml` says 0.946–1.547 mA over corners —
agrees). D9-D12 `(5.15 − 3.1)/6.98 k = 0.29 mA` … `(5.15 − 2.6)/6.98 k =
0.37 mA` (`part.yaml` says 0.282–0.377 mA — agrees). Dim by design, with a
documented 3.92 k substitution already on the BOM. Not a finding.

### (c) R42 — the DNP 5VC setpoint-trim strap

**Connection: CONFIRMED CORRECT.** `R42.1 = 5VC`, `R42.2 = FB_C` — i.e. exactly
in parallel with `R12` (`R12.1 = 5VC`, `R12.2 = FB_C`), the 5VC feedback-divider
top leg.

**Shipped state: CONFIRMED UNPOPULATED.** R42 has **no row in
`fab/cpl.csv`**, so it is not placed. Verified arithmetic both ways:

    unpopulated: R_top = 4.12 k          -> 1.215 x (1 + 4.120/1.21) = 5.352 V
    populated:   4.12 k || 160 k = 4.017 k -> 1.215 x (1 + 4.017/1.21) = 5.249 V

**5.352 V is the figure `DETAIL_DESIGN.md` sec.2.11 and sec.4 carry** (nominal
5.352 V, corners 5.227/5.479 V, and the E-MARGIN budget is built on 5.227 V).
So the unpopulated state *is* the state the design math describes. ✓

Caveat recorded as **PR-6**: R42 *is* on `fab/bom.csv` (160 kΩ, C25757) while
absent from the CPL.

### (d) The ENKILL master-off bus

`ENKILL` has **7 members, all accounted for**:

    SW1.2 (COM)  U2.4 (EN)  U11.4 (EN)  Q7.1 (G)  Q8.1 (G)  R8.2  R17.2

- SW1 SS12D07VG6: `COM(2) = ENKILL`, `T1(1) = GND`, `T2(3) = no-connect`. Slide
  to T1 → EN grounded → both bucks in <10 µA shutdown. ✓ matches
  `02_parts/SS12D07VG6-087/part.yaml`; COM = centre pin is the SS-12D07 drawing
  standard.
- **R8 and R17 are BOTH 100 kΩ from VIN to ENKILL** — this is not a duplicate,
  it is one pull-up per buck (`part.yaml` gotcha names them "R8 buck-A /
  R17 buck-C"), giving **50 kΩ effective**. Checked against SNVS499I §6.3.2:
  *"A 1-MΩ pullup resistor to VIN can be used… At low input voltage the pullup
  resistor can be reduced to 100 kΩ to speed up the EN transition time"*, with
  *"the enable rise time must be less than 4 µs for 250-kHz operation."*
  50 kΩ is faster than the DS's own suggested floor: with ~70 pF of combined EN
  + 2 × BSS138 C_iss + trace, `t(0→3.3 V) = 50 k × 70 p × ln(12.6/9.3) ≈ 1.1 µs`
  < 4 µs. **PASS**, with margin.
- EN loading: DS EN input bias is −7.5…+1 µA at 3 V and ≤ 90 µA at 100 V; at
  ~12 V the two EN pins together take well under 30 µA, so ENKILL sits within
  ~1.5 V of VIN — far above the 3.3 V V_IH. ✓
- Q7 BSS138 `G(1) = ENKILL, S(2) = GND, D(3) = QG`; R30 100 kΩ from QG to PMID
  (Q6's own source). ENKILL high → Q7 on → QG low → Vgs(Q6) ≈ −5.35 V → Q6 on.
  ENKILL low → Q7 off → QG floats to PMID → Vgs(Q6) ≈ 0 → Q6 off, body diode
  (anode = D = 5VC, cathode = S = PMID) blocks PMID→5VC back-feed. ✓
- Switch current on master-off: `2 × 12.6 V / 100 kΩ = 252 µA` — trivial for a
  0.3 A part. ✓

### (e) Floating pins, and pins tied to a forbidden rail

Every no-connect in the netlist, adjudicated individually:

| pin | net | datasheet position | verdict |
|---|---|---|---|
| U3.8 / U4.8 / U5.8 FAULT | unconnected | SLVS931B: *"Active-low open-drain output"* — an output, no pull-up required | ✓ legal (no fault indication by design) |
| U7.3 DP2, U7.4 DM2 | unconnected | unused second BC1.2 channel | see **PR-8** |
| J5.A8 SBU1, J5.B8 SBU2 | unconnected | sideband, unused on a charge-only port | ✓ |
| SW1.3 T2 | unconnected | the unused throw; EN floats up via R8‖R17 | ✓ |

**Pins the datasheet says must not float — all driven:**
- LM5116 EN (SNVS499I §6.3.2 *"It must not be left floating"*) → on ENKILL ✓
- LM5116 VCCX (*"If VCCX is unused, VCCX must be connected to ground"*) → GND ✓
- LM5116 AGND/PGND/EP → GND ✓; TPS2557 EP → GND ✓

**Pins tied to a rail the datasheet forbids — none found.** Checked in
particular: CSG is on GND with the DS's ±1 V CSG-to-GND window respected; CS
swings only −I·R_S ≈ −60 mV at 6 A against a −3 V floor; DEMB sits at 0 V
against a −0.3…VCC abs max and a −0.3…2 V recommended range; TPS2557 EN at
5.15 V against a −0.3…7 V abs max; every USBLC6 VBUS pin is on its own port's
rail (see PR-7).

## Findings

| id | finding | sev | evidence |
|---|---|---|---|
| **PR-1** | **`pin_audit.py` silently produced an EMPTY dossier for U2 and U11 — the two 21-pad LM5116 buck controllers, the highest-consequence parts on the board.** The BOM MPN is `LM5116MHX/NOPB`; the tool does `ypath = parts / mpn / "part.yaml"`, which resolves to `02_parts/LM5116MHX/NOPB/part.yaml` — nonexistent. It then falls through with `ymap = {}`, `ds = "(none)"`, `verified = ""`, prints no warning and exits 0. `U2.md`/`U11.md` therefore read `datasheet: (none)`, `part.yaml verification note: (none)` and `(not in yaml)` on all 21 pads, while `U3.md` (MPN without a slash) carries both. A reviewer working from the dossier alone would have adjudicated the two bucks with **no datasheet pin table at all**. The hazard was already known one level down and never propagated: `02_parts/LM5116MHX-NOPB/part.yaml` line 4 literally says `note_dirname: "directory LM5116MHX-NOPB; '/' in MPN not usable in a path"`. This is the canon "a gate that cannot fail is worthless" pattern, review-tooling edition. **The board is unaffected** — this review re-read SNVS499I Table 4-1 directly — but the instrument the protocol depends on failed exactly where it mattered most. | **P1** | `skills/kicad-pcb/scripts/pin_audit.py:130`; `fab/bom.csv` row `C13755,"U11,U2",…,LM5116MHX/NOPB,C13755`; dossier `U2.md` vs `U3.md` |
| **PR-2** | `pin_audit.py:124-125` (`elif len(numbered) <= 3: continue`) excludes **every 2- and 3-pin part** from dossier coverage unless `--refs` is passed. On this board that silently omits D1, D2, D3, D4, D5, D8–D12 (TVS/zener/boot-diode/LED polarity), J1 (XT60 — the part whose own `part.yaml` records that a reversed XT60 shipped once), C1/C2 (polarized electrolytics), RS1/RS2, L1/L2, F2, SW1, Q7, Q8. The run reported `dossiers: 22` against a 122-ref board with no note that 100 refs were skipped. These are precisely the parts the project's own part files flag as the repeat-offender class. | **P2** | `skills/kicad-pcb/scripts/pin_audit.py:124-125`; dossier directory contains 22 files, netlist has 122 refs |
| **PR-3** | **Every pin in the exported netlist is typed `passive`** — 364 `passive` + 8 `passive+no_connect`, out of 372. Not one pin is `power_in`, `power_out`, `output`, `input` or `bidirectional`; the `.kicad_sch` contains no `(type …)` tokens at all. KiCad ERC's electrical-type matrix (output↔output collision, power-output collision, "input not driven", "pin not connected") is therefore **structurally incapable of firing** on this schematic, so a "0 ERC violations" result carries no pin-type information whatsoever. The board's own pin-type sanity is fine (verified by hand: both LM5116 gate drives fan out to exactly one gate each, no net has two drivers, no net has a single member) — but that was verified *here*, not by the gate. | **P2** | `usb_hub_3s_v2.net` pintype histogram `{passive: 364, passive+no_connect: 8}`; `grep -o '(type "[a-z_]*")' usb_hub_3s_v2.kicad_sch` → 0 matches |
| **PR-4** | **U2.11 and U11.11 (DEMB) are tied directly to GND, i.e. R_DEMB = 0 Ω.** SNVS499I states verbatim: *"When R_DEMB = 0 Ω, the LM5116 will always run in diode emulation"* and *"Fully synchronous operation is obtained if the DEMB pin is always biased to a higher potential than the SW pin when LO is high. R_DEMB = 10 kΩ will bias the DEMB pin to 0.45 V minimum, which is adequate for most applications."* TI's Figure 7-1 / Table 7-1 — **the worked design this board declares it adopts per canon M6** (`part.yaml layout_refs`, `DETAIL_DESIGN.md` "Sources") — fits **R8 = 10 kΩ** from DEMB to PGND for exactly that reason. This board omits it. Consequence: **both bucks run in permanent diode emulation and never operate fully synchronously**; below `I_out ≈ I_pp/2 ≈ 0.9 A` (re-derived: `I_pp = (5.15/(6.8 µH × 250 kHz)) × (1 − 5.15/12.6) = 1.79 A`) each rail is in DCM. This is *legal* — grounding DEMB is the DS-sanctioned configuration for start-up into a pre-biased load, and DCM at light load is arguably the right choice on a battery — but **`DETAIL_DESIGN.md` contains zero occurrences of "DEMB" or "diode emulation"**, and that file's own rule is *"A value in the schematic with no line here is UNJUSTIFIED."* An intentional departure from the cited reference design that changes the light-load behaviour of both rails has no written derivation. | **P2** | SNVS499I §6.3.x + Fig 7-1 + Table 7-1 (`R8 CRCW0603103J 10 kΩ`); netlist `U2.11 → GND`, `U11.11 → GND`; `grep -i "demb\|diode emulation" 01_docs/DETAIL_DESIGN.md` → 0 hits |
| **PR-5** | **The USBLC6 "pass-through" is collapsed onto single nets.** On U8/U9/U10/U12, pins 1 and 6 are on the SAME net and pins 3 and 4 are on the SAME net (e.g. U8.1 = U8.6 = DP_A1, U8.3 = U8.4 = DM_A1). This is **not a wiring error** — ST doc 11265 Rev 5 Figure 1 labels pins 1 and 6 both "I/O1" and pins 3 and 4 both "I/O2", i.e. each pair is one internal node — so it is electrically identical. But `DETAIL_DESIGN.md` sec.5.2 asserts *"Pass-through pairs 1-6 (D+) and 3-4 (D−)"*, and once both pads are on one net **nothing in the netlist, the ERC or the DRC can distinguish an in-line clamp from a stub hanging off a tee**. The property that makes an ESD array useful — that it is the first thing a transient meets, between the connector and everything downstream — is now a pure layout property with no gate behind it. Recommend the claim either be demoted to a layout-only assertion or be given a routing check. | **P2 / QUESTION** | ST USBLC6-2 doc 11265 Rev 5 Fig 1; netlist `DP_A1 => J2.3, U6.1, U8.1, U8.6` |
| **PR-6** | **R42 (160 kΩ, C25757) is on `fab/bom.csv` but has no row in `fab/cpl.csv`.** So are F1 and SW1 (BOM-only: `['F1','R42','SW1']`; CPL-only: `[]`). The intent is documented in the `.tsx` and the electrical answer is correct (see (c)), but the mechanism rests on an uncited assumption about the fab's behaviour, quoted from the source: *"JLC SOURCES one 160k 0402 and does NOT place it — it arrives loose with the order."* A BOM designator with no CPL position is a routine JLC DFM query; if the desk resolves it by *placing* R42 instead, the shipped 5VC becomes 5.249 V rather than the 5.352 V every downstream number in `DETAIL_DESIGN.md` sec.4 is built on (and the E-MARGIN worst-min drops 5.227 → 5.125 V). Worth one explicit line in the order notes rather than an assumption. | **P2** | `fab/bom.csv` vs `fab/cpl.csv` set difference; `source/usb_hub_3s_v2.tsx:322-367` |
| **PR-7** | U12's VBUS pin (and, marginally, U8/U9/U10's) sits above the USBLC6's 5.25 V characterization point: 5.352 V nominal / 5.479 V worst static corner on 5VC. **Already recorded** as an accepted deviation in `DETAIL_DESIGN.md` sec.5.3. Independently re-verified against the ST datasheet rather than against the write-up: Table 1 "Absolute ratings" genuinely lists only V_PP, T_stg, T_j and T_L — **there is no V_BUS voltage entry**, so the sec.5.3 reasoning ("5.25 V is a test condition, the device limit is V_BR = 6 V min") holds as written. No new action; listed so the coverage is complete. | **P2 (recorded)** | `USBLC6-2SC6_ST.pdf` Table 1 p.2; `DETAIL_DESIGN.md` sec.5.3 |
| **PR-8** | U7's unused channel-2 pins (DP2 pin 3, DM2 pin 4) are left floating. Both `02_parts/TPS2513ADBVR/part.yaml` (*"unused channel 2 pins (DP2/DM2) float with no_connect flags"*) and `DETAIL_DESIGN.md` sec.3 assert this is fine, **but neither cites a datasheet line**, and the only "can be left floating" sentence in SLVSBY8D belongs to the **TPS2514x** pin table, where pins 3/4 are genuine `N/C` — a *different device variant*. On the dual TPS2513A those pins are real DP2/DM2 detection I/O. The risk is low (an unused detection channel simply idles with nothing attached), but the citation currently supports a claim about a part that is not fitted. | **P2** | SLVSBY8D §6 pin functions: TPS2513x pins 3/4 = DP2/DM2 (I/O); TPS2514x pins 3/4 = *"No connect pin. Can be grounded or left floating."* |
| **PR-9** | The USB-A receptacles J2/J3/J4 use the vendored `usb_hub_3s:KH-AF90DIP-112_Horizontal`. Its geometry matches the Kinghelm drawing exactly (signal pitches 2.500/2.000/2.500, shell holes ⌀3.0 at 13.240 spacing, 2.600 forward, first signal hole 3.119 from the left shell — all confirmed by rendering the drawing). **But the vendor drawing does not number the four signal holes, and the pattern is geometrically symmetric**, so the drawing alone cannot establish which end is pin 1 = VBUS. The footprint is a byte-level derivative of KiCad's `Connector_USB:USB_A_Stewart_SS-52100-001_Horizontal` (identical pads at x = 0 / 2.5 / 4.5 / 7, identical property UUIDs, shells moved 3.07→3.119 and y 2.71→2.60 to match Kinghelm), so pin 1 = VBUS is **inherited from the KiCad library convention plus the USB-A contact standard** — sound, and the same conclusion `part.yaml` reaches, but it is inheritance, not a reading of *this* vendor's drawing. Consequence if wrong is severe (VBUS↔GND swapped on all three ports), so it belongs on the order-preview mechanical confirm list alongside SW1's throw direction. Separately noted: the vendored footprint carries **no F.SilkS geometry at all** (the KiCad original's silk body outline was stripped); only F.CrtYd and F.Fab survive. | **P2** | `KH-AF90DIP-112.pdf` p.1 PCB pattern (unnumbered); `usb_hub_3s.pretty/KH-AF90DIP-112_Horizontal.kicad_mod` vs `/usr/share/kicad/footprints/Connector_USB.pretty/USB_A_Stewart_SS-52100-001_Horizontal.kicad_mod` |

**No P0 findings.**

## Things specifically hunted for and NOT found

Recorded so the negative result is evidence rather than silence:

- No mirrored footprint on any part (6 datasheet pin figures re-read).
- No swapped drain/source on any of the six power FETs; both P-FETs (Q1 input
  RPP, Q6 USB-C reverse-block) have **D on the source-of-power side and S on the
  load side**, which is the orientation that makes the P-channel body diode
  (anode = drain) conduct forward and block reverse. Re-derived from
  semiconductor physics, not from the write-up.
- No gate-drive output landing on more than one gate, and none landing on a
  non-gate node.
- No net with only one member (every net has ≥ 2 pins; the 8 no-connects are
  explicitly flagged, not accidental singletons).
- No power rail on a feedback pin, and no feedback pin on a rail.
- No boot diode reversed (D3/D4 cathode on HB, anode on VCC).
- No TVS or zener reversed: D1 SMBJ15A K=VIN/A=GND; D2 BZT52C12 K=VIN(source)/
  A=RPP_G(gate); D5 SMBJ6.0A K=VBUSC/A=GND.
- No LED reversed and none unballasted (all five checked, both ends).
- No polarized electrolytic reversed (C1/C2 pad 1 = VIN, pad 2 = GND).
- J1 XT60 pad 1 = GND, pad 2 = VBAT — matching `part.yaml`'s "PAD 1 IS NEGATIVE"
  hard fact.
- No missing exposed pad and no EP on the wrong net (U2, U11, U3, U4, U5).
- No PCB/netlist divergence: 372/372 pad-net assignments identical.
- The three USB-A port cells and the two buck cells are **structurally
  identical instance-for-instance** — no lone divergent channel.

## Verdict

Four of the nine findings (PR-1, PR-2, PR-3, and the documentation half of
PR-4) are defects in the **gates and instruments**, not in the board. The
netlist itself came through 372/372 pins with no wiring error, no reversal, no
mirror, and no forbidden connection. The one P1 is that the dossier generator
this protocol runs on failed silently and invisibly on the two most complex
parts of the board — the board survived only because this review went back to
the datasheet. That must be fixed before the next board's pin review can be
believed.

No P0 was found, so the release is not blocked. The header verdict is
`PASS-WITH-NOTES` (the `08_reviews/contracts.md` vocabulary); the brief's
required binary line follows.

VERDICT: PASS
