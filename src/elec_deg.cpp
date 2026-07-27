#include <Arduino.h>
#include <dxl_servo.h>
#include <calibrate.h>
#include <linearity.h>
#include <elec_deg.h>
#include <relay.h>
#include <progress.h>


// --------------- CONSTANTS
const size_t ELEC_ARRAY_SIZE = 2;

// --------------- VARIABLES
float print_elec_deg[ELEC_ARRAY_SIZE];
float print_elec_volt[ELEC_ARRAY_SIZE];
bool smaller_steps = false;

// --------------- ELEC_DEG_FUNCTIONS
void elec_deg_init(){
    for(int i = 0; i < ELEC_ARRAY_SIZE; i++){
        print_elec_deg[i] = 0;
        print_elec_volt[i] = 0;
    }
    smaller_steps = false;
}

void elec_deg_movement(){
    float total_elec_deg = 0;
    soll_tick_total = deg_to_tick(target_deg_total); // ca. 330°
    real_tick_total = end_tick - start_tick;
    
    int32_t offset_von_soll = (real_tick_total-soll_tick_total) / 2;
    
    // Falls keine deadzones und mech = elec
    if(d12_deg == 0){
        d12_tick = sim_mercy_start - start_tick - offset_von_soll;
    } else {
        d12_tick = deg_to_tick(d12_deg);
    }
    if(d31_deg == 0){
        d31_tick = sim_mercy_end - start_tick - offset_von_soll;
    } else {
        d31_tick = deg_to_tick(d31_deg);
    }


    if(fabsf(end_tick - start_tick - d31_tick) < 30 || d12_deg == 0 || d31_deg == 0){
        smaller_steps = true;
    }

    int32_t sim_tick [] = {d31_tick, d12_tick};
  
    int32_t drive_tick[ELEC_ARRAY_SIZE];
    for(size_t i = 0; i < ELEC_ARRAY_SIZE; i++){    
        drive_tick[i] = sim_tick[i] + start_tick + offset_von_soll;
    }

    for (size_t i = 0; i<ELEC_ARRAY_SIZE; i++) {
        if(i == 0){
            report_progress("ELEC", "D12_CHECK", 10);
        } else if(i == 1){
            report_progress("ELEC", "D31_CHECK", 50);
        }
        //DEBUG_SERIAL.print(tick);
        int32_t tick = drive_tick[i];

        // drive_to(tick, user_rpm);
        // if (!reached_goal(tick, 2)) {
        // // Strom-Trip -> sofort raus
        // Serial.println("CANCEL");
        // cancelled = true;
        // break;
        // }
        drive_and_check(tick, user_rpm);
        
        int32_t rel_tick = tick - start_tick;
        if(relay_switch){
            if(rel_tick == d31_tick + offset_von_soll){
                if(smaller_steps){
                    print_elec_deg[i] = correction_movement(print_elec_volt[i], ist_start_volt, 1, 1, true) - tick_to_deg(start_tick) - real_mid_deg;
                } else{
                    print_elec_deg[i] = correction_movement(print_elec_volt[i], ist_start_volt, 1, 1) - tick_to_deg(start_tick) - real_mid_deg;
                }
            cw_rechts = print_elec_deg[i];
            } else if(rel_tick == d12_tick + offset_von_soll){
                if(smaller_steps){
                    print_elec_deg[i] = correction_movement(print_elec_volt[i], ist_end_volt, 0, 0, true) - tick_to_deg(start_tick) - real_mid_deg;
                } else{
                    print_elec_deg[i] = correction_movement(print_elec_volt[i], ist_end_volt, 0, 0) - tick_to_deg(start_tick) - real_mid_deg;
                }
                ccw_links = print_elec_deg[i];
            }
        } else {
            if(rel_tick == d31_tick + offset_von_soll){
                if(smaller_steps){
                    print_elec_deg[i] = correction_movement(print_elec_volt[i], ist_start_volt, 1, 1, true) - tick_to_deg(start_tick) - real_mid_deg;
                } else{
                    print_elec_deg[i] = correction_movement(print_elec_volt[i], ist_start_volt, 1, 1) - tick_to_deg(start_tick) - real_mid_deg;
                }
            cw_rechts = print_elec_deg[i];
            } else if(rel_tick == d12_tick + offset_von_soll){
                if(smaller_steps){
                    print_elec_deg[i] = correction_movement(print_elec_volt[i], ist_end_volt, 0, 0, true) - tick_to_deg(start_tick) - real_mid_deg;
                } else{
                    print_elec_deg[i] = correction_movement(print_elec_volt[i], ist_end_volt, 0, 0) - tick_to_deg(start_tick) - real_mid_deg;
                }
                ccw_links = print_elec_deg[i];
            }
        }
        
    }
    report_progress("ELEC", "TOTAL_ELEC", 90);
    total_elec_deg = print_elec_deg[0]-print_elec_deg[1];
    Serial.print("TOTAL_ELEC");
    Serial.println(total_elec_deg);
    all_relays_off();
}