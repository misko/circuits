"""Shared board geometry constants — single source for generate_board.py,
route_prep.py, route_channels.py, stitch_and_fill.py, audit_board.py.

All coordinates in mm, board frame (y-down). Derivations in
01_docs/DETAIL_DESIGN.md #1 and ADR-0002.
"""

# board outline
X0, Y0, X1, Y1 = 50.0, 50.0, 215.0, 114.0

# port slices
NPORT = 6
PITCH = 19.0
CX = [107.0 + PITCH * i for i in range(NPORT)]      # slice centers

# per-slice vertical geometry
STUD_Y = 57.0            # J1..J6 M4 stud centers
SHUNT_X, SHUNT_Y = -2.0, 74.0   # RS offset (rel cx), pads at y 71.535 / 76.465
FUSE_Y = 89.0            # F1..F6 centers; pad2 pair y 82.25, pad1 pair y 95.75
INA_X, INA_Y = 6.0, 63.5        # U1..U6 (rot 180): west col x +3.9, east col x +8.1
RP_Y, RN_Y = 72.55, 71.5  # filter R centers (rot 90: pad1 south=tap side)
RP_X, RN_X = 4.9, 6.9     # pad2 (north) of each IS its net's column x
TAP_P_Y, TAP_N_Y = 75.6, 72.5   # Kelvin tap rows (shunt pad inner edges)
CD_X, CD_Y = 5.9, 68.5   # diff cap rot 0: pads bridge the KA/KB verticals
CB_X, CB_Y = 8.9, 59.85  # INA bypass (rot 90: pad1 south + stub to the 3V3 rail)

# power pours (F.Cu unless noted)
VP_POUR = (-7.25, 3.25, 51.8, 71.5)    # x0,x1 (rel cx), y0,y1 — 10.5mm wide
VF_POUR = (-7.25, 3.25, 76.5, 84.5)
TRUNK_F = [(66.0, 103.0), (97.0, 103.0), (97.0, 93.5), (208.0, 93.5),
           (208.0, 111.5), (66.0, 111.5)]           # VBUS F.Cu (with west strip)
TRUNK_B = [(97.0, 93.5), (208.0, 93.5), (208.0, 111.5), (97.0, 111.5)]
GND_F = [(50.0, 50.0), (99.4, 50.0), (99.4, 93.2), (97.0, 93.2),
         (97.0, 102.7), (66.0, 102.7), (66.0, 114.0), (50.0, 114.0)]

# corridor lanes (B.Cu, full-width E-W under the slices)
LANE_SDA, LANE_SCL, LANE_ALERT, LANE_3V3 = 66.2, 67.0, 67.8, 68.6
LANE_W = {"SDA": 0.30, "SCL": 0.30, "ALERT": 0.30, "3V3": 0.50}
# west lane terminations: boundary parts (pad1 south at y 64.06, rot 90)
BOUND_X = {"SDA": 93.1, "SCL": 90.9, "ALERT": 88.7, "3V3": 86.5}  # 2.2 pitch (0805 rot-90 courtyard is 2.04 wide)
BOUND_Y = 63.1           # R15/R16/R17/C14 centers
BOUND_PAD1_Y = 64.06     # R15/16/17 pad1 (lane-terminal via-in-pad) y
# C14 is FLIPPED (rot 270): its 3V3 pad1 sits NORTH at 62.14 and is fed by a
# hand bus over R15/16/17 pad2 (all 3V3); its GND pad2 (south) gets a via.
BOUND_3V3_PAD1_Y = 62.1425
BOUND_3V3_PAD2_Y = 64.0575

# in-slice signal columns (x rel cx) and vias
COL_A1, COL_A0, COL_ALERT, COL_SDA, COL_SCL, COL_3V3 = 8.1, 9.2, 9.8, 10.4, 11.0, 11.6
# (east INA pads span x 7.35-8.85: only A1 may run inside that band — straight
#  south from its own pad; every other column clears 8.85+0.15)
GND_BAND_Y = 65.3        # A-strap GND via y (B.Cu plane band between pads+lanes)
V3_NORTH_Y = 61.9        # 3V3 F.Cu horizontal (north of INA, clears stud pad + pad row)
PAD7_VIA = (4.2, 63.0)   # GND via-in-pad at INA pad7
CB_GND_VIA = None  # via-in-pad at CB pad2 (computed in route_channels)
KA_COL, KB_COL = 4.9, 6.9   # tap verticals = RP/RN pad2 x (inter-pad channel)
PAD8_JOG_X = 5.8            # VBUS pin (pad8) ties to KB (IN-) via this jog

# Kelvin attach points (rel cx) — pad inner edges (audit I-KELVIN)
KP_ATTACH = (-2.0, 75.6)   # inside shunt pad1 (south pad), near north edge
KN_ATTACH = (-2.0, 72.5)   # inside shunt pad2 (north pad), near south edge
KELVIN_AREA = (-5.5, 7.5, 68.5, 78.8)  # named rule area (x0,x1,y0,y1 rel cx)

# track/via dims
W_SIG, W_EPWR, W_TAP = 0.30, 0.50, 0.40
VIA_D, VIA_DRILL = 0.56, 0.30      # cluster vias (JLC 2oz: annular 0.13)
VIA_STITCH = 0.60                  # GND stitch vias

# electronics anchors (world coords) — see generate_board.py ANCHOR
MODULE_XY = (68.0, 61.0)           # U7, rot 90 (antenna west)
ANT_KEEPOUT = (50.0, 61.2, 50.0, 75.3)   # module's own embedded keepout zone + margin
STUD_IN = (151.0, 105.8)           # J7 M5 (+12-24V)
STUD_GND = (58.0, 107.0)           # J8 M4 (GND ref)

# mounting holes (NPTH 3.2mm)
HOLES = [(52.3, 93.0), (211.0, 52.8), (211.0, 111.2), (98.0, 84.0)]

# KRT keepouts (User.2)
KRT_KEEPOUTS = [
    (98.2, 50.0, 215.0, 114.0),    # everything east (slices+trunk+corridor)
    (86.0, 64.6, 98.2, 69.2),      # corridor strip west portion
    (64.0, 102.6, 96.0, 114.0),    # trunk west strip
    (50.0, 50.0, 61.2, 75.3),      # antenna keepout (module-embedded zone)
]
