"""Shared board geometry — single source for generate_board.py, route_bank.py,
route_prep.py, stitch_and_fill.py, audit_board.py.

All mm, board frame (y-down). Derivations: 01_docs/DETAIL_DESIGN.md,
ADR-0002 (isolation numbers). ISO_MIN = 6.0mm creepage/clearance (§6.3).

Bank routing scheme (as-built, ADR-0002 amendment 2026-07-19):
- per super-column k, ALL THREE sanctioned SELV verticals share
  two x slots west of the coil pads: COIL_V_ODD (-1.15: odd-coil B.Cu +
  RELAY_5V F.Cu) and COIL_V_EVEN (-1.7: even-coil B.Cu); short stubs
  reach the coil pads. West edge of the stack is COIL_X-1.9; the previous
  column's easternmost keypad copper is CONT_X[k-1]+1.9 = COIL_X[k]-8.26
  => gap 6.36mm >= ISO_MIN. Binding minimum is the package's own
  coil-pad-to-contact-pad distance: 7.62 - 2x0.75 = 6.12mm.
- coil nets travel E-W on B.Cu lanes (COIL_LANE_YS), drop at a via IN
  the tail of their ULN OUT pad (COIL_VIA_Y row). KRT never touches
  KEYPAD/COIL/RELAY_5V nets (route_bank.py draws them).
- contact nets: corridor lane offsets {0,1.15,1.7} (2 per layer),
  E-W fan lanes in the FAN band (16 per layer), jog-drops into J11.
"""

# board outline — height grown 112->120 (Y1 132->140) per ADR-0006: §8.2 asks
# only for an enclosure-compatible outline + mounting holes (no fixed enclosure
# exists), so +8mm south buys a third south row that lets the SELV coil-driver
# logic chain leave the power/safety strip and decouplers land at their ICs.
X0, Y0, X1, Y1 = 20.0, 20.0, 205.0, 140.0        # 185 x 120

ISO_MIN = 6.0          # keypad-copper to SELV-copper floor (§6.3)

# ---------------- relay bank (ADR-0002 geometry) ----------------
NSC = 8                                # super-columns
SC_PITCH = 17.78
COIL_X0 = 66.0                         # coil column of super-column 1
COIL_X = [COIL_X0 + SC_PITCH * k for k in range(NSC)]
CONT_X = [x + 7.62 for x in COIL_X]    # contact columns
ROW_Y = [58.0, 78.5]                   # pin1/14 y for row0 (north), row1
PIN_SPAN = 15.24                       # pin1->pin7 (and 14->8) span
# relay Kn: n = 2k-1 (row0) / 2k (row1) of super-column k (1-based)

# contact corridor lane x-offsets from CONT_X (all EAST, <= 1.7)
LANE_F0 = 0.0     # row0 pin14 (A net) F.Cu — straight off the pad
LANE_F1 = 1.15    # row1 pin8  (B net) F.Cu
LANE_B0 = 1.15    # row0 pin8  (B net) B.Cu
LANE_B1 = 1.7     # row1 pin14 (A net) B.Cu
W_CONTACT = 0.4

# isolation slots (Edge.Cuts), 2mm wide, between super-columns
SLOT_W = 2.0
SLOT_X = [COIL_X0 + 13.05 + SC_PITCH * k for k in range(NSC - 1)]
SLOT_Y0, SLOT_Y1 = 47.0, 97.0   # top was 44.0: the fan band (y34-46) + J11
# ch11/12 drops grazed the slot tops at x150.2 (copper_edge_clearance). y47
# keeps the slots fully covering the bank relay region (y58-93) with margin,
# well clear of the isolated north-strip keypad routing.
WSLOT_X, WSLOT_Y0, WSLOT_Y1 = 61.5, 22.5, 52.0   # strip west guard slot

