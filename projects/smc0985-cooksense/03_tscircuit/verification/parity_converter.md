=== cooksense netlist parity (converter kicad_sch vs sealed 04_kicad) ===
input: netlist = /home/mouse9911/gits/circuits/projects/smc0985-cooksense/03_tscircuit/verification/converter_netlist.net
input: board   = /home/mouse9911/gits/circuits/projects/smc0985-cooksense/04_kicad/cooksense.kicad_pcb
converter nets=167  kicad nets=169
  DIFF '3V3': only_converter=[('R_WDOKPD', '1'), ('R_WDOKSER', '1'), ('TP_WDOK', '1'), ('U_AND1', '3'), ('U_CAND1', '1'), ('U_EXP', '18'), ('U_FAULTAND', '1'), ('U_OENAND', '2'), ('U_ONESHOT', '11'), ('U_WD', '1')] only_kicad=[]
  DIFF 'FAULT': only_converter=[('R_OPTOLED', '2'), ('U_OPTO', '1')] only_kicad=[]
  DIFF 'OPTO_LED_A': only_converter=[] only_kicad=[('R_OPTOLED', '2'), ('U_OPTO', '1')]
  DIFF 'WD_OK': only_converter=[] only_kicad=[('R_WDOKPD', '1'), ('R_WDOKSER', '1'), ('TP_WDOK', '1'), ('U_AND1', '3'), ('U_CAND1', '1'), ('U_EXP', '18'), ('U_FAULTAND', '1'), ('U_OENAND', '2'), ('U_ONESHOT', '11'), ('U_WD', '1')]
  NO-CONNECT DIFF: only_converter=[] only_kicad=[('J_KEY_MATRIX', 'MP')]
connected nodes: converter=787 kicad=787   no-connects: converter=29 kicad=30
REAL DISCREPANCIES: 5/169 nets  ->  FAIL
