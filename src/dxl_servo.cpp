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
const int32_t MAX_SAFE_MOVE_TICKS = 13000;

Dynamixel2Arduino dxl(DXL_SERIAL, DXL_DIR_PIN);


// --------------- CONSTANTS
const float DEG_PER_TICK = 360.0f / 4096.0f;
const float TICK_PER_DEG = 4096.0f / 360.0f;
const float RPM_PER_VEL = 0.229;
const float START_CURRENT = 800;
const float CUR_TOLERANCE = 35;
const int POLL_TIMER = 1;
const float SLOW_RPM = 8;
const int32_t MAX_POSITION_JUMP_TICKS = 512;
using namespace ControlTableItem;

// --------------- VARIABLES
int32_t stopped_tick;
float cal_cur0, cal_cur1, cal_cur2, cal_cur3;
float cur_tolerance_slow = 6; // dp37 4-5, stiel 1-2
bool cancelled;
int32_t cur_pos;
float cur_cur;
float user_rpm = 60;
float rpm1, rpm2, rpm3;
bool hohlwelle;

// --------------- HELPER FUNCTIONS
int32_t deg_to_tick(float deg){
  return deg * TICK_PER_DEG;
}

float tick_to_deg(int32_t tick){
  return tick * DEG_PER_TICK;
}

bool read_tick_position_checked(int32_t &position){
  const float raw_position =
      dxl.getPresentPosition(DID, UNIT_RAW);

  if(dxl.getLastLibErrCode() != DXL_LIB_OK ||
     !isfinite(raw_position)){
    return false;
  }

  position = static_cast<int32_t>(lroundf(raw_position));
  return true;
}

int32_t get_tick_position(){
  return dxl.getPresentPosition(DID, UNIT_RAW);
}

float get_deg_position(){
  return tick_to_deg(dxl.getPresentPosition(DID, UNIT_RAW));
}

uint32_t rpm_to_time(int32_t goal_tick, float rpm){
  uint32_t out_time = 60/rpm*1000;
  int32_t current_tick = dxl.getPresentPosition(DID, UNIT_RAW);
  int32_t diff_pos = abs(current_tick - goal_tick);
  out_time = out_time * diff_pos/4096;
  return out_time;
}

void dxl_init(){
  cancelled = false;
  stopped_tick = 0;
  cal_cur0 = 0;
  cal_cur1 = 0;
  cal_cur2 = 0;
  cal_cur3 = 0;
  cur_pos = 0;
  cur_cur = 0;
  rpm1 = 0;
  rpm2 = 0;
  rpm3 = 0;
}

void cancel_with_reason(const char* reason) {
  if(!cancelled) {
    Serial.print("CANCEL:");
    Serial.println(reason);
  }

  cancelled = true;
}

// void stop_motion(uint8_t DYN_ID){
//   dxl.setGoalPosition(DYN_ID, get_tick_position(), UNIT_RAW);
// }

void stop_motion(uint8_t DYN_ID){
  int32_t hold_position;

  if(!read_tick_position_checked(hold_position)){
    cancelled = true;
    dxl.torqueOff(DYN_ID);
    Serial.println("STOP_FAILED:POSITION_READ;TORQUE_OFF");
    return;
  }

  const int64_t position_jump =
      static_cast<int64_t>(hold_position) -
      static_cast<int64_t>(cur_pos);

  // Ein Sprung wie 2050 -> -65536 darf niemals als Halteziel
  // an den Servo geschrieben werden.
  if(position_jump > MAX_POSITION_JUMP_TICKS ||
     position_jump < -MAX_POSITION_JUMP_TICKS){

    cancelled = true;
    dxl.torqueOff(DYN_ID);

    Serial.print("STOP_FAILED:IMPLAUSIBLE_POSITION;LAST=");
    Serial.print(cur_pos);
    Serial.print(";READ=");
    Serial.print(hold_position);
    Serial.println(";TORQUE_OFF");

    return;
  }

  if(!dxl.setGoalPosition(DYN_ID, hold_position, UNIT_RAW)){
    cancelled = true;
    dxl.torqueOff(DYN_ID);
    Serial.println("STOP_FAILED:HOLD_WRITE;TORQUE_OFF");
  }
}


// --------------- DRIVE FUNCTIONS

// void drive_to(int32_t tick, float rpm, uint8_t DYN_ID){
//   int32_t current_tick = get_tick_position();

//   // if(!read_tick_position_checked(current_tick)){
//   //   dxl.torqueOff(DYN_ID);
//   //   cancel_with_reason("POSITION_READ_FAILED");
//   //   return;
//   // }

//   cur_pos = current_tick;

//   const int64_t delta =
//       static_cast<int64_t>(tick) -
//       static_cast<int64_t>(current_tick);

