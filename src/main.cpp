#include <Arduino.h>
#include <Dynamixel2Arduino.h>
#include <math.h>
#include <elapsedMillis.h>
#include <array>


// --------------- DYNAMIXEL VARIABLES
#define DXL_SERIAL Serial1
#define DEBUG_SERIAL Serial

const int DXL_DIR_PIN = A6;
const uint8_t DID = 1;
const float DXL_PROTOCOL = 2.0;
const uint32_t DXL_BAUD = 1000000;

Dynamixel2Arduino dxl(DXL_SERIAL, DXL_DIR_PIN);


// --------------- VARIABLES
const float DEG_PER_TICK = 360.0f / 4096.0f;
const float TICK_PER_DEG = 4096.0f / 360.0f;
const float RPM_PER_VEL = 0.229;
using namespace ControlTableItem;
const int32_t CHECK_END_START = -2000;
const int32_t CHECK_END_END = 6000;
const int32_t CALIBRATE_CURRENT_CCW = 1700;
const int32_t CALIBRATE_CURRENT_CW = 2400;
const int32_t ZERO_TICK = 2050;
const float MERCY_TOLERANCE_TICK = 15;
const float CHECK_ENDS_TOL_DEG = 10;
const int POLL_TIMER = 1;

int32_t stopped_tick;
float start_current = 180;
float cal_cur0, cal_cur1, cal_cur2, cal_cur3;
float cur_tolerance = 5;
int32_t start_tick, end_tick, mid_tick;
int32_t sim_mercy_start, sim_mercy_end;
bool cancelled;
int32_t cur_pos;
float cur_cur;
float slow_rpm = 5;
float user_rpm, rpm1, rpm2, rpm3;
float real_time1 = 0, real_time2 = 0, real_time3 = 0;
float theo_time1 = 0, theo_time2 = 0, theo_time3 = 0;
float target_deg_total;
int32_t user_go_to;
float delay1, delay2, delay3;
int tar_volt = 10;

const size_t print_array_size = 13;
float print_ist_deg[print_array_size];
float print_soll_deg[print_array_size];
float print_soll_volt[print_array_size];
float print_ist_volt[print_array_size];
float print_real_diff_mid[print_array_size];
float print_soll_volt_real[print_array_size];
float print_linear_real[print_array_size];
bool empty_cells[print_array_size];
bool error_lin;
bool error_mech;
bool error_midDead;
bool error_lin_index[print_array_size];

int32_t real_tick_total, soll_tick_total;
float soll_deg_total;
float d11_deg, d12_deg, d21_deg, d22_deg, d31_deg, d32_deg;
int32_t d11_tick, d12_tick, d21_tick, d22_tick, d31_tick, d32_tick;
int32_t user_goto;
float ist_start_volt, ist_end_volt, ist_mid_volt;
float ccw_links, ccw_rechts, cw_links, cw_rechts, aktiv_ccw, aktiv_cw, ges_aktiv;
float real_mid_deg;
float lin_min, lin_max;


// --------------- SETUP AND ASSIST FUNCTIONS
void setup(){
  Serial.begin(115200);
  dxl.begin(DXL_BAUD);
  dxl.setPortProtocolVersion(DXL_PROTOCOL);

  dxl.torqueOff(DID);
  dxl.setOperatingMode(DID, OP_EXTENDED_POSITION);
  dxl.writeControlTableItem(DRIVE_MODE, DID, 0b101);
  dxl.writeControlTableItem(HOMING_OFFSET, DID, 0);
  dxl.writeControlTableItem(PROFILE_VELOCITY, DID, 1000);
  dxl.writeControlTableItem(PROFILE_ACCELERATION, DID, 500);
  dxl.torqueOn(DID);

  dxl.ledOn(DID);
}




// --------------- INIT FUNCTION
void dxl_init(){
  cancelled = false;
  cal_cur0 = 0;
  cal_cur1 = 0;
  cal_cur2 = 0;
  cal_cur3 = 0;
  error_lin = false;
  error_mech = false;
  error_midDead = false;
  for (size_t i = 0; i < print_array_size; ++i) {
    error_lin_index[i] = false;
  }
  lin_max = 0;
  lin_min = 0;
  cancelled = false;
}




// -------------------- LINEARITY

// --------------- LOOP
void loop(){
  if(Serial.available()){
    String command = Serial.readStringUntil('\n');
    command.trim();

    // EINGABE VON PYTHON
    if(command.startsWith("SETW:")){target_deg_total = command.substring(5).toFloat();}
    if(command.startsWith("SETS:")){user_rpm = command.substring(5).toFloat();}

    if(command.startsWith("goto:")){user_go_to = command.substring(5).toFloat();}

    if(command == "ZERO"){
      go_zero();
    }
    
    if(command == "GO"){
      dxl_init();
      calibrate_currents();
      check_ends();

      if(cancelled == false){
        Serial.println("READY");
      } else{
        Serial.println("CANCEL");
        cancelled = false;
      }
    }
    if(command == "START"){
      noise_movement();

      if(cancelled == true){
        Serial.println("CANCEL");
        cancelled = false;
      }
      drive_to(ZERO_TICK, user_rpm);
      reached_goal(ZERO_TICK, 2);
      dxl.ledOff(DID);
    }
  }
}
