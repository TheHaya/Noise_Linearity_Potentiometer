#include <Arduino.h>
#include <dxl_servo.h>
#include <calibrate.h>
#include <elapsedMillis.h>
#include <relay.h>


// --------------- CONSTANTS
const int32_t CHECK_END_MERCY_DEG = 30;
const int32_t CHECK_END_START = -8000;
const int32_t CHECK_END_END = 12000;
const int32_t ZERO_TICK = 2050;
const float MERCY_TOLERANCE_TICK = 15;
const float CHECK_ENDS_TOL_DEG = 10;
const float SAFETY_VOLT = 10;
const float SLOW_RPM = 8;

// --------------- VARIABLES
int32_t start_tick, end_tick, real_mid_tick;
int32_t sim_mercy_start, sim_mercy_end;
int32_t calibrate_current_ccw = 1750;
int32_t calibrate_current_cw = 2350;

float ist_start_volt, ist_end_volt, ist_mid_volt;
float user_rpm, rpm1, rpm2, rpm3;
float real_time1, real_time2, real_time3;
float theo_time1, theo_time2, theo_time3;
float target_deg_total;
float delay1, delay2, delay3;
float safety_pos_volt;
float tar_volt;



// --------------- CALIBRATIONS
void calibrate_init(){
start_tick = 0;
end_tick = 0;
real_mid_tick = 0;
sim_mercy_start = 0;
sim_mercy_end = 0;
ist_start_volt = 0;
ist_end_volt = 0;
ist_mid_volt = 0;
endless_start_volt = 0; 
endless_end_volt = 0;
endless_start_deg = 0;
rpm1 = 0;
rpm2 = 0;
rpm3 = 0;

real_time1 = 0;
real_time2 = 0;
real_time3 = 0;
theo_time1 = 0;
theo_time2 = 0;
theo_time3 = 0;
delay1 = 0;
delay2 = 0;
delay3 = 0;

}
float corr_measure(){
  float current_volt = NAN;
  elapsedMillis timer;
  int t = 8000;
  Serial.setTimeout(50);
  Serial.print("VOLTR");
  Serial.println(dxl.getPresentPosition(DID,UNIT_RAW));
  delay(50);
  
  while(timer < t){
    if(cancelled) break;
    if(Serial.available()){
      String VCommand = Serial.readStringUntil('\n');
      VCommand.trim();
      if(VCommand == "STOP"){
        cancelled = true;
        stop_motion();
        break;
      }
      if(VCommand.startsWith("ISTV:")){
        if(VCommand.substring(5) == "ERR"){
          break;
        }
        current_volt = VCommand.substring(5).toFloat();
        break; 
      } 
    }
  }
  return current_volt;
}