//   Serial.print("MOVE_REQUEST:CURRENT=");
//   Serial.print(current_tick);
//   Serial.print(";TARGET=");
//   Serial.print(tick);
//   Serial.print(";DELTA=");
//   Serial.println(delta);

//   if(delta > MAX_SAFE_MOVE_TICKS || delta < -MAX_SAFE_MOVE_TICKS){
//     cancelled = true;
//     dxl.torqueOff(DYN_ID);

//     Serial.print("MOVE_REJECTED:CURRENT=");
//     Serial.print(current_tick);
//     Serial.print(";TARGET=");
//     Serial.print(tick);
//     cancel_with_reason("MOVE_DISTANCE_EXCEEDED");
//     return;
//   }

//   if(!dxl.writeControlTableItem(
//         PROFILE_VELOCITY, DYN_ID, rpm_to_time(tick, rpm)) ||
//      !dxl.writeControlTableItem(
//         PROFILE_ACCELERATION, DYN_ID, 0)){

//     cancelled = true;
//     dxl.torqueOff(DYN_ID);
//     Serial.println("MOVE_REJECTED:PROFILE_WRITE_FAILED;TORQUE_OFF");
//     return;
//   }

//   if(!dxl.setGoalPosition(DYN_ID, tick, UNIT_RAW)){
//     cancelled = true;
//     dxl.torqueOff(DYN_ID);
//     Serial.println("MOVE_REJECTED:GOAL_WRITE_FAILED;TORQUE_OFF");
//     return;
//   }

//   const int32_t written_goal =
//       dxl.readControlTableItem(GOAL_POSITION, DYN_ID);

//   if(dxl.getLastLibErrCode() != DXL_LIB_OK ||
//      written_goal != tick){

//     cancelled = true;
//     dxl.torqueOff(DYN_ID);

//     Serial.print("MOVE_REJECTED:GOAL_VERIFY_FAILED;REQUESTED=");
//     Serial.print(tick);
//     Serial.print(";READBACK=");
//     Serial.print(written_goal);
//     Serial.println(";TORQUE_OFF");
//     return;
//   }

//   Serial.print("MOVE_ACCEPTED:GOAL=");
//   Serial.println(written_goal);
// }

// bool reached_goal(int32_t target_tick, uint8_t measure_spd, uint8_t measure_mode, int timeout, 
//                   uint8_t error_tick, uint8_t DYN_ID){
//   elapsedMillis polling;
//   elapsedMillis t;

//   // if(cancelled){
//   //   Serial.println("MOVE_REJECTED:ALREADY_CANCELLED");
//   //   return false;
//   // }

//   while(cancelled == false && t < timeout){  
//     if(polling > POLL_TIMER){
//       cur_pos = get_tick_position();
//       cur_cur = fabsf(dxl.getPresentCurrent(DID, UNIT_MILLI_AMPERE));

//       if (Serial.available()) {
//         String stop_command = Serial.readStringUntil('\n');
//         stop_command.trim();
//         if(stop_command == "STOP"){
//           Serial.println("Vorgang wurde abgebrochen");
//           stop_motion(DYN_ID);
//           cancelled = true;
//           break;
//         }
//       }
//       if(measure_mode == 0){
//         switch(measure_spd){
//           case 0: if(cur_cur > cal_cur0 + cur_tolerance_slow){
//             stopped_tick = get_tick_position();
//             dxl.setGoalPosition(DID, cur_pos, UNIT_RAW);
//             return false;} 
//             break;
//           case 1: if(cur_cur > cal_cur1 + CUR_TOLERANCE){
//             dxl.setGoalPosition(DID, cur_pos, UNIT_RAW);
//             cancel_with_reason("CURRENT_LIMIT_RPM1");
//             // cancelled = true;
//             // Serial.println("CANCEL");
//             return false;} 
//             break;
//           case 2: if(cur_cur > cal_cur2 + CUR_TOLERANCE){
//             dxl.setGoalPosition(DID, cur_pos, UNIT_RAW);
//             cancel_with_reason("CURRENT_LIMIT_RPM2");
//             // cancelled = true;
//             // Serial.println("CANCEL");
//             return false;} 
//             break;
//           case 3: if(cur_cur > cal_cur3 + CUR_TOLERANCE){
//             dxl.setGoalPosition(DID, cur_pos, UNIT_RAW);
//             cancel_with_reason("CURRENT_LIMIT_RPM3");
//             // cancelled = true;
//             // Serial.println("CANCEL");
//             return false;} 
//             break;
//           default: break;
//         }
//       }

