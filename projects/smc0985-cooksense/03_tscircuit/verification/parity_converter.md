=== cooksense netlist parity (converter kicad_sch vs sealed 04_kicad) ===
converter nets=161  kicad nets=160
  DIFF '3V3': only_converter=[] only_kicad=[('R_DOORPU', '2')]
  DIFF '3V3_ANALOG': only_converter=[('C_COMP', '1'), ('C_COMP2', '1'), ('R_OPENT', '1'), ('U_COMP', '8'), ('U_COMP2', '8')] only_kicad=[]
  DIFF '5V_PROTECTED': only_converter=[] only_kicad=[('C_COMP', '1'), ('U_COMP', '8')]
  DIFF 'CONTACTOR_C': only_converter=[('J_ESTOPLOOP', '1')] only_kicad=[('J_ESTOP', '3')]
  DIFF 'CONTACTOR_LOOP': only_converter=[('J_ESTOPLOOP', '2')] only_kicad=[('J_ESTOP', '4')]
  DIFF 'DOOR_RAW': only_converter=[('R_DOORPD', '1')] only_kicad=[('R_DOORPU', '1')]
  DIFF 'GND': only_converter=[('C_COMP2', '2'), ('J_ESTOP', '3'), ('J_ESTOP', '4'), ('R_CLMPA', '2'), ('R_CLMPB', '2'), ('R_DOORPD', '2'), ('R_OPENB', '2'), ('U_COMP2', '4')] only_kicad=[]
  DIFF 'TCAM_OPEN': only_converter=[('R_OPENB', '1'), ('R_OPENT', '2'), ('U_COMP2', '3'), ('U_COMP2', '5')] only_kicad=[]
  DIFF 'TEMP_OK': only_converter=[('U_COMP2', '1'), ('U_COMP2', '7')] only_kicad=[]
  DIFF 'TH_CAM_A': only_converter=[('R_CLMPA', '1'), ('U_COMP2', '2')] only_kicad=[]
  DIFF 'TH_CAM_B': only_converter=[('R_CLMPB', '1'), ('U_COMP2', '6')] only_kicad=[]
  NO-CONNECT DIFF: only_converter=[] only_kicad=[('J_KEY_MATRIX', 'MP')]
connected nodes: converter=748 kicad=728   no-connects: converter=31 kicad=32
REAL DISCREPANCIES: 12  ->  FAIL
