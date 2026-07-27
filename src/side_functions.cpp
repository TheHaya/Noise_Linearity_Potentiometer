#include <Arduino.h>
#include <dxl_servo.h>
#include <calibrate.h>
#include <relay.h>
// --------------- VARIABLES
int32_t user_go_to;
int32_t tester_val = 1;
// --------------- FUNCTIONS
void go_zero()
{
  drive_to(ZERO_TICK, user_rpm);
  reached_goal(ZERO_TICK, 1, 1);
  // Serial.print("CHECK_INPUT");
  // drive_and_check(ZERO_TICK, user_rpm, 1, true);
  Serial.println("ZERO_READY");
}

void go_to()
{
  drive_to(user_go_to, user_rpm/2);
  reached_goal(user_go_to, 1, 1);
  // drive_and_check(user_go_to, user_rpm, 1, true);
  Serial.println("GOTO_READY");
}

void show_cur_pos()
{
  int32_t show_pos = dxl.getPresentPosition(DID, UNIT_RAW);
  Serial.print("WHERE_POS");
  Serial.println(show_pos);
}

void tester(){
  switch(tester_val){
    case 1:
      apply_relay_mode(INIT_RELAY_MODE);
      tester_val += 1;
      break;
    case 2:
      apply_relay_mode(POL_INIT_RELAY_MODE);
      tester_val += 1;
      break;
    case 3:
      apply_relay_mode(TOTAL_RESISTANCE_RELAY_MODE);
      tester_val = 1;
      break;
    default:
      break;
  }
  
}