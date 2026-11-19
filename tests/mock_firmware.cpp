/* Standalone host simulation of the ACTUAL Arduino .ino source.
 * A temporary stub USB header is supplied by test_firmware_mock.py.
 * This is not a CH552 binary compile or physical USB test. */
#include <cassert>
#include <cstdint>
#include <vector>
#include <cstdio>

#define USER_USB_RAM 1
#define INPUT_PULLUP 2
#define LOW 0
#define HIGH 1
static unsigned long fakeTime=0;
static unsigned char abState=0;
static unsigned char heldPins[64]={};
struct Report { unsigned long time; unsigned char button; int axis; };
static std::vector<Report> reports;
static std::vector<unsigned char> keydowns;
static std::vector<unsigned char> keyups;
static unsigned busRejects=0;
unsigned long millis(){return fakeTime;}
void pinMode(unsigned char, int){}
int digitalRead(unsigned char pin){
  if(pin==14) return (abState & 2) ? HIGH : LOW;
  if(pin==15) return (abState & 1) ? HIGH : LOW;
  return heldPins[pin] ? LOW : HIGH;
}
void USBInit(void){}
void Keyboard_press(unsigned char key){keydowns.push_back(key);}
void Keyboard_release(unsigned char key){keyups.push_back(key);}
unsigned char Gamepad_setState(unsigned char buttons,signed char axis){
  if(busRejects){--busRejects;return 0;}
  reports.push_back({fakeTime,buttons,(int)axis});
  return 1;
}

#include "ch552_gamepad_keyboard.ino"

static void advance(unsigned duration){
  for(unsigned i=0;i<duration;i++){fakeTime++; loop();}
}
static void sendClick(bool positive, bool service=true) {
  const unsigned char cw[]={1,3,2,0};
  const unsigned char ccw[]={2,3,1,0};
  const unsigned char *s=positive?cw:ccw;
  for(unsigned i=0;i<4;i++) {
    abState=s[i]; if(service) loop(); else pollEncoder();
  }
}
int main(){
  setup();
  advance(20); // initial neutral report
  assert(reports.size()==1 && reports[0].axis==0);
  busRejects=2; // transient endpoint busy: no pulses may be consumed
  sendClick(true);
  sendClick(true);
  sendClick(false);
  assert(pendingSteps.count==3);
  advance(270);
  assert(pendingSteps.count==0);
  std::vector<int> values;
  for(const auto &r:reports) values.push_back(r.axis);
  const std::vector<int> expected={0,0,127,0,0,127,0,0,-127,0};
  assert(values==expected);
  // Each counted edge must have a fresh neutral report BEFORE full scale.
  for(size_t i=2;i<reports.size();i+=3){
    assert(reports[i-1].axis==0);
    assert(reports[i].axis==127 || reports[i].axis==-127);
    assert(reports[i].time-reports[i-1].time>=DIAL_NEUTRAL_MS);
  }
  for(size_t i=3;i<reports.size();i+=3){
    assert(reports[i].axis==0);
    assert(reports[i].time-reports[i-1].time>=DIAL_ACTIVE_MS);
  }
  heldPins[BTN_F1_PIN]=1;
  advance(BUTTON_DEBOUNCE_MS+2);
  assert(keydowns.size()==1 && keydowns[0]==KEYMAP_F1);
  heldPins[BTN_F1_PIN]=0;
  advance(BUTTON_DEBOUNCE_MS+2);
  assert(keyups.size()==1 && keyups[0]==KEYMAP_F1);
  // 24 clockwise detents produce 24 independent +127/0 pairs.
  reports.clear();
  for(int i=0;i<24;i++) sendClick(true,false);
  assert(pendingSteps.count==24);
  advance(24*(DIAL_ACTIVE_MS+DIAL_NEUTRAL_MS+GAMEPAD_REFRESH_MS)+200);
  assert(pendingSteps.count==0);
  unsigned asserted=0,neutral=0;
  int previous=0;
  for(size_t i=0;i<reports.size();++i){
    const auto &r=reports[i];
    if(r.axis==127){
      assert(i>0 && reports[i-1].axis==0); // 0 sent BEFORE +127
      assert(r.time-reports[i-1].time>=DIAL_NEUTRAL_MS);
      asserted++;
    }
    if(r.axis==0 && previous==127)neutral++;
    previous=r.axis;
  }
  assert(asserted==24 && neutral==24);
  assert(reports.size()==72); // 3 reports for each click: 0 / +127 / 0
  std::puts("PASS: firmware mocked USB 1-click=0->+/-127, idle reset, busy retry, buttons, 24-detent rotation");
}
