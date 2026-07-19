"""Shared board geometry — single source for generate_board.py, route_bank.py,
route_prep.py, stitch_and_fill.py, audit_board.py.

All mm, board frame (y-down). Derivations: 01_docs/DETAIL_DESIGN.md,
ADR-0002 (isolation numbers). ISO_MIN = 6.0mm creepage/clearance (§6.3).
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

# contact corridor lane x-offsets from CONT_X (ADR-0002: all EAST, <=2.0)
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
FAN_Y0, FAN_Y1 = 33.6, 46.4     # E-W lane band (16 lanes x 0.8)
FAN_PITCH = 0.8

# iso comb (keypad-copper region, for keepouts/audit): north strip + corridors
STRIP_RECT = (68.0, 21.0, 203.0, 50.5)           # x0,y0,x1,y1
CORR_Y1 = 95.0                                   # corridors reach row1 pin8+
CORR_HALF_W = 2.7                                # x_c-0.5 .. x_c+2.7 span

# SELV keep-back (planes / KRT / floaters): 6mm beyond the comb
NOGO = (60.0, Y0, X1, 101.0)   # x0,y0,x1,y1 — no SELV copper here except
                               # the sanctioned coil-column verticals
COIL_V_X = -1.3                # RELAY_5V vertical offset (F.Cu) from COIL_X
COIL_L_B = -1.3                # COIL_(2k-1) vertical offset (B.Cu)
COIL_L_I2 = -1.3               # COIL_(2k) vertical offset (In2.Cu)

R5V_BUS_Y = 101.8              # RELAY_5V F.Cu bus (west of bank -> Q1)
COIL_LANE_Y0 = 103.0           # In2/B.Cu E-W coil lanes band start
COIL_LANE_PITCH = 0.7

# ---------------- SELV floorplan anchors ----------------
PICO_XY = (42.0, 84.0)         # J2 socket center; rows x = +-8.89
ULN1_XY = (98.0, 108.5)        # U5 (drives K1-K8, west corridors)
ULN2_XY = (158.0, 108.5)       # U6 (K9-K16)
SR1_XY = (84.0, 121.0)         # U3 74HC595 #1
SR2_XY = (144.0, 121.0)        # U4 #2
WD_XY = (63.0, 108.0)          # U7 LVC1G123
GATE_XY = (63.0, 116.0)        # U8 NAND / U9 AND3 cluster
Q1_XY = (56.0, 101.8)          # high-side PFET on the bus line
TC_XY = (31.0, 33.0)           # U1 MAX31856 (NW analog corner)

# mounting holes (NPTH 3.2mm; nylon standoffs)
HOLES = [(24.0, 24.0), (201.0, 24.5), (24.0, 128.0), (201.0, 128.0),
         (24.0, 62.0), (120.0, 128.0)]

# KRT keepouts (User.2): iso comb + margin + relay bank + strip
KRT_KEEPOUTS = [
    (60.0, Y0, X1, 101.2),          # whole bank + strip + margin (hand-routed)
]

# track/via dims
W_SIG, W_PWR, W_COIL = 0.3, 0.6, 0.4
VIA_D, VIA_DRILL = 0.6, 0.3
VIA_STITCH = 0.6
