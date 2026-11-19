/*
 * WebTRX RC-28 style controller / CH552T keyboard-only prototype.
 * Firmware proof of concept; NOT composite HID / NOT validated on hardware.
 * CH55xDuino 0.0.26 + Generic_Examples/05.USB/HidKeyboard USB source.
 * Target board: WeAct CH552 Core Board V1.0; P3.6 and RST reserved.
 *
 * Source directory requirement:
 *   src/userUsbHidKeyboard/USBHIDKeyboard.h (plus sibling sources)
 * Must be copied from the same CH55xDuino version.
 */
#ifndef USER_USB_RAM
#error "Select USER USB setting for CH55xDuino"
#endif
#include "src/userUsbHidKeyboard/USBHIDKeyboard.h"

#define ENC_A_PIN 14    /* P1.4 */
#define ENC_B_PIN 15    /* P1.5 */
#define F1_PIN    16    /* P1.6 */
#define F2_PIN    17    /* P1.7 */
#define PTT_PIN   32    /* P3.2 */

/* Test-only key map. NOT a verified WebTRX hotkey map. */
#define KEY_DIAL_CW   'e'
#define KEY_DIAL_CCW  'q'
#define KEY_F1        '1'
#define KEY_F2        '2'
#define KEY_PTT       'p'
#define REVERSE_DIAL   0
#define BUTTON_DEBOUNCE_MS  15UL
#define KEY_PULSE_MS         30UL
#define KEY_GAP_MS          10UL
#define DIAL_QUEUE_MAX       64

/* Gray-code 4x decoder: CW is 00,01,11,10,00 (depending on wiring). */
static const signed char qdec[16] = {
    0,  1, -1,  0,
   -1,  0,  0,  1,
    1,  0,  0, -1,
    0, -1,  1,  0
};
static unsigned char lastAB = 0;
static signed char quarter = 0;
static signed char dialQueue = 0;   /* -64..+64 pending key pulses */
static unsigned char pulsePhase = 0; /* 0 idle; 1 pressed; 2 released gap */
static unsigned char activePulseKey = 0;
static unsigned long pulseSince = 0;

typedef struct {
    unsigned char pin;
    unsigned char key;
    unsigned char rawPressed;
    unsigned char stablePressed;
    unsigned long changedAt;
} Button;
static Button buttons[3] = {
    {F1_PIN,  KEY_F1, 0, 0, 0},
    {F2_PIN,  KEY_F2, 0, 0, 0},
    {PTT_PIN, KEY_PTT,0, 0, 0}
};

static void pollButtons(unsigned long now) {
    unsigned char i;
    for (i = 0; i < 3; ++i) {
        Button *b = &buttons[i];
        unsigned char raw = (digitalRead(b->pin) == LOW);
        if (raw != b->rawPressed) {
            b->rawPressed = raw;
            b->changedAt = now;
        }
        if ((now - b->changedAt) >= BUTTON_DEBOUNCE_MS &&
            b->stablePressed != b->rawPressed) {
            b->stablePressed = b->rawPressed;
            if (b->stablePressed) Keyboard_press(b->key);
            else Keyboard_release(b->key);
        }
    }
}

static void pollEncoder(void) {
    unsigned char ab = (digitalRead(ENC_A_PIN) ? 2 : 0) |
                       (digitalRead(ENC_B_PIN) ? 1 : 0);
    signed char step = qdec[(lastAB << 2) | ab];
    lastAB = ab;
#if REVERSE_DIAL
    step = -step;
#endif
    if (!step) return;
    quarter += step;
    if (quarter >= 4) {
        quarter = 0;
        if (dialQueue < DIAL_QUEUE_MAX) ++dialQueue;
    } else if (quarter <= -4) {
        quarter = 0;
        if (dialQueue > -DIAL_QUEUE_MAX) --dialQueue;
    }
}

/* No delay(): continuously sample A/B phase even during USB key pulses. */
static void sendQueuedDialPulses(unsigned long now) {
    if (pulsePhase == 1) {
        if ((now - pulseSince) >= KEY_PULSE_MS) {
            Keyboard_release(activePulseKey);
            pulseSince = now;
            pulsePhase = 2;
        }
        return;
    }
    if (pulsePhase == 2) {
        if ((now - pulseSince) >= KEY_GAP_MS) pulsePhase = 0;
        return;
    }
    if (dialQueue) {
        activePulseKey = (dialQueue > 0) ? KEY_DIAL_CW : KEY_DIAL_CCW;
        if (dialQueue > 0) --dialQueue;
        else ++dialQueue;
        Keyboard_press(activePulseKey);
        pulseSince = now;
        pulsePhase = 1;
    }
}

void setup(void) {
    unsigned char i;
    pinMode(ENC_A_PIN, INPUT_PULLUP);
    pinMode(ENC_B_PIN, INPUT_PULLUP);
    pinMode(F1_PIN, INPUT_PULLUP);
    pinMode(F2_PIN, INPUT_PULLUP);
    pinMode(PTT_PIN, INPUT_PULLUP);
    lastAB = (digitalRead(ENC_A_PIN) ? 2 : 0) |
             (digitalRead(ENC_B_PIN) ? 1 : 0);
    for (i = 0; i < 3; ++i) {
        /* Only transitions after startup are emitted. */
        buttons[i].rawPressed = (digitalRead(buttons[i].pin) == LOW);
        buttons[i].stablePressed = buttons[i].rawPressed;
        buttons[i].changedAt = 0;
    }
    USBInit();
}
void loop(void) {
    unsigned long now = millis();
    pollEncoder();
    pollButtons(now);
    sendQueuedDialPulses(now);
}
