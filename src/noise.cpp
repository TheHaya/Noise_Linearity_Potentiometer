#include <Arduino.h>
#include <noise.h>
#include <calibrate.h>
#include <dxl_servo.h>
#include <relay.h>
#include <progress.h>

// --------------- NOISE MOVEMENT
void noise_preparation_movement(){
  float rpm_intervall; 
  
  // drive_to(sim_mercy_start, user_rpm);
  // reached_goal(sim_mercy_start, 2);

  for(int i = 1; i <= 10; i++){
    rpm_intervall = user_rpm*1.5;

    drive_to(sim_mercy_start, rpm_intervall);
    reached_goal(sim_mercy_start, 3, 0, 10000, 5);
    drive_to(sim_mercy_end, rpm_intervall);
    reached_goal(sim_mercy_end, 3, 0, 10000, 5);
    // drive_and_check(sim_mercy_start, rpm_intervall);
    // drive_and_check(sim_mercy_end, rpm_intervall);
  }
}

void noise_movement(){
  float sim_rpm;
  float rpm_intervall; 

  for(int i = 1; i <= 3; i++){
    rpm_intervall = user_rpm/2;
    sim_rpm = rpm_intervall * i;

    drive_to(sim_mercy_start, sim_rpm);
    reached_goal(sim_mercy_start, i, 0, 10000, 5);
    drive_to(sim_mercy_end, sim_rpm);
    reached_goal(sim_mercy_end, i, 0, 10000, 5);
    drive_to(sim_mercy_start, sim_rpm);
    reached_goal(sim_mercy_start, i, 0, 10000, 5);
    drive_to(sim_mercy_end, sim_rpm);
    reached_goal(sim_mercy_end, i, 0, 10000, 5);
    // drive_and_check(sim_mercy_start, sim_rpm);
    // drive_and_check(sim_mercy_end, sim_rpm);
    // drive_and_check(sim_mercy_start, sim_rpm);
    // drive_and_check(sim_mercy_end, sim_rpm);
  }
  Serial.println("NOISE_MOVE_FINISH");
}