// dead_direction 0 -> deadzone links von position //////--- ;;; 1 -> rechts von position ---//////
// dead_half 0 -> linke Hälfte, 1 -> rechte Hälfte
float correction_movement(float &current_volt, float goal_volt, 
                          int dead_direction, int dead_half, int timeout){
  const int32_t STEP = 20;
  const int32_t PUSHBACK = 200;
  const float V_TOL = 0.001f;        
  const int32_t TICK_TOL = 1;
  elapsedMillis error_timer;
  int32_t low, high;
  current_volt = corr_measure();
  
  while(error_timer < timeout){
    while(!cancelled && fabsf(current_volt - goal_volt) <= V_TOL) {
      int32_t t = 0;
      int32_t back = 0;
      if(dead_direction == 0){                // deadzone links von position
        t = get_tick_position() + STEP;
      } else if(dead_direction == 1){         // deadzone rechts von position
        t = get_tick_position() - STEP;
      }
      drive_to(t, user_rpm);
      reached_goal(t, 2);
      current_volt = corr_measure();
    }

    high = get_tick_position();

    while(!cancelled && fabsf(current_volt - goal_volt) > V_TOL) {
      int32_t t = 0;
      int32_t back = 0;
      if(dead_direction == 0){                // deadzone links von position
        t = get_tick_position() - STEP;
      } else if(dead_direction == 1){         // deadzone rechts von position
        t = get_tick_position() + STEP;
      }
      drive_to(t, user_rpm);
      reached_goal(t, 2);
      current_volt = corr_measure();
    }

    low = get_tick_position();

    while(!cancelled && abs(high - low) > TICK_TOL) {
      int32_t back = 0;
      int32_t mid = (high + low) / 2;
      if(dead_half == 0){back = mid + PUSHBACK;}  // dead linke Hälfte
        else {back = mid - PUSHBACK;}             // dead rechte Hälfte   
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

    if((dead_half == 0 && dead_direction == 0) || (dead_half == 1 && dead_direction == 1)){
      return tick_to_deg(low);
    }
    return tick_to_deg(high);
  }
  return NAN;
}

void calibrate_currents(){
  calibrate_current_cw = get_tick_position() + 300;
  calibrate_current_ccw = get_tick_position() - 300;
  drive_to(calibrate_current_cw, SLOW_RPM);
  reached_goal(calibrate_current_cw, 0, 1);
  
  drive_to(calibrate_current_ccw, SLOW_RPM);
  reached_goal(calibrate_current_ccw, 0, 1);
  
  drive_to(calibrate_current_cw, SLOW_RPM);
  reached_goal(calibrate_current_cw, 0, 1);
  


  for(int i = 1; i <= 3; i++){
    float rpm_intervall = user_rpm/2;
    float cal_rpm = rpm_intervall*i;
    elapsedMillis cur_millis;
    drive_to(calibrate_current_ccw, cal_rpm);
    reached_goal(calibrate_current_ccw, i, 1);
    // if(!reached_goal(calibrate_current_ccw, i, 1));

    drive_to(calibrate_current_cw, cal_rpm);
    reached_goal(calibrate_current_cw, i, 1);
    // if(!reached_goal(calibrate_current_cw, i, 1));

    switch(i){
      case 1: rpm1 = cal_rpm; real_time1 = cur_millis; 
              theo_time1 = rpm_to_time(calibrate_current_ccw, cal_rpm); 
              break;
      case 2: rpm2 = cal_rpm; real_time2 = cur_millis; 
              theo_time2 = rpm_to_time(calibrate_current_ccw, cal_rpm);
              break;
      case 3: rpm3 = cal_rpm; real_time3 = cur_millis; 
              theo_time3 = rpm_to_time(calibrate_current_ccw, cal_rpm); 
              break;
      default: break;
    }
  }
  delay1 = (real_time1 - 2*theo_time1)/1000; // ms -> s
  delay2 = (real_time2 - 2*theo_time2)/1000;
  delay3 = (real_time3 - 2*theo_time3)/1000;

  Serial.print("DELAY1");
  Serial.println(delay1);
  Serial.print("DELAY2");
  Serial.println(delay2);
  Serial.print("DELAY3");
  Serial.println(delay3);
  Serial.print("CUR0");
  Serial.println(cal_cur0);
  Serial.print("CUR1");
  Serial.println(cal_cur1);
  Serial.print("CUR2");
  Serial.println(cal_cur2);
  Serial.print("CUR3");
  Serial.println(cal_cur3);

}




void check_beginning(float total_deg){
  const float LOW_SAFETY = SAFETY_VOLT*0.1;
  const float HIGH_SAFETY = SAFETY_VOLT*0.9;
  safety_pos_volt = corr_measure();
  if(safety_pos_volt <= LOW_SAFETY){
    int32_t low_to_mid = get_tick_position() - deg_to_tick(total_deg)/2;
    drive_to(low_to_mid, SLOW_RPM);
    reached_goal(low_to_mid, 0, 1);

  } else if(safety_pos_volt >= HIGH_SAFETY){
    int32_t high_to_mid = get_tick_position() + deg_to_tick(total_deg)/2;
    drive_to(high_to_mid, SLOW_RPM);
    reached_goal(high_to_mid, 0, 1);

  }
}

// --------------- MECHANICAL ENDS
void check_ends(){
  
  drive_to(CHECK_END_END, SLOW_RPM);
  if(reached_goal(CHECK_END_END, 0, 0, 30000) == false){
    end_tick = stopped_tick;
    ist_start_volt = corr_measure();
    // ist_end_volt = corr_measure(ist_end_volt);
  }
 
  for(int i = 0; i < 5; i++){
  dxl.ledOff(1);
  delay(100);
    dxl.ledOn(1);
  delay(100);
  } 

  int32_t test_check_start = get_tick_position() - deg_to_tick(target_deg_total-CHECK_END_MERCY_DEG);

  drive_to(test_check_start, user_rpm);
  reached_goal(test_check_start, 2);

  drive_to(CHECK_END_START, SLOW_RPM);
  if(reached_goal(CHECK_END_START, 0, 0, 30000) == false){
    start_tick = stopped_tick;
    ist_end_volt = corr_measure();
    // ist_start_volt = corr_measure(ist_start_volt);
  }

  sim_mercy_start = start_tick + MERCY_TOLERANCE_TICK;
  sim_mercy_end = end_tick - MERCY_TOLERANCE_TICK;
  uint32_t total_distance = abs(end_tick - start_tick);
  real_mid_tick = start_tick + total_distance / 2;
  uint32_t sim_distance = abs(sim_mercy_end - sim_mercy_start);
  Serial.print("TICKS");
  Serial.println(sim_distance);
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

