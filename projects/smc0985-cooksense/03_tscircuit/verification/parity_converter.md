=== cooksense netlist parity (converter kicad_sch vs sealed 04_kicad) ===
input: netlist = /home/mouse9911/gits/circuits/projects/smc0985-cooksense/03_tscircuit/verification/converter_netlist.net
input: board   = /home/mouse9911/gits/circuits/projects/smc0985-cooksense/04_kicad/cooksense.kicad_pcb
converter nets=171  kicad nets=169
  DIFF '5V_RPP': only_converter=[('C_EFIN', '1')] only_kicad=[]
  DIFF 'DOOR_RAW': only_converter=[('R_DOORS', '2')] only_kicad=[('D_DOOR', '1'), ('J_DOOR', '2'), ('J_DOOR', '4'), ('R_DOORPD', '1')]
  DIFF 'DOOR_RAW_IN': only_converter=[('D_DOOR', '1'), ('J_DOOR', '2'), ('R_DOORPD', '1'), ('R_DOORS', '1')] only_kicad=[]
  DIFF 'ESTOP_RAW': only_converter=[('R_ESTOPS', '2')] only_kicad=[('D_ESTOP', '1'), ('J_ESTOP', '2'), ('R_ESTOPPD', '1')]
  DIFF 'ESTOP_RAW_IN': only_converter=[('D_ESTOP', '1'), ('J_ESTOP', '2'), ('R_ESTOPPD', '1'), ('R_ESTOPS', '1')] only_kicad=[]
  DIFF 'GND': only_converter=[('C_EFIN', '2'), ('J_DOOR', '4')] only_kicad=[]
  NO-CONNECT DIFF: only_converter=[] only_kicad=[('J_KEY_MATRIX', 'MP')]
connected nodes: converter=793 kicad=787   no-connects: converter=29 kicad=30
REAL DISCREPANCIES: 7/171 nets  ->  FAIL
