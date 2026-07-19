"""Shared board geometry — single source for generate_board.py, route_bank.py,
route_prep.py, stitch_and_fill.py, audit_board.py.

All mm, board frame (y-down). Derivations: 01_docs/DETAIL_DESIGN.md,
ADR-0002 (isolation numbers). ISO_MIN = 6.0mm creepage/clearance (§6.3).

Bank routing scheme (as-built, ADR-0002 amendment 2026-07-19):
- per super-column k, ALL THREE sanctioned SELV verticals share
  x = COIL_X[k] + COIL_V_X (west of the coil pads) on three layers:
  F.Cu = RELAY_5V trunk, B.Cu = odd coil (row0), In2.Cu = even coil (row1);
  short stubs reach the coil pads. West edge of that track stack is
  COIL_X-1.5; the previous column's easternmost keypad copper is
  CONT_X[k-1]+2.2 = COIL_X[k]-7.96 => gap 6.46mm >= ISO_MIN.
- coil nets travel E-W on B.Cu/In2 lanes (COIL_LANE_YS), drop at their
  bridge test point (THT, all-layer) in the TP row by the ULNs, and finish
  on F.Cu into the ULN OUT pad. KRT never touches COIL/KC/RELAY_5V nets.
- contact nets: 4 corridor lane offsets per super-column (2 per layer),
  E-W fan lanes in FAN band (16 per layer), jog-drops into J11.
"""

# board outline
X0, Y0, X1, Y1 = 20.0, 20.0, 205.0, 132.0        # 185 x 112

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

# contact corridor lane x-offsets from CONT_X (all EAST, <= 2.0)
LANE_F0 = 0.0     # row0 pin14 (A net) F.Cu — straight off the pad
LANE_F1 = 1.3     # row1 pin8  (B net) F.Cu
LANE_B0 = 1.3     # row0 pin8  (B net) B.Cu
LANE_B1 = 2.0     # row1 pin14 (A net) B.Cu
W_CONTACT = 0.4

# isolation slots (Edge.Cuts), 2mm wide, between super-columns
SLOT_W = 2.0
SLOT_X = [COIL_X0 + 13.05 + SC_PITCH * k for k in range(NSC - 1)]
SLOT_Y0, SLOT_Y1 = 44.0, 97.0
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
COIL_V_X = -1.3                # shared vertical offset from COIL_X:
                               #   F.Cu=RELAY_5V, B.Cu=odd coil, In2=even coil
W_COIL = 0.4

R5V_BUS_Y = 101.8              # RELAY_5V F.Cu bus (Q1 -> all columns)
W_R5V = 0.8
COIL_LANE_YS = [98.8, 99.5, 100.2, 100.9]   # E-W coil lanes (B.Cu and In2)

# coil bridge test points (THT D2.0/1.0): one row per ULN, 2.54 pitch
TP_ROW_Y = 104.8
ULN1_XY = (98.0, 110.0)        # U5 (K1-K8)
ULN2_XY = (158.0, 110.0)       # U6 (K9-K16)


def tp_x(uln_x, i):            # i = 0..7 west->east
    return uln_x + (i - 3.5) * 2.54


# ULN pads (SOIC-18W rotated so pin rows run E-W): north row y = uln_y - 4.35,
# 9 pads west->east = 10(COM),11(OUT8)..18(OUT1); south row = 1(IN1)..9(GND).
ULN_PAD_DY = 4.35

# ---------------- SELV floorplan anchors ----------------
PICO_XY = (42.0, 84.0)         # J2 socket center; rows x = +-8.89
SR1_XY = (84.0, 121.0)         # U3 74HC595 #1
SR2_XY = (144.0, 121.0)        # U4 #2
WD_XY = (63.0, 110.0)          # U7 LVC1G123
Q1_XY = (56.0, 101.8)          # high-side PFET on the bus line
TC_XY = (31.0, 33.0)           # U1 MAX31856 (NW analog corner)

# mounting holes (NPTH 3.2mm; nylon standoffs)
HOLES = [(24.0, 24.0), (201.0, 24.5), (24.0, 128.0), (201.0, 128.0),
         (24.0, 62.0), (120.0, 128.0)]

# KRT keepouts (User.2): iso comb + bank + lanes + TP rows + ULN north row
KRT_KEEPOUTS = [
    (60.0, Y0, X1, 102.6),                    # bank + strip + lanes + bus
    (ULN1_XY[0] - 10.4, 102.6, ULN1_XY[0] + 10.4, 106.8),
    (ULN2_XY[0] - 10.4, 102.6, ULN2_XY[0] + 10.4, 106.8),
]

# track/via dims
W_SIG, W_PWR = 0.25, 0.5
VIA_D, VIA_DRILL = 0.6, 0.3
VIA_STITCH = 0.6
