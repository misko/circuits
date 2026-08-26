#ifndef PHUB_STARTUP_H
#define PHUB_STARTUP_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

/*
 * Platform binding for the release-critical startup sequence. PMBus word
 * callbacks accept host-order uint16_t values; the STM32 binding must put the
 * low byte on the wire first. USB2517 callbacks implement SMBus Block
 * Read/Write, including the byte-count field required by DS00001598C.
 */
typedef struct {
    void *context;
    void (*set_external_safe)(void *context);
    void (*set_run_hold)(void *context, uint8_t channel, bool asserted);
    void (*set_hub_reset)(void *context, bool asserted);
    bool (*read_power_good)(void *context, uint8_t channel);
    void (*delay_ms)(void *context, uint32_t delay_ms);
    int (*pmbus_write_byte)(void *context, uint8_t address, uint8_t command,
                            uint8_t value);
    int (*pmbus_read_byte)(void *context, uint8_t address, uint8_t command,
                           uint8_t *value);
    int (*pmbus_write_word)(void *context, uint8_t address, uint8_t command,
                            uint16_t value);
    int (*pmbus_read_word)(void *context, uint8_t address, uint8_t command,
                           uint16_t *value);
    int (*hub_block_write)(void *context, uint8_t address, uint8_t reg,
                           const uint8_t *data, size_t length);
    int (*hub_block_read)(void *context, uint8_t address, uint8_t reg,
                          uint8_t *data, size_t length);
} phub_startup_hal_t;

typedef enum {
    PHUB_STARTUP_OK = 0,
    PHUB_STARTUP_BAD_HAL = -1,
    PHUB_STARTUP_LTC_IO = -2,
    PHUB_STARTUP_LTC_VERIFY = -3,
    PHUB_STARTUP_POWER_GOOD = -4,
    PHUB_STARTUP_HUB_IO = -5,
    PHUB_STARTUP_HUB_VERIFY = -6
} phub_startup_result_t;

enum {
    PHUB_LTC_GLOBAL_ADDRESS = 0x5A,
    PHUB_LTC_DEVICE_ADDRESS = 0x4F,
    PHUB_USB2517_ADDRESS = 0x2C,
    PHUB_LTC_VOUT_COMMAND = 0x14DC,
    PHUB_LTC_IOUT_CAL_GAIN = 0xD280,
    PHUB_LTC_IOUT_OC_LIMIT = 0xCBC0,
    PHUB_LTC_FREQUENCY = 0xF3E8
};

phub_startup_result_t phub_startup_run(const phub_startup_hal_t *hal);

/* Test/diagnostic helper: decode a PMBus Linear11 word to milli-units. */
int32_t phub_linear11_milli(uint16_t word);

#endif
