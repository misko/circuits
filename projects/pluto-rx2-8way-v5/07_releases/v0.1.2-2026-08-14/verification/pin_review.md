subject: pluto-rx2-8way-v5 v0.1.0-2026-08-13 physical pin and footprint review
date: 2026-08-13
reviewer: pin-review (GPT-5 Codex, physical pin/footprint lens)
context-given: release-archive-plus-authorities
source_commit: 798ef9812019efb9e9857332736926d099192a03
board_sha256: 43689fe44daa2bd437979c573e78da39a51aacd9d4664a24e7e29bc1c22ea0b3
design_verdict: SOUND
order_verdict: DO-NOT-ORDER

# Exact physical-pin and footprint review

## Scope

This hardware-only review compares the exact staged board and release-local
footprints with the retained manufacturer pin tables, drawings, exact BOM,
and fabrication drills. Firmware is excluded. The exact board matches the
staged project board byte-for-byte, and the release netlist-to-board parity
report is zero-discrepancy over 22 nets and 131 connected nodes.

## Pin and land checks

| ref | physical authority and realized check | result |
|---|---|---|
| U1 | PE42482 top-view pinout is preserved: LS=1/GND, RF2/3/4=2/4/6, VDD=8, V1..V4=9..12, RF5/6/7/8=13/15/17/19, RFC=22, RF1=24, all named grounds plus 2.75 mm EP/pad 25 on GND, and pin 20 open. Perimeter lands are 0.30 x 0.60 mm on 0.50 mm pitch; the exposed land is 2.75 mm square. | PASS |
| U2 | ST DS13866 Rev 5 TSSOP-20 pin map matches the board: VDD/VDDA=4, VSS/VSSA=5, NRST=6, PA0..PA3=7..10, SWDIO=18, SWCLK=19. All other pins are explicit no-connects. The stock TSSOP-20 4.4 x 6.5 mm, 0.65 mm-pitch footprint matches the selected package. | PASS |
| U3 | TPS7A2433 DBV fixed-output pin map matches: IN=1, GND=2, EN=3 tied to IN, NC=4 open, OUT=5. The SOT-23-5 land is the selected DBV package. | PASS |
| U4 | TPD2E2U06 DRL map matches: pins 1/2 open, IO1=3/CC1, GND=4, IO2=5/CC2. The SOT-553 land matches the DRL package. | PASS |
| D1 | SMBJ6.0A pad 1/cathode is VBUS_PROTECTED and pad 2/anode is GND in the DO-214AA SMB land. | PASS |
| J1 | GCT USB4105 Rev B contact identities are retained. Coincident A1/B12 and A12/B1 lands are GND; coincident A4/B9 and A9/B4 lands are VBUS; A5 and B5 remain separate CC1/CC2; D+/D-/SBU contacts are open; all shell stakes are GND. The two 0.65 mm locators and four shell slots are present. | PASS |
| J2-J10 | Each Amphenol 901-143-6RFX has pin 1 as its RF net and pins 2..5 as GND. Relative centres are one signal at (0,0) and four grounds at (+/-2.54,+/-2.54) mm. Fabrication uses the Rev-C manufacturer finished holes: 1.50 mm signal and 1.70 mm grounds, with 2.40/2.80 mm copper lands. All nine bodies face their assigned board edge in the staged 3D evidence. | PASS |
| J11 | Samtec FTSH-105-01-L-DV-K-P-TR uses the manufacturer 0.74 x 2.79 mm lands, 1.27 mm column pitch, and 4.065 mm row spacing. Pins are 1=VTref/3V3, 2=SWDIO, 3=GND, 4=SWCLK, 5=GND, 9=GNDDetect/GND, 10=NRST; 6/7/8 are open. Pin 1 and keying are present in the board evidence. | PASS |
| passives | BOM values and packages match the exact dossiers: 5.1 kohm 1% Rd at R1/R2; 10 kohm 1% control biases at R3-R6; 4.7 uF 16 V at C1-C3; 100 nF 16 V at C4-C6; exact 0603L010YR at F1. | PASS |

The released BOM resolves 13 exact rows and 29 fitted placements. Its LCSC
codes match the staged source and retained dossiers 13/13. Model coverage is
29/29, assembly coverage is complete, and the release fabrication census has
the expected nine SMA 1.50 mm signal holes and 36 SMA 1.70 mm ground holes.
U1's nine 0.45/0.25 mm via-in-pad sites are a distinct protected family from
the 629 ordinary 0.45/0.20 mm vias.

## External confirmation still required

The local pin and land mappings are sound, but three placement rotations have
only pad-number-derived catalog corroboration: U1/C5121458, U2/C5452432, and
J11/C2932107. JLC's live placement preview must confirm their pin-1/key
orientation before payment. D1 polarity, J1 mouth direction, and all nine SMA
body directions must be confirmed in the same preview.

JLC catalog CAD for C429844 uses 1.60/1.80 mm drills, while the retained
Amphenol Rev-C authority calls for 1.50/1.70 mm. The manufacturer land is
correctly preserved, but JLC must explicitly accept it and must echo all nine
connectors as wave/manual through-hole assembly. Similarly, JLC's generic
C2932107 land must not replace the manufacturer Samtec land.

## Verdict

No physical pin-number, net-to-pad, package-selection, or manufacturer-land
defect was found. The exact staged hardware is SOUND. The order remains
DO-NOT-ORDER because current uploader interpretation, exact through-hole
acceptance, placement/polarity preview, selective via process, and first
article inspection have not yet supplied external confirmation. This is not a
sourcing block; the staged stock census clears all 13 rows for five boards.