//       if(measure_mode == 1){
//         switch(measure_spd){
//           case 0: if(cal_cur0 < cur_cur){cal_cur0 = cur_cur;} break;
//           case 1: if(cal_cur1 < cur_cur){cal_cur1 = cur_cur;} break;
//           case 2: if(cal_cur2 < cur_cur){cal_cur2 = cur_cur;} break;
//           case 3: if(cal_cur3 < cur_cur){cal_cur3 = cur_cur;} break;
//           default: break;
//         }
//         if(fabsf(cur_cur) >= START_CURRENT){
//           dxl.setGoalPosition(DID, cur_pos, UNIT_RAW);
//           cancelled = true;
//           Serial.println("CANCEL");
//           return false;
//           break;
//         }
//       }

//       if ((fabsf(cur_pos - target_tick) <= error_tick) && cur_pos - target_tick < 0) {
//         //for(int i = 0; i<5 ; i++){
//           dxl.setGoalPosition(DID, get_tick_position() + 1, UNIT_RAW);
//         //} 
//         return true;
//         break;
//       }
//       else if ((fabsf(cur_pos - target_tick) <= error_tick) && cur_pos - target_tick > 0) {
//         //for(int i = 0; i<5 ; i++){
//           dxl.setGoalPosition(DID, get_tick_position() - 1, UNIT_RAW);
//         //} 
//         return true;
//         break;
//       }
//       else if (cur_pos == target_tick){
//         return true;
//         break;
//       }
//       polling = 0;
//     }
//   }
//   // if(cancelled){
//   //   return false;
//   // }

//   stop_motion(DYN_ID);
//   return false;
// }

void drive_to(int32_t tick, float rpm, uint8_t DYN_ID){
  // dxl.torqueOff(DYN_ID);
  dxl.writeControlTableItem(PROFILE_VELOCITY, DYN_ID, rpm_to_time(tick, rpm)); 
  dxl.writeControlTableItem(PROFILE_ACCELERATION, DYN_ID, 0);
  // dxl.setGoalPosition(DYN_ID, tick, UNIT_RAW);
  // dxl.torqueOn(DYN_ID);
  dxl.setGoalPosition(DYN_ID, tick, UNIT_RAW);
}

bool reached_goal(int32_t target_tick, uint8_t measure_spd, uint8_t measure_mode, int timeout, 
                  uint8_t error_tick, uint8_t DYN_ID){
  elapsedMillis polling;
  elapsedMillis t;

  while(cancelled == false && t < timeout){  
    if(polling > POLL_TIMER){
      cur_pos = get_tick_position();
      cur_cur = fabsf(dxl.getPresentCurrent(DID, UNIT_MILLI_AMPERE));

      if (Serial.available()) {
        String stop_command = Serial.readStringUntil('\n');
        stop_command.trim();
        if(stop_command == "STOP"){
          Serial.println("Vorgang wurde abgebrochen");
          stop_motion(DYN_ID);
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
          case 1: if(cur_cur > cal_cur1 + CUR_TOLERANCE){
            dxl.setGoalPosition(DID, cur_pos, UNIT_RAW);
            cancelled = true;
            Serial.println("CANCEL");
            return false;} 
            break;
          case 2: if(cur_cur > cal_cur2 + CUR_TOLERANCE){
            dxl.setGoalPosition(DID, cur_pos, UNIT_RAW);
            cancelled = true;
            Serial.println("CANCEL");
            return false;} 
            break;
          case 3: if(cur_cur > cal_cur3 + CUR_TOLERANCE){
            dxl.setGoalPosition(DID, cur_pos, UNIT_RAW);
            cancelled = true;
            Serial.println("CANCEL");
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
        if(fabsf(cur_cur) >= START_CURRENT){
          dxl.setGoalPosition(DID, cur_pos, UNIT_RAW);
          cancelled = true;
          Serial.println("CANCEL");
          return false;
          break;
        }
      }

      if ((fabsf(cur_pos - target_tick) <= error_tick) && cur_pos - target_tick < 0) {
        //for(int i = 0; i<5 ; i++){
          dxl.setGoalPosition(DID, get_tick_position() + 1, UNIT_RAW);
        //} 
        return true;
        break;
      }
      else if ((fabsf(cur_pos - target_tick) <= error_tick) && cur_pos - target_tick > 0) {
        //for(int i = 0; i<5 ; i++){
          dxl.setGoalPosition(DID, get_tick_position() - 1, UNIT_RAW);
        //} 
        return true;
        break;
      }
      else if (cur_pos == target_tick){
        return true;
        break;
      }
      polling = 0;
    }
  }
  stop_motion(DYN_ID);
  return false;
}

void calc_rpm(){
  float rpm_intervall = user_rpm/2;
  for(int i = 1; i <= 3; i++){
    switch(i){
      case 1:
        rpm1 = rpm_intervall*i;
        break;
      case 2:
        rpm2 = rpm_intervall*i;
        break;
      case 3:
        rpm3 = rpm_intervall*i;
        break;
      default:
        break;
    }
  }
}