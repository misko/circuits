=== cooksense netlist parity (converter kicad_sch vs sealed 04_kicad) ===
input: netlist = /home/mouse9911/gits/circuits/projects/smc0985-cooksense/03_tscircuit/verification/converter_netlist.net
input: board   = /home/mouse9911/gits/circuits/projects/smc0985-cooksense/04_kicad/cooksense.kicad_pcb
converter nets=163  kicad nets=163
  DIFF '3V3': only_converter=[('R_AND1PD', '1'), ('U_AND1', '4'), ('U_AND3', '1')] only_kicad=[]
  DIFF 'AND1': only_converter=[] only_kicad=[('R_AND1PD', '1'), ('U_AND1', '4'), ('U_AND3', '1')]
  DIFF 'WD_OK': only_converter=[('R_WDOKSER', '1')] only_kicad=[('U_EXP', '8')]
  DIFF 'WD_OK_EXP': only_converter=[('R_WDOKSER', '2'), ('U_EXP', '8')] only_kicad=[]
  NO-CONNECT DIFF: only_converter=[] only_kicad=[('J_KEY_MATRIX', 'MP')]
connected nodes: converter=777 kicad=775   no-connects: converter=29 kicad=30
REAL DISCREPANCIES: 5/164 nets  ->  FAIL
