#include <Arduino.h>
#include <servo.h>
#include <calibrate.h>
#include <linearity.h>


// --------------- VARIABLES
int32_t elec_deg;


// --------------- ELEC_DEG_FUNCTIONS
void elec_deg_movement(){
    soll_tick_total = deg_to_tick(soll_deg_total); // ca. 330°
    real_tick_total = end_tick - start_tick;
    int32_t offset_von_soll = (real_tick_total-soll_tick_total) / 2;
    

    d12_tick = deg_to_tick(d12_deg);
    d21_tick = deg_to_tick(d21_deg);
    d22_tick = deg_to_tick(d22_deg);
    d31_tick = deg_to_tick(d31_deg);

    int32_t sim_tick [] = {d22_tick, d31_tick, d21_tick, d12_tick};
  
    int32_t drive_tick[4];
    for(size_t i = 0; i <= 4; i++){    
        drive_tick[i] = sim_tick[i] + start_tick + offset_von_soll;
    }
}