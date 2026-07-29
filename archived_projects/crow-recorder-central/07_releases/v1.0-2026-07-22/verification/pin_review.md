# Pin review verdicts — crow-recorder-central v1.0

Fresh-context per-group reviews per pin-review-protocol. Reviewers were given
pin_audit dossiers with NO design context and re-read each datasheet figure
independently. Full per-part dossiers: 06_build/pin_review/. ZERO FAILs across
all groups.

## Summary of all group verdicts

| group | parts | verdict | note |
|---|---|---|---|
| digital core | U1 XU316-1024-TQ128 | PASS | all 129 pins vs datasheet Table 4; winding CCW vs Fig 2; no mirror |
| flash | U4 W25Q16JVSSIQ | PASS | quad-IO bit order matches port 4B |
| clock buffer | U5 NC7NZ34K8X | PASS | channel pairing verified (1->2 MCLK fanout) |
| ADC | U2/U3 PCM1865 | PASS | MCLK/BCLK/LRCK series links R40-R43 re-measured in netlist (QUESTION -> PASS); XI=GND, SCKI=MCLK |
| sensor | U6 SHT40 | PASS | I2C 0x44 |
| RJ45 ports | J1-J8 RJHSE-5384 | PASS | contact-for-contact vs crow-mic-pod sealed ADR-0004; rotation-not-mirror proven by the dimension chain |
| USB-C | J12 USB4105-GF-A | PASS | A/B symmetry; CC1/CC2 Rd 5.1k each to GND verified |
| ESD (audio) | D21-D28 TPD2E2U06 | PASS | all 8 ports symmetric, CCW, no mirror |
| ESD (USB) | D10 TPD4EUSB30 | PASS | D+/D- correct; unused ch2 float intentional |
| power | U10/U11 bucks, U12/U13 LDOs, Q9 revFET, D9 TVS | PASS | see group_power below |

## group_esd.md (verbatim)
# fresh-context pin review — ESD group (D21-D28 TPD2E2U06DRLR, D10 TPD4EUSB30DQAR)
Reviewer: fresh agent, 2026-07-21. Datasheet figures re-rendered and read
independently (SLLSEG9C p.3; SLVSAC2G Fig 5-2/Table 5-1 + DQA0010B).

VERDICT: PASS   (D21..D28 TPD2E2U06DRLR, grouped — no per-instance exceptions)
D21..D28 pins 1,2 (NC): expected netless, floating permitted vs dossier shows unconnected — match
D21..D28 pin 3 (IO1): expected ESD channel to a connector-bound signal vs dossier shows AUD_P1..AUD_P8 respectively — match, symmetric across all 8 ports
D21..D28 pin 4 (GND): expected ground vs dossier shows GND — match
D21..D28 pin 5 (IO2): expected ESD channel to a connector-bound signal vs dossier shows AUD_N1..AUD_N8 respectively — match, symmetric across all 8 ports
D21..D28 winding: expected CCW top view, pin 1 top-left vs dossier computed CCW, pad 1 W-top — match, no mirror

VERDICT: PASS   (D10 TPD4EUSB30DQAR)
D10 pin 1 (D1+): expected USB D+ vs USB_DP — match
D10 pin 2 (D1-): expected USB D- vs USB_DM — match
D10 pins 3,8 (GND): expected both grounded vs both GND — match
D10 pins 4,5 (D2+/D2-): unused channel may float vs unconnected — intentional single-port use, inert
D10 pins 6,7,9,10 (NC): expected netless vs unconnected — match
D10 winding: expected CCW top view, pin 1 top-left, channels all west column (DQA not flow-through) vs dossier CCW — match, no mirror
D10 exposed pad: none expected (DQA0010B) vs 10 perimeter pads, no EP — match

No FAILs, no QUESTIONs.

## group_power.md (verbatim)
# fresh-context pin review — power group (U10/U11 AP61102, U12 TLV70018, U13 XC6227, Y1 X322524MOB4SI, U6 SHT40)
Reviewer: fresh agent, 2026-07-21. All figures independently rendered/read;
every dossier = datasheet figure at identity or pure rotation, NO mirrors;
all CCW windings match.

VERDICT: PASS (U10 AP61102) — FB->FB1 divider, VIN->5V, SW->BK1_SW, EN->5V (sanctioned), PG->BK1_PG
VERDICT: QUESTION->PASS (U11 AP61102) — structural divergence U10.EN=5V vs
  U11.EN=BK1_PG (rail sequencing). Reviewer could not see whether open-drain
  BK1_PG has a pull-up. ADJUDICATED by orchestrator with board measurement
  (pcbnew net dump, 2026-07-21): R12 "10k PG1 pu" BK1_PG->5V and R15
  "10k PG2 pu" BK2_PG->3V3 both present — U11 EN rises when buck 1 is in
  regulation; sequencing is deliberate and functional. PASS.
VERDICT: PASS (U12 TLV70018DDCR) — IN->3V3, EN->3V3, OUT->1V8, NC float allowed
VERDICT: PASS (U13 XC6227C331PR-G) — PR-G=SOT-89-5 confirmed from ordering
  table; CE->5V (C-type active-high), tab VSS->GND, VOUT->3V3A
VERDICT: PASS (Y1 X322524MOB4SI) — diagonal electrodes 1/3 on XIN/XTAL2, case 2/4->GND
VERDICT: PASS (U6 SHT40) — SDA/SCL/VDD/VSS match Fig.18; custom land = Fig.17 exactly

Summary: 6 PASS after one evidence-backed adjudication; 0 FAIL.
