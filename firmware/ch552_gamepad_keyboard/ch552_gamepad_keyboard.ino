/*
 * WebTRX Dial Controller RevA / WeAct CH552 Core Board V1.0
 * USB HID: Report ID 1 = keyboard; Report ID 2 = gamepad X/buttons.
 * EC12E2420801 (24 detents/24 pulses): ONE detent = ONE full-scale
 * signed joystick X pulse (+127 or -127) followed by an X=0 report.
 * The stream is serialized; repeated direction events include neutral gaps.
 * CH55xDuino 0.0.26: patch example first using tools/prepare_firmware.py
 * NOTICE: Not built, flashed, USB enumerated, or tested with WebTRX yet.
 */
#ifndef USER_USB_RAM
#error "CH55xDuino Tools > USB Settings must select USER CODE USB RAM"
#endif
#include "config.h"
#include "rotary_event.h"
#include "src/userUsbHidKeyboardMouse/USBHIDKeyboardMouse.h"

static RotaryDecoder decoder;
static RotaryEventQueue pendingSteps;
static unsigned char gamepadButtons;
static unsigned char lastSentButtons;
static signed char lastSentAxis;
static unsigned long lastGamepadSentMs;
static unsigned long phaseStartedMs;
static signed char activeDirection;

/* The 0 state MUST be successfully sent between successive step pulses. */
enum PulsePhase {
  PULSE_INITIAL_NEUTRAL,
  PULSE_READY,
  PULSE_ASSERT,
  PULSE_HOLD,
  PULSE_RELEASE,
  PULSE_NEUTRAL_GAP
};
static PulsePhase pulsePhase;

typedef struct {
  unsigned char pin;
  unsigned char key;
  unsigned char mask;
  unsigned char routeGamepad;
  unsigned char rawPressed;
  unsigned char stablePressed;
  unsigned long lastChangeMs;
} SwitchInput;
static SwitchInput switches[3] = {
  {BTN_F1_PIN,  KEYMAP_F1,  GAMEPAD_F1_MASK,  F1_AS_GAMEPAD_BUTTON, 0,0,0},
  {BTN_F2_PIN,  KEYMAP_F2,  GAMEPAD_F2_MASK,  F2_AS_GAMEPAD_BUTTON, 0,0,0},
  {BTN_PTT_PIN, KEYMAP_PTT, GAMEPAD_PTT_MASK,PTT_AS_GAMEPAD_BUTTON,0,0,0}
};

static unsigned char readEncoder(void) {
  return (digitalRead(ENC_A_PIN) ? 2 : 0) |
         (digitalRead(ENC_B_PIN) ? 1 : 0);
}

static void pollEncoder(void) {
  int8_t step = rotaryDecoder_update(&decoder, readEncoder());
#if ENCODER_REVERSE
  step = -step;
#endif
  if (step != 0) {
    /* Preserve the order of all detected clicks, even during rapid turns.
     * The queue is bounded; droppedEvents tracks overflow for diagnosis. */
    (void)rotaryQueue_push(&pendingSteps, step);
  }
}

static void pollButtons(unsigned long now) {
  unsigned char i;
  for (i = 0; i < 3; ++i) {
    SwitchInput *b = &switches[i];
    unsigned char pressed = (digitalRead(b->pin) == LOW);
    if (pressed != b->rawPressed) {
      b->rawPressed = pressed;
      b->lastChangeMs = now;
    }
    if (pressed == b->stablePressed ||
        (now - b->lastChangeMs) < BUTTON_DEBOUNCE_MS) continue;
    b->stablePressed = pressed;
    if (b->routeGamepad) {
      if (pressed) gamepadButtons |= b->mask;
      else gamepadButtons &= (unsigned char)~b->mask;
    } else {
      if (pressed) Keyboard_press(b->key);
      else Keyboard_release(b->key);
    }
  }
}

/* Return 1 only when the required state is already sent or the USB
 * library accepted a new report. Keep retrying on a busy endpoint. */
static unsigned char sendGamepadState(signed char axis, unsigned long now) {
  if (axis == lastSentAxis && gamepadButtons == lastSentButtons) return 1;
  if ((now - lastGamepadSentMs) < GAMEPAD_REFRESH_MS) return 0;
  lastGamepadSentMs = now;
  if (!Gamepad_setState(gamepadButtons, axis)) return 0;
  lastSentAxis = axis;
  lastSentButtons = gamepadButtons;
  return 1;
}

static void serviceDialPulse(unsigned long now) {
  switch (pulsePhase) {
  case PULSE_INITIAL_NEUTRAL:
    if (sendGamepadState(0, now)) pulsePhase = PULSE_READY;
    break;
  case PULSE_READY:
    (void)sendGamepadState(0, now); /* update any gamepad-mapped switches */
    if (pendingSteps.count != 0) {
      activeDirection = rotaryQueue_front(&pendingSteps);
      pulsePhase = PULSE_ASSERT;
    }
    break;
  case PULSE_ASSERT:
    if (sendGamepadState(activeDirection > 0 ? 127 : -127, now)) {
      /* Consume click only AFTER successful report submission. */
      rotaryQueue_pop(&pendingSteps);
      phaseStartedMs = now;
      pulsePhase = PULSE_HOLD;
    }
    break;
  case PULSE_HOLD:
    (void)sendGamepadState(activeDirection > 0 ? 127 : -127, now);
    if ((now - phaseStartedMs) >= DIAL_ACTIVE_MS) pulsePhase = PULSE_RELEASE;
    break;
  case PULSE_RELEASE:
    if (sendGamepadState(0, now)) {
      phaseStartedMs = now;
      pulsePhase = PULSE_NEUTRAL_GAP;
    }
    break;
  case PULSE_NEUTRAL_GAP:
    (void)sendGamepadState(0, now);
    if ((now - phaseStartedMs) >= DIAL_NEUTRAL_MS) pulsePhase = PULSE_READY;
    break;
  }
}

void setup(void) {
  unsigned char i;
  pinMode(ENC_A_PIN, INPUT_PULLUP);
  pinMode(ENC_B_PIN, INPUT_PULLUP);
  rotaryDecoder_init(&decoder, readEncoder());
  rotaryQueue_init(&pendingSteps);
  pinMode(BTN_F1_PIN, INPUT_PULLUP);
  pinMode(BTN_F2_PIN, INPUT_PULLUP);
  pinMode(BTN_PTT_PIN, INPUT_PULLUP);
  gamepadButtons = 0;
  lastSentButtons = 255;
  lastSentAxis = 126; /* force initial neutral HID report */
  lastGamepadSentMs = millis();
  phaseStartedMs = millis();
  activeDirection = 0;
  pulsePhase = PULSE_INITIAL_NEUTRAL;
  for (i = 0; i < 3; ++i) {
    SwitchInput *b = &switches[i];
    b->rawPressed = (digitalRead(b->pin) == LOW);
    b->stablePressed = b->rawPressed; /* do not send keydown during boot */
    b->lastChangeMs = millis();
  }
  USBInit();
}

void loop(void) {
  unsigned long now = millis();
  pollEncoder();
  pollButtons(now);
  serviceDialPulse(now);
}
