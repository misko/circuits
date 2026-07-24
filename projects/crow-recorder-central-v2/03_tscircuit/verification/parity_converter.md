=== crow_recorder_central_v2 netlist parity (converter kicad_sch vs sealed 04_kicad) ===
converter nets=114  kicad nets=116
  DIFF '5V': only_converter=[('Cc2P', '2'), ('Rs2P', '1')] only_kicad=[]
  DIFF 'AUDIO4M': only_converter=[('F4', '2'), ('J6', '4'), ('J6', '7')] only_kicad=[]
  DIFF 'GND': only_converter=[('J10', 'SH'), ('J3', 'SH'), ('J4', 'SH'), ('J5', 'SH'), ('J6', 'SH'), ('J7', 'SH'), ('J8', 'SH'), ('J9', 'SH')] only_kicad=[]
  DIFF 'MID2P': only_converter=[] only_kicad=[('Cc2P', '2'), ('Rs2P', '1')]
  DIFF 'P5VA_4': only_converter=[] only_kicad=[('F4', '2'), ('J6', '4'), ('J6', '7')]
  DIFF 'USB_DM': only_converter=[] only_kicad=[('D_USB', '2'), ('J2', 'A7'), ('J2', 'B7'), ('U1', '59')]
  DIFF 'USB_DN': only_converter=[('D_USB', '2'), ('J2', 'A7'), ('J2', 'B7'), ('U1', '59')] only_kicad=[]
connected nodes: converter=599 kicad=591   no-connects: converter=143 kicad=143
REAL DISCREPANCIES: 7  ->  FAIL
