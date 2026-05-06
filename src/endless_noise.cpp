#include <Arduino.h>
#include <noise.h>
#include <calibrate.h>
#include <dxl_servo.h>
#include <relay.h>
#include <endless_calibrate.h>


// --------------- NOISE MOVEMENT
void endless_noise_preparation_movement(){
  float rpm_intervall; 

  for(int i = 1; i <= 10; i++){
    rpm_intervall = user_rpm*1.5;

    drive_to(endless_sim_start, rpm_intervall);
    reached_goal(endless_sim_start, 3);
    drive_to(endless_sim_end, rpm_intervall);
    reached_goal(endless_sim_end, 3);
  }
}


void endless_noise_movement(){
    float sim_rpm;
    float rpm_intervall; 
    int32_t endless_noise_start_tick;

    for(int i = 1; i <= 3; i++){
        for(int j = 1; j <= 2; j++){
            rpm_intervall = user_rpm/2;
            sim_rpm = rpm_intervall * i;
            endless_noise_start_tick = endless_sim_start+((i - 1) * 2 + j)*4096;

            drive_to(endless_noise_start_tick, sim_rpm);
            reached_goal(endless_noise_start_tick, i);
        }
    }

    for(int i = 1; i <= 3; i++){
        for(int j = 1; j <= 2; j++){
            rpm_intervall = user_rpm/2;
            sim_rpm = rpm_intervall * i;
            endless_noise_start_tick = endless_sim_start+ (6 - ((i - 1) * 2 + j))*4096; // Zählt wieder zurück von 6 -> 1

            drive_to(endless_noise_start_tick, sim_rpm);
            reached_goal(endless_noise_start_tick, i);
        }
    }
        
}