# isolated north strip (J11 + fan)
J11_XY = (140.0, 30.0)          # 2x16 IDC, columns 2.54, rows 2.54
J11_COL0_X = J11_XY[0] - 15 * 2.54 / 2          # 120.95
J11_ROWA_Y = J11_XY[1] - 1.27                    # odd pins (A nets)
J11_ROWB_Y = J11_XY[1] + 1.27                    # even pins (B nets)
FAN_Y0, FAN_Y1 = 33.6, 46.4     # E-W lane band (16 lanes x 0.8 per layer)
FAN_PITCH = 0.8
FAN_LANE_Y = [34.0 + FAN_PITCH * i for i in range(16)]

# iso comb (keypad-copper region, for keepouts/audit): north strip + corridors
STRIP_RECT = (68.0, 21.0, 203.0, 50.5)           # x0,y0,x1,y1
CORR_Y1 = 95.0                                   # corridors reach row1 pin8+
CORR_HALF_W = 2.7                                # x_c-0.5 .. x_c+2.7 span

# SELV keep-back (planes / KRT / floaters): no SELV copper here except
# the sanctioned bank routing (verticals, lanes, TP bridges, R5V bus)
NOGO = (60.0, Y0, X1, 106.8)   # x0,y0,x1,y1
COIL_V_ODD = -1.15             # odd-coil vertical (B.Cu) + RELAY_5V (F.Cu)
COIL_V_EVEN = -1.7             # even-coil vertical (B.Cu)
W_COIL = 0.4

R5V_BUS_Y = 101.8              # RELAY_5V F.Cu bus (Q1 -> all columns)
W_R5V = 0.8
COIL_LANE_YS = [100.9 + 0.6 * i for i in range(8)]   # B.Cu E-W coil lanes
COIL_VIA_Y = 106.0             # via-in-pad-tail row at the ULN OUT pads

ULN1_XY = (92.0, 110.0)        # U5 (K1-K8; pad row must clear the col-3 coil verticals)
ULN2_XY = (158.0, 110.0)       # U6 (K9-K16)

# ULN pads (SOIC-18W rotated so pin rows run E-W): north row y = uln_y - 4.65,
# west->east = 18(OUT1)..10(COM); south row = 1(IN1)..9(GND) west->east.
ULN_PAD_DY = 4.65

# ---------------- SELV floorplan anchors ----------------
PICO_XY = (42.0, 84.0)         # J2 socket center; rows x = +-8.89
SR1_XY = (84.0, 121.0)         # U3 74HC595 #1
SR2_XY = (144.0, 121.0)        # U4 #2
WD_XY = (66.5, 110.0)          # U7 LVC1G123
Q1_XY = (61.5, 108.8)          # high-side PFET below the bank, drain north
TC_XY = (31.0, 33.0)           # U1 MAX31856 (NW analog corner)

# mounting holes (NPTH 3.2mm; nylon standoffs) — south holes track Y1=140
# H5 west-mid support relocated 62->110.5: the west edge is fully packed with
# JST connectors J3(y35-49) J4(51-65) J14(65-81) J7/J8(84-107); the only clear
# west-edge gap for a 3.2mm hole is y107-114 between J8 and the F1 power corner.
# H6 south-mid support: was (133,136) — collided with J13 (137,136) pads
# (npth_inside_courtyard + courtyard overlap + hole clearance). Moved to
# (126,124), a south-central pocket north of the J12/J13 connector row with
# 7.75mm clearance to the nearest pad.
HOLES = [(24.0, 24.0), (201.0, 24.5), (24.0, 136.0), (201.0, 136.0),
         (24.0, 110.5), (126.0, 124.0)]

# KRT keepouts (User.2): iso comb + bank + lanes + TP rows + ULN north row
KRT_KEEPOUTS = [
    (60.0, Y0, X1, 106.8),     # bank + strip + lanes + via rows + ULN north
    (60.3, 106.8, 62.7, 107.9),  # Q1 drain-pad tongue (drain faces north)
]

# track/via dims
W_SIG, W_PWR = 0.25, 0.5
VIA_D, VIA_DRILL = 0.6, 0.3
VIA_STITCH = 0.6
