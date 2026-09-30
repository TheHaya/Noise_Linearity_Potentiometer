#include <Arduino.h>
#include <dxl_servo.h>
#include <calibrate.h>
#include <elapsedMillis.h>
#include <relay.h>
#include <progress.h>

// --------------- CONSTANTS
const int32_t ENDLESS_MERCY_TOLERANCE_TICK = 2;

// --------------- VARIABLES
float endless_start_volt, endless_end_volt;
int32_t endless_start_tick, endless_end_tick;
int32_t endless_sim_start, endless_sim_end;


// --------------- FUNCTIONS

void endless_init(){
  endless_start_volt = 0; 
  endless_end_volt = 0;
  endless_start_tick = 0;
  endless_end_tick = 0;
  endless_sim_start = 0;
  endless_sim_end = 0;
}

void find_endless_volt_crossover(){
  int32_t next_segment;
  float before_volt, after_volt;

  after_volt = corr_measure();
  for(int i = 0; i < 6; i++){
    before_volt = after_volt;
    next_segment = get_tick_position() + deg_to_tick(60);
    drive_to(next_segment, user_rpm);
    reached_goal(next_segment, 2, 1);
    after_volt = corr_measure();
    if(abs(after_volt-before_volt) > 5){
      endless_end_volt = before_volt;
      endless_start_volt = after_volt;
      break;
    }
  }
}

float correction_movement_endless_starts(float &current_volt, float goal_volt, int start, int timeout){   
  const int32_t STEP = 200;
  const int32_t PUSHBACK = 200; 
  const float V_TOL = 2;
  const int32_t TICK_TOL = 1;
  elapsedMillis error_timer;
  int32_t low, high;
  current_volt = corr_measure();
  
  while(error_timer < timeout){
    while(!cancelled && (fabsf(current_volt - goal_volt) <= V_TOL)) {
      int32_t t = 0;
      int32_t back = 0;               // deadzone links von position
      if(start){
        t = get_tick_position() - STEP;
      }
      else{
        t = get_tick_position() + STEP;
      }
      drive_to(t, user_rpm);
      reached_goal(t, 2);
      current_volt = corr_measure();
    }
    high = get_tick_position();
    while(!cancelled && (fabsf(current_volt - goal_volt) > V_TOL)) {
      int32_t t = 0;
      int32_t back = 0;
      if(start){
        t = get_tick_position() + STEP;
      }
      else{
        t = get_tick_position() - STEP;
      }
      drive_to(t, user_rpm);
      reached_goal(t, 2);
      current_volt = corr_measure();
    }
    low = get_tick_position();
    while(!cancelled && abs(high - low) > TICK_TOL) {
      int32_t back = 0;
      int32_t mid = (high + low) / 2;
      back = mid + PUSHBACK; // dead linke Hälfte  
      drive_to(back, user_rpm);
      reached_goal(back, 2);
      drive_to(mid, user_rpm);
      reached_goal(mid, 2);

      current_volt = corr_measure();
      if(fabsf(current_volt - goal_volt) > V_TOL) {
        high = mid;
      } else {
        low = mid;
      }
    }
    return low;
  }
  return NAN;
}


void find_endless_starting_point(){
  float cur_volt;
  report_progress("MECH", "ENDLESS_START_TICK", 70);
  // Absicherung wegen Ring Ende
  endless_start_tick = correction_movement_endless_starts(cur_volt, endless_start_volt, 1);
  drive_to(endless_start_tick + ENDLESS_MERCY_TOLERANCE_TICK, user_rpm); 
  reached_goal(endless_start_tick + ENDLESS_MERCY_TOLERANCE_TICK, 2);
  if(relay_switch){
    ist_start_volt = corr_measure(1);
    Serial.print("IST_S_VOLT:");
    Serial.println(ist_start_volt, 8);
    
    if(measure_start_resistance){
    ist_start_resistance = corr_measure_res(1);
    }
    if(measure_total_resistance){
      ist_total_resistance = corr_measure_res(3);
    }

  } else{
    ist_end_volt = corr_measure(2);
    Serial.print("IST_E_VOLT:");
    Serial.println(ist_end_volt, 8);
    if(measure_end_resistance){
      ist_end_resistance = corr_measure_res(2);
    }
  }
  
  
  drive_to(endless_start_tick + 3750, user_rpm); // ~330°
  reached_goal(endless_start_tick + 3750, 2);
  if(relay_switch){
    apply_relay_mode(INIT_RELAY_MODE);
  } else{
    apply_relay_mode(POL_INIT_RELAY_MODE);
  }
  delay(200);

  report_progress("MECH", "ENDLESS_END_TICK", 80);
  // Absicherung wegen Ring Ende
  endless_end_tick = correction_movement_endless_starts(cur_volt, endless_start_volt, 0);
  if(relay_switch){
    apply_relay_mode(POL_INIT_RELAY_MODE);
  } else{
    apply_relay_mode(INIT_RELAY_MODE);
  }
  delay(200);
  drive_to(endless_end_tick - ENDLESS_MERCY_TOLERANCE_TICK, user_rpm);
  reached_goal(endless_end_tick - ENDLESS_MERCY_TOLERANCE_TICK, 2);
  if(relay_switch){
    ist_end_volt = corr_measure(2);
    Serial.print("IST_E_VOLT:");
    Serial.println(ist_end_volt, 8);
    if(measure_end_resistance){
      ist_end_resistance = corr_measure_res(2);
    }
  } else{
    ist_start_volt = corr_measure(1);
    Serial.print("IST_S_VOLT:");
    Serial.println(ist_start_volt, 8);
    if(measure_start_resistance){
    ist_start_resistance = corr_measure_res(1);
    }
    if(measure_total_resistance){
      ist_total_resistance = corr_measure_res(3);
    }
  }

  endless_sim_start = endless_start_tick + ENDLESS_MERCY_TOLERANCE_TICK;
  endless_sim_end = endless_end_tick - ENDLESS_MERCY_TOLERANCE_TICK;
  sim_mercy_start = endless_sim_start;
  sim_mercy_end = endless_sim_end;

  uint32_t total_distance = abs(endless_end_tick - endless_start_tick); // 4096 ticks -> 360°
  real_mid_tick = endless_start_tick + total_distance / 2;
  // uint32_t sim_distance = abs(sim_mercy_end - sim_mercy_start);
  // Serial.print("TICKS");
  // Serial.println(sim_distance);
  report_progress("MECH", "ZERO_ENDLESS", 90);
  Serial.print("ANGLE");
  Serial.println(tick_to_deg(total_distance));
  for(int i = 0; i < 5; i++){
    dxl.ledOff(1);
    delay(100);
     dxl.ledOn(1);
    delay(100);
  }
  all_relays_off();
}

