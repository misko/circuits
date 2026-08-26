#include "phub_startup.h"

#include <string.h>

enum {
    PMBUS_PAGE = 0x00,
    PMBUS_OPERATION = 0x01,
    PMBUS_ON_OFF_CONFIG = 0x02,
    PMBUS_VOUT_COMMAND = 0x21,
    PMBUS_FREQUENCY_SWITCH = 0x33,
    PMBUS_IOUT_CAL_GAIN = 0x38,
    PMBUS_VOUT_OV_FAULT_RESPONSE = 0x41,
    PMBUS_VOUT_UV_FAULT_RESPONSE = 0x45,
    PMBUS_IOUT_OC_FAULT_LIMIT = 0x46,
    PMBUS_IOUT_OC_FAULT_RESPONSE = 0x47,
    PMBUS_OT_FAULT_RESPONSE = 0x50,
    PMBUS_MFR_PWM_MODE = 0xD4,
    PMBUS_MFR_ADDRESS = 0xE6,
    PMBUS_MFR_PWM_CONFIG = 0xF5,
    HUB_STATUS_COMMAND = 0xFF
};

typedef struct {
    uint8_t command;
    uint8_t value;
} byte_setting_t;

typedef struct {
    uint8_t command;
    uint16_t value;
} word_setting_t;

static const byte_setting_t ltc_page_bytes[] = {
    {PMBUS_OPERATION, 0x00},             /* immediate off during setup */
    {PMBUS_ON_OFF_CONFIG, 0x1F},         /* RUN and OPERATION both required */
    {PMBUS_MFR_PWM_MODE, 0x83},          /* high ILIM, 8 V range, forced CCM */
    {PMBUS_IOUT_OC_FAULT_RESPONSE, 0xC0},/* immediate shutdown, no retry */
    {PMBUS_VOUT_OV_FAULT_RESPONSE, 0x80},/* immediate shutdown, no retry */
    {PMBUS_VOUT_UV_FAULT_RESPONSE, 0x80},/* immediate shutdown, no retry */
    {PMBUS_OT_FAULT_RESPONSE, 0x80}      /* immediate shutdown, no retry */
};

static const word_setting_t ltc_page_words[] = {
    {PMBUS_VOUT_COMMAND, PHUB_LTC_VOUT_COMMAND},
    {PMBUS_IOUT_CAL_GAIN, PHUB_LTC_IOUT_CAL_GAIN},
    {PMBUS_IOUT_OC_FAULT_LIMIT, PHUB_LTC_IOUT_OC_LIMIT}
};

/*
 * USB2517 DS00001598C Table 7-1, registers 00h..10h. The standard Microchip
 * silicon VID/PID are retained, strings are disabled, the hub is self-powered,
 * Multi-TT with individual power/OC, port 5 is non-removable/compound, and
 * physical ports 6 and 7 are disabled. Upstream VBUS is sense-only, hence 0 mA.
 */
static const uint8_t usb2517_image[] = {
    0x24, 0x04, 0x17, 0x25, 0x00, 0x01, 0x9B, 0x28, 0x00,
    0x20, 0xC0, 0xC0, 0x00, 0x32, 0x00, 0x32, 0x32
};

static bool hal_valid(const phub_startup_hal_t *hal)
{
    return hal != NULL && hal->set_external_safe != NULL &&
           hal->set_run_hold != NULL && hal->set_hub_reset != NULL &&
           hal->read_power_good != NULL && hal->delay_ms != NULL &&
           hal->pmbus_write_byte != NULL && hal->pmbus_read_byte != NULL &&
           hal->pmbus_write_word != NULL && hal->pmbus_read_word != NULL &&
           hal->hub_block_write != NULL && hal->hub_block_read != NULL;
}

static void force_safe(const phub_startup_hal_t *hal)
{
    hal->set_external_safe(hal->context);
    hal->set_run_hold(hal->context, 0, true);
    hal->set_run_hold(hal->context, 1, true);
    hal->set_hub_reset(hal->context, true);
}

static int checked_write_byte(const phub_startup_hal_t *hal, uint8_t command,
                              uint8_t value)
{
    uint8_t actual = 0;
    if (hal->pmbus_write_byte(hal->context, PHUB_LTC_DEVICE_ADDRESS,
                              command, value) != 0)
        return PHUB_STARTUP_LTC_IO;
    if (hal->pmbus_read_byte(hal->context, PHUB_LTC_DEVICE_ADDRESS,
                             command, &actual) != 0)
        return PHUB_STARTUP_LTC_IO;
    return actual == value ? PHUB_STARTUP_OK : PHUB_STARTUP_LTC_VERIFY;
}

