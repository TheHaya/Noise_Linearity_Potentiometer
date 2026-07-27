#include <Arduino.h>
#include <dxl_servo.h>
#include <calibrate.h>
#include <endless_calibrate.h>
#include <linearity.h>
#include <elec_deg.h>
#include <relay.h>
#include <endless_elec_deg.h>
#include <progress.h>

// --------------- CONSTANTS


// --------------- VARIABLES


// --------------- ELEC_DEG_FUNCTIONS


void endless_elec_deg_movement(){
    float total_elec_deg = 0;
    soll_tick_total = deg_to_tick(target_deg_total); 
    real_tick_total = endless_end_tick - endless_start_tick;
    
    int32_t offset_von_soll = (real_tick_total-soll_tick_total) / 2;
    

    d12_tick = deg_to_tick(d12_deg);
    d31_tick = deg_to_tick(d31_deg);

    if(fabsf(endless_end_tick - endless_start_tick - d31_tick) < 30){
        smaller_steps = true;
    }

    int32_t sim_tick [] = {d31_tick, d12_tick};
  
    int32_t drive_tick[ELEC_ARRAY_SIZE];
    for(size_t i = 0; i < ELEC_ARRAY_SIZE; i++){    
        drive_tick[i] = sim_tick[i] + endless_start_tick + offset_von_soll;
    }

    for (size_t i = 0; i<ELEC_ARRAY_SIZE; i++) {
        //DEBUG_SERIAL.print(tick);
        int32_t tick = drive_tick[i];

        drive_to(tick, user_rpm);
        if (!reached_goal(tick, 2)) {
        // Strom-Trip -> sofort raus
        Serial.println("CANCEL");
        cancelled = true;
        break;
        }
        // drive_and_check(tick, user_rpm);

        int32_t rel_tick = tick - endless_start_tick;
        if(rel_tick == d31_tick + offset_von_soll){
            if(smaller_steps){
                print_elec_deg[i] = correction_movement(print_elec_volt[i], ist_end_volt, 1, 1, true) - tick_to_deg(endless_start_tick) - real_mid_deg;
            } else{
                print_elec_deg[i] = correction_movement(print_elec_volt[i], ist_end_volt, 1, 1) - tick_to_deg(endless_start_tick) - real_mid_deg;
            }
            cw_rechts = print_elec_deg[i];
        } else if(rel_tick == d12_tick + offset_von_soll){
            if(smaller_steps){
                print_elec_deg[i] = correction_movement(print_elec_volt[i], ist_start_volt, 0, 0, true) - tick_to_deg(endless_start_tick) - real_mid_deg;
            } else{
                print_elec_deg[i] = correction_movement(print_elec_volt[i], ist_start_volt, 0, 0) - tick_to_deg(endless_start_tick) - real_mid_deg;
            }
            ccw_links = print_elec_deg[i];
        }

    }
    total_elec_deg = print_elec_deg[0]-print_elec_deg[1];
    Serial.print("TOTAL_ELEC");
    Serial.println(total_elec_deg);
    all_relays_off();
}