/*
 * WebTRX Dial Controller RevA / CH552T
 * USB HID (Report ID 1 keyboard, Report ID 2 joystick/gamepad).
 * Requires patched CH55xDuino 0.0.26 HidKeyboardMouse example USB sources:
 *    python tools/prepare_firmware.py <path-to-HidKeyboardMouse-example>
 * Then open this .ino with the board configured for USER CODE USB RAM.
 *
 * NOTICE: Not built, flashed, enumerated, or tested with WebTRX yet.
 */
#ifndef USER_USB_RAM
#error "CH55xDuino Tools > USB Settings must select USER CODE USB RAM"
#endif
#include "config.h"
#include "src/userUsbHidKeyboardMouse/USBHIDKeyboardMouse.h"

static const signed char quadrature[16] = {
     0,  1, -1,  0,
    -1,  0,  0,  1,
     1,  0,  0, -1,
     0, -1,  1,  0
};
static unsigned char lastAB;
static signed char phaseAccumulator;
static signed char dialAxis;
static unsigned char gamepadButtons;
static unsigned char lastSentButtons;
static signed char lastSentAxis;
static unsigned long lastDetentMs;
static unsigned long lastGamepadSentMs;
static unsigned char hadDetent;

/* Switch input, HID keyboard mapping, and gamepad routing configuration. */
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

static signed char axisValue(unsigned long interval) {
  unsigned long numerator;
  if (interval <= AXIS_MIN_INTERVAL_MS) return AXIS_MAX_VALUE;
  if (interval >= AXIS_MAX_INTERVAL_MS) return AXIS_MIN_VALUE;
  numerator = (AXIS_MAX_INTERVAL_MS - interval) *
              (AXIS_MAX_VALUE - AXIS_MIN_VALUE);
  return (signed char)(AXIS_MIN_VALUE +
       numerator / (AXIS_MAX_INTERVAL_MS - AXIS_MIN_INTERVAL_MS));
}

static void onRotaryDetent(signed char dir, unsigned long now) {
  signed char value;
#if ENCODER_REVERSE
  dir = -dir;
#endif
  /* Initial event uses medium sensitivity until a velocity is known. */
  value = hadDetent ? axisValue(now - lastDetentMs) : 64;
  hadDetent = 1;
  lastDetentMs = now;
  dialAxis = (dir > 0) ? value : -value;
}

static void pollEncoder(unsigned long now) {
  unsigned char ab = readEncoder();
  signed char delta = quadrature[(lastAB << 2) | ab];
  lastAB = ab;
  if (!delta) return;
  phaseAccumulator += delta;
  if (phaseAccumulator >= ROTARY_EDGES_PER_STEP) {
    phaseAccumulator = 0;
    onRotaryDetent(1, now);
  } else if (phaseAccumulator <= -ROTARY_EDGES_PER_STEP) {
    phaseAccumulator = 0;
    onRotaryDetent(-1, now);
  }
}

static void pollButtons(unsigned long now) {
  unsigned char i;
  for (i = 0; i < 3; i++) {
    SwitchInput *b = &switches[i];
    unsigned char isPressed = (digitalRead(b->pin) == LOW);
    if (isPressed != b->rawPressed) {
      b->rawPressed = isPressed;
      b->lastChangeMs = now;
    }
    if (isPressed == b->stablePressed ||
        (now - b->lastChangeMs) < BUTTON_DEBOUNCE_MS) continue;
    b->stablePressed = isPressed;
    if (b->routeGamepad) {
      if (isPressed) gamepadButtons |= b->mask;
      else gamepadButtons &= ~b->mask;
    } else {
      if (isPressed) Keyboard_press(b->key);
      else Keyboard_release(b->key);
    }
  }
}

static void sendGamepad(unsigned long now) {
  if ((now - lastGamepadSentMs) < GAMEPAD_REFRESH_MS) return;
  lastGamepadSentMs = now;
  if (dialAxis == lastSentAxis && gamepadButtons == lastSentButtons) return;
  /* Important: If USB transfer fails, retry the state change next time. */
  if (Gamepad_setState(gamepadButtons, dialAxis)) {
    lastSentAxis = dialAxis;
    lastSentButtons = gamepadButtons;
  }
}

void setup(void) {
  unsigned char i;
  pinMode(ENC_A_PIN, INPUT_PULLUP);
  pinMode(ENC_B_PIN, INPUT_PULLUP);
  lastAB = readEncoder();
  phaseAccumulator = 0;
  dialAxis = 0;
  gamepadButtons = 0;
  lastSentAxis = 127; /* force 0-axis report after enumeration */
  lastSentButtons = 255;
  hadDetent = 0;
  lastGamepadSentMs = millis();
  lastDetentMs = millis();
  for (i = 0; i < 3; i++) {
    SwitchInput *b = &switches[i];
    pinMode(b->pin, INPUT_PULLUP);
    b->rawPressed = (digitalRead(b->pin) == LOW);
    b->stablePressed = b->rawPressed; /* no initial keydown */
    b->lastChangeMs = millis();
  }
  USBInit();
}
void loop(void) {
  unsigned long now = millis();
  pollEncoder(now);
  pollButtons(now);
  /* A joystick axis is absolute. Simulate spring return after idle. */
  if (dialAxis && (now - lastDetentMs) >= AXIS_ZERO_HOLD_MS) {
    dialAxis = 0;
    hadDetent = 0;
  }
  sendGamepad(now);
}
