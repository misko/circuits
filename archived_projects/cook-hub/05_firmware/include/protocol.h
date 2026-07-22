/* cook-hub <-> Pi 5 USB CDC protocol skeleton (spec §10). COBS framing,
 * CRC32 (IEEE, reflected, over header+payload before COBS). This header is
 * the wire CONTRACT; PROTOCOL.md is the prose twin.                      */
#ifndef COOK_HUB_PROTOCOL_H
#define COOK_HUB_PROTOCOL_H
#include <stdint.h>

#define PROTO_VERSION 1

/* §10.3 packet classes */
typedef enum {
    PKT_HEARTBEAT = 0x01,   /* Pi->Pico, 5-10 Hz; loss 500ms-1s => release */
    PKT_STATUS = 0x02,      /* Pico->Pi, 10 Hz: state, faults, sensors     */
    PKT_THERMAL_FRAME = 0x03, /* 768x s16 (0.01 C) + frame ctr + flags     */
    PKT_SENSOR_FAULT = 0x04,
    PKT_RELAY_COMMAND = 0x05, /* see relay_cmd_t; ACK before actuation     */
    PKT_RELAY_ACK = 0x06,
    PKT_RELAY_COMPLETE = 0x07,
    PKT_STOP_REQUEST = 0x08,  /* highest priority (§6.7)                   */
    PKT_ESTOP_EVENT = 0x09,
    PKT_CONFIG = 0x0A,        /* key timing, thermistor beta, rates        */
    PKT_TIME_SYNC = 0x0B,
    PKT_FIRMWARE_VERSION = 0x0C,
} pkt_type_t;

typedef struct __attribute__((packed)) {
    uint8_t version;   /* PROTO_VERSION */
    uint8_t type;      /* pkt_type_t */
    uint16_t seq;
    uint64_t t_us;     /* Pico monotonic timestamp */
    uint16_t len;      /* payload bytes */
    /* payload[len]; uint32_t crc32; then COBS + 0x00 delimiter */
} pkt_hdr_t;

/* §10.6 relay command payload */
typedef struct __attribute__((packed)) {
    uint32_t cmd_id;      /* unique, echoed in ACK/COMPLETE            */
    uint8_t key_id;       /* WHITELISTED logical key, NOT a matrix pos */
    uint16_t hold_ms;     /* clamped to [50,500]; hard max 500 (§11.3) */
    uint8_t req_state;    /* required supervisor state                 */
    uint64_t not_after_us; /* max allowed start time                   */
} relay_cmd_t;

uint32_t crc32_ieee(const uint8_t *d, uint32_t n);
/* COBS: encode/decode, max frame 2048 (thermal frame 1536 + hdr + crc) */
uint32_t cobs_encode(const uint8_t *in, uint32_t n, uint8_t *out);
int32_t cobs_decode(const uint8_t *in, uint32_t n, uint8_t *out);

/* rates (§10.4): status 10Hz, thermal 4-8Hz, SHT 1Hz, TC 5-10Hz,
 * HX711 10Hz, thermistors 2-5Hz, door/E-stop event + status repeat.     */
#endif
