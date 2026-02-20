#include <Arduino.h>
#include <dxl_servo.h>
#include <calibrate.h>

int32_t user_go_to;

void go_zero(){
    drive_to(ZERO_TICK, user_rpm);
    reached_goal(ZERO_TICK, 2, 1);
    Serial.println("ZERO_READY");}

void go_to(){
  drive_to(user_go_to, user_rpm);
  reached_goal(user_go_to, 2, 1);
  Serial.println("READY");
}