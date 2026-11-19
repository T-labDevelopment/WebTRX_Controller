#include <cassert>
#include <cstdint>
#include <cstdio>
#include "../firmware/ch552_gamepad_keyboard/rotary_event.h"

static int8_t cw(RotaryDecoder *decoder) {
  int8_t events=0;
  const uint8_t seq[]={1,3,2,0};
  for(uint8_t s:seq) events+=rotaryDecoder_update(decoder,s);
  return events;
}
static int8_t ccw(RotaryDecoder *decoder) {
  int8_t events=0;
  const uint8_t seq[]={2,3,1,0};
  for(uint8_t s:seq) events+=rotaryDecoder_update(decoder,s);
  return events;
}
int main() {
  RotaryDecoder d;
  RotaryEventQueue q;
  rotaryDecoder_init(&d,0);
  rotaryQueue_init(&q);
  assert(cw(&d)==+1); // one mechanical click, four Gray transitions
  assert(ccw(&d)==-1);
  for(int i=0;i<24;i++) assert(cw(&d)==1); // 360° at 24 clicks
  for(int i=0;i<24;i++) assert(ccw(&d)==-1);
  assert(rotaryDecoder_update(&d,1)==0);
  assert(rotaryDecoder_update(&d,0)==0); // contact bounce does not count
  assert(rotaryDecoder_update(&d,3)==0); // invalid two-bit Gray transition
  assert(rotaryDecoder_update(&d,0)==0);
  assert(cw(&d)==1);

  assert(rotaryQueue_push(&q,+1)==1);
  assert(rotaryQueue_push(&q,+1)==1);
  assert(rotaryQueue_push(&q,-1)==1);
  assert(q.count==3);
  assert(rotaryQueue_front(&q)==1);rotaryQueue_pop(&q);
  assert(rotaryQueue_front(&q)==1);rotaryQueue_pop(&q);
  assert(rotaryQueue_front(&q)==-1);rotaryQueue_pop(&q);
  assert(rotaryQueue_front(&q)==0);
  assert(q.count==0);
  for(unsigned i=0;i<ROTARY_EVENT_QUEUE_CAPACITY;i++) {
    assert(rotaryQueue_push(&q,(i%2==0)?1:-1)==1);
  }
  assert(rotaryQueue_push(&q,1)==0);
  assert(q.droppedEvents==1);
  for(unsigned i=0;i<ROTARY_EVENT_QUEUE_CAPACITY;i++){
    assert(rotaryQueue_front(&q)==((i%2==0)?1:-1));
    rotaryQueue_pop(&q);
  }
  assert(q.count==0);
  assert(rotaryQueue_push(&q,-1)==1);
  assert(rotaryQueue_front(&q)==-1);
  assert(q.droppedEvents==1);
  std::puts("PASS: rotary quadrature 24-detent and 64-event FIFO host tests");
}
