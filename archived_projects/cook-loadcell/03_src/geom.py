"""cook-loadcell shared geometry (mm, y-down). 55 x 45 2-layer."""
X0, Y0, X1, Y1 = 20.0, 20.0, 75.0, 65.0

HOLES = [(23.5, 23.5), (71.5, 23.5), (23.5, 61.5), (71.5, 61.5)]

# analog corner = W half; digital/power = SE
ANALOG_RECT = (20.0, 26.0, 44.0, 58.0)   # bridge nodes + INA + VFB live here
DIG_MIN_SEP = 4.0                        # DAT/CLK copper to BRIDGE copper

W_SIG, W_PWR, W_BRIDGE = 0.25, 0.4, 0.5
VIA_D, VIA_DRILL = 0.6, 0.3
