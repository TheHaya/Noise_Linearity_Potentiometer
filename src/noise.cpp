#include <Arduino.h>
#include <noise.h>
#include <calibrate.h>
#include <dxl_servo.h>
#include <relay.h>

// --------------- NOISE MOVEMENT
void noise_movement(){
  float sim_rpm;
  float rpm_intervall; 

  for(int i = 1; i <= 3; i++){
    rpm_intervall = user_rpm/2;
    sim_rpm = rpm_intervall * i;

    drive_to(sim_mercy_start, sim_rpm);
    reached_goal(sim_mercy_start, i);
    drive_to(sim_mercy_end, sim_rpm);
    reached_goal(sim_mercy_end, i);
  }
  all_relays_off();
  Serial.println("NOISE_MOVE_FINISH");
}