static int checked_write_word(const phub_startup_hal_t *hal, uint8_t command,
                              uint16_t value)
{
    uint16_t actual = 0;
    if (hal->pmbus_write_word(hal->context, PHUB_LTC_DEVICE_ADDRESS,
                              command, value) != 0)
        return PHUB_STARTUP_LTC_IO;
    if (hal->pmbus_read_word(hal->context, PHUB_LTC_DEVICE_ADDRESS,
                             command, &actual) != 0)
        return PHUB_STARTUP_LTC_IO;
    return actual == value ? PHUB_STARTUP_OK : PHUB_STARTUP_LTC_VERIFY;
}

static int configure_ltc(const phub_startup_hal_t *hal)
{
    size_t i;
    uint8_t page;
    int result;

    /* Global addressing is write-only; open ASEL pins make all seven bits live. */
    if (hal->pmbus_write_byte(hal->context, PHUB_LTC_GLOBAL_ADDRESS,
                              PMBUS_MFR_ADDRESS,
                              PHUB_LTC_DEVICE_ADDRESS) != 0)
        return PHUB_STARTUP_LTC_IO;

    result = checked_write_word(hal, PMBUS_FREQUENCY_SWITCH,
                                PHUB_LTC_FREQUENCY);
    if (result != PHUB_STARTUP_OK)
        return result;
    result = checked_write_byte(hal, PMBUS_MFR_PWM_CONFIG, 0x00);
    if (result != PHUB_STARTUP_OK)
        return result; /* channel 0 = 0 degrees, channel 1 = 180 degrees */

    for (page = 0; page < 2; ++page) {
        result = checked_write_byte(hal, PMBUS_PAGE, page);
        if (result != PHUB_STARTUP_OK)
            return result;
        for (i = 0; i < sizeof(ltc_page_bytes) / sizeof(ltc_page_bytes[0]); ++i) {
            result = checked_write_byte(hal, ltc_page_bytes[i].command,
                                        ltc_page_bytes[i].value);
            if (result != PHUB_STARTUP_OK)
                return result;
        }
        for (i = 0; i < sizeof(ltc_page_words) / sizeof(ltc_page_words[0]); ++i) {
            result = checked_write_word(hal, ltc_page_words[i].command,
                                        ltc_page_words[i].value);
            if (result != PHUB_STARTUP_OK)
                return result;
        }
        result = checked_write_byte(hal, PMBUS_OPERATION, 0x80);
        if (result != PHUB_STARTUP_OK)
            return result; /* still held off by the external RUN clamp */
    }
    return PHUB_STARTUP_OK;
}

static int configure_hub(const phub_startup_hal_t *hal)
{
    uint8_t readback[sizeof(usb2517_image)];
    const uint8_t attach = 0x01;

    /* RESET rising edge latches CFG_SEL=001; the hub waits unattached. */
    hal->set_hub_reset(hal->context, false);
    hal->delay_ms(hal->context, 2);
    if (hal->hub_block_write(hal->context, PHUB_USB2517_ADDRESS, 0x00,
                             usb2517_image, sizeof(usb2517_image)) != 0)
        return PHUB_STARTUP_HUB_IO;
    if (hal->hub_block_read(hal->context, PHUB_USB2517_ADDRESS, 0x00,
                            readback, sizeof(readback)) != 0)
        return PHUB_STARTUP_HUB_IO;
    if (memcmp(readback, usb2517_image, sizeof(readback)) != 0)
        return PHUB_STARTUP_HUB_VERIFY;
    if (hal->hub_block_write(hal->context, PHUB_USB2517_ADDRESS,
                             HUB_STATUS_COMMAND, &attach, 1) != 0)
        return PHUB_STARTUP_HUB_IO;
    return PHUB_STARTUP_OK;
}

phub_startup_result_t phub_startup_run(const phub_startup_hal_t *hal)
{
    int result;

    if (!hal_valid(hal))
        return PHUB_STARTUP_BAD_HAL;
    force_safe(hal);
    result = configure_ltc(hal);
    if (result != PHUB_STARTUP_OK)
        goto fail;

    hal->set_run_hold(hal->context, 0, false);
    hal->set_run_hold(hal->context, 1, false);
    hal->delay_ms(hal->context, 20);
    if (!hal->read_power_good(hal->context, 0) ||
        !hal->read_power_good(hal->context, 1)) {
        result = PHUB_STARTUP_POWER_GOOD;
        goto fail;
    }

    result = configure_hub(hal);
    if (result != PHUB_STARTUP_OK)
        goto fail;
    return PHUB_STARTUP_OK;

fail:
    force_safe(hal);
    return (phub_startup_result_t)result;
}

int32_t phub_linear11_milli(uint16_t word)
{
    int32_t exponent = (int32_t)((word >> 11) & 0x1F);
    int32_t mantissa = (int32_t)(word & 0x7FF);
    int32_t value = mantissa * 1000;
    if ((exponent & 0x10) != 0)
        exponent -= 32;
    if ((mantissa & 0x400) != 0)
        mantissa -= 2048;
    value = mantissa * 1000;
    if (exponent >= 0)
        return value << exponent;
    return value >> -exponent;
}
