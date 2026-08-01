#include <stdio.h>
#include <string.h>
#include <inttypes.h>

#include "hardware/clocks.h"
#include "hardware/dma.h"
#include "hardware/irq.h"
#include "hardware/pio.h"
#include "hardware/sync.h"
#include "pico/stdlib.h"

#include "rx2_core.h"
#include "switch_seq.pio.h"

#define SELECT_PIN_BASE 0u
#define STATUS_LED_PIN 4u
#define LINE_CAPACITY 160u

static PIO seq_pio = pio0;
static uint seq_sm;
static uint seq_offset;
static int seq_dma = -1;
static uint32_t schedule[RX2_STATE_COUNT] __attribute__((aligned(32)));
static struct rx2_status status;
static float actual_sample_rate_hz;
static volatile uint32_t observed_frame_count;
static volatile uint32_t observed_transition_count;
static volatile uint8_t observed_selected_state;

static void selector_write(uint8_t code)
{
    gpio_put_masked(0x0fu << SELECT_PIN_BASE,
                    ((uint32_t)code & 0x0fu) << SELECT_PIN_BASE);
}

static void sequence_irq(void)
{
    if (pio_interrupt_get(seq_pio, 0u)) {
        pio_interrupt_clear(seq_pio, 0u);
        observed_transition_count++;
        observed_selected_state =
            (uint8_t)((observed_selected_state + 1u) % RX2_STATE_COUNT);
        if (observed_selected_state == 0u)
            observed_frame_count++;
    }
}

static void sequence_stop(void)
{
    bool was_running = status.running;

    if (seq_dma >= 0)
        dma_channel_abort((uint)seq_dma);
    pio_sm_set_enabled(seq_pio, seq_sm, false);
    pio_sm_clear_fifos(seq_pio, seq_sm);
    pio_interrupt_clear(seq_pio, 0u);
    if (was_running) {
        status.frame_count = observed_frame_count;
        status.transition_count = observed_transition_count;
        status.selected_state = observed_selected_state;
    }
    rx2_stop(&status);
}

static void sequence_reconfigure(void)
{
    float divider = (float)clock_get_hz(clk_sys) /
                    (float)status.config.sample_rate_hz;
    uint32_t div_fixed = (uint32_t)(divider * 256.0f + 0.5f);
    for (uint8_t state = 0; state < RX2_STATE_COUNT; ++state)
        schedule[state] = rx2_schedule_word(&status.config, state);
    pio_sm_set_clkdiv_int_frac(seq_pio, seq_sm,
                               (uint16_t)(div_fixed >> 8),
                               (uint8_t)(div_fixed & 0xffu));
    actual_sample_rate_hz = (float)clock_get_hz(clk_sys) * 256.0f /
                            (float)div_fixed;
}

static void sequence_start(void)
{
    sequence_stop();
    sequence_reconfigure();
    status.frame_count = 0u;
    status.transition_count = 0u;
    rx2_start(&status);
    observed_frame_count = 0u;
    observed_transition_count = 0u;
    observed_selected_state = 0u;

    /* STOP can leave the SM in the dwell loop.  Reset its execution state and
     * PC so every RUN begins by pulling schedule[0], never by finishing a
     * stale dwell from the preceding run. */
    pio_sm_restart(seq_pio, seq_sm);
    pio_sm_exec(seq_pio, seq_sm, pio_encode_jmp(seq_offset));

    dma_channel_config config = dma_channel_get_default_config((uint)seq_dma);
    channel_config_set_transfer_data_size(&config, DMA_SIZE_32);
    channel_config_set_read_increment(&config, true);
    channel_config_set_write_increment(&config, false);
    /* Pico SDK's boolean selects the address side: false = READ.  The TX FIFO
     * write address is fixed; the eight-word schedule READ address must wrap.
     * Ringing the write side leaves the DMA reading beyond schedule[7]. */
    channel_config_set_ring(&config, false, 5u); /* 8 words x 4 bytes */
    channel_config_set_dreq(&config, pio_get_dreq(seq_pio, seq_sm, true));
    dma_channel_configure((uint)seq_dma, &config, &seq_pio->txf[seq_sm],
                          schedule, UINT32_MAX, true);
    pio_sm_set_enabled(seq_pio, seq_sm, true);
}

