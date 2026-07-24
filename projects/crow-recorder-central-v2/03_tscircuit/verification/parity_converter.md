=== crow_recorder_central_v2 netlist parity (converter kicad_sch vs sealed 04_kicad) ===
converter nets=115  kicad nets=116
  DIFF '0V9': only_converter=[('C_c10', '1'), ('C_c11', '1'), ('C_c12', '1'), ('C_c13', '1'), ('C_c9', '1')] only_kicad=[]
  DIFF 'AUDIO4M': only_converter=[('F4', '2'), ('J6', '4'), ('J6', '7')] only_kicad=[]
  DIFF 'GND': only_converter=[('C_c10', '2'), ('C_c11', '2'), ('C_c12', '2'), ('C_c13', '2'), ('C_c9', '2'), ('J10', 'SH'), ('J3', 'SH'), ('J4', 'SH'), ('J5', 'SH'), ('J6', 'SH'), ('J7', 'SH'), ('J8', 'SH'), ('J9', 'SH')] only_kicad=[]
  DIFF 'P5VA_4': only_converter=[] only_kicad=[('F4', '2'), ('J6', '4'), ('J6', '7')]
connected nodes: converter=606 kicad=588   no-connects: converter=146 kicad=146
REAL DISCREPANCIES: 4  ->  FAIL
