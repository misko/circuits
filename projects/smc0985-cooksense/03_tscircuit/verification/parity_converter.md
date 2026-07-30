=== cooksense netlist parity (converter kicad_sch vs sealed 04_kicad) ===
input: netlist = /home/mouse9911/gits/circuits/projects/smc0985-cooksense/03_tscircuit/verification/converter_netlist.net
input: board   = /home/mouse9911/gits/circuits/projects/smc0985-cooksense/04_kicad/cooksense.kicad_pcb
converter nets=167  kicad nets=171
  DIFF '3V3': only_converter=[('J_ESTOP', '2')] only_kicad=[('J_DOOR', '1'), ('J_ESTOP', '1')]
  DIFF 'DOOR_NI': only_converter=[] only_kicad=[('U_SCHM', '10'), ('U_SCHM', '13')]
  DIFF 'DOOR_OK': only_converter=[] only_kicad=[('R_DOOROKPD', '1'), ('R_DOOROKSER', '1'), ('U_OSCLR', '1'), ('U_SCHM', '12')]
  DIFF 'DOOR_OK_EXP': only_converter=[] only_kicad=[('R_DOOROKSER', '2'), ('U_EXP', '4')]
  DIFF 'DOOR_RAW': only_converter=[] only_kicad=[('R_DOORS', '2'), ('U_SCHM', '11')]
  DIFF 'DOOR_RAW_IN': only_converter=[] only_kicad=[('D_DOOR', '1'), ('J_DOOR', '2'), ('R_DOORPD', '1'), ('R_DOORS', '1')]
  DIFF 'ESTOP_OK': only_converter=[('U_OSCLR', '1')] only_kicad=[]
  DIFF 'ESTOP_RAW_IN': only_converter=[('J_ESTOP', '3')] only_kicad=[('J_ESTOP', '2')]
  DIFF 'GND': only_converter=[('J_ESTOP', '1'), ('R_GPB3PD', '1'), ('U_SCHM', '11'), ('U_SCHM', '13')] only_kicad=[('D_DOOR', '2'), ('J_DOOR', '3'), ('J_DOOR', '4'), ('J_DOOR', '5'), ('J_DOOR', 'MP'), ('J_ESTOP', '3'), ('J_ESTOP', '4'), ('J_ESTOP', '5'), ('R_DOOROKPD', '2'), ('R_DOORPD', '2')]
  DIFF 'GPB3_SPARE': only_converter=[('R_GPB3PD', '2'), ('U_EXP', '4')] only_kicad=[]
  NO-CONNECT DIFF: only_converter=[('U_SCHM', '10'), ('U_SCHM', '12')] only_kicad=[('J_KEY_MATRIX', 'MP')]
connected nodes: converter=775 kicad=793   no-connects: converter=31 kicad=30
REAL DISCREPANCIES: 11/172 nets  ->  FAIL
