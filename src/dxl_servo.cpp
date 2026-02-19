#include <dxl_servo.h>
#include <Arduino.h>
#include <Dynamixel2Arduino.h>
#include <math.h>
#include <elapsedMillis.h>

// --------------- DYNAMIXEL VARIABLES
#define DXL_SERIAL Serial1
#define DEBUG_SERIAL Serial

const int DXL_DIR_PIN = 2;
const uint8_t DID = 1;
const float DXL_PROTOCOL = 2.0;
const uint32_t DXL_BAUD = 1000000;

Dynamixel2Arduino dxl(DXL_SERIAL, DXL_DIR_PIN);


// --------------- VARIABLES
const float DEG_PER_TICK = 360.0f / 4096.0f;
const float TICK_PER_DEG = 4096.0f / 360.0f;
const float RPM_PER_VEL = 0.229;
using namespace ControlTableItem;

const int POLL_TIMER = 1;

int32_t stopped_tick;
float start_current = 800;
float cal_cur0, cal_cur1, cal_cur2, cal_cur3;
float cur_tolerance = 4;
float cur_tolerance_slow = 1;
bool cancelled;
int32_t cur_pos;
float cur_cur;



int32_t deg_to_tick(float deg){
  return deg * TICK_PER_DEG;
}

float tick_to_deg(int32_t tick){
  return tick * DEG_PER_TICK;
}

int32_t get_tick_position(){
  return dxl.getPresentPosition(DID, UNIT_RAW);
}

float get_deg_position(){
  return tick_to_deg(dxl.getPresentPosition(DID, UNIT_RAW));
}

uint32_t rpm_to_time(int32_t goal_tick, float rpm){
  uint32_t out_time = 60/rpm*1000;
  int32_t diff_pos = abs(dxl.getPresentPosition(DID, UNIT_RAW) - goal_tick);
  out_time = out_time * diff_pos/4096;
  return out_time;
}

void dxl_init(){
  cancelled = false;
  cal_cur0 = 0;
  cal_cur1 = 0;
  cal_cur2 = 0;
  cal_cur3 = 0;
}


// --------------- DRIVE FUNCTIONS
void drive_to(int32_t tick, float rpm, uint8_t DYN_ID){
  dxl.torqueOff(DYN_ID);
  dxl.writeControlTableItem(PROFILE_VELOCITY, DYN_ID, rpm_to_time(tick, rpm)); 
  //dxl.writeControlTableItem(PROFILE_VELOCITY, DYN_ID, rpm);
  dxl.writeControlTableItem(PROFILE_ACCELERATION, DYN_ID, 0);
  dxl.torqueOn(DYN_ID);
  dxl.setGoalPosition(DYN_ID, tick, UNIT_RAW);
}

bool reached_goal(int32_t target_tick, uint8_t measure_spd, uint8_t measure_mode,
                  uint8_t error_tick, uint8_t DYN_ID){
  elapsedMillis polling;
  elapsedMillis t;

  while(cancelled == false){
    if(polling > POLL_TIMER){
      cur_pos = get_tick_position();
      cur_cur = fabsf(dxl.getPresentCurrent(DID, UNIT_MILLI_AMPERE));

      if (Serial.available()) {
        String stop_command = Serial.readStringUntil('\n');
        stop_command.trim();
        if(stop_command == "STOP"){
          Serial.println("Vorgang wurde abgebrochen");
          cancelled = true;
          break;
        }
      }
      if(measure_mode == 0){
        switch(measure_spd){
          case 0: if(cur_cur > cal_cur0 + cur_tolerance_slow){
            stopped_tick = get_tick_position();
            dxl.setGoalPosition(DID, cur_pos, UNIT_RAW);
            return false;} 
            break;
          case 1: if(cur_cur > cal_cur1 + cur_tolerance){
            dxl.setGoalPosition(DID, cur_pos, UNIT_RAW);
            return false;} 
            break;
          case 2: if(cur_cur > cal_cur2 + cur_tolerance){
            dxl.setGoalPosition(DID, cur_pos, UNIT_RAW);
            return false;} 
            break;
          case 3: if(cur_cur > cal_cur3 + cur_tolerance){
            dxl.setGoalPosition(DID, cur_pos, UNIT_RAW);
            return false;} 
            break;
          default: break;
        }
      }

      if(measure_mode == 1){
        switch(measure_spd){
          case 0: if(cal_cur0 < cur_cur){cal_cur0 = cur_cur;} break;
          case 1: if(cal_cur1 < cur_cur){cal_cur1 = cur_cur;} break;
          case 2: if(cal_cur2 < cur_cur){cal_cur2 = cur_cur;} break;
          case 3: if(cal_cur3 < cur_cur){cal_cur3 = cur_cur;} break;
          default: break;
        }
        if(fabsf(cur_cur) >= start_current){
          dxl.setGoalPosition(DID, cur_pos, UNIT_RAW);
          return false;
        }
      }

      if ((fabsf(cur_pos - target_tick) <= error_tick) && cur_pos - target_tick < 0) {
        for(int i = 0; i<5 ; i++){
          dxl.setGoalPosition(DID, get_tick_position() + 1, UNIT_RAW);
        } 
        return true;
      }
      else if ((fabsf(cur_pos - target_tick) <= error_tick) && cur_pos - target_tick > 0) {
        for(int i = 0; i<5 ; i++){
          dxl.setGoalPosition(DID, get_tick_position() - 1, UNIT_RAW);
        } 
        return true;
      }
      else if (cur_pos == target_tick){
        return true;
      }
      polling = 0;
    }
  }
  dxl.setGoalPosition(DID, get_tick_position(), UNIT_RAW);
  return false;
}
