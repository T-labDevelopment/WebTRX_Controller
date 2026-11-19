#ifndef WTRX_ROTARY_EVENT_H
#define WTRX_ROTARY_EVENT_H
/*
 * Portable, hardware-independent quadrature/one-detent event module.
 * One full A/B sequence (four valid Gray transitions) gives +1 or -1.
 * EC12E2420801 has 24 pulses and 24 mechanical detents per revolution.
 * Verify final direction and detent phase on the real encoder.
 */
#include <stdint.h>

#define ROTARY_EVENT_QUEUE_CAPACITY 64

typedef struct {
    uint8_t previousAB;
    int8_t edgeBalance;
} RotaryDecoder;

typedef struct {
    int8_t direction[ROTARY_EVENT_QUEUE_CAPACITY];
    uint8_t readIndex;
    uint8_t writeIndex;
    uint8_t count;
    uint16_t droppedEvents;
} RotaryEventQueue;

static void rotaryDecoder_init(RotaryDecoder *d, uint8_t initialAB) {
    d->previousAB = initialAB & 3;
    d->edgeBalance = 0;
}

static int8_t rotaryDecoder_update(RotaryDecoder *d, uint8_t ab) {
    static const int8_t table[16] = {
       0, 1,-1, 0,
      -1, 0, 0, 1,
       1, 0, 0,-1,
       0,-1, 1, 0
    };
    uint8_t prev = d->previousAB;
    int8_t delta;
    ab &= 3;
    d->previousAB = ab;
    if ((prev ^ ab) == 3) { /* invalid two-bit Gray-code leap */
        d->edgeBalance = 0;
        return 0;
    }
    delta = table[(prev << 2) | ab];
    if (delta == 0) return 0;
    d->edgeBalance += delta;
    if (d->edgeBalance >= 4) {
        d->edgeBalance = 0;
        return 1;
    }
    if (d->edgeBalance <= -4) {
        d->edgeBalance = 0;
        return -1;
    }
    return 0;
}

static void rotaryQueue_init(RotaryEventQueue *q) {
    q->readIndex = 0;
    q->writeIndex = 0;
    q->count = 0;
    q->droppedEvents = 0;
}

static uint8_t rotaryQueue_push(RotaryEventQueue *q, int8_t dir) {
    if (dir != 1 && dir != -1) return 0;
    if (q->count >= ROTARY_EVENT_QUEUE_CAPACITY) {
        ++q->droppedEvents;
        return 0;
    }
    q->direction[q->writeIndex] = dir;
    q->writeIndex = (uint8_t)((q->writeIndex + 1) % ROTARY_EVENT_QUEUE_CAPACITY);
    ++q->count;
    return 1;
}

static int8_t rotaryQueue_front(const RotaryEventQueue *q) {
    if (q->count == 0) return 0;
    return q->direction[q->readIndex];
}

static void rotaryQueue_pop(RotaryEventQueue *q) {
    if (q->count == 0) return;
    q->readIndex = (uint8_t)((q->readIndex + 1) % ROTARY_EVENT_QUEUE_CAPACITY);
    --q->count;
}
#endif
