#include <Arduino.h>
#include <Dynamixel2Arduino.h>
#include <math.h>
#include <elapsedMillis.h>
#include <array>

#include <servo.h>
#include <calibrate.h>
#include <noise.h>
#include <linearity.h>
#include <elec_deg.h>


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


// --------------- LOOP
void loop(){
  if(Serial.available()){
    String command = Serial.readStringUntil('\n');
    command.trim();

    // EINGABE VON PYTHON
    if(command.startsWith("SETW:")){target_deg_total = command.substring(5).toFloat();}
    if(command.startsWith("SETS:")){user_rpm = command.substring(5).toFloat();}
    if(command.startsWith("goto:")){user_go_to = command.substring(5).toFloat();}
    if(command.startsWith("dead11:")){d11_deg = command.substring(7).toFloat();}
    if(command.startsWith("dead12:")){d12_deg = command.substring(7).toFloat();}
    if(command.startsWith("dead21:")){d21_deg = command.substring(7).toFloat();}
    if(command.startsWith("dead22:")){d22_deg = command.substring(7).toFloat();}
    if(command.startsWith("dead31:")){d31_deg = command.substring(7).toFloat();}
    if(command.startsWith("dead32:")){d32_deg = command.substring(7).toFloat();}

    if(command == "ZERO"){
      go_zero();
    }
    
    if(command == "ENDS_GO"){
      dxl_init();
      calibrate_currents();
      check_ends();
      
      if(cancelled == true){
        Serial.println("CANCEL");
        cancelled = false;
      }
      drive_to(ZERO_TICK, user_rpm);
      reached_goal(ZERO_TICK, 2);
      dxl.ledOff(DID);
    }

     if(command == "ELEC_DEG_GO"){
      dxl_init();
      calibrate_currents();
      check_ends(true);
      
      if(cancelled == false){
        Serial.println("ELEC_DEG_READY");
      } else{
        Serial.println("CANCEL");
        cancelled = false;
      }
    }
    if(command == "ELEC_DEG_START"){
      elec_deg_movement();

      if(cancelled == true){
        Serial.println("CANCEL");
        cancelled = false;
      }
      drive_to(ZERO_TICK, user_rpm);
      reached_goal(ZERO_TICK, 2);
      dxl.ledOff(DID);
    }

    if(command == "NOISE_GO"){
      dxl_init();
      calibrate_currents();
      check_ends();
      
      if(cancelled == false){
        Serial.println("NOISE_READY");
      } else{
        Serial.println("CANCEL");
        cancelled = false;
      }
    }
    if(command == "NOISE_START"){
      noise_movement();

      if(cancelled == true){
        Serial.println("CANCEL");
        cancelled = false;
      }
      drive_to(ZERO_TICK, user_rpm);
      reached_goal(ZERO_TICK, 2);
      dxl.ledOff(DID);
    }

    if(command == "LINEAR_GO"){
      dxl_init();
      lin_init();
      calibrate_currents();
      check_ends(true);
      
      if(cancelled == false){
        Serial.println("LINEAR_READY");
      } else{
        Serial.println("CANCEL");
        cancelled = false;
      }
    }
    if(command == "LINEAR_START"){
      linearity_movement();

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