static void print_status(void)
{
    uint32_t irq_state = save_and_disable_interrupts();
    uint32_t frames = status.running ? observed_frame_count
                                     : status.frame_count;
    uint32_t transitions = status.running ? observed_transition_count
                                          : status.transition_count;
    uint8_t selected = status.running ? observed_selected_state
                                      : status.selected_state;
    restore_interrupts(irq_state);

    printf("OK running=%u muted=%u state=%u frame=%lu transitions=%lu "
           "sample_rate_req=%lu sample_rate_actual=%.3f blank=%lu "
           "ordinary_clean=%lu reference_clean=%lu frame_samples=%lu "
           "sync=FREE_RUNNING\n",
           status.running, status.muted,
           status.muted ? 0u : (unsigned)selected + 1u,
           (unsigned long)frames,
           (unsigned long)transitions,
           (unsigned long)status.config.sample_rate_hz,
           (double)actual_sample_rate_hz,
           (unsigned long)status.config.blank_samples,
           (unsigned long)status.config.ordinary_clean_samples,
           (unsigned long)status.config.reference_clean_samples,
           (unsigned long)rx2_frame_samples(&status.config));
}

static void handle_line(char *line)
{
    unsigned state;
    struct rx2_config next;

    if (!strcmp(line, "INFO?")) {
        puts("OK product=pluto-rx2-8way-v4 protocol=RX2CTL/1 "
             "mcu=RP2040-Zero transport=USB-CDC");
    } else if (!strcmp(line, "STATUS?")) {
        print_status();
    } else if (sscanf(line, "SELECT %u", &state) == 1) {
        sequence_stop();
        if (!state || !rx2_select(&status, (uint8_t)(state - 1u))) {
            puts("ERR BAD_STATE expected=1..8");
            return;
        }
        selector_write(rx2_gpio_code(status.selected_state));
        print_status();
    } else if (!strcmp(line, "OFF")) {
        sequence_stop();
        rx2_mute(&status);
        selector_write(RX2_ALL_OFF_GPIO_CODE);
        print_status();
    } else if (!strcmp(line, "RUN")) {
        sequence_start();
        print_status();
    } else if (!strcmp(line, "STOP")) {
        sequence_stop();
        print_status();
    } else if (sscanf(line, "CONFIG %" SCNu32 " %" SCNu32 " %" SCNu32
                      " %" SCNu32,
                      &next.sample_rate_hz,
                      &next.ordinary_clean_samples,
                      &next.reference_clean_samples,
                      &next.blank_samples) == 4) {
        sequence_stop();
        if (!rx2_set_config(&status, &next)) {
            puts("ERR BAD_CONFIG");
            return;
        }
        sequence_reconfigure();
        print_status();
    } else if (!strcmp(line, "ZERO_COUNTERS")) {
        uint32_t irq_state = save_and_disable_interrupts();
        status.frame_count = 0u;
        status.transition_count = 0u;
        observed_frame_count = 0u;
        observed_transition_count = 0u;
        restore_interrupts(irq_state);
        print_status();
    } else {
        puts("ERR BAD_COMMAND");
    }
}

int main(void)
{
    char line[LINE_CAPACITY];
    size_t used = 0u;

    stdio_init_all();
    rx2_status_init(&status);
    for (uint pin = SELECT_PIN_BASE; pin < SELECT_PIN_BASE + 4u; ++pin) {
        gpio_init(pin);
        gpio_set_dir(pin, GPIO_OUT);
    }
    gpio_init(STATUS_LED_PIN);
    gpio_set_dir(STATUS_LED_PIN, GPIO_OUT);
    selector_write(rx2_gpio_code(0u));

    seq_sm = pio_claim_unused_sm(seq_pio, true);
    seq_offset = pio_add_program(seq_pio, &switch_seq_program);
    pio_sm_config config = switch_seq_program_get_default_config(seq_offset);
    sm_config_set_out_pins(&config, SELECT_PIN_BASE, 4u);
    sm_config_set_out_shift(&config, true, false, 32u);
    pio_sm_set_consecutive_pindirs(seq_pio, seq_sm, SELECT_PIN_BASE, 4u, true);
    pio_sm_init(seq_pio, seq_sm, seq_offset, &config);
    seq_dma = dma_claim_unused_channel(true);
    pio_set_irq0_source_enabled(seq_pio, pis_interrupt0, true);
    irq_set_exclusive_handler(PIO0_IRQ_0, sequence_irq);
    irq_set_enabled(PIO0_IRQ_0, true);
    sequence_reconfigure();

    puts("OK boot product=pluto-rx2-8way-v4 state=1 sync=FREE_RUNNING");
    while (true) {
        int ch = getchar_timeout_us(1000u);
        gpio_put(STATUS_LED_PIN, status.running);
        if (ch == PICO_ERROR_TIMEOUT)
            continue;
        if (ch == '\r')
            continue;
        if (ch == '\n') {
            line[used] = '\0';
            if (used)
                handle_line(line);
            used = 0u;
        } else if (used + 1u < sizeof(line)) {
            line[used++] = (char)ch;
        } else {
            used = 0u;
            puts("ERR LINE_TOO_LONG");
        }
    }
}
