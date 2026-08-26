=== usb_controlled_debug_hub netlist parity (converter kicad_sch vs sealed 04_kicad) ===
input: netlist = /home/mouse9911/gits/circuits/projects/usb-controlled-debug-hub-v2/03_tscircuit/verification/converter_netlist.net
input: board   = /home/mouse9911/gits/circuits/projects/usb-controlled-debug-hub-v2/04_kicad/usb_controlled_debug_hub.kicad_pcb
converter nets=117  kicad nets=104
  DIFF 'DATA_CC1': only_converter=[('J_DATA', 'A5'), ('R_CC1', '1')] only_kicad=[]
  DIFF 'DATA_CC2': only_converter=[('J_DATA', 'B5'), ('R_CC2', '1')] only_kicad=[]
  DIFF 'GND': only_converter=[('C_PD_IN1', '2'), ('C_PD_IN2', '2'), ('C_PD_IN_HF', '2'), ('C_PD_OUT1', '2'), ('C_PD_OUT2', '2'), ('C_PD_OUT3', '2'), ('C_PD_VDD', '2'), ('D_PD_TVS', '1'), ('J_DATA', 'A1'), ('J_DATA', 'A12'), ('J_DATA', 'B1'), ('J_DATA', 'B12'), ('J_DATA', 'SH'), ('J_POWER', 'A1'), ('J_POWER', 'A12'), ('J_POWER', 'B1'), ('J_POWER', 'B12'), ('J_POWER', 'SH'), ('R_CC1', '2'), ('R_CC2', '2'), ('R_PD_FB_BOT', '2'), ('R_PD_UV_BOT', '2'), ('U_PD', '11'), ('U_PD', '9'), ('U_PD_BUCK', '10'), ('U_PD_BUCK', '3'), ('U_PD_BUCK', '9')] only_kicad=[('J_PWR', '2'), ('J_UP', '4'), ('J_UP', '5')]
  DIFF 'P5V_FUSED': only_converter=[] only_kicad=[('C_AGG_IN', '1'), ('F_IN', '2'), ('R_AGG_UV_TOP', '1'), ('U_AGG', '5')]
  DIFF 'P5V_RAW': only_converter=[] only_kicad=[('F_IN', '1'), ('J_PWR', '1')]
  DIFF 'P5V_REG': only_converter=[('C_AGG_IN', '1'), ('C_PD_OUT1', '1'), ('C_PD_OUT2', '1'), ('C_PD_OUT3', '1'), ('L_PD', '2'), ('R_AGG_UV_TOP', '1'), ('R_PD_FB_A', '1'), ('R_PD_FF', '1'), ('U_AGG', '5')] only_kicad=[]
  DIFF 'PD_BOOT': only_converter=[('C_PD_BOOT', '1'), ('U_PD_BUCK', '7')] only_kicad=[]
  DIFF 'PD_BUCK_EN': only_converter=[('R_PD_UV_BOT', '1'), ('R_PD_UV_TOP', '2'), ('U_PD_BUCK', '1')] only_kicad=[]
  DIFF 'PD_CC1': only_converter=[('J_POWER', 'A5'), ('U_PD', '7')] only_kicad=[]
  DIFF 'PD_CC2': only_converter=[('J_POWER', 'B5'), ('U_PD', '6')] only_kicad=[]
  DIFF 'PD_FB': only_converter=[('C_PD_FF', '2'), ('R_PD_FB_B', '2'), ('R_PD_FB_BOT', '1'), ('U_PD_BUCK', '2')] only_kicad=[]
  DIFF 'PD_FB_TOP': only_converter=[('R_PD_FB_A', '2'), ('R_PD_FB_B', '1')] only_kicad=[]
  DIFF 'PD_FF': only_converter=[('C_PD_FF', '1'), ('R_PD_FF', '2')] only_kicad=[]
  DIFF 'PD_SW': only_converter=[('C_PD_BOOT', '2'), ('L_PD', '1'), ('U_PD_BUCK', '6')] only_kicad=[]
  DIFF 'PD_VBUS_SENSE': only_converter=[('R_PD_VBUS', '2'), ('U_PD', '8')] only_kicad=[]
  DIFF 'PD_VDD': only_converter=[('C_PD_VDD', '1'), ('R_PD_VDD', '2'), ('U_PD', '1'), ('U_PD', '2'), ('U_PD', '3')] only_kicad=[]
  DIFF 'UP_HUB_N': only_converter=[('J_DATA', 'A7'), ('J_DATA', 'B7')] only_kicad=[('J_UP', '2')]
  DIFF 'UP_HUB_P': only_converter=[('J_DATA', 'A6'), ('J_DATA', 'B6')] only_kicad=[('J_UP', '3')]
  DIFF 'USB_UP_VBUS': only_converter=[('J_DATA', 'A4'), ('J_DATA', 'A9'), ('J_DATA', 'B4'), ('J_DATA', 'B9')] only_kicad=[('J_UP', '1')]
  DIFF 'VBUS_PD': only_converter=[('C_PD_IN1', '1'), ('C_PD_IN2', '1'), ('C_PD_IN_HF', '1'), ('D_PD_TVS', '2'), ('F_PD', '2'), ('R_PD_UV_TOP', '1'), ('R_PD_VBUS', '1'), ('R_PD_VDD', '1'), ('U_PD_BUCK', '8')] only_kicad=[]
  DIFF 'VBUS_PD_RAW': only_converter=[('F_PD', '1'), ('J_POWER', 'A4'), ('J_POWER', 'A9'), ('J_POWER', 'B4'), ('J_POWER', 'B9')] only_kicad=[]
  NO-CONNECT DIFF: only_converter=[('J_DATA', 'A8'), ('J_DATA', 'B8'), ('J_POWER', 'A6'), ('J_POWER', 'A7'), ('J_POWER', 'A8'), ('J_POWER', 'B6'), ('J_POWER', 'B7'), ('J_POWER', 'B8'), ('U_PD', '10'), ('U_PD', '4'), ('U_PD', '5'), ('U_PD_BUCK', '4'), ('U_PD_BUCK', '5')] only_kicad=[]
connected nodes: converter=549 kicad=472   no-connects: converter=49 kicad=36
REAL DISCREPANCIES: 22/119 nets  ->  FAIL
