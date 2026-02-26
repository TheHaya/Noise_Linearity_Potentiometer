#include <Arduino.h>
#include <dxl_servo.h>
#include <calibrate.h>
#include <linearity.h>
#include <elec_deg.h>
#include <relay.h>

// --------------- VARIABLES
const size_t ELEC_ARRAY_SIZE = 4;
float print_elec_deg[ELEC_ARRAY_SIZE];
float print_elec_volt[ELEC_ARRAY_SIZE];


// --------------- ELEC_DEG_FUNCTIONS
void elec_deg_movement(){
    float total_elec_deg = 0;
    soll_tick_total = deg_to_tick(target_deg_total); // ca. 330°
    real_tick_total = end_tick - start_tick;
    
    int32_t offset_von_soll = (real_tick_total-soll_tick_total) / 2;
    

    d12_tick = deg_to_tick(d12_deg);
    d21_tick = deg_to_tick(d21_deg);
    d22_tick = deg_to_tick(d22_deg);
    d31_tick = deg_to_tick(d31_deg);

    
    int32_t sim_tick [] = {d22_tick, d31_tick, d21_tick, d12_tick};
  
    int32_t drive_tick[ELEC_ARRAY_SIZE];
    for(size_t i = 0; i < ELEC_ARRAY_SIZE; i++){    
        drive_tick[i] = sim_tick[i] + start_tick + offset_von_soll;
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
        
        int32_t rel_tick = tick - start_tick;
        
        if(rel_tick == d12_tick + offset_von_soll){
            print_elec_deg[i] = correction_movement(print_elec_volt[i], ist_start_volt, 0, 0) - tick_to_deg(start_tick) - real_mid_deg;
            ccw_links = print_elec_deg[i];
        } else if(rel_tick == d21_tick + offset_von_soll){
            print_elec_deg[i] = correction_movement(print_elec_volt[i], ist_mid_volt, 1, 0) - tick_to_deg(start_tick) - real_mid_deg;
            ccw_rechts = print_elec_deg[i];
        } else if(rel_tick == d22_tick + offset_von_soll){
            print_elec_deg[i] = correction_movement(print_elec_volt[i], ist_mid_volt, 0, 1) - tick_to_deg(start_tick) - real_mid_deg;
            cw_links = print_elec_deg[i];
        } else if(rel_tick == d31_tick + offset_von_soll){
            print_elec_deg[i] = correction_movement(print_elec_volt[i], ist_end_volt, 1, 1) - tick_to_deg(start_tick) - real_mid_deg;
            cw_rechts = print_elec_deg[i];
        }
        
    }
    total_elec_deg = (print_elec_deg[1]-print_elec_deg[0]) + (print_elec_deg[2]-print_elec_deg[3]);
    Serial.print("TOTAL_ELEC");
    Serial.println(total_elec_deg);
    all_relays_off();
}