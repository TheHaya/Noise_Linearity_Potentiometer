#include <Arduino.h>
#include <noise.h>
#include <calibrate.h>
#include <dxl_servo.h>
#include <relay.h>
#include <endless_calibrate.h>
#include <progress.h>

int32_t endless_noise_prep_start;
int32_t endless_noise_prep_end;

void endless_noise_init(){
    endless_noise_prep_start = 0;
    endless_noise_prep_end = 0;
}
// --------------- NOISE MOVEMENT
void endless_noise_preparation_movement(){
    float rpm_intervall; 
    endless_noise_prep_start = get_tick_position();
    endless_noise_prep_end = endless_noise_prep_start + 4096; // ganze umdrehung

    for(int i = 1; i <= 10; i++){
        rpm_intervall = user_rpm*1.5;

        drive_to(endless_noise_prep_start, rpm_intervall);
        reached_goal(endless_noise_prep_start, 3);
        drive_to(endless_noise_prep_end, rpm_intervall);
        reached_goal(endless_noise_prep_end, 3);
    }
    drive_to(endless_noise_prep_start, rpm_intervall);
        reached_goal(endless_noise_prep_start, 3);
}


void endless_noise_movement(){
    float sim_rpm;
    float rpm_intervall; 
    int32_t endless_noise_start_tick;

    for(int i = 1; i <= 3; i++){
        rpm_intervall = user_rpm/2;
        sim_rpm = rpm_intervall * i;
        endless_noise_start_tick = endless_noise_prep_start + i * 8192; // 2 Umdrehungen pro go

        drive_to(endless_noise_start_tick, sim_rpm);
        reached_goal(endless_noise_start_tick, i);
        }

    for(int i = 1; i <= 3; i++){
        rpm_intervall = user_rpm/2;
        sim_rpm = rpm_intervall * i;
        endless_noise_start_tick = endless_noise_prep_start+ (3 - i) * 8192; // Zählt wieder zurück von 6 -> 1

        drive_to(endless_noise_start_tick, sim_rpm);
        reached_goal(endless_noise_start_tick, i);
        }
    Serial.println("NOISE_MOVE_FINISH");
}
