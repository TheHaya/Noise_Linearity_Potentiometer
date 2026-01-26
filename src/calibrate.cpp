#include <Arduino.h>
#include <servo.h>
#include <calibrate.h>
#include <elapsedMillis.h>


const int32_t CHECK_END_START = -2000;
const int32_t CHECK_END_END = 6000;
const int32_t CALIBRATE_CURRENT_CCW = 1700;
const int32_t CALIBRATE_CURRENT_CW = 2400;
const int32_t ZERO_TICK = 2050;
const float MERCY_TOLERANCE_TICK = 15;
const float CHECK_ENDS_TOL_DEG = 10;

int32_t start_tick, end_tick, mid_tick;
int32_t sim_mercy_start, sim_mercy_end;

float ist_start_volt, ist_end_volt, ist_mid_volt;
float slow_rpm = 5;
float user_rpm, rpm1, rpm2, rpm3;
float real_time1 = 0, real_time2 = 0, real_time3 = 0;
float theo_time1 = 0, theo_time2 = 0, theo_time3 = 0;
float target_deg_total;
float delay1, delay2, delay3;



// --------------- CALIBRATIONS
float corr_measure(float current_volt){
  cancelled = false;
  Serial.println("VOLTR");
  delay(50);
  if(cancelled == false){
    for(;;){
    String VCommand = Serial.readStringUntil('\n');
    VCommand.trim();
      if(VCommand.startsWith("ISTV:")){
        current_volt = VCommand.substring(5).toFloat();
        break;
      }
    }
  }
  return current_volt;
}


// dead_direction 0 -> deadzone links von position //////--- ;;; 1 -> rechts von position ---//////
float correction_movement(float &current_volt, float goal_volt, 
                          int dead_direction, int dead_half, uint timeout){
  const float v_tol = 0.001f;        
  const int32_t TICK_TOL = 1;
  elapsedMillis error_timer;
  int32_t low, high;
  current_volt = corr_measure(current_volt);
  
  while(error_timer < timeout){
    while (!cancelled && fabsf(current_volt - goal_volt) <= v_tol) {
      int32_t t = 0;
      int32_t back = 0;
      if(dead_direction == 0){                // deadzone links von position
        t = get_tick_position() + 20;
        if(dead_half == 0){ back = t + 500;}  // dead linke Hälfte
      else { back = t - 500;}                 // dead rechte Hälfte
      } else if(dead_direction == 1){         // deadzone rechts von position
        t = get_tick_position() - 20;
        if(dead_half == 0){ back = t + 500;} 
        else { back = t - 500;}
      }
      drive_to(back, user_rpm);
      reached_goal(back, 2);
      drive_to(t, user_rpm);
      reached_goal(t, 2);
      current_volt = corr_measure(current_volt);
    }

    high = get_tick_position();

    while (!cancelled && fabsf(current_volt - goal_volt) > v_tol) {
      int32_t t = 0;
      int32_t back = 0;
      if(dead_direction == 0){                // deadzone links von position
        t = get_tick_position() - 20;
        if(dead_half == 0){ back = t + 500;}  // dead linke Hälfte
        else { back = t - 500;}               // dead rechte Hälfte
      } else if(dead_direction == 1){         // deadzone rechts von position
        t = get_tick_position() + 20;
        if(dead_half == 0){ back = t + 500;}
        else { back = t - 500;}
      }
      drive_to(back, user_rpm);
      reached_goal(back, 2);
      drive_to(t, user_rpm);
      reached_goal(t, 2);
      current_volt = corr_measure(current_volt);
    }

    low = get_tick_position();

    while (!cancelled && abs(high - low) > TICK_TOL) {
      int32_t back = 0;
      int32_t mid = (high + low) / 2;
      if(dead_half == 0){back = mid + 500;}  // dead linke Hälfte
        else {back = mid - 500;}             // dead rechte Hälfte   
      drive_to(back, user_rpm);
      reached_goal(back, 2);
      drive_to(mid, user_rpm);
      reached_goal(mid, 2);

      current_volt = corr_measure(current_volt);
      if ((current_volt - goal_volt) > v_tol) {
        high = mid;
      } else {
        low = mid;
      }
    }
    float edge_deg = 0;
      if(dead_direction == 0){
        edge_deg = tick_to_deg(low);
      } else if(dead_direction == 1){
        edge_deg = tick_to_deg(high);
      }
    return edge_deg;
  }
  return false;
}
  

void calibrate_currents(){
  drive_to(CALIBRATE_CURRENT_CW, user_rpm);
  reached_goal(CALIBRATE_CURRENT_CW, 2, 1);

  drive_to(CALIBRATE_CURRENT_CCW, slow_rpm);
  reached_goal(CALIBRATE_CURRENT_CCW, 0, 1);
  drive_to(CALIBRATE_CURRENT_CW, slow_rpm);
  reached_goal(CALIBRATE_CURRENT_CW, 0, 1);

  for(int i = 1; i <= 3; i++){
    float rpm_intervall = user_rpm/2;
    float cal_rpm = rpm_intervall*i;
    elapsedMillis cur_millis;
    drive_to(CALIBRATE_CURRENT_CCW, cal_rpm);
    reached_goal(CALIBRATE_CURRENT_CCW, i, 1);
    drive_to(CALIBRATE_CURRENT_CW, cal_rpm);
    reached_goal(CALIBRATE_CURRENT_CW, i, 1);
    switch(i){
      case 1: rpm1 = cal_rpm; real_time1 = cur_millis; 
              theo_time1 = rpm_to_time(CALIBRATE_CURRENT_CCW, cal_rpm); 
              break;
      case 2: rpm2 = cal_rpm; real_time2 = cur_millis; 
              theo_time2 = rpm_to_time(CALIBRATE_CURRENT_CCW, cal_rpm);
              break;
      case 3: rpm3 = cal_rpm; real_time3 = cur_millis; 
              theo_time3 = rpm_to_time(CALIBRATE_CURRENT_CCW, cal_rpm); 
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
  drive_to(ZERO_TICK, rpm1);
  reached_goal(ZERO_TICK, rpm1);
}


// --------------- MECHANICAL ENDS
void check_ends(bool uses_dmm){
  int32_t check_mercy_start = deg_to_tick(360 - target_deg_total + CHECK_ENDS_TOL_DEG);
  int32_t check_mercy_end = deg_to_tick(target_deg_total - CHECK_ENDS_TOL_DEG);
  
  if(uses_dmm){ist_mid_volt = corr_measure(ist_mid_volt);}

  drive_to(check_mercy_start, rpm3);
  reached_goal(check_mercy_start, 3);
  drive_to(CHECK_END_START, slow_rpm);
  if(reached_goal(CHECK_END_START, 0) == false){
    start_tick = stopped_tick;
    if(uses_dmm){ist_start_volt = corr_measure(ist_start_volt);}
  }
  for(int i = 0; i < 5; i++){
    dxl.ledOff(1);
    delay(100);
     dxl.ledOn(1);
    delay(100);
  } 
  drive_to(check_mercy_end, rpm3);
  reached_goal(check_mercy_end, 3);
  drive_to(CHECK_END_END, slow_rpm);
  if(reached_goal(CHECK_END_END, 0) == false){
    end_tick = stopped_tick;
    if(uses_dmm){ist_end_volt = corr_measure(ist_end_volt);}
  }
  
  sim_mercy_start = start_tick + MERCY_TOLERANCE_TICK;
  sim_mercy_end = end_tick - MERCY_TOLERANCE_TICK;
  uint32_t total_distance = abs(end_tick - start_tick);
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
}
