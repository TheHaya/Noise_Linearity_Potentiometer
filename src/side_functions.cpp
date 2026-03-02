#include <Arduino.h>
#include <dxl_servo.h>
#include <calibrate.h>

// --------------- VARIABLES
int32_t user_go_to;


// --------------- FUNCTIONS
void go_zero(){
  drive_to(ZERO_TICK, user_rpm);
  reached_goal(ZERO_TICK, 2, 1);
  Serial.println("ZERO_READY");
}

void go_to(){
  drive_to(user_go_to, user_rpm);
  reached_goal(user_go_to, 2, 1);
  Serial.println("GOTO_READY");
}

void show_cur_pos(){
  int32_t show_pos = dxl.getPresentPosition(DID, UNIT_RAW);
  Serial.print("WHERE_POS");
  Serial.println(show_pos);
}