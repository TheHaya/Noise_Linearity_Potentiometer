#include <Arduino.h>
#include <noise.h>
#include <calibrate.h>
#include <servo.h>

int32_t user_go_to;

// --------------- NOISE MOVEMENT
void noise_movement(){
  float sim_rpm;
  float rpm_intervall; 

  drive_to(sim_mercy_end, user_rpm/2);
  reached_goal(sim_mercy_end, 1);
  for(int i = 1; i <= 3; i++){
    rpm_intervall = user_rpm/2;
    sim_rpm = rpm_intervall * i;

    drive_to(sim_mercy_start, sim_rpm);
    reached_goal(sim_mercy_start, i);
    drive_to(sim_mercy_end, sim_rpm);
    reached_goal(sim_mercy_end, i);
  }
  Serial.println("FINISH");
}

void go_zero(){
  drive_to(ZERO_TICK, user_rpm);
  reached_goal(ZERO_TICK, 2);
  
  Serial.println("READY");
}

void go_to(){
  drive_to(user_go_to, user_rpm);
  reached_goal(user_go_to, 2);
  
  Serial.println("READY");
}