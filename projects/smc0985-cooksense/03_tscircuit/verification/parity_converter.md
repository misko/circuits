=== cooksense netlist parity (converter kicad_sch vs sealed 04_kicad) ===
input: netlist = /home/mouse9911/gits/circuits/projects/smc0985-cooksense/03_tscircuit/verification/converter_netlist.net
input: board   = /home/mouse9911/gits/circuits/projects/smc0985-cooksense/04_kicad/cooksense.kicad_pcb
converter nets=169  kicad nets=164
  DIFF '3V3': only_converter=[('C_OS', '2'), ('R_OS', '1'), ('U_ONESHOT', '15')] only_kicad=[]
  DIFF 'DOOR_OK': only_converter=[('R_DOOROKSER', '1')] only_kicad=[('U_EXP', '4')]
  DIFF 'DOOR_OK_EXP': only_converter=[('R_DOOROKSER', '2'), ('U_EXP', '4')] only_kicad=[]
  DIFF 'EFUSE_FLT_DIV': only_converter=[('R_FLTDIVB', '1'), ('R_FLTDIVT', '2'), ('U_EXP', '1')] only_kicad=[]
  DIFF 'EFUSE_FLT_N': only_converter=[('R_FLTDIVT', '1')] only_kicad=[('U_EXP', '1')]
  DIFF 'ESTOP_OK': only_converter=[('R_ESTOPOKSER', '1')] only_kicad=[('U_EXP', '3')]
  DIFF 'ESTOP_OK_EXP': only_converter=[('R_ESTOPOKSER', '2'), ('U_EXP', '3')] only_kicad=[]
  DIFF 'FAULT': only_converter=[('R_FAULTSER', '1')] only_kicad=[('U_EXP', '6')]
  DIFF 'FAULT_EXP': only_converter=[('R_FAULTSER', '2'), ('U_EXP', '6')] only_kicad=[]
  DIFF 'GND': only_converter=[('R_FLTDIVB', '2')] only_kicad=[]
  DIFF 'MODE_AUTO_HW': only_converter=[('R_MODEHWSER', '1')] only_kicad=[('U_EXP', '2')]
  DIFF 'MODE_AUTO_HW_EXP': only_converter=[('R_MODEHWSER', '2'), ('U_EXP', '2')] only_kicad=[]
  DIFF 'OS_RC': only_converter=[] only_kicad=[('C_OS', '2'), ('R_OS', '1'), ('U_ONESHOT', '15')]
  DIFF 'TEMP_OK': only_converter=[('R_TEMPOKSER', '1')] only_kicad=[('U_EXP', '5')]
  DIFF 'TEMP_OK_EXP': only_converter=[('R_TEMPOKSER', '2'), ('U_EXP', '5')] only_kicad=[]
  NO-CONNECT DIFF: only_converter=[] only_kicad=[('J_KEY_MATRIX', 'MP')]
connected nodes: converter=791 kicad=777   no-connects: converter=29 kicad=30
REAL DISCREPANCIES: 16/170 nets  ->  FAIL
