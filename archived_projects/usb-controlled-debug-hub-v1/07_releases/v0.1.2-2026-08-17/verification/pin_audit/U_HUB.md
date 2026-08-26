# pin dossier: U_HUB  (USB2517I-JZX)

- footprint: Package_DFN_QFN:QFN-64-1EP_9x9mm_P0.5mm_EP4.7x4.7mm_ThermalVias
- board position: (93.0, 65.0) rot 0
- computed winding of pins 1..N: **CCW (top view)**
- datasheet: projects/usb-controlled-debug-hub-v1/02_parts/USB2517I-JZX/DS00001598C.pdf
- part.yaml verification note: CITED: complete 1-64 map read from DS00001598C Figure 3-1 PDF p7 and cross-checked against Table 5-1 PDF pp11-16 plus Microchip EVB-USB2517 schematic sheet 2; pad 65 realization cross-checked against the EVB symbol VSS(FLAG) and selected footprint. 2026-07-31.

Coordinates are FOOTPRINT-LOCAL mm, rotation undone; +y is DOWN
(so this table reads like the top view of the part on the board).

| pad | local (x,y) | side | size | function (part.yaml) | NET on board |
|---|---|---|---|---|---|
| 1 | (-4.41,-3.75) | W | 0.88x0.2 | USBDN1_DM/PRT_DIS_M1 | MGMT_P |
| 2 | (-4.41,-3.25) | W | 0.88x0.2 | USBDN1_DP/PRT_DIS_P1 | MGMT_N |
| 3 | (-4.41,-2.75) | W | 0.88x0.2 | USBDN2_DM/PRT_DIS_M2 | P1_HUB_N |
| 4 | (-4.41,-2.25) | W | 0.88x0.2 | USBDN2_DP/PRT_DIS_P2 | P1_HUB_P |
| 5 | (-4.41,-1.75) | W | 0.88x0.2 | VDDA33 | 3V3_MAIN |
| 6 | (-4.41,-1.25) | W | 0.88x0.2 | USBDN3_DM/PRT_DIS_M3 | P2_HUB_N |
| 7 | (-4.41,-0.75) | W | 0.88x0.2 | USBDN3_DP/PRT_DIS_P3 | P2_HUB_P |
| 8 | (-4.41,-0.25) | W | 0.88x0.2 | USBDN4_DM/PRT_DIS_M4 | P3_HUB_N |
| 9 | (-4.41,+0.25) | W | 0.88x0.2 | USBDN4_DP/PRT_DIS_P4 | P3_HUB_P |
| 10 | (-4.41,+0.75) | W | 0.88x0.2 | VDDA33 | 3V3_MAIN |
| 11 | (-4.41,+1.25) | W | 0.88x0.2 | USBDN5_DM/PRT_DIS_M5 | P4_HUB_N |
| 12 | (-4.41,+1.75) | W | 0.88x0.2 | USBDN5_DP/PRT_DIS_P5 | P4_HUB_P |
| 13 | (-4.41,+2.25) | W | 0.88x0.2 | CFG_SEL2 | HUB_CFG2 |
| 14 | (-4.41,+2.75) | W | 0.88x0.2 | LED_B7_N | unconnected-(U_HUB-LED_B7-Pad14) |
| 15 | (-4.41,+3.25) | W | 0.88x0.2 | LED_A7_N/PRT_SWP7 | HUB_SWAP7 |
| 16 | (-4.41,+3.75) | W | 0.88x0.2 | LED_B6_N | unconnected-(U_HUB-LED_B6-Pad16) |
| 17 | (-3.75,+4.41) | S | 0.2x0.88 | LED_A6_N/PRT_SWP6 | HUB_SWAP6 |
| 18 | (-3.25,+4.41) | S | 0.2x0.88 | LED_B5_N | unconnected-(U_HUB-LED_B5-Pad18) |
| 19 | (-2.75,+4.41) | S | 0.2x0.88 | TEST | unconnected-(U_HUB-TEST-Pad19) |
| 20 | (-2.25,+4.41) | S | 0.2x0.88 | PRTPWR4 | HUB_PRTPWR4 |
| 21 | (-1.75,+4.41) | S | 0.2x0.88 | OCS4_N | HUB_OCS4_N |
| 22 | (-1.25,+4.41) | S | 0.2x0.88 | OCS3_N | HUB_OCS3_N |
| 23 | (-0.75,+4.41) | S | 0.2x0.88 | PRTPWR3 | HUB_PRTPWR3 |
| 24 | (-0.25,+4.41) | S | 0.2x0.88 | VDD33CR | 3V3_MAIN |
| 25 | (+0.25,+4.41) | S | 0.2x0.88 | VDD18 | HUB_VDD18 |
| 26 | (+0.75,+4.41) | S | 0.2x0.88 | PRTPWR2 | HUB_PRTPWR2 |
| 27 | (+1.25,+4.41) | S | 0.2x0.88 | OCS2_N | HUB_OCS2_N |
| 28 | (+1.75,+4.41) | S | 0.2x0.88 | OCS1_N | HUB_OCS1_N |
| 29 | (+2.25,+4.41) | S | 0.2x0.88 | PRTPWR1 | HUB_PRTPWR1 |
| 30 | (+2.75,+4.41) | S | 0.2x0.88 | PRTPWR5 | HUB_PRTPWR5 |
| 31 | (+3.25,+4.41) | S | 0.2x0.88 | LED_A5_N/PRT_SWP5 | HUB_SWAP5 |
| 32 | (+3.75,+4.41) | S | 0.2x0.88 | LED_B4_N | unconnected-(U_HUB-LED_B4-Pad32) |
| 33 | (+4.41,+3.75) | E | 0.88x0.2 | LED_A4_N/PRT_SWP4 | HUB_SWAP4 |
| 34 | (+4.41,+3.25) | E | 0.88x0.2 | LED_B3_N/GANG_EN | HUB_GANG |
| 35 | (+4.41,+2.75) | E | 0.88x0.2 | OCS5_N | HUB_OCS5_N |
| 36 | (+4.41,+2.25) | E | 0.88x0.2 | PRTPWR7 | unconnected-(U_HUB-PRTPWR7-Pad36) |
| 37 | (+4.41,+1.75) | E | 0.88x0.2 | OCS7_N | unconnected-(U_HUB-OCS7_N-Pad37) |
| 38 | (+4.41,+1.25) | E | 0.88x0.2 | OCS6_N | unconnected-(U_HUB-OCS6_N-Pad38) |
| 39 | (+4.41,+0.75) | E | 0.88x0.2 | PRTPWR6 | unconnected-(U_HUB-PRTPWR6-Pad39) |
| 40 | (+4.41,+0.25) | E | 0.88x0.2 | SDA/SMBDATA/NON_REM1 | HUB_NONREM1 |
| 41 | (+4.41,-0.25) | E | 0.88x0.2 | SCL/SMBCLK/CFG_SEL0 | HUB_CFG0 |
| 42 | (+4.41,-0.75) | E | 0.88x0.2 | HS_IND/CFG_SEL1 | HUB_CFG1 |
| 43 | (+4.41,-1.25) | E | 0.88x0.2 | RESET_N | HUB_RESET_N |
| 44 | (+4.41,-1.75) | E | 0.88x0.2 | VBUS_DET | HUB_VBUS_SENSE |
| 45 | (+4.41,-2.25) | E | 0.88x0.2 | SUSP_IND/LOCAL_PWR/NON_REM0 | HUB_NONREM0 |
| 46 | (+4.41,-2.75) | E | 0.88x0.2 | VDD33 | 3V3_MAIN |
| 47 | (+4.41,-3.25) | E | 0.88x0.2 | LED_A3_N/PRT_SWP3 | HUB_SWAP3 |
| 48 | (+4.41,-3.75) | E | 0.88x0.2 | LED_B2_N/BOOST1 | HUB_BOOST1 |
| 49 | (+3.75,-4.41) | N | 0.2x0.88 | LED_A2_N/PRT_SWP2 | HUB_SWAP2 |
| 50 | (+3.25,-4.41) | N | 0.2x0.88 | LED_B1_N/BOOST0 | HUB_BOOST0 |
| 51 | (+2.75,-4.41) | N | 0.2x0.88 | LED_A1_N/PRT_SWP1 | HUB_SWAP1 |
| 52 | (+2.25,-4.41) | N | 0.2x0.88 | VDDA33 | 3V3_MAIN |
| 53 | (+1.75,-4.41) | N | 0.2x0.88 | USBDN6_DM/PRT_DIS_M6 | HUB_DIS6_N |
| 54 | (+1.25,-4.41) | N | 0.2x0.88 | USBDN6_DP/PRT_DIS_P6 | HUB_DIS6_P |
| 55 | (+0.75,-4.41) | N | 0.2x0.88 | USBDN7_DM/PRT_DIS_M7 | HUB_DIS7_N |
| 56 | (+0.25,-4.41) | N | 0.2x0.88 | USBDN7_DP/PRT_DIS_P7 | HUB_DIS7_P |
| 57 | (-0.25,-4.41) | N | 0.2x0.88 | VDDA33 | 3V3_MAIN |
| 58 | (-0.75,-4.41) | N | 0.2x0.88 | USBUP_DM | UP_HUB_N |
| 59 | (-1.25,-4.41) | N | 0.2x0.88 | USBUP_DP | UP_HUB_P |
| 60 | (-1.75,-4.41) | N | 0.2x0.88 | XTAL2 | XTAL2 |
| 61 | (-2.25,-4.41) | N | 0.2x0.88 | XTAL1/CLKIN | XTAL1 |
| 62 | (-2.75,-4.41) | N | 0.2x0.88 | VDD18PLL | HUB_VDD18PLL |
| 63 | (-3.25,-4.41) | N | 0.2x0.88 | RBIAS | RBIAS |
| 64 | (-3.75,-4.41) | N | 0.2x0.88 | VDD33PLL | 3V3_MAIN |
| 65 | (-2.10,-2.10) | W | 0.5x0.5 THT | EP/VSS | GND |
| 65 | (-2.10,-0.70) | W | 0.5x0.5 THT | EP/VSS | GND |
| 65 | (-2.10,+0.70) | W | 0.5x0.5 THT | EP/VSS | GND |
| 65 | (-2.10,+2.10) | S | 0.5x0.5 THT | EP/VSS | GND |
| 65 | (-0.70,-2.10) | N | 0.5x0.5 THT | EP/VSS | GND |
| 65 | (-0.70,-0.70) | W | 0.5x0.5 THT | EP/VSS | GND |
| 65 | (-0.70,+0.70) | S | 0.5x0.5 THT | EP/VSS | GND |
| 65 | (-0.70,+2.10) | S | 0.5x0.5 THT | EP/VSS | GND |
| 65 | (+0.00,+0.00) | center | 4.7x4.7 | EP/VSS | GND |
| 65 | (+0.00,+0.00) | center | 4.7x4.7 | EP/VSS | GND |
| 65 | (+0.70,-2.10) | N | 0.5x0.5 THT | EP/VSS | GND |
| 65 | (+0.70,-0.70) | E | 0.5x0.5 THT | EP/VSS | GND |
| 65 | (+0.70,+0.70) | S | 0.5x0.5 THT | EP/VSS | GND |
| 65 | (+0.70,+2.10) | S | 0.5x0.5 THT | EP/VSS | GND |
| 65 | (+2.10,-2.10) | E | 0.5x0.5 THT | EP/VSS | GND |
| 65 | (+2.10,-0.70) | E | 0.5x0.5 THT | EP/VSS | GND |
| 65 | (+2.10,+0.70) | E | 0.5x0.5 THT | EP/VSS | GND |
| 65 | (+2.10,+2.10) | S | 0.5x0.5 THT | EP/VSS | GND |

(9 unnumbered paste/mechanical pads not shown)
