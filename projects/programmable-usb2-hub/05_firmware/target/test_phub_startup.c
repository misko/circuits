#include "phub_startup.h"

#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

typedef struct {
    bool run_hold[2];
    bool hub_reset;
    bool power_good[2];
    bool hub_attached;
    unsigned safe_calls;
    uint8_t ltc_address;
    uint8_t page;
    uint8_t byte_reg[2][256];
    uint16_t word_reg[2][256];
    uint8_t hub_reg[256];
    int corrupt_ltc_page;
    int corrupt_ltc_command;
    int corrupt_hub_reg;
} mock_t;

static void set_external_safe(void *context) { ((mock_t *)context)->safe_calls++; }
static void set_run_hold(void *context, uint8_t ch, bool hold) { ((mock_t *)context)->run_hold[ch] = hold; }
static void set_hub_reset(void *context, bool reset) { ((mock_t *)context)->hub_reset = reset; }
static bool read_power_good(void *context, uint8_t ch) { return ((mock_t *)context)->power_good[ch]; }
static void delay_ms(void *context, uint32_t delay) { (void)context; (void)delay; }

static int pmbus_write_byte(void *context, uint8_t address, uint8_t command, uint8_t value)
{
    mock_t *m = context;
    if (address == PHUB_LTC_GLOBAL_ADDRESS && command == 0xE6) {
        m->ltc_address = value;
        return 0;
    }
    if (address != m->ltc_address)
        return -1;
    if (command == 0x00)
        m->page = value;
    m->byte_reg[m->page][command] = value;
    return 0;
}

static int pmbus_read_byte(void *context, uint8_t address, uint8_t command, uint8_t *value)
{
    mock_t *m = context;
    if (address != m->ltc_address)
        return -1;
    *value = command == 0x00 ? m->page : m->byte_reg[m->page][command];
    if ((int)m->page == m->corrupt_ltc_page && command == m->corrupt_ltc_command)
        *value ^= 1;
    return 0;
}

static int pmbus_write_word(void *context, uint8_t address, uint8_t command, uint16_t value)
{
    mock_t *m = context;
    if (address != m->ltc_address)
        return -1;
    m->word_reg[m->page][command] = value;
    return 0;
}

static int pmbus_read_word(void *context, uint8_t address, uint8_t command, uint16_t *value)
{
    mock_t *m = context;
    if (address != m->ltc_address)
        return -1;
    *value = m->word_reg[m->page][command];
    if ((int)m->page == m->corrupt_ltc_page && command == m->corrupt_ltc_command)
        *value ^= 1;
    return 0;
}

static int hub_block_write(void *context, uint8_t address, uint8_t reg,
                           const uint8_t *data, size_t length)
{
    mock_t *m = context;
    if (address != PHUB_USB2517_ADDRESS || length == 0 || length > 32)
        return -1;
    memcpy(&m->hub_reg[reg], data, length);
    if (reg == 0xFF && length == 1)
        m->hub_attached = (data[0] & 1u) != 0;
    return 0;
}

static int hub_block_read(void *context, uint8_t address, uint8_t reg,
                          uint8_t *data, size_t length)
{
    mock_t *m = context;
    if (address != PHUB_USB2517_ADDRESS || length == 0 || length > 32)
        return -1;
    memcpy(data, &m->hub_reg[reg], length);
    if (m->corrupt_hub_reg >= (int)reg &&
        m->corrupt_hub_reg < (int)(reg + length))
        data[m->corrupt_hub_reg - reg] ^= 1;
    return 0;
}

static phub_startup_hal_t make_hal(mock_t *mock)
{
    phub_startup_hal_t hal = {
        mock, set_external_safe, set_run_hold, set_hub_reset,
        read_power_good, delay_ms, pmbus_write_byte, pmbus_read_byte,
        pmbus_write_word, pmbus_read_word, hub_block_write, hub_block_read
    };
    return hal;
}

static mock_t make_mock(void)
{
    mock_t mock;
    memset(&mock, 0, sizeof(mock));
    mock.power_good[0] = true;
    mock.power_good[1] = true;
    mock.corrupt_ltc_page = -1;
    mock.corrupt_ltc_command = -1;
    mock.corrupt_hub_reg = -1;
    return mock;
}

static void test_success(void)
{
    mock_t mock = make_mock();
    phub_startup_hal_t hal = make_hal(&mock);
    assert(phub_startup_run(&hal) == PHUB_STARTUP_OK);
    assert(mock.ltc_address == PHUB_LTC_DEVICE_ADDRESS);
    assert(!mock.run_hold[0] && !mock.run_hold[1]);
    assert(!mock.hub_reset && mock.hub_attached);
    assert(mock.word_reg[0][0x21] == PHUB_LTC_VOUT_COMMAND);
    assert(mock.word_reg[1][0x38] == PHUB_LTC_IOUT_CAL_GAIN);
    assert(mock.word_reg[1][0x46] == PHUB_LTC_IOUT_OC_LIMIT);
    assert(mock.byte_reg[0][0x47] == 0xC0);
    assert(mock.hub_reg[0x06] == 0x9B);
    assert(mock.hub_reg[0x09] == 0x20);
    assert(mock.hub_reg[0x0A] == 0xC0);
}

static void test_ltc_mismatch_is_safe(void)
{
    mock_t mock = make_mock();
    phub_startup_hal_t hal = make_hal(&mock);
    mock.corrupt_ltc_page = 1;
    mock.corrupt_ltc_command = 0x46;
    assert(phub_startup_run(&hal) == PHUB_STARTUP_LTC_VERIFY);
    assert(mock.run_hold[0] && mock.run_hold[1]);
    assert(mock.hub_reset && !mock.hub_attached);
}

static void test_hub_mismatch_is_safe(void)
{
    mock_t mock = make_mock();
    phub_startup_hal_t hal = make_hal(&mock);
    mock.corrupt_hub_reg = 0x0A;
    assert(phub_startup_run(&hal) == PHUB_STARTUP_HUB_VERIFY);
    assert(mock.run_hold[0] && mock.run_hold[1]);
    assert(mock.hub_reset && !mock.hub_attached);
    assert(mock.safe_calls == 2);
}

static void test_missing_power_good_is_safe(void)
{
    mock_t mock = make_mock();
    phub_startup_hal_t hal = make_hal(&mock);
    mock.power_good[1] = false;
    assert(phub_startup_run(&hal) == PHUB_STARTUP_POWER_GOOD);
    assert(mock.run_hold[0] && mock.run_hold[1]);
    assert(mock.hub_reset && !mock.hub_attached);
}

int main(void)
{
    assert(phub_linear11_milli(PHUB_LTC_IOUT_CAL_GAIN) == 10000);
    assert(phub_linear11_milli(PHUB_LTC_IOUT_OC_LIMIT) == 7500);
    assert(phub_linear11_milli(PHUB_LTC_FREQUENCY) == 250000);
    test_success();
    test_ltc_mismatch_is_safe();
    test_hub_mismatch_is_safe();
    test_missing_power_good_is_safe();
    puts("phub_startup: PASS");
    return 0;
}
