# cook-hub USB CDC protocol (spec §10) — prose twin of include/protocol.h

Framing: COBS with 0x00 delimiter. Inside each frame:
`pkt_hdr_t (version=1, type, seq, t_us, len) + payload[len] + crc32` —
CRC32 (IEEE) computed over header+payload BEFORE COBS encoding.
Max decoded frame 2048 bytes (THERMAL_FRAME = 1536 payload + 14 hdr + 4).

| type | dir | rate | payload |
|---|---|---|---|
| 0x01 HEARTBEAT | Pi->Pico | 5-10 Hz | uint32 pi_seq |
| 0x02 STATUS | Pico->Pi | 10 Hz | state, fault, door/estop, sensor summary + freshness/error counters (§11.2) |
| 0x03 THERMAL_FRAME | Pico->Pi | 4-8 Hz | 768 x s16 (0.01 C), frame ctr, sensor status flags (§10.5) |
| 0x04 SENSOR_FAULT | Pico->Pi | event | sensor id, fault code, counter |
| 0x05 RELAY_COMMAND | Pi->Pico | on demand | relay_cmd_t (§10.6): cmd_id, whitelisted key_id, hold_ms, req_state, not_after_us |
| 0x06 RELAY_ACK | Pico->Pi | before actuation | cmd_id, accept/reject + reason |
| 0x07 RELAY_COMPLETE | Pico->Pi | after release | cmd_id, actual hold, state |
| 0x08 STOP_REQUEST | Pi->Pico | event | — (highest priority §6.7) |
| 0x09 ESTOP_EVENT | Pico->Pi | event | edge + latched state; recovery needs operator-ack CONFIG |
| 0x0A CONFIG | Pi->Pico | on demand | key timing (50-500ms clamp), thermistor betas (§3.10d), rates; CRC/version stored + reported (§11.5) |
| 0x0B TIME_SYNC | both | 1/min | Pi tx time, Pico rx t_us (offset est. §10.7) |
| 0x0C FIRMWARE_VERSION | Pico->Pi | on boot/req | git sha, config CRC |

Safety rules baked into the transport (§1.6-1.8, §6.6):
- No packet type can address relays by matrix coordinates — only
  whitelisted logical key ids; the Pi-side compiler owns the key map.
- Heartbeat loss 500 ms-1 s: release all keys; the Pico may send
  STOP/CLEAR only if the mapping is known unambiguous, else it releases
  and raises the contactor-drop request (GP15 low = drop).
- Every RELAY_COMMAND is ACKed before actuation and COMPLETEd after
  release; unknown/duplicate cmd_id or a req_state mismatch = reject.
- CRC failure on ANY inbound frame during RS_PRESSING = release (§11.3).
