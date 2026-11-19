#ifndef WTRX_CONTROLLER_CONFIG_H
#define WTRX_CONTROLLER_CONFIG_H
/*
 * WebTRX Dial Controller RevA (WeAct CH552 Core Board V1.0)
 * CH55xDuino 0.0.26 / USB gamepad + keyboard experimental firmware.
 * EC12E2420801 24-detent encoder; ONE full-scale axis pulse per click.
 * USB VID:PID 1209:0001 is ONLY permitted for private in-house testing.
 * Must obtain an allocated VID/PID before distribution or production.
 */
#define ENC_A_PIN 14       /* P1.4 */
#define ENC_B_PIN 15       /* P1.5 */
#define BTN_F1_PIN 16      /* P1.6 */
#define BTN_F2_PIN 17      /* P1.7 */
#define BTN_PTT_PIN 32     /* P3.2 */

#define ENCODER_REVERSE 0  /* swap the clockwise/counter-clockwise sign */
/* One EC12E2420801 mechanical click = +127/-127 then zero.
 * Timing must be tuned against WebTRX Gamepad API sampling on real hardware.
 * 35ms high + 25ms neutral = ~16.7 detent-events/s maximum drain rate.
 */
#define DIAL_ACTIVE_MS 35UL
#define DIAL_NEUTRAL_MS 25UL
#define BUTTON_DEBOUNCE_MS 12UL
#define GAMEPAD_REFRESH_MS 10UL

/* Per-switch output: 0 = keyboard key (default), 1 = gamepad button. */
#define F1_AS_GAMEPAD_BUTTON 0
#define F2_AS_GAMEPAD_BUTTON 0
#define PTT_AS_GAMEPAD_BUTTON 0
/* Values understood by CH55xDuino's Keyboard_press/release API. */
#define KEYMAP_F1 '1'
#define KEYMAP_F2 '2'
#define KEYMAP_PTT 'p'
/* Button positions on the gamepad report: 1, 2, 3. */
#define GAMEPAD_F1_MASK 0x01
#define GAMEPAD_F2_MASK 0x02
#define GAMEPAD_PTT_MASK 0x04
#endif
