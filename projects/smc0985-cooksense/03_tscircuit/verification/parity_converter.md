=== cooksense netlist parity (converter kicad_sch vs sealed 04_kicad) ===
converter nets=160  kicad nets=160
  DIFF 'GND': only_converter=[('R_WDPETPD', '2')] only_kicad=[]
  DIFF 'WD_PET': only_converter=[('R_WDPETPD', '1')] only_kicad=[]
  NO-CONNECT DIFF: only_converter=[] only_kicad=[('J_KEY_MATRIX', 'MP')]
connected nodes: converter=728 kicad=726   no-connects: converter=31 kicad=32
REAL DISCREPANCIES: 3  ->  FAIL
