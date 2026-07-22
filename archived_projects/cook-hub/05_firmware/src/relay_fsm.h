/* Relay/keypad state machine skeleton — spec §6.7/§11.3/§11.4 contract.
 * Compact interface contract, NOT an implementation.                     */
#ifndef COOK_HUB_RELAY_FSM_H
#define COOK_HUB_RELAY_FSM_H
#include <stdbool.h>
#include <stdint.h>

/* §11.4 local fault hierarchy, highest priority first. Any fault at or
 * above the current state's tolerance releases ALL relays (§1.8). */
typedef enum {
    FAULT_ESTOP = 1,          /* hardware also cut the coil rail        */
    FAULT_HW_WATCHDOG = 2,    /* WD_OK dropped: /OE + rail dead in HW   */
    FAULT_DOOR_OPEN = 3,      /* during programming/start sequence      */
    FAULT_PI_HEARTBEAT = 4,   /* >500ms-1s without PKT_HEARTBEAT        */
    FAULT_HUB_INTERNAL = 5,
    FAULT_BAD_COMMAND = 6,    /* whitelist / CRC / state mismatch       */
    FAULT_SENSOR_STALE = 7,
    FAULT_NONE_COMPLETE = 8,  /* normal command completion              */
} fault_t;

typedef enum {
    RS_BOOT = 0,      /* §11.1: OE off, rail gate off, SR zeroed        */
    RS_SAFE,          /* sensors up, relays locked out                  */
    RS_READY,         /* heartbeat healthy, RLY_EN may assert           */
    RS_ARMED,         /* command accepted + ACKed, awaiting actuation   */
    RS_PRESSING,      /* ONE relay closed, hold timer running (<=500ms) */
    RS_COOLDOWN,      /* inter-key gap >=100ms (§6.7)                   */
    RS_FAULT,         /* latched; E-stop recovery needs operator ack    */
} relay_state_t;

/* invariants enforced by the implementation (test hooks assert these):
 *  - at most ONE relay bit set in the 74HC595 chain, ever (§6.7);
 *  - hold clamped to [50,500] ms; sequence max 32 presses;
 *  - STOP_REQUEST preempts everything below FAULT_DOOR_OPEN;
 *  - any protocol error / heartbeat loss / door / E-stop => release all,
 *    RLY_EN low, shift chain zeroed, then re-latch;
 *  - RS_FAULT from FAULT_ESTOP exits only on explicit operator ack pkt. */

void relay_fsm_init(void);
bool relay_fsm_submit(const void *relay_cmd /* relay_cmd_t */);
void relay_fsm_fault(fault_t f);
void relay_fsm_tick_1ms(void);
relay_state_t relay_fsm_state(void);
#endif
