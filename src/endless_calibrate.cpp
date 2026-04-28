#include <Arduino.h>
#include <dxl_servo.h>
#include <calibrate.h>
#include <elapsedMillis.h>
#include <relay.h>
#include <calibrate.h>

float endless_start_volt, endless_end_volt, endless_start_deg, endless_end_deg;

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
    return tick_to_deg(low);
  }
  return NAN;
}


void find_endless_starting_point(){
  float cur_volt;
  endless_start_deg = correction_movement_endless_starts(cur_volt, endless_start_volt, 1);
  apply_relay_mode(ENDLESS_INIT_RELAY_MODE);
  endless_end_deg = correction_movement_endless_starts(cur_volt, endless_start_volt, 0);
}

