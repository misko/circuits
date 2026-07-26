=== cooksense netlist parity (converter kicad_sch vs sealed 04_kicad) ===
converter nets=161  kicad nets=161
  DIFF '3V3': only_converter=[] only_kicad=[('R_TEMPOK', '2')]
  DIFF '3V3_ANALOG': only_converter=[('R_TEMPOK', '2')] only_kicad=[]
  NO-CONNECT DIFF: only_converter=[] only_kicad=[('J_KEY_MATRIX', 'MP')]
connected nodes: converter=748 kicad=748   no-connects: converter=31 kicad=32
REAL DISCREPANCIES: 3  ->  FAIL
